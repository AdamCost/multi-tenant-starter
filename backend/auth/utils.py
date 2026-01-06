"""
Authentication utilities - shared JWT validation with main app
"""
import os
import sys
import logging
from datetime import datetime, timedelta
from typing import Optional

from jose import jwt, JWTError
from passlib.context import CryptContext

logger = logging.getLogger(__name__)

# Password hashing
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")


def _get_secret_key() -> str:
    """Get secret key, failing fast in production if not set."""
    key = os.getenv("SECRET_KEY") or os.getenv("SHARED_SECRET_KEY")

    if key:
        return key

    # Only allow default in development
    environment = os.getenv("ENVIRONMENT", "development").lower()
    if environment in ("development", "dev", "local"):
        logger.warning("Using development SECRET_KEY. Do not use in production!")
        return "dev-secret-key-change-in-production"

    # Fail hard in production/staging
    logger.critical("SECRET_KEY environment variable is required in production")
    sys.exit(1)


# JWT Settings
SECRET_KEY = _get_secret_key()
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = int(os.getenv("ACCESS_TOKEN_EXPIRE_MINUTES", "240"))  # 4 hours default


def verify_password(plain_password: str, hashed_password: str) -> bool:
    """Verify a password against its hash."""
    return pwd_context.verify(plain_password, hashed_password)


def get_password_hash(password: str) -> str:
    """Generate password hash."""
    return pwd_context.hash(password)


def create_access_token(data: dict, expires_delta: Optional[timedelta] = None) -> str:
    """Create a JWT access token."""
    to_encode = data.copy()

    if expires_delta:
        expire = datetime.utcnow() + expires_delta
    else:
        expire = datetime.utcnow() + timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)

    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)

    return encoded_jwt


def verify_token(token: str) -> Optional[dict]:
    """
    Verify a JWT token and return its payload.
    """
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        return payload
    except JWTError:
        return None


def decode_token(token: str) -> Optional[str]:
    """Decode token and return user ID (sub claim)."""
    payload = verify_token(token)
    if payload:
        return payload.get("sub")
    return None
