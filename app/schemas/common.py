from typing import Generic, TypeVar, List, Optional
from pydantic import BaseModel

T = TypeVar('T')


class PaginatedResponse(BaseModel, Generic[T]):
    """Respuesta paginada genérica"""
    items: List[T]
    total: int
    page: int
    size: int
    pages: int
    has_next: bool
    has_prev: bool


class ErrorResponse(BaseModel):
    """Respuesta de error estándar"""
    error: str
    message: str
    details: Optional[dict] = None


class SuccessResponse(BaseModel):
    """Respuesta de éxito estándar"""
    success: bool = True
    message: str
    data: Optional[dict] = None