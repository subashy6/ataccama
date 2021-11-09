"""Utility classes and functions."""

from __future__ import annotations

import datetime
import os
import pathlib
import re
import signal
import sys
import threading
import uuid

from typing import TYPE_CHECKING

import psutil
import setproctitle
import threadpoolctl

from aicore.common.exceptions import AICoreException


# Do not import machine learning libraries here! (would disable limits for number of threads they may spawn)


if TYPE_CHECKING:
    from collections.abc import Callable
    from types import FrameType
    from typing import Optional

    from aicore.common.types import CorrelationId, EntityId

# Earliest representable timezone-aware `datetime` object
DATETIME_MIN = datetime.datetime.min.replace(tzinfo=datetime.timezone.utc)


class NaiveDatetimeError(AICoreException):
    """Datetime without time zone encountered."""


def random_correlation_id() -> CorrelationId:
    """Create a random correlation id."""
    # Java implementation uses UUID.randomUUID().toString().substring(30), toString() adds 4 hyphens
    # See also https://bitbucket.atc.services/projects/DEV-LIBS/repos/logging/browse/modules/ata-logging-context/src/main/java/com/ataccama/lib/logging/context/UUIDCorrelationIdGenerator.java#9  # noqa: E501
    return str(uuid.uuid4())[30:]  # Last 6 characters of Java UUID, see comments for UUID_SIZE


def serialize_entity_id(entity_id: EntityId) -> str:
    """Convert entity id from UUID format to string representation."""
    return str(entity_id)


def deserialize_entity_id(entity_id: str) -> EntityId:
    """Convert entity id from string to UUID format."""
    return uuid.UUID(entity_id)


def handle_shutdown_signals(signal_handler: Callable[[int, FrameType], None]) -> None:
    """Register signal handler for shutdown signals.

    Note: signals can be registered only by and are always handled in the main thread.
        https://docs.python.org/3/library/signal.html#signals-and-threads
    """
    if sys.platform == "win32":
        # (letters reference the module docstring in supervisor.py)
        # SIGTERM is useless (see f)), additionally SIGBREAK is used due to b) and c)
        handled_signals = [signal.SIGINT, signal.SIGBREAK]
    else:
        handled_signals = [signal.SIGINT, signal.SIGTERM]

    for signal_num in handled_signals:
        signal.signal(signal_num, signal_handler)


def get_signal_name(signal_num: int) -> str:
    """Return signal name given its number; return empty string for unknown signal number."""
    try:
        return signal.Signals(signal_num).name
    except ValueError:
        return ""


def set_process_title(service_name: str, service_version: str) -> None:
    """Set title of the current process."""
    setproctitle.setproctitle(f"Ataccama One 2.0 - AI Core - {service_name}:{service_version}")


def set_event_after(interval: float, event: Optional[threading.Event] = None) -> threading.Event:
    """Set an event after interval, no-op if it becomes set sooner; optionally create such event if none specified."""
    event = event or threading.Event()
    # Not using threading.Timer as it doesn't support "name" and "daemon" args
    threading.Thread(target=lambda: event.wait(interval) or event.set(), name="set_event_after", daemon=True).start()
    return event


def timestamp_str(timestamp: int, timespec: str = "seconds") -> str:
    """Format a (UTC) timestamp as ISO8601 string."""
    if timestamp == -1:
        return "Never updated"

    return datetime_str(datetime_fromtimestamp(timestamp), timespec)


def datetime_str(utc_datetime: datetime.datetime, timespec: str = "auto") -> str:
    """Format an aware datetime in UTC as ISO8601 string."""
    if utc_datetime.utcoffset() != datetime.timedelta():
        raise ValueError("expected a datetime.datetime with UTC timezone")

    # There is no hard rule for using numerical or the Z suffix - https://tools.ietf.org/html/rfc3339#page-3
    # The Z suffix is preferred throughout AI-Core
    return f"{utc_datetime.replace(tzinfo=None).isoformat(timespec=timespec)}Z"


def load_version(version_txt_location: str) -> str:
    """Load version of AI Core from artifact-version.txt file."""
    with open(version_txt_location) as file:
        return file.readline().strip()


# Limits for number of threads spawned by machine-learning
# - Beware of silent re-ordering of imports by Isort or moving the setting limits
# - Beware of CPU affinity silently set by the infrastructure (Docker, virtualization, NUMA or customer's admin tooling)
# - Beware of NUMA systems (limit threads to local CPU cores and local memory if bigger than NUMA stride, otherwise 1)
# - "jobs" property is used inside the machine-learning algorithms whose libraries expose "n_jobs" argument (Joblib)
# - Dynamic API has higher overhead than static API (spawns more threads that configured limit)
# - Only real CPU cores speed up CPU-bound calculations (hyper-threads share CPU caches)
# - CPU affinity is ignored when auto-detecting via cpu_count() (but psutil's cpu_affinity counts hyper-threads)
# - Default thread limits will use all available CPU cores (including hyper-threads)

