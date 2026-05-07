"""Catalog service: query active snapshot items with filters and facets."""
from __future__ import annotations

from collections import Counter
from decimal import Decimal
from typing import Any

from alibabot.storage import SupabaseStorage


ALLOWED_SORTS = {
    "name": "name",
    "price": "price_eur",
    "brand": "brand",
    "in_stock": "in_stock",
    "recent": "scraped_at",
}


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
        color: str | None = None,
        size: str | None = None,
        sort: str = "name",
        direction: str = "asc",
        limit: int = 50,
        offset: int = 0,
    ) -> dict[str, Any]:
        snap_uuid = self.get_active_snapshot_uuid()
        if not snap_uuid:
            return {
                "items": [], "total": 0, "limit": limit, "offset": offset,
                "snapshot_id": None, "sort": sort, "direction": direction,
            }

        query = self.client.table("catalog_items").select("*", count="exact").eq("snapshot_id", snap_uuid)
        query = self._apply_filters(
            query, supplier, category, subcategory, brand, in_stock, q, min_price, max_price,
            color=color, size=size,
        )

        sort_col = ALLOWED_SORTS.get(sort, "name")
        desc = direction == "desc"
        query = query.order(sort_col, desc=desc).range(offset, offset + limit - 1)
        result = query.execute()

        return {
            "items": result.data or [],
            "total": result.count or 0,
            "limit": limit,
            "offset": offset,
            "snapshot_id": self.get_active_snapshot_label(),
            "sort": sort,
            "direction": direction,
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
        color: str | None = None,
        size: str | None = None,
    ) -> dict[str, Any]:
        """Compute facet counts. Loads all matching items (could be optimized later with SQL aggregation).

        Color/size filter values are accepted for API symmetry but intentionally
        NOT applied to the facet computation: we want users to switch between
        colors/sizes without the count for the currently-selected option
        collapsing to that selection.
        """
        snap_uuid = self.get_active_snapshot_uuid()
        if not snap_uuid:
            return {
                "suppliers": [], "brands": [], "categories": [], "subcategories": [],
                "colors": [], "sizes": [],
                "total": 0, "snapshot_id": None,
            }

        query = self.client.table("catalog_items").select(
            "supplier, brand, category, subcategory, inferred_options, variants"
        ).eq("snapshot_id", snap_uuid)
        query = self._apply_filters(
            query, supplier, category, subcategory, brand, in_stock, q, min_price, max_price,
        )

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

        colors: Counter = Counter()
        sizes: Counter = Counter()
        for row in all_rows:
            inf = row.get("inferred_options") or {}
            inf_color = inf.get("color")
            if inf_color:
                colors[inf_color] += 1
            else:
                for v in (row.get("variants") or []):
                    if not v.get("available"):
                        continue
                    v_color = (v.get("normalized_options") or {}).get("color")
                    if v_color:
                        colors[v_color] += 1
                        break

            inf_size = inf.get("size")
            if inf_size:
                sizes[inf_size] += 1
            else:
                for v in (row.get("variants") or []):
                    if not v.get("available"):
                        continue
                    v_size = (v.get("normalized_options") or {}).get("size")
                    if v_size:
                        sizes[v_size] += 1
                        break

        return {
            "suppliers": [{"value": k, "count": v} for k, v in suppliers.most_common()],
            "brands": [{"value": k, "count": v} for k, v in brands.most_common()],
            "categories": [{"value": k, "count": v} for k, v in categories.most_common()],
            "subcategories": [{"value": k, "count": v} for k, v in subcategories.most_common()],
            "colors": [{"value": k, "count": v} for k, v in colors.most_common(50)],
            "sizes": [{"value": k, "count": v} for k, v in sizes.most_common(50)],
            "total": len(all_rows),
            "snapshot_id": self.get_active_snapshot_label(),
        }

    @staticmethod
    def _apply_filters(
        query,
        supplier,
        category,
        subcategory,
        brand,
        in_stock,
        q,
        min_price,
        max_price,
        *,
        color: str | None = None,
        size: str | None = None,
    ):
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
        # Simple JSONB filter on inferred_options (covers Viral + Deflow item-level).
        # FCS / Surf Lounge items whose color/size live only in variants[].normalized_options
        # are not matched here; tracked in todo as Phase 3+ improvement.
        if color:
            query = query.eq("inferred_options->>color", color)
        if size:
            query = query.eq("inferred_options->>size", size)
        return query
