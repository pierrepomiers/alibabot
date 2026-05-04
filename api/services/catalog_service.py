"""Catalog service: query active snapshot items with filters and facets."""
from __future__ import annotations

from collections import Counter
from decimal import Decimal
from typing import Any

from alibabot.storage import SupabaseStorage


class CatalogService:
    def __init__(self, storage: SupabaseStorage | None = None):
        self.storage = storage or SupabaseStorage()
        self.client = self.storage.client

    def get_active_snapshot_uuid(self) -> str | None:
        result = (
            self.client.table("catalog_snapshots")
            .select("id, snapshot_id")
            .eq("status", "active")
            .order("activated_at", desc=True)
            .limit(1)
            .execute()
        )
        rows = result.data or []
        if not rows:
            return None
        return rows[0]["id"]

    def get_active_snapshot_label(self) -> str | None:
        result = (
            self.client.table("catalog_snapshots")
            .select("snapshot_id")
            .eq("status", "active")
            .order("activated_at", desc=True)
            .limit(1)
            .execute()
        )
        rows = result.data or []
        return rows[0]["snapshot_id"] if rows else None

    def list_items(
        self,
        *,
        supplier: str | None = None,
        category: str | None = None,
        subcategory: str | None = None,
        brand: str | None = None,
        in_stock: bool | None = None,
        q: str | None = None,
        min_price: Decimal | None = None,
        max_price: Decimal | None = None,
        limit: int = 50,
        offset: int = 0,
    ) -> dict[str, Any]:
        snap_uuid = self.get_active_snapshot_uuid()
        if not snap_uuid:
            return {"items": [], "total": 0, "limit": limit, "offset": offset, "snapshot_id": None}

        query = self.client.table("catalog_items").select("*", count="exact").eq("snapshot_id", snap_uuid)
        query = self._apply_filters(query, supplier, category, subcategory, brand, in_stock, q, min_price, max_price)
        query = query.order("name", desc=False).range(offset, offset + limit - 1)
        result = query.execute()

        return {
            "items": result.data or [],
            "total": result.count or 0,
            "limit": limit,
            "offset": offset,
            "snapshot_id": self.get_active_snapshot_label(),
        }

    def get_facets(
        self,
        *,
        supplier: str | None = None,
        category: str | None = None,
        subcategory: str | None = None,
        brand: str | None = None,
        in_stock: bool | None = None,
        q: str | None = None,
        min_price: Decimal | None = None,
        max_price: Decimal | None = None,
    ) -> dict[str, Any]:
        """Compute facet counts. Loads all matching items (could be optimized later with SQL aggregation)."""
        snap_uuid = self.get_active_snapshot_uuid()
        if not snap_uuid:
            return {
                "suppliers": [], "brands": [], "categories": [], "subcategories": [],
                "total": 0, "snapshot_id": None,
            }

        query = self.client.table("catalog_items").select(
            "supplier, brand, category, subcategory"
        ).eq("snapshot_id", snap_uuid)
        query = self._apply_filters(query, supplier, category, subcategory, brand, in_stock, q, min_price, max_price)

        all_rows: list[dict[str, Any]] = []
        offset = 0
        BATCH = 1000
        while True:
            page = query.range(offset, offset + BATCH - 1).execute().data or []
            all_rows.extend(page)
            if len(page) < BATCH:
                break
            offset += BATCH

        suppliers = Counter(r.get("supplier") for r in all_rows if r.get("supplier"))
        brands = Counter(r.get("brand") for r in all_rows if r.get("brand"))
        categories = Counter(r.get("category") for r in all_rows if r.get("category"))
        subcategories = Counter(r.get("subcategory") for r in all_rows if r.get("subcategory"))

        return {
            "suppliers": [{"value": k, "count": v} for k, v in suppliers.most_common()],
            "brands": [{"value": k, "count": v} for k, v in brands.most_common()],
            "categories": [{"value": k, "count": v} for k, v in categories.most_common()],
            "subcategories": [{"value": k, "count": v} for k, v in subcategories.most_common()],
            "total": len(all_rows),
            "snapshot_id": self.get_active_snapshot_label(),
        }

    @staticmethod
    def _apply_filters(query, supplier, category, subcategory, brand, in_stock, q, min_price, max_price):
        if supplier:
            query = query.eq("supplier", supplier)
        if category:
            query = query.eq("category", category)
        if subcategory:
            query = query.eq("subcategory", subcategory)
        if brand:
            query = query.eq("brand", brand)
        if in_stock is not None:
            query = query.eq("in_stock", in_stock)
        if q:
            query = query.ilike("name", f"%{q}%")
        if min_price is not None:
            query = query.gte("price_eur", float(min_price))
        if max_price is not None:
            query = query.lte("price_eur", float(max_price))
        return query
