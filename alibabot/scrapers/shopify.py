import httpx
from decimal import Decimal
from datetime import datetime
from alibabot.models import CatalogItem, CatalogVariant
from alibabot.normalizers.core import normalize_options, extract_from_name
from alibabot.scrapers.base import BaseScraper
from alibabot.utils.http import fetch


class ShopifyScraper(BaseScraper):
    """Scraper générique Shopify via /collections/<handle>/products.json (public, paginated)."""

    async def scrape(self, client: httpx.AsyncClient) -> list[CatalogItem]:
        self.started_at = datetime.utcnow()
        items: list[CatalogItem] = []
        seen_refs: set[str] = set()

        for col in self.config.collections:
            handle = col.handle
            if not handle:
                self._add_error(
                    f"Missing 'handle' for shopify collection (category={col.category})",
                    error_type="config_error",
                )
                continue

            page = 1
            while True:
                url = f"{self.config.base_url}/collections/{handle}/products.json?limit=250&page={page}"
                try:
                    response = await fetch(client, url, rate_limit_seconds=self.config.rate_limit_seconds)
                    data = response.json()
                except Exception as e:
                    self._add_error(f"Fetch failed: {e}", category=handle, url=url, error_type="fetch_error")
                    break

                products = data.get("products", [])
                if not products:
                    break

                for p in products:
                    ref = str(p.get("id"))
                    if ref in seen_refs:
                        continue
                    seen_refs.add(ref)
                    try:
                        item = self._parse_product(p, category=col.category, subcategory=col.subcategory)
                        if self._validate_item(item):
                            items.append(item)
                    except Exception as e:
                        self._add_error(f"Parse failed for product {ref}: {e}", category=handle, error_type="parse_error")

                if len(products) < 250:
                    break
                page += 1

        self.finished_at = datetime.utcnow()
        return items

    def _parse_product(self, p: dict, *, category: str, subcategory: str | None) -> CatalogItem:
        handle = p["handle"]
        product_url = f"{self.config.base_url}/products/{handle}"

        variants_data = p.get("variants", [])
        variants: list[CatalogVariant] = []
        prices: list[Decimal] = []
        any_available = False

        for v in variants_data:
            price = Decimal(str(v["price"])) if v.get("price") else None
            if price is not None:
                prices.append(price)
            available = bool(v.get("available", False))
            if available:
                any_available = True

            option_names = [opt["name"] for opt in p.get("options", [])]
            option_values = [v.get(f"option{i+1}") for i in range(len(option_names))]
            options = {n: val for n, val in zip(option_names, option_values) if val}

            variants.append(CatalogVariant(
                variant_id=str(v["id"]),
                title=v.get("title", ""),
                sku=v.get("sku") or None,
                price_eur=price,
                available=available,
                options=options,
                normalized_options=normalize_options(self.supplier_id, options),
            ))

        image_url = None
        images = p.get("images", [])
        if images:
            image_url = images[0].get("src")

        brand = p.get("vendor") or self.config.default_brand

        tags_raw = p.get("tags", [])
        tags = tags_raw if isinstance(tags_raw, list) else [t.strip() for t in (tags_raw or "").split(",") if t.strip()]

        title = p.get("title", "")
        inferred = extract_from_name(self.supplier_id, title)

        return CatalogItem(
            supplier=self.supplier_id,
            supplier_ref=str(p["id"]),
            name=title,
            brand=brand,
            category=category,
            subcategory=subcategory,
            description=(p.get("body_html") or "")[:500] or None,
            price_eur=min(prices) if prices else None,
            price_min_eur=min(prices) if prices else None,
            price_max_eur=max(prices) if prices else None,
            in_stock=any_available,
            product_url=product_url,
            image_url=image_url,
            variants=variants,
            tags=tags,
            inferred_options=inferred,
            raw={"handle": handle, "id": p["id"]},
        )
