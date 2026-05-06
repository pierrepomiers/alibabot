# Alibabot Frontend

Frontend statique pour la validation des snapshots Alibabot.

## Stack

Vanilla JS, monolithe `index.html`. Pas de build, pas de framework. Hébergé sur GitHub Pages.

## Configuration

Avant de déployer, remplir dans `index.html` :

```javascript
const CONFIG = {
  supabaseUrl: "https://wmlxljwabqpiosvhmmmd.supabase.co",
  supabaseKey: "<ANON_KEY_HERE>",  // ← à remplir
  apiUrl: "https://alibabot.onrender.com",
  apiSecret: "alibabot2026",
};
```

La clé `anon public` se trouve dans Supabase Dashboard → Settings → API.

## Auth

Login via Supabase email/pass. Créer un utilisateur dans Supabase Dashboard → Authentication → Users → Add user.

## Tester en local

```bash
cd frontend
python3 -m http.server 8080
```

Puis ouvrir `http://localhost:8080`.

## Déploiement

GitHub Pages depuis branche `main`, dossier `/frontend`. Configuration : Settings → Pages.
