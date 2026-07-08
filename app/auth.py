"""Password login, signed-cookie sessions, and a simple rate limiter.

Single-user app: one shared password protects all routes. Sessions are signed
with itsdangerous so the cookie cannot be forged. Failed logins are rate
limited per client IP to blunt brute-force attempts.
"""

from __future__ import annotations

import hmac
import time
from dataclasses import dataclass, field

from itsdangerous import BadSignature, URLSafeTimedSerializer

SESSION_COOKIE = "focus_session"
SESSION_MAX_AGE = 60 * 60 * 24 * 14  # 14 days
_MAX_ATTEMPTS = 5
_WINDOW_SECONDS = 300


@dataclass
class RateLimiter:
    """Fixed-window failed-attempt counter keyed by client identifier."""

    _hits: dict[str, list[float]] = field(default_factory=dict)

    def blocked(self, key: str, now: float | None = None) -> bool:
        """Return True if ``key`` has exceeded the allowed attempts."""
        now = time.time() if now is None else now
        recent = [t for t in self._hits.get(key, []) if now - t < _WINDOW_SECONDS]
        self._hits[key] = recent
        return len(recent) >= _MAX_ATTEMPTS

    def record_failure(self, key: str, now: float | None = None) -> None:
        """Record a failed attempt for ``key``."""
        now = time.time() if now is None else now
        self._hits.setdefault(key, []).append(now)

    def reset(self, key: str) -> None:
        """Clear recorded attempts after a successful login."""
        self._hits.pop(key, None)


class Auth:
    """Verify passwords and issue/validate session tokens.

    Args:
        password: The shared login password.
        secret_key: Key used to sign session cookies.
    """

    def __init__(self, password: str, secret_key: str) -> None:
        self._password = password
        self._serializer = URLSafeTimedSerializer(secret_key, salt="focus-session")
        self.rate_limiter = RateLimiter()

    def check_password(self, candidate: str) -> bool:
        """Constant-time comparison of a candidate password."""
        return hmac.compare_digest(candidate or "", self._password)

    def issue_token(self) -> str:
        """Create a signed session token."""
        return self._serializer.dumps({"ok": True})

    def valid_token(self, token: str | None) -> bool:
        """Validate a session token, honoring its max age."""
        if not token:
            return False
        try:
            self._serializer.loads(token, max_age=SESSION_MAX_AGE)
            return True
        except (BadSignature, Exception):
            return False
