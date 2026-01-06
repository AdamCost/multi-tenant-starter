"""
API Key Service

Manages API keys, usage tracking, and webhooks.
"""
from sqlalchemy.orm import Session
from sqlalchemy import and_, func
from typing import List, Dict, Any, Optional, Tuple
from uuid import UUID
from datetime import datetime, timedelta
import secrets
import hashlib
import hmac
import json
import logging

from models.api_key import (
    APIKey,
    APIUsage,
    Webhook,
    WebhookDelivery,
    WebhookDeliveryStatus,
)

logger = logging.getLogger(__name__)


# =============================================================================
# API KEY MANAGEMENT
# =============================================================================

def generate_api_key() -> Tuple[str, str, str]:
    """
    Generate a new API key.

    Returns:
        Tuple of (full_key, key_hash, key_prefix)
    """
    # Generate a secure random key
    key = f"sk_{secrets.token_urlsafe(32)}"  # sk = Starter Key
    key_hash = hashlib.sha256(key.encode()).hexdigest()
    key_prefix = key[:12]

    return key, key_hash, key_prefix


def verify_api_key(key: str, key_hash: str) -> bool:
    """Verify an API key against its hash."""
    computed_hash = hashlib.sha256(key.encode()).hexdigest()
    return secrets.compare_digest(computed_hash, key_hash)


async def create_api_key(
    db: Session,
    organization_id: UUID,
    name: str,
    user_id: Optional[UUID] = None,
    description: Optional[str] = None,
    scopes: Optional[List[str]] = None,
    rate_limit_per_minute: int = 60,
    rate_limit_per_day: int = 10000,
    expires_in_days: Optional[int] = None,
) -> Tuple[APIKey, str]:
    """
    Create a new API key.

    Returns:
        Tuple of (APIKey model, full_key_string)
        Note: The full key is only returned once and should be shown to user immediately.
    """
    full_key, key_hash, key_prefix = generate_api_key()

    expires_at = None
    if expires_in_days:
        expires_at = datetime.utcnow() + timedelta(days=expires_in_days)

    api_key = APIKey(
        organization_id=organization_id,
        created_by_user_id=user_id,
        name=name,
        key_hash=key_hash,
        key_prefix=key_prefix,
        description=description,
        scopes=scopes or [],
        rate_limit_per_minute=rate_limit_per_minute,
        rate_limit_per_day=rate_limit_per_day,
        expires_at=expires_at,
    )

    db.add(api_key)
    db.commit()
    db.refresh(api_key)

    return api_key, full_key


async def get_api_key(
    db: Session,
    key_id: UUID,
    organization_id: UUID
) -> Optional[APIKey]:
    """Get an API key by ID."""
    return db.query(APIKey).filter(
        and_(
            APIKey.id == key_id,
            APIKey.organization_id == organization_id
        )
    ).first()


async def get_api_key_by_key(db: Session, key: str) -> Optional[APIKey]:
    """
    Look up an API key by the actual key string.
    Used for authentication.
    """
    key_hash = hashlib.sha256(key.encode()).hexdigest()
    return db.query(APIKey).filter(APIKey.key_hash == key_hash).first()


async def get_api_keys_for_org(
    db: Session,
    organization_id: UUID
) -> List[APIKey]:
    """Get all API keys for an organization."""
    return db.query(APIKey).filter(
        APIKey.organization_id == organization_id
    ).order_by(APIKey.created_at.desc()).all()


async def update_api_key(
    db: Session,
    key_id: UUID,
    organization_id: UUID,
    **kwargs
) -> Optional[APIKey]:
    """Update an API key."""
    api_key = await get_api_key(db, key_id, organization_id)
    if not api_key:
        return None

    allowed_fields = [
        "name", "description", "scopes", "rate_limit_per_minute",
        "rate_limit_per_day", "is_active", "expires_at"
    ]

    for key, value in kwargs.items():
        if key in allowed_fields and value is not None:
            setattr(api_key, key, value)

    api_key.updated_at = datetime.utcnow()
    db.commit()
    db.refresh(api_key)

    return api_key


