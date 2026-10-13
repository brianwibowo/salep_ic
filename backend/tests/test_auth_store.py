from __future__ import annotations

import pytest

from app.services.auth_service import AuthenticationFailed, AuthStore, password_hash


def test_password_sessions_are_revocable_and_shared(tmp_path):
    store = AuthStore(f"sqlite:///{tmp_path / 'auth.db'}", create_schema=True)
    identity = store.create_user("Marketing.User", "a-strong-test-passphrase", "marketing")

    token, session = store.login("marketing.user", "a-strong-test-passphrase", "127.0.0.1")
    assert session == identity
    assert store.resolve(token)["username"] == "marketing.user"

    with pytest.raises(AuthenticationFailed):
        store.login("marketing.user", "wrong-passphrase", "127.0.0.1")

    store.update_user("marketing.user", password="another-strong-passphrase")
    assert store.resolve(token) is None
    with pytest.raises(AuthenticationFailed):
        store.login("marketing.user", "a-strong-test-passphrase", "127.0.0.1")
    refreshed, _ = store.login("marketing.user", "another-strong-passphrase", "127.0.0.1")
    assert store.resolve(refreshed)["role"] == "marketing"


def test_password_policy_rejects_weak_values():
    with pytest.raises(ValueError):
        password_hash("too-short")
