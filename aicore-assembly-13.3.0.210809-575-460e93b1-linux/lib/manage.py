#! /usr/bin/env python

"""Command-line utilities for managing the application and its infrastructure."""

from __future__ import annotations

import enum
import functools

import typer  # Additional imports are done inside individual command functions to allow bootstrapping via 'install'

from aicore.common.exceptions import AICoreException


# Do not import this module anywhere in the code!

DEFAULT_DB = "ai"
DEFAULT_USER = "one"
DEFAULT_CONNECTION_STRING = f"postgresql://{DEFAULT_USER}:one@localhost:5431/postgres"
AI_CORE_API_REPO_PATH = "../ai-core-api"
CONFIGURATION_SERVICE_API_REPO_PATH = "../../cs/onecfg-api"
PYTHON_VERSION = "3.9.5"

CONFIG_SERVICE_JSON_PATH = "doc/configService.json"
LICENSES_README_PATH = "doc/README-licenses.md"
METRICS_README_PATH = "doc/README-metrics.md"
PROPERTIES_README_PATH = "doc/README-properties.md"
ETC_APPLICATION_PROPERTIES_PATH = "etc/application.properties"
DEFAULT_APPLICATION_PROPERTIES_PATH = "lib/application.properties"

EXIT_CODE_SUCCESS = 0
EXIT_CODE_FAILURE = 1
EXIT_CODE_SOFT_FAILURE = 2

app = typer.Typer()


class SchemaOperation(str, enum.Enum):
    """Supported DDL operations for management of a database."""

    create = "create"
    drop = "drop"
    truncate = "truncate"
    upgrade = "upgrade"
    version = "version"

    @classmethod
    def is_migration(cls, operation):
        """Indicate whether given operation is a database migration."""
        return operation in {cls.upgrade, cls.version}


class PostgreSQLDatabaseOperation(str, enum.Enum):
    """Supported DDL operations for management of PostgreSQL databases."""

    create = "create"
    drop = "drop"


class BuildType(str, enum.Enum):
    """Supported types of application builds."""

    package = "package"
    minimal_package = "minimal_package"
    docker_package = "docker_package"
    docker_image = "docker_image"


class DatabaseType(str, enum.Enum):
    """Vendor of the database backend."""

    postgres = "postgres"
    oracle = "oracle"
    mssql = "mssql"


class CheckType(str, enum.Enum):
    """Code checks available for execution."""

    typing = "typing"
    linting = "linting"
    marks = "marks"
    config = "config"
    licenses = "licenses"


class Runtime(str, enum.Enum):
    """Run from the source code or in a Docker container."""

    docker = "docker"
    native = "native"


class BenchmarkedAlgorithm(str, enum.Enum):
    """Machine-learning algorithm measured for speed based on given thread limits."""

    neighbors = "neighbors"  # NeighborsCalculator - uses Joblib with thread-pool executor
    isolation_forest = "isolation_forest"  # IsolationForestModel - uses Joblib with "Loky" process executor
    time_series = "time_series"  # TimeSeriesAnalysisModel - uses LAPACK/OpenBLAS with threads
    dot = "dot"  # numpy.dot() - uses OpenBLAS with threads
    norm = "norm"  # scipy.linalg.norm() - uses OpenBLAS with threads
    # Add more machine-learning algorithms as needed


class ProtoAPI(str, enum.Enum):
    """Available API types for protobuf generation."""

    all = "all"
    configuration_service = "onecfg-api"
    ai_core = "ai-core-api"


def run_repl(namespace):
    """Run an interactive Python shell."""
    try:
        import IPython
        import traitlets.config

        config = traitlets.config.Config({})
        config.InteractiveShell.xmode = "Verbose"  # See the line magic %xmode
        IPython.start_ipython(user_ns=namespace, argv=["--no-confirm-exit"], config=config)

    except ImportError:
        import code

        code.interact(local=namespace)


def docker_compose(services: list[str], build: bool = False):
    """Create a Docker Compose command."""
    import compose.cli.main

    options = {
        "SERVICE": services,
        "--detach": False,
        "--no-deps": False,
        "--always-recreate-deps": False,
        "--abort-on-container-exit": False,
        "--remove-orphans": False,
        "--no-recreate": False,
        "--force-recreate": False,
        "--no-build": False,
        "--build": build,
        "--scale": [],
        "--no-color": False,
        "--no-log-prefix": False,
    }

    project = compose.cli.main.project_from_options(".", {})
    command = compose.cli.main.TopLevelCommand(project)

    return command, options


