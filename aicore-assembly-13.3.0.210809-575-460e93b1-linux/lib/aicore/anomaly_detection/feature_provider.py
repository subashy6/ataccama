"""Feature provider for Anomaly Detection Module. Deserializer from protobuf messages to pandas dataframes."""
from __future__ import annotations

from typing import TYPE_CHECKING

import numpy
import pandas

from aicore.anomaly_detection.definitions import Category, CategoryType, Frequency
from aicore.anomaly_detection.proto import anomaly_detection_pb2 as ad_proto


if TYPE_CHECKING:
    from typing import Union

    from aicore.anomaly_detection.types import (
        DataContainerType,
        DeserializedData,
        DeserializerFunction,
        NumericDataType,
    )

MIN_FETCHED_DATA_POINTS = 2  # If number of profiles < 2, anomaly detection is skipped.

CATEGORIES_FROM_PROTO: dict[ad_proto.CategoryType.V, CategoryType] = {
    ad_proto.CategoryType.GENERIC: CategoryType.GENERIC,
    ad_proto.CategoryType.FINGERPRINTS: CategoryType.FINGERPRINTS,
    ad_proto.CategoryType.FREQUENCIES: CategoryType.FREQUENCIES,
}


class DataContainer:
    """Helper class for feature provider to deserialize intermediate data from proto message."""

    def __init__(self, category_type: CategoryType):
        self.category_type = category_type
        self.data: list[DeserializedData] = []


def deserialize_to_categories(response_with_data: list[ad_proto.GetHistoryResponse]) -> list[Category]:
    """Transform proto categorical data to pandas dataframes features."""
    if len(response_with_data) == 0:
        return []
    # We take the last (newest) data point which is a reference point for supported categories for AD
    supported_categories = get_supported_categories(response_with_data[-1])
    data_collection = {cat_name: DataContainer(cat_type) for cat_name, cat_type in supported_categories.items()}
    # We want to save only continuous data for a given category from the end,
    # thus if a category is supported by all data points except the one on index e.g. n-5, we save only last 4
    # and discard the other.
    supported_categories_bool = {category_name: False for category_name in supported_categories.keys()}

    for response in reversed(list(response_with_data)):
        for category in response.category_data:
            category_name = category.category_name
            # The sequence of a given category is interrupted so we make sure we don't save it from the rest of data
            if category_name not in supported_categories_bool.keys():
                continue
            # Only if a category is used then it's still supported for the next data points
            supported_categories_bool[category_name] = True

            data_collection[category_name].data.append(save_proto_data(category.statistics_values))

        # If a category does not appear in a data point it can no longer be saved - we want only continuous sequences
        # Setting default to False, only if present in the data point then a category can be still used
        supported_categories_bool = {
            category_name: False for category_name, supported in supported_categories_bool.items() if supported
        }

    category_collection = process_data_into_dataframes(data_collection)
    category_collection = reorder_and_prune_category_collection(category_collection)
    return category_collection


def get_supported_categories(last_data_point: ad_proto.GetHistoryResponse) -> dict[str, CategoryType]:
    """Find supported categories for anomaly detection, i.e. categories present in the last data point."""
    return {
        category.category_name: CATEGORIES_FROM_PROTO[category.category_type]
        for category in list(last_data_point.category_data)
    }


def deserialize_numeric(data_proto: NumericDataType) -> dict[str, Union[float, int]]:
    """Deserialize numeric proto map data to dictionary."""
    return dict(data_proto.dict)


def deserialize_double_array(data_proto: ad_proto.DoubleArray) -> dict[str, float]:
    """Deserialize numeric proto array data to dictionary with new keys."""
    features_names = ["feature" + str(index) for index in range(len(data_proto.array))]
    return {feature_name: value for feature_name, value in zip(features_names, data_proto.array)}


def deserialize_string_array(data_proto: ad_proto.StringArray) -> dict[str, float]:
    """Deserialize string proto array data to dictionary with new keys."""
    features_names = ["feature" + str(index) for index in range(len(data_proto.array))]
    try:
        data_dict = {feature_name: float(value) for feature_name, value in zip(features_names, data_proto.array)}
    except ValueError:  # AD is able to process only numerical values thus ignoring string values
        data_dict = {}
    return data_dict


def deserialize_frequencies(data_proto: ad_proto.Frequencies) -> Frequency:
    """Deserialize frequencies data to its own data object."""
    return Frequency(data_proto.head, data_proto.tail, data_proto.row_count, data_proto.distinct_count)


DESERIALIZERS: dict[type[DataContainerType], DeserializerFunction] = {
    ad_proto.DictStringInt32: deserialize_numeric,
    ad_proto.DictStringInt64: deserialize_numeric,
    ad_proto.DictStringDouble: deserialize_numeric,
    ad_proto.DoubleArray: deserialize_double_array,
    ad_proto.StringArray: deserialize_string_array,
    ad_proto.Frequencies: deserialize_frequencies,
}


