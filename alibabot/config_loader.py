from pathlib import Path
from typing import Any
import yaml
from pydantic import BaseModel, Field


class CollectionConfig(BaseModel):
    """Une collection à scraper chez un fournisseur."""
    handle: str | None = None  # Pour Shopify
    path: str | None = None    # Pour PrestaShop
    category: str
    subcategory: str | None = None


class SupplierConfig(BaseModel):
    name: str
    type: str  # "shopify" | "prestashop"
    base_url: str
    rate_limit_seconds: float = 1.0
    default_brand: str | None = None
    collections: list[CollectionConfig]


class AlibabotConfig(BaseModel):
    allowed_categories: list[str]
    suppliers: dict[str, SupplierConfig]


def load_config(path: Path | None = None) -> AlibabotConfig:
    """Charge la config YAML depuis le chemin spécifié, ou config/suppliers.yaml par défaut."""
    if path is None:
        path = Path(__file__).resolve().parent.parent / "config" / "suppliers.yaml"
    raw: dict[str, Any] = yaml.safe_load(path.read_text())
    return AlibabotConfig(**raw)
