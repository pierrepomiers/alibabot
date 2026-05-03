from abc import ABC, abstractmethod
from datetime import datetime
import httpx
from alibabot.config_loader import SupplierConfig
from alibabot.models import CatalogItem, ScrapeError


class BaseScraper(ABC):
    """Base class for all scrapers.

    Enforces category whitelist : items whose category is not in `allowed_categories`
    are rejected (not added to results) and an error is logged for audit.
    """

    def __init__(self, supplier_id: str, config: SupplierConfig, allowed_categories: set[str]):
        self.supplier_id = supplier_id
        self.config = config
        self.allowed_categories = allowed_categories
        self.errors: list[ScrapeError] = []
        self.started_at: datetime | None = None
        self.finished_at: datetime | None = None
        self.rejected_count: int = 0

    @abstractmethod
    async def scrape(self, client: httpx.AsyncClient) -> list[CatalogItem]:
        """Scrape l'intégralité du catalogue. Les erreurs non bloquantes vont dans self.errors."""
        ...

    def _add_error(
        self,
        message: str,
        *,
        category: str | None = None,
        url: str | None = None,
        error_type: str = "scrape_error",
    ):
        self.errors.append(ScrapeError(
            supplier=self.supplier_id,
            category=category,
            url=url,
            error_type=error_type,
            message=message,
        ))

    def _validate_item(self, item: CatalogItem) -> bool:
        """Vérifie que l'item respecte la whitelist de catégories.

        Returns True if valid (keep), False if rejected (drop).
        """
        if item.category not in self.allowed_categories:
            self.rejected_count += 1
            self._add_error(
                f"Item rejected (category '{item.category}' not in allowed list): {item.name}",
                category=item.category,
                url=str(item.product_url),
                error_type="category_rejected",
            )
            return False
        return True
