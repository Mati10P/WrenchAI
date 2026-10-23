"""Persist vehicle context and messages without changing existing repairs."""

import sqlalchemy as sa
from alembic import op

revision = "0002"
down_revision = "0001_repair_records"
branch_labels = None
depends_on = None


def upgrade():
    op.add_column("vehicles", sa.Column("mileage", sa.Integer(), nullable=True))
    op.add_column("vehicles", sa.Column("modifications", sa.Text(), nullable=True))
    op.create_check_constraint(
        "vehicle_mileage_range",
        "vehicles",
        "mileage IS NULL OR mileage BETWEEN 0 AND 10000000",
    )
    op.create_table(
        "messages",
        sa.Column("id", sa.Uuid(), primary_key=True),
        sa.Column(
            "incident_id",
            sa.Uuid(),
            sa.ForeignKey("incidents.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column("content", sa.Text(), nullable=False),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.func.now(),
            nullable=False,
        ),
    )
    op.create_index("ix_messages_incident_id", "messages", ["incident_id"])


def downgrade():
    op.drop_table("messages")
    op.drop_constraint("vehicle_mileage_range", "vehicles", type_="check")
    op.drop_column("vehicles", "modifications")
    op.drop_column("vehicles", "mileage")
