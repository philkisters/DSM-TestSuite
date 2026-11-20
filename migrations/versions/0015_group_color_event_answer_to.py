"""core.groups.color (defaults to '#' + first 6 hex chars of md5(name)); proxy.events.answer_to

Revision ID: 0015
Revises: 0014
"""
from alembic import op

revision = "0015"
down_revision = "0014"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.execute("ALTER TABLE core.groups ADD COLUMN color TEXT")
    op.execute("UPDATE core.groups SET color = '#' || left(md5(name), 6)")
    op.execute("ALTER TABLE core.groups ALTER COLUMN color SET NOT NULL")
    op.execute("""
        ALTER TABLE core.groups
            ADD CONSTRAINT ck_group_color CHECK (color ~ '^#[0-9a-fA-F]{6}$')
    """)
    # A column default cannot reference other columns, so a trigger fills it in.
    op.execute("""
        CREATE FUNCTION core.groups_default_color() RETURNS trigger AS $$
        BEGIN
            IF NEW.color IS NULL THEN
                NEW.color := '#' || left(md5(NEW.name), 6);
            END IF;
            RETURN NEW;
        END;
        $$ LANGUAGE plpgsql
    """)
    op.execute("""
        CREATE TRIGGER trg_groups_default_color
            BEFORE INSERT ON core.groups
            FOR EACH ROW EXECUTE FUNCTION core.groups_default_color()
    """)

    op.execute("ALTER TABLE proxy.events ADD COLUMN answer_to BIGINT")


def downgrade() -> None:
    op.execute("ALTER TABLE proxy.events DROP COLUMN answer_to")
    op.execute("DROP TRIGGER trg_groups_default_color ON core.groups")
    op.execute("DROP FUNCTION core.groups_default_color()")
    op.execute("ALTER TABLE core.groups DROP CONSTRAINT ck_group_color")
    op.execute("ALTER TABLE core.groups DROP COLUMN color")
