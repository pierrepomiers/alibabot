# 🛒 Alibabot

> *« Sésame, ouvre-toi ! »*

Catalogue multi-fournisseurs de matériel de surf pour **NOTOX / GREEN WAVE SAS**.

Scrape les catalogues publics de plusieurs fournisseurs surf, agrège les produits et permettra (Phase 2-3) de pousser des lignes dans des devis Odoo.

## État actuel : Phase 2B — API REST déployée

CLI scraping ✅ + Supabase ✅ + cron mensuel ✅ + **API FastAPI sur Render ✅**. Frontend GitHub Pages à venir (Phase 3).

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

## Phase 2B — API REST (FastAPI)

API REST déployée sur Render (free tier), auto-deploy on push `main`. Source dans `api/`, config dans `render.yaml`.

### Lancer en local

```bash
source .venv/bin/activate
set -a; source .env; set +a
export API_SECRET=alibabot2026

uvicorn api.main:app --reload --port 8000
```

`.env` doit contenir `SUPABASE_URL` et `SUPABASE_SERVICE_ROLE_KEY`.

### Endpoints

Toutes les routes (sauf `/health` et `/config`) attendent le header `x-api-secret`.

```bash
# Health (no auth)
curl http://localhost:8000/health

# Config check
curl http://localhost:8000/config

# Snapshots
curl -H "x-api-secret: alibabot2026" http://localhost:8000/snapshots
curl -H "x-api-secret: alibabot2026" "http://localhost:8000/snapshots?status=pending"
curl -H "x-api-secret: alibabot2026" "http://localhost:8000/snapshots/<snap_id>/diff?detail=summary"

# Validation manuelle
curl -X POST -H "x-api-secret: alibabot2026" "http://localhost:8000/snapshots/<snap_id>/accept?activated_by=pierre"
curl -X POST -H "x-api-secret: alibabot2026" "http://localhost:8000/snapshots/<snap_id>/reject?reason=test"

# Catalogue actif
curl -H "x-api-secret: alibabot2026" "http://localhost:8000/catalog/active?supplier=fcs&category=fins&limit=10"
curl -H "x-api-secret: alibabot2026" "http://localhost:8000/catalog/active/facets"
```

### Déploiement Render

1. New Web Service → connecte le repo `alibabot` → Render lit `render.yaml`
2. Settings → Environment : ajouter `SUPABASE_URL`, `SUPABASE_SERVICE_ROLE_KEY`, `API_SECRET=alibabot2026`
3. Premier deploy déclenché auto, puis auto-deploy on push `main`
4. Configurer UptimeRobot ping `/health` toutes les 5 min (free tier sleep)

## Configuration

**Toute modification de fournisseurs/collections se fait dans `config/suppliers.yaml`.** Pas dans le code.

## Roadmap

- [x] **Phase 1** — CLI scraping + snapshots JSON locaux
- [x] **Phase 2A** — Persistence Supabase + cron mensuel GitHub Actions
- [x] **Phase 2B** — API FastAPI sur Render + endpoints validation
- [ ] **Phase 3** — Frontend GitHub Pages avec filtres + intégration Odoo

Voir `todo-items.md` pour le détail.
