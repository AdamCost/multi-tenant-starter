"""
FastAPI authentication dependencies

Supports both Bearer token authentication (for API clients)
and httpOnly cookie authentication (for browser clients).
"""
from uuid import UUID
from typing import Optional

from fastapi import Depends, HTTPException, status, Request, Cookie
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from sqlalchemy.orm import Session

from database import get_db
from models import User
from .utils import verify_token

# HTTP Bearer scheme for JWT tokens (auto_error=False to allow cookie fallback)
security = HTTPBearer(auto_error=False)

# Cookie name must match routes/auth.py
COOKIE_NAME = "access_token"


async def get_current_user(
    request: Request,
    credentials: Optional[HTTPAuthorizationCredentials] = Depends(security),
    db: Session = Depends(get_db)
) -> User:
    """
    Get the current user from JWT token.

    Supports two authentication methods:
    1. Bearer token in Authorization header (for API clients)
    2. httpOnly cookie (for browser clients)

    Bearer token takes precedence if both are present.
    """
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )

    token = None

    # Try Bearer token first (API clients)
    if credentials:
        token = credentials.credentials
    else:
        # Fall back to httpOnly cookie (browser clients)
        token = request.cookies.get(COOKIE_NAME)

    if not token:
        raise credentials_exception

    payload = verify_token(token)

    if payload is None:
        raise credentials_exception

    user_id_str: str = payload.get("sub")
    if user_id_str is None:
        raise credentials_exception

    try:
        user_id = UUID(user_id_str)
    except ValueError:
        raise credentials_exception

    user = db.query(User).filter(User.id == user_id).first()

    if user is None:
        raise credentials_exception

    return user


async def get_current_active_user(
    current_user: User = Depends(get_current_user)
) -> User:
    """Ensure the current user is active."""
    if not current_user.is_active:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Inactive user"
        )
    return current_user


def get_optional_user(
    request: Request,
    credentials: Optional[HTTPAuthorizationCredentials] = Depends(security),
    db: Session = Depends(get_db)
) -> Optional[User]:
    """
    Get the current user if authenticated, otherwise return None.

    Supports both Bearer token and httpOnly cookie authentication.
    Useful for endpoints that can work with or without authentication.
    """
    token = None

    # Try Bearer token first
    if credentials:
        token = credentials.credentials
    else:
        # Fall back to cookie
        token = request.cookies.get(COOKIE_NAME)

    if not token:
        return None

    payload = verify_token(token)
    if payload is None:
        return None

    user_id_str = payload.get("sub")
    if user_id_str is None:
        return None

    try:
        user_id = UUID(user_id_str)
    except ValueError:
        return None

    return db.query(User).filter(User.id == user_id).first()