def create_microservice(microservice_name):
    """Create given microservice using configuration from given URL."""
    from aicore.common.config import Config
    from aicore.registry import JOB_NAMES, MICROSERVICE_NAMES, UnknownMicroserviceError, get_service

    try:
        microservice_class, config_options = get_service(microservice_name)  # Beware, can import NumPy
    except UnknownMicroserviceError:
        typer.echo(
            f"Microservice {microservice_name!r} not found.\nSupported microservices: {MICROSERVICE_NAMES!r}\n Supported jobs: {JOB_NAMES!r}\n Supported commands: ['infra', 'db', 'keycloak', 'all']"  # noqa: E501
        )
        exit(1)

    config = Config.from_all_sources(microservice_name, config_options)
    return microservice_class(config)


def compile_protobuf_file(source_folder, proto_file_name, target_module, workdir):
    """Compile the definition of gRPC service for given module into protobuf message descriptors."""
    import shutil
    import subprocess
    import sys

    shutil.copy(f"{source_folder}/{proto_file_name}.proto", workdir)

    # Importing the protobuf compiler as Python module would break the import path handling even more
    subprocess_args = [
        sys.executable,  # Python executable name in Jenkins build image may differ from default 'python'
        "-m",
        "grpc_tools.protoc",
        "--proto_path=.",
        "--python_out=.",
        "--mypy_out=.",
        f"{proto_file_name}.proto",
    ]
    result = subprocess.run(subprocess_args, cwd=workdir)

    if result.returncode:
        exit(f"Protobuf compiler failed to process {proto_file_name}")

    source_file_without_extension = f"{workdir}/{proto_file_name}_pb2"
    target_dir = f"aicore/{target_module}/proto"
    for ext in (".py", ".pyi"):
        shutil.copy(source_file_without_extension + ext, target_dir)


def update_api_version(repo_path, api_type):
    """Update version.txt with version of API."""
    import re
    import subprocess
    import sys

    with open(f"{repo_path}/version.txt", "r") as file:
        version = file.read().rstrip("\n")

    commit_hash = subprocess.run(
        args=["git", "rev-parse", "HEAD"], capture_output=True, text=True, encoding=sys.stdout.encoding, cwd=repo_path
    ).stdout.strip()

    with open("version-api.txt", "r") as file:
        data = file.read()

    data = re.sub(f"{api_type} version.txt content: .*", f"{api_type} version.txt content: {version}", data)
    data = re.sub(f"{api_type} commit hash: .*", f"{api_type} commit hash: {commit_hash}", data)

    with open("version-api.txt", "w") as file:
        file.write(data)


def compile_ai_core_protobuf_module(module_name, workdir):
    """Compile the definition of gRPC service for given module into protobuf message descriptors."""
    java_module = module_name.replace("_", "-")  # Naming convention for Java modules requires dashes
    source_folder = f"{AI_CORE_API_REPO_PATH}/modules/{java_module}/src/main/proto/ataccama/aicore/{module_name}"

    compile_protobuf_file(source_folder, module_name, module_name, workdir)


def compile_cs_protobuf(workdir):
    """Compile the definition of gRPC service for Configuration Service into protobuf message descriptors."""
    source_folder = f"{CONFIGURATION_SERVICE_API_REPO_PATH}/modules/onecfg-api/src/main/proto"

    for proto_file_name in ["ClientService", "PropertyService"]:
        compile_protobuf_file(source_folder, proto_file_name, "common", workdir)


def check_typing():
    """Run typing check on AI-Core code."""
    import subprocess
    import sys

    result = subprocess.run([sys.executable, "-m", "mypy"])

    return result.returncode


def check_linting():
    """Run linting check on AI-Core code."""
    import flake8.main.application

    linter = flake8.main.application.Application()
    linter.run(["."])
    typer.echo(linter.result_count)

    if linter.result_count:
        typer.echo("The code is not clean according to flake8 - fix the issues and retry")
        return EXIT_CODE_FAILURE

    return EXIT_CODE_SUCCESS


