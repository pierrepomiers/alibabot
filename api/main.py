"""Alibabot API — Phase 2B."""
from __future__ import annotations

import os
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from api.routes import snapshots, catalog, admin

app = FastAPI(
    title="Alibabot API",
    description="Catalogue multi-fournisseurs NOTOX — endpoints snapshots & catalog",
    version="2.0.0",
)

# CORS permissif pour Phase 3 (frontend GitHub Pages cross-origin)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=False,
    allow_methods=["GET", "POST", "OPTIONS"],
    allow_headers=["*"],
)


@app.get("/health")
@app.head("/health")
async def health():
    """Keep-alive endpoint, sans auth (pour UptimeRobot)."""
    return {"status": "ok", "service": "alibabot-api"}


@app.get("/config")
async def config_check():
    """Diagnostic : vérifie que les env vars sont set (sans révéler les valeurs)."""
    return {
        "supabase_url_set": bool(os.environ.get("SUPABASE_URL")),
        "supabase_key_set": bool(os.environ.get("SUPABASE_SERVICE_ROLE_KEY")),
        "api_secret_set": bool(os.environ.get("API_SECRET")),
    }


# Routers
app.include_router(snapshots.router, prefix="/snapshots", tags=["snapshots"])
app.include_router(catalog.router, prefix="/catalog", tags=["catalog"])
app.include_router(admin.router, prefix="/admin", tags=["admin"])
