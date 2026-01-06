"""
Multi-Tenant Starter API Routes
"""
from .auth import router as auth_router
from .organizations import router as organizations_router

__all__ = [
    "auth_router",
    "organizations_router",
]
