"""Anomaly Detector for attributes based on the history of their profiles."""
from __future__ import annotations

from typing import TYPE_CHECKING

import numpy
import pandas
import scipy.fft
import statsmodels.tsa.seasonal as seasonal

from sklearn.ensemble import IsolationForest
from sklearn.linear_model import LinearRegression

from aicore.anomaly_detection.definitions import (
    AnomalyDetectionResultBase,
    AnomalyDetectorModelBase,
    Category,
    CategoryType,
    ConfidenceBounds,
    FeatureResultPerIndex,
    IsolationForestFeatureResult,
    SeasonalDecomposeError,
    TimeSeriesComponents,
    TimeSeriesFeatureResult,
)
from aicore.anomaly_detection.feature_provider import MIN_FETCHED_DATA_POINTS
from aicore.common.utils import resolve_cpu_count


if TYPE_CHECKING:
    from typing import Iterator, Union

    from aicore.anomaly_detection.types import (
        AnomalyDetectionWorkflow,
        AnomalyPrediction,
        AnomalyPredictions,
        AnomalyScore,
        AnomalyScores,
        CategoryData,
        CategoryFeatureData,
        FeatureName,
    )

LIMIT_OF_FREQUENCY_FEATURES = 20  # Processing only 10 most and 10 least frequent items due to performance requirements.
MIN_TIME_SERIES_LENGTH = 6  # If number of profiles < 6, time series is skipped and non-time series model is used.
TIME_SERIES_ROUNDING = 4  # Rounding decomposed components to 4th decimal number.
LINEAR_REGRESSION_ON_LAST_N_POINTS = 10  # Number of history points to be taken into account for drifting trend.
MIN_REQUIRED_PERIODS = 2  # Two full periods are required in order to run seasonal decomposition.
MAX_Z_SCORE = 10.0  # Z-scores are limited to [0; MAX_Z_SCORE] interval.
# Approximate maximum number of non-blank
# characters to render. We pass it as an optional parameter to ease the tests.
N_CHAR_MAX = 700


def select_model_class(periodicity: int) -> type[AnomalyDetectorModelBase]:
    """Select model class according to provided periodicity."""
    return TimeSeriesAnalysisModel if periodicity else IsolationForestModel


class IsolationForestResult(AnomalyDetectionResultBase):
    """Evaluation of one feature by Isolation Forest."""

    # Isolation forest does not have any bounds, so it returns this dummy values to be consistent with other models
    DUMMY_BOUNDS = ConfidenceBounds(0.0, 0.0, 0.0)

    def __init__(self):
        self.category_predictions: AnomalyPredictions = numpy.empty(0, dtype=bool)
        self.category_scores: AnomalyScores = numpy.empty(0, dtype=float)
        self.feature_results: dict[FeatureName, IsolationForestFeatureResult] = {}

    def add_feature_result(
        self,
        feature_name: str,
        anomaly_scores: AnomalyScores,
        predictions: AnomalyPredictions,
    ):
        """Add non-time series IsolationForest result for each feature."""
        self.feature_results[feature_name] = IsolationForestFeatureResult(anomaly_scores, predictions)

    def is_category_anomalous(self) -> bool:
        """Check if any prediction in the category is anomalous, thus the whole category is anomalous."""
        return self.category_predictions.any().item()

    def get_score(self, index_from_end) -> AnomalyScore:
        """Get category score for a given index."""
        return self.category_scores[-index_from_end - 1].item()

    def get_prediction(self, index_from_end) -> AnomalyPrediction:
        """Get category prediction for a given index."""
        return self.category_predictions[-index_from_end - 1].item()

    def iter_feature_results(self, index_from_end: int) -> Iterator[FeatureResultPerIndex]:
        """Get the feature results in a unified format."""
        # Protobuf does not work with numpy bool or float, thus it needs to be transformed to python types by .item()
        for feature_name, (anomaly_scores, predictions) in self.feature_results.items():
            yield FeatureResultPerIndex(
                feature_name,
                anomaly_scores[-index_from_end - 1].item(),
                predictions[-index_from_end - 1].item(),
                self.DUMMY_BOUNDS,
            )


