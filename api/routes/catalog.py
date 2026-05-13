"""Catalog routes — query the active snapshot."""
from __future__ import annotations

from decimal import Decimal
from fastapi import APIRouter, Depends, Query

from api.auth import require_api_secret
from api.schemas import CatalogPage, CatalogFacets
from api.services.catalog_service import CatalogService

router = APIRouter(dependencies=[Depends(require_api_secret)])


@router.get("/active", response_model=CatalogPage)
async def list_active_items(
    supplier: str | None = Query(default=None),
    category: str | None = Query(default=None),
    subcategory: str | None = Query(default=None),
    brand: str | None = Query(default=None),
    in_stock: bool | None = Query(default=None),
    q: str | None = Query(default=None, description="Recherche texte sur le nom"),
    min_price: Decimal | None = Query(default=None, ge=0),
    max_price: Decimal | None = Query(default=None, ge=0),
    color: str | None = Query(default=None),
    size: str | None = Query(default=None),
    fin_system: str | None = Query(default=None, description="Système de dérive (Thruster, Quad, Twin, ...)"),
    sort: str = Query(default="name", regex="^(name|price|brand|in_stock|recent)$"),
    direction: str = Query(default="asc", regex="^(asc|desc)$"),
    limit: int = Query(default=50, ge=1, le=500),
    offset: int = Query(default=0, ge=0),
):
    svc = CatalogService()
    return svc.list_items(
        supplier=supplier,
        category=category,
        subcategory=subcategory,
        brand=brand,
        in_stock=in_stock,
        q=q,
        min_price=min_price,
        max_price=max_price,
        color=color,
        size=size,
        fin_system=fin_system,
        sort=sort,
        direction=direction,
        limit=limit,
        offset=offset,
    )


@router.get("/active/facets", response_model=CatalogFacets)
async def get_facets(
    supplier: str | None = Query(default=None),
    category: str | None = Query(default=None),
    subcategory: str | None = Query(default=None),
    brand: str | None = Query(default=None),
    in_stock: bool | None = Query(default=None),
    q: str | None = Query(default=None),
    min_price: Decimal | None = Query(default=None, ge=0),
    max_price: Decimal | None = Query(default=None, ge=0),
    color: str | None = Query(default=None),
    size: str | None = Query(default=None),
    fin_system: str | None = Query(default=None, description="Système de dérive (Thruster, Quad, Twin, ...)"),
):
    svc = CatalogService()
    return svc.get_facets(
        supplier=supplier,
        category=category,
        subcategory=subcategory,
        brand=brand,
        in_stock=in_stock,
        q=q,
        min_price=min_price,
        max_price=max_price,
        color=color,
        size=size,
        fin_system=fin_system,
    )
