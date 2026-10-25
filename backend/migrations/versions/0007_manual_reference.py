"""Store the explicitly selected factory documentary reference."""

import sqlalchemy as sa
from alembic import op

revision = "0007"
down_revision = "0006"
branch_labels = None
depends_on = None


def upgrade():
    op.add_column(
        "vehicles", sa.Column("manual_reference", sa.String(80), nullable=True)
    )
    op.create_check_constraint(
        "vehicle_manual_reference",
        "vehicles",
        "manual_reference IS NULL OR manual_reference = 'gol-g2-1600-mi-1998-factory'",
    )


def downgrade():
    op.drop_constraint("vehicle_manual_reference", "vehicles", type_="check")
    op.drop_column("vehicles", "manual_reference")
