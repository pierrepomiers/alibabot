"""Snapshot routes."""
from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException, Query

from api.auth import require_api_secret
from api.schemas import SnapshotSummary, SnapshotDetail, SnapshotDiff, DiffSummary
from api.services.snapshots_service import SnapshotsService
from api.services.diff_service import DiffService

router = APIRouter(dependencies=[Depends(require_api_secret)])


@router.get("", response_model=list[SnapshotSummary])
async def list_snapshots(
    status: str | None = Query(default=None, description="pending | active | rejected | archived"),
    limit: int = Query(default=20, ge=1, le=100),
):
    svc = SnapshotsService()
    return svc.list_snapshots(status=status, limit=limit)


@router.get("/{snapshot_id}", response_model=SnapshotDetail)
async def get_snapshot(snapshot_id: str):
    svc = SnapshotsService()
    snap = svc.get_snapshot(snapshot_id)
    if not snap:
        raise HTTPException(status_code=404, detail=f"Snapshot not found: {snapshot_id}")
    return snap


@router.get("/{snapshot_id}/diff", response_model=SnapshotDiff)
async def diff_snapshot(
    snapshot_id: str,
    detail: str = Query(default="full", regex="^(full|summary)$"),
):
    svc = SnapshotsService()
    target = svc.get_snapshot(snapshot_id)
    if not target:
        raise HTTPException(status_code=404, detail=f"Snapshot not found: {snapshot_id}")

    active = svc.get_active_snapshot()

    diff_svc = DiffService()
    result = diff_svc.diff(
        target_uuid=target["id"],
        base_uuid=active["id"] if active else None,
    )

    response = {
        "snapshot_id": snapshot_id,
        "active_snapshot_id": active["snapshot_id"] if active else None,
        "summary": result["summary"],
        "added": [],
        "removed": [],
        "price_changed": [],
        "stock_changed": [],
    }
    if detail == "full":
        response["added"] = result["added"]
        response["removed"] = result["removed"]
        response["price_changed"] = result["price_changed"]
        response["stock_changed"] = result["stock_changed"]
    return response


@router.post("/{snapshot_id}/accept", response_model=SnapshotSummary)
async def accept_snapshot(
    snapshot_id: str,
    activated_by: str = Query(default="api"),
):
    svc = SnapshotsService()
    try:
        return svc.accept(snapshot_id, activated_by=activated_by)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.post("/{snapshot_id}/reject", response_model=SnapshotSummary)
async def reject_snapshot(
    snapshot_id: str,
    reason: str | None = Query(default=None),
):
    svc = SnapshotsService()
    try:
        return svc.reject(snapshot_id, reason=reason)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
