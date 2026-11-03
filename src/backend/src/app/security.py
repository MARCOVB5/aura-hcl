from datetime import datetime, timedelta, timezone

import jwt
from pwdlib import PasswordHash

from app.config import settings

password_hasher = PasswordHash.recommended()
TOKEN_LIFETIME_SECONDS = 8 * 60 * 60


def hash_password(password: str) -> str:
    return password_hasher.hash(password)


def verify_password(password: str, password_hash: str) -> bool:
    return password_hasher.verify(password, password_hash)


def create_access_token(user_id: int) -> str:
    now = datetime.now(timezone.utc)
    return jwt.encode(
        {"sub": str(user_id), "iat": now, "exp": now + timedelta(seconds=TOKEN_LIFETIME_SECONDS)},
        settings.jwt_secret,
        algorithm="HS256",
    )


def decode_user_id(token: str) -> int:
    claims = jwt.decode(
        token, settings.jwt_secret, algorithms=["HS256"],
        options={"require": ["sub", "iat", "exp"]},
    )
    subject = claims["sub"]
    if not isinstance(subject, str) or not subject.isascii() or not subject.isdecimal():
        raise jwt.InvalidTokenError("Invalid subject")
    user_id = int(subject)
    if not 0 < user_id < 2**64:
        raise jwt.InvalidTokenError("Invalid subject")
    return user_id
