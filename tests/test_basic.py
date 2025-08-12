"""
Basic tests for FinOps Lite.
"""

import pytest
from finops_lite.utils.errors import (
    validate_days, 
    validate_threshold, 
    ValidationError,
    AWSCredentialsError,
    handle_error
)

def test_validate_days_valid():
    """Test valid days input."""
    assert validate_days(30) == 30
    assert validate_days(1) == 1
    assert validate_days(365) == 365

def test_validate_days_invalid():
    """Test invalid days input."""
    with pytest.raises(ValidationError):
        validate_days(0)
    
    with pytest.raises(ValidationError):
        validate_days(400)
    
    with pytest.raises(ValidationError):
        validate_days(-5)

def test_validate_threshold_valid():
    """Test valid threshold input."""
    assert validate_threshold(10.0) == 10.0
    assert validate_threshold(0) == 0.0
    assert validate_threshold(100) == 100.0

def test_validate_threshold_invalid():
    """Test invalid threshold input."""
    with pytest.raises(ValidationError):
        validate_threshold(-1)
    
    with pytest.raises(ValidationError):
        validate_threshold(50000)  # Too high

def test_error_classes():
    """Test custom exception classes."""
    # Test that our custom exceptions can be instantiated
    cred_error = AWSCredentialsError("Test credentials error")
    assert str(cred_error) == "Test credentials error"
    
    val_error = ValidationError("Test validation error")
    assert str(val_error) == "Test validation error"

def test_handle_error_basic():
    """Test basic error handling (doesn't crash)."""
    # This just tests that handle_error doesn't crash
    try:
        handle_error(ValidationError("test"), verbose=False)
        handle_error(AWSCredentialsError("test"), verbose=False)
    except Exception:
        pytest.fail("handle_error should not raise exceptions")

def test_cli_imports():
    """Test that CLI modules can be imported."""
    from finops_lite.cli import cli, main
    from finops_lite.utils.config import load_config
    from finops_lite.utils.logger import setup_logger
    
    # If we get here without ImportError, the test passes
    assert True