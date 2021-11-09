"""Abbreviations for commonly used types."""
from __future__ import annotations

from typing import TYPE_CHECKING

import aicore.anomaly_detection.proto.anomaly_detection_pb2 as ad_proto


if TYPE_CHECKING:
    from typing import Any, Callable, Optional, Union

    import numpy
    import pandas

    from aicore.anomaly_detection.definitions import Category, Frequency

    GenericId = str  # Generic id, can be attribute profile id or catalog id or potentially other id
    GenericHCN = int  # Generic history change number
    EntityType = str  # Type of entity - fetched data, e.g. catalog-level, attribute-level, DQ rule
    GenericHCNs = list[GenericHCN]

    Feedbacks = list[bool]  # Feedback for each fetched data instance, True means confirmed anomalous by the user

    NumericDataType = Union[ad_proto.DictStringInt32, ad_proto.DictStringInt64, ad_proto.DictStringDouble]
    DataContainerType = Union[
        NumericDataType,
        ad_proto.StringArray,
        ad_proto.DoubleArray,
    ]

    AnomalyScore = float  # How much a feature is anomalous
    AnomalyScores = numpy.ndarray  # How much a feature is anomalous
    AnomalyPrediction = bool  # True if the result is anomalous, False otherwise
    AnomalyPredictions = numpy.ndarray  # True if the result is anomalous, False otherwise
    CategoryName = str  # Name of the category of features
    FeatureName = str  # Name of individual feature

    # Union is here to convince mypy that this is a type alias and not variable assignment,
    # see https://github.com/python/mypy/issues/8674
    CategoryData = Union[pandas.DataFrame]
    CategoryFeatureData = pandas.Series

    # Describes anomaly detection method steps (which are applied to particular category)
    # None means that anomaly detection cannot be performed (category not supported)
    AnomalyDetectionWorkflow = Optional[list[Callable[[Category], None]]]

    DeserializedData = Union[dict[str, float], Frequency]
    DeserializerFunction = Callable[[Any], DeserializedData]
