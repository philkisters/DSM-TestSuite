"""groups.vm_ip, challenges.archived (drop phase), runs.network_id

Revision ID: 0004
Revises: 0003
"""
from alembic import op

revision = "0004"
down_revision = "0003"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.execute("ALTER TABLE core.groups DROP COLUMN network_id")
    op.execute("ALTER TABLE core.groups ADD COLUMN vm_ip TEXT")
    op.execute("ALTER TABLE core.challenges DROP COLUMN phase")
    op.execute("ALTER TABLE core.challenges ADD COLUMN archived BOOLEAN NOT NULL DEFAULT false")
    # network_id is generated per run to avoid collisions in the proxy
    op.execute("ALTER TABLE core.runs ADD COLUMN network_id TEXT")
    op.execute("CREATE UNIQUE INDEX ix_runs_network_id ON core.runs (network_id) WHERE network_id IS NOT NULL")


def downgrade() -> None:
    op.execute("DROP INDEX core.ix_runs_network_id")
    op.execute("ALTER TABLE core.runs DROP COLUMN network_id")
    op.execute("ALTER TABLE core.challenges DROP COLUMN archived")
    op.execute("ALTER TABLE core.challenges ADD COLUMN phase TEXT NOT NULL DEFAULT ''")
    op.execute("ALTER TABLE core.groups ADD COLUMN network_id TEXT")
    op.execute("UPDATE core.groups SET network_id = 'group-' || id")
    op.execute("ALTER TABLE core.groups ALTER COLUMN network_id SET NOT NULL")
    op.execute("ALTER TABLE core.groups ADD CONSTRAINT groups_network_id_key UNIQUE (network_id)")
    op.execute("ALTER TABLE core.groups DROP COLUMN vm_ip")
