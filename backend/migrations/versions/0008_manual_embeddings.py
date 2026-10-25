"""Private OCR navigation embeddings, separate from approved passages."""

import sqlalchemy as sa
from alembic import op
from pgvector.sqlalchemy import Vector

revision = "0008"
down_revision = "0007"
branch_labels = None
depends_on = None


def upgrade():
    op.execute("CREATE EXTENSION IF NOT EXISTS vector")
    op.create_table(
        "manual_embeddings",
        sa.Column("id", sa.String(100), primary_key=True),
        sa.Column("page_id", sa.String(80), nullable=False),
        sa.Column("bundle_sha256", sa.String(64), nullable=False),
        sa.Column("text_sha256", sa.String(64), nullable=False),
        sa.Column("model", sa.String(100), nullable=False),
        sa.Column("embedding", Vector(768), nullable=False),
    )


def downgrade():
    op.drop_table("manual_embeddings")
    # The shared extension may have other consumers; leave it installed.
