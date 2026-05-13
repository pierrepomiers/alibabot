# TODO Alibabot

> Fichier vivant. À mettre à jour à chaque session de travail.
> Format : checkbox + scope + description.

## ✅ Phase 3G.2 — Done (frontend fin_system)

- [x] Section sidebar "Système de dérive" (visible si category=fins)
- [x] Badge fin_system sur les cartes produits fins
- [x] Param fin_system envoyé à l'API
- [x] Auto-reset fin_system quand on change de catégorie

## ✅ Phase 3G.1 — Done (backend fin_system)

- [x] Module `alibabot/normalizers/fin_system.py` (extraction tags + nom)
- [x] Wire dans scrapers Shopify et PrestaShop
- [x] CLI `validate-normalizer` étend l'affichage avec fin_systems
- [x] API : paramètre `fin_system` sur `/catalog/active` et `/catalog/active/facets`
- [x] Schéma Supabase : index sur `inferred_options->>'fin_system'`

## 🚧 Phase 3G.1 — À faire côté utilisateur

- [ ] Exécuter le SQL ALTER dans Supabase (index inferred_fin_system)
- [ ] Re-scrape complet : `alibabot scrape`
- [ ] Diagnostic : `alibabot validate-normalizer snapshots/<dernier>.json`
- [ ] Si couverture OK : `alibabot push-snapshot snapshots/<dernier>.json`

## ✅ Fix — filtre color/size couvre maintenant tous les fournisseurs

- [x] Filtrage variant-aware : matche `inferred_options` OU `variants[].normalized_options` avec available=true
- [x] Pagination en mémoire quand un filtre color/size est actif
- [x] FCS, Surf Lounge, Deflow variants désormais filtrables (bug observé : FCS+Black retournait 0)

## ✅ Phase 3F — Done (mini-fixes + clôture)

- [x] Bouton-au-survol des cartes : label raccourci "+ Ajout devis/cmd"
- [x] Backend : préfixe URL ligne note `👉` → `-->` (compat PDF Odoo)

## 🎉 PROJET ALIBABOT — TERMINÉ ET EN PRODUCTION

L'écosystème complet est livré. Voir `CLAUDE.md` pour le pipeline détaillé.

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

## ✅ Phase 3B — Done

- [x] Backend : paramètres `sort` + `direction` sur `/catalog/active`
- [x] Frontend : onglets Validation / Catalogue
- [x] Frontend : vue catalogue avec sidebar facettée (fournisseur, catégorie, marque, prix, stock)
- [x] Frontend : recherche texte (debounce 300ms) + tri
- [x] Frontend : grille de cartes (photo + brand + name + price + supplier + lien)
- [x] Frontend : scroll infini via IntersectionObserver

## ✅ Phase 3E — Done

### Backend (garybot-api)
- [x] /orders/draft inclut state='sale' du dernier mois
- [x] POST /orders/{id}/lines détecte state='sale' → mode informatif (qty=0, price=0, pas de TVA)
- [x] Réponse JSON enrichie : `informative_mode`, `order_state`

### Frontend (alibabot)
- [x] 🔒 préfixe dans dropdown pour les commandes validées
- [x] Bandeau info dans le modal si mode informatif
- [x] Bouton submit adapté ("Ajouter (ligne info)")
- [x] Toast adapté selon le mode

## 🚧 Phase 3E — À tester côté utilisateur

- [ ] Sur une commande draft : comportement nominal Phase 3D inchangé
- [ ] Sur une commande validée : 3 lignes ajoutées, total inchangé
- [ ] Si Odoo refuse qty=0 : implémenter plan B (line_note pour ligne 1)

## ✅ Phase 3D — Done

- [x] `CONFIG.garybotApiUrl` ajouté au frontend
- [x] Bouton "+ Ajouter au devis" (visible au survol) sur les cartes du catalogue
- [x] Modal d'ajout (produit + sélecteur variante + dropdown devis draft)
- [x] Mémorisation du dernier devis sélectionné en session (`S.lastSelectedOrderId`)
- [x] Submit → `POST garybot-api/orders/{id}/lines` → 3 lignes Odoo
- [x] Toast de confirmation / erreur en bas de page (3 s auto)
- [x] Bouton submit désactivé pendant la requête (anti double-clic)

## 🎉 PROJET ALIBABOT — TERMINÉ

L'écosystème complet :
- Cron hebdomadaire (lundi 2 h UTC) → scrape 4 fournisseurs → ~1226 items normalisés
- Supabase persistence + auto-purge (rejected/pending 7 j, archived 60 j)
- API REST FastAPI sur Render (auth multi-secrets côté garybot-api, x-api-secret côté alibabot)
- Frontend GitHub Pages : validation snapshots + catalogue avec variantes (pastilles couleur, pills taille, filtres facettés)
- Intégration Odoo : ajout direct au devis depuis la carte produit

Action restante côté utilisateur :
- [ ] Sur Render `garybot-api` : env var `API_SECRETS=notox2026,alibabot2026` (+ conserver `API_SECRET=notox2026`)
- [ ] Dans Odoo : 5 produits avec `default_code` `FINS`, `LEASH`, `PAD`, `BAG`, `DIVERS` (cf. `garybot-api/CLAUDE-backend.md` §12)
- [ ] Tester end-to-end depuis https://pierrepomiers.github.io/alibabot/

## ✅ Phase 3B++.3 — Done (variantes UI + filtres)

