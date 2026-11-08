"""The LAN address a camera's owner typed, to show it on the Cameras page

Nullable and additive. An Imou camera opens through Imou's cloud by serial
number; this column only remembers the address its owner knows it by.

Added only if missing, so the order in which this and the database repository
reach a database does not matter.

Revision ID: 0022_camera_address
Revises: 0021_camera_address
Create Date: 2026-11-07 (moved from 0021 on 2026-11-14)
"""
from alembic import op
import sqlalchemy as sa

revision = "0022_camera_address"
down_revision = "0021_camera_address"
branch_labels = None
depends_on = None


def _has_address() -> bool:
    return "address" in {column["name"] for column in sa.inspect(op.get_bind()).get_columns("cameras")}


def upgrade() -> None:
    if not _has_address():
        with op.batch_alter_table("cameras") as batch:
            batch.add_column(sa.Column("address", sa.String(255)))


def downgrade() -> None:
    if _has_address():
        with op.batch_alter_table("cameras") as batch:
            batch.drop_column("address")
