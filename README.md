# Alibabot 🧞‍♂️

Catalogue multi-fournisseurs pour NOTOX (planches de surf custom). Aide au sourcing d'accessoires (dérives, leashes, pads, housses, transport) avec injection directe dans les devis Odoo.

🌐 **App en production** : https://pierrepomiers.github.io/alibabot/

---

## Ce qu'Alibabot fait pour toi

- Scrape automatiquement 4 fournisseurs (Viral Surf, FCS Europe, Surf Lounge, Deflow Surf) chaque lundi matin
- Centralise ~1200 produits, normalise couleurs et tailles, expose des filtres facettés (marque, catégorie, couleur, taille, prix, dispo)
- Versionne le catalogue en snapshots : tu valides chaque nouvelle version (accept / reject / restore) avant qu'elle remplace l'active
- Bouton **+ Ajout devis/cmd** sur chaque produit qui injecte 3 lignes dans un devis Odoo (1 produit générique + 2 notes : nom détaillé + lien vers la fiche fournisseur)
- Détecte automatiquement les commandes Odoo déjà validées (Shopify "boitier custom") et bascule en mode "ligne informative" (qty=0, prix=0) pour ne pas toucher au total

---

## Stack

| Composant | Tech | Hébergement |
|---|---|---|
| Frontend | Vanilla JS, monolithe `docs/index.html` | GitHub Pages |
| API alibabot | FastAPI (Python 3.11+) | Render free tier |
| DB | Supabase Postgres + Auth | Supabase free tier |
| Scrapers | Python (`httpx`, `selectolax`, `pydantic v2`) | Local + GitHub Actions cron |
| Intégration Odoo | via `garybot-api` (repo séparé) | Render free tier |

---

## Comment ça marche au quotidien

### 1. Un client demande un accessoire en magasin
1. Tu ouvres https://pierrepomiers.github.io/alibabot/
2. Onglet **Catalogue**
3. Tu cherches / filtres (marque, catégorie, couleur, taille, prix, en stock)
4. Tu vois prix TTC + dispo + variantes chez chaque fournisseur

### 2. Tu prépares un devis pour un client
1. Tu trouves les accessoires dans le catalogue
2. Survol carte → bouton **+ Ajout devis/cmd**
3. Tu sélectionnes la couleur/taille puis le devis Odoo cible (les 50 derniers drafts)
4. Le produit + ses 2 notes sont injectés dans Odoo, total recalculé à l'ouverture

### 3. Commande Shopify "boitier custom"
Bernabot a importé la commande en 1 ligne globale. Tu veux détailler le contenu pour l'atelier sans toucher au total facturé.
1. Tu ajoutes les produits depuis Alibabot
2. Tu sélectionnes la commande validée (préfixée 🔒 dans le dropdown)
3. Mode informatif activé auto (qty=0, prix=0) — bandeau bleu et bouton "Ajouter (ligne info)"
4. Lignes ajoutées comme info, total inchangé

