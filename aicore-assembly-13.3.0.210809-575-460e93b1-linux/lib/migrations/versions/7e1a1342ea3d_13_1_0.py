"""13.1.0 - Date columns' type changed from DateTime to TIMESTAMP WITH TIMEZONE.

Revision ID: 7e1a1342ea3d
Revises: ae1027a6ad0
Create Date: 2021-04-21 11:56:38.357803

"""

from __future__ import annotations

import sys

import alembic
import sqlalchemy


sys.path.append(".")


revision = "7e1a1342ea3d"
down_revision = "ae1027a6ad0"
branch_labels = None
depends_on = None


def change_date_column_type():
    """Change the type of date columns from DateTime to TIMESTAMP."""
    # Update last_modified column
    for table_name in ["attributes", "assigned_terms", "rejected_terms", "disabled_terms", "similarity_thresholds"]:
        alembic.op.alter_column(
            table_name,
            "last_modified",
            type_=sqlalchemy.TIMESTAMP(timezone=True),
            postgresql_using="last_modified AT TIME ZONE 'UTC'",
        )

    # Update other date columns
    alembic.op.alter_column(
        "attributes",
        "suggestions_freshness",
        type_=sqlalchemy.TIMESTAMP(timezone=True),
        postgresql_using="suggestions_freshness AT TIME ZONE 'UTC'",
    )
    alembic.op.alter_column(
        "attributes",
        "suggestions_last_modified",
        type_=sqlalchemy.TIMESTAMP(timezone=True),
        postgresql_using="suggestions_last_modified AT TIME ZONE 'UTC'",
    )


def upgrade():
    """Migrate the database from previous revision."""
    from aicore.common.registry import LogId
    from migrations.config import database, logger

    if database.engine.dialect.name != "postgresql":
        logger.error(
            "DB schema upgrade to version 13.1.0 can only be performed on PostgreSQL",
            message_id=LogId.db_migration,
            _color="<white><bold>",
        )
        exit(1)

    with logger.action(LogId.db_migration) as action:
        action.start("Starting DB schema upgrade to version 13.1.0", _color="<white><bold>")

        try:
            change_date_column_type()
        except Exception as error:
            action.exception("Failed to change DateTime columns to TIMESTAMP WITH TIME ZONE", error=error)
            raise error

        action.info("Changed DateTime columns to TIMESTAMP WITH TIME ZONE")
        action.finish("Upgraded the DB schema to version 13.1.0", _color="<white><bold>")


def downgrade():
    """Migrate the database back to the previous revision (if possible)."""
    from aicore.common.registry import LogId
    from migrations.config import logger

    logger.warning("Downgrade from version 13.1.0 to Cycle 9 is not supported", message_id=LogId.db_migration)

    raise NotImplementedError
