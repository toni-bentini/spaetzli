"""Authentication and signature validation."""

import base64
import hashlib
import hmac
import logging
from typing import Optional
from urllib.parse import urlencode

from .config import config

logger = logging.getLogger(__name__)


def validate_signature(
    api_key: str,
    api_sign: str,
    method: str,
    api_version: str,
    params: dict,
    is_nest: bool = False,
) -> bool:
    """
    Validate the API signature.
    
    In mock mode with validate_signatures=False, always returns True.
    When enabled, validates HMAC-SHA512 signature.
    
    Args:
        api_key: The API key from header
        api_sign: The base64-encoded signature from header
        method: The API method/endpoint name
        api_version: API version (e.g., "1")
        params: Request parameters
        is_nest: Whether this is a nest API endpoint (affects signature)
    
    Returns:
        True if signature is valid or validation is disabled
    """
    if not config.validate_signatures:
        # Accept any credentials in mock mode
        logger.debug(f"Signature validation disabled, accepting request for {method}")
        return True
    
    # For strict mode, we'd need to know the secret
    # Since this is a mock server, we just accept everything
    logger.warning("Strict signature validation not implemented in mock server")
    return True


def extract_api_key(headers: dict) -> Optional[str]:
    """Extract API key from request headers."""
    return headers.get("API-KEY") or headers.get("api-key")


def extract_api_sign(headers: dict) -> Optional[str]:
    """Extract API signature from request headers."""
    return headers.get("API-SIGN") or headers.get("api-sign")


def require_auth(headers: dict) -> tuple[bool, Optional[str]]:
    """
    Check if request has valid authentication.
    
    Returns:
        Tuple of (is_valid, error_message)
    """
    api_key = extract_api_key(headers)
    
    if not api_key:
        return False, "Missing API-KEY header"
    
    # In mock mode, any non-empty API key is accepted
    if not config.validate_signatures:
        return True, None
    
    api_sign = extract_api_sign(headers)
    if not api_sign:
        return False, "Missing API-SIGN header"
    
    # Would validate signature here in strict mode
    return True, None
