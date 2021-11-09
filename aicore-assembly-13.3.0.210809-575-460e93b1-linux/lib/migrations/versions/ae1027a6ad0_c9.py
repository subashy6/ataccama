"""Cycle 9 - Suggestions moved to the fingerprints table.

Revision ID: ae1027a6ad0
Revises: ae1027a6acf
Create Date: 2020-11-18 19:57:47.859149

"""

from __future__ import annotations

import sys

import alembic
import sqlalchemy


sys.path.append(".")

from aicore.common.database import SQL_DATETIME_MIN, utcnow  # noqa: E402, I001


revision = "ae1027a6ad0"
down_revision = "ae1027a6acf"
branch_labels = None
depends_on = None


def extend_fingerprints():
    """Rename the 'fingerprints' table and extend it by new columns."""
    alembic.op.rename_table("fingerprints", new_table_name="attributes")

    with alembic.op.batch_alter_table("attributes") as batch_operation:
        # NULL constraints are temporarily disabled until the data are migrated
        batch_operation.add_column(sqlalchemy.Column("suggestions", sqlalchemy.LargeBinary, nullable=True))
        batch_operation.add_column(
            sqlalchemy.Column("suggestions_freshness", sqlalchemy.DateTime, index=True, nullable=True)
        )
        batch_operation.add_column(
            sqlalchemy.Column("suggestions_last_modified", sqlalchemy.DateTime, index=True, nullable=True)
        )

        batch_operation.drop_column("last_processed")

    table = sqlalchemy.table(
        "attributes", sqlalchemy.column("suggestions_freshness"), sqlalchemy.column("suggestions_last_modified")
    )
    alembic.op.execute(
        sqlalchemy.update(table).values(
            suggestions_freshness=SQL_DATETIME_MIN,
            suggestions_last_modified=SQL_DATETIME_MIN,
        )
    )


def change_last_modified_type(table_name):
    """Change the type of the last modified column from UNIX timestamp by DateTime."""
    with alembic.op.batch_alter_table(table_name) as batch_operation:
        batch_operation.drop_column("last_modified")
        # NULL constraint is temporarily disabled until the data are migrated
        batch_operation.add_column(sqlalchemy.Column("last_modified", sqlalchemy.DateTime, index=True, nullable=True))

    # All suggestions will have to be recalculated anyway due to lack of freshness in the previous schema
    # so the laborious migration of timestamps in DB backend-agnostic way is not worth of the effort
    table = sqlalchemy.table(table_name, sqlalchemy.column("last_modified"))
    alembic.op.execute(sqlalchemy.update(table).values(last_modified=utcnow()))


def delete_pending_suggestions():
    """Delete all suggestion results not yet consumed by MMM."""
    suggestions = sqlalchemy.table("suggestions", sqlalchemy.column("attribute_id"), sqlalchemy.column("suggestions"))

    # Suggestions for all attributes will have to be recalculated anyway (see the freshness timestamp)
    alembic.op.execute(sqlalchemy.delete(suggestions))  # SQLAlchemy doesn't directly support TRUNCATE TABLE


def reactivate_null_constraints():
    """Re-activate all temporarily disabled NULL constraints."""
    with alembic.op.batch_alter_table("attributes") as batch_operation:
        batch_operation.alter_column("last_modified", nullable=False)
        batch_operation.alter_column("suggestions_freshness", nullable=False)
        batch_operation.alter_column("suggestions_last_modified", nullable=False)


def remove_deprecated_tables():
    """Remove tables that are not needed anymore."""
    alembic.op.drop_table("suggestions")


def upgrade():
    """Migrate the database from previous revision."""
    from aicore.common.registry import LogId
    from migrations.config import logger

    logger.info("Starting DB schema upgrade to Cycle 9", message_id=LogId.db_migration, _color="<white><bold>")

    extend_fingerprints()
    logger.info(
        "Renamed the 'fingerprints' table to 'attributes' and added columns for suggestion resultss",
        message_id=LogId.db_migration,
    )

    for table_name in ("attributes", "assigned_terms", "rejected_terms", "disabled_terms", "similarity_thresholds"):
        change_last_modified_type(table_name)
        logger.info(
            "Changed UNIX timestamp 'last_modified' of {table_name!r} table to DateTime",
            table_name=table_name,
            message_id=LogId.db_migration,
        )

    delete_pending_suggestions()
    logger.info(
        "Deleted all suggestions not yet consumed by MMM from 'suggestions' table", message_id=LogId.db_migration
    )

    reactivate_null_constraints()
    logger.info("Re-activated temporarily disabled NULL constraints", message_id=LogId.db_migration)

    remove_deprecated_tables()
    logger.info("Removed the 'suggestions' table", message_id=LogId.db_migration)

    logger.info("Upgraded the DB schema to Cycle 9", message_id=LogId.db_migration, _color="<white><bold>")
    logger.warning(
        "Suggestions for all attributes will be recalculated because all timestamps were set to NOW()",
        message_id=LogId.db_migration,
    )


def downgrade():
    """Migrate the database back to the previous revision (if possible)."""
    from aicore.common.registry import LogId
    from migrations.config import logger

    logger.warning("Downgrade from Cycle 9 to Cycle 8 is not supported", message_id=LogId.db_migration)

    raise NotImplementedError
