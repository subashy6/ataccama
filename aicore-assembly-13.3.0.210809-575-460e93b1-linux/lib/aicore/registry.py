"""Central registry of AI Core machine-learning modules and microservices.

The module generally should not contain direct imports from microservices or their common parts as its used for
running individual microservices.

If needed, imports should be dynamic (as in `get_services`).
"""

from __future__ import annotations

import importlib
import itertools
import pathlib
import pkgutil

from aicore.common.exceptions import AICoreException


AICORE_PATH = pathlib.Path(__file__).parent
IGNORED_MODULES = ["management", "common"]


def _get_modules() -> tuple[list, dict, dict]:
    modules = []
    microservice_modules = {}
    job_modules = {}

    # `pkgutil` does not support pathlib.Path - paths have to be provided as strings
    for module in pkgutil.iter_modules([str(AICORE_PATH)]):
        if not module.ispkg or module.name in IGNORED_MODULES:
            continue

        modules.append(module.name)
        imported_module = importlib.import_module(f"aicore.{module.name}")

        try:
            microservice_modules[module.name] = imported_module.MICROSERVICES
        except AttributeError:
            job_modules[module.name] = imported_module.JOBS

    return modules, microservice_modules, job_modules


MODULES, MODULE_MICROSERVICES, MODULE_JOBS = _get_modules()
MICROSERVICE_NAMES = list(itertools.chain.from_iterable(MODULE_MICROSERVICES.values()))
JOB_NAMES = list(itertools.chain.from_iterable(MODULE_JOBS.values()))


class UnknownMicroserviceError(AICoreException):
    """Unknown microservice name was provided."""


# DAO import 'costs' 10MB of additional memory; should be imported only when needed
def get_dao() -> dict:
    """Provide DAOs of individual microservices."""
    from aicore.term_suggestions.database import TSDAO

    return {"ts": TSDAO}


def get_log_ids() -> dict:
    """Provide log IDs used by microservices."""
    app_log_ids = {}
    for module_name in [*MODULES, "common"]:
        try:
            log_ids = importlib.import_module(f"aicore.{module_name}.registry").LogId
        except AttributeError:
            continue

        app_log_ids[module_name] = log_ids

    return app_log_ids


def get_metrics() -> dict:
    """Provide metrics used by microservices."""
    app_metrics = {}
    for module_name in [*MODULES, "common"]:
        try:
            metrics = importlib.import_module(f"aicore.{module_name}.registry").METRICS
        except AttributeError:
            continue

        for metric in metrics:
            app_metrics[metric.__name_prefix__] = metric

    return app_metrics


def get_service(service_name: str) -> tuple[type, dict]:
    """Retrieve service class and its configuration."""
    modules = MODULE_MICROSERVICES
    service_module = "microservices"
    service_collection = "MICROSERVICES"

    if service_name in JOB_NAMES:
        modules = MODULE_JOBS
        service_module = "jobs"
        service_collection = "JOBS"

    for module_name, services in modules.items():
        if service_name in services:
            config_module = importlib.import_module(f"aicore.{module_name}.config")
            service_module = importlib.import_module(f"aicore.{module_name}.{service_module}")

            microservice = getattr(service_module, service_collection)[service_name]
            return microservice, config_module.CONFIG_OPTIONS

    raise UnknownMicroserviceError


def get_all_config_options() -> list:
    """Provide all microservices' configuration options."""
    from aicore.common.cli import CLIENT_CONFIG_OPTIONS as CLI_CLIENT_CONFIG_OPTIONS
    from aicore.common.cli import SERVER_CONFIG_OPTIONS as CLI_SERVER_CONFIG_OPTIONS

    configs = [CLI_CLIENT_CONFIG_OPTIONS, CLI_SERVER_CONFIG_OPTIONS]

    for module_name in itertools.chain(MODULE_MICROSERVICES, MODULE_JOBS):
        config_module = importlib.import_module(f"aicore.{module_name}.config")
        configs.append(config_module.CONFIG_OPTIONS)

    return configs


def collect_health_check_config_options():
    """Get config option necessary for composing health actuator url for all AI Core microservices."""
    options = {}

    for microservice_name in MICROSERVICE_NAMES:
        microservice_config = get_service(microservice_name)[1]

        for suffix in ["_host", "_http_port"]:
            key = f"{microservice_name}{suffix}"
            options[key] = microservice_config[key]

    return options
