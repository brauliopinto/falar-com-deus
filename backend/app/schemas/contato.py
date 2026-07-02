from pydantic import BaseModel, EmailStr, Field


class ContatoRequest(BaseModel):
    nome: str = Field(min_length=2, max_length=100)
    email: EmailStr
    assunto: str = Field(min_length=3, max_length=150)
    mensagem: str = Field(min_length=10, max_length=5000)


class ContatoResponse(BaseModel):
    status: str
    message: str
