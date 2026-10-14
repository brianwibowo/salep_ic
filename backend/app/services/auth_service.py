"""Password authentication and revocable sessions shared by API replicas."""
from functools import lru_cache
import hashlib
from pathlib import Path
import re
import secrets
import time
import uuid

from argon2 import PasswordHasher
from argon2.exceptions import InvalidHashError, VerificationError
from sqlalchemy import case, delete, select
from sqlalchemy.orm import Session

from app.core.config import settings
from app.db.auth_models import AuthBase, AuthLoginBucket, AuthSession, AuthUser
from app.db.engine import build_engine, normalize_database_url

hasher = PasswordHasher(time_cost=3, memory_cost=65536, parallelism=1)
_dummy_hash = hasher.hash(secrets.token_urlsafe(32))


class AuthenticationFailed(Exception):
    pass


class LoginThrottled(Exception):
    pass


class SessionConflict(Exception):
    pass


def token_digest(token: str) -> str:
    return hashlib.sha256(token.encode()).hexdigest()


def normalize_username(value: str) -> str:
    value = value.strip().casefold()
    if not re.fullmatch(r'[a-z0-9][a-z0-9_.@+-]{2,119}', value):
        raise ValueError('Username harus 3–120 karakter: huruf, angka, _, ., @, +, atau -')
    return value


def password_hash(password: str) -> str:
    if not 15 <= len(password) <= 128:
        raise ValueError('Password harus 15–128 karakter; gunakan passphrase unik')
    return hasher.hash(password)


