"""Cycle 8 - initial revision.

Revision ID: ae1027a6acf
Revises:
Create Date: 2020-11-18 17:09:46.145546

"""

from __future__ import annotations

import sys

import alembic
import sqlalchemy


sys.path.append(".")


from aicore.common.constants import CORRELATION_ID_SIZE, UUID_SIZE  # noqa: E402
from aicore.term_suggestions.fingerprints import FINGERPRINT_SIZE  # noqa: E402


revision = "ae1027a6acf"
down_revision = None
branch_labels = None
depends_on = None


def create_fingerprints():
    """Create the 'fingerprints' table."""
    alembic.op.create_table(
        "fingerprints",
        sqlalchemy.Column("attribute_id", sqlalchemy.String(UUID_SIZE), primary_key=True),
        sqlalchemy.Column("fingerprint", sqlalchemy.LargeBinary(FINGERPRINT_SIZE), nullable=False),
        sqlalchemy.Column("last_modified", sqlalchemy.BigInteger, index=True, nullable=False),
        sqlalchemy.Column("last_processed", sqlalchemy.BigInteger, index=True, nullable=False),
        sqlalchemy.Column("correlation_id", sqlalchemy.String(CORRELATION_ID_SIZE), nullable=False),
        sqlalchemy.Column("deleted", sqlalchemy.Boolean, nullable=False),  # Kept in C8 by mistake and not actually used
    )


def create_assigned_terms():
    """Create the 'assigned_terms' table."""
    alembic.op.create_table(
        "assigned_terms",
        sqlalchemy.Column("attribute_id", sqlalchemy.String(UUID_SIZE), primary_key=True),
        sqlalchemy.Column("terms", sqlalchemy.LargeBinary, nullable=False),
        sqlalchemy.Column("last_modified", sqlalchemy.BigInteger, index=True, nullable=False),
        sqlalchemy.Column("correlation_id", sqlalchemy.String(CORRELATION_ID_SIZE), nullable=False),
    )


def create_rejected_terms():
    """Create the 'rejected_terms' table."""
    alembic.op.create_table(
        "rejected_terms",
        sqlalchemy.Column("attribute_id", sqlalchemy.String(UUID_SIZE), primary_key=True),
        sqlalchemy.Column("terms", sqlalchemy.LargeBinary, nullable=False),
        sqlalchemy.Column("last_modified", sqlalchemy.BigInteger, index=True, nullable=False),
        sqlalchemy.Column("correlation_id", sqlalchemy.String(CORRELATION_ID_SIZE), nullable=False),
    )


def create_disabled_terms():
    """Create the 'disabled_terms' table."""
    alembic.op.create_table(
        "disabled_terms",
        sqlalchemy.Column("term_id", sqlalchemy.String(UUID_SIZE), primary_key=True),
        sqlalchemy.Column("last_modified", sqlalchemy.BigInteger, index=True, nullable=False),
        sqlalchemy.Column("correlation_id", sqlalchemy.String(CORRELATION_ID_SIZE), nullable=False),
        sqlalchemy.Column("deleted", sqlalchemy.Boolean(), nullable=False),
    )


def create_similarity_thresholds():
    """Create the 'similarity_thresholds' table."""
    alembic.op.create_table(
        "similarity_thresholds",
        sqlalchemy.Column("term_id", sqlalchemy.String(UUID_SIZE), primary_key=True),
        sqlalchemy.Column("value", sqlalchemy.Float, nullable=False),
        sqlalchemy.Column("last_modified", sqlalchemy.BigInteger, index=True, nullable=False),
        sqlalchemy.Column("correlation_id", sqlalchemy.String(CORRELATION_ID_SIZE), nullable=False),
    )


def create_learning_strategies():
    """Create the 'learning_strategies' table."""
    alembic.op.create_table(
        "learning_strategies",
        sqlalchemy.Column("term_id", sqlalchemy.String(UUID_SIZE), primary_key=True),
        sqlalchemy.Column("adaptive", sqlalchemy.Boolean, nullable=False),
        sqlalchemy.Column("correlation_id", sqlalchemy.String(CORRELATION_ID_SIZE), nullable=False),
    )


def create_feedbacks():
    """Create the 'feedbacks' table."""
    alembic.op.create_table(
        "feedbacks",
        sqlalchemy.Column(
            "sequential_id",
            sqlalchemy.BigInteger().with_variant(sqlalchemy.Integer, "sqlite"),
            primary_key=True,
            autoincrement=True,
        ),
        sqlalchemy.Column("term_id", sqlalchemy.String(UUID_SIZE), nullable=False),
        sqlalchemy.Column("positive", sqlalchemy.Boolean, nullable=False),
        sqlalchemy.Column("correlation_id", sqlalchemy.String(CORRELATION_ID_SIZE), nullable=False),
    )


def create_suggestions():
    """Create the 'suggestions' table."""
    alembic.op.create_table(
        "suggestions",
        sqlalchemy.Column("attribute_id", sqlalchemy.String(UUID_SIZE), primary_key=True),
        sqlalchemy.Column("suggestions", sqlalchemy.LargeBinary, nullable=False),
    )


def upgrade():
    """Set the database schema to the state as of its first internal release in Cycle 8."""
    from aicore.common.registry import LogId
    from migrations.config import logger

    logger.info("Starting DB schema upgrade to Cycle 8", message_id=LogId.db_migration, _color="<white><bold>")

    create_fingerprints()
    logger.info("Created the 'fingerprints' table", message_id=LogId.db_migration)

    create_assigned_terms()
    logger.info("Created the 'assigned_terms' table", message_id=LogId.db_migration)

    create_rejected_terms()
    logger.info("Created the 'rejected_terms' table", message_id=LogId.db_migration)

    create_disabled_terms()
    logger.info("Created the 'disabled_terms' table", message_id=LogId.db_migration)

    create_similarity_thresholds()
    logger.info("Created the 'similarity_thresholds' table", message_id=LogId.db_migration)

    create_learning_strategies()
    logger.info("Created the 'learning_strategies' table", message_id=LogId.db_migration)

    create_feedbacks()
    logger.info("Created the 'feedbacks' table", message_id=LogId.db_migration)

    create_suggestions()
    logger.info("Created the 'suggestions' table", message_id=LogId.db_migration)

    logger.info("Created the baseline DB schema from Cycle 8", message_id=LogId.db_migration, _color="<white><bold>")


def downgrade():
    """Revert to an empty database schema."""
    from aicore.common.registry import LogId
    from migrations.config import logger

    TABLE_NAMES = (
        "fingerprints",
        "assigned_terms",
        "rejected_terms",
        "disabled_terms",
        "similarity_thresholds",
        "learning_strategies",
        "feedbacks",
        "suggestions",
    )

    for table_name in TABLE_NAMES:
        alembic.op.drop_table(table_name)

    logger.info("Reverted to an empty database schema", message_id=LogId.db_migration, _color="<white><bold>")
