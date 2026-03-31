import bcrypt
from jose import JWTError, jwt
from datetime import datetime, timedelta
from itsdangerous import URLSafeTimedSerializer
from config import get_settings

settings = get_settings()
serializer = URLSafeTimedSerializer(settings.SECRET_KEY)


def hash_password(password: str) -> str:
    pwd_bytes = password.encode("utf-8")[:72]
    salt = bcrypt.gensalt()
    return bcrypt.hashpw(pwd_bytes, salt).decode("utf-8")


def verify_password(plain_password: str, hashed_password: str) -> bool:
    try:
        pwd_bytes = plain_password.encode("utf-8")[:72]
        hash_bytes = hashed_password.encode("utf-8")
        return bcrypt.checkpw(pwd_bytes, hash_bytes)
    except Exception:
        return False


def create_access_token(data: dict, expires_delta: timedelta | None = None) -> str:
    to_encode = data.copy()
    expire = datetime.utcnow() + (
        expires_delta or timedelta(days=settings.ACCESS_TOKEN_EXPIRE_DAYS)
    )
    to_encode.update({"exp": expire, "iat": datetime.utcnow()})
    return jwt.encode(to_encode, settings.SECRET_KEY, algorithm=settings.ALGORITHM)


def decode_access_token(token: str) -> dict | None:
    try:
        payload = jwt.decode(token, settings.SECRET_KEY, algorithms=[settings.ALGORITHM])
        if payload.get("exp") and datetime.utcfromtimestamp(payload["exp"]) < datetime.utcnow():
            return None
        return payload
    except JWTError:
        return None


def generate_reset_token(email: str) -> str:
    return serializer.dumps(email, salt="password-reset")


def verify_reset_token(token: str, max_age: int | None = None) -> str | None:
    try:
        return serializer.loads(
            token, salt="password-reset",
            max_age=max_age or settings.RESET_TOKEN_MAX_AGE,
        )
    except Exception:
        return None
