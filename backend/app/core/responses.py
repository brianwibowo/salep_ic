"""Shared API response envelope for SALEP endpoints."""

from typing import Any, Generic, TypeVar

from fastapi.encoders import jsonable_encoder
from fastapi.responses import JSONResponse
from pydantic import BaseModel

T = TypeVar("T")


class ApiResponse(BaseModel, Generic[T]):
    """Consistent response contract exposed by the public API."""

    status: bool
    message: str
    data: T | None = None


def success_response(data: T, message: str = "Request berhasil") -> dict[str, Any]:
    """Create a successful response body while preserving FastAPI's status code."""

    return ApiResponse[T](status=True, message=message, data=data).model_dump()


def error_response(
    message: str,
    status_code: int,
    data: Any = None,
) -> JSONResponse:
    """Create a failed response body with a meaningful HTTP status code."""

    body = ApiResponse[Any](status=False, message=message, data=data).model_dump()
    return JSONResponse(status_code=status_code, content=jsonable_encoder(body))


def detail_message(detail: Any, fallback: str = "Request gagal") -> str:
    """Turn FastAPI exception details into a safe, user-facing message."""

    return detail if isinstance(detail, str) else fallback
