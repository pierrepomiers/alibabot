"""Response schemas for the Alibabot API."""
from __future__ import annotations

from datetime import datetime
from decimal import Decimal
from typing import Any
from pydantic import BaseModel, Field


# ─── Snapshots ─────────────────────────────────────────────────────

class SnapshotSummary(BaseModel):
    """Snapshot list item."""
    id: str
    snapshot_id: str
    status: str
    triggered_by: str
    created_at: datetime
    started_at: datetime
    finished_at: datetime
    activated_at: datetime | None = None
    activated_by: str | None = None
    notes: str | None = None
    item_count: int = 0
    error_count: int = 0
    stats: dict[str, Any] = Field(default_factory=dict)


class SnapshotDetail(SnapshotSummary):
    """Detailed snapshot with full error log."""
    error_log: list[dict[str, Any]] = Field(default_factory=list)


# ─── Diff ──────────────────────────────────────────────────────────

class DiffItem(BaseModel):
    supplier: str
    supplier_ref: str
    name: str
    brand: str | None = None
    category: str
    price_eur: Decimal | None = None
    in_stock: bool = True


class PriceChange(DiffItem):
    old_price: Decimal | None = None
    new_price: Decimal | None = None
    delta_pct: float | None = None


class StockChange(DiffItem):
    old_in_stock: bool
    new_in_stock: bool


class DiffSummary(BaseModel):
    added: int = 0
    removed: int = 0
    price_changed: int = 0
    stock_changed: int = 0


class SnapshotDiff(BaseModel):
    snapshot_id: str
    active_snapshot_id: str | None = None
    summary: DiffSummary
    added: list[DiffItem] = Field(default_factory=list)
    removed: list[DiffItem] = Field(default_factory=list)
    price_changed: list[PriceChange] = Field(default_factory=list)
    stock_changed: list[StockChange] = Field(default_factory=list)


# ─── Catalog ───────────────────────────────────────────────────────

class CatalogVariantOut(BaseModel):
    variant_id: str
    title: str
    sku: str | None = None
    price_eur: Decimal | None = None
    available: bool = True
    options: dict[str, str] = Field(default_factory=dict)


class CatalogItemOut(BaseModel):
    id: str
    supplier: str
    supplier_ref: str
    name: str
    brand: str | None = None
    category: str
    subcategory: str | None = None
    description: str | None = None
    price_eur: Decimal | None = None
    price_min_eur: Decimal | None = None
    price_max_eur: Decimal | None = None
    currency: str = "EUR"
    in_stock: bool = True
    product_url: str
    image_url: str | None = None
    variants: list[CatalogVariantOut] = Field(default_factory=list)
    tags: list[str] = Field(default_factory=list)


class CatalogPage(BaseModel):
    items: list[CatalogItemOut]
    total: int
    limit: int
    offset: int
    snapshot_id: str | None = None
    sort: str | None = None
    direction: str | None = None


class FacetCount(BaseModel):
    value: str
    count: int


class CatalogFacets(BaseModel):
    suppliers: list[FacetCount]
    brands: list[FacetCount]
    categories: list[FacetCount]
    subcategories: list[FacetCount]
    total: int
    snapshot_id: str | None = None
