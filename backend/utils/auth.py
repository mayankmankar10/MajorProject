# backend/utils/auth.py
# Simplified auth utilities for testing without authentication

from typing import Optional
from fastapi import HTTPException, Depends, Header
from dotenv import load_dotenv

load_dotenv()

# Simple mock functions for testing purposes
# These will be replaced when proper authentication is implemented

def get_password_hash(password: str) -> str:
    """Mock hash function for testing - returns plain password."""
    return f"hashed_{password}"


def verify_password(plain_password: str, hashed_password: str) -> bool:
    """Mock verify function for testing - simple comparison."""
    return f"hashed_{plain_password}" == hashed_password


def create_access_token(data: dict) -> str:
    """Mock token creation - returns a simple concatenated string."""
    return f"mock_token_{data.get('user_id')}_{data.get('role')}"


def decode_access_token(token: str) -> Optional[dict]:
    """Mock token decode - extracts info from mock token."""
    try:
        parts = token.split("_")
        if len(parts) >= 4 and parts[0] == "mock" and parts[1] == "token":
            return {
                "user_id": int(parts[2]),
                "role": parts[3]
            }
    except:
        pass
    return None


def get_current_user(authorization: Optional[str] = Header(None)):
    """Dependency to get current user from JWT token."""
    if not authorization:
        raise HTTPException(status_code=401, detail="Authorization header missing")
    
    # Extract token from "Bearer <token>"
    parts = authorization.split()
    if len(parts) != 2 or parts[0].lower() != "bearer":
        raise HTTPException(status_code=401, detail="Invalid authorization header format")
    
    token = parts[1]
    user_data = decode_access_token(token)
    
    if not user_data:
        raise HTTPException(status_code=401, detail="Invalid or expired token")
    
    return user_data
