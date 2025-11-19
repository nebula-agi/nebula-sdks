"""
Custom exceptions for the Nebula Simple SDK
"""

from typing import Any


class NebulaException(Exception):
    """Base exception for Nebula API errors"""

    def __init__(
        self,
        message: str,
        status_code: int | None = None,
        details: dict[Any, Any] | None = None,
    ):
        self.message = message
        self.status_code = status_code
        self.details = details or {}
        super().__init__(self.message)

    def __str__(self):
        if self.status_code:
            return f"Nebula API Error ({self.status_code}): {self.message}"
        return f"Nebula API Error: {self.message}"


class NebulaClientException(Exception):
    """Exception for client-side errors (network, configuration, etc.)"""

    def __init__(self, message: str, original_exception: Exception | None = None):
        self.message = message
        self.original_exception = original_exception
        super().__init__(self.message)

    def __str__(self):
        return f"Nebula Client Error: {self.message}"


class NebulaAuthenticationException(NebulaException):
    """Exception for authentication errors"""

    def __init__(self, message: str = "Authentication failed"):
        super().__init__(message, status_code=401)


class NebulaRateLimitException(NebulaException):
    """Exception for rate limiting errors"""

    def __init__(self, message: str = "Rate limit exceeded"):
        super().__init__(message, status_code=429)


class NebulaValidationException(NebulaException):
    """Exception for validation errors"""

    def __init__(self, message: str, details: dict[Any, Any] | None = None):
        super().__init__(message, status_code=400, details=details)


class NebulaNotFoundException(NebulaException):
    """Exception for resource not found errors (engrams, documents, etc.)"""

    def __init__(self, resource_id: str, resource_type: str = "Resource"):
        super().__init__(f"{resource_type} not found: {resource_id}", status_code=404)
