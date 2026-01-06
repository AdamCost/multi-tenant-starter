"""
Password Reset Token Model
"""
import uuid
from datetime import datetime
from sqlalchemy import Column, String, DateTime, ForeignKey
from sqlalchemy.orm import relationship

from database import Base
from .types import GUID


class PasswordResetToken(Base):
    """
    Stores password reset tokens.
    Tokens are hashed for security - the plain token is only sent via email.
    """
    __tablename__ = "password_reset_tokens"

    id = Column(GUID(), primary_key=True, default=uuid.uuid4)
    user_id = Column(GUID(), ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    token_hash = Column(String(255), nullable=False, index=True)
    expires_at = Column(DateTime, nullable=False)
    used_at = Column(DateTime, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)

    # Relationship
    user = relationship("User", backref="password_reset_tokens")

    def is_valid(self) -> bool:
        """Check if token is valid (not expired and not used)."""
        if self.used_at is not None:
            return False
        if datetime.utcnow() > self.expires_at:
            return False
        return True

    def mark_used(self):
        """Mark token as used."""
        self.used_at = datetime.utcnow()
