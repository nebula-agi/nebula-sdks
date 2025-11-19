"""
Tests for the exception classes
"""

from nebula import (
    NebulaAuthenticationException,
    NebulaClientException,
    NebulaException,
    NebulaRateLimitException,
    NebulaValidationException,
)


class TestNebulaException:
    """Test cases for NebulaException"""

    def test_nebula_exception_creation(self):
        """Test creating NebulaException with message only"""
        exception = NebulaException("Test error message")

        assert str(exception) == "Nebula API Error: Test error message"
        assert exception.message == "Test error message"
        assert exception.status_code is None
        assert exception.details == {}

    def test_nebula_exception_with_status_code(self):
        """Test creating NebulaException with status code"""
        exception = NebulaException("Test error message", status_code=404)

        assert str(exception) == "Nebula API Error (404): Test error message"
        assert exception.message == "Test error message"
        assert exception.status_code == 404
        assert exception.details == {}

    def test_nebula_exception_with_details(self):
        """Test creating NebulaException with details"""
        details = {"field": "required", "value": "missing"}
        exception = NebulaException(
            "Test error message", status_code=400, details=details
        )

        assert str(exception) == "Nebula API Error (400): Test error message"
        assert exception.message == "Test error message"
        assert exception.status_code == 400
        assert exception.details == details

    def test_nebula_exception_inheritance(self):
        """Test that NebulaException inherits from Exception"""
        exception = NebulaException("Test error message")
        assert isinstance(exception, Exception)


class TestNebulaClientException:
    """Test cases for NebulaClientException"""

    def test_nebula_client_exception_creation(self):
        """Test creating NebulaClientException with message only"""
        exception = NebulaClientException("Test client error")

        assert str(exception) == "Nebula Client Error: Test client error"
        assert exception.message == "Test client error"
        assert exception.original_exception is None

    def test_nebula_client_exception_with_original_exception(self):
        """Test creating NebulaClientException with original exception"""
        original_exception = ValueError("Original error")
        exception = NebulaClientException("Test client error", original_exception)

        assert str(exception) == "Nebula Client Error: Test client error"
        assert exception.message == "Test client error"
        assert exception.original_exception == original_exception

    def test_nebula_client_exception_inheritance(self):
        """Test that NebulaClientException inherits from Exception"""
        exception = NebulaClientException("Test client error")
        assert isinstance(exception, Exception)


class TestNebulaAuthenticationException:
    """Test cases for NebulaAuthenticationException"""

    def test_nebula_authentication_exception_creation(self):
        """Test creating NebulaAuthenticationException with default message"""
        exception = NebulaAuthenticationException()

        assert str(exception) == "Nebula API Error (401): Authentication failed"
        assert exception.message == "Authentication failed"
        assert exception.status_code == 401
        assert exception.details == {}

    def test_nebula_authentication_exception_with_custom_message(self):
        """Test creating NebulaAuthenticationException with custom message"""
        exception = NebulaAuthenticationException("Invalid API key")

        assert str(exception) == "Nebula API Error (401): Invalid API key"
        assert exception.message == "Invalid API key"
        assert exception.status_code == 401

    def test_nebula_authentication_exception_inheritance(self):
        """Test that NebulaAuthenticationException inherits from NebulaException"""
        exception = NebulaAuthenticationException()
        assert isinstance(exception, NebulaException)
        assert isinstance(exception, Exception)


class TestNebulaRateLimitException:
    """Test cases for NebulaRateLimitException"""

    def test_nebula_rate_limit_exception_creation(self):
        """Test creating NebulaRateLimitException with default message"""
        exception = NebulaRateLimitException()

        assert str(exception) == "Nebula API Error (429): Rate limit exceeded"
        assert exception.message == "Rate limit exceeded"
        assert exception.status_code == 429
        assert exception.details == {}

    def test_nebula_rate_limit_exception_with_custom_message(self):
        """Test creating NebulaRateLimitException with custom message"""
        exception = NebulaRateLimitException("Too many requests")

        assert str(exception) == "Nebula API Error (429): Too many requests"
        assert exception.message == "Too many requests"
        assert exception.status_code == 429

    def test_nebula_rate_limit_exception_inheritance(self):
        """Test that NebulaRateLimitException inherits from NebulaException"""
        exception = NebulaRateLimitException()
        assert isinstance(exception, NebulaException)
        assert isinstance(exception, Exception)


class TestNebulaValidationException:
    """Test cases for NebulaValidationException"""

    def test_nebula_validation_exception_creation(self):
        """Test creating NebulaValidationException with message only"""
        exception = NebulaValidationException("Validation error")

        assert str(exception) == "Nebula API Error (400): Validation error"
        assert exception.message == "Validation error"
        assert exception.status_code == 400
        assert exception.details == {}

    def test_nebula_validation_exception_with_details(self):
        """Test creating NebulaValidationException with details"""
        details = {"field": "required", "value": "missing"}
        exception = NebulaValidationException("Validation error", details)

        assert str(exception) == "Nebula API Error (400): Validation error"
        assert exception.message == "Validation error"
        assert exception.status_code == 400
        assert exception.details == details

    def test_nebula_validation_exception_inheritance(self):
        """Test that NebulaValidationException inherits from NebulaException"""
        exception = NebulaValidationException("Validation error")
        assert isinstance(exception, NebulaException)
        assert isinstance(exception, Exception)


class TestExceptionHierarchy:
    """Test the exception hierarchy"""

    def test_exception_hierarchy(self):
        """Test that all exceptions are properly related"""
        # Base exceptions
        nebula_exception = NebulaException("Test")
        client_exception = NebulaClientException("Test")

        # Specific exceptions
        auth_exception = NebulaAuthenticationException()
        rate_limit_exception = NebulaRateLimitException()
        validation_exception = NebulaValidationException("Test")

        # All should inherit from Exception
        assert isinstance(nebula_exception, Exception)
        assert isinstance(client_exception, Exception)
        assert isinstance(auth_exception, Exception)
        assert isinstance(rate_limit_exception, Exception)
        assert isinstance(validation_exception, Exception)

        # Specific exceptions should inherit from NebulaException
        assert isinstance(auth_exception, NebulaException)
        assert isinstance(rate_limit_exception, NebulaException)
        assert isinstance(validation_exception, NebulaException)

        # ClientException should NOT inherit from NebulaException
        assert not isinstance(client_exception, NebulaException)

        # NebulaException should NOT inherit from NebulaClientException
        assert not isinstance(nebula_exception, NebulaClientException)