def check_marks():
    """Check if all tests of AI-Core code are marked."""
    import re
    import subprocess
    import sys

    process_args = [
        sys.executable,
        "-m",
        "pytest",
        "--collect-only",
        "--no-summary",
        "--no-header",
        "-m",
        # No brackets required due to how the args list is parsed
        "not unit and not component and not integration and not math",
    ]
    result = subprocess.run(args=process_args, capture_output=True)
    output = result.stdout.decode(sys.stdout.encoding)

    try:
        collected_tests = re.findall("collected (\\d+) items", output)[0]
        deselected_tests = re.findall("\\/ (\\d+) deselected", output)[0]
    except IndexError:
        typer.echo(f"Failed to parse pytest output:\n{output}")
        return EXIT_CODE_FAILURE

    if collected_tests != deselected_tests:
        typer.echo(
            f"{output}\n{int(collected_tests) - int(deselected_tests)} tests are missing the @pytest.mark decorator"
        )
        return EXIT_CODE_FAILURE

    return EXIT_CODE_SUCCESS


def check_config():
    """Check if all files connected to AI-Core properties were properly generated."""
    from aicore.common.config import ConfigurationError
    from aicore.management.config import (
        check_default_values,
        generate_application_properties_content,
        generate_config_json_content,
        generate_readme_content,
    )

    try:
        check_default_values(ETC_APPLICATION_PROPERTIES_PATH)
    except ConfigurationError as error:
        typer.echo(error)
        return EXIT_CODE_FAILURE

    for path, content_generator in {
        DEFAULT_APPLICATION_PROPERTIES_PATH: generate_application_properties_content,
        PROPERTIES_README_PATH: generate_readme_content,
        CONFIG_SERVICE_JSON_PATH: generate_config_json_content,
    }.items():
        generated_content = content_generator()

        with open(path) as file:
            file_content = file.read()

        if generated_content != file_content:
            typer.echo("There are some changes in the properties file, regenerate it via `python manage.py config`")
            return EXIT_CODE_FAILURE

    return EXIT_CODE_SUCCESS


def check_licenses():
    """Check if license file was properly generated."""
    import io

    from aicore.management.licenses import generate_licenses_content, get_all_licenses

    package_licenses = get_all_licenses(include_development=False)

    with io.StringIO() as generated_file:
        generate_licenses_content(package_licenses, generated_file)

        generated_file.seek(0)
        generated_content = generated_file.read()

    with open(LICENSES_README_PATH) as file:
        file_content = file.read()

    if generated_content != file_content:
        typer.echo("There are some changes in the licenses file, regenerate it via `python manage.py licenses`")
        return EXIT_CODE_FAILURE

    return EXIT_CODE_SUCCESS


@app.command()
def install(dev: bool = True, user: bool = False):
    """Install all PIP packages required for the development."""
    import subprocess
    import sys

    # https://pip.pypa.io/en/stable/user_guide/?highlight=_internal#using-pip-from-your-program
    subprocess_args = [sys.executable, "-m", "pip", "install", "-r", "requirements.txt"]

    if dev:
        subprocess_args.extend(["-r", "requirements_dev.txt"])

    if user:
        subprocess_args.append("--user")

    subprocess.check_call(args=subprocess_args)  # raise in case subprocess returns non-zero


@app.command()
def upgrade():
    """Upgrade all PIP packages required for the development."""
    import subprocess
    import sys

    subprocess_args = [
        sys.executable,
        "-m",
        "pip",
        "install",
        "-U",
        "-r",
        "requirements.txt",
        "-r",
        "requirements_dev.txt",
    ]

    subprocess.check_call(subprocess_args)  # raise in case subprocess returns non-zero


@app.command()
def schema(operation: SchemaOperation):
    """Modify the database schema."""
    from aicore.common.config import DB_CONFIG_OPTIONS, PATHS_OPTIONS, get_config
    from aicore.common.database import create_database
    from aicore.common.registry import LogId
    from aicore.management.config import alembic_config
    from aicore.registry import get_dao

    if SchemaOperation.is_migration(operation):
        if operation == SchemaOperation.upgrade:
            import alembic

            config = get_config(PATHS_OPTIONS, DB_CONFIG_OPTIONS)
            migrations_config = alembic_config(config.connection_string, config.migrations_path)
            alembic.command.upgrade(migrations_config, "head")
        elif operation == SchemaOperation.version:
            database = create_database()
            typer.echo(database.get_current_schema_version())
    else:
        database = create_database()

        if operation == SchemaOperation.drop:
            database.drop_all_tables()

            database.logger.warning("Database schema dropped", message_id=LogId.db_drop)

        elif operation == SchemaOperation.create:
            import alembic

            # Create the tables using table definitions in the DAOs, not in migration scripts
            # Use migration scripts only for creating older schema versions when testing the migrations
            for dao_class in get_dao().values():
                dao = dao_class(database)
                dao.create_tables()

            # Set the database schema to the latest available revision
            config = get_config(PATHS_OPTIONS, DB_CONFIG_OPTIONS)
            migrations_config = alembic_config(config.connection_string, config.migrations_path)
            alembic.command.stamp(migrations_config, "head")

            database.logger.info("Database schema created", message_id=LogId.db_create, _color="<white><bold>")

        elif operation == SchemaOperation.truncate:
            for dao_class in get_dao().values():
                dao = dao_class(database)
                dao.truncate_tables()

            database.logger.warning("All tables were truncated", message_id=LogId.db_truncate)


