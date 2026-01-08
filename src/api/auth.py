"""Authentication API endpoints."""
from fastapi import APIRouter, Depends
from fastapi.security import OAuth2PasswordBearer
from pydantic import BaseModel, EmailStr, Field, SecretStr
from typing import Optional

from cloudsound_shared.jwt_handler import (
    create_access_token,
    create_refresh_token,
    verify_token,
    TokenData,
)
from cloudsound_shared.config.settings import app_settings
from cloudsound_shared.logging import get_logger
from cloudsound_shared.exceptions import (
    AuthenticationError,
    TokenInvalidError,
    CredentialsInvalidError,
)

logger = get_logger(__name__)

router = APIRouter(prefix="/auth", tags=["authentication"])

oauth2_scheme = OAuth2PasswordBearer(tokenUrl=f"{app_settings.api_prefix}/auth/login")


class TokenResponse(BaseModel):
    """Token response model."""
    access_token: str = Field(..., description="JWT access token")
    refresh_token: str = Field(..., description="JWT refresh token")
    token_type: str = Field(default="bearer", description="Token type")
    expires_in: int = Field(
        default=3600,
        description="Token expiration time in seconds",
    )


class LoginRequest(BaseModel):
    """Login request model with validation."""
    email: EmailStr = Field(..., description="User email address")
    password: str = Field(
        ...,
        min_length=1,
        max_length=128,
        description="User password",
    )


class RefreshTokenRequest(BaseModel):
    """Refresh token request model."""
    refresh_token: str = Field(..., min_length=10, description="JWT refresh token")

# Default tenant ID - used for development and single-tenant deployments
DEFAULT_TENANT_ID = "aaaaaaaa-0000-0000-0000-000000000001"


@router.post("/login", response_model=TokenResponse)
async def login(request: LoginRequest) -> TokenResponse:
    """
    Authenticate user and return JWT tokens.
    
    Note: This is a placeholder implementation. In production, this should:
    1. Verify credentials against database
    2. Check user status (active, locked, etc.)
    3. Implement rate limiting
    4. Log authentication attempts
    """
    # TODO: Implement actual authentication logic
    # For now, accept any email/password for development
    logger.info("login_attempt", email=request.email)
    
    # Mock user data - replace with database lookup
    user_role = "admin" if request.email.lower().startswith("admin") else "user"
    user_data = {
        "user_id": "user-123",  # Get from database
        "email": request.email,
        "role": user_role,  # Get from database
        "tenant_id": DEFAULT_TENANT_ID,  # Default tenant for row-level multitenancy
    }
    
    access_token = create_access_token(user_data)
    refresh_token = create_refresh_token(user_data)
    
    logger.info("login_success", email=request.email, tenant_id=DEFAULT_TENANT_ID)
    
    return TokenResponse(
        access_token=access_token,
        refresh_token=refresh_token,
    )

@router.post("/refresh", response_model=TokenResponse)
async def refresh_token(request: RefreshTokenRequest) -> TokenResponse:
    """Refresh access token using refresh token."""
    token_data = verify_token(request.refresh_token)
    
    if not token_data or token_data.role != "refresh":
        logger.warning("invalid_refresh_token")
        raise TokenInvalidError(
            message="Invalid or expired refresh token",
        )
    
    # Create new access token
    user_data = {
        "user_id": token_data.user_id,
        "email": token_data.email,
        "role": token_data.role,
        "tenant_id": token_data.tenant_id,
    }
    
    access_token = create_access_token(user_data)
    new_refresh_token = create_refresh_token(user_data)  # New refresh token
    
    logger.info("token_refreshed", user_id=token_data.user_id)
    
    return TokenResponse(
        access_token=access_token,
        refresh_token=new_refresh_token,
    )


async def get_current_user(token: str = Depends(oauth2_scheme)) -> TokenData:
    """Dependency to get current authenticated user."""
    token_data = verify_token(token)
    
    if token_data is None:
        raise AuthenticationError(
            message="Could not validate credentials",
            details={"header": "Authorization"},
        )
    
    return token_data

