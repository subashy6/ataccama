"""${message}

Revision ID: ${up_revision}
Revises: ${down_revision | comma,n}
Create Date: ${create_date}

"""

from __future__ import annotations

import sys

import alembic
import sqlalchemy


sys.path.append(".")


revision = ${repr(up_revision).replace("'", '"')}
down_revision = ${repr(down_revision).replace("'", '"')}
branch_labels = ${repr(branch_labels).replace("'", '"')}
depends_on = ${repr(depends_on).replace("'", '"')}


def create_something():
    """Create the 'something' table."""
    # TODO: Implement the upgrade script


def upgrade():
    """Migrate the database from previous revision."""
    from aicore.common.registry import LogId
    from migrations.config import logger

    logger.info("Starting DB schema upgrade to version XYZ", message_id=LogId.db_migration, _color="<white><bold>")

    ${upgrades if upgrades else "add_something_to_schema()"}
    logger.info("Created table 'something'", message_id=LogId.db_migration)

    logger.info("Upgraded the DB schema to version XYZ", message_id=LogId.db_migration, _color="<white><bold>")


def downgrade():
    """Migrate the database back to the previous revision (if possible)."""
    from aicore.common.registry import LogId
    from migrations.config import logger

    ${downgrades if downgrades else "pass"}
    logger.warning("Downgrade from version XYZ to version XYZ-1 is not supported", message_id=LogId.db_migration)

    raise NotImplementedError
