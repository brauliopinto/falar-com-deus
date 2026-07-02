"""add raw columns and pre-normalize pt fields

Revision ID: 20260628_0001
Revises: 20260627_0001
Create Date: 2026-06-28
"""

from alembic import op
import sqlalchemy as sa

revision = "20260628_0001"
down_revision = "20260627_0001"
branch_labels = None
depends_on = None

RAW_COLS = [
    "titulo_raw",
    "subtitulo_raw",
    "leitura_ref_raw",
    "conteudo_i_raw",
    "conteudo_ii_raw",
    "conteudo_iii_raw",
    "reflexao_raw",
]

PT_COLS = [
    "titulo_pt",
    "subtitulo_pt",
    "conteudo_i_pt",
    "conteudo_ii_pt",
    "conteudo_iii_pt",
    "reflexao_pt",
]


def upgrade() -> None:
    for col in RAW_COLS:
        op.add_column(
            "meditacoes",
            sa.Column(col, sa.Text(), nullable=False, server_default=""),
        )

    # Populate *_raw with the current (already-normalized) ES values — best approximation
    # for existing rows since the original HTML is no longer available.
    conn = op.get_bind()
    conn.execute(sa.text("""
        UPDATE meditacoes SET
            titulo_raw       = titulo,
            subtitulo_raw    = subtitulo,
            leitura_ref_raw  = leitura_ref,
            conteudo_i_raw   = conteudo_i,
            conteudo_ii_raw  = conteudo_ii,
            conteudo_iii_raw = conteudo_iii,
            reflexao_raw     = reflexao
    """))

    # Normalize existing PT fields so the DB matches what the frontend will now read directly.
    from app.services.text_normalizer import normalize_text

    rows = conn.execute(
        sa.text(f"SELECT id, {', '.join(PT_COLS)} FROM meditacoes")
    ).fetchall()

    for row in rows:
        row_dict = row._mapping
        updates = {col: normalize_text(row_dict[col]) for col in PT_COLS}
        set_clause = ", ".join(f"{col} = :{col}" for col in PT_COLS)
        conn.execute(
            sa.text(f"UPDATE meditacoes SET {set_clause} WHERE id = :id"),
            {**updates, "id": row_dict["id"]},
        )


def downgrade() -> None:
    for col in RAW_COLS:
        op.drop_column("meditacoes", col)
