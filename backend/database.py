"""
Database connection and session management
"""
import os
from sqlalchemy import create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
from logging_config import get_logger

logger = get_logger(__name__)

# Database URL from environment or default to local PostgreSQL
DATABASE_URL = os.getenv(
    "DATABASE_URL",
    "postgresql://postgres:postgres@localhost:5434/starter_db"
)

# Handle Heroku-style postgres:// URLs
if DATABASE_URL.startswith("postgres://"):
    DATABASE_URL = DATABASE_URL.replace("postgres://", "postgresql://", 1)

# Configure connection pool for production scale
engine = create_engine(
    DATABASE_URL,
    pool_pre_ping=True,
    pool_size=20,
    max_overflow=10,
    pool_timeout=30,
    pool_recycle=1800,  # Recycle connections after 30 minutes
)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

Base = declarative_base()


def get_db():
    """Dependency that provides a database session."""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


def init_db():
    """
    Import all models to ensure they are registered with SQLAlchemy.

    Note: Table creation is now handled by Alembic migrations.
    Run 'alembic upgrade head' to create/update database schema.
    """
    from models import (
        User,
        Organization,
        OrganizationMembership,
        OrganizationInvite,
        PasswordResetToken,
        APIKey,
        APIUsage,
        Webhook,
        WebhookDelivery,
    )
    # Schema creation is handled by Alembic migrations
    # To create tables, run: alembic upgrade head


def seed_test_user():
    """
    Seed a test user for development/testing purposes.
    Creates user, organization, and membership if not exists.
    Only runs in development environment.
    """
    # Only seed in development
    if os.getenv("ENVIRONMENT", "development") != "development":
        return

    from models import User, Organization, OrganizationMembership
    from auth.utils import get_password_hash

    TEST_EMAIL = "test@example.com"
    TEST_PASSWORD = "TestPassword123"
    TEST_NAME = "Test User"
    TEST_ORG_NAME = "Test Organization"
    TEST_ORG_SLUG = "test-org"

    db = SessionLocal()
    try:
        # Check if test user exists
        existing_user = db.query(User).filter(User.email == TEST_EMAIL).first()
        if existing_user:
            logger.debug(f"Test user already exists: {TEST_EMAIL}")
            return

        # Create test user
        user = User(
            email=TEST_EMAIL,
            password_hash=get_password_hash(TEST_PASSWORD),
            name=TEST_NAME,
            is_active=True,
            email_verified=True,
        )
        db.add(user)
        db.commit()
        db.refresh(user)

        # Create organization
        org = Organization(
            name=TEST_ORG_NAME,
            slug=TEST_ORG_SLUG,
            owner_id=user.id,
        )
        db.add(org)
        db.commit()
        db.refresh(org)

        # Create membership
        membership = OrganizationMembership(
            organization_id=org.id,
            user_id=user.id,
            role="owner",
            status="active",
        )
        db.add(membership)
        db.commit()

        logger.info(f"Test user created: {TEST_EMAIL}")
    except Exception as e:
        db.rollback()
        logger.error(f"Error seeding test user: {e}")
    finally:
        db.close()
