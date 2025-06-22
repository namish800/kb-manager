"""Global exception handlers and custom exceptions."""

import logging
import traceback
from typing import Any, Dict, Optional

from fastapi import HTTPException, Request, status
from fastapi.responses import JSONResponse


logger = logging.getLogger(__name__)


# Custom Exception Classes
class KBEventHandlerException(Exception):
    """Base exception for KB Event Handler."""

    def __init__(
        self,
        message: str,
        error_code: str,
        status_code: int = status.HTTP_500_INTERNAL_SERVER_ERROR,
        details: Optional[Dict[str, Any]] = None,
    ):
        self.message = message
        self.error_code = error_code
        self.status_code = status_code
        self.details = details or {}
        super().__init__(message)


class AuthenticationError(KBEventHandlerException):
    """Authentication related errors."""

    def __init__(self, message: str = "Authentication failed", details: Optional[Dict[str, Any]] = None):
        super().__init__(
            message=message,
            error_code="AUTHENTICATION_ERROR",
            status_code=status.HTTP_401_UNAUTHORIZED,
            details=details,
        )


class ValidationError(KBEventHandlerException):
    """Validation related errors."""

    def __init__(self, message: str, details: Optional[Dict[str, Any]] = None):
        super().__init__(
            message=message,
            error_code="VALIDATION_ERROR",
            status_code=status.HTTP_400_BAD_REQUEST,
            details=details,
        )


class TenantNotFoundError(KBEventHandlerException):
    """Tenant not found errors."""

    def __init__(self, tenant_id: int):
        super().__init__(
            message=f"Tenant with ID {tenant_id} not found",
            error_code="TENANT_NOT_FOUND",
            status_code=status.HTTP_404_NOT_FOUND,
            details={"tenant_id": tenant_id},
        )


class ResourceNotFoundError(KBEventHandlerException):
    """Resource not found errors."""

    def __init__(self, resource_type: str, resource_id: Any):
        super().__init__(
            message=f"{resource_type} with ID {resource_id} not found",
            error_code="RESOURCE_NOT_FOUND",
            status_code=status.HTTP_404_NOT_FOUND,
            details={"resource_type": resource_type, "resource_id": resource_id},
        )


# Exception Handlers
async def kb_event_handler_exception_handler(
    request: Request, exc: KBEventHandlerException
) -> JSONResponse:
    """Handle custom KB Event Handler exceptions."""
    correlation_id = getattr(request.state, "correlation_id", "unknown")
    
    logger.error(
        "KB Event Handler exception occurred",
        extra={
            "error_code": exc.error_code,
            "message": exc.message,
            "status_code": exc.status_code,
            "details": exc.details,
            "correlation_id": correlation_id,
            "path": request.url.path,
            "method": request.method,
        },
    )

    return JSONResponse(
        status_code=exc.status_code,
        content={
            "error": exc.error_code,
            "message": exc.message,
            "correlation_id": correlation_id,
            "details": exc.details,
        },
    )


async def http_exception_handler(request: Request, exc: HTTPException) -> JSONResponse:
    """Handle FastAPI HTTP exceptions."""
    correlation_id = getattr(request.state, "correlation_id", "unknown")
    
    logger.warning(
        "HTTP exception occurred",
        extra={
            "status_code": exc.status_code,
            "detail": exc.detail,
            "correlation_id": correlation_id,
            "path": request.url.path,
            "method": request.method,
        },
    )

    return JSONResponse(
        status_code=exc.status_code,
        content={
            "error": "HTTP_ERROR",
            "message": exc.detail,
            "correlation_id": correlation_id,
        },
    )


async def general_exception_handler(request: Request, exc: Exception) -> JSONResponse:
    """Handle unexpected exceptions."""
    correlation_id = getattr(request.state, "correlation_id", "unknown")
    
    logger.error(
        "Unexpected exception occurred",
        extra={
            "exception_type": type(exc).__name__,
            "exception_message": str(exc),
            "correlation_id": correlation_id,
            "path": request.url.path,
            "method": request.method,
            "traceback": traceback.format_exc(),
        },
    )

    return JSONResponse(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        content={
            "error": "INTERNAL_SERVER_ERROR",
            "message": "An unexpected error occurred",
            "correlation_id": correlation_id,
        },
    ) 