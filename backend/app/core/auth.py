"""Password authentication with server-owned roles and shared revocable sessions."""
from fastapi import APIRouter, HTTPException, Request, Response
from pydantic import BaseModel, ConfigDict, Field, SecretStr
from starlette.concurrency import run_in_threadpool
from app.core.config import settings
from app.core.responses import error_response, success_response
from app.services.auth_service import AuthenticationFailed, LoginThrottled, SessionConflict, get_auth_store

router = APIRouter(prefix="/api/v1/auth")
# Different name deliberately invalidates all legacy role-only demo sessions.
COOKIE = "salep_session_v2"


async def enforce_access(request, call_next):
    path = request.url.path
    if path.startswith('/api/v1/') and request.method not in {'GET', 'HEAD', 'OPTIONS'}:
        origin = request.headers.get('origin')
        allowed_origins = {item.rstrip('/') for item in settings.cors_origins}
        if (origin and origin.rstrip('/') not in allowed_origins) or request.headers.get('sec-fetch-site') == 'cross-site':
            return error_response('Origin tidak diizinkan', status_code=403)
    if path.startswith('/api/v1/') and not path.startswith('/api/v1/auth/') and request.method != 'OPTIONS':
        try:
            identity = await run_in_threadpool(get_auth_store().resolve, request.cookies.get(COOKIE, ''))
        except Exception:
            return error_response('Layanan autentikasi belum siap', status_code=503)
        role = identity['role'] if identity else None
        if not role:
            return error_response('Silakan login terlebih dahulu', status_code=401)
        request.state.role = role
        request.state.username = identity.get('username')
        if role == 'super_admin':
            if not path.startswith('/api/v1/admin/'):
                return error_response('Akses khusus Super Admin', status_code=403)
        elif role == 'sales':
            allowed = (
                request.method == 'GET' and (
                    path == '/api/v1/leads' or
                    path == '/api/v1/leads/stats' or
                    path in {'/api/v1/inaproc/final', '/api/v1/inaproc/final/summary'} or
                    path.startswith('/api/v1/spse/tender/') or
                    path.startswith('/api/v1/spse/leads/') or
                    (path.startswith('/api/v1/leads/') and path.rsplit('/', 1)[-1] not in {'recent'})
                )
            ) or (request.method == 'PATCH' and path.endswith('/sales-status'))
            if not allowed:
                return error_response('Akses khusus marketing', status_code=403)
        elif path.endswith('/sales-status'):
            return error_response('Akses khusus sales', status_code=403)
    response = await call_next(request)
    response.headers['X-Content-Type-Options'] = 'nosniff'
    response.headers['X-Frame-Options'] = 'DENY'
    response.headers['Referrer-Policy'] = 'same-origin'
    if path.startswith('/api/v1/'):
        response.headers['Cache-Control'] = 'no-store'
    if settings.is_production:
        response.headers['Strict-Transport-Security'] = 'max-age=31536000'
    return response


class Login(BaseModel):
    model_config = ConfigDict(extra='forbid')
    username: str = Field(min_length=1, max_length=120)
    password: SecretStr = Field(min_length=1, max_length=128)


@router.post('/login')
def login(payload: Login, request: Request, response: Response):
    try:
        token, identity = get_auth_store().login(
            payload.username, payload.password.get_secret_value(),
            request.client.host if request.client else 'unknown',
            request.cookies.get(COOKIE, ''),
        )
    except LoginThrottled:
        raise HTTPException(429, 'Terlalu banyak percobaan login; coba lagi nanti') from None
    except AuthenticationFailed:
        raise HTTPException(401, 'Username atau password tidak valid') from None
    except SessionConflict:
        raise HTTPException(409, 'Logout sebelum masuk dengan akun lain') from None
    response.set_cookie(COOKIE, token, httponly=True, secure=settings.is_production,
                        samesite='strict', max_age=settings.auth_session_ttl_seconds, path='/')
    response.delete_cookie('salep_session', path='/')
    return success_response(identity, 'Login berhasil')


@router.get('/me')
def me(request: Request):
    identity = get_auth_store().resolve(request.cookies.get(COOKIE, ''))
    if not identity:
        raise HTTPException(401, 'Silakan login')
    return success_response(identity, 'Sesi aktif')


@router.post('/logout')
def logout(request: Request, response: Response):
    get_auth_store().logout(request.cookies.get(COOKIE, ''))
    response.delete_cookie(COOKIE, path='/', secure=settings.is_production, httponly=True, samesite='strict')
    return success_response({'ok': True}, 'Logout berhasil')