class AuthStore:
    def __init__(self, url: str, *, create_schema: bool = False):
        self.engine = build_engine(url)
        if create_schema:
            AuthBase.metadata.create_all(self.engine)

    @staticmethod
    def _identity(user: AuthUser) -> dict:
        return {'user_id': user.id, 'username': user.username, 'role': user.role}

    def resolve(self, token: str) -> dict | None:
        if not token or len(token) > 128:
            return None
        with Session(self.engine) as session:
            user = session.scalar(select(AuthUser).join(AuthSession).where(
                AuthSession.token_hash == token_digest(token),
                AuthSession.expires_at > time.time(),
                AuthSession.user_version == AuthUser.version,
                AuthUser.active.is_(True),
            ))
            return self._identity(user) if user else None

    def _throttle(self, username: str, client_ip: str) -> None:
        # Atomic upsert works across workers/replicas, including unknown users.
        from sqlalchemy.dialects.postgresql import insert as pg_insert
        from sqlalchemy.dialects.sqlite import insert as sqlite_insert
        insert = pg_insert if self.engine.dialect.name == 'postgresql' else sqlite_insert
        now = time.time()
        counts = []
        with Session(self.engine) as session:
            for scope, identity, limit in (
                ('account', username, settings.auth_login_account_limit),
                ('ip', client_ip, settings.auth_login_ip_limit),
            ):
                key = token_digest(f'{scope}:{identity}')
                fresh = AuthLoginBucket.expires_at <= now
                stmt = insert(AuthLoginBucket).values(key=key, count=1, expires_at=now + settings.auth_login_window_seconds)
                stmt = stmt.on_conflict_do_update(index_elements=['key'], set_={
                    'count': case((fresh, 1), else_=AuthLoginBucket.count + 1),
                    'expires_at': case((fresh, now + settings.auth_login_window_seconds), else_=AuthLoginBucket.expires_at),
                }).returning(AuthLoginBucket.count)
                counts.append((session.scalar(stmt), limit))
            session.commit()
        if any(count > limit for count, limit in counts):
            raise LoginThrottled()

    def _clear_login_buckets(self, username: str, client_ip: str) -> None:
        keys = [token_digest(f"account:{username}"), token_digest(f"ip:{client_ip}")]
        with Session(self.engine) as session:
            session.execute(delete(AuthLoginBucket).where(AuthLoginBucket.key.in_(keys)))
            session.commit()

    def login(self, username: str, password: str, client_ip: str, previous_token: str = '') -> tuple[str, dict]:
        username = username.strip().casefold()
        self._throttle(username, client_ip)
        with Session(self.engine) as session:
            # Lock the user against password reset/deactivation while issuing a session.
            user = session.scalar(select(AuthUser).where(AuthUser.username == username).with_for_update())
            try:
                valid = hasher.verify(user.password_hash if user else _dummy_hash, password)
            except (VerificationError, InvalidHashError):
                valid = False
            if not valid or user is None or not user.active:
                raise AuthenticationFailed()
            previous = session.get(AuthSession, token_digest(previous_token)) if previous_token else None
            if previous and previous.expires_at > time.time() and previous.user_id != user.id:
                raise SessionConflict()
            if previous:
                session.delete(previous)
            if hasher.check_needs_rehash(user.password_hash):
                user.password_hash = hasher.hash(password)
            token = secrets.token_urlsafe(32)
            now = time.time()
            session.add(AuthSession(token_hash=token_digest(token), user_id=user.id, user_version=user.version,
                                    created_at=now, expires_at=now + settings.auth_session_ttl_seconds))
            session.commit()
            self._clear_login_buckets(username, client_ip)
            return token, self._identity(user)

    def logout(self, token: str) -> None:
        with Session(self.engine) as session:
            session.execute(delete(AuthSession).where(AuthSession.token_hash == token_digest(token)))
            session.commit()

    def create_user(self, username: str, password: str, role: str) -> dict:
        username = normalize_username(username)
        if role not in {'marketing', 'sales', 'super_admin'}:
            raise ValueError('Role tidak valid')
        hashed = password_hash(password)
        with Session(self.engine) as session:
            if session.scalar(select(AuthUser.id).where(AuthUser.username == username)):
                raise ValueError('Username sudah terdaftar; gunakan reset-password')
            user = AuthUser(id=uuid.uuid4().hex, username=username, password_hash=hashed, role=role,
                            active=True, version=1, created_at=time.time())
            session.add(user)
            session.commit()
            return self._identity(user)

    def list_users(self) -> list[dict]:
        with Session(self.engine) as session:
            users = session.scalars(
                select(AuthUser).order_by(AuthUser.created_at.desc(), AuthUser.username.asc())
            ).all()
            return [
                {
                    'user_id': user.id,
                    'username': user.username,
                    'role': user.role,
                    'active': user.active,
                    'created_at': user.created_at,
                }
                for user in users
            ]

    def deactivate_user(self, username: str, *, requested_by: str) -> dict:
        username = normalize_username(username)
        requested_by = normalize_username(requested_by)
        if username == requested_by:
            raise ValueError('Akun yang sedang digunakan tidak dapat dinonaktifkan')

        with Session(self.engine) as session:
            user = session.scalar(
                select(AuthUser).where(AuthUser.username == username).with_for_update()
            )
            if not user:
                raise ValueError('User tidak ditemukan')
            if user.role == 'super_admin':
                raise ValueError('Akun Super Admin tidak dapat dinonaktifkan dari halaman ini')

            if user.active:
                user.active = False
                user.version += 1
                # Revoke existing sessions so the account loses access immediately.
                session.execute(delete(AuthSession).where(AuthSession.user_id == user.id))
                session.commit()

            return {
                'user_id': user.id,
                'username': user.username,
                'role': user.role,
                'active': user.active,
            }

    def update_user(self, username: str, *, password: str | None = None, active: bool | None = None, role: str | None = None) -> None:
        hashed = password_hash(password) if password is not None else None
        with Session(self.engine) as session:
            user = session.scalar(select(AuthUser).where(AuthUser.username == normalize_username(username)).with_for_update())
            if not user:
                raise ValueError('User tidak ditemukan')
            if hashed:
                user.password_hash = hashed
            if active is not None:
                user.active = active
            if role is not None:
                if role not in {'marketing', 'sales', 'super_admin'}:
                    raise ValueError('Role tidak valid')
                user.role = role
            user.version += 1
            session.execute(delete(AuthSession).where(AuthSession.user_id == user.id))
            session.commit()

    def cleanup(self) -> None:
        with Session(self.engine) as session:
            session.execute(delete(AuthSession).where(AuthSession.expires_at <= time.time()))
            session.execute(delete(AuthLoginBucket).where(AuthLoginBucket.expires_at <= time.time()))
            session.commit()


@lru_cache(maxsize=4)
def _store(url: str, development_sqlite: bool) -> AuthStore:
    return AuthStore(url, create_schema=development_sqlite)


def get_auth_store() -> AuthStore:
    url = normalize_database_url(settings.auth_database_url or settings.database_url)
    if settings.is_production and not url.startswith('postgresql+psycopg://'):
        raise RuntimeError('Production auth requires PostgreSQL DATABASE_URL or AUTH_DATABASE_URL')
    if not url:
        path = Path(__file__).resolve().parents[2] / 'data' / 'salep-auth.db'
        path.parent.mkdir(parents=True, exist_ok=True)
        url = f'sqlite:///{path}'
    return _store(url, not settings.is_production and url.startswith('sqlite:'))


# Test and process lifecycle hooks can invalidate a store when configuration changes.
get_auth_store.cache_clear = _store.cache_clear  # type: ignore[attr-defined]
