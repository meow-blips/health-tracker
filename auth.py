from passlib.context import CryptContext
from jose import JWTError, jwt
from datetime import datetime, timedelta
from itsdangerous import URLSafeTimedSerializer

SECRET_KEY = "healthtrack-secret-key-change-in-production-2026"
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 60 * 24 * 7  # 7 days

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")
serializer = URLSafeTimedSerializer(SECRET_KEY)


def hash_password(password: str) -> str:
    return pwd_context.hash(password)


def verify_password(plain_password: str, hashed_password: str) -> bool:
    return pwd_context.verify(plain_password, hashed_password)


def create_access_token(data: dict, expires_delta: timedelta | None = None) -> str:
    to_encode = data.copy()
    expire = datetime.utcnow() + (expires_delta or timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES))
    to_encode.update({"exp": expire})
    return jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)


def decode_access_token(token: str) -> dict | None:
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        return payload
    except JWTError:
        return None


def generate_reset_token(email: str) -> str:
    return serializer.dumps(email, salt="password-reset")


def verify_reset_token(token: str, max_age: int = 3600) -> str | None:
    try:
        return serializer.loads(token, salt="password-reset", max_age=max_age)
    except Exception:
        return None
