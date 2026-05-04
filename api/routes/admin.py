"""Admin routes."""
from __future__ import annotations

from fastapi import APIRouter, Depends

from api.auth import require_api_secret
from alibabot.storage import SupabaseStorage

router = APIRouter(dependencies=[Depends(require_api_secret)])


@router.post("/purge")
async def purge_old():
    """Trigger purge_old_snapshots manually (>7 days rejected/pending)."""
    storage = SupabaseStorage()
    result = storage.purge_old()
    return {"purged": result}
