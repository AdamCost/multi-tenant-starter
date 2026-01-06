"""
Organization models for multi-tenancy
"""
import secrets
from sqlalchemy import Column, String, DateTime, ForeignKey, Boolean
from sqlalchemy.orm import relationship
from datetime import datetime, timedelta
import uuid

from database import Base
from .types import GUID


class Organization(Base):
    """
    Organization - represents a tenant/team in the multi-tenant system.
    """
    __tablename__ = "organizations"

    id = Column(GUID(), primary_key=True, default=uuid.uuid4)
    name = Column(String(255), nullable=False)
    slug = Column(String(100), unique=True, nullable=False, index=True)
    owner_id = Column(GUID(), ForeignKey("users.id", ondelete="SET NULL"), nullable=True)

    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)

    # Relationships
    owner = relationship("User", backref="owned_organizations", foreign_keys=[owner_id])
    memberships = relationship("OrganizationMembership", back_populates="organization", cascade="all, delete-orphan")

    def __repr__(self):
        return f"<Organization(id={self.id}, name={self.name})>"


class OrganizationMembership(Base):
    """
    Organization membership - links users to organizations (teams).

    Roles:
    - admin: Full access, can manage team members
    - editor: Can create/edit content
    - viewer: Read-only access
    """
    __tablename__ = "organization_memberships"

    id = Column(GUID(), primary_key=True, default=uuid.uuid4)
    organization_id = Column(GUID(), ForeignKey("organizations.id", ondelete="CASCADE"), nullable=False, index=True)
    user_id = Column(GUID(), ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)

    role = Column(String(50), default="viewer", nullable=False)  # admin, editor, viewer
    is_account_owner = Column(Boolean, default=False, nullable=False)
    status = Column(String(50), default="active", nullable=False)  # active, invited, suspended

    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)

    # Relationships
    organization = relationship("Organization", back_populates="memberships")
    user = relationship("User", backref="organization_memberships")

    def can_manage_team(self) -> bool:
        """Check if user can add/remove team members."""
        return self.role == "admin"

    def can_edit(self) -> bool:
        """Check if user can create/edit content."""
        return self.role in ("admin", "editor")

    def can_view(self) -> bool:
        """Check if user can view content."""
        return self.role in ("admin", "editor", "viewer")

    def is_admin(self) -> bool:
        return self.role == "admin"

    def __repr__(self):
        return f"<OrganizationMembership(org={self.organization_id}, user={self.user_id}, role={self.role})>"


class OrganizationInvite(Base):
    """
    Pending invitation to join an organization.

    Allows admins to invite users by email even if they don't have an account yet.
    The invited user must create an account to accept the invitation.
    """
    __tablename__ = "organization_invites"

    id = Column(GUID(), primary_key=True, default=uuid.uuid4)
    organization_id = Column(GUID(), ForeignKey("organizations.id", ondelete="CASCADE"), nullable=False, index=True)
    email = Column(String(255), nullable=False, index=True)
    role = Column(String(50), default="viewer", nullable=False)  # editor, viewer
    token = Column(String(255), unique=True, nullable=False, index=True)
    invited_by = Column(GUID(), ForeignKey("users.id", ondelete="SET NULL"), nullable=True)
    status = Column(String(50), default="pending", nullable=False)  # pending, accepted, expired, cancelled

    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    expires_at = Column(DateTime, nullable=False)

    # Relationships
    organization = relationship("Organization", backref="invites")
    inviter = relationship("User", backref="sent_invites", foreign_keys=[invited_by])

    @staticmethod
    def generate_token():
        """Generate a secure random token for the invite link."""
        return secrets.token_urlsafe(32)

    @staticmethod
    def default_expiry():
        """Return default expiration time (7 days from now)."""
        return datetime.utcnow() + timedelta(days=7)

    def is_expired(self) -> bool:
        """Check if the invitation has expired."""
        return datetime.utcnow() > self.expires_at

    def is_valid(self) -> bool:
        """Check if the invitation can still be accepted."""
        return self.status == "pending" and not self.is_expired()

    def __repr__(self):
        return f"<OrganizationInvite(org={self.organization_id}, email={self.email}, status={self.status})>"
