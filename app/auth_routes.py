"""
Authentication & Authorization API Routes
Provides secure REST endpoints for user signup, login, session validation,
and logout with PBKDF2-HMAC-SHA256 password hashing and SQLite persistence.
"""

from fastapi import APIRouter, HTTPException, Depends, Header, Query
from pydantic import BaseModel, EmailStr, Field
from typing import Optional, Dict, Any
import secrets
import sqlite3

from src.auth import register_user, authenticate_user
from src.tracker import track_activity

router = APIRouter(prefix="/api/auth", tags=["Authentication"])

# In-memory session store: token -> {"user": user_data, "created": timestamp}
# Sessions expire after 24 hours. Tokens live only in this process.
SESSION_TTL_SECONDS = 24 * 60 * 60
ACTIVE_SESSIONS: Dict[str, Dict[str, Any]] = {}


def _create_session(user_info: Dict[str, Any]) -> str:
    import time
    token = secrets.token_hex(24)
    ACTIVE_SESSIONS[token] = {
        "user": user_info,
        "created": time.time(),
    }
    return token


def _get_session_user(auth_token: Optional[str]) -> Optional[Dict[str, Any]]:
    import time
    if not auth_token:
        return None
    session = ACTIVE_SESSIONS.get(auth_token)
    if not session:
        return None
    if time.time() - session["created"] > SESSION_TTL_SECONDS:
        ACTIVE_SESSIONS.pop(auth_token, None)
        return None
    return session["user"]


class SignUpRequest(BaseModel):
    username: str = Field(..., min_length=3, max_length=50)
    email: str = Field(..., min_length=5, max_length=100)
    password: str = Field(..., min_length=6, max_length=100)
    full_name: Optional[str] = ""
    tier: Optional[str] = "pro"


class LoginRequest(BaseModel):
    username: str = Field(..., min_length=1)  # Can be username or email
    password: str = Field(..., min_length=1)



@router.post("/signup")
@router.post("/register")
async def signup(req: SignUpRequest):
    """Register a new user account with secure password hashing."""
    success, message = register_user(
        username=req.username,
        email=req.email,
        password=req.password,
        full_name=req.full_name or req.username,
        tier=req.tier or "pro"
    )

    if not success:
        raise HTTPException(status_code=400, detail=message)

    user_data = get_user_by_username(req.username)
    if not user_data:
        user_data = {
            "username": req.username,
            "email": req.email,
            "full_name": req.full_name or req.username,
            "tier": req.tier or "pro",
        }

    # Generate session token
    token = _create_session(user_data)

    return {
        "status": "success",
        "message": "Account created successfully! Welcome to Market ML.",
        "user": user_data,
        "token": token
    }


@router.post("/login")
async def login(req: LoginRequest):
    """Authenticate existing user credentials."""
    success, message, user_data = authenticate_user(
        username_or_email=req.username,
        password=req.password
    )

    if not success or not user_data:
        raise HTTPException(status_code=401, detail=message)

    # Sanitize user dict (remove sensitive fields if any)
    user_info = {
        "id": user_data.get("id"),
        "username": user_data.get("username"),
        "email": user_data.get("email"),
        "full_name": user_data.get("full_name"),
        "tier": user_data.get("tier", "pro"),
        "created_at": user_data.get("created_at")
    }

    # Generate session token
    token = _create_session(user_info)

    return {
        "status": "success",
        "message": message,
        "user": user_info,
        "token": token
    }


@router.get("/me")
async def get_current_user(
    authorization: Optional[str] = Header(None),
    token: Optional[str] = Query(None)
):
    """Validate the current session token. A valid token is mandatory — user
    profiles can never be fetched by username alone."""
    auth_token = token
    if authorization and authorization.startswith("Bearer "):
        auth_token = authorization.split(" ")[1]

    user = _get_session_user(auth_token)
    if user is not None:
        return {
            "status": "success",
            "authenticated": True,
            "user": user
        }

    raise HTTPException(status_code=401, detail="Session expired or invalid credentials")


@router.post("/logout")
async def logout(
    authorization: Optional[str] = Header(None),
    token: Optional[str] = Query(None)
):
    """Invalidate active session token."""
    auth_token = token
    if authorization and authorization.startswith("Bearer "):
        auth_token = authorization.split(" ")[1]

    user = _get_session_user(auth_token)
    if user is not None:
        ACTIVE_SESSIONS.pop(auth_token, None)
        track_activity(
            action="USER_LOGOUT",
            username=user.get("username", "guest"),
            details={"logout_status": "successful"}
        )

    return {
        "status": "success",
        "message": "Logged out successfully"
    }
