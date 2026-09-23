"""Password-reset token helpers using itsdangerous timed serializers."""

from __future__ import annotations

from flask import current_app
from itsdangerous import BadSignature, SignatureExpired, URLSafeTimedSerializer


def _serializer() -> URLSafeTimedSerializer:
    return URLSafeTimedSerializer(
        current_app.config["SECRET_KEY"],
        salt="litera-password-reset",
    )


def make_reset_token(user_id: int, session_version: int) -> str:
    """Embed user id + session_version so a used reset cannot be replayed."""
    return _serializer().dumps({"uid": user_id, "sv": int(session_version or 0)})


def load_reset_token(token: str, max_age: int | None = None) -> dict | None:
    """Return the payload or None if the token is missing, expired, or forged."""
    if not token:
        return None
    age = max_age
    if age is None:
        age = int(current_app.config.get("PASSWORD_RESET_MAX_AGE", 3600))
    try:
        payload = _serializer().loads(token, max_age=age)
    except (BadSignature, SignatureExpired):
        return None
    if not isinstance(payload, dict) or "uid" not in payload:
        return None
    return payload