async def delete_api_key(
    db: Session,
    key_id: UUID,
    organization_id: UUID
) -> bool:
    """Delete an API key."""
    api_key = await get_api_key(db, key_id, organization_id)
    if not api_key:
        return False

    db.delete(api_key)
    db.commit()
    return True


async def revoke_api_key(
    db: Session,
    key_id: UUID,
    organization_id: UUID
) -> Optional[APIKey]:
    """Revoke (deactivate) an API key without deleting it."""
    return await update_api_key(db, key_id, organization_id, is_active=False)


# =============================================================================
# USAGE TRACKING
# =============================================================================

async def record_api_usage(
    db: Session,
    api_key: APIKey,
    endpoint: str,
    method: str,
    status_code: int,
    response_time_ms: Optional[int] = None,
    request_ip: Optional[str] = None,
):
    """Record an API request for usage tracking."""
    usage = APIUsage(
        api_key_id=api_key.id,
        organization_id=api_key.organization_id,
        endpoint=endpoint,
        method=method,
        status_code=status_code,
        response_time_ms=response_time_ms,
        request_ip=request_ip,
    )

    # Update API key usage stats
    api_key.last_used_at = datetime.utcnow()
    api_key.last_used_ip = request_ip
    api_key.total_requests += 1

    db.add(usage)
    db.commit()


async def check_rate_limit(
    db: Session,
    api_key: APIKey,
) -> Tuple[bool, Dict[str, int]]:
    """
    Check if an API key is within rate limits.

    Returns:
        Tuple of (is_allowed, rate_limit_info)
    """
    now = datetime.utcnow()
    minute_ago = now - timedelta(minutes=1)
    day_ago = now - timedelta(days=1)

    # Count requests in last minute
    requests_this_minute = db.query(func.count(APIUsage.id)).filter(
        and_(
            APIUsage.api_key_id == api_key.id,
            APIUsage.timestamp >= minute_ago
        )
    ).scalar()

    # Count requests in last day
    requests_today = db.query(func.count(APIUsage.id)).filter(
        and_(
            APIUsage.api_key_id == api_key.id,
            APIUsage.timestamp >= day_ago
        )
    ).scalar()

    info = {
        "requests_this_minute": requests_this_minute,
        "limit_per_minute": api_key.rate_limit_per_minute,
        "requests_today": requests_today,
        "limit_per_day": api_key.rate_limit_per_day,
    }

    is_allowed = (
        requests_this_minute < api_key.rate_limit_per_minute and
        requests_today < api_key.rate_limit_per_day
    )

    return is_allowed, info


async def get_usage_stats(
    db: Session,
    organization_id: UUID,
    api_key_id: Optional[UUID] = None,
    days: int = 30
) -> Dict[str, Any]:
    """Get API usage statistics."""
    since = datetime.utcnow() - timedelta(days=days)

    query = db.query(APIUsage).filter(
        and_(
            APIUsage.organization_id == organization_id,
            APIUsage.timestamp >= since
        )
    )

    if api_key_id:
        query = query.filter(APIUsage.api_key_id == api_key_id)

    total = query.count()

    # Group by endpoint
    by_endpoint = {}
    endpoint_counts = db.query(
        APIUsage.endpoint,
        func.count(APIUsage.id)
    ).filter(
        and_(
            APIUsage.organization_id == organization_id,
            APIUsage.timestamp >= since
        )
    ).group_by(APIUsage.endpoint).all()

    for endpoint, count in endpoint_counts:
        by_endpoint[endpoint] = count

    # Group by status code
    by_status = {}
    status_counts = db.query(
        APIUsage.status_code,
        func.count(APIUsage.id)
    ).filter(
        and_(
            APIUsage.organization_id == organization_id,
            APIUsage.timestamp >= since
        )
    ).group_by(APIUsage.status_code).all()

    for status, count in status_counts:
        by_status[status] = count

    # Average response time
    avg_response_time = db.query(
        func.avg(APIUsage.response_time_ms)
    ).filter(
        and_(
            APIUsage.organization_id == organization_id,
            APIUsage.timestamp >= since,
            APIUsage.response_time_ms.isnot(None)
        )
    ).scalar()

    return {
        "total_requests": total,
        "period_days": days,
        "by_endpoint": by_endpoint,
        "by_status": by_status,
        "avg_response_time_ms": round(avg_response_time, 2) if avg_response_time else None,
    }


