from datetime import datetime

from pydantic import BaseModel, Field


class ProblemFieldError(BaseModel):
    """Um campo inválido de um erro de validação"""

    field: str = Field(..., description="Caminho do campo inválido", examples=["latitude"])
    errorCode: str = Field(..., description="Código estável do erro do campo", examples=["VALIDATION_FAILED"])
    detail: str = Field(
        ..., description="Explicação para quem depura", examples=["Input should be less than or equal to 90"]
    )


class ProblemDetail(BaseModel):
    """Corpo de todo erro HTTP do serviço, no contrato de erro da organização"""

    type: str = Field(..., description="Sempre about:blank", examples=["about:blank"])
    title: str = Field(..., description="O mesmo valor de errorCode", examples=["NOT_FOUND"])
    status: int = Field(..., description="Código HTTP", examples=[404])
    errorCode: str = Field(..., description="Código estável do catálogo de erros", examples=["NOT_FOUND"])
    detail: str = Field(
        ...,
        description="Explicação para quem depura, em português; o front não exibe",
        examples=["Lugar não encontrado"],
    )
    instance: str = Field(..., description="Caminho da requisição", examples=["/v1/address/places/ChIJ1"])
    timestamp: datetime = Field(..., description="Instante do erro, em UTC")
    traceId: str | None = Field(default=None, description="Id do trace, para cruzar com os logs")
    errors: list[ProblemFieldError] | None = Field(default=None, description="Campos inválidos, só em validação")
