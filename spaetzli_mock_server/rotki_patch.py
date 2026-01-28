"""
Patch module to redirect Rotki premium API calls to the mock server.

Usage:
    1. Import this module early in your Rotki startup
    2. Or apply the patch manually to rotkehlchen/premium/premium.py

This module monkey-patches the Premium class to use configurable URLs.
"""

import os
import logging

logger = logging.getLogger(__name__)

# Configuration via environment variables
MOCK_SERVER_URL = os.environ.get("SPAETZLI_MOCK_URL", "http://localhost:8080")
ENABLE_MOCK = os.environ.get("SPAETZLI_ENABLE", "0") == "1"


def patch_premium_urls():
    """
    Patch the Premium class to use mock server URLs.
    
    Call this before creating any Premium instances.
    """
    if not ENABLE_MOCK:
        logger.info("Spaetzli mock server disabled (set SPAETZLI_ENABLE=1 to enable)")
        return False
    
    try:
        from rotkehlchen.premium import premium as premium_module
        
        original_init = premium_module.Premium.__init__
        
        def patched_init(self, *args, **kwargs):
            original_init(self, *args, **kwargs)
            # Override URLs after original init
            self.rotki_api = f'{MOCK_SERVER_URL}/api/{self.apiversion}/'
            self.rotki_nest = f'{MOCK_SERVER_URL}/nest/{self.apiversion}/'
            logger.info(f"Spaetzli: Redirecting premium API to {MOCK_SERVER_URL}")
        
        premium_module.Premium.__init__ = patched_init
        logger.info("Spaetzli: Premium URL patch applied successfully")
        return True
        
    except Exception as e:
        logger.error(f"Spaetzli: Failed to patch Premium class: {e}")
        return False


def get_mock_credentials():
    """
    Get mock credentials that will work with the mock server.
    
    Returns:
        Tuple of (api_key, api_secret) that the mock server will accept.
    """
    import base64
    
    # Any credentials work with the mock server
    api_key = "spaetzli-mock-key-" + "x" * 64
    api_secret = base64.b64encode(b"spaetzli-mock-secret-" + b"x" * 64).decode()
    
    return api_key, api_secret


# Auto-patch if enabled
if ENABLE_MOCK:
    patch_premium_urls()