# =============================================================================
# WEBHOOK MANAGEMENT
# =============================================================================

def generate_webhook_secret() -> str:
    """Generate a webhook signing secret."""
    return secrets.token_hex(32)


async def create_webhook(
    db: Session,
    organization_id: UUID,
    name: str,
    url: str,
    events: List[str],
    user_id: Optional[UUID] = None,
    description: Optional[str] = None,
) -> Webhook:
    """Create a new webhook."""
    webhook = Webhook(
        organization_id=organization_id,
        created_by_user_id=user_id,
        name=name,
        url=url,
        secret=generate_webhook_secret(),
        events=events,
        description=description,
    )

    db.add(webhook)
    db.commit()
    db.refresh(webhook)

    return webhook


async def get_webhook(
    db: Session,
    webhook_id: UUID,
    organization_id: UUID
) -> Optional[Webhook]:
    """Get a webhook by ID."""
    return db.query(Webhook).filter(
        and_(
            Webhook.id == webhook_id,
            Webhook.organization_id == organization_id
        )
    ).first()


async def get_webhooks_for_org(
    db: Session,
    organization_id: UUID
) -> List[Webhook]:
    """Get all webhooks for an organization."""
    return db.query(Webhook).filter(
        Webhook.organization_id == organization_id
    ).order_by(Webhook.created_at.desc()).all()


async def get_webhooks_for_event(
    db: Session,
    organization_id: UUID,
    event_type: str
) -> List[Webhook]:
    """Get active webhooks subscribed to a specific event."""
    webhooks = db.query(Webhook).filter(
        and_(
            Webhook.organization_id == organization_id,
            Webhook.is_active == True
        )
    ).all()

    # Filter by event subscription (JSONB contains)
    return [w for w in webhooks if event_type in w.events]


async def update_webhook(
    db: Session,
    webhook_id: UUID,
    organization_id: UUID,
    **kwargs
) -> Optional[Webhook]:
    """Update a webhook."""
    webhook = await get_webhook(db, webhook_id, organization_id)
    if not webhook:
        return None

    allowed_fields = ["name", "url", "events", "description", "is_active"]

    for key, value in kwargs.items():
        if key in allowed_fields and value is not None:
            setattr(webhook, key, value)

    webhook.updated_at = datetime.utcnow()
    db.commit()
    db.refresh(webhook)

    return webhook


async def delete_webhook(
    db: Session,
    webhook_id: UUID,
    organization_id: UUID
) -> bool:
    """Delete a webhook."""
    webhook = await get_webhook(db, webhook_id, organization_id)
    if not webhook:
        return False

    db.delete(webhook)
    db.commit()
    return True


async def regenerate_webhook_secret(
    db: Session,
    webhook_id: UUID,
    organization_id: UUID
) -> Optional[str]:
    """Regenerate a webhook's signing secret."""
    webhook = await get_webhook(db, webhook_id, organization_id)
    if not webhook:
        return None

    new_secret = generate_webhook_secret()
    webhook.secret = new_secret
    webhook.updated_at = datetime.utcnow()
    db.commit()

    return new_secret


# =============================================================================
# WEBHOOK DELIVERY
# =============================================================================

