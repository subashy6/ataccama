"""Microservices (processes or Docker containers) used for DB upgrading."""

from __future__ import annotations

import alembic.command
import alembic.config

from aicore.common.database import Database, DatabaseError, get_latest_schema_version
from aicore.common.microservice import Microservice
from aicore.management.config import alembic_config
from aicore.upgrade import UPGRADE
from aicore.upgrade.registry import LogId


class UpgradableDatabase(Database):
    """Database that waits for any schema version, not just the latest."""

    def is_ready(self) -> bool:
        """Indicate whether the database has the version set."""
        try:
            self.current_version = self.get_current_schema_version()
        except DatabaseError as error:
            self.health.not_ready(str(error.__cause__))
            return False

        if not self.current_version:
            self.health.not_ready("Schema version is not set.")
            return False

        return True


class UpgradeService(Microservice):
    """Upgrade DB schema to the latest version."""

    def __init__(self, config):
        super().__init__("upgrade", config)

        self.db = self.database()
        self.wsgi_server()

        self.migrations_config = alembic_config(self.config.connection_string, self.config.migrations_path)

    def database(self) -> Database:
        """Create an upgradable database."""
        database = UpgradableDatabase(
            "db",
            self.logger,
            self.config.connection_string,
            get_latest_schema_version(self.config.migrations_path),
            self.metrics,
            onstart_retrying=self.retrying_controller(on_start=True),
            retrying=self.retrying_controller(),
            **self.config.engine_kwargs,
        )
        self.contained_resources.add(database)

        return database

    def on_start(self):
        """Upgrade DB schema."""
        if self.db.current_version == self.db.latest_version:
            self.logger.info("DB schema is up-to-date", message_id=LogId.db_upgrade)
            return

        alembic.command.upgrade(self.migrations_config, "head")


MICROSERVICES = {
    UPGRADE: UpgradeService,
}