class IsolationForestModel(IsolationForest, AnomalyDetectorModelBase):
    """
    This class reimplements the fit method to shift the offset from -0.5 to -0.6.

    In other words it modifies the threshold for classifying anomalies. This setting has been tuned over CVUT datasets
    on cases with 0, 1, 2 anomalies among 20 partitions.

    """

    result_class = IsolationForestResult
    result: IsolationForestResult
    offset: float

    def __init__(self, config, hcns: list[int]):
        AnomalyDetectorModelBase.__init__(self, config, hcns)

        super_kwargs = {"contamination": "auto", "random_state": 22, "n_estimators": 50}

        jobs = resolve_cpu_count(self.config.jobs)
        if jobs is not None:
            super_kwargs["n_jobs"] = jobs

        IsolationForest.__init__(self, **super_kwargs)
        # We set our own offset based on config to set the base model's offset later after fit method
        self.offset: float = config.anomaly_detector_isolation_forest_threshold

        # GENERIC type needs fit and predict on each category and then on individual features for explainability
        # FREQUENCIES type is run on categories then need to be cut off and then run on individual features
        # FINGERPRINTS type in only run on categories, individual features do not have meaning to be run separately
        self.methods_per_category_type: dict[CategoryType, AnomalyDetectionWorkflow] = {
            CategoryType.GENERIC: [self.fit_and_predict_on_categories, self.fit_and_predict_on_features],
            # These statistics are cut off, because they can be potentially very long and thus slow down the processing
            CategoryType.FREQUENCIES: [
                self.fit_and_predict_on_categories,
                self.cut_off_frequencies,
                self.fit_and_predict_on_features,
            ],
            CategoryType.FINGERPRINTS: [self.fit_and_predict_on_categories],
        }

    def __repr__(
        self, _n_char_max=N_CHAR_MAX
    ) -> str:  # The parameter is upper cases to follow the same pattern as the base class
        # Specifically in sklearn BaseEstimator found in base.py
        return type(self).__name__

    def min_data_length(self, _category: Category):
        """Get minimal length of data for which anomaly detection model can be run."""
        return MIN_FETCHED_DATA_POINTS

    def fit_and_predict_on_categories(self, category: Category):
        """Detect anomalies on category level."""
        scores, predictions = self.detect_anomalies(category.data, category.indexes_of_confirmed_anomalous)
        self.result.category_scores = scores
        self.result.category_predictions = predictions

    def fit_and_predict_on_features(self, category: Category):
        """Detect anomalies on individual feature level."""
        # Anomaly detection done on individual features to get explainability of anomalies
        if self.result.is_category_anomalous():
            for feature_name, feature_data_frame in category.features.items():
                anomaly_scores, predictions = self.detect_anomalies(
                    feature_data_frame, category.indexes_of_confirmed_anomalous
                )
                self.result.add_feature_result(feature_name, anomaly_scores, predictions)

    def cut_off_frequencies(self, category: Category):
        """
        Cut off frequencies to have only most frequent.

        Cutting off frequencies to minimize running time of Isolation forest.
        Limit number of used features - thus avoiding the worst case which could be number_of_rows*number_of_profiles.
        Most interesting are most frequent from the last profile and most frequent over all.
        """
        last_profile_sorted = category.data.iloc[-1].sort_values(ascending=False)
        most_frequent_keys_last_profile = last_profile_sorted.head(LIMIT_OF_FREQUENCY_FEATURES // 2).index.values
        data_without_keys_from_last_profile = category.data.drop(columns=most_frequent_keys_last_profile)
        sorted_by_sum = data_without_keys_from_last_profile.sum().sort_values(ascending=False)
        most_frequent_keys = set(sorted_by_sum.head(LIMIT_OF_FREQUENCY_FEATURES // 2).index.values)
        frequent_keys_to_keep = set.union(most_frequent_keys, most_frequent_keys_last_profile)

        category.data = category.data[frequent_keys_to_keep]

    def detect_anomalies(
        self, data_frame: CategoryData, indexes_of_confirmed_anomalous: list[int]
    ) -> tuple[AnomalyScores, AnomalyPredictions]:
        """Analyze anomalies by Isolation Forest in a given category of feature data and get scores and predictions."""
        # We do not use previously confirmed anomalous points, thus we remove (drop) them
        data_frame_anomalies_dropped = data_frame.drop(index=indexes_of_confirmed_anomalous)

        anomaly_scores, predictions = self.compute_anomaly_scores_and_predictions(data_frame_anomalies_dropped)

        # We insert dropped indexes i.e. previously confirmed anomalies which we didn't use in the model
        for index in indexes_of_confirmed_anomalous:
            anomaly_scores = numpy.insert(anomaly_scores, index, 1.0)
            predictions = numpy.insert(predictions, index, True)

        return anomaly_scores, predictions

    def compute_anomaly_scores_and_predictions(
        self, data: Union[CategoryData, CategoryFeatureData]
    ) -> tuple[numpy.ndarray, numpy.ndarray]:
        """Based on the shape of the dataframe compute anomaly scores and predictions."""
        # How many data points (e.g. profiles) are stored for a given category (e.g. some might be cut off)
        number_of_data_points_per_category = data.shape[0]
        # If we don't have enough data points after removing the anomalous ones we set the values to default
        if number_of_data_points_per_category < 2:
            # We set default value of 0 as anomaly score
            anomaly_scores = numpy.zeros(number_of_data_points_per_category, dtype=float)
            # We set default value of False as prediction
            predictions = numpy.zeros(number_of_data_points_per_category, dtype=bool)
            return anomaly_scores, predictions

        data = pandas.DataFrame(data)  # make sure the input is 2d
        self.fit(data)

        # Base fit method sets default offset parameter, we need to set our own defined by config for the decision fn
        # If using default offset parameter, the model is oversensitive and detecting many false positive anomalies
        self.offset_ = self.offset
        anomaly_scores = -self.decision_function(data)  # Positive anomaly score means an anomaly
        # Sometimes when values are identical among profiles, these anomaly scores are very close to 0.
        anomaly_scores[abs(anomaly_scores) < 1e-5] = 0
        predictions = anomaly_scores > 0  # True if anomaly

        return anomaly_scores, predictions


class TimeSeriesResult(AnomalyDetectionResultBase):
    """Evaluation of one feature by Time series analysis."""

    def __init__(self):
        self.feature_results: dict[FeatureName, TimeSeriesFeatureResult] = {}

    def add(
        self,
        feature_name: str,
        anomaly_score: float,
        prediction: bool,
        last_point_bounds: ConfidenceBounds,
        # Lower expected bound, expected value, upper expected bound
    ):
        """Add time series result for each specified feature."""
        self.feature_results[feature_name] = TimeSeriesFeatureResult(
            anomaly_score=anomaly_score, prediction=prediction, bounds=last_point_bounds
        )

    def get_score(self, _index_from_end) -> AnomalyScore:
        """Get max anomaly score over all features."""
        # We do not yet use _index_from_end, only if time series would be done for more than just the last data point
        return max(feature_result.anomaly_score for feature_result in self.feature_results.values())

    def get_prediction(self, _index_from_end) -> AnomalyPrediction:
        """Get whether there was anomaly over all features."""
        # We do not yet use _index_from_end, only if time series would be done for more than just the last data point
        any_anomalous = any(feature_result.prediction for feature_result in self.feature_results.values())
        return any_anomalous

    def iter_feature_results(self, _index_from_end: int) -> Iterator[FeatureResultPerIndex]:
        """Get feature results in a unified format."""
        for feature_name, (score, prediction, bounds) in self.feature_results.items():
            yield FeatureResultPerIndex(feature_name, score, prediction, bounds)


class TimeSeriesAnalysisModel(AnomalyDetectorModelBase):
    """Time series model using decomposition of season, trend and residuals (errors)."""

    result_class = TimeSeriesResult
    result: TimeSeriesResult

    def __init__(self, config, hcns: list[int]):
        super().__init__(config, hcns)

        # The number of standard deviations from the mean beyond which points are marked as anomalous
        self.threshold_std = config.anomaly_detector_time_series_std_threshold

        # Uses convolution filter which uses SciPy's FFT which is parallelized by concurrent.futures.ThreadPoolExecutor
        # but statsmodels doesn't expose SciPy's setting of thread workers so we have to use it ourselves
        # Most likely the number of threads can be driven via limit for OpenMP as well
        self.workers = resolve_cpu_count(self.config.jobs)

        if self.workers is None:
            self.workers = scipy.fft.get_workers()

        self.methods_per_category_type: dict[CategoryType, AnomalyDetectionWorkflow] = {
            CategoryType.GENERIC: [self.fit_and_predict_on_features],
            # These statistics are cut off, because they can be potentially very long and thus slow down the processing
            CategoryType.FREQUENCIES: [
                self.fit_and_predict_on_features,
                self.cut_off_frequencies,
            ],
            # Fingerprints are not used in time series analysis, TSA model is unable to take a multidimensional input
            CategoryType.FINGERPRINTS: None,
        }

    @property
    def hcns(self):
        """Time series model takes only the last hcn."""
        return self._hcns[-1:]

    def __repr__(self):
        return type(self).__name__

    def min_data_length(self, category: Category):
        """Get minimal length of data for which anomaly detection model can be run."""
        return max(MIN_TIME_SERIES_LENGTH, category.periodicity * MIN_REQUIRED_PERIODS + 1)

    def fit_and_predict_on_features(self, category: Category):
        """Run anomaly detection individually on each feature in a category."""
        for feature_name, feature_data_time_series in category.features.items():
            self.impute_anomalous_points_in_time_series(
                feature_data_time_series, category.periodicity, category.indexes_of_confirmed_anomalous
            )
            anomaly_score, prediction, last_point_bounds = self.analyze_time_series(
                feature_data_time_series, category.periodicity
            )
            self.result.add(feature_name, anomaly_score, prediction, last_point_bounds)

    def cut_off_frequencies(self, _category: Category):
        """Cut off frequencies in time-series analysis results to contain only most anomalous."""
        # Sorting the statistics by anomaly scores (descending) and cutting off,
        # indexing [1] first takes the value of the dictionary and then the anomaly score
        sorted_frequencies = sorted(
            self.result.feature_results.items(),
            key=lambda result: result[1].anomaly_score,
            reverse=True,
        )

        # Limiting the number of returned results - at worst case could be row_count*number_of_profiles
        sorted_and_cut_off = sorted_frequencies[:LIMIT_OF_FREQUENCY_FEATURES]

        self.result.feature_results = {
            feature_name: feature_result for feature_name, feature_result in sorted_and_cut_off
        }

    def impute_anomalous_points_in_time_series(
        self,
        time_series: pandas.Series,
        periodicity: int,
        indexes_of_confirmed_anomalous: list[int],
    ):
        """Replace confirmed anomalous points with predictions."""
        # Assumes there are no sequential anomalies
        for index in indexes_of_confirmed_anomalous:
            # Replace anomalous by average of neighbours
            if index < periodicity * MIN_REQUIRED_PERIODS:
                value_to_replace = self.get_replacement_value_of_average_of_neighbours(time_series, index)
            # Use time series analysis to predict the expected value to replace the anomalous point
            else:
                # We take the time series up to (including) the anomalous value
                time_series_up_to_index = time_series.iloc[: index + 1]
                # We find the expected value of the anomalous point
                bounds = self.analyze_time_series(time_series_up_to_index, periodicity).bounds
                # We replace the anomalous value by the expected as predicted by the time series analysis
                value_to_replace = bounds.mean_value

            time_series.update(pandas.Series([value_to_replace], index=[index]))

    @staticmethod
    def get_replacement_value_of_average_of_neighbours(time_series: pandas.Series, index_of_anomalous: int) -> float:
        """Compute replacement value for a point in time series by the average of its neighbours."""
        # How many data points (e.g. profiles) are stored for a given statistic (e.g. some might be cut off)
        number_of_data_points_per_statistic = time_series.shape[0]
        # When we want to replace the first value, we replace it with the right neighbour only
        if index_of_anomalous == 0:
            return time_series.iloc[1]
        # When we want to replace the last value, we use the left neighbour only
        elif index_of_anomalous == number_of_data_points_per_statistic - 1:
            return time_series.iloc[-2]
        else:
            return (time_series.iloc[index_of_anomalous - 1] + time_series.iloc[index_of_anomalous + 1]) / 2.0

    def analyze_time_series(self, time_series: CategoryFeatureData, periodicity: int) -> TimeSeriesFeatureResult:
        """Run anomaly detection for one time series."""
        time_series_without_last_point = time_series.iloc[:-1]  # Anomaly prediction only on last datapoint
        value_of_last_point = time_series.iloc[-1].item()

        with scipy.fft.set_workers(self.workers):
            try:
                # Do not use built-in extrapolate trend method, contains bug, thus setting the param to 0
                decomposed: seasonal.DecomposeResult = seasonal.seasonal_decompose(
                    time_series_without_last_point, period=periodicity, extrapolate_trend=0
                )
            except Exception as error:
                raise SeasonalDecomposeError(periodicity) from error

        # There is a bug in statsmodel library extrapolate_trend method, thus we use our own
        extrapolated_trend = self.extrapolate_trend(decomposed.trend, periodicity)
        # Residuals need to be obtained from the extrapolated trend
        extrapolated_resid = decomposed.observed - extrapolated_trend - decomposed.seasonal

        time_series_components = TimeSeriesComponents(
            trend=extrapolated_trend.values, seasonal=decomposed.seasonal.values, residuals=extrapolated_resid.values
        )
        next_trend = self.predict_next_trend(time_series_components.trend)
        next_seasonal = self.predict_next_seasonal(time_series_components.seasonal, periodicity)
        correction = next_trend + next_seasonal

        bounds = self.get_normality_bounds(time_series_components.residuals, correction)
        anomaly_score = self.compute_anomaly_score(bounds, value_of_last_point)
        prediction = self.is_anomalous(anomaly_score)

        return TimeSeriesFeatureResult(anomaly_score, prediction, bounds)

    @staticmethod
    def predict_next_trend(trend: numpy.ndarray) -> float:
        """Predict next value from a trend using Linear regression."""
        n_points = len(trend)
        # Changing type to float64 (previously float32) fixes failing test on Windows due to linalg error
        x_values = numpy.arange(n_points).reshape(-1, 1).astype(numpy.float64)
        y_values = trend.reshape(-1, 1).astype(numpy.float64)
        regressor = LinearRegression()
        # Fit the linear regressor on last 'LINEAR_REGRESSION_ON_LAST_N_POINTS' points
        regressor.fit(
            x_values[-LINEAR_REGRESSION_ON_LAST_N_POINTS:],
            y_values[-LINEAR_REGRESSION_ON_LAST_N_POINTS:],
        )
        # Predict one point ahead
        predicted_trend = regressor.predict(numpy.asarray(n_points).reshape(-1, 1)).item()
        # Rounding to get clean results, linear regression gives imprecise results due to optimization process
        return numpy.round(predicted_trend, TIME_SERIES_ROUNDING)

    @staticmethod
    def predict_next_seasonal(seasonal_data: numpy.ndarray, periodicity) -> float:
        """Predict next value based on seasonal data."""
        # Seasonal value is predicted as the next point of the periodic function given by the period
        # To obtain the next value of the periodical pattern we take the first value located at n previous period steps
        return seasonal_data[-periodicity].item()

    def get_normality_bounds(self, population_values: numpy.ndarray, correction: float) -> ConfidenceBounds:
        """Compute confidence bound of normal datapoint."""
        mean = numpy.mean(population_values).item() + correction
        std = numpy.std(population_values).item()

        max_bound = round(mean + self.threshold_std * std, TIME_SERIES_ROUNDING)
        min_bound = round(mean - self.threshold_std * std, TIME_SERIES_ROUNDING)
        mean = round(mean, TIME_SERIES_ROUNDING)

        # If due to number precision the mean is not inside the bounds we adjust the bounds
        if max_bound < mean or min_bound > mean:
            max_bound = mean
            min_bound = mean

        return ConfidenceBounds(min_bound, mean, max_bound)

    def compute_anomaly_score(self, bounds: ConfidenceBounds, evaluated_value: float) -> float:
        """Compute anomaly score (z-score) of the evaluated value based on bounds."""
        bound_spread = bounds.max_bound - bounds.min_bound
        # Due to number imprecision or due to identical population values
        if bound_spread < 1e-5:
            if evaluated_value == bounds.mean_value:
                z_score = 0.0
            else:
                # Cap maximum possible anomaly score, when population values are identical and evaluated different
                z_score = MAX_Z_SCORE
        else:
            # Cap maximum possible anomaly score
            z_score = min(
                abs(evaluated_value - bounds.mean_value) / (bound_spread * 0.5) * self.threshold_std, MAX_Z_SCORE
            )

        return z_score

    def is_anomalous(self, z_score: float) -> bool:
        """Use anomaly scores to decide on prediction of anomalies."""
        return z_score > self.threshold_std

    @staticmethod
    def extrapolate_trend(trend: pandas.Series, npoints: int) -> pandas.Seris:
        """
        Fix original extrapolate trend method from seasonal_decompose of statsmodel library - wrong indexing.

        When periodicity is low i.e. 2, the trend was not extrapolated from the whole sequence,
        but only from one value, due to wrong setting of variable 'back' and the derivation of 'front_last' from it.
        Replace nan values on trend's end-points with least-squares extrapolated
        values with regression considering npoints closest defined points.
        """
        # Getting indexes on which to base extrapolation for the beginning and the end
        front = next(i for i, vals in enumerate(trend) if not numpy.any(numpy.isnan(vals)))
        back_plus_1 = trend.shape[0] - next(i for i, vals in enumerate(trend[::-1]) if not numpy.any(numpy.isnan(vals)))
        front_last = min(front + npoints, back_plus_1)
        back_first = max(front, back_plus_1 - npoints)

        # Finding linear extrapolation for the beginning of the trend using least squares
        k, n = numpy.linalg.lstsq(
            numpy.c_[numpy.arange(front, front_last), numpy.ones(front_last - front)], trend[front:front_last], rcond=-1
        )[0]
        extra = (numpy.arange(0, front) * numpy.c_[k] + numpy.c_[n]).T
        if trend.ndim == 1:
            extra = extra.squeeze()
        trend[:front] = extra

        # Finding linear extrapolation for the end of the trend using least squares
        k, n = numpy.linalg.lstsq(
            numpy.c_[numpy.arange(back_first, back_plus_1), numpy.ones(back_plus_1 - back_first)],
            trend[back_first:back_plus_1],
            rcond=-1,
        )[0]
        extra = (numpy.arange(back_plus_1, trend.shape[0]) * numpy.c_[k] + numpy.c_[n]).T
        if trend.ndim == 1:
            extra = extra.squeeze()
        trend[back_plus_1:] = extra

        # Rounding to get clean results, least squares give imprecise results due to optimization process
        return numpy.round(trend, TIME_SERIES_ROUNDING)
