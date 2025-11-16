"""
Authentication API for password-protected access
"""
import os
import secrets
from fastapi import APIRouter, HTTPException, status
from pydantic import BaseModel
from typing import Optional

router = APIRouter(prefix="/auth", tags=["Authentication"])

class PasswordVerification(BaseModel):
    password: str

class AuthResponse(BaseModel):
    success: bool
    message: str
    token: Optional[str] = None

@router.post("/verify", response_model=AuthResponse)
async def verify_password(data: PasswordVerification):
    """
    Verify the dashboard password
    
    Returns a simple token if password is correct
    """
    # Read password at request time, not import time
    dashboard_password = os.getenv("DASHBOARD_PASSWORD", "")
    
    if not dashboard_password:
        # If no password is set, allow access with warning
        return AuthResponse(
            success=True,
            message="No password configured - access granted",
            token=secrets.token_urlsafe(32)
        )
    
    if data.password == dashboard_password:
        # Generate a simple session token
        token = secrets.token_urlsafe(32)
        return AuthResponse(
            success=True,
            message="Authentication successful",
            token=token
        )
    else:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid password"
        )

@router.get("/status")
async def auth_status():
    """
    Check if authentication is required
    """
    # Read password at request time, not import time
    dashboard_password = os.getenv("DASHBOARD_PASSWORD", "")
    
    return {
        "auth_required": bool(dashboard_password),
        "configured": bool(dashboard_password)
    }

