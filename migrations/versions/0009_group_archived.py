"""core.group: adds an 'archived' column to the groups table.

Revision ID: 0009
Revises: 0008
"""
from alembic import op

revision = "0009"
down_revision = "0008"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.execute("""
        ALTER TABLE core.groups ADD COLUMN archived BOOLEAN NOT NULL DEFAULT FALSE;
    """)

def downgrade() -> None:
    op.execute("""
        ALTER TABLE core.groups DROP COLUMN archived;
    """)