@app.command()
def ci_postgres(
    operation: PostgreSQLDatabaseOperation,
    connection_string: str = typer.Argument(DEFAULT_CONNECTION_STRING),
    db_name: str = typer.Option(DEFAULT_DB),
    user_name: str = typer.Option(DEFAULT_USER, help="Username of the owner of the database"),
):
    """Create/Drop a Ci/CD PostgreSQL database (temporary hack)."""
    from psycopg2.extensions import ISOLATION_LEVEL_AUTOCOMMIT

    from aicore.common.database import create_database

    if "postgresql://" not in connection_string:
        raise AICoreException("Invalid connection string: only PostgreSQL database is supported")

    # The DB doesn't exist yet so the connection string from Config cannot be used yet
    database = create_database(connection_string, echo="debug")

    with database.connection() as connection:
        with connection.begin():
            connection.connection.set_isolation_level(ISOLATION_LEVEL_AUTOCOMMIT)  # Close transaction on connection

            if operation == PostgreSQLDatabaseOperation.create:
                create_db_query = f'CREATE DATABASE "{db_name}" WITH OWNER {user_name}'
                grant_rights_query = f'GRANT ALL PRIVILEGES ON DATABASE "{db_name}" TO {user_name}'

                connection.execute(create_db_query)
                connection.execute(grant_rights_query)
            elif operation == PostgreSQLDatabaseOperation.drop:
                # https://sqlalchemy-utils.readthedocs.io/en/latest/_modules/sqlalchemy_utils/functions/database.html#drop_database  # noqa: E501

                drop_db_query = f'DROP DATABASE IF EXISTS "{db_name}"'
                connection.execute(drop_db_query)


@app.command()
def cli(name: str = typer.Option("cli_client", help="Name of the created microservice.")):
    """Run a Python REPL and connect to AI Core's database using SQLAlchemy."""
    import requests
    import sqlalchemy

    from aicore.common.auth import basic_auth, bearer_auth, internal_auth
    from aicore.common.cli import CLIENT_CONFIG_OPTIONS, SERVER_CONFIG_OPTIONS, CliService
    from aicore.common.config import get_config
    from aicore.registry import get_dao

    module_options = CLIENT_CONFIG_OPTIONS if name == "cli_client" else SERVER_CONFIG_OPTIONS
    config = get_config(module_options, microservice_name=name)
    microservice = CliService(config, name)

    use_grpc_server = hasattr(microservice, "test_grpc_server")
    use_grpc_client = hasattr(microservice, "test_grpc_client")
    use_graphql_client = hasattr(microservice, "test_graphql_client")
    use_database = hasattr(microservice, "test_database")

    namespace = {
        "config": config,
        "basic_auth": basic_auth,
        "bearer_auth": functools.partial(bearer_auth, config),
        "internal_auth": functools.partial(internal_auth, config),
        "requests": requests,
        "wsgi": microservice.test_wsgi_server,
        "health": microservice.health,
        "logger": microservice.logger,
        "metrics": microservice.metrics,
        "cli": microservice,
    }

    if use_grpc_server:
        namespace["grpc_server"] = (microservice.test_grpc_server,)

    if use_grpc_client:
        commands = {command.__name__: command for command in microservice.grpc_commands}
        namespace.update(commands)

    if use_graphql_client:
        namespace["graphql_client"] = microservice.test_graphql_client

    if use_database:
        namespace["sa"] = sqlalchemy
        namespace["conn"] = microservice.test_database.engine.connect()
        namespace["database"] = microservice.test_database
        for module_name, dao_class in get_dao().items():
            dao = dao_class(microservice.test_database)
            namespace[f"{module_name}_dao"] = dao

    with microservice:
        import textwrap

        PATHS = list(microservice.actuator.handlers.keys())
        typer.echo(
            f"Started WSGI server: '{microservice.test_wsgi_server.host}:{microservice.test_wsgi_server.port}', paths: {PATHS}"  # noqa: E501
        )

        if use_grpc_server:
            typer.echo(
                f"Started gRPC server: '{microservice.test_grpc_server.host}:{microservice.test_grpc_server.port}'"  # noqa: E501
            )

        if use_grpc_client:
            typer.echo(
                textwrap.dedent(
                    f"""
                    Started gRPC client: '{microservice.test_grpc_client.host}:{microservice.test_grpc_client.port}'

                    Usage:
                        command = TestCommand(["some data", "other data"])
                        cli.grpc_send(command)
                        print(list(command.echos))
                    """
                )
            )

        if use_graphql_client:
            QUERY = (
                '{_modelMetadata{entities(entityName:"metadata"){entityName,__typename,properties{name,__typename}}}}'
            )
            typer.echo(
                textwrap.dedent(
                    f"""
                    Configured GraphQL client: '{microservice.test_graphql_client.http_client.url}'

                    Usage:
                        entity_name_query = {QUERY!r}
                        result = graphql_client.send(entity_name_query, correlation_id='123456')
                        print([entity['entityName'] for entity in result['data']['_modelMetadata']['entities']])
                """  # noqa: E501
                )
            )

        typer.echo(
            textwrap.dedent(
                """
                HTTP client(s)

                Usage:
                    cli.http_get()
                    cli.http_get(basic=True)
                    cli.http_get(path=cli.actuator.LIVENESS_PATH)
                    cli.http_get(connection_name="translator")
            """  # noqa: E501
            )
        )

        if use_database:
            typer.echo(
                textwrap.dedent(
                    f"""
                    Connected to the database: {microservice.test_database.connection_string!r}

                    Usage:
                        ts_dao.get_fingerprints()
                        conn.execute('SELECT * from attributes').fetchall()
                        conn.execute(sa.select([ts_dao.attributes.c.attribute_id])).fetchall()
                        conn.execute(ts_dao.attributes.select()).fetchall()

                        Do not forget to run conn.commit() to save the changes to database!
                        """
                )
            )

        typer.echo(f"Namespace: {list(namespace.keys())!r}\n")
        run_repl(namespace)


