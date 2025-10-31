# backend/utils/auth.py
# Minimal placeholder auth helpers - replace with real auth (Firebase / OAuth / JWT) in production

from fastapi import HTTPException, Header

def require_api_key(x_api_key: str | None = Header(None)):
    # in dev, accept any non-empty key or skip
    if not x_api_key:
        raise HTTPException(status_code=401, detail="Missing API Key")
    return True
