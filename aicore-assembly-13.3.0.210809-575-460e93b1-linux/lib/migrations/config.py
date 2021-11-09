"""Configure the logging and collect the table defintions from all DAOs."""

from __future__ import annotations

import logging

import alembic
import sqlalchemy

from aicore.common.config import DB_CONFIG_OPTIONS, get_config
from aicore.common.database import CONSTRAINTS_CONVENTION, create_database
from aicore.common.logging import remove_nonroot_handlers
from aicore.registry import get_dao


context = alembic.context  # Magical proxy module for current EnvironmentContext which configures the MigrationContext
config = get_config(DB_CONFIG_OPTIONS)
database = create_database(config.connection_string, name="migration", echo="debug")
logger = database.logger  # To be used by individual migration scripts

remove_nonroot_handlers()  # alembic.context silently creates "sqlalchemy.engine.base.Engine" logger with StreamHandler
logging.getLogger().setLevel(logging.INFO)
logging.getLogger("sqlalchemy.engine").setLevel(logging.WARN)
logging.getLogger("alembic").setLevel(logging.INFO)

# Autogeneration of migration boilerplate code from diff of introspected current and target table definitions
daos = {}  # Key: DAO name, value: DAO
target_metadata = sqlalchemy.MetaData(naming_convention=CONSTRAINTS_CONVENTION)
for dao_name, dao_class in get_dao().items():
    dao = dao_class(database)
    dao.define_tables(target_metadata)  # Populate the target metadata
    daos[dao_name] = dao


# For debugging of migration scripts use sqlalchemy.MetaData(bind=database.engine, reflect=True).tables
