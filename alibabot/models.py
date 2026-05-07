from datetime import datetime
from decimal import Decimal
from typing import Optional
from pydantic import BaseModel, Field, HttpUrl


class CatalogVariant(BaseModel):
    """Une variante d'un produit (taille, couleur, longueur…)."""
    variant_id: str
    title: str
    sku: Optional[str] = None
    price_eur: Optional[Decimal] = None
    available: bool = True
    options: dict[str, str] = Field(default_factory=dict)
    normalized_options: dict[str, str] = Field(default_factory=dict)


class CatalogItem(BaseModel):
    """Un produit du catalogue d'un fournisseur."""
    # Identification
    supplier: str = Field(..., description="Slug fournisseur: 'viral' | 'fcs' | 'surflounge' | 'deflow'")
    supplier_ref: str = Field(..., description="ID/handle unique chez le fournisseur")

    # Infos produit
    name: str
    brand: Optional[str] = None
    category: str = Field(..., description="fins | leashes | pads | covers | transport")
    subcategory: Optional[str] = None
    description: Optional[str] = None

    # Pricing
    price_eur: Optional[Decimal] = None
    price_min_eur: Optional[Decimal] = None
    price_max_eur: Optional[Decimal] = None
    currency: str = "EUR"

    # Stock
    in_stock: bool = True

    # Médias
    product_url: HttpUrl
    image_url: Optional[HttpUrl] = None

    # Variantes
    variants: list[CatalogVariant] = Field(default_factory=list)

    # Tags / attributs bruts
    tags: list[str] = Field(default_factory=list)
    raw: dict = Field(default_factory=dict)

    # Options inférées depuis le nom (utile pour Viral, qui n'a pas de variants structurés)
    inferred_options: dict[str, str] = Field(default_factory=dict)

    # Métadonnées scraping
    scraped_at: datetime = Field(default_factory=datetime.utcnow)


class ScrapeError(BaseModel):
    """Erreur non bloquante."""
    supplier: str
    category: Optional[str] = None
    url: Optional[str] = None
    error_type: str
    message: str


class ScrapeSnapshot(BaseModel):
    """Résultat d'un run de scraping complet."""
    snapshot_id: str
    started_at: datetime
    finished_at: datetime
    items: list[CatalogItem]
    errors: list[ScrapeError] = Field(default_factory=list)
    stats: dict[str, dict] = Field(default_factory=dict)
