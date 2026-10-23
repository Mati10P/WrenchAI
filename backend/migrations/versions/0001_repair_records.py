"""Vehicles, mechanical incidents and measurements."""

from alembic import op
import sqlalchemy as sa

revision = "0001_repair_records"
down_revision = None
branch_labels = None
depends_on = None


def upgrade():
    op.create_table(
        "vehicles",
        sa.Column("id", sa.Uuid(), primary_key=True),
        sa.Column("name", sa.String(100), nullable=False),
        sa.Column("make", sa.String(60)),
        sa.Column("model", sa.String(80)),
        sa.Column("year", sa.Integer()),
        sa.Column("fuel", sa.String(40)),
        sa.Column("engine_code", sa.String(40)),
        sa.Column("market", sa.String(60)),
        sa.Column("notes", sa.Text()),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.func.now(),
            nullable=False,
        ),
        sa.CheckConstraint("year IS NULL OR year BETWEEN 1886 AND 2100"),
    )
    op.create_table(
        "incidents",
        sa.Column("id", sa.Uuid(), primary_key=True),
        sa.Column(
            "vehicle_id",
            sa.Uuid(),
            sa.ForeignKey("vehicles.id", ondelete="RESTRICT"),
            nullable=False,
        ),
        sa.Column("title", sa.String(160), nullable=False),
        sa.Column("description", sa.Text(), nullable=False),
        sa.Column("symptoms", sa.JSON(), nullable=False),
        sa.Column("mileage", sa.Integer()),
        sa.Column("status", sa.String(20), nullable=False),
        sa.Column("resolution", sa.Text()),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.func.now(),
            nullable=False,
        ),
        sa.Column("resolved_at", sa.DateTime(timezone=True)),
        sa.CheckConstraint("status IN ('OPEN', 'IN_PROGRESS', 'RESOLVED')"),
        sa.CheckConstraint("mileage IS NULL OR mileage >= 0"),
        sa.CheckConstraint(
            "(status = 'RESOLVED' AND resolution IS NOT NULL AND length(trim(resolution)) > 0 AND resolved_at IS NOT NULL) OR (status != 'RESOLVED' AND resolution IS NULL AND resolved_at IS NULL)"
        ),
    )
    op.create_index("ix_incidents_vehicle_id", "incidents", ["vehicle_id"])
    op.create_index("ix_incidents_status", "incidents", ["status"])
    op.create_table(
        "measurements",
        sa.Column("id", sa.Uuid(), primary_key=True),
        sa.Column(
            "incident_id",
            sa.Uuid(),
            sa.ForeignKey("incidents.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column("name", sa.String(100), nullable=False),
        sa.Column("value", sa.Numeric(14, 4), nullable=False),
        sa.Column("unit", sa.String(30), nullable=False),
        sa.Column("conditions", sa.Text()),
        sa.Column(
            "observed_at",
            sa.DateTime(timezone=True),
            server_default=sa.func.now(),
            nullable=False,
        ),
    )
    op.create_index("ix_measurements_incident_id", "measurements", ["incident_id"])


def downgrade():
    op.drop_table("measurements")
    op.drop_table("incidents")
    op.drop_table("vehicles")
