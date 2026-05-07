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


@app.command("validate-normalizer")
def validate_normalizer(
    file: Path = typer.Argument(..., help="Chemin vers un snapshot JSON local"),
    show_unmatched: int = typer.Option(0, "--unmatched", "-u", help="Afficher N items sans extraction"),
):
    """Analyse un snapshot et affiche la couverture de la normalisation par fournisseur."""
    import json
    from collections import Counter, defaultdict
    from alibabot.models import ScrapeSnapshot

    if not file.exists():
        console.print(f"[red]File not found: {file}[/]")
        raise typer.Exit(1)

    data = json.loads(file.read_text())
    snapshot = ScrapeSnapshot(**data)

    by_supplier: dict[str, dict] = defaultdict(lambda: {
        "total": 0,
        "with_variants": 0,
        "variants_total": 0,
        "variants_with_size": 0,
        "variants_with_color": 0,
        "items_with_inferred_size": 0,
        "items_with_inferred_color": 0,
    })

    sizes_seen: dict[str, Counter] = defaultdict(Counter)
    colors_seen: dict[str, Counter] = defaultdict(Counter)
    unmatched: dict[str, list[str]] = defaultdict(list)

    for item in snapshot.items:
        s = by_supplier[item.supplier]
        s["total"] += 1

        if item.variants:
            s["with_variants"] += 1
            for v in item.variants:
                s["variants_total"] += 1
                if v.normalized_options.get("size"):
                    s["variants_with_size"] += 1
                    sizes_seen[item.supplier][v.normalized_options["size"]] += 1
                if v.normalized_options.get("color"):
                    s["variants_with_color"] += 1
                    colors_seen[item.supplier][v.normalized_options["color"]] += 1

        if item.inferred_options.get("size"):
            s["items_with_inferred_size"] += 1
            sizes_seen[item.supplier][item.inferred_options["size"]] += 1
        if item.inferred_options.get("color"):
            s["items_with_inferred_color"] += 1
            colors_seen[item.supplier][item.inferred_options["color"]] += 1
        if item.supplier == "viral" and not item.inferred_options:
            if len(unmatched[item.supplier]) < 50:
                unmatched[item.supplier].append(item.name)

    table = Table(title=f"Couverture normalisation — snapshot {snapshot.snapshot_id}")
    table.add_column("Fournisseur", style="cyan")
    table.add_column("Items", justify="right")
    table.add_column("Avec variants", justify="right")
    table.add_column("Variants totales", justify="right")
    table.add_column("Size %", justify="right", style="green")
    table.add_column("Color %", justify="right", style="yellow")

    for sup, s in sorted(by_supplier.items()):
        if s["variants_total"] > 0:
            size_pct = f"{100*s['variants_with_size']/s['variants_total']:.1f}%"
            color_pct = f"{100*s['variants_with_color']/s['variants_total']:.1f}%"
        else:
            size_pct = f"{100*s['items_with_inferred_size']/s['total']:.1f}% (inferred)" if s['total'] else "—"
            color_pct = f"{100*s['items_with_inferred_color']/s['total']:.1f}% (inferred)" if s['total'] else "—"
        table.add_row(
            sup,
            str(s['total']),
            str(s['with_variants']),
            str(s['variants_total']),
            size_pct,
            color_pct,
        )
    console.print(table)

    console.print("\n[bold]Top sizes par fournisseur :[/]")
    for sup, counter in sorted(sizes_seen.items()):
        top = counter.most_common(10)
        console.print(f"  {sup}: " + ", ".join(f"{v}({n})" for v, n in top))

    console.print("\n[bold]Top colors par fournisseur :[/]")
    for sup, counter in sorted(colors_seen.items()):
        top = counter.most_common(10)
        console.print(f"  {sup}: " + ", ".join(f"{v}({n})" for v, n in top))

    if show_unmatched > 0 and "viral" in unmatched:
        console.print(f"\n[bold red]{len(unmatched['viral'])} items Viral sans extraction :[/]")
        for name in unmatched["viral"][:show_unmatched]:
            console.print(f"  - {name}")


if __name__ == "__main__":
    app()
