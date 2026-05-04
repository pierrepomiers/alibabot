"""Snapshots business logic."""
from __future__ import annotations

from datetime import datetime, timezone
from typing import Any

from alibabot.storage import SupabaseStorage


class SnapshotsService:
    def __init__(self, storage: SupabaseStorage | None = None):
        self.storage = storage or SupabaseStorage()
        self.client = self.storage.client

    # ─── Listing ────────────────────────────────────────────────────

    def list_snapshots(self, status: str | None = None, limit: int = 20) -> list[dict[str, Any]]:
        rows = self.storage.list_snapshots(status=status, limit=limit)
        return [self._enrich(row) for row in rows]

    def get_snapshot(self, snapshot_id: str) -> dict[str, Any] | None:
        result = (
            self.client.table("catalog_snapshots")
            .select("*")
            .eq("snapshot_id", snapshot_id)
            .maybe_single()
            .execute()
        )
        if not result.data:
            return None
        return self._enrich(result.data)

    def get_snapshot_by_uuid(self, uuid: str) -> dict[str, Any] | None:
        result = (
            self.client.table("catalog_snapshots")
            .select("*")
            .eq("id", uuid)
            .maybe_single()
            .execute()
        )
        if not result.data:
            return None
        return self._enrich(result.data)

    def get_active_snapshot(self) -> dict[str, Any] | None:
        result = (
            self.client.table("catalog_snapshots")
            .select("*")
            .eq("status", "active")
            .order("activated_at", desc=True)
            .limit(1)
            .execute()
        )
        rows = result.data or []
        if not rows:
            return None
        return self._enrich(rows[0])

    # ─── Mutations ──────────────────────────────────────────────────

    def accept(self, snapshot_id: str, activated_by: str = "api") -> dict[str, Any]:
        snap = self.get_snapshot(snapshot_id)
        if not snap:
            raise ValueError(f"Snapshot not found: {snapshot_id}")
        if snap["status"] != "pending":
            raise ValueError(f"Cannot accept snapshot in status '{snap['status']}'")

        now = datetime.now(timezone.utc).isoformat()

        # Archive previous active
        self.client.table("catalog_snapshots").update(
            {"status": "archived"}
        ).eq("status", "active").execute()

        # Activate the chosen one
        result = (
            self.client.table("catalog_snapshots")
            .update({
                "status": "active",
                "activated_at": now,
                "activated_by": activated_by,
            })
            .eq("snapshot_id", snapshot_id)
            .execute()
        )
        return self._enrich(result.data[0]) if result.data else snap

    def reject(self, snapshot_id: str, reason: str | None = None) -> dict[str, Any]:
        snap = self.get_snapshot(snapshot_id)
        if not snap:
            raise ValueError(f"Snapshot not found: {snapshot_id}")
        if snap["status"] != "pending":
            raise ValueError(f"Cannot reject snapshot in status '{snap['status']}'")

        update = {"status": "rejected"}
        if reason:
            update["notes"] = reason
        result = (
            self.client.table("catalog_snapshots")
            .update(update)
            .eq("snapshot_id", snapshot_id)
            .execute()
        )
        return self._enrich(result.data[0]) if result.data else snap

    # ─── Helpers ────────────────────────────────────────────────────

    def _enrich(self, row: dict[str, Any]) -> dict[str, Any]:
        """Enrichit un row snapshot avec item_count + error_count calculés."""
        stats = row.get("stats") or {}
        item_count = sum((s or {}).get("count", 0) for s in stats.values())
        error_count = len(row.get("error_log") or [])
        row["item_count"] = item_count
        row["error_count"] = error_count
        return row
