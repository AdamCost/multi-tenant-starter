"""
Organization management routes
"""
from uuid import UUID
from typing import List, Optional

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from pydantic import BaseModel, EmailStr

from database import get_db
from models import User, Organization, OrganizationMembership, OrganizationInvite
from auth.dependencies import get_current_active_user, get_optional_user
from auth.organization import get_current_organization, require_org_role

router = APIRouter(prefix="/api/organizations", tags=["organizations"])


# Pydantic schemas
class OrganizationResponse(BaseModel):
    id: str
    name: str
    slug: str
    role: str

    class Config:
        from_attributes = True


class MemberResponse(BaseModel):
    id: str
    user_id: str
    email: str
    name: Optional[str]
    role: str
    status: str
    is_account_owner: bool = False

    class Config:
        from_attributes = True


class AddMemberRequest(BaseModel):
    email: EmailStr
    role: str = "editor"  # editor or viewer (not admin - must be promoted)


class UpdateMemberRequest(BaseModel):
    role: str


class InviteResponse(BaseModel):
    id: str
    email: str
    role: str
    status: str
    created_at: str
    expires_at: str
    inviter_name: Optional[str]

    class Config:
        from_attributes = True


class CreateInviteRequest(BaseModel):
    email: EmailStr
    role: str = "editor"  # editor or viewer


class AcceptInviteResponse(BaseModel):
    message: str
    organization_id: str
    organization_name: str


class AcceptInviteWithSignupRequest(BaseModel):
    name: str
    password: str


class AcceptInviteWithSignupResponse(BaseModel):
    message: str
    organization_id: str
    organization_name: str
    access_token: str
    user_exists: bool = False


# Endpoints

@router.get("", response_model=List[OrganizationResponse])
async def list_user_organizations(
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """List all organizations the current user belongs to."""
    # Use join to fetch organizations and memberships in a single query
    results = db.query(Organization, OrganizationMembership.role).join(
        OrganizationMembership,
        Organization.id == OrganizationMembership.organization_id
    ).filter(
        OrganizationMembership.user_id == current_user.id,
        OrganizationMembership.status == "active"
    ).all()

    return [
        OrganizationResponse(
            id=str(org.id),
            name=org.name,
            slug=org.slug,
            role=role
        )
        for org, role in results
    ]


@router.get("/{org_id}/members", response_model=List[MemberResponse])
async def list_organization_members(
    org_id: UUID,
    organization: Organization = Depends(get_current_organization),
    db: Session = Depends(get_db)
):
    """List all members of the team."""
    # Use join to fetch memberships and users in a single query
    results = db.query(OrganizationMembership, User).join(
        User,
        OrganizationMembership.user_id == User.id
    ).filter(
        OrganizationMembership.organization_id == org_id
    ).all()

    return [
        MemberResponse(
            id=str(membership.id),
            user_id=str(user.id),
            email=user.email,
            name=user.name,
            role=membership.role,
            status=membership.status,
            is_account_owner=membership.is_account_owner
        )
        for membership, user in results
    ]


@router.post("/{org_id}/members", response_model=MemberResponse)
async def add_organization_member(
    org_id: UUID,
    request: AddMemberRequest,
    membership: OrganizationMembership = Depends(require_org_role("admin")),
    organization: Organization = Depends(get_current_organization),
    db: Session = Depends(get_db)
):
    """Add a user to the team by email. Requires admin role."""
    # Validate role - can only add as editor or viewer (admin must be promoted)
    if request.role not in ("editor", "viewer"):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Role must be 'editor' or 'viewer'. To make someone admin, add them first then update their role."
        )

    # Find user by email
    user = db.query(User).filter(User.email == request.email).first()
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found with that email"
        )

    # Check if already a member
    existing = db.query(OrganizationMembership).filter(
        OrganizationMembership.organization_id == org_id,
        OrganizationMembership.user_id == user.id
    ).first()

    if existing:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="User is already a member of this team"
        )

    # Create membership
    new_membership = OrganizationMembership(
        organization_id=org_id,
        user_id=user.id,
        role=request.role,
        status="active",
        is_account_owner=False,
    )
    db.add(new_membership)
    db.commit()
    db.refresh(new_membership)

    return MemberResponse(
        id=str(new_membership.id),
        user_id=str(user.id),
        email=user.email,
        name=user.name,
        role=new_membership.role,
        status=new_membership.status,
        is_account_owner=False
    )


