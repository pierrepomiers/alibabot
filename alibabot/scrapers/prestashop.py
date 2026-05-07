import re
from datetime import datetime
from decimal import Decimal
from urllib.parse import urljoin
import httpx
from selectolax.parser import HTMLParser
from alibabot.models import CatalogItem
from alibabot.normalizers.core import extract_from_name
from alibabot.scrapers.base import BaseScraper
from alibabot.utils.http import fetch


VIRAL_KNOWN_BRANDS = [
    "CAPTAIN FIN CO",
    "VIRAL SURF",
    "ASTRODECK",
    "FUTURES",
    "JUST",
    "FCS",
    "OAM",
]


def extract_brand_from_name(name: str) -> str | None:
    """Extract a known brand from a product name (case-insensitive, word-boundary match).

    Strategies (in order, first match wins):
    1. Text after the last comma matches a known brand exactly (case-insensitive)
       e.g. "..., FUTURES." → "FUTURES"
    2. Known brand appears as a whole word anywhere in the name (case-insensitive)
       e.g. "Dérive longboard - Futures Performance 7..." → "FUTURES"

    Returns the brand normalized in UPPERCASE, or None if no known brand is found.
    """
    if not name:
        return None

    if "," in name:
        tail = name.rsplit(",", 1)[1].strip().rstrip(".").strip()
        tail_upper = tail.upper()
        for brand in VIRAL_KNOWN_BRANDS:
            if tail_upper == brand:
                return brand

    name_upper = name.upper()
    for brand in VIRAL_KNOWN_BRANDS:
        pattern = r"(?:^|[^A-Z0-9])" + re.escape(brand) + r"(?:[^A-Z0-9]|$)"
        if re.search(pattern, name_upper):
            return brand

    return None


class PrestashopScraper(BaseScraper):
    """Scraper PrestaShop pour Viral Surf — parse HTML."""

    async def scrape(self, client: httpx.AsyncClient) -> list[CatalogItem]:
        self.started_at = datetime.utcnow()
        items: list[CatalogItem] = []
        seen_refs: set[str] = set()

        for col in self.config.collections:
            path = col.path
            if not path:
                self._add_error(
                    f"Missing 'path' for prestashop collection (category={col.category})",
                    error_type="config_error",
                )
                continue

            page = 1
            while True:
                url = f"{self.config.base_url}{path}?page={page}" if page > 1 else f"{self.config.base_url}{path}"
                try:
                    response = await fetch(client, url, rate_limit_seconds=self.config.rate_limit_seconds)
                    html = response.text
                except Exception as e:
                    self._add_error(f"Fetch failed: {e}", category=path, url=url, error_type="fetch_error")
                    break

                tree = HTMLParser(html)
                products = tree.css("article.product-miniature") or tree.css(".product-miniature, .js-product-miniature")
                if not products:
                    break

                page_items_count = 0
                for prod_node in products:
                    try:
                        item = self._parse_product(prod_node, category=col.category, subcategory=col.subcategory)
                        if item is None:
                            continue
                        if item.supplier_ref in seen_refs:
                            continue
                        if self._validate_item(item):
                            seen_refs.add(item.supplier_ref)
                            items.append(item)
                            page_items_count += 1
                    except Exception as e:
                        self._add_error(f"Parse failed: {e}", category=path, error_type="parse_error")

                next_link = tree.css_first("a.next, a[rel='next']")
                if page_items_count == 0 or not next_link:
                    break
                page += 1
                if page > 20:  # safety
                    break

        self.finished_at = datetime.utcnow()
        return items

    def _parse_product(self, node, *, category: str, subcategory: str | None) -> CatalogItem | None:
        link_node = (
            node.css_first("a.product-thumbnail")
            or node.css_first("h2.product-title a")
            or node.css_first(".product-title a")
            or node.css_first("h3 a")
            or node.css_first("a")
        )
        if not link_node:
            return None
        product_url = link_node.attributes.get("href", "")
        if product_url and not product_url.startswith("http"):
            product_url = urljoin(self.config.base_url, product_url)

        name_node = node.css_first("h2.product-title") or node.css_first("h3.product-title") or node.css_first(".product-title")
        name = name_node.text(strip=True) if name_node else link_node.text(strip=True)

        m = re.search(r"/(\d+)-", product_url)
        if not m:
            return None
        supplier_ref = m.group(1)

        price_node = node.css_first("span.price") or node.css_first(".product-price-and-shipping .price") or node.css_first(".price")
        price_eur = None
        if price_node:
            price_text = price_node.text(strip=True).replace("\xa0", " ")
            price_match = re.search(r"([\d\s]+[,.]?\d*)", price_text)
            if price_match:
                price_str = price_match.group(1).replace(" ", "").replace(",", ".")
                try:
                    price_eur = Decimal(price_str)
                except Exception:
                    pass

        img_node = node.css_first("img.product-thumbnail") or node.css_first("img")
        image_url = None
        if img_node:
            image_url = img_node.attributes.get("data-src") or img_node.attributes.get("src")

        in_stock = True
        out_of_stock_node = node.css_first(".product-flag.out_of_stock, .product-availability")
        if out_of_stock_node and "rupture" in out_of_stock_node.text(strip=True).lower():
            in_stock = False

        detected_brand = extract_brand_from_name(name) or self.config.default_brand

        inferred = extract_from_name(self.supplier_id, name)

        return CatalogItem(
            supplier=self.supplier_id,
            supplier_ref=supplier_ref,
            name=name,
            brand=detected_brand,
            category=category,
            subcategory=subcategory,
            price_eur=price_eur,
            price_min_eur=price_eur,
            price_max_eur=price_eur,
            in_stock=in_stock,
            product_url=product_url,
            image_url=image_url,
            inferred_options=inferred,
            raw={"path": product_url},
        )
