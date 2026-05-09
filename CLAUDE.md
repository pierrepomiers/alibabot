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
| POST | `/snapshots/{snapshot_id}/restore` | oui | Réactive un snapshot `archived` comme actif (refuse 400 si non-archived) |
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
- Function : `purge_old_snapshots()` (purge `rejected` + `pending` > 7 jours, `archived` > 60 jours)
- Auth : `service_role` key (bypass RLS, OK pour le cron interne)
- RLS activé mais sans policies anon → DB privée par défaut (Phase 2B ajoutera les policies pour l'API)

## 5bis. Workflow opérationnel (Phase 3B+ updated)

| Évènement | Effet |
|---|---|
| Cron hebdomadaire (lundi 2h UTC) | Scrape les 4 fournisseurs, push snapshot status=pending |
| `workflow_dispatch` (bouton GitHub) | Trigger manuel à la demande |
| `alibabot push-snapshot file.json` | Push manuel local → Supabase |
| `alibabot list-snapshots` | Liste les snapshots Supabase |
| Auto-purge | rejected/pending > 7j, archived > 60j |
| Restore | Réactive un snapshot archived comme actif (UI ou API) |

## 6. Conventions

- **Python 3.11+** uniquement
- **httpx async** partout
- **Pydantic v2** pour valider toutes les données
- **Rich** pour l'output CLI
- **Erreurs non bloquantes** : un scraper qui échoue partiellement remplit `self.errors` mais ne casse pas les autres
- **Rate-limiting poli** : configurable par fournisseur, 3s pour Cloudflare (FCS), 1-1.5s sinon
- **Pas de scraping authentifié** : prix publics uniquement
- **Pas de Playwright** en Phase 1

## 6bis. Normalisation des variantes (Phase 3B++.1 + bis)

Module `alibabot/normalizers/` qui standardise `size` et `color` à partir de :

- **Shopify (FCS, Surf Lounge)** : mapping des clés (`Size/Colour/TAILLE/COULEUR/Couleurs/etc.`) → `size/color`.
- **Shopify Deflow** : pas de variantes de couleur Shopify (chaque coloris = produit séparé). Couleur extraite **depuis le nom du produit** via la même heuristique que Viral. Stocké dans `CatalogItem.inferred_options` au niveau item.
- **Viral PrestaShop** : pas de variantes structurées. Extraction depuis le nom (whitelist couleurs + regex tailles).

Les **valeurs sont canonicalisées** dans `normalizers/values.py` :
- Couleurs : FR→EN (`Noir → Black`, `Bleu → Blue`, …) + Title Case (`BLACK SILVER → Black Silver`)
- Tailles : préservation des formats (`M`, `XL`, `9'0''`, `200 x 50 cm`) + Title Case sinon (`MEDIUM → Medium`)

Les `options` brutes sont préservées dans le champ original ; les valeurs canonicalisées vivent dans `normalized_options` (variantes Shopify) et `inferred_options` (item, pour Viral et Deflow).

Pour mesurer la qualité : `alibabot validate-normalizer snapshots/<file>.json`

## 6ter. Variables d'environnement

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

## 7bis. Frontend (Phase 3A)

Localisation : `frontend/`. Vanilla JS monolithe, pas de build.

### Auth

Supabase email/pass. Le client utilise la clé `anon public` (jamais la `service_role`). RLS protège la DB côté backend ; le frontend appelle l'API alibabot avec le JWT du user en `Authorization: Bearer ...` plus le `x-api-secret`.

### Vues actuelles

- `S.view = "login"` : formulaire email/pass
- `S.view = "snapshots"` : liste des snapshots
- `S.view = "diff"` : diff détaillé + accept/reject
- `S.view = "catalog"` : grille produits + sidebar facettes + scroll infini

### Vues à venir

- Phase 3D : modal "ajouter au devis Odoo"

### Phase 3B : Vue catalogue

Onglet "Catalogue" en plus de "Validation" dans le header. `S.view` peut être `"snapshots" | "diff" | "catalog"`.

Sidebar gauche (250px, sticky) : facettes (fournisseur, catégorie, marque, **couleurs**, **tailles**), inputs prix min/max, checkbox "en stock uniquement", bouton "Réinitialiser les filtres".

Zone centrale : barre de recherche (debounce 300ms), dropdown de tri, grille de cartes responsive (`auto-fill, minmax(200px, 1fr)`), scroll infini via `IntersectionObserver` sur `#catalog-sentinel`.

Filtres backend supportés : `supplier`, `category`, `subcategory`, `brand`, `in_stock`, `q`, `min_price`, `max_price`, `color`, `size`.
Tri : `sort=name|price|brand|in_stock|recent` + `direction=asc|desc` (cf. `ALLOWED_SORTS` dans `api/services/catalog_service.py`).

Facettes pour Phase 3B = **globales** (sur tout le snapshot avec filtres autres que color/size appliqués). Les facettes color/size acceptent `?color=…&size=…` pour symétrie API mais ne sont **pas** appliquées au calcul des compteurs (pour pouvoir basculer d'une couleur à l'autre sans que la sélection courante n'aspire les compteurs). L'amélioration "cross-filter facets" complète est reportée plus tard si besoin.

### Phase 3D : Bouton "Ajouter au devis"

Sur les cartes du catalogue, un bouton "+ Ajouter au devis" est rendu mais reste invisible (`opacity: 0`) tant que la souris n'est pas sur la `.product-card` (`:hover` ou `:focus-within`). Il n'apparaît que pour les items qui ont à la fois un `id` et un `price_eur`.

Au clic : modal `S.modal` qui :
- Affiche le produit (image, marque, nom, prix TTC, fournisseur)
- Si `>1` couleur : sélecteur obligatoire (boutons pastille + nom)
- Si `>1` taille : sélecteur obligatoire (boutons texte)
- Auto-sélectionne la couleur/taille s'il n'y en a qu'une
- Dropdown des 50 derniers `sale.order` draft (chargés via `garybot-api/orders/draft`, mis en cache `S.draftsLoaded` pour la session)
- Pré-sélectionne le dernier devis utilisé (`S.lastSelectedOrderId`)

Au submit : `POST garybot-api/orders/{id}/lines` (cf. Phase 3C garybot-api) qui crée 3 lignes Odoo (1 produit générique + 2 notes). Le bouton submit est désactivé pendant la requête pour éviter le double-clic.

Toast de confirmation/erreur (`S.toast`) en bas de page (3 s auto, dismissible). Classe `.toast-bottom` distincte du `.toast` historique (top, erreur globale).

URL et auth de garybot-api : `CONFIG.garybotApiUrl` + `CONFIG.apiSecret` (= `alibabot2026`). Le secret doit être présent dans `API_SECRETS` côté garybot-api Render.

Note : le total du devis Odoo n'est pas recalculé immédiatement après création — Odoo le recalcule à l'ouverture du devis dans son UI (workflow normal puisque l'édition fine se fait dans Odoo, pas dans GaryBot).

### Phase 3B++.3 : Variantes UI

**Affichage** : pastilles couleur (avec tooltip) + pills tailles sur chaque carte produit.
- Seules les variantes `available: true` sont affichées
- Mapping nom de couleur → hex dans `COLOR_HEX` (frontend uniquement)
- Couleurs composées (ex: `Black / Grey`) : on prend la première pour la pastille (`split(/[\/&]/)[0]`)
- Source des couleurs/tailles : `CatalogItem.inferred_options` (Viral, Deflow item-level) **ou** `CatalogVariant.normalized_options` quand `available=true` (FCS, Surf Lounge)

**Filtres sidebar** : sections "Couleurs" (avec pastille) et "Tailles" (limite 8, "Voir toutes" sinon).
- API : `/catalog/active?color=Black&size=M`
- `/catalog/active/facets` retourne `colors[]` et `sizes[]` (top 50 chacun)

**Limite connue** : le filtre `color`/`size` côté API ne match que `inferred_options` (Viral + Deflow). Les items FCS / Surf Lounge dont la couleur ne vit que dans `variants[].normalized_options` ne sont pas matchés par le filtre — ils restent navigables via les autres filtres (marque, catégorie). Cross-filter complet à reprendre Phase 3+ si besoin.

### URL de la page

GitHub Pages : `https://pierrepomiers.github.io/alibabot/` (publication via dossier `/docs`).

## 8. Suivi des tâches

`todo-items.md` à la racine du repo. À mettre à jour à chaque session de travail.
