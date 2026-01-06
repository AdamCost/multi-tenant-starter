"""
Password Reset Service - Handles password reset token generation and validation
"""
import os
import secrets
import hashlib
from datetime import datetime, timedelta
from typing import Optional

from sqlalchemy.orm import Session

from models import User, PasswordResetToken
from auth.utils import get_password_hash
from logging_config import get_logger

logger = get_logger(__name__)

# Token configuration
TOKEN_LENGTH = 32  # 256 bits of entropy
TOKEN_EXPIRY_HOURS = 1  # 1 hour expiry


def generate_reset_token() -> str:
    """Generate a cryptographically secure reset token."""
    return secrets.token_urlsafe(TOKEN_LENGTH)


def hash_token(token: str) -> str:
    """Hash a token for secure storage."""
    return hashlib.sha256(token.encode()).hexdigest()


def create_reset_token(db: Session, email: str) -> Optional[str]:
    """
    Create a password reset token for a user.

    Returns the plain token (to be sent via email) or None if user not found.
    The token hash is stored in the database.
    """
    # Find user by email (case-insensitive)
    user = db.query(User).filter(
        User.email.ilike(email)
    ).first()

    if not user:
        logger.debug(f"Password reset requested for non-existent email")
        return None

    if not user.is_active:
        logger.debug(f"Password reset requested for inactive user")
        return None

    # Generate token
    plain_token = generate_reset_token()
    token_hash = hash_token(plain_token)

    # Create reset token record
    reset_token = PasswordResetToken(
        user_id=user.id,
        token_hash=token_hash,
        expires_at=datetime.utcnow() + timedelta(hours=TOKEN_EXPIRY_HOURS)
    )

    db.add(reset_token)
    db.commit()

    logger.info(f"Password reset token created for user {user.id}")
    return plain_token


def validate_reset_token(db: Session, token: str) -> Optional[PasswordResetToken]:
    """
    Validate a password reset token.

    Returns the token record if valid, None otherwise.
    """
    token_hash = hash_token(token)

    reset_token = db.query(PasswordResetToken).filter(
        PasswordResetToken.token_hash == token_hash
    ).first()

    if not reset_token:
        logger.debug("Invalid password reset token")
        return None

    if not reset_token.is_valid():
        logger.debug("Expired or used password reset token")
        return None

    return reset_token


def reset_password(db: Session, token: str, new_password: str) -> bool:
    """
    Reset a user's password using a valid reset token.

    Returns True if successful, False otherwise.
    """
    reset_token = validate_reset_token(db, token)

    if not reset_token:
        return False

    # Get the user
    user = db.query(User).filter(User.id == reset_token.user_id).first()

    if not user:
        logger.error(f"User not found for valid reset token")
        return False

    # Update password
    user.password_hash = get_password_hash(new_password)

    # Mark token as used
    reset_token.mark_used()

    db.commit()

    logger.info(f"Password reset successful for user {user.id}")
    return True


def send_reset_email(email: str, token: str, base_url: str = None) -> bool:
    """
    Send password reset email.

    Returns True if email was sent successfully, False otherwise.
    """
    if base_url is None:
        base_url = os.getenv("FRONTEND_URL", "http://localhost:5173")

    reset_url = f"{base_url}/reset-password?token={token}"

    sendgrid_api_key = os.getenv("SENDGRID_API_KEY")
    app_name = os.getenv("APP_NAME", "Starter")

    if not sendgrid_api_key:
        # Log for development - email not configured
        logger.debug(f"Would send password reset email to {email}")
        logger.debug(f"Reset URL: {reset_url}")
        return True  # Return True in dev mode

    try:
        import sendgrid
        from sendgrid.helpers.mail import Mail, Email, To, Content

        sg = sendgrid.SendGridAPIClient(api_key=sendgrid_api_key)

        from_email = Email(os.getenv("SENDGRID_FROM_EMAIL", "noreply@example.com"))
        to_email = To(email)
        subject = f"Reset Your Password - {app_name}"

        html_content = f"""
        <html>
        <body style="font-family: system-ui, -apple-system, sans-serif; max-width: 600px; margin: 0 auto; padding: 20px; background-color: #F8FAFC;">
            <div style="background-color: white; border-radius: 16px; padding: 32px; box-shadow: 0 1px 3px rgba(0,0,0,0.1);">
                <div style="text-align: center; margin-bottom: 24px;">
                    <div style="width: 48px; height: 48px; background: linear-gradient(135deg, #2563EB, #7C3AED); border-radius: 12px; margin: 0 auto 16px; display: flex; align-items: center; justify-content: center;">
                        <span style="color: white; font-weight: bold; font-size: 24px;">S</span>
                    </div>
                    <h1 style="color: #0F172A; font-size: 24px; margin: 0;">Reset Your Password</h1>
                </div>

                <p style="color: #334155; font-size: 16px; line-height: 1.6;">
                    You requested to reset your password for your {app_name} account.
                </p>
                <p style="color: #334155; font-size: 16px; line-height: 1.6;">
                    Click the button below to set a new password. This link expires in 1 hour.
                </p>

                <div style="margin: 32px 0; text-align: center;">
                    <a href="{reset_url}"
                       style="display: inline-block; background: linear-gradient(135deg, #2563EB, #7C3AED); color: white; padding: 14px 28px; text-decoration: none; border-radius: 12px; font-weight: 600; font-size: 16px;">
                        Reset Password
                    </a>
                </div>

                <p style="color: #475569; font-size: 14px; line-height: 1.6;">
                    If you didn't request this, you can safely ignore this email. Your password will remain unchanged.
                </p>

                <hr style="border: none; border-top: 1px solid #E2E8F0; margin: 24px 0;" />

                <p style="color: #94A3B8; font-size: 12px; text-align: center;">
                    {app_name}
                </p>
            </div>
        </body>
        </html>
        """

        message = Mail(
            from_email=from_email,
            to_emails=to_email,
            subject=subject,
            html_content=Content("text/html", html_content)
        )

        response = sg.send(message)
        success = response.status_code in [200, 201, 202]

        if success:
            logger.info(f"Password reset email sent to {email}")
        else:
            logger.warning(f"Failed to send password reset email, status: {response.status_code}")

        return success

    except Exception as e:
        logger.error(f"Failed to send password reset email: {e}")
        return False


def cleanup_expired_tokens(db: Session) -> int:
    """
    Clean up expired and used tokens older than 24 hours.

    Returns the number of tokens deleted.
    """
    cutoff = datetime.utcnow() - timedelta(hours=24)

    deleted = db.query(PasswordResetToken).filter(
        (PasswordResetToken.expires_at < datetime.utcnow()) |
        (PasswordResetToken.used_at.isnot(None) & (PasswordResetToken.used_at < cutoff))
    ).delete()

    db.commit()

    if deleted > 0:
        logger.info(f"Cleaned up {deleted} expired password reset tokens")

    return deleted
