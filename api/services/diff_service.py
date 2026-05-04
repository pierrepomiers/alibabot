"""Diff service: compare two snapshots."""
from __future__ import annotations

from decimal import Decimal
from typing import Any

from alibabot.storage import SupabaseStorage


class DiffService:
    def __init__(self, storage: SupabaseStorage | None = None):
        self.storage = storage or SupabaseStorage()
        self.client = self.storage.client

    def diff(self, target_uuid: str, base_uuid: str | None) -> dict[str, Any]:
        """Compute added/removed/price_changed/stock_changed between target and base.

        If base is None (no active snapshot yet), all items are 'added' and others empty.
        """
        target_items = self._load_items(target_uuid)
        base_items = self._load_items(base_uuid) if base_uuid else {}

        added = []
        removed = []
        price_changed = []
        stock_changed = []

        target_keys = set(target_items.keys())
        base_keys = set(base_items.keys())

        for key in target_keys - base_keys:
            added.append(self._to_diff_item(target_items[key]))

        for key in base_keys - target_keys:
            removed.append(self._to_diff_item(base_items[key]))

        for key in target_keys & base_keys:
            t = target_items[key]
            b = base_items[key]

            t_price = _to_decimal(t.get("price_eur"))
            b_price = _to_decimal(b.get("price_eur"))
            if t_price != b_price:
                delta_pct = None
                if b_price and b_price > 0 and t_price is not None:
                    delta_pct = float((t_price - b_price) / b_price * 100)
                pc = self._to_diff_item(t)
                pc["old_price"] = b_price
                pc["new_price"] = t_price
                pc["delta_pct"] = delta_pct
                price_changed.append(pc)

            if bool(t.get("in_stock")) != bool(b.get("in_stock")):
                sc = self._to_diff_item(t)
                sc["old_in_stock"] = bool(b.get("in_stock"))
                sc["new_in_stock"] = bool(t.get("in_stock"))
                stock_changed.append(sc)

        return {
            "summary": {
                "added": len(added),
                "removed": len(removed),
                "price_changed": len(price_changed),
                "stock_changed": len(stock_changed),
            },
            "added": added,
            "removed": removed,
            "price_changed": price_changed,
            "stock_changed": stock_changed,
        }

    def _load_items(self, snapshot_uuid: str) -> dict[tuple[str, str], dict[str, Any]]:
        """Returns dict keyed by (supplier, supplier_ref)."""
        out: dict[tuple[str, str], dict[str, Any]] = {}
        offset = 0
        BATCH = 1000
        while True:
            result = (
                self.client.table("catalog_items")
                .select("supplier, supplier_ref, name, brand, category, price_eur, in_stock")
                .eq("snapshot_id", snapshot_uuid)
                .range(offset, offset + BATCH - 1)
                .execute()
            )
            rows = result.data or []
            for row in rows:
                out[(row["supplier"], row["supplier_ref"])] = row
            if len(rows) < BATCH:
                break
            offset += BATCH
        return out

    @staticmethod
    def _to_diff_item(row: dict[str, Any]) -> dict[str, Any]:
        return {
            "supplier": row["supplier"],
            "supplier_ref": row["supplier_ref"],
            "name": row["name"],
            "brand": row.get("brand"),
            "category": row["category"],
            "price_eur": _to_decimal(row.get("price_eur")),
            "in_stock": bool(row.get("in_stock", True)),
        }


def _to_decimal(v: Any) -> Decimal | None:
    if v is None:
        return None
    try:
        return Decimal(str(v))
    except Exception:
        return None
