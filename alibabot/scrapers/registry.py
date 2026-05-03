from alibabot.config_loader import SupplierConfig
from alibabot.scrapers.base import BaseScraper
from alibabot.scrapers.shopify import ShopifyScraper
from alibabot.scrapers.prestashop import PrestashopScraper


SCRAPER_TYPES: dict[str, type[BaseScraper]] = {
    "shopify": ShopifyScraper,
    "prestashop": PrestashopScraper,
}


def build_scraper(supplier_id: str, config: SupplierConfig, allowed_categories: set[str]) -> BaseScraper:
    cls = SCRAPER_TYPES.get(config.type)
    if cls is None:
        raise ValueError(f"Unknown scraper type '{config.type}' for supplier '{supplier_id}'")
    return cls(supplier_id=supplier_id, config=config, allowed_categories=allowed_categories)
