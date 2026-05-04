# Alibabot — Contexte projet pour Claude

> Document de référence pour Claude Code. À lire avant toute intervention.

## 1. Qui / Quoi

**Alibabot** = catalogue multi-fournisseurs de matériel de surf pour NOTOX (GREEN WAVE SAS, Anglet).
3ème repo de l'écosystème, après `garybot` (frontend) et `garybot-api` (backend Odoo).

Nom inspiré d'Ali Baba (le marchand des Mille et Une Nuits qui ouvre la caverne aux trésors).

## 2. État actuel — Phase 2B

CLI scraping ✅ + Supabase persistence ✅ + cron mensuel ✅ + **API FastAPI sur Render ✅**.

L'API expose les snapshots (list, detail, diff, accept, reject) et le catalogue actif (filtres riches + facettes).
Auth via header `x-api-secret`. Déployée sur Render free tier, auto-deploy on push main.

### API endpoints

| Méthode | Route | Auth | Description |
|---|---|---|---|
| GET / HEAD | `/health` | non | Keep-alive (UptimeRobot) |
| GET | `/config` | non | Diagnostic env vars (sans révéler les valeurs) |
| GET | `/snapshots` | oui | Liste paginée (filtre `?status=`, `?limit=`) |
| GET | `/snapshots/{snapshot_id}` | oui | Détail (avec error_log complet) |
| GET | `/snapshots/{snapshot_id}/diff?detail=full\|summary` | oui | Diff vs snapshot actif |
| POST | `/snapshots/{snapshot_id}/accept` | oui | Active ce snapshot, archive l'ancien |
| POST | `/snapshots/{snapshot_id}/reject?reason=...` | oui | Rejette ce snapshot |
| GET | `/catalog/active` | oui | Liste paginée + filtres riches |
| GET | `/catalog/active/facets` | oui | Compteurs par fournisseur / marque / catégorie |
| POST | `/admin/purge` | oui | Trigger purge_old_snapshots manuel |

## 3. Catégories métier (whitelist stricte)

Seules ces catégories sont conservées :
- `fins` — Dérives (single, twin, thruster, quad, longboard, twinzer)
- `leashes` — Leashes (surf, longboard, foil, bodyboard)
- `pads` — Traction pads
- `covers` — Housses de planches
- `transport` — Sangles, racks, soft racks, protections de toit

**Tout item hors de cette liste est rejeté** par `BaseScraper._validate_item()` et loggé en erreur de type `category_rejected`.

## 4. Architecture (cible finale)

```
Phase 1 : CLI → snapshots/*.json
Phase 2 : GitHub Actions cron nocturne → Supabase pending → FastAPI sur Render → validation manuelle
Phase 3 : Frontend GitHub Pages → filtres + injection lignes devis Odoo via XML-RPC
```

## 5. Source unique de vérité : `config/suppliers.yaml`

**Toute la configuration des fournisseurs/collections est dans ce fichier YAML.**

Modèle :
```yaml
allowed_categories: [fins, leashes, pads, covers, transport]
suppliers:
  <slug>:
    name: ...
    type: shopify | prestashop
    base_url: ...
    rate_limit_seconds: ...
    default_brand: ... | null
    collections:
      - handle: ... (Shopify) | path: ... (PrestaShop)
        category: fins | leashes | pads | covers | transport
        subcategory: ... | null
```

Pour ajouter un fournisseur Shopify : juste ajouter une entrée YAML, **pas de code**.
Pour ajouter une nouvelle plateforme : créer un nouveau scraper dans `alibabot/scrapers/`, l'enregistrer dans `registry.py`.

## 4bis. Stockage Supabase

- Project URL : `https://wmlxljwabqpiosvhmmmd.supabase.co`
- Tables : `catalog_snapshots`, `catalog_items`
- Vue : `catalog_active_items`
- Function : `purge_old_snapshots()` (purge `rejected` + `pending` > 7 jours)
- Auth : `service_role` key (bypass RLS, OK pour le cron interne)
- RLS activé mais sans policies anon → DB privée par défaut (Phase 2B ajoutera les policies pour l'API)

## 5bis. Workflow opérationnel

| Évènement | Effet |
|---|---|
| Cron mensuel (1er à 3h UTC) | Scrape les 4 fournisseurs, push snapshot status=pending |
| `workflow_dispatch` (bouton GitHub) | Trigger manuel à la demande |
| `alibabot push-snapshot file.json` | Push manuel local → Supabase |
| `alibabot list-snapshots` | Liste les snapshots Supabase |
| Auto-purge | Snapshots `rejected` ou `pending` > 7 jours supprimés |

## 6. Conventions

- **Python 3.11+** uniquement
- **httpx async** partout
- **Pydantic v2** pour valider toutes les données
- **Rich** pour l'output CLI
- **Erreurs non bloquantes** : un scraper qui échoue partiellement remplit `self.errors` mais ne casse pas les autres
- **Rate-limiting poli** : configurable par fournisseur, 3s pour Cloudflare (FCS), 1-1.5s sinon
- **Pas de scraping authentifié** : prix publics uniquement
- **Pas de Playwright** en Phase 1

## 6bis. Variables d'environnement

| Var | Où | Rôle |
|---|---|---|
| `SUPABASE_URL` | GitHub Actions secret + Render env + `.env` local | URL projet Supabase |
| `SUPABASE_SERVICE_ROLE_KEY` | GitHub Actions secret + Render env + `.env` local | Auth bypass RLS |
| `API_SECRET` | Render env + `.env` local | Header `x-api-secret` attendu (= `alibabot2026`) |

## 7. Comment tester

```bash
alibabot list-suppliers
alibabot scrape-one deflow
cat snapshots/<timestamp>.json | jq '.stats'
cat snapshots/<timestamp>.json | jq '.items[0]'
cat snapshots/<timestamp>.json | jq '.errors[:5]'
```

## 8. Suivi des tâches

`todo-items.md` à la racine du repo. À mettre à jour à chaque session de travail.