# See also:
# - https://github.com/joblib/threadpoolctl#setting-the-maximum-size-of-thread-pools
# - https://joblib.readthedocs.io/en/latest/parallel.html#avoiding-over-subscription-of-cpu-resources
# - https://github.com/xianyi/OpenBLAS/tree/master#set-the-number-of-threads-with-environment-variables


def set_static_thread_limits(omp=None, blas=None):
    """Limit the number of threads spawned by machine-learning libraries via static API (environment variables)."""
    if omp is None and blas is None:
        return  # Do not use the static API

    if "numpy" in sys.modules:
        # NumPy reads environment variables upon import and sets thread limits for OpenBLAS and LAPACK
        raise Exception("NumPy must be imported AFTER setting the static thread limits")

    omp = resolve_cpu_count(omp)
    blas = resolve_cpu_count(blas)

    if omp:  # OpenMP (for nested parallelism with Joblib's "Loky" executor - each process uses OpenBLAS with threads)
        os.environ["OMP_NUM_THREADS"] = str(omp)  # The preferred way of configuring the thread limits

    if blas:  # OpenBLAS (matrix multiplication) and LAPACK (FFT and linear solvers/decomposition) used by NumPy/SciPy
        os.environ["OPENBLAS_NUM_THREADS"] = str(blas)


def resolve_cpu_count(desired_cpu_count: Optional[int]):
    """Get CPU count based on real CPUs and desired number of CPUs."""
    if desired_cpu_count is None:
        return desired_cpu_count

    real_cpu_count = psutil.cpu_count(logical=False)

    if desired_cpu_count == 0:
        return real_cpu_count

    if desired_cpu_count < 0:
        return max(real_cpu_count + desired_cpu_count, 1)

    return min(desired_cpu_count, real_cpu_count)


def set_dynamic_thread_limits(threads=None):
    """Limit the number of threads spawned by machine-learning libraries via dynamic C-API."""
    if threads is None:
        return  # Do not use the dynamic API

    if "numpy" not in sys.modules:
        # threadpoolctl library sets the limits only to ML libraries that are already imported
        raise Exception("NumPy must be imported BEFORE setting the dynamic thread limits")

    # Supports OpenMP and BLAS which are used by NumPy/SciPy/Scikit-Learn
    threadpoolctl.threadpool_limits(threads or psutil.cpu_count(logical=False))


def get_thread_limits():
    """Get the current limits of number of threads spawned by machine-learning libraries."""
    thread_limits = {}

    for library in threadpoolctl.threadpool_info():
        path_parts = pathlib.Path(library["filepath"]).parts
        path_index = path_parts.index("site-packages") + 1
        library_name = path_parts[path_index].split(".libs")[0]
        thread_limits[library_name] = (
            library["num_threads"],
            (library["prefix"], library["version"], library.get("threading_layer")),
        )  # Useful for checking the auto-detected number of CPU cores and discovering over-subscription

    return thread_limits


def ant_path_to_regex(ant_path: str):
    """Convert ant-style path to regex.

    Ant-path pattern:
      ? matches one character
      * matches zero or more characters
      ** matches zero or more directories in a path
    """
    pattern = ant_path.replace("/", r"\/")  # Escape path separator (e.g. for /aaa/bbb)
    pattern = pattern.replace(".", r"\.")  # Escape dot (e.g. for /aaa/file.jpg)
    # Replace single * (not preceded and not succeeded by *) with anything that is not a path separator
    # (e.g. for /aaa/*/file.jpg)
    pattern = re.sub(r"(?<!\*)\*(?!\*)", r"[^\/]+", pattern)
    pattern = pattern.replace("?", r"\w")  # Use word character (e.g. for /aaa/file.???)

    return pattern.replace("**", r".*")  # Zero or more directories = anything (e.g. for /aaa/**/file.jpg)


def datetime_now() -> datetime.datetime:
    """Get the current UTC time as timezone-aware `datetime` object."""
    # utcnow is naive and is not recommended - https://docs.python.org/3/library/datetime.html#datetime.datetime.utcnow
    return datetime.datetime.now(tz=datetime.timezone.utc)


def datetime_fromtimestamp(timestamp: float) -> datetime.datetime:
    """Get the current UTC time as timezone-aware `datetime` object from a timestamp."""
    # utcfromtimestamp is naive and is not recommended
    # https://docs.python.org/3/library/datetime.html#datetime.datetime.utcfromtimestamp
    return datetime.datetime.fromtimestamp(timestamp, tz=datetime.timezone.utc)


def datetime_to_utc(aware_datetime: datetime.datetime) -> datetime.datetime:
    """Transform aware `datetime` to `datetime` with UTC timezone."""
    if not aware_datetime.tzinfo:
        raise NaiveDatetimeError("Expected datetime with timezone")

    return aware_datetime.astimezone(tz=datetime.timezone.utc)


def human_readable_size(size_bytes: int, precision: int = 2) -> str:
    """Return a human-readable representation of a size given in bytes."""
    if size_bytes < 1000:
        return f"{size_bytes} B"

    size = size_bytes
    for prefix in ("k", "M", "G", "T", "P", "E"):
        size = round(size / 1000.0, precision)
        if size < 1000.0:
            break

    return f"{size:.{precision}f} {prefix}B"
