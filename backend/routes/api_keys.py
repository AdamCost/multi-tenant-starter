"""
API Keys and Webhooks routes

Provides endpoints for:
- Managing API keys
- Managing webhooks
- Viewing usage statistics
"""
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from pydantic import BaseModel, HttpUrl
from typing import Optional, List
from uuid import UUID
from datetime import datetime

from database import get_db
from auth.dependencies import get_current_active_user
from auth.organization import get_current_organization
from models.user import User
from models.organization import Organization
from services import api_key_service
from middleware.feature_flags import require_feature

router = APIRouter(
    prefix="/api/developer",
    tags=["developer"],
    dependencies=[Depends(require_feature("API_KEYS_ENABLED"))]
)


# =============================================================================
# SCHEMAS
# =============================================================================

class APIKeyCreateRequest(BaseModel):
    """Request to create an API key."""
    name: str
    description: Optional[str] = None
    scopes: List[str] = []
    rate_limit_per_minute: int = 60
    rate_limit_per_day: int = 10000
    expires_in_days: Optional[int] = None


class APIKeyUpdateRequest(BaseModel):
    """Request to update an API key."""
    name: Optional[str] = None
    description: Optional[str] = None
    scopes: Optional[List[str]] = None
    rate_limit_per_minute: Optional[int] = None
    rate_limit_per_day: Optional[int] = None
    is_active: Optional[bool] = None


class APIKeyResponse(BaseModel):
    """API key response (without the actual key)."""
    id: str
    name: str
    key_prefix: str
    description: Optional[str]
    scopes: List[str]
    rate_limit_per_minute: int
    rate_limit_per_day: int
    is_active: bool
    expires_at: Optional[str]
    last_used_at: Optional[str]
    total_requests: int
    created_at: str


class APIKeyCreatedResponse(BaseModel):
    """Response when creating an API key (includes the actual key once)."""
    api_key: APIKeyResponse
    key: str
    message: str = "Store this key securely. It will not be shown again."


class WebhookCreateRequest(BaseModel):
    """Request to create a webhook."""
    name: str
    url: str
    events: List[str]
    description: Optional[str] = None


class WebhookUpdateRequest(BaseModel):
    """Request to update a webhook."""
    name: Optional[str] = None
    url: Optional[str] = None
    events: Optional[List[str]] = None
    description: Optional[str] = None
    is_active: Optional[bool] = None


class WebhookResponse(BaseModel):
    """Webhook response."""
    id: str
    name: str
    url: str
    events: List[str]
    description: Optional[str]
    is_active: bool
    last_triggered_at: Optional[str]
    last_success_at: Optional[str]
    last_failure_at: Optional[str]
    failure_count: int
    created_at: str


class WebhookDeliveryResponse(BaseModel):
    """Webhook delivery log response."""
    id: str
    event_type: str
    status: str
    status_code: Optional[int]
    error_message: Optional[str]
    attempt_count: int
    created_at: str
    delivered_at: Optional[str]


class ScopeResponse(BaseModel):
    """Available scope response."""
    id: str
    name: str
    description: str


class EventResponse(BaseModel):
    """Available event response."""
    id: str
    name: str
    description: str


class UsageStatsResponse(BaseModel):
    """Usage statistics response."""
    total_requests: int
    period_days: int
    by_endpoint: dict
    by_status: dict
    avg_response_time_ms: Optional[float]


# =============================================================================
# REFERENCE ENDPOINTS
# =============================================================================

@router.get("/scopes", response_model=List[ScopeResponse])
async def list_available_scopes():
    """Get list of available API key scopes."""
    return api_key_service.AVAILABLE_SCOPES


@router.get("/events", response_model=List[EventResponse])
async def list_available_events():
    """Get list of available webhook events."""
    return api_key_service.AVAILABLE_EVENTS


# =============================================================================
# API KEY ENDPOINTS
# =============================================================================

@router.get("/api-keys", response_model=List[APIKeyResponse])
async def list_api_keys(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
    organization: Organization = Depends(get_current_organization),
):
    """Get all API keys for the organization."""
    keys = await api_key_service.get_api_keys_for_org(db, organization.id)
    return [_api_key_to_response(k) for k in keys]


