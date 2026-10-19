"""core.challenges: adds a 'steps' column to the groups table.

Revision ID: 0010
Revises: 0009
"""
from alembic import op

revision = "0010"
down_revision = "0009"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.execute("""
        ALTER TABLE core.challenges ADD COLUMN steps INTEGER NOT NULL DEFAULT 1;
    """)

def downgrade() -> None:
    op.execute("""
        ALTER TABLE core.challenges DROP COLUMN steps;
    """)
