"""
Authentication API for password-protected access
"""
import os
import secrets
from fastapi import APIRouter, HTTPException, status
from pydantic import BaseModel
from typing import Optional

router = APIRouter(prefix="/auth", tags=["Authentication"])

# Get password from environment variable
DASHBOARD_PASSWORD = os.getenv("DASHBOARD_PASSWORD", "")

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
    if not DASHBOARD_PASSWORD:
        # If no password is set, allow access with warning
        return AuthResponse(
            success=True,
            message="No password configured - access granted",
            token=secrets.token_urlsafe(32)
        )
    
    if data.password == DASHBOARD_PASSWORD:
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
    return {
        "auth_required": bool(DASHBOARD_PASSWORD),
        "configured": bool(DASHBOARD_PASSWORD)
    }

