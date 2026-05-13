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


def _item_matches_color(item: dict, color: str) -> bool:
    """Returns True if the item has the requested color, either:
    - in inferred_options.color (Viral, Deflow item-level), OR
    - in at least one available variant's normalized_options.color (FCS, Surf Lounge, Deflow variants)
    """
    inferred = item.get("inferred_options") or {}
    if inferred.get("color") == color:
        return True
    for v in (item.get("variants") or []):
        if not v.get("available"):
            continue
        opts = v.get("normalized_options") or {}
        if opts.get("color") == color:
            return True
    return False


def _item_matches_size(item: dict, size: str) -> bool:
    """Same logic as _item_matches_color, for size."""
    inferred = item.get("inferred_options") or {}
    if inferred.get("size") == size:
        return True
    for v in (item.get("variants") or []):
        if not v.get("available"):
            continue
        opts = v.get("normalized_options") or {}
        if opts.get("size") == size:
            return True
    return False


def _item_matches_fin_system(item: dict, fin_system: str) -> bool:
    """Returns True if the item's inferred_options.fin_system matches."""
    inferred = item.get("inferred_options") or {}
    return inferred.get("fin_system") == fin_system


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
        fin_system: str | None = None,
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
        )

        sort_col = ALLOWED_SORTS.get(sort, "name")
        desc = direction == "desc"
        query = query.order(sort_col, desc=desc)

        needs_variant_filter = (color is not None) or (size is not None) or (fin_system is not None)

        if needs_variant_filter:
            all_items: list[dict] = []
            cur_offset = 0
            BATCH = 1000
            while True:
                page = query.range(cur_offset, cur_offset + BATCH - 1).execute().data or []
                all_items.extend(page)
                if len(page) < BATCH:
                    break
                cur_offset += BATCH

            filtered = []
            for item in all_items:
                if color and not _item_matches_color(item, color):
                    continue
                if size and not _item_matches_size(item, size):
                    continue
                if fin_system and not _item_matches_fin_system(item, fin_system):
                    continue
                filtered.append(item)

            total = len(filtered)
            page_items = filtered[offset:offset + limit]

            return {
                "items": page_items,
                "total": total,
                "limit": limit,
                "offset": offset,
                "snapshot_id": self.get_active_snapshot_label(),
                "sort": sort,
                "direction": direction,
            }

        query = query.range(offset, offset + limit - 1)
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
        fin_system: str | None = None,
    ) -> dict[str, Any]:
        """Compute facet counts. Loads all matching items (could be optimized later with SQL aggregation).

        Color/size/fin_system filter values are accepted for API symmetry but
        intentionally NOT applied to the facet computation: we want users to
        switch between values without the count for the currently-selected
        option collapsing to that selection.
        """
        snap_uuid = self.get_active_snapshot_uuid()
        if not snap_uuid:
            return {
                "suppliers": [], "brands": [], "categories": [], "subcategories": [],
                "colors": [], "sizes": [], "fin_systems": [],
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
        fin_systems: Counter = Counter()
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

            inf_fin_system = inf.get("fin_system")
            if inf_fin_system:
                fin_systems[inf_fin_system] += 1

        return {
            "suppliers": [{"value": k, "count": v} for k, v in suppliers.most_common()],
            "brands": [{"value": k, "count": v} for k, v in brands.most_common()],
            "categories": [{"value": k, "count": v} for k, v in categories.most_common()],
            "subcategories": [{"value": k, "count": v} for k, v in subcategories.most_common()],
            "colors": [{"value": k, "count": v} for k, v in colors.most_common(50)],
            "sizes": [{"value": k, "count": v} for k, v in sizes.most_common(50)],
            "fin_systems": [{"value": k, "count": v} for k, v in fin_systems.most_common(20)],
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
        return query