@router.patch("/{org_id}/members/{user_id}", response_model=MemberResponse)
async def update_member_role(
    org_id: UUID,
    user_id: UUID,
    request: UpdateMemberRequest,
    membership: OrganizationMembership = Depends(require_org_role("admin")),
    organization: Organization = Depends(get_current_organization),
    db: Session = Depends(get_db)
):
    """Update a member's role. Requires admin role."""
    # Validate role
    if request.role not in ("admin", "editor", "viewer"):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Role must be 'admin', 'editor', or 'viewer'"
        )

    # Find membership
    target = db.query(OrganizationMembership).filter(
        OrganizationMembership.organization_id == org_id,
        OrganizationMembership.user_id == user_id
    ).first()

    if not target:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Member not found"
        )

    # Can't change account owner's role
    if target.is_account_owner:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Cannot change the account owner's role"
        )

    target.role = request.role
    db.commit()
    db.refresh(target)

    user = db.query(User).filter(User.id == user_id).first()

    return MemberResponse(
        id=str(target.id),
        user_id=str(user.id),
        email=user.email,
        name=user.name,
        role=target.role,
        status=target.status,
        is_account_owner=target.is_account_owner
    )


@router.delete("/{org_id}/members/{user_id}", status_code=status.HTTP_204_NO_CONTENT)
async def remove_organization_member(
    org_id: UUID,
    user_id: UUID,
    membership: OrganizationMembership = Depends(require_org_role("admin")),
    organization: Organization = Depends(get_current_organization),
    db: Session = Depends(get_db)
):
    """Remove a member from the team. Requires admin role."""
    # Find membership
    target = db.query(OrganizationMembership).filter(
        OrganizationMembership.organization_id == org_id,
        OrganizationMembership.user_id == user_id
    ).first()

    if not target:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Member not found"
        )

    # Can't remove the account owner
    if target.is_account_owner:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Cannot remove the account owner"
        )

    db.delete(target)
    db.commit()


# Invite endpoints

@router.get("/{org_id}/invites", response_model=List[InviteResponse])
async def list_organization_invites(
    org_id: UUID,
    organization: Organization = Depends(get_current_organization),
    membership: OrganizationMembership = Depends(require_org_role("admin")),
    db: Session = Depends(get_db)
):
    """List all pending invites for an organization. Requires admin role."""
    invites = db.query(OrganizationInvite).filter(
        OrganizationInvite.organization_id == org_id,
        OrganizationInvite.status == "pending"
    ).all()

    result = []
    for invite in invites:
        inviter = db.query(User).filter(User.id == invite.invited_by).first() if invite.invited_by else None
        result.append(InviteResponse(
            id=str(invite.id),
            email=invite.email,
            role=invite.role,
            status=invite.status,
            created_at=invite.created_at.isoformat(),
            expires_at=invite.expires_at.isoformat(),
            inviter_name=inviter.name if inviter else None
        ))

    return result


@router.post("/{org_id}/invites", response_model=InviteResponse)
async def create_organization_invite(
    org_id: UUID,
    request: CreateInviteRequest,
    membership: OrganizationMembership = Depends(require_org_role("admin")),
    organization: Organization = Depends(get_current_organization),
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """Create an invite for a new team member. Requires admin role."""
    # Validate role - can only invite as editor or viewer
    if request.role not in ("editor", "viewer"):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Role must be 'editor' or 'viewer'. To make someone admin, invite them first then update their role."
        )

    # Check if user already exists and is a member
    existing_user = db.query(User).filter(User.email == request.email).first()
    if existing_user:
        existing_membership = db.query(OrganizationMembership).filter(
            OrganizationMembership.organization_id == org_id,
            OrganizationMembership.user_id == existing_user.id
        ).first()
        if existing_membership:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="User is already a member of this organization"
            )

    # Check for existing pending invite
    existing_invite = db.query(OrganizationInvite).filter(
        OrganizationInvite.organization_id == org_id,
        OrganizationInvite.email == request.email,
        OrganizationInvite.status == "pending"
    ).first()

    if existing_invite:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="An invite has already been sent to this email"
        )

    # Create invite
    invite = OrganizationInvite(
        organization_id=org_id,
        email=request.email,
        role=request.role,
        token=OrganizationInvite.generate_token(),
        invited_by=current_user.id,
        expires_at=OrganizationInvite.default_expiry()
    )
    db.add(invite)
    db.commit()
    db.refresh(invite)

    # Send invite email
    from services.org_invite_service import send_org_invite_email
    send_org_invite_email(invite, organization, current_user.name)

    return InviteResponse(
        id=str(invite.id),
        email=invite.email,
        role=invite.role,
        status=invite.status,
        created_at=invite.created_at.isoformat(),
        expires_at=invite.expires_at.isoformat(),
        inviter_name=current_user.name
    )


@router.delete("/{org_id}/invites/{invite_id}", status_code=status.HTTP_204_NO_CONTENT)
async def cancel_organization_invite(
    org_id: UUID,
    invite_id: UUID,
    membership: OrganizationMembership = Depends(require_org_role("admin")),
    organization: Organization = Depends(get_current_organization),
    db: Session = Depends(get_db)
):
    """Cancel a pending invite. Requires admin role."""
    invite = db.query(OrganizationInvite).filter(
        OrganizationInvite.id == invite_id,
        OrganizationInvite.organization_id == org_id
    ).first()

    if not invite:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Invite not found"
        )

    invite.status = "cancelled"
    db.commit()


