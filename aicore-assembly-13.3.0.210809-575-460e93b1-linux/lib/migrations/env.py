"""Launcher for database migrations of AI Core."""

from __future__ import annotations

import sys


sys.path.append(".")

from migrations.config import config, context, database, target_metadata  # noqa: E402


def print_sql():
    """Print a SQL migration script to stdout."""
    context.configure(
        url=config.connection_string,
        target_metadata=target_metadata,
        literal_binds=True,
        dialect_opts=config.engine_kwargs,
    )

    with context.begin_transaction():
        context.run_migrations()


def migrate():
    """Alter schema of the configured database."""
    with database.engine.connect() as connection:
        context.configure(connection=connection, target_metadata=target_metadata)

        with context.begin_transaction():
            context.run_migrations()


if context.is_offline_mode():
    print_sql()
else:
    migrate()
