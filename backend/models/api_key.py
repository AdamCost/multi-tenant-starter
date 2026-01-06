"""
API Key models

Supports:
- API key management with scopes
- Usage tracking and rate limiting
- Webhook configurations
"""
from sqlalchemy import Column, String, DateTime, Boolean, Integer, Text, ForeignKey
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import relationship
from datetime import datetime
from enum import Enum as PyEnum
import uuid

from database import Base
from .types import GUID


class APIKeyScope(str, PyEnum):
    """Available API key scopes."""
    # Read scopes
    READ_EMPLOYEES = "read:employees"
    READ_CAMPAIGNS = "read:campaigns"
    READ_DEBRIEF = "read:debrief"
    READ_ANALYTICS = "read:analytics"

    # Write scopes
    WRITE_CAMPAIGNS = "write:campaigns"
    WRITE_DEBRIEF = "write:debrief"
    WRITE_EMPLOYEES = "write:employees"

    # Admin scopes
    ADMIN_USERS = "admin:users"
    ADMIN_SETTINGS = "admin:settings"


class WebhookEvent(str, PyEnum):
    """Available webhook events."""
    # Debrief events
    DEBRIEF_SUBMITTED = "debrief.submitted"
    DEBRIEF_ISSUE_CREATED = "debrief.issue.created"
    DEBRIEF_ISSUE_RESOLVED = "debrief.issue.resolved"
    DEBRIEF_DIGEST_SENT = "debrief.digest.sent"

    # Campaign events
    CAMPAIGN_CREATED = "campaign.created"
    CAMPAIGN_COMPLETED = "campaign.completed"
    INTERVIEW_COMPLETED = "interview.completed"

    # HRIS events
    HRIS_SYNC_COMPLETED = "hris.sync.completed"
    HRIS_SYNC_FAILED = "hris.sync.failed"


class WebhookDeliveryStatus(str, PyEnum):
    """Status of webhook delivery."""
    PENDING = "pending"
    SUCCESS = "success"
    FAILED = "failed"
    RETRYING = "retrying"


class APIKey(Base):
    """
    API keys for external integrations.
    """
    __tablename__ = "api_keys"

    id = Column(GUID(), primary_key=True, default=uuid.uuid4)
    organization_id = Column(GUID(), ForeignKey("organizations.id", ondelete="CASCADE"), nullable=False, index=True)
    created_by_user_id = Column(GUID(), ForeignKey("users.id", ondelete="SET NULL"), nullable=True)

    # Key info
    name = Column(String(100), nullable=False)
    key_hash = Column(String(64), nullable=False, unique=True)  # SHA-256 hash
    key_prefix = Column(String(12), nullable=False)  # First 8 chars for identification
    description = Column(String(500), nullable=True)

    # Permissions & limits
    scopes = Column(JSONB, nullable=False, default=list)
    rate_limit_per_minute = Column(Integer, nullable=False, default=60)
    rate_limit_per_day = Column(Integer, nullable=False, default=10000)

    # Usage tracking
    last_used_at = Column(DateTime, nullable=True)
    last_used_ip = Column(String(50), nullable=True)
    total_requests = Column(Integer, nullable=False, default=0)

    # Status
    is_active = Column(Boolean, nullable=False, default=True)
    expires_at = Column(DateTime, nullable=True)

    # Timestamps
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)

    # Relationships
    organization = relationship("Organization", backref="api_keys")
    created_by = relationship("User", backref="created_api_keys")
    usage_logs = relationship("APIUsage", back_populates="api_key", cascade="all, delete-orphan")

    def __repr__(self):
        return f"<APIKey(id={self.id}, name={self.name}, prefix={self.key_prefix})>"

    @property
    def is_expired(self) -> bool:
        if not self.expires_at:
            return False
        return datetime.utcnow() >= self.expires_at

    @property
    def is_valid(self) -> bool:
        return self.is_active and not self.is_expired

    def has_scope(self, scope: str) -> bool:
        return scope in self.scopes


class APIUsage(Base):
    """
    Usage logs for API requests.
    Used for analytics and rate limit tracking.
    """
    __tablename__ = "api_usage"

    id = Column(GUID(), primary_key=True, default=uuid.uuid4)
    api_key_id = Column(GUID(), ForeignKey("api_keys.id", ondelete="CASCADE"), nullable=False, index=True)
    organization_id = Column(GUID(), ForeignKey("organizations.id", ondelete="CASCADE"), nullable=False, index=True)

    # Request details
    endpoint = Column(String(200), nullable=False, index=True)
    method = Column(String(10), nullable=False)
    status_code = Column(Integer, nullable=False)
    response_time_ms = Column(Integer, nullable=True)
    request_ip = Column(String(50), nullable=True)

    # Timestamp
    timestamp = Column(DateTime, default=datetime.utcnow, nullable=False, index=True)

    # Relationships
    api_key = relationship("APIKey", back_populates="usage_logs")
    organization = relationship("Organization", backref="api_usage_logs")

    def __repr__(self):
        return f"<APIUsage(id={self.id}, endpoint={self.endpoint}, status={self.status_code})>"


class Webhook(Base):
    """
    Webhook configurations for event notifications.
    """
    __tablename__ = "webhooks"

    id = Column(GUID(), primary_key=True, default=uuid.uuid4)
    organization_id = Column(GUID(), ForeignKey("organizations.id", ondelete="CASCADE"), nullable=False, index=True)
    created_by_user_id = Column(GUID(), ForeignKey("users.id", ondelete="SET NULL"), nullable=True)

    # Webhook config
    name = Column(String(100), nullable=False)
    url = Column(String(500), nullable=False)
    secret = Column(String(64), nullable=False)  # For HMAC signing
    description = Column(String(500), nullable=True)

    # Events to trigger on
    events = Column(JSONB, nullable=False, default=list)

    # Status
    is_active = Column(Boolean, nullable=False, default=True)
    last_triggered_at = Column(DateTime, nullable=True)
    last_success_at = Column(DateTime, nullable=True)
    last_failure_at = Column(DateTime, nullable=True)
    failure_count = Column(Integer, nullable=False, default=0)

    # Timestamps
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)

    # Relationships
    organization = relationship("Organization", backref="webhooks")
    created_by = relationship("User", backref="created_webhooks")
    deliveries = relationship("WebhookDelivery", back_populates="webhook", cascade="all, delete-orphan")

    def __repr__(self):
        return f"<Webhook(id={self.id}, name={self.name}, url={self.url})>"

    def is_subscribed_to(self, event_type: str) -> bool:
        return event_type in self.events


class WebhookDelivery(Base):
    """
    Delivery logs for webhooks.
    """
    __tablename__ = "webhook_deliveries"

    id = Column(GUID(), primary_key=True, default=uuid.uuid4)
    webhook_id = Column(GUID(), ForeignKey("webhooks.id", ondelete="CASCADE"), nullable=False, index=True)

    # Event details
    event_type = Column(String(100), nullable=False)
    payload = Column(JSONB, nullable=True)

    # Delivery result
    status = Column(String(50), nullable=False, default=WebhookDeliveryStatus.PENDING.value, index=True)
    status_code = Column(Integer, nullable=True)
    response_body = Column(Text, nullable=True)
    error_message = Column(String(1000), nullable=True)
    attempt_count = Column(Integer, nullable=False, default=1)

    # Timestamps
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False, index=True)
    delivered_at = Column(DateTime, nullable=True)

    # Relationships
    webhook = relationship("Webhook", back_populates="deliveries")

    def __repr__(self):
        return f"<WebhookDelivery(id={self.id}, event={self.event_type}, status={self.status})>"