@app.command()
def build(
    build_type: BuildType = typer.Argument(default=BuildType.package),
    python_path: str = typer.Option(""),
    python_version: str = typer.Option(default=PYTHON_VERSION),
):
    """Build AI-Core as a package or Docker image (dev)."""
    if build_type == BuildType.package:
        from assembly import build

        build.create_bare_metal_package(python_path, python_version)
        build.create_pom()
        build.create_config_json_package()
    elif build_type == BuildType.minimal_package:
        from assembly import build

        build.create_minimal_bare_metal_packages()
        build.create_pom()
        build.create_config_json_package()
    elif build_type == BuildType.docker_package or build_type == BuildType.docker_image:
        from assembly import build

        build.create_docker_package()

        if build_type == BuildType.docker_image:
            # Empty `services` translates to 'all'
            command, options = docker_compose(services=[])
            # `docker-compose build` specific prop to try to pull base image before building
            options["--pull"] = True

            command.build(options)


@app.command()
def run(
    microservice_name: str = typer.Argument(...),
    runtime: Runtime = typer.Argument(Runtime.native),
    db: DatabaseType = typer.Option(DatabaseType.postgres),
):
    """Run given AI Core microservice, PostgreSQL ('db'), Keycloak ('keycloak') or whole infrastructure ('infra')."""
    if microservice_name == "infra":
        command, options = docker_compose([db, "keycloak"])
        command.up(options)
    elif microservice_name == "monitoring":
        command, options = docker_compose(["prometheus", "grafana"])
        command.up(options)
    elif microservice_name == "db":
        command, options = docker_compose([db])
        command.up(options)
    elif microservice_name == "keycloak":
        command, options = docker_compose(["keycloak"])
        command.up(options)
    elif runtime == Runtime.native:
        from aicore.common.config import PARALLELISM_CONFIG_OPTIONS, Config
        from aicore.common.utils import handle_shutdown_signals, set_process_title, set_static_thread_limits

        # Cannot re-use Config from create_microservice() because of import from NumPy
        thread_config = Config.from_all_sources(microservice_name, PARALLELISM_CONFIG_OPTIONS)
        set_static_thread_limits(thread_config.omp, thread_config.blas)

        if microservice_name == "all":
            from aicore.common.config import Config
            from aicore.common.supervisor import CONFIG_OPTIONS, Supervisor

            microservice_name = "supervisor"
            config = Config.from_all_sources(microservice_name, CONFIG_OPTIONS)
            microservice = Supervisor(config)
        else:
            # Empty microservice consumes cca 150 MB (RSS)
            microservice = create_microservice(microservice_name)

        set_process_title(microservice_name, microservice.version)
        handle_shutdown_signals(microservice.handle_shutdown_signal)

        with microservice:
            microservice.run_forever()

    elif runtime == Runtime.docker:
        # May require apt install golang-docker-credential-helpers
        services = [db, "ai-core" if microservice_name == "all" else microservice_name]
        command, options = docker_compose(services)
        command.up(options)