@router.post("/api-keys", response_model=APIKeyCreatedResponse)
async def create_api_key(
    request: APIKeyCreateRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
    organization: Organization = Depends(get_current_organization),
):
    """
    Create a new API key.

    The full key is only returned once. Store it securely.
    """
    # Validate scopes
    valid_scope_ids = [s["id"] for s in api_key_service.AVAILABLE_SCOPES]
    for scope in request.scopes:
        if scope not in valid_scope_ids:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Invalid scope: {scope}"
            )

    api_key, full_key = await api_key_service.create_api_key(
        db=db,
        organization_id=organization.id,
        name=request.name,
        user_id=current_user.id,
        description=request.description,
        scopes=request.scopes,
        rate_limit_per_minute=request.rate_limit_per_minute,
        rate_limit_per_day=request.rate_limit_per_day,
        expires_in_days=request.expires_in_days,
    )

    return APIKeyCreatedResponse(
        api_key=_api_key_to_response(api_key),
        key=full_key,
    )


@router.get("/api-keys/{key_id}", response_model=APIKeyResponse)
async def get_api_key(
    key_id: UUID,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
    organization: Organization = Depends(get_current_organization),
):
    """Get an API key by ID."""
    api_key = await api_key_service.get_api_key(db, key_id, organization.id)
    if not api_key:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="API key not found"
        )
    return _api_key_to_response(api_key)


@router.patch("/api-keys/{key_id}", response_model=APIKeyResponse)
async def update_api_key(
    key_id: UUID,
    request: APIKeyUpdateRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
    organization: Organization = Depends(get_current_organization),
):
    """Update an API key."""
    # Validate scopes if provided
    if request.scopes:
        valid_scope_ids = [s["id"] for s in api_key_service.AVAILABLE_SCOPES]
        for scope in request.scopes:
            if scope not in valid_scope_ids:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail=f"Invalid scope: {scope}"
                )

    updates = request.model_dump(exclude_unset=True)
    api_key = await api_key_service.update_api_key(
        db=db,
        key_id=key_id,
        organization_id=organization.id,
        **updates
    )

    if not api_key:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="API key not found"
        )

    return _api_key_to_response(api_key)


@router.delete("/api-keys/{key_id}")
async def delete_api_key(
    key_id: UUID,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
    organization: Organization = Depends(get_current_organization),
):
    """Delete an API key."""
    success = await api_key_service.delete_api_key(db, key_id, organization.id)
    if not success:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="API key not found"
        )
    return {"message": "API key deleted successfully"}


@router.post("/api-keys/{key_id}/revoke")
async def revoke_api_key(
    key_id: UUID,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
    organization: Organization = Depends(get_current_organization),
):
    """Revoke an API key without deleting it."""
    api_key = await api_key_service.revoke_api_key(db, key_id, organization.id)
    if not api_key:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="API key not found"
        )
    return {"message": "API key revoked successfully"}


# =============================================================================
# USAGE ENDPOINTS
# =============================================================================

@router.get("/usage", response_model=UsageStatsResponse)
async def get_usage_stats(
    api_key_id: Optional[UUID] = None,
    days: int = 30,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
    organization: Organization = Depends(get_current_organization),
):
    """Get API usage statistics."""
    stats = await api_key_service.get_usage_stats(
        db=db,
        organization_id=organization.id,
        api_key_id=api_key_id,
        days=days,
    )
    return stats


# =============================================================================
# WEBHOOK ENDPOINTS
# =============================================================================

@router.get("/webhooks", response_model=List[WebhookResponse])
async def list_webhooks(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
    organization: Organization = Depends(get_current_organization),
):
    """Get all webhooks for the organization."""
    webhooks = await api_key_service.get_webhooks_for_org(db, organization.id)
    return [_webhook_to_response(w) for w in webhooks]


@router.post("/webhooks", response_model=WebhookResponse)
async def create_webhook(
    request: WebhookCreateRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
    organization: Organization = Depends(get_current_organization),
):
    """Create a new webhook."""
    # Validate events
    valid_event_ids = [e["id"] for e in api_key_service.AVAILABLE_EVENTS]
    for event in request.events:
        if event not in valid_event_ids:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Invalid event: {event}"
            )

    webhook = await api_key_service.create_webhook(
        db=db,
        organization_id=organization.id,
        name=request.name,
        url=request.url,
        events=request.events,
        user_id=current_user.id,
        description=request.description,
    )

    return _webhook_to_response(webhook)


