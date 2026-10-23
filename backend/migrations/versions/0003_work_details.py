"""Work metadata separate from the original problem and its mileage."""

import sqlalchemy as sa
from alembic import op

revision = "0003"
down_revision = "0002"
branch_labels = None
depends_on = None


def upgrade():
    op.add_column("incidents", sa.Column("work_notes", sa.Text(), nullable=True))
    op.add_column("incidents", sa.Column("performed_on", sa.Date(), nullable=True))
    op.add_column("incidents", sa.Column("work_mileage", sa.Integer(), nullable=True))
    op.create_check_constraint(
        "work_mileage_range",
        "incidents",
        "work_mileage IS NULL OR work_mileage BETWEEN 0 AND 10000000",
    )
    # Preserve prior resolutions without pretending their entry date was the work date.
    op.execute(
        "UPDATE incidents SET work_notes = resolution WHERE resolution IS NOT NULL"
    )


def downgrade():
    op.drop_constraint("work_mileage_range", "incidents", type_="check")
    op.drop_column("incidents", "work_mileage")
    op.drop_column("incidents", "performed_on")
    op.drop_column("incidents", "work_notes")
