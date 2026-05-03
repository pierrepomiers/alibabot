# TODO Alibabot

> Fichier vivant. À mettre à jour à chaque session de travail.
> Format : checkbox + scope + description.

## 🚧 Phase 1 — Scrapers

### Handles de collections à confirmer

- [ ] **fcs/covers** — Trouver le handle Shopify exact pour les housses FCS (Stretch Cover, Travel Cover). À vérifier sur https://www.surffcs.eu/
- [ ] **fcs/transport** — Idem pour les sangles, racks, Cam Lock Tie Down, Soft Racks
- [ ] **deflow/transport** — Vérifier si Deflow a une gamme transport (drybags inclus ?). À voir sur https://www.deflowsurf.com/
- [ ] **viral/transport** — Vérifier si Viral Surf a des accessoires de transport et leurs handles
- [ ] **viral/covers** — La page `/fr/2913-housses` ne couvre que Just, vérifier s'il y a d'autres marques de housses chez Viral

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

## 📦 Phase 2B — À venir

- [ ] FastAPI déployé sur Render
- [ ] Endpoints : `/snapshots`, `/snapshots/{id}/diff`, `/snapshots/{id}/accept`, `/snapshots/{id}/reject`, `/catalog/active`
- [ ] Policies RLS Supabase pour l'API
- [ ] Auth `x-api-secret` (cohérent avec garybot-api)
- [ ] Tests unitaires (pytest)

## 🎨 Phase 3 — Frontend + Odoo (futur)

- [ ] Page statique GitHub Pages
- [ ] Filtres : fournisseur, marque, catégorie, prix, dispo
- [ ] Endpoint `/odoo/orders/{id}/lines` (réutilise XML-RPC de garybot-api)
- [ ] Diff viewer avant acceptation snapshot
- [ ] Branding : intégrer le visuel "Ali Baba au fez" (favicon, header)

## 🐛 Bugs / observations

- PrestaShop bascule en mode AJAX si Accept inclut application/json — Accept doit rester strictement text/html. Découvert pendant le scraping de viral-surf.com.

## 💡 Idées

- [ ] Système de matching cross-fournisseur (mêmes produits chez plusieurs distributeurs) pour comparer les prix
- [ ] Historique des prix par produit (tracking évolution dans le temps)
- [ ] Alertes "ce produit a baissé de 20% depuis le dernier snapshot"
