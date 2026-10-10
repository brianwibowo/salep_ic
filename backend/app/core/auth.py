"""Demo login with opaque, server-owned sessions; role changes require logout."""
from contextlib import contextmanager
import hashlib
import secrets
import sqlite3
import time
from typing import Literal

from fastapi import APIRouter, HTTPException, Request, Response
from pydantic import BaseModel
from app.core.config import settings
from app.core.responses import error_response, success_response
from app.services.lead_repository import DB_PATH

router = APIRouter(prefix="/api/v1/auth")
COOKIE = "salep_session"


@contextmanager
def connection():
    conn = sqlite3.connect(DB_PATH)
    conn.execute("CREATE TABLE IF NOT EXISTS sessions (token TEXT PRIMARY KEY, role TEXT NOT NULL, expires REAL NOT NULL)")
    try:
        with conn:
            yield conn
    finally:
        conn.close()


def session_role(request):
    token = request.cookies.get(COOKIE, "")
    with connection() as conn:
        row = conn.execute("SELECT role FROM sessions WHERE token=? AND expires>?", (hashlib.sha256(token.encode()).hexdigest(), time.time())).fetchone()
    return row[0] if row else None


async def enforce_access(request, call_next):
    path = request.url.path
    if path.startswith('/api/v1/') and not path.startswith('/api/v1/auth/'):
        role = session_role(request)
        if not role:
            return error_response('Silakan login terlebih dahulu', status_code=401)
        request.state.role = role
        if request.method not in {'GET', 'HEAD', 'OPTIONS'}:
            origin = request.headers.get('origin')
            # Behind a TLS-terminating reverse proxy, request.base_url may contain
            # the proxy's internal scheme/host rather than the browser's public URL.
            # Compare against configured public origins instead of that value.
            allowed_origins = {item.rstrip('/') for item in settings.cors_origins if item != '*'}
            if origin and origin.rstrip('/') not in allowed_origins:
                return error_response('Origin tidak diizinkan', status_code=403)
        if role == 'sales':
            allowed = (request.method == 'GET' and (path == '/api/v1/leads' or path == '/api/v1/leads/stats' or (path.startswith('/api/v1/leads/') and path.rsplit('/', 1)[-1] not in {'recent'}))) or (request.method == 'PATCH' and path.endswith('/sales-status'))
            if not allowed:
                return error_response('Akses khusus marketing', status_code=403)
        elif path.endswith('/sales-status'):
            return error_response('Akses khusus sales', status_code=403)
    return await call_next(request)


class Login(BaseModel):
    role: Literal['marketing', 'sales']


@router.post('/login')
def login(payload: Login, request: Request, response: Response):
    existing = session_role(request)
    if existing and existing != payload.role:
        raise HTTPException(409, 'Logout sebelum masuk dengan role lain')
    token = secrets.token_urlsafe(32)
    with connection() as conn:
        conn.execute('DELETE FROM sessions WHERE expires < ?', (time.time(),))
        if request.cookies.get(COOKIE):
            conn.execute('DELETE FROM sessions WHERE token=?', (hashlib.sha256(request.cookies[COOKIE].encode()).hexdigest(),))
        conn.execute('INSERT INTO sessions VALUES (?, ?, ?)', (hashlib.sha256(token.encode()).hexdigest(), payload.role, time.time()+86400))
    response.set_cookie(COOKIE, token, httponly=True, secure=settings.is_production, samesite='strict', max_age=86400)
    return success_response({'role': payload.role}, 'Login berhasil')


@router.get('/me')
def me(request: Request):
    role = session_role(request)
    if not role:
        raise HTTPException(401, 'Silakan login')
    return success_response({'role': role}, 'Sesi aktif')


@router.post('/logout')
def logout(request: Request, response: Response):
    with connection() as conn:
        conn.execute('DELETE FROM sessions WHERE token=?', (hashlib.sha256(request.cookies.get(COOKIE, '').encode()).hexdigest(),))
    response.delete_cookie(COOKIE)
    return success_response({'ok': True}, 'Logout berhasil')
