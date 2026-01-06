"""
User model for authentication (shared with main app)
"""
from sqlalchemy import Column, String, DateTime, Boolean
from datetime import datetime
import uuid

from database import Base
from .types import GUID


class User(Base):
    """
    User account model.
    """
    __tablename__ = "users"

    id = Column(GUID(), primary_key=True, default=uuid.uuid4)
    email = Column(String(255), unique=True, nullable=False, index=True)
    password_hash = Column(String(255), nullable=True)  # Nullable for SSO users
    name = Column(String(255), nullable=True)

    # Account status
    is_active = Column(Boolean, default=True)
    email_verified = Column(Boolean, default=False)

    # SSO
    google_id = Column(String(255), unique=True, nullable=True)
    microsoft_id = Column(String(255), unique=True, nullable=True)

    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)

    def __repr__(self):
        return f"<User(id={self.id}, email={self.email})>"
