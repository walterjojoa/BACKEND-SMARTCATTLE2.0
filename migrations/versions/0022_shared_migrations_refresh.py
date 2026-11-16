"""Re-apply the shared migrations, which gained five files since 0012

0012 copied database/migrations/ from the database repository and applied it so
that a fresh database would not be left with schema.sql alone. It did its job,
but it only runs once: a database that already passed it never sees a file added
to that folder afterwards.

Five arrived since: 0029 users.preferences, 0030 camera_account, 0031 the
detections view, 0032 the daily_reports() function and 0033 the assistant's role
and views. No revision of this backend creates any of them, so every database
migrated before this revision is missing all five, and so is every fresh one
built from the stale copy.

Applying the folder again is the same no-op 0012 relies on: every file there is
written to be safe to run twice. The alternative -- listing only the five new
files -- would leave the same hole open the next time the folder grows.

Revision ID: 0022_shared_migrations_refresh
Revises: 0021_camera_address
Create Date: 2026-11-16
"""
from pathlib import Path

from alembic import op

revision = "0022_shared_migrations_refresh"
down_revision = "0021_camera_address"
branch_labels = None
depends_on = None

SHARED_MIGRATIONS = Path(__file__).resolve().parents[2] / "database" / "migrations"


def upgrade() -> None:
    bind = op.get_bind()
    if bind.dialect.name != "postgresql":
        # The files are PostgreSQL (DO blocks, views, plpgsql). SQLite, the
        # test database, only ever gets the columns the backend uses.
        return
    # The driver's own cursor, without parameters: through exec_driver_sql
    # psycopg reads every % in the files (format() patterns, LIKE) as a
    # placeholder. Same connection, so the same migration transaction.
    cursor = bind.connection.dbapi_connection.cursor()
    try:
        for path in sorted(SHARED_MIGRATIONS.glob("*.sql")):
            cursor.execute(path.read_text(encoding="utf-8"))
    finally:
        cursor.close()


#: Views the five new files hang off tables this backend owns and drops on the way
#: down: 0031's `detections` reads detection_logs (0019) and 0033's v_assistant_alerts
#: reads security_alerts (0008). Left in place they turn those downgrades into
#: "cannot drop table detection_logs because other objects depend on it".
DEPENDENT_VIEWS = (
    "v_assistant_alerts",
    "v_assistant_cameras",
    "v_assistant_events",
    "v_assistant_detections",
    "detections",
)


def downgrade() -> None:
    bind = op.get_bind()
    if bind.dialect.name != "postgresql":
        return
    # Only the views, and only these. The rest of what the shared files add --
    # users.preferences, the daily_reports() function, indexes, comments -- belongs
    # to the database repository, which has no down migrations: 0012 leaves it alone
    # for the same reason. A function is not a tracked dependency, so none of that
    # blocks a downgrade.
    for view in DEPENDENT_VIEWS:
        # Names from the constant above, never from input.
        op.execute(f"DROP VIEW IF EXISTS {view}")  # noqa: S608
