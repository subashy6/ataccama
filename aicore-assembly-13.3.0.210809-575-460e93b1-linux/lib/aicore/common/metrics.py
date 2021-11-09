"""Application-specific metrics compatible with Prometheus."""

from __future__ import annotations

import contextlib
import enum
import types

from typing import TYPE_CHECKING, Optional

import prometheus_client

from aicore.common.exceptions import AICoreException


if TYPE_CHECKING:
    from typing import Callable, Iterable


class UnknownMetricError(AICoreException):
    """Exception for encountering an unknown metric."""

    def __init__(self, metric: MetricEnum):
        super().__init__(f"Metric '{metric}' has not been registered")


class MetricType(enum.Enum):
    """Enum of all available metric types."""

    info = prometheus_client.Info
    counter = prometheus_client.Counter
    gauge = prometheus_client.Gauge
    histogram = prometheus_client.Histogram
    summary = prometheus_client.Summary


class MetricEnum(enum.Enum):
    """Base class for enums containing used metrics.

    Example entries:
        example_metric_name1 = (MetricType.counter, "Metric description")
        example_metric_name2 = (MetricType.counter, "Metric description", ["label1", ...])
        example_metric_name3 = (MetricType.counter, "Metric description", ["label1", ...], {"kwarg1": kwarg1_value})
    """

    __name_prefix__ = ""  # Common prefix to all metrics defined in an enum, see full_name()
    __platform_prefix__ = "ataccama_one_aicore"  # Company-wide prefix to all metrics emitted by the component

    def __init__(
        self, type_: MetricType, description: str, labels: Optional[list[str]] = None, kwargs: Optional[dict] = None
    ):
        self.type = type_
        self.description = description
        self.labels = labels or []
        self.kwargs = kwargs or {}

    @types.DynamicClassAttribute  # Allow enum member named "full_name", otherwise same as @property
    def full_name(self) -> str:
        """Return prefixed name of the metric, presentable to Prometheus."""
        metric_name = f"{self.__name_prefix__}_{self.name}" if self.__name_prefix__ else self.name
        return f"{self.__platform_prefix__}_{metric_name}"


class MetricsDAO:
    """Wrapper for Prometheus metrics stored in a local registry.

    Basic KnowHow on Prometheus Python Client -> https://github.com/prometheus/client_python#instrumenting

    Best Practices:
        - https://prometheus.io/docs/concepts/metric_types/
        - https://prometheus.io/docs/practices/instrumentation/#counter-vs-gauge-summary-vs-histogram
        - https://prometheus.io/docs/practices/histograms/
        - https://prometheus.io/docs/practices/naming/

    Cheatsheet for selecting a metric type:
        - can go up and be reset (requests served, tasks completed)               -->  Counter
        - can go up and down, can be set (current memory used, current requests)  -->  Gauge
        - can provide a histogram + counts/sums (request duration/size/codes)     -->  Histogram
        - can provide counts/sums (without histogram)                             -->  Summary

    Cheatsheet for metric naming:
        - should be prefixed with the relevant domain (http, grpc, process, db)
        - should have a single unit (no seconds and bytes in same metric)
        - should be suffixed with chosen unit in plural if applicable (seconds, bytes, info, total)

        Examples: http_request_duration_seconds, process_memory_usage_bytes, http_requests_total, microservice_info

    Cheatsheet for label naming:
        - should represent the same logical thing-being-measured as the metric

        Examples: grpc_command_count[type], http_request_total[status], db_query_seconds[operation]
    """

    def __init__(self):
        self.metrics = {}
        self.registry = prometheus_client.CollectorRegistry(auto_describe=True)

        prometheus_client.ProcessCollector(registry=self.registry)
        prometheus_client.PlatformCollector(registry=self.registry)
        prometheus_client.GCCollector(registry=self.registry)

    def register(self, metrics: Iterable[MetricEnum]):
        """Create and cache the provided metrics."""
        for metric in metrics:
            if metric.full_name not in self.metrics:
                metric_class = metric.type.value
                self.metrics[metric.full_name] = metric_class(
                    metric.full_name,
                    metric.description,
                    metric.labels,
                    registry=self.registry,
                    **metric.kwargs,
                )

    def add_info(self, metric: MetricEnum, **kwargs):
        """Register the provided info on the specified Info metric."""
        self._get(metric).info(kwargs)

    def increment(self, metric: MetricEnum, amount: float = 1, **labels):
        """Increment specified Counter/Gauge metric."""
        self._get(metric, **labels).inc(amount)

    def observe(self, metric: MetricEnum, amount: float, **labels):
        """Observe the given amount by the specified Histogram/Summary metric."""
        self._get(metric, **labels).observe(amount)

    def set_callback(self, metric: MetricEnum, function: Callable[[], float], **labels: str):
        """Set callback which lazily provides the value of the specified Gauge metric.

        Typically useful for third party code which can't be modified.
        """
        self._get(metric, **labels).set_function(function)

    def set_value(self, metric: MetricEnum, value: float, **labels):
        """Set the specified Gauge metric to the given value."""
        self._get(metric, **labels).set(value)

    @contextlib.contextmanager
    def measure_time(self, metric: MetricEnum, **labels):
        """Measure time through the specified Gauge/Histogram/Summary metric."""
        with self._get(metric, **labels).time():
            yield

    def _get(self, metric: MetricEnum, **labels):
        """Retrieve the specified metric."""
        try:
            metric_instance = self.metrics[metric.full_name]
        except KeyError:
            raise UnknownMetricError(metric) from None

        if labels:
            metric_instance = metric_instance.labels(**labels)

        return metric_instance

    def __repr__(self):
        return repr(list(self.registry.collect()))

    # Inspired by prometheus_client.exposition.make_wsgi_app()
    def dump(self, format_type, query):
        """Serialize metrics from a local registry to the requested format."""
        registry = self.registry
        if "name[]" in query:
            registry = registry.restricted_registry(query["name[]"])

        if format_type == "prometheus_plaintext":  # See https://prometheus.io/docs/instrumenting/exposition_formats
            encoder = prometheus_client.exposition.generate_latest
            content_type = prometheus_client.exposition.CONTENT_TYPE_LATEST
        else:  # "openmetrics_plaintext", see https://github.com/OpenObservability/OpenMetrics
            encoder = prometheus_client.openmetrics.exposition.generate_latest
            content_type = prometheus_client.openmetrics.exposition.CONTENT_TYPE_LATEST

        return encoder(registry), content_type
