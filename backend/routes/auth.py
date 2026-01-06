"""
Authentication routes

Provides endpoints for user authentication, registration, and password reset.
"""
import os
from fastapi import APIRouter, Depends, HTTPException, status, Request, Response
from sqlalchemy.orm import Session
from pydantic import BaseModel, EmailStr
from typing import Optional
import re

from database import get_db
from models import User, Organization, OrganizationMembership
from auth.utils import create_access_token, verify_password, get_password_hash
from auth.dependencies import get_current_active_user
from limiter import limiter

router = APIRouter(prefix="/api/auth", tags=["auth"])

# Cookie configuration
COOKIE_NAME = "access_token"
COOKIE_MAX_AGE = 60 * 60 * 24 * 7  # 7 days
ENVIRONMENT = os.getenv("ENVIRONMENT", "development")


def set_auth_cookie(response: Response, token: str):
    """Set httpOnly cookie with JWT token."""
    response.set_cookie(
        key=COOKIE_NAME,
        value=token,
        httponly=True,
        secure=ENVIRONMENT == "production",  # HTTPS only in production
        samesite="lax",
        max_age=COOKIE_MAX_AGE,
        path="/"
    )


def clear_auth_cookie(response: Response):
    """Clear the auth cookie on logout."""
    response.delete_cookie(key=COOKIE_NAME, path="/")


def validate_password(password: str) -> tuple[bool, str]:
    """Validate password meets security requirements."""
    if len(password) < 12:
        return False, "Password must be at least 12 characters"
    if not re.search(r"[A-Z]", password):
        return False, "Password must contain at least one uppercase letter"
    if not re.search(r"[a-z]", password):
        return False, "Password must contain at least one lowercase letter"
    if not re.search(r"\d", password):
        return False, "Password must contain at least one number"
    return True, ""


class LoginRequest(BaseModel):
    email: EmailStr
    password: str


class LoginResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"
    user: dict


class RegisterRequest(BaseModel):
    email: EmailStr
    password: str
    name: Optional[str] = None


class ForgotPasswordRequest(BaseModel):
    email: EmailStr


class ResetPasswordRequest(BaseModel):
    token: str
    new_password: str


@router.post("/login", response_model=LoginResponse)
@limiter.limit("5/minute")
async def login(
    request: Request,
    response: Response,
    login_data: LoginRequest,
    db: Session = Depends(get_db)
):
    """
    Login with email and password.

    Sets httpOnly cookie with JWT token for secure browser auth.
    Also returns token in response body for API clients.
    Rate limited to 5 attempts per minute per IP.
    """
    user = db.query(User).filter(User.email == login_data.email).first()

    if not user or not user.password_hash:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid email or password"
        )

    if not verify_password(login_data.password, user.password_hash):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid email or password"
        )

    if not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Account is inactive"
        )

    token = create_access_token(data={"sub": str(user.id)})

    # Set httpOnly cookie for browser clients
    set_auth_cookie(response, token)

    # Get user's organization
    membership = db.query(OrganizationMembership).filter(
        OrganizationMembership.user_id == user.id,
        OrganizationMembership.status == "active"
    ).first()

    user_data = {
        "id": str(user.id),
        "email": user.email,
        "name": user.name,
    }
    if membership:
        user_data["organization_id"] = str(membership.organization_id)

    return LoginResponse(
        access_token=token,
        user=user_data
    )


@router.post("/register", response_model=LoginResponse)
@limiter.limit("3/minute")
async def register(
    request: Request,
    response: Response,
    register_data: RegisterRequest,
    db: Session = Depends(get_db)
):
    """
    Register a new user.

    Rate limited to 3 registrations per minute per IP.
    """
    # Validate password strength
    is_valid, error_msg = validate_password(register_data.password)
    if not is_valid:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=error_msg
        )

    # Check if user exists
    existing = db.query(User).filter(User.email == register_data.email).first()
    if existing:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Email already registered"
        )

    # Create user
    user = User(
        email=register_data.email,
        password_hash=get_password_hash(register_data.password),
        name=register_data.name,
        is_active=True,
    )
    db.add(user)
    db.commit()
    db.refresh(user)

    # Create organization for the user
    org_name = register_data.name or register_data.email.split("@")[0]
    # Create a URL-safe slug
    base_slug = re.sub(r'[^a-z0-9]+', '-', org_name.lower()).strip('-')
    slug = base_slug or 'org'
    # Ensure unique slug
    counter = 1
    while db.query(Organization).filter(Organization.slug == slug).first():
        slug = f"{base_slug}-{counter}"
        counter += 1

    organization = Organization(
        name=f"{org_name}'s Organization",
        slug=slug,
        owner_id=user.id,
    )
    db.add(organization)
    db.commit()
    db.refresh(organization)

    # Create organization membership - registering user is account owner
    membership = OrganizationMembership(
        organization_id=organization.id,
        user_id=user.id,
        role="admin",
        is_account_owner=True,
        status="active",
    )
    db.add(membership)
    db.commit()

    # Create token
    token = create_access_token(data={"sub": str(user.id)})

    # Set httpOnly cookie for browser clients
    set_auth_cookie(response, token)

    return LoginResponse(
        access_token=token,
        user={
            "id": str(user.id),
            "email": user.email,
            "name": user.name,
            "organization_id": str(organization.id),
        }
    )


@router.post("/logout")
async def logout(response: Response):
    """
    Logout by clearing the auth cookie.

    For API clients using Bearer tokens, simply discard the token.
    """
    clear_auth_cookie(response)
    return {"message": "Logged out successfully"}


@router.get("/me")
async def get_current_user_info(
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """Get current user information."""
    # Get user's organization
    membership = db.query(OrganizationMembership).filter(
        OrganizationMembership.user_id == current_user.id,
        OrganizationMembership.status == "active"
    ).first()

    user_data = {
        "id": str(current_user.id),
        "email": current_user.email,
        "name": current_user.name,
        "email_verified": current_user.email_verified,
    }
    if membership:
        user_data["organization_id"] = str(membership.organization_id)

    return user_data


@router.post("/forgot-password")
@limiter.limit("3/minute")
async def forgot_password(request: Request, data: ForgotPasswordRequest, db: Session = Depends(get_db)):
    """
    Request a password reset.

    Always returns success to prevent email enumeration.
    Rate limited to 3 requests per minute per IP.
    """
    from services.password_reset_service import create_reset_token, send_reset_email

    # Create reset token (returns None if user not found)
    token = create_reset_token(db, data.email)

    # Send email only if token was created (user exists)
    if token:
        send_reset_email(data.email, token)

    # Always return success to prevent email enumeration
    return {
        "message": "If an account exists with this email, you will receive a password reset link shortly."
    }


@router.post("/reset-password")
@limiter.limit("5/minute")
async def reset_password(request: Request, data: ResetPasswordRequest, db: Session = Depends(get_db)):
    """
    Reset password using a valid reset token.

    Rate limited to 5 attempts per minute per IP.
    """
    from services.password_reset_service import reset_password as do_reset_password

    # Validate password strength
    is_valid, error_msg = validate_password(data.new_password)
    if not is_valid:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=error_msg
        )

    # Attempt to reset password
    success = do_reset_password(db, data.token, data.new_password)

    if not success:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid or expired reset token"
        )

    return {"message": "Password reset successful. You can now log in with your new password."}
