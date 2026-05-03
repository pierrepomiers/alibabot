import asyncio
import json
from datetime import datetime
from pathlib import Path
import httpx
from alibabot.config_loader import load_config, AlibabotConfig
from alibabot.models import ScrapeSnapshot
from alibabot.scrapers.base import BaseScraper
from alibabot.scrapers.registry import build_scraper


def build_all_scrapers(config: AlibabotConfig) -> list[BaseScraper]:
    allowed = set(config.allowed_categories)
    return [build_scraper(sid, scfg, allowed) for sid, scfg in config.suppliers.items()]


def build_scraper_for(config: AlibabotConfig, supplier_id: str) -> BaseScraper:
    if supplier_id not in config.suppliers:
        raise ValueError(f"Unknown supplier: {supplier_id}. Known: {list(config.suppliers.keys())}")
    allowed = set(config.allowed_categories)
    return build_scraper(supplier_id, config.suppliers[supplier_id], allowed)


async def run_scrapers(scrapers: list[BaseScraper]) -> ScrapeSnapshot:
    started = datetime.utcnow()
    snapshot_id = started.strftime("%Y-%m-%dT%H-%M-%S")

    all_items = []
    all_errors = []
    stats = {}

    async with httpx.AsyncClient() as client:
        for scraper in scrapers:
            t0 = datetime.utcnow()
            try:
                items = await scraper.scrape(client)
            except Exception as e:
                items = []
                scraper._add_error(f"Fatal scraper error: {e}", error_type="fatal")
            t1 = datetime.utcnow()

            all_items.extend(items)
            all_errors.extend(scraper.errors)
            stats[scraper.supplier_id] = {
                "supplier_name": scraper.config.name,
                "count": len(items),
                "rejected": scraper.rejected_count,
                "errors": len(scraper.errors),
                "duration_s": round((t1 - t0).total_seconds(), 1),
            }

    return ScrapeSnapshot(
        snapshot_id=snapshot_id,
        started_at=started,
        finished_at=datetime.utcnow(),
        items=all_items,
        errors=all_errors,
        stats=stats,
    )


def save_snapshot(snapshot: ScrapeSnapshot, output_dir: Path) -> Path:
    output_dir.mkdir(parents=True, exist_ok=True)
    path = output_dir / f"{snapshot.snapshot_id}.json"
    path.write_text(snapshot.model_dump_json(indent=2))
    return path
