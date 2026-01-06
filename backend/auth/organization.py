"""
Organization authentication dependencies
"""
from uuid import UUID
from typing import Optional

from fastapi import Depends, HTTPException, status, Header
from sqlalchemy.orm import Session

from database import get_db
from models import User, Organization, OrganizationMembership
from .dependencies import get_current_active_user


async def get_current_organization(
    x_organization_id: Optional[str] = Header(None, alias="X-Organization-ID"),
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
) -> Organization:
    """
    Get the current organization from the X-Organization-ID header.

    Validates that the user is a member of the organization.
    """
    if not x_organization_id:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="X-Organization-ID header is required"
        )

    try:
        org_id = UUID(x_organization_id)
    except ValueError:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid organization ID format"
        )

    organization = db.query(Organization).filter(Organization.id == org_id).first()

    if not organization:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Organization not found"
        )

    # Verify user is a member
    membership = db.query(OrganizationMembership).filter(
        OrganizationMembership.organization_id == org_id,
        OrganizationMembership.user_id == current_user.id,
        OrganizationMembership.status == "active"
    ).first()

    if not membership:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You are not a member of this organization"
        )

    return organization


async def get_org_membership(
    organization: Organization = Depends(get_current_organization),
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
) -> OrganizationMembership:
    """Get the current user's membership in the organization."""
    membership = db.query(OrganizationMembership).filter(
        OrganizationMembership.organization_id == organization.id,
        OrganizationMembership.user_id == current_user.id,
        OrganizationMembership.status == "active"
    ).first()

    if not membership:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Organization membership not found"
        )

    return membership


def require_org_role(required_role: str):
    """
    Dependency factory for role-based access control.

    Roles (highest to lowest):
    - admin: Full access, can manage team
    - editor: Can create/edit campaigns
    - viewer: Can view and chat only

    Usage:
        @router.post("/admin-only")
        async def admin_only(membership = Depends(require_org_role("admin"))):
            ...
    """
    async def role_checker(
        membership: OrganizationMembership = Depends(get_org_membership)
    ) -> OrganizationMembership:
        role_hierarchy = {"viewer": 0, "editor": 1, "admin": 2}

        required_level = role_hierarchy.get(required_role, 0)
        user_level = role_hierarchy.get(membership.role, 0)

        if user_level < required_level:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"This action requires {required_role} role or higher"
            )

        return membership

    return role_checker


def require_permission(permission: str):
    """
    Permission-based access control.

    Permissions:
    - 'view': Can view insights and chat (all roles)
    - 'edit': Can create/edit campaigns (admin, editor)
    - 'manage_team': Can add/remove team members (admin only)

    Usage:
        @router.post("/campaigns")
        async def create_campaign(membership = Depends(require_permission("edit"))):
            ...
    """
    async def permission_checker(
        membership: OrganizationMembership = Depends(get_org_membership)
    ) -> OrganizationMembership:
        permission_map = {
            'view': ['admin', 'editor', 'viewer'],
            'edit': ['admin', 'editor'],
            'manage_team': ['admin'],
        }

        allowed_roles = permission_map.get(permission, [])

        if membership.role not in allowed_roles:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"This action requires '{permission}' permission"
            )

        return membership

    return permission_checker
