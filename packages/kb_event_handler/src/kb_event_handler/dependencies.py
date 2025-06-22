"""Global dependencies for the FastAPI application."""

import logging
import uuid
from typing import Annotated

from fastapi import Depends, Header, Request
from fastapi.security import HTTPBearer

from .config import settings
from .exceptions import AuthenticationError, ValidationError


logger = logging.getLogger(__name__)

# Security scheme for OpenAPI docs
security = HTTPBearer(auto_error=False)


async def get_correlation_id(request: Request) -> str:
    """Get or generate correlation ID for request tracking."""
    correlation_id = getattr(request.state, "correlation_id", None)
    if not correlation_id:
        correlation_id = str(uuid.uuid4())
        request.state.correlation_id = correlation_id
    return correlation_id


async def authenticate_api_key(
    x_api_key: Annotated[str, Header(alias="X-API-Key")]
) -> str:
    """Validate the API key from request headers."""
    if not x_api_key:
        raise AuthenticationError("API key is required")
    
    if x_api_key != settings.api_secret_key:
        raise AuthenticationError("Invalid API key")
    
    return x_api_key


async def get_tenant_id(
    x_tenant_id: Annotated[str, Header(alias="X-Tenant-ID")]
) -> int:
    """Extract and validate tenant ID from request headers."""
    if not x_tenant_id:
        raise ValidationError("Tenant ID is required in X-Tenant-ID header")
    
    try:
        tenant_id = int(x_tenant_id)
        if tenant_id <= 0:
            raise ValueError("Tenant ID must be positive")
        return tenant_id
    except (ValueError, TypeError) as e:
        raise ValidationError(
            f"Invalid tenant ID format: {x_tenant_id}",
            details={"provided_value": x_tenant_id, "error": str(e)}
        )


# Dependency aliases for common use
CorrelationIdDep = Annotated[str, Depends(get_correlation_id)]
ApiKeyDep = Annotated[str, Depends(authenticate_api_key)]
TenantIdDep = Annotated[int, Depends(get_tenant_id)] 