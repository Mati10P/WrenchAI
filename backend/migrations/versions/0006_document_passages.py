"""Persist administratively accepted documentary passages."""

import sqlalchemy as sa
from alembic import op

revision = "0006"
down_revision = "0005"
branch_labels = None
depends_on = None


def upgrade():
    op.create_table(
        "document_passages",
        sa.Column("id", sa.String(80), primary_key=True),
        sa.Column("payload", sa.JSON(), nullable=False),
        sa.Column("search_text", sa.Text(), nullable=False),
        sa.Column("corpus_sha256", sa.String(64), nullable=False),
    )


def downgrade():
    op.drop_table("document_passages")
