"""create meditacoes table

Revision ID: 20260627_0001
Revises:
Create Date: 2026-06-27 00:00:00
"""

from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision = "20260627_0001"
down_revision = None
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "meditacoes",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("data", sa.String(length=10), nullable=False, unique=True),
        sa.Column("titulo", sa.Text(), nullable=False),
        sa.Column("subtitulo", sa.Text(), nullable=False),
        sa.Column("leitura_ref", sa.Text(), nullable=False),
        sa.Column("conteudo_i", sa.Text(), nullable=False),
        sa.Column("conteudo_ii", sa.Text(), nullable=False),
        sa.Column("conteudo_iii", sa.Text(), nullable=False),
        sa.Column("reflexao", sa.Text(), nullable=False),
        sa.Column("titulo_pt", sa.Text(), nullable=False),
        sa.Column("subtitulo_pt", sa.Text(), nullable=False),
        sa.Column("conteudo_i_pt", sa.Text(), nullable=False),
        sa.Column("conteudo_ii_pt", sa.Text(), nullable=False),
        sa.Column("conteudo_iii_pt", sa.Text(), nullable=False),
        sa.Column("reflexao_pt", sa.Text(), nullable=False),
        sa.Column("fonte_traducao", sa.String(length=50), nullable=False),
        sa.Column("criado_em", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
    )
    op.create_index("ix_meditacoes_data", "meditacoes", ["data"], unique=True)


def downgrade() -> None:
    op.drop_index("ix_meditacoes_data", table_name="meditacoes")
    op.drop_table("meditacoes")
