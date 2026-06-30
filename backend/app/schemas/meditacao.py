from datetime import datetime

from pydantic import BaseModel, Field


class MeditacaoBase(BaseModel):
    data: str = Field(pattern=r"^\d{2}/\d{2}/\d{4}$")
    titulo_raw: str = ""
    titulo: str
    subtitulo_raw: str = ""
    subtitulo: str
    leitura_ref_raw: str = ""
    leitura_ref: str
    leitura_ref_pt: str = ""
    conteudo_i_raw: str = ""
    conteudo_i: str
    conteudo_ii_raw: str = ""
    conteudo_ii: str
    conteudo_iii_raw: str = ""
    conteudo_iii: str
    titulo_pt: str
    subtitulo_pt: str
    conteudo_i_pt: str
    conteudo_ii_pt: str
    conteudo_iii_pt: str
    fonte_traducao: str


class MeditacaoCreate(MeditacaoBase):
    pass


class MeditacaoResponse(MeditacaoBase):
    id: int
    criado_em: datetime

    model_config = {"from_attributes": True}


class MeditacaoListResponse(BaseModel):
    items: list[MeditacaoResponse]
    total: int
    limit: int
    offset: int


class ScrapeResponse(BaseModel):
    status: str
    data: str
    message: str