### 4. Valider le catalogue après scrape hebdo
Chaque lundi matin, un nouveau snapshot `pending` arrive.
1. Onglet **Validation**
2. Cliquer **Voir le diff** sur le pending
3. Vérifier ajouts / retraits / changements de prix
4. **Accept** (active le snapshot, archive l'ancien) ou **Reject** avec une raison

---

## Architecture

```
┌──────────────────┐   cron lundi 2h UTC    ┌──────────────────┐
│ GitHub Actions   │ ─────────────────────► │  4 fournisseurs  │
│ (scrape + push)  │ ◄───── ~1200 items ──── │ (HTTP public)    │
└──────────────────┘                         └──────────────────┘
         │
         │ snapshot pending
         ▼
┌──────────────────┐    REST + JWT/secret   ┌──────────────────┐
│ Supabase Postgres│ ◄────────────────────► │ FastAPI (Render) │
│ catalog_snapshots│                         │ alibabot.onrender│
│ catalog_items    │                         └──────────────────┘
└──────────────────┘                                 ▲
                                                     │
                                            ┌──────────────────┐
                                            │ Frontend (Pages) │
                                            │ docs/index.html  │
                                            └──────────────────┘
                                                     │ + Ajout
                                                     ▼
                                            ┌──────────────────┐
                                            │ garybot-api      │
                                            │ ─► Odoo XML-RPC  │
                                            └──────────────────┘
```

---

## Maintenance & opérations

### Variables d'environnement

**Render — service `alibabot-api`**
- `SUPABASE_URL`
- `SUPABASE_SERVICE_ROLE_KEY`
- `API_SECRET=alibabot2026`

**Render — service `garybot-api` (repo séparé, hub Odoo)**
- `API_SECRETS=notox2026,alibabot2026` (multi-secrets, virgules)
- `ODOO_URL`, `ODOO_DB`, `ODOO_USER`, `ODOO_API_KEY`

**GitHub Actions secrets** (pour le cron de scrape)
- `SUPABASE_URL`
- `SUPABASE_SERVICE_ROLE_KEY`

### Commandes locales

```bash
cd alibabot && source .venv/bin/activate && set -a; source .env; set +a

alibabot list-suppliers                              # config YAML chargée
alibabot scrape                                      # scrape complet (~2 min)
alibabot scrape-one deflow                           # un seul fournisseur
alibabot list-snapshots                              # via Supabase
alibabot push-snapshot snapshots/<file>.json         # push manuel
alibabot validate-normalizer snapshots/<file>.json   # diagnostic couverture
```

### Déclencher un scrape manuel

GitHub → onglet **Actions** → workflow **Weekly catalog scrape** → **Run workflow**.

### Restaurer un ancien snapshot

Onglet **Validation** → trouver l'archived → bouton **🔄 Restaurer**.

### Modifier la rétention

Fonction `purge_old_snapshots()` dans `db/schema.sql`. Modifier les `interval '7 days'` (rejected, pending) et `interval '60 days'` (archived) puis ré-exécuter dans le SQL Editor Supabase.

### Ajouter un fournisseur Shopify

Ajouter une entrée dans `config/suppliers.yaml` (handle, catégorie, brand par défaut). **Pas de code à toucher.** Pour une nouvelle plateforme (autre que Shopify / PrestaShop) : créer un scraper dans `alibabot/scrapers/` et l'enregistrer dans `registry.py`.

---

## Limites connues

- **Filtre couleur/taille de l'API** : ne couvre que `inferred_options` (Viral, Deflow item-level). Les variants Shopify FCS / Surf Lounge ne sont pas filtrables via l'API mais leurs pastilles s'affichent sur les cartes.
- **Couverture variantes Viral** : ~70-80% (extraction depuis le nom, best-effort — pas de fetch fiche produit).
- **Cold start Render** : ~30 s au premier appel après inactivité (free tier). Pas de keep-alive externe en place.
- **Pas de comparateur cross-fournisseurs** : le même produit chez plusieurs distributeurs apparaît plusieurs fois (backlog).

---

## Documentation technique

- [`CLAUDE.md`](./CLAUDE.md) — Référence technique détaillée (conventions, schéma, endpoints, workflow)
- [`todo-items.md`](./todo-items.md) — État des tâches et backlog
- [`docs/index.html`](./docs/index.html) — Frontend monolithe vanilla JS
- [`db/schema.sql`](./db/schema.sql) — Schéma Supabase + fonction de purge

---

## URLs

- Frontend : https://pierrepomiers.github.io/alibabot/
- API alibabot : https://alibabot.onrender.com
- API garybot (Odoo) : https://garybot-api.onrender.com
- Supabase project : `wmlxljwabqpiosvhmmmd`
- Repo : https://github.com/pierrepomiers/alibabot

---

*Construit en quelques jours par Pierre Pomiers (NOTOX) avec l'aide de Claude (Anthropic).*