# Public invite endpoints (for accepting invites)
invite_router = APIRouter(prefix="/api/invites", tags=["invites"])


@invite_router.get("/{token}")
async def get_invite_info(
    token: str,
    db: Session = Depends(get_db)
):
    """Get information about an invite (public endpoint for invite page)."""
    invite = db.query(OrganizationInvite).filter(
        OrganizationInvite.token == token
    ).first()

    if not invite:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Invite not found"
        )

    if invite.status != "pending":
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Invite has already been {invite.status}"
        )

    if invite.is_expired():
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invite has expired"
        )

    org = db.query(Organization).filter(Organization.id == invite.organization_id).first()

    return {
        "email": invite.email,
        "role": invite.role,
        "organization_name": org.name if org else "Unknown",
        "expires_at": invite.expires_at.isoformat()
    }


@invite_router.post("/{token}/accept", response_model=AcceptInviteResponse)
async def accept_invite(
    token: str,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """Accept an invite and join the organization. Requires authentication."""
    invite = db.query(OrganizationInvite).filter(
        OrganizationInvite.token == token
    ).first()

    if not invite:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Invite not found"
        )

    if not invite.is_valid():
        if invite.is_expired():
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Invite has expired"
            )
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Invite has already been {invite.status}"
        )

    # Verify email matches (case-insensitive)
    if invite.email.lower() != current_user.email.lower():
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="This invite was sent to a different email address"
        )

    # Check if already a member
    existing = db.query(OrganizationMembership).filter(
        OrganizationMembership.organization_id == invite.organization_id,
        OrganizationMembership.user_id == current_user.id
    ).first()

    if existing:
        # Already a member, just mark invite as accepted
        invite.status = "accepted"
        db.commit()

        org = db.query(Organization).filter(Organization.id == invite.organization_id).first()
        return AcceptInviteResponse(
            message="You are already a member of this organization",
            organization_id=str(invite.organization_id),
            organization_name=org.name if org else "Unknown"
        )

    # Create membership
    new_membership = OrganizationMembership(
        organization_id=invite.organization_id,
        user_id=current_user.id,
        role=invite.role,
        status="active"
    )
    db.add(new_membership)

    # Mark invite as accepted
    invite.status = "accepted"
    db.commit()

    org = db.query(Organization).filter(Organization.id == invite.organization_id).first()

    return AcceptInviteResponse(
        message="Successfully joined the organization",
        organization_id=str(invite.organization_id),
        organization_name=org.name if org else "Unknown"
    )


@invite_router.post("/{token}/accept-with-signup", response_model=AcceptInviteWithSignupResponse)
async def accept_invite_with_signup(
    token: str,
    request: AcceptInviteWithSignupRequest,
    db: Session = Depends(get_db)
):
    """
    Accept an invite and create a new user account in one step.

    This is for users who don't have an account yet. They provide their name
    and password, and we create the account and membership simultaneously.
    """
    from auth.utils import get_password_hash, create_access_token

    invite = db.query(OrganizationInvite).filter(
        OrganizationInvite.token == token
    ).first()

    if not invite:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Invite not found"
        )

    if not invite.is_valid():
        if invite.is_expired():
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Invite has expired"
            )
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Invite has already been {invite.status}"
        )

    # Check if user already exists
    existing_user = db.query(User).filter(User.email == invite.email).first()

    if existing_user:
        # User exists - they should use the regular accept flow with login
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="An account with this email already exists. Please log in first, then accept the invite."
        )

    # Validate password requirements
    if len(request.password) < 12:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Password must be at least 12 characters"
        )

    # Create new user
    new_user = User(
        email=invite.email,
        name=request.name,
        password_hash=get_password_hash(request.password),
        is_active=True,
        email_verified=True  # Verified via invite token
    )
    db.add(new_user)
    db.flush()  # Get user ID without committing

    # Create membership
    new_membership = OrganizationMembership(
        organization_id=invite.organization_id,
        user_id=new_user.id,
        role=invite.role,
        status="active"
    )
    db.add(new_membership)

    # Mark invite as accepted
    invite.status = "accepted"
    db.commit()
    db.refresh(new_user)

    # Generate access token for auto-login
    access_token = create_access_token(data={"sub": str(new_user.id)})

    org = db.query(Organization).filter(Organization.id == invite.organization_id).first()

    return AcceptInviteWithSignupResponse(
        message="Account created and joined organization successfully",
        organization_id=str(invite.organization_id),
        organization_name=org.name if org else "Unknown",
        access_token=access_token,
        user_exists=False
    )
