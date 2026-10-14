from typing import Literal

from fastapi import APIRouter, HTTPException, Request
from pydantic import BaseModel, Field, SecretStr

from app.core.responses import success_response
from app.services.auth_service import get_auth_store


router = APIRouter(prefix="/api/v1/admin", tags=["admin"])


class CreateUserRequest(BaseModel):
    username: str = Field(min_length=3, max_length=120)
    password: SecretStr = Field(min_length=15, max_length=128)
    role: Literal["marketing", "sales"]


def require_super_admin(request: Request) -> None:
    if request.state.role != "super_admin":
        raise HTTPException(status_code=403, detail="Akses khusus Super Admin")


@router.get("/users")
def list_users(request: Request):
    require_super_admin(request)
    users = get_auth_store().list_users()
    return success_response(users, "Daftar akun berhasil diambil")


@router.post("/users", status_code=201)
def create_user(payload: CreateUserRequest, request: Request):
    # Pemeriksaan di backend wajib, meskipun menu frontend nanti disembunyikan.
    require_super_admin(request)

    try:
        user = get_auth_store().create_user(
            payload.username,
            payload.password.get_secret_value(),
            payload.role,
        )
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc

    # Respons hanya berisi identitas akun, tidak pernah password atau hash-nya.
    return success_response(user, "Akun berhasil dibuat")


@router.delete("/users/{username}")
def deactivate_user(username: str, request: Request):
    require_super_admin(request)

    try:
        user = get_auth_store().deactivate_user(
            username,
            requested_by=request.state.username,
        )
    except ValueError as exc:
        message = str(exc)
        status_code = 404 if message == "User tidak ditemukan" else 400
        raise HTTPException(status_code=status_code, detail=message) from exc

    return success_response(user, "Akun berhasil dinonaktifkan")
