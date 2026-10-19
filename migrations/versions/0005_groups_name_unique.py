"""core.groups.name unique (runs look groups up by name)

Revision ID: 0005
Revises: 0004
"""
from alembic import op

revision = "0005"
down_revision = "0004"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.execute("ALTER TABLE core.groups ADD CONSTRAINT groups_name_key UNIQUE (name)")


def downgrade() -> None:
    op.execute("ALTER TABLE core.groups DROP CONSTRAINT groups_name_key")
