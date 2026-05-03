"""Nightly scrape script — pushes snapshot to Supabase.

Triggered by GitHub Actions on a monthly schedule, or manually via workflow_dispatch.
"""
from __future__ import annotations

import asyncio
import sys
from datetime import datetime

from rich.console import Console
from rich.table import Table

from alibabot.config_loader import load_config
from alibabot.runner import build_all_scrapers, run_scrapers
from alibabot.storage import SupabaseStorage

console = Console()


async def main(triggered_by: str = "cron") -> int:
    console.print(f"[bold cyan]🛒 Alibabot nightly scrape[/] — triggered_by={triggered_by}")
    console.print(f"[dim]Started at {datetime.utcnow().isoformat()} UTC[/]\n")

    # 1. Scrape
    config = load_config()
    scrapers = build_all_scrapers(config)
    snapshot = await run_scrapers(scrapers)

    console.print(f"\n📦 Scrape complete: {len(snapshot.items)} items, {len(snapshot.errors)} errors")
    _print_stats(snapshot)

    # 2. Push to Supabase
    console.print(f"\n[bold cyan]📤 Pushing to Supabase...[/]")
    storage = SupabaseStorage()
    snap_uuid = storage.save_snapshot(snapshot, triggered_by=triggered_by)
    console.print(f"✅ Snapshot saved: id={snap_uuid}, status=pending")

    # 3. Purge old
    console.print(f"\n[bold cyan]🧹 Purging old snapshots...[/]")
    purged = storage.purge_old()
    if purged:
        for status, count in purged.items():
            console.print(f"   - {status}: {count} deleted")
    else:
        console.print(f"   - nothing to purge")

    console.print(f"\n[bold green]✅ Done.[/]")
    return 0


def _print_stats(snapshot):
    table = Table(title=f"Snapshot {snapshot.snapshot_id}")
    table.add_column("Fournisseur", style="cyan")
    table.add_column("Items", justify="right", style="green")
    table.add_column("Rejetés", justify="right", style="yellow")
    table.add_column("Erreurs", justify="right", style="red")
    table.add_column("Durée (s)", justify="right")
    for sup_id, s in snapshot.stats.items():
        table.add_row(
            s["supplier_name"],
            str(s["count"]),
            str(s.get("rejected", 0)),
            str(s["errors"]),
            f"{s['duration_s']:.1f}",
        )
    console.print(table)


if __name__ == "__main__":
    triggered_by = sys.argv[1] if len(sys.argv) > 1 else "cron"
    exit_code = asyncio.run(main(triggered_by=triggered_by))
    sys.exit(exit_code)
