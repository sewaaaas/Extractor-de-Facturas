"""Endpoint de disponibilidad sin dependencias externas."""

from typing import Literal

from fastapi import APIRouter
from pydantic import BaseModel

router = APIRouter(tags=["health"])


class HealthResponse(BaseModel):
    """Contrato estable del health check."""

    status: Literal["ok"]
    service: Literal["invoice-extractor"]


@router.get("/health", response_model=HealthResponse)
def health_check() -> HealthResponse:
    """Confirma que el proceso HTTP está disponible."""

    return HealthResponse(status="ok", service="invoice-extractor")
