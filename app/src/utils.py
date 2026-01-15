"""Utility functions for the application"""
import os
from flask import request, has_request_context


def get_base_url():
    """
    Get the base URL for the application.
    
    Priority:
    1. BASE_URL environment variable (if set)
    2. Dynamically construct from request (for ECS Express Mode)
    3. Default to localhost for development
    
    This allows the application to work even if BASE_URL is not set initially,
    which is useful for ECS Express Mode where the URL is only known after deployment.
    """
    # First, check if BASE_URL is explicitly set
    base_url = os.getenv('BASE_URL')
    
    if base_url:
        return base_url.rstrip('/')
    
    # If not set, try to construct from the current request
    # This works in ECS Express Mode where the ALB provides the correct host
    if has_request_context():
        try:
            # Get the scheme (http/https)
            scheme = request.headers.get('X-Forwarded-Proto', request.scheme)
            
            # Get the host (includes port if non-standard)
            host = request.headers.get('X-Forwarded-Host', request.host)
            
            # Construct the base URL
            return f"{scheme}://{host}"
        except Exception:
            # If anything goes wrong, fall through to default
            pass
    
    # Fallback to localhost for development
    return 'http://127.0.0.1:5001'
