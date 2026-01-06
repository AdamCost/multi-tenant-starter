"""
Multi-Tenant Starter - SaaS Boilerplate

A production-ready multi-tenant SaaS foundation with authentication,
organization management, and API key support.
"""
import os
from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from starlette.middleware.base import BaseHTTPMiddleware
from dotenv import load_dotenv
from slowapi import _rate_limit_exceeded_handler
from slowapi.errors import RateLimitExceeded
from limiter import limiter
from logging_config import setup_logging, get_logger


class SecurityHeadersMiddleware(BaseHTTPMiddleware):
    """Add security headers to all responses."""

    async def dispatch(self, request: Request, call_next):
        response = await call_next(request)

        # Content Security Policy - allows React app to function
        csp_directives = [
            "default-src 'self'",
            "script-src 'self' 'unsafe-inline' 'unsafe-eval'",
            "style-src 'self' 'unsafe-inline'",
            "img-src 'self' data: https: blob:",
            "font-src 'self' data:",
            "connect-src 'self' https://*.sendgrid.net wss:",
            "frame-ancestors 'none'",
            "base-uri 'self'",
            "form-action 'self'",
            "object-src 'none'",
        ]
        response.headers["Content-Security-Policy"] = "; ".join(csp_directives)

        # Additional security headers
        response.headers["X-Content-Type-Options"] = "nosniff"
        response.headers["X-Frame-Options"] = "DENY"
        response.headers["X-XSS-Protection"] = "1; mode=block"
        response.headers["Referrer-Policy"] = "strict-origin-when-cross-origin"
        response.headers["Permissions-Policy"] = "geolocation=(), microphone=(), camera=()"

        # HSTS in production
        if os.getenv("ENVIRONMENT") == "production":
            response.headers["Strict-Transport-Security"] = "max-age=31536000; includeSubDomains"

        return response


# Load environment variables
load_dotenv()

# Setup logging
setup_logging()
logger = get_logger(__name__)

# Create FastAPI app
app = FastAPI(
    title="Multi-Tenant Starter",
    description="Production-ready multi-tenant SaaS boilerplate",
    version="1.0.0",
    docs_url="/docs",
    redoc_url="/redoc",
)

# CORS configuration - require explicit origins in production
ENVIRONMENT = os.getenv("ENVIRONMENT", "development")
if ENVIRONMENT == "production":
    ALLOWED_ORIGINS = os.getenv("ALLOWED_ORIGINS", "").split(",")
    if not ALLOWED_ORIGINS or ALLOWED_ORIGINS == [""]:
        raise ValueError("ALLOWED_ORIGINS must be set in production")
else:
    ALLOWED_ORIGINS = os.getenv("ALLOWED_ORIGINS", "http://localhost:5173,http://localhost:3000").split(",")

app.add_middleware(
    CORSMiddleware,
    allow_origins=ALLOWED_ORIGINS,
    allow_credentials=True,
    allow_methods=["GET", "POST", "PATCH", "DELETE", "OPTIONS"],
    allow_headers=["Authorization", "Content-Type", "X-Organization-ID"],
    max_age=3600,
)

# Security headers middleware
app.add_middleware(SecurityHeadersMiddleware)

# Rate limiting setup
app.state.limiter = limiter
app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)

# Import and include routers
from routes import auth_router, organizations_router
from routes.organizations import invite_router as org_invite_router
from routes.api_keys import router as api_keys_router

app.include_router(auth_router)
app.include_router(organizations_router)
app.include_router(org_invite_router)
app.include_router(api_keys_router)


# Health check endpoint
@app.get("/health")
async def health_check():
    """Health check endpoint."""
    return {"status": "healthy", "service": "multi-tenant-starter"}


@app.get("/")
async def root():
    """Root endpoint with API info."""
    return {
        "name": "Multi-Tenant Starter",
        "version": "1.0.0",
        "description": "Production-ready multi-tenant SaaS boilerplate",
        "docs": "/docs",
    }


# Environment variable validation
def validate_environment():
    """Validate required environment variables are set."""
    required_vars = ["DATABASE_URL", "SECRET_KEY"]
    optional_but_recommended = ["SENDGRID_API_KEY"]

    missing = [var for var in required_vars if not os.getenv(var)]
    if missing:
        raise ValueError(f"Missing required environment variables: {', '.join(missing)}")

    # Warn about missing optional vars
    missing_optional = [var for var in optional_but_recommended if not os.getenv(var)]
    if missing_optional:
        logger.warning(f"Optional environment variables not set: {', '.join(missing_optional)}")
        logger.warning("Some features may not work correctly")


# Run database migrations
def run_migrations():
    """Run alembic migrations programmatically."""
    from alembic.config import Config
    from alembic import command

    alembic_cfg = Config("alembic.ini")
    command.upgrade(alembic_cfg, "head")


# Database initialization on startup
@app.on_event("startup")
async def startup_event():
    """Validate environment and initialize database on startup."""
    # Validate environment variables
    if ENVIRONMENT == "production":
        validate_environment()

    # Run database migrations
    try:
        run_migrations()
        logger.info("Database migrations completed successfully")
    except Exception as e:
        logger.warning(f"Could not run migrations: {e}")
        logger.warning("Falling back to direct table creation")

        # Fallback: Initialize database directly
        from database import init_db
        try:
            init_db()
            logger.info("Database tables initialized successfully")
        except Exception as e2:
            logger.warning(f"Could not initialize database: {e2}")

    # Seed test user if needed
    from database import seed_test_user
    try:
        seed_test_user()
    except Exception as e:
        logger.warning(f"Could not seed test user: {e}")


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        "main:app",
        host="0.0.0.0",
        port=int(os.getenv("PORT", 8001)),
        reload=os.getenv("ENVIRONMENT", "development") == "development"
    )