@app.command()
def health_check(
    microservice_name: str = typer.Argument(...),
    timeout: float = typer.Argument(10, help="Time to request microservice before exiting"),
):
    """Health check of a microservice; exitcode == 0 if alive 1 otherwise."""
    from aicore.common.actuator import microservice_health_check
    from aicore.common.config import get_config
    from aicore.common.logging import LogConfig, Logger
    from aicore.registry import get_service

    _, microservice_config_options = get_service(microservice_name)
    config = get_config(microservice_config_options)
    logger = Logger("health_check", LogConfig.from_config(config))

    is_alive = microservice_health_check(microservice_name, config, logger, timeout)

    exit(0 if is_alive else 1)


@app.command()
def check(check_types: list[CheckType] = typer.Argument(None, help="Types of check to execute")):
    """Run specified check on AI-Core code."""
    check_types = check_types or [CheckType.linting, CheckType.marks, CheckType.config, CheckType.licenses]

    type_functions = {
        CheckType.typing: check_typing,
        CheckType.linting: check_linting,
        CheckType.marks: check_marks,
        CheckType.config: check_config,
        CheckType.licenses: check_licenses,
    }

    exit_code = EXIT_CODE_SUCCESS

    for check_type in check_types:
        typer.echo(f"*** Checking {check_type} ***")
        result = type_functions[check_type]()

        exit_code |= result

    exit(exit_code)


@app.command()
def test(args: str = typer.Argument(""), checks: bool = True):
    """Run the linter and tests of AI Core.

    Passing arguments to Pytest has to be done in an awkward way:
    ./manage.py test -- '-k unit'
    """
    import pytest

    if checks:
        check([CheckType.typing, CheckType.linting, CheckType.marks, CheckType.config])

    exit_code = pytest.main(list(args.split(" ")))  # Support for variable args in Typer/Click is poor
    exit(exit_code)


@app.command()
def benchmark(
    algorithm: BenchmarkedAlgorithm,
    size: int = 10000,
    threads: str = "null",
    jobs: str = "0",
    omp: str = "0",
    blas: str = "null",
):
    """Measure the speed of calculation using given threads and jobs (0 = all non-HT CPUs, "null" = do not set)."""
    # Numpy must be imported after setting thread limits to pass env variables to OpenBLAS (beware of Black.Isort!)
    import timeit

    import threadpoolctl

    from aicore.common.utils import set_dynamic_thread_limits, set_static_thread_limits

    threads = int(threads) if threads != "null" else None
    jobs = int(jobs) if jobs != "null" else None
    omp = int(omp) if omp != "null" else None
    blas = int(blas) if blas != "null" else None

    set_static_thread_limits(omp, blas)

    if algorithm == BenchmarkedAlgorithm.neighbors:
        import numpy  # Do not move to the outer scope, Isort would place the import before setting of static limits

        from aicore.term_suggestions.fingerprints import FINGERPRINT_DTYPE, FINGERPRINT_LENGTH
        from aicore.term_suggestions.neighbors import FingerprintsIndex, NeighborsCalculator

        set_dynamic_thread_limits(threads)
        attributes = [str(index) for index in range(1000)]  # Batch size
        data = numpy.random.rand(size, FINGERPRINT_LENGTH).astype(FINGERPRINT_DTYPE)

        # Data is set manually -> capacity can be limited to the least amount of attributes
        fingerprints_index = FingerprintsIndex(capacity=1)
        fingerprints_index.fingerprints.storage = data
        fingerprints_index.fingerprints.occupied = size

        for index in range(size):
            fingerprints_index.id_to_idx[str(index)] = index

        neighbors = NeighborsCalculator(fingerprints_index)

        statement = "neighbors.top_k(attributes)"
    elif algorithm in {BenchmarkedAlgorithm.isolation_forest, BenchmarkedAlgorithm.time_series}:
        import numpy
        import pandas

        from aicore.anomaly_detection.anomaly_detector import IsolationForestModel, TimeSeriesAnalysisModel
        from aicore.anomaly_detection.definitions import Category, CategoryType
        from aicore.common.config import Config

        set_dynamic_thread_limits(threads)
        data = pandas.DataFrame({f"a{index}": list(range(500)) for index in range(size)})
        category = Category("cat_name", CategoryType.GENERIC, data)

        config = Config("dummy_microservice", {})
        config.jobs = jobs

        if algorithm == BenchmarkedAlgorithm.isolation_forest:
            config.anomaly_detector_isolation_forest_threshold = -0.6
            model = IsolationForestModel(config, hcns=[])
            statement = "model.fit_and_predict(category)"
        else:
            config.anomaly_detector_time_series_std_threshold = 3
            category.periodicity = 2
            model = TimeSeriesAnalysisModel(config, hcns=[])
            statement = "model.fit_and_predict(category)"

    elif algorithm == BenchmarkedAlgorithm.dot:
        import numpy

        set_dynamic_thread_limits(threads)
        data = numpy.random.rand(size, size)

        statement = "numpy.dot(data, data)"
    elif algorithm == BenchmarkedAlgorithm.norm:
        import numpy
        import scipy.linalg  # noqa: F401

        set_dynamic_thread_limits(threads)
        data = numpy.random.rand(size, size)

        statement = "scipy.linalg.norm(data, ord=2)"

    elapsed = timeit.timeit(stmt=statement, number=1, globals=locals())

    if not threads:
        effective_threads = str(max(info["num_threads"] for info in threadpoolctl.threadpool_info()))
        threads = f"{effective_threads} (default)" if threads is None else effective_threads

    typer.echo(
        f"Calculating {algorithm}(size={size}) with {threads} threads and {jobs} jobs took {elapsed:.2f} seconds"  # noqa: E501
    )


