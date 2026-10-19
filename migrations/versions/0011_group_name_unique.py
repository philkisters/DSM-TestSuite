"""core.groups: make the column name and vm_ip unique

Revision ID: 0011
Revises: 0010
"""
from alembic import op

revision = "0011"
down_revision = "0010"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.execute("""
        ALTER TABLE core.groups ADD CONSTRAINT uq_group_name UNIQUE (name);
        ALTER TABLE core.groups ADD CONSTRAINT uq_group_vm_ip UNIQUE (vm_ip);
    """)

def downgrade() -> None:
    op.execute("""
        ALTER TABLE core.groups DROP CONSTRAINT uq_group_name;
        ALTER TABLE core.groups DROP CONSTRAINT uq_group_vm_ip;
    """)
