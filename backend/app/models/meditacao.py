from datetime import datetime

from sqlalchemy import DateTime, Integer, String, Text, func
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base import Base


class Meditacao(Base):
    __tablename__ = "meditacoes"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    data: Mapped[str] = mapped_column(String(10), unique=True, nullable=False, index=True)
    titulo_raw: Mapped[str] = mapped_column(Text, nullable=False, server_default="")
    titulo: Mapped[str] = mapped_column(Text, nullable=False)
    subtitulo_raw: Mapped[str] = mapped_column(Text, nullable=False, server_default="")
    subtitulo: Mapped[str] = mapped_column(Text, nullable=False)
    leitura_ref_raw: Mapped[str] = mapped_column(Text, nullable=False, server_default="")
    leitura_ref: Mapped[str] = mapped_column(Text, nullable=False)
    leitura_ref_pt: Mapped[str] = mapped_column(Text, nullable=False, server_default="")
    conteudo_i_raw: Mapped[str] = mapped_column(Text, nullable=False, server_default="")
    conteudo_i: Mapped[str] = mapped_column(Text, nullable=False)
    conteudo_ii_raw: Mapped[str] = mapped_column(Text, nullable=False, server_default="")
    conteudo_ii: Mapped[str] = mapped_column(Text, nullable=False)
    conteudo_iii_raw: Mapped[str] = mapped_column(Text, nullable=False, server_default="")
    conteudo_iii: Mapped[str] = mapped_column(Text, nullable=False)
    titulo_pt: Mapped[str] = mapped_column(Text, nullable=False)
    subtitulo_pt: Mapped[str] = mapped_column(Text, nullable=False)
    conteudo_i_pt: Mapped[str] = mapped_column(Text, nullable=False)
    conteudo_ii_pt: Mapped[str] = mapped_column(Text, nullable=False)
    conteudo_iii_pt: Mapped[str] = mapped_column(Text, nullable=False)
    fonte_traducao: Mapped[str] = mapped_column(String(50), nullable=False, default="deepl")
    criado_em: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        server_default=func.now(),
    )
