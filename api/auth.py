"""API authentication."""
from __future__ import annotations

import os
from fastapi import Header, HTTPException, status


async def require_api_secret(x_api_secret: str | None = Header(default=None)):
    """Dependency: validates the x-api-secret header against env var."""
    expected = os.environ.get("API_SECRET")
    if not expected:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="API_SECRET not configured on server",
        )
    if x_api_secret != expected:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or missing x-api-secret header",
        )
