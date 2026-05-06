# TODO Alibabot

> Fichier vivant. À mettre à jour à chaque session de travail.
> Format : checkbox + scope + description.

## 🚧 Phase 1 — Scrapers

### Handles de collections à confirmer

- [x] **fcs/covers** — résolu : handle `covers` (collection parente : day-covers, travel-covers, stretch-covers, longboard-covers)
- [x] **fcs/transport** — résolu : handle `auto-accessories` (tie-downs, soft-racks, scooter-bike-racks, key-locks, kanulock)
- [x] **deflow/transport** — RÉSOLU : Deflow n'a pas de collection transport propre. Tentative avec `range` abandonnée car ratio bruit/signal trop élevé (~40% d'items hors-transport : wax, vis, casquettes). Couverture transport assurée par FCS (18 items) + Surf Lounge (14 items).
- [ ] **viral/transport** — NON RÉSOLU : Viral Surf n'a pas de collection dédiée transport. Sangles potentielles dans `/fr/313-accessoires-surf` (fourre-tout) mais avec doublons. À reconsidérer Phase 3 si besoin.
- [x] **viral/covers** — la collection `/fr/2913-housses` est suffisante (multi-marques, pas seulement Just)

### Améliorations scrapers

- [x] **viral/brand** — Extraction de la marque depuis le nom (whitelist + match word-boundary). Couverture 98.2% (546/556). Les 10 items restants n'ont aucune marque connue dans le nom (fallback page-fiche encore possible si besoin).
- [x] **all/price_min_max (Viral)** — Propagation de price_eur vers price_min_eur / price_max_eur dans le scraper PrestaShop pour cohérence avec Shopify.
- [ ] **viral** — Vérifier la gestion du stock : lire les badges "Rupture de stock" et "Nouveau"
- [ ] **shopify** — Vérifier la robustesse de la pagination quand un fournisseur a plus de 250 produits dans une collection
- [ ] **all** — Logger les rejets de catégorie de manière plus visible (ex: stats par fournisseur "X items rejetés car hors-catégorie")

### Données

- [ ] Comparer les TTC entre fournisseurs : Viral et Surf Lounge sont-ils HT ou TTC ? Confirmer.
- [ ] Pour les fournisseurs multi-marques (Viral ✅, Surf Lounge), s'assurer que la marque est bien extraite (utile pour comparer entre fournisseurs)

## ✅ Phase 2A — Done

- [x] Schéma Supabase (`db/schema.sql`)
- [x] Module `alibabot/storage.py`
- [x] Script cron `cron/nightly_scrape.py`
- [x] Workflow GitHub Actions mensuel + manuel
- [x] CLI `push-snapshot` et `list-snapshots`
- [x] Auto-purge `rejected`/`pending` > 7 jours

## 🚧 Phase 2A — À faire côté utilisateur

- [ ] Exécuter `db/schema.sql` dans le SQL Editor Supabase
- [ ] Créer `.env` local avec `SUPABASE_URL` + `SUPABASE_SERVICE_ROLE_KEY`
- [ ] Tester `alibabot push-snapshot snapshots/<dernier>.json` en local
- [ ] Configurer secrets GitHub : `SUPABASE_URL` + `SUPABASE_SERVICE_ROLE_KEY`
- [ ] Trigger manuel du workflow GitHub Actions pour valider end-to-end

## ✅ Phase 2B — Done

- [x] FastAPI structuré dans `api/` (main, auth, schemas, routes/, services/)
- [x] Endpoints snapshots : list, detail, diff (full|summary), accept, reject
- [x] Endpoints catalog : `/catalog/active` (filtres riches) + `/catalog/active/facets`
- [x] Endpoint admin : `/admin/purge`
- [x] Auth `x-api-secret` sur toutes les routes (sauf `/health` et `/config`)
- [x] CORS permissif (préparation Phase 3 cross-origin)
- [x] `render.yaml` (auto-deploy on push main, plan free, region frankfurt)

## 🚧 Phase 2B — À faire côté utilisateur

- [ ] Connecter le repo `alibabot` à Render (New Web Service → Render lit `render.yaml`)
- [ ] Configurer 3 env vars dans Render dashboard : `SUPABASE_URL`, `SUPABASE_SERVICE_ROLE_KEY`, `API_SECRET=alibabot2026`
- [ ] Déclencher le premier deploy
- [ ] Tester `/health` et `/config` puis les endpoints authentifiés depuis l'URL Render publique
- [ ] Configurer UptimeRobot ping `/health` toutes les 5 min (anti-sleep free tier)
- [ ] Tests unitaires (pytest) — reportés en améliorations

## ✅ Phase 2C — Done

- [x] Compléter la config FCS : ajout `covers` et `auto-accessories`
- [x] Compléter la config Deflow : ajout `range` (transport)
- [x] Confirmer absence de collection transport chez Viral (acceptable, redondance avec FCS auto-accessories et Surf Lounge accessoires-auto-rack-velo)

## ✅ Phase 3A — Done

- [x] Frontend monolithe `frontend/index.html` avec login Supabase
- [x] Vue snapshots (liste + filtre par status)
- [x] Vue diff avec sections add/remove/price/stock
- [x] Boutons accept/reject

## 🚧 Phase 3A — À faire côté utilisateur

- [ ] Créer un utilisateur dans Supabase Auth (Dashboard → Authentication → Users → Add user)
- [ ] Récupérer la clé `anon public` (Settings → API)
- [ ] Remplacer `<ANON_KEY_HERE>` dans `frontend/index.html`
- [ ] Configurer GitHub Pages : Settings → Pages → Branch `main` / Folder `/frontend`
- [ ] Ouvrir l'URL et tester le flow complet (login → liste → diff → accept)

## 📦 Phase 3B — À venir

- [ ] Vue catalogue avec filtres facettés
- [ ] Recherche texte
- [ ] Pagination
- [ ] Cartes produits avec photo

## 📦 Phase 3C — À venir

- [ ] Endpoint `GET /orders/draft` dans garybot-api
- [ ] Endpoint `POST /orders/{id}/lines` dans garybot-api

## 📦 Phase 3D — À venir

- [ ] Modal "ajouter au devis" sur les cartes produits
- [ ] Toast de confirmation
- [ ] Branding : intégrer le visuel "Ali Baba au fez" (favicon, header)

## 🐛 Bugs / observations

- PrestaShop bascule en mode AJAX si Accept inclut application/json — Accept doit rester strictement text/html. Découvert pendant le scraping de viral-surf.com.

## 💡 Idées

- [ ] Système de matching cross-fournisseur (mêmes produits chez plusieurs distributeurs) pour comparer les prix
- [ ] Historique des prix par produit (tracking évolution dans le temps)
- [ ] Alertes "ce produit a baissé de 20% depuis le dernier snapshot"
