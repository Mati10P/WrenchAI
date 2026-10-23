"""Exact paid amounts for to-do items."""

import sqlalchemy as sa
from alembic import op

revision = "0004"
down_revision = "0003"
branch_labels = None
depends_on = None


def upgrade():
    op.add_column("incidents", sa.Column("cost", sa.Numeric(14, 2), nullable=True))
    op.create_check_constraint(
        "task_cost_nonnegative", "incidents", "cost IS NULL OR cost >= 0"
    )


def downgrade():
    op.drop_constraint("task_cost_nonnegative", "incidents", type_="check")
    op.drop_column("incidents", "cost")
