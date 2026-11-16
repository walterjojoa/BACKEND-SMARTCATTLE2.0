"""Join the Imou camera address and the shared migrations refresh

Both 0022 revisions start from 0021: 0022_camera_address (Imou, deploy-walter)
and 0022_shared_migrations_refresh (main). This revision only joins the two
heads so `alembic upgrade head` keeps working. A database already at
0022_camera_address runs the refresh and then this; a fresh one runs all three.

Revision ID: 0023_merge_camera_address
Revises: 0022_camera_address, 0022_shared_migrations_refresh
Create Date: 2026-11-16
"""

revision = "0023_merge_camera_address"
down_revision = ("0022_camera_address", "0022_shared_migrations_refresh")
branch_labels = None
depends_on = None


def upgrade() -> None:
    pass


def downgrade() -> None:
    pass
