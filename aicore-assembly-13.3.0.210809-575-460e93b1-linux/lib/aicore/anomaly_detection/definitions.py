"""Definitions of base classes e.g. anomaly detection result and model and category class."""
from __future__ import annotations

import abc

from enum import Enum
from typing import TYPE_CHECKING, ClassVar, NamedTuple

import numpy
import pandas

from aicore.common.exceptions import AICoreException


if TYPE_CHECKING:
    from typing import Iterator, Optional

    from aicore.anomaly_detection.types import (
        AnomalyDetectionWorkflow,
        AnomalyPrediction,
        AnomalyScore,
        CategoryData,
        CategoryName,
        Feedbacks,
        GenericHCNs,
    )

# Confidence bounds for a prediction - min bound, mean value (expected), max bound
ConfidenceBounds = NamedTuple("ConfidenceBounds", [("min_bound", float), ("mean_value", float), ("max_bound", float)])

# Result of Time series analysis model with score, prediction, and expected bounds (lower expected bound,
# expected value and upper expected bound) prescribed by the model
TimeSeriesFeatureResult = NamedTuple(
    "TimeSeriesFeatureResult", [("anomaly_score", float), ("prediction", bool), ("bounds", ConfidenceBounds)]
)

# Decomposed time series contains trend, season and residuals (errors), these are used for further analysis and anomaly
# detection.
TimeSeriesComponents = NamedTuple(
    "TimeSeriesComponents", [("trend", numpy.ndarray), ("seasonal", numpy.ndarray), ("residuals", numpy.ndarray)]
)

# Result of Isolation Forest model, including anomaly scores and anomaly predictions
IsolationForestFeatureResult = NamedTuple(
    "IsolationForestFeatureResult", [("anomaly_scores", numpy.ndarray), ("predictions", numpy.ndarray)]
)

# Feature result from an anomaly detector model for a given index of a data point, including anomaly score, predictions,
# category and expected bounds: (expected value, upper expected bound, and lower expected bound)
FeatureResultPerIndex = NamedTuple(
    "FeatureResultPerIndex",
    [("feature_name", str), ("score", float), ("prediction", bool), ("bounds", ConfidenceBounds)],
)


class AnomalyDetectionResultBase(abc.ABC):
    """Abstract Based Class for Anomaly Detection Result."""

    @abc.abstractmethod
    def get_score(self, index_from_end: int) -> AnomalyScore:
        """Get category score for a given index."""

    @abc.abstractmethod
    def get_prediction(self, index_from_end: int) -> AnomalyPrediction:
        """Get category prediction for a given index."""

    @abc.abstractmethod
    def iter_feature_results(self, index_from_end: int) -> Iterator[FeatureResultPerIndex]:
        """Get the feature results for the given index."""


class AnomalyDetectorModelBase(abc.ABC):
    """Base class for a model performing anomaly detection."""

    result_class: ClassVar[type[AnomalyDetectionResultBase]]

    def __init__(self, config, hcns: GenericHCNs):
        self.config = config
        self.result: Optional[AnomalyDetectionResultBase] = None
        self._hcns = hcns

        self.methods_per_category_type: dict[CategoryType, AnomalyDetectionWorkflow] = {}

    @property  # Models can modified list of history change numbers
    def hcns(self):
        """Get full history change numbers for all data points."""
        return self._hcns

    @abc.abstractmethod
    def min_data_length(self, category: Category) -> int:
        """Get minimal length of data for which anomaly detection model can be run."""

    def fit_and_predict(self, category: Category):
        """Detect anomalies for given model, only if the model is valid for given input."""
        if category.number_of_data_points < self.min_data_length(category):
            return

        methods_steps = self.methods_per_category_type[category.type]
        # None means that anomaly detection cannot be performed (category not supported)
        if methods_steps is None:
            return

        self.result = self.result_class()
        for model_method in methods_steps:
            model_method(category)

        category.result = self.result


class Category:
    """Main building block of anomaly detector, contains type, and data and other AD parameters."""

    def __init__(self, name: CategoryName, type: CategoryType, data: CategoryData):
        self.name = name
        self.type = type
        self.data = data

        self.indexes_of_confirmed_anomalous: list[int] = []
        self.periodicity: int = 0
        self.hcns: GenericHCNs = []
        self.result: Optional[AnomalyDetectionResultBase] = None

    @property
    def number_of_data_points(self) -> int:
        """Return number of used data points in the category."""
        return self.data.shape[0]

    @property
    def features(self):
        """Split category to individual features so that we can analyze each separately."""
        return {feature_name: pandas.Series(self.data[feature_name]) for feature_name in self.data.columns}

    def set_category_attributes(self, periodicity: int, feedbacks: Feedbacks):
        """Set attributes to category."""
        # For time series not containing seasonality (no repeating pattern) but only trend the periodicity is set to 2
        self.periodicity = 2 if periodicity == 1 else periodicity

        # Taking feedback only for the not-cut-off data points by accessing the list from the end
        feedbacks_cut_off = feedbacks[-self.number_of_data_points :]
        self.indexes_of_confirmed_anomalous = [index for index, feedback in enumerate(feedbacks_cut_off) if feedback]

    @staticmethod
    def get_usable_categories(categories: list[Category], index_from_end: int) -> list[Category]:
        """Return only categories which contain the given index i.e. there were not cut off for that index."""
        # Usable categories have initialized result i.e. AD model was used on them
        return [
            category for category in categories if index_from_end < category.number_of_data_points and category.result
        ]

    @staticmethod
    def any_anomalous_category(categories: list[Category], index_from_end) -> AnomalyPrediction:
        """Return whether there is any anomalous category in the data point."""
        usable_categories = Category.get_usable_categories(categories, index_from_end)
        return any(category.result.get_prediction(index_from_end) for category in usable_categories)

    @staticmethod
    def any_evaluated_category(categories: list[Category]) -> bool:
        """At least one category result was saved thus anomaly detection model was applied."""
        return any(category.result for category in categories)


class CategoryType(Enum):
    """Category types for anomaly detection defined based on the proto API communication."""

    GENERIC = 1
    FINGERPRINTS = 2  # Fingerprints are mapping of the data to hyper-dimensional space, sort of hashing
    FREQUENCIES = 3  # Most frequent and least frequent items or masks


class SeasonalDecomposeError(AICoreException):
    """Error in seasonal decomposition of time series which may indicate an issue with periodicity."""

    def __init__(self, periodicity: int):
        super().__init__(f"Error in seasonal decompose, periodicity was {periodicity}")


class Frequency:
    """Frequency type contains most frequent (head) and least frequent (tail) and row and distinct count.

    Frequencies can be created from actual values in the data, or masks (letters and digits) or patterns.
    """

    def __init__(self, head: dict, tail: dict, row_count: int, distinct_count: int):
        self.head = head
        self.tail = tail
        self.row_count = row_count
        self.distinct_count = distinct_count

    @property
    def percentage_head(self) -> dict:
        """Transform most frequent values to percentages given the total row count."""
        # Percentages in format in range 0.0 to 1.0
        return {key: value / self.row_count for key, value in self.head.items()}

    @property
    def percentage_tail(self) -> dict:
        """Transform least frequent values to percentages given the total row count."""
        # Percentages in format in range 0.0 to 1.0
        return {key: value / self.row_count for key, value in self.tail.items()}
