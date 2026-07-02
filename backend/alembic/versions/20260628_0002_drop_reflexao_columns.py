"""drop reflexao columns

Revision ID: 20260628_0002
Revises: 20260628_0001
Create Date: 2026-06-28
"""

from alembic import op

revision = "20260628_0002"
down_revision = "20260628_0001"
branch_labels = None
depends_on = None

COLS = ["reflexao_raw", "reflexao", "reflexao_pt"]


def upgrade() -> None:
    for col in COLS:
        op.drop_column("meditacoes", col)


def downgrade() -> None:
    import sqlalchemy as sa
    op.add_column("meditacoes", sa.Column("reflexao_pt", sa.Text(), nullable=False, server_default=""))
    op.add_column("meditacoes", sa.Column("reflexao", sa.Text(), nullable=False, server_default=""))
    op.add_column("meditacoes", sa.Column("reflexao_raw", sa.Text(), nullable=False, server_default=""))
