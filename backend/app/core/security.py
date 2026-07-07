"""JWT creation/verification, Google token verification, and at-rest encryption."""
from __future__ import annotations

import base64
import hashlib
from datetime import datetime, timedelta, timezone

from cryptography.fernet import Fernet, InvalidToken
from jose import JWTError, jwt

from app.core.config import settings
from app.core.exceptions import UnauthorizedError


# ---------- JWT ----------
def create_access_token(user_id: str, email: str) -> str:
    now = datetime.now(timezone.utc)
    payload = {
        "sub": user_id,
        "email": email,
        "iat": int(now.timestamp()),
        "exp": int((now + timedelta(minutes=settings.jwt_expire_minutes)).timestamp()),
    }
    return jwt.encode(payload, settings.jwt_secret, algorithm=settings.jwt_algorithm)


def decode_access_token(token: str) -> dict:
    try:
        return jwt.decode(token, settings.jwt_secret, algorithms=[settings.jwt_algorithm])
    except JWTError as exc:  # noqa: BLE001
        raise UnauthorizedError("Invalid or expired token") from exc


# ---------- Google OAuth ----------
def verify_google_id_token(id_token_str: str) -> dict:
    """Verify a Google ID token, returning {sub, email, name}. Raises UnauthorizedError."""
    from google.auth.transport import requests as google_requests
    from google.oauth2 import id_token as google_id_token

    try:
        info = google_id_token.verify_oauth2_token(
            id_token_str, google_requests.Request(), settings.google_client_id
        )
    except ValueError as exc:  # noqa: BLE001
        raise UnauthorizedError("Google token verification failed") from exc
    return {"sub": info["sub"], "email": info.get("email", ""), "name": info.get("name", "")}


# ---------- Encryption at rest (Fernet) ----------
def _fernet() -> Fernet:
    key = settings.encryption_key
    if not key:
        # Derive a deterministic dev key from the JWT secret so local runs work without setup.
        digest = hashlib.sha256(settings.jwt_secret.encode()).digest()
        key = base64.urlsafe_b64encode(digest).decode()
    return Fernet(key.encode() if isinstance(key, str) else key)


def encrypt_text(plaintext: str) -> str:
    return _fernet().encrypt(plaintext.encode()).decode()


def decrypt_text(ciphertext: str) -> str:
    try:
        return _fernet().decrypt(ciphertext.encode()).decode()
    except (InvalidToken, ValueError):
        # Tolerate legacy/plaintext rows in dev.
        return ciphertext
