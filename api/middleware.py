"""
Authentication middleware for API endpoints
"""
import os
from typing import Optional
from fastapi import HTTPException, status, Request
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials

# Simple bearer token security scheme
security = HTTPBearer(auto_error=False)

class AuthMiddleware:
    """Authentication middleware for protecting API endpoints"""
    
    @staticmethod
    def is_auth_required() -> bool:
        """Check if authentication is required"""
        # Read at request time, not import time
        dashboard_password = os.getenv("DASHBOARD_PASSWORD", "")
        return bool(dashboard_password)
    
    @staticmethod
    async def verify_token(request: Request) -> bool:
        """
        Verify authentication token from session.
        
        Note: This is a simple implementation. In production, you should:
        - Store tokens in a database or Redis
        - Add token expiration
        - Add refresh tokens
        - Use JWT or similar standard
        """
        if not AuthMiddleware.is_auth_required():
            # No authentication required
            return True
        
        # Check for token in Authorization header
        auth_header = request.headers.get("Authorization")
        if auth_header and auth_header.startswith("Bearer "):
            token = auth_header.replace("Bearer ", "")
            # For now, any non-empty token is valid
            # In production, verify against stored tokens
            return bool(token)
        
        # No token provided but auth is required
        return False
    
    @staticmethod
    async def require_auth(request: Request):
        """
        Dependency that requires authentication.
        Raises HTTPException if not authenticated.
        """
        if not await AuthMiddleware.verify_token(request):
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Authentication required",
                headers={"WWW-Authenticate": "Bearer"},
            )
        return True


# Dependency for protecting endpoints
async def require_auth(request: Request):
    """FastAPI dependency for requiring authentication"""
    await AuthMiddleware.require_auth(request)
    return True