def save_proto_data(statistics: ad_proto.Statistics) -> DeserializedData:
    """Save generic data type to pandas dataframe."""
    data_proto = getattr(statistics, statistics.WhichOneof("oneof_data"))
    deserializer = DESERIALIZERS[type(data_proto)]
    return deserializer(data_proto)


def process_data_into_dataframes(data_collection: dict[str, DataContainer]) -> list[Category]:
    """For all frequencies data process them to form feature collection."""
    category_collection: list[Category] = []
    for category_name, category_data in data_collection.items():
        if category_data.category_type == CategoryType.FREQUENCIES:
            dataframe = get_frequencies_features_from_multiple_data_points(category_data.data)
        else:
            dataframe = pandas.DataFrame(category_data.data)

        category_collection.append(Category(category_name, category_data.category_type, dataframe))
    return category_collection


def reorder_and_prune_category_collection(category_collection: list[Category]) -> list[Category]:
    """Sort feature collection by original order of received data points and remove empty dataframes."""
    # Reverse order because of saving the features from the newest to oldest data points
    # Sort the column alphabetically to make the whole AD module deterministic
    # Save dataframes which have more than 1 row - AD cannot be done on empty or single row dataframe
    category_collection_cleaned = []
    for category in category_collection:
        if category.number_of_data_points >= MIN_FETCHED_DATA_POINTS and not category.data.empty:
            category.data = category.data[::-1].reset_index(drop=True).sort_index(axis=1)
            category_collection_cleaned.append(category)

    return category_collection_cleaned


def get_frequencies_features_from_multiple_data_points(
    frequencies_all_profiles: list[Frequency],
) -> pandas.DataFrame:
    """Find all the unique frequent item keys and use them to create the dataframe."""
    frequent_items_keys: set[str] = set()
    for frequency_per_profile in frequencies_all_profiles:
        # If any profile has empty frequency we do not save frequencies at all i.e. return empty dataframe
        if not frequency_per_profile.head and not frequency_per_profile.tail:
            return pandas.DataFrame()

        frequent_items_keys.update(frequency_per_profile.head.keys())
        frequent_items_keys.update(frequency_per_profile.tail.keys())

    return get_compound_frequencies_over_data_points(frequencies_all_profiles, frequent_items_keys)


def get_compound_frequencies_over_data_points(
    frequencies_all_profiles: list[Frequency], frequent_items_keys: set
) -> pandas.DataFrame:
    """Create dataframe with a proper format, using all the frequencies and their unique keys."""
    compound_frequencies = pandas.DataFrame(columns=frequent_items_keys, dtype=int)
    for frequency_per_profile in frequencies_all_profiles:
        frequency_combined, estimate_for_missing_key = process_frequency(frequency_per_profile)

        # If a key is missing in the dict then use the estimated default value
        frequency_with_defaults = {
            frequent_item_key: frequency_combined.get(frequent_item_key, estimate_for_missing_key)
            for frequent_item_key in frequent_items_keys
        }
        compound_frequencies = compound_frequencies.append(frequency_with_defaults, ignore_index=True)

    return compound_frequencies


def process_frequency(frequency: Frequency) -> tuple[dict[str, float], float]:
    """Check whether row count and distinct count were provided for frequency and process accordingly."""
    # If row count or distinct count is zero, it likely means it was not sent, then only combine head and tail
    if not frequency.row_count or not frequency.distinct_count:
        return frequency.head | frequency.tail, 0.0

    # Get percentage from expected missing occurrences
    estimated_for_missing_percentage = estimate_expected_missing_frequency(frequency) / frequency.row_count

    # Transform occurrences to percentages (in format in range 0.0 to 1.0) using row count
    # Combine both head and tail frequencies
    frequency_combined = frequency.percentage_head | frequency.percentage_tail
    return frequency_combined, numpy.round(estimated_for_missing_percentage, 4)


def estimate_expected_missing_frequency(frequency: Frequency) -> float:
    """Compute expected missing value from frequency most and least frequent values and row and distinct count."""
    total_recorded_occurrences = sum(frequency.head.values()) + sum(frequency.tail.values())
    missing_occurrences_total = frequency.row_count - total_recorded_occurrences
    missing_number_of_keys = frequency.distinct_count - (len(frequency.head) + len(frequency.tail))

    # Expectation for a missing key, missing mass divided by the number of missing, if no missing then 0
    estimated_occurrences_for_missing_key = (
        missing_occurrences_total / missing_number_of_keys if missing_number_of_keys else 0
    )
    return numpy.round(estimated_occurrences_for_missing_key, 4)