def sign_webhook_payload(payload: dict, secret: str) -> str:
    """Sign a webhook payload using HMAC-SHA256."""
    payload_str = json.dumps(payload, sort_keys=True, separators=(',', ':'))
    signature = hmac.new(
        secret.encode(),
        payload_str.encode(),
        hashlib.sha256
    ).hexdigest()
    return f"sha256={signature}"


async def create_webhook_delivery(
    db: Session,
    webhook: Webhook,
    event_type: str,
    payload: dict
) -> WebhookDelivery:
    """Create a webhook delivery record."""
    delivery = WebhookDelivery(
        webhook_id=webhook.id,
        event_type=event_type,
        payload=payload,
        status=WebhookDeliveryStatus.PENDING.value,
    )

    db.add(delivery)
    db.commit()
    db.refresh(delivery)

    return delivery


async def update_delivery_status(
    db: Session,
    delivery: WebhookDelivery,
    status: str,
    status_code: Optional[int] = None,
    response_body: Optional[str] = None,
    error_message: Optional[str] = None,
):
    """Update a webhook delivery status."""
    delivery.status = status
    delivery.status_code = status_code
    delivery.response_body = response_body
    delivery.error_message = error_message

    if status == WebhookDeliveryStatus.SUCCESS.value:
        delivery.delivered_at = datetime.utcnow()

    db.commit()


async def get_webhook_deliveries(
    db: Session,
    webhook_id: UUID,
    organization_id: UUID,
    limit: int = 50
) -> List[WebhookDelivery]:
    """Get delivery logs for a webhook."""
    # Verify webhook belongs to organization
    webhook = await get_webhook(db, webhook_id, organization_id)
    if not webhook:
        return []

    return db.query(WebhookDelivery).filter(
        WebhookDelivery.webhook_id == webhook_id
    ).order_by(WebhookDelivery.created_at.desc()).limit(limit).all()


# Available scopes for documentation
AVAILABLE_SCOPES = [
    {"id": "read:employees", "name": "Read Employees", "description": "Read HRIS employee data"},
    {"id": "read:campaigns", "name": "Read Campaigns", "description": "Read campaign data and results"},
    {"id": "read:debrief", "name": "Read Debrief", "description": "Read debrief submissions and issues"},
    {"id": "read:analytics", "name": "Read Analytics", "description": "Access analytics and reporting data"},
    {"id": "write:campaigns", "name": "Write Campaigns", "description": "Create and manage campaigns"},
    {"id": "write:debrief", "name": "Write Debrief", "description": "Submit debrief responses"},
    {"id": "write:employees", "name": "Write Employees", "description": "Create and update employee records"},
    {"id": "admin:users", "name": "Admin Users", "description": "Manage organization users"},
    {"id": "admin:settings", "name": "Admin Settings", "description": "Manage organization settings"},
]

# Available webhook events for documentation
AVAILABLE_EVENTS = [
    {"id": "debrief.submitted", "name": "Debrief Submitted", "description": "When an employee submits a debrief"},
    {"id": "debrief.issue.created", "name": "Issue Created", "description": "When a new issue is extracted from debrief"},
    {"id": "debrief.issue.resolved", "name": "Issue Resolved", "description": "When an issue is marked as resolved"},
    {"id": "debrief.digest.sent", "name": "Digest Sent", "description": "When a manager digest email is sent"},
    {"id": "campaign.created", "name": "Campaign Created", "description": "When a new campaign is created"},
    {"id": "campaign.completed", "name": "Campaign Completed", "description": "When a campaign is marked complete"},
    {"id": "interview.completed", "name": "Interview Completed", "description": "When an interview is completed"},
    {"id": "hris.sync.completed", "name": "HRIS Sync Completed", "description": "When HRIS sync completes successfully"},
    {"id": "hris.sync.failed", "name": "HRIS Sync Failed", "description": "When HRIS sync fails"},
]