@router.get("/webhooks/{webhook_id}", response_model=WebhookResponse)
async def get_webhook(
    webhook_id: UUID,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
    organization: Organization = Depends(get_current_organization),
):
    """Get a webhook by ID."""
    webhook = await api_key_service.get_webhook(db, webhook_id, organization.id)
    if not webhook:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Webhook not found"
        )
    return _webhook_to_response(webhook)


@router.patch("/webhooks/{webhook_id}", response_model=WebhookResponse)
async def update_webhook(
    webhook_id: UUID,
    request: WebhookUpdateRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
    organization: Organization = Depends(get_current_organization),
):
    """Update a webhook."""
    # Validate events if provided
    if request.events:
        valid_event_ids = [e["id"] for e in api_key_service.AVAILABLE_EVENTS]
        for event in request.events:
            if event not in valid_event_ids:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail=f"Invalid event: {event}"
                )

    updates = request.model_dump(exclude_unset=True)
    webhook = await api_key_service.update_webhook(
        db=db,
        webhook_id=webhook_id,
        organization_id=organization.id,
        **updates
    )

    if not webhook:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Webhook not found"
        )

    return _webhook_to_response(webhook)


@router.delete("/webhooks/{webhook_id}")
async def delete_webhook(
    webhook_id: UUID,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
    organization: Organization = Depends(get_current_organization),
):
    """Delete a webhook."""
    success = await api_key_service.delete_webhook(db, webhook_id, organization.id)
    if not success:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Webhook not found"
        )
    return {"message": "Webhook deleted successfully"}


@router.post("/webhooks/{webhook_id}/regenerate-secret")
async def regenerate_webhook_secret(
    webhook_id: UUID,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
    organization: Organization = Depends(get_current_organization),
):
    """Regenerate a webhook's signing secret."""
    new_secret = await api_key_service.regenerate_webhook_secret(
        db, webhook_id, organization.id
    )
    if not new_secret:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Webhook not found"
        )
    return {
        "secret": new_secret,
        "message": "Store this secret securely. It will not be shown again."
    }


@router.get("/webhooks/{webhook_id}/deliveries", response_model=List[WebhookDeliveryResponse])
async def list_webhook_deliveries(
    webhook_id: UUID,
    limit: int = 50,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
    organization: Organization = Depends(get_current_organization),
):
    """Get delivery logs for a webhook."""
    deliveries = await api_key_service.get_webhook_deliveries(
        db, webhook_id, organization.id, limit
    )
    return [
        WebhookDeliveryResponse(
            id=str(d.id),
            event_type=d.event_type,
            status=d.status,
            status_code=d.status_code,
            error_message=d.error_message,
            attempt_count=d.attempt_count,
            created_at=d.created_at.isoformat(),
            delivered_at=d.delivered_at.isoformat() if d.delivered_at else None,
        )
        for d in deliveries
    ]


# =============================================================================
# HELPER FUNCTIONS
# =============================================================================

def _api_key_to_response(api_key) -> APIKeyResponse:
    """Convert APIKey model to response."""
    return APIKeyResponse(
        id=str(api_key.id),
        name=api_key.name,
        key_prefix=api_key.key_prefix,
        description=api_key.description,
        scopes=api_key.scopes or [],
        rate_limit_per_minute=api_key.rate_limit_per_minute,
        rate_limit_per_day=api_key.rate_limit_per_day,
        is_active=api_key.is_active,
        expires_at=api_key.expires_at.isoformat() if api_key.expires_at else None,
        last_used_at=api_key.last_used_at.isoformat() if api_key.last_used_at else None,
        total_requests=api_key.total_requests,
        created_at=api_key.created_at.isoformat(),
    )


def _webhook_to_response(webhook) -> WebhookResponse:
    """Convert Webhook model to response."""
    return WebhookResponse(
        id=str(webhook.id),
        name=webhook.name,
        url=webhook.url,
        events=webhook.events or [],
        description=webhook.description,
        is_active=webhook.is_active,
        last_triggered_at=webhook.last_triggered_at.isoformat() if webhook.last_triggered_at else None,
        last_success_at=webhook.last_success_at.isoformat() if webhook.last_success_at else None,
        last_failure_at=webhook.last_failure_at.isoformat() if webhook.last_failure_at else None,
        failure_count=webhook.failure_count,
        created_at=webhook.created_at.isoformat(),
    )