@app.command()
def proto(api: ProtoAPI = typer.Argument(ProtoAPI.ai_core, help="Type of API to generate")):
    """Generate Python boilerplate of gRPC messages from protobuf definitions.

    Note: By default, only AI Core API boilerplate is generated. Research guys can generate code for their API
    without the need of having latest Configuration Service API checked out.
    """
    import tempfile

    if api in [ProtoAPI.ai_core, ProtoAPI.all]:
        MODULES = ("common", "term_suggestions", "nlp_search", "anomaly_detection", "ai_matching")

        with tempfile.TemporaryDirectory() as tempdir:
            for module in MODULES:
                compile_ai_core_protobuf_module(module, tempdir)

        update_api_version(AI_CORE_API_REPO_PATH, ProtoAPI.ai_core)

    if api in [ProtoAPI.configuration_service, ProtoAPI.all]:
        with tempfile.TemporaryDirectory() as tempdir:
            compile_cs_protobuf(tempdir)

        update_api_version(CONFIGURATION_SERVICE_API_REPO_PATH, ProtoAPI.configuration_service)


@app.command()
def container_id():
    """Retrieve current container ID."""
    from aicore.common import docker

    docker_id = docker.get_container_id()
    typer.echo(docker_id)


@app.command()
def config():
    """Generate application.properties, config options README, and configService.json."""
    from aicore.management.config import (
        check_default_values,
        generate_application_properties_content,
        generate_config_json_content,
        generate_readme_content,
    )

    check_default_values(ETC_APPLICATION_PROPERTIES_PATH)

    for path, content_generator in {
        DEFAULT_APPLICATION_PROPERTIES_PATH: generate_application_properties_content,
        PROPERTIES_README_PATH: generate_readme_content,
        CONFIG_SERVICE_JSON_PATH: generate_config_json_content,
    }.items():
        content = content_generator()

        with open(path, "w") as file:
            file.write(content)


@app.command()
def licenses(dev: bool = typer.Option(default=False, help="Include PIP packages used only for development")):
    """Generate license report for PIP packages used by the application."""
    from aicore.management.licenses import generate_licenses_content, get_all_licenses

    package_licenses = get_all_licenses(include_development=dev)

    for _, value in sorted(package_licenses.items(), key=lambda package: (package[1][0], package[0])):
        license_warning = value[2]
        if license_warning:
            typer.echo(license_warning)

    with open(LICENSES_README_PATH, "wt") as licenses_file:
        generate_licenses_content(package_licenses, licenses_file)


