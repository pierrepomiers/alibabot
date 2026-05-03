# 🛒 Alibabot

> *« Sésame, ouvre-toi ! »*

Catalogue multi-fournisseurs de matériel de surf pour **NOTOX / GREEN WAVE SAS**.

Scrape les catalogues publics de plusieurs fournisseurs surf, agrège les produits et permettra (Phase 2-3) de pousser des lignes dans des devis Odoo.

## État actuel : Phase 1 — CLI scraping

Pour le moment, seul le scraping CLI est implémenté. Pas encore de Supabase, d'API ou de frontend.

## Catégories ciblées

`fins` · `leashes` · `pads` · `covers` · `transport`

Tout produit hors de ces catégories est automatiquement rejeté (et loggé pour audit).

## Fournisseurs

| Slug | Nom | Plateforme |
|---|---|---|
| `viral` | Viral Surf | PrestaShop |
| `fcs` | FCS Europe | Shopify (Cloudflare) |
| `surflounge` | Surf Lounge | Shopify |
| `deflow` | Deflow Surf | Shopify |

## Installation

```bash
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
pip install -e .
```

## Usage

```bash
# Lister les fournisseurs configurés
alibabot list-suppliers

# Scrape tous les fournisseurs
alibabot scrape

# Scrape un seul fournisseur (debug)
alibabot scrape-one deflow

# Output personnalisé
alibabot scrape --out ./mes-snapshots
```

Les snapshots sont écrits dans `snapshots/<timestamp>.json`.

## Configuration

**Toute modification de fournisseurs/collections se fait dans `config/suppliers.yaml`.** Pas dans le code.

## Roadmap

- [x] **Phase 1** — CLI scraping + snapshots JSON locaux
- [ ] **Phase 2** — Persistence Supabase + API FastAPI + cron nocturne + validation manuelle
- [ ] **Phase 3** — Frontend GitHub Pages avec filtres + intégration Odoo

Voir `todo-items.md` pour le détail.
