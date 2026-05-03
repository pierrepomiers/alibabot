"""Supabase storage client for alibabot snapshots."""
from __future__ import annotations

import os
from datetime import datetime, timezone
from typing import Any
from supabase import Client, create_client

from alibabot.models import ScrapeSnapshot, CatalogItem


class SupabaseStorage:
    """Client wrapper for Supabase. Uses service_role key (bypass RLS)."""

    def __init__(self, url: str | None = None, key: str | None = None):
        url = url or os.environ.get("SUPABASE_URL")
        key = key or os.environ.get("SUPABASE_SERVICE_ROLE_KEY")
        if not url or not key:
            raise RuntimeError(
                "Missing Supabase credentials. Set SUPABASE_URL and SUPABASE_SERVICE_ROLE_KEY env vars."
            )
        self.client: Client = create_client(url, key)

    # ─── Snapshots ──────────────────────────────────────────────────

    def save_snapshot(
        self,
        snapshot: ScrapeSnapshot,
        triggered_by: str = "cron",
    ) -> str:
        """Save a snapshot and all its items. Returns the inserted snapshot UUID.

        The snapshot is created with status='pending' by default.
        """
        snap_row = {
            "snapshot_id": snapshot.snapshot_id,
            "started_at": snapshot.started_at.replace(tzinfo=timezone.utc).isoformat(),
            "finished_at": snapshot.finished_at.replace(tzinfo=timezone.utc).isoformat(),
            "status": "pending",
            "triggered_by": triggered_by,
            "stats": snapshot.stats,
            "error_log": [e.model_dump() for e in snapshot.errors],
        }
        result = self.client.table("catalog_snapshots").insert(snap_row).execute()
        if not result.data:
            raise RuntimeError(f"Failed to insert snapshot: {result}")
        snapshot_uuid = result.data[0]["id"]

        items_payload = [self._item_to_row(item, snapshot_uuid) for item in snapshot.items]
        BATCH_SIZE = 500
        for i in range(0, len(items_payload), BATCH_SIZE):
            batch = items_payload[i : i + BATCH_SIZE]
            self.client.table("catalog_items").insert(batch).execute()

        return snapshot_uuid

    def list_snapshots(self, status: str | None = None, limit: int = 20) -> list[dict[str, Any]]:
        """List snapshots, most recent first."""
        q = self.client.table("catalog_snapshots").select("*").order("created_at", desc=True).limit(limit)
        if status:
            q = q.eq("status", status)
        return q.execute().data or []

    def purge_old(self) -> dict[str, int]:
        """Run the SQL purge function. Returns counts deleted by status."""
        result = self.client.rpc("purge_old_snapshots").execute()
        out: dict[str, int] = {}
        for row in result.data or []:
            out[row["deleted_status"]] = row["deleted_count"]
        return out

    # ─── Helpers ────────────────────────────────────────────────────

    @staticmethod
    def _item_to_row(item: CatalogItem, snapshot_uuid: str) -> dict[str, Any]:
        d = item.model_dump(mode="json")
        d["snapshot_id"] = snapshot_uuid
        return d
