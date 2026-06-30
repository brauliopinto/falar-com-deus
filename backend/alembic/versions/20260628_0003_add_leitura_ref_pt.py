"""add leitura_ref_pt column

Revision ID: 20260628_0003
Revises: 20260628_0002
Create Date: 2026-06-28
"""

from alembic import op
import sqlalchemy as sa

revision = "20260628_0003"
down_revision = "20260628_0002"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column(
        "meditacoes",
        sa.Column("leitura_ref_pt", sa.Text(), nullable=False, server_default=""),
    )


def downgrade() -> None:
    op.drop_column("meditacoes", "leitura_ref_pt")