- [x] API : params `color` + `size` sur `/catalog/active`
- [x] API : compteurs `colors[]` + `sizes[]` dans `/catalog/active/facets`
- [x] Schémas API : `inferred_options` exposé sur `CatalogItemOut`, `normalized_options` sur `CatalogVariantOut`
- [x] Frontend : pastilles couleur + pills tailles sur chaque carte produit (seulement les variantes `available`)
- [x] Frontend : filtres sidebar Couleurs (avec pastille) + Tailles
- [x] Frontend : `Réinitialiser` reset aussi color/size

## 📦 Phase 3+ — Améliorations futures

- [ ] Cross-filter facets complets (compteurs intelligents qui ignorent le filtre courant)
- [ ] Phase 3C : endpoints garybot-api pour Odoo
- [ ] Migrer `regex=` → `pattern=` sur les `Query(...)` (`api/routes/catalog.py`, `api/routes/snapshots.py`) pour éviter le DeprecationWarning FastAPI

## ✅ Phase 3B++.1 bis — Done (patch normalisation)

- [x] Module `alibabot/normalizers/values.py` (canonicalisation couleurs + tailles)
- [x] FR→EN sur les couleurs (Noir→Black, Bleu→Blue, etc.)
- [x] Title Case canonique (BLACK SILVER → Black Silver)
- [x] `couleurs` (pluriel) ajouté à COLOR_KEYS pour Surf Lounge
- [x] Extraction depuis nom étendue à Deflow (Shopify scraper appelle aussi `extract_from_name`)
- [x] Whitelist couleurs enrichie (Granite, Burgundy, Cherry, Mint, Acid Lemon, etc.)

## 🚧 Phase 3B++.1 bis — À faire côté utilisateur

- [ ] `alibabot scrape` (re-scrape complet)
- [ ] `alibabot validate-normalizer snapshots/<dernier>.json` — vérifier que :
  - Deflow Color % > 30 % (avant : 0 %)
  - Surf Lounge Color en TitleCase (`Black Silver` au lieu de `BLACK SILVER`)
  - Viral `Noir` et `Black` sont fusionnés en `Black`
- [ ] Si OK : `alibabot push-snapshot snapshots/<dernier>.json`

## ✅ Phase 3B++.1 — Done (normalisation backend)

- [x] Module `alibabot/normalizers/` (core, shopify_options, viral_name)
- [x] Champs `normalized_options` (variants) et `inferred_options` (items) dans les modèles
- [x] Intégration dans les scrapers Shopify et PrestaShop
- [x] Schéma Supabase mis à jour (ALTER TABLE + 2 indexes)
- [x] CLI `alibabot validate-normalizer`

## 🚧 Phase 3B++.1 — À faire côté utilisateur

- [ ] Exécuter le SQL ALTER TABLE dans Supabase (cf. fin de `db/schema.sql`)
- [ ] Re-scraper en local : `alibabot scrape`
- [ ] Inspecter avec : `alibabot validate-normalizer snapshots/<dernier>.json`
- [ ] Si couverture Viral acceptable : `alibabot push-snapshot snapshots/<dernier>.json`
- [ ] Sinon : ajuster `alibabot/normalizers/viral_name.py` et re-tester

## 📦 Phase 3B++.2 — À venir

- [ ] Re-scrape de validation + accept du snapshot avec variantes normalisées

## 📦 Phase 3B++.3 — À venir

- [ ] Frontend : pastilles couleurs + pills tailles sur les cartes produits
- [ ] (Phase 3+ wishlist) Filtres facettés sur size et color dans la sidebar

## ✅ Phase 3B+ — Done (consolidation)

- [x] Cron hebdomadaire (lundi 2h UTC) au lieu de mensuel
- [x] Rétention 60 jours pour les snapshots archived
- [x] Endpoint POST /snapshots/{id}/restore
- [x] Bouton "Restaurer" sur les archived dans l'UI

## 🚧 Phase 3B+ — À faire côté utilisateur

- [ ] Exécuter le nouveau `db/schema.sql` (fonction `purge_old_snapshots` mise à jour) dans le SQL Editor Supabase
- [ ] Vérifier que le prochain run du workflow GitHub Actions a bien lieu un lundi

## 📦 Phase 3C — À venir

- [ ] Endpoint `GET /orders/draft` dans garybot-api
- [ ] Endpoint `POST /orders/{id}/lines` dans garybot-api
- [ ] Documenter le pattern d'auth croisé alibabot↔garybot

## 📦 Phase 3D — À venir

- [ ] Bouton "Ajouter au devis" sur chaque carte produit
- [ ] Modal avec dropdown des devis draft + sélecteur quantité + variant
- [ ] Toast de confirmation
- [ ] `CONFIG.garybotApiUrl` dans `docs/index.html`
- [ ] Branding : intégrer le visuel "Ali Baba au fez" (favicon, header)

## 🎨 Phase 3+ : améliorations UX

- [ ] Cross-filter facets (compteurs intelligents qui ignorent le filtre courant)
- [ ] Sauvegarde des filtres dans l'URL (deep linking)
- [ ] Comparateur multi-fournisseurs (même produit chez plusieurs distributeurs)
- [ ] Favoris / wishlist
- [ ] Historique de prix par produit (Phase 4 si on garde l'historique des snapshots)

## 🐛 Bugs / observations

- PrestaShop bascule en mode AJAX si Accept inclut application/json — Accept doit rester strictement text/html. Découvert pendant le scraping de viral-surf.com.

## 💡 Idées

- [ ] Système de matching cross-fournisseur (mêmes produits chez plusieurs distributeurs) pour comparer les prix
- [ ] Historique des prix par produit (tracking évolution dans le temps)
- [ ] Alertes "ce produit a baissé de 20% depuis le dernier snapshot"