@app.command()
def metrics():
    """Generate report of Prometheus metrics used by the application."""
    from aicore.registry import get_metrics

    with open(METRICS_README_PATH, "wt") as metrics_file:
        metrics_file.write("| Component | Metric | Type | Description | Labels |\n")
        metrics_file.write("| ----------- | ----------- | ----------- | ----------- | ----------- |\n")

        for component, metrics in sorted(get_metrics().items()):
            for metric in metrics:
                metrics_file.write(
                    f"| {component} | {metric.full_name} | {metric.type.name} | {metric.description} | `{metric.labels}` |\n"  # noqa: E501
                )


@app.command()
def status():
    """Produce report of AI-Core microservice statuses."""
    import more_itertools
    import tabulate

    from aicore.common.config import get_config
    from aicore.management.status import get_authentication_status, get_microservices_status
    from aicore.registry import MICROSERVICE_NAMES, get_all_config_options

    config = get_config(*get_all_config_options())
    microservices_status, resources_status = get_microservices_status(MICROSERVICE_NAMES, config)

    typer.echo(tabulate.tabulate(microservices_status, tablefmt="grid", headers="keys"))
    typer.echo("\n")

    if resources_status:
        typer.echo(tabulate.tabulate(resources_status.values(), tablefmt="grid", headers="keys"))
        typer.echo("\n")

    neighbors_status = more_itertools.one(
        filter(lambda microservice_status: microservice_status["Microservice"] == "neighbors", microservices_status)
    )
    # MMM-connecting microservices can be UNAVAILABLE and MMM won't be in the resource_status dictionary
    mmm_status = resources_status.get("mmm", {"Status": "UNAVAILABLE"})

    # Do not verify authentication until required components are up
    if all(comp_status["Status"] == "UP" for comp_status in [neighbors_status, mmm_status]):
        authentication_status = get_authentication_status(config)
        typer.echo(tabulate.tabulate(authentication_status, tablefmt="grid", headers="keys"))
    else:
        typer.echo("Authentication verification was not attempted as required components (Neighbors, MMM) are not UP")


@app.command()
def changes(
    old_branch: str = typer.Option(None, help="Old release branch that should already be documented in CHANGELOG"),
    new_branch: str = typer.Option(None, help="New release branch whose missing changes interest us"),
):
    """Get issue numbers and dependency update changes that are not part of the CHANGELOG between two branches.

    Example: python manage.py changes --old-branch release-13.2.X --new-branch release-13.3.X
    """
    from aicore.management.changes import (
        get_commits_in_range,
        get_common_ancestor,
        get_current_branch,
        get_previous_release_branch,
        load_changelog_dependencies,
        load_changelog_issue_numbers,
        parse_dependencies_versions,
        parse_issue_numbers,
    )

    if not new_branch:
        new_branch = get_current_branch()
    if not old_branch:
        old_branch = get_previous_release_branch(new_branch)

    common_ancestor_hash = get_common_ancestor(old_branch, new_branch)

    new_branch_commits = get_commits_in_range(common_ancestor_hash, new_branch)
    commit_issue_numbers = parse_issue_numbers(new_branch_commits)
    changelog_issue_numbers = load_changelog_issue_numbers()
    missing_issue_numbers = commit_issue_numbers - changelog_issue_numbers

    typer.echo(f"Found {len(commit_issue_numbers)} issue numbers between {old_branch} and {new_branch}\n")

    if missing_issue_numbers:
        typer.echo(f"Found {len(missing_issue_numbers)} missing issues based on issue numbers in commit messages:")
        for issue_number in missing_issue_numbers:
            typer.echo(f"* ??? [{issue_number}](https://support.ataccama.com/jira/browse/{issue_number})")
    else:
        typer.echo("No missing issues found based on issue numbers in commit messages")

    typer.echo("")

    # Renovate commits only to master branch, fixes in release branches shouldn't contain the same dependencies
    commit_dependencies = parse_dependencies_versions(new_branch_commits)
    changelog_dependencies = load_changelog_dependencies()
    missing_dependencies = {
        name: version for name, version in commit_dependencies.items() if changelog_dependencies.get(name) != version
    }

    typer.echo(f"Found {len(commit_dependencies)} dependency updates between {old_branch} and {new_branch}\n")

    if missing_dependencies:
        typer.echo(f"Found {len(missing_dependencies)} missing dependency updates based on renovate commit messages:")
        for name, version in missing_dependencies.items():
            typer.echo(f"* {name} to {version}")
    else:
        typer.echo("No missing dependencies found based on renovate commit messages")

    if missing_issue_numbers or missing_dependencies:
        exit(EXIT_CODE_FAILURE)


if __name__ == "__main__":
    app()
