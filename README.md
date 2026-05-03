# 🛒 Alibabot

> *« Sésame, ouvre-toi ! »*

Catalogue multi-fournisseurs de matériel de surf pour **NOTOX / GREEN WAVE SAS**.

Scrape les catalogues publics de plusieurs fournisseurs surf, agrège les produits et permettra (Phase 2-3) de pousser des lignes dans des devis Odoo.

## État actuel : Phase 2A — CLI scraping + Supabase

CLI scraping ✅ + persistence Supabase ✅ + cron mensuel GitHub Actions. API FastAPI et frontend à venir (Phase 2B/3).

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

## Phase 2A — Persistence Supabase

Scraping mensuel automatique via GitHub Actions, stockage Supabase.

### Configuration locale (pour tester)

Crée un `.env` à la racine :

```bash
SUPABASE_URL=https://wmlxljwabqpiosvhmmmd.supabase.co
SUPABASE_SERVICE_ROLE_KEY=<la_service_role_key>
```

Puis :

```bash
# Pousser un snapshot JSON local vers Supabase
alibabot push-snapshot snapshots/2026-05-03T17-34-48.json

# Lister les snapshots stockés
alibabot list-snapshots
alibabot list-snapshots --status pending
```

### Cron GitHub Actions

Le workflow `.github/workflows/nightly-scrape.yml` tourne automatiquement le 1er de chaque mois à 3h UTC. Trigger manuel possible via "Actions → Monthly catalog scrape → Run workflow".

Secrets requis (à configurer dans Settings → Secrets → Actions) :
- `SUPABASE_URL`
- `SUPABASE_SERVICE_ROLE_KEY`

## Configuration

**Toute modification de fournisseurs/collections se fait dans `config/suppliers.yaml`.** Pas dans le code.

## Roadmap

- [x] **Phase 1** — CLI scraping + snapshots JSON locaux
- [x] **Phase 2A** — Persistence Supabase + cron mensuel GitHub Actions
- [ ] **Phase 2B** — API FastAPI sur Render + endpoints validation
- [ ] **Phase 3** — Frontend GitHub Pages avec filtres + intégration Odoo

Voir `todo-items.md` pour le détail.
