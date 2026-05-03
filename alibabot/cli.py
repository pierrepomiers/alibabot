import asyncio
from pathlib import Path
import typer
from rich.console import Console
from rich.table import Table
from alibabot.config_loader import load_config
from alibabot.runner import build_all_scrapers, build_scraper_for, run_scrapers, save_snapshot

app = typer.Typer(help="Alibabot — Catalogue multi-fournisseurs NOTOX")
console = Console()


@app.command()
def scrape(
    output_dir: Path = typer.Option(Path("snapshots"), "--out", "-o", help="Dossier de sortie des snapshots"),
):
    """Scrape tous les fournisseurs et produit un snapshot JSON."""
    config = load_config()
    scrapers = build_all_scrapers(config)
    console.print(f"[bold cyan]🛒 Alibabot[/] — scraping {len(scrapers)} fournisseur(s)...")
    snapshot = asyncio.run(run_scrapers(scrapers))
    path = save_snapshot(snapshot, output_dir)
    _print_summary(snapshot, path)


@app.command("scrape-one")
def scrape_one(
    supplier: str = typer.Argument(..., help="Slug fournisseur: viral | fcs | surflounge | deflow"),
    output_dir: Path = typer.Option(Path("snapshots"), "--out", "-o"),
):
    """Scrape un seul fournisseur (debug)."""
    config = load_config()
    scraper = build_scraper_for(config, supplier)
    console.print(f"[bold cyan]🛒 Alibabot[/] — scraping [yellow]{scraper.config.name}[/]...")
    snapshot = asyncio.run(run_scrapers([scraper]))
    path = save_snapshot(snapshot, output_dir)
    _print_summary(snapshot, path)


@app.command("list-suppliers")
def list_suppliers():
    """Liste les fournisseurs configurés."""
    config = load_config()
    table = Table(title="Fournisseurs Alibabot")
    table.add_column("Slug", style="cyan")
    table.add_column("Nom", style="green")
    table.add_column("Type")
    table.add_column("Collections", justify="right")
    for sid, scfg in config.suppliers.items():
        table.add_row(sid, scfg.name, scfg.type, str(len(scfg.collections)))
    console.print(table)
    console.print(f"\nCatégories autorisées : [cyan]{', '.join(config.allowed_categories)}[/]")


def _print_summary(snapshot, path: Path):
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
            str(s["rejected"]),
            str(s["errors"]),
            f"{s['duration_s']:.1f}",
        )

    console.print(table)
    console.print(f"\n💾 Snapshot écrit dans: [bold]{path}[/]")
    console.print(
        f"📦 Total : [bold green]{len(snapshot.items)}[/] items kept, "
        f"[yellow]{sum(s.get('rejected', 0) for s in snapshot.stats.values())}[/] rejected, "
        f"[red]{len(snapshot.errors)}[/] errors"
    )

    if snapshot.errors:
        console.print("\n[bold red]Premières erreurs (max 10) :[/]")
        for err in snapshot.errors[:10]:
            console.print(f"  - [{err.supplier}] {err.error_type}: {err.message}")
        if len(snapshot.errors) > 10:
            console.print(f"  ... et {len(snapshot.errors) - 10} autres (voir snapshot JSON)")


@app.command("push-snapshot")
def push_snapshot(
    file: Path = typer.Argument(..., help="Chemin vers un snapshot JSON local"),
    triggered_by: str = typer.Option("cli_push", "--source", help="cli_push | manual | cron"),
):
    """Pousse un snapshot JSON local vers Supabase (status=pending)."""
    import json
    from alibabot.models import ScrapeSnapshot
    from alibabot.storage import SupabaseStorage

    if not file.exists():
        console.print(f"[red]File not found: {file}[/]")
        raise typer.Exit(1)

    console.print(f"[cyan]📂 Loading snapshot from {file}...[/]")
    data = json.loads(file.read_text())
    snapshot = ScrapeSnapshot(**data)
    console.print(f"   {len(snapshot.items)} items, {len(snapshot.errors)} errors")

    console.print(f"[cyan]📤 Pushing to Supabase (triggered_by={triggered_by})...[/]")
    storage = SupabaseStorage()
    snap_uuid = storage.save_snapshot(snapshot, triggered_by=triggered_by)
    console.print(f"[green]✅ Saved: id={snap_uuid}, status=pending[/]")


@app.command("list-snapshots")
def list_snapshots(
    status: str = typer.Option(None, "--status", "-s", help="Filtrer par status"),
    limit: int = typer.Option(20, "--limit", "-n"),
):
    """Liste les snapshots stockés dans Supabase."""
    from alibabot.storage import SupabaseStorage

    storage = SupabaseStorage()
    rows = storage.list_snapshots(status=status, limit=limit)
    if not rows:
        console.print("[yellow]No snapshots found.[/]")
        return

    table = Table(title="Snapshots Supabase")
    table.add_column("snapshot_id", style="cyan")
    table.add_column("status")
    table.add_column("triggered_by")
    table.add_column("created_at")
    table.add_column("items", justify="right")
    for row in rows:
        stats = row.get("stats", {}) or {}
        total_items = sum((s or {}).get("count", 0) for s in stats.values())
        table.add_row(
            row["snapshot_id"],
            row["status"],
            row["triggered_by"],
            row["created_at"][:19],
            str(total_items),
        )
    console.print(table)


if __name__ == "__main__":
    app()
