"""Variant normalization — interface and dispatch."""
from __future__ import annotations


NORMALIZED_KEYS = {"size", "color"}


def normalize_options(supplier: str, raw_options: dict[str, str]) -> dict[str, str]:
    """Normalise les options d'une variante Shopify.

    Pour Viral (pas de variantes structurées), retourne {} ; utiliser
    extract_from_name() à la place sur l'item.
    """
    if not raw_options:
        return {}
    from alibabot.normalizers.shopify_options import normalize_shopify_options
    return normalize_shopify_options(raw_options)


def extract_from_name(supplier: str, name: str) -> dict[str, str]:
    """Extrait size/color depuis le nom du produit (utile pour Viral PrestaShop).

    Retourne dict potentiellement vide si rien ne matche. Capture les
    erreurs regex inattendues plutôt que de planter le scrape entier.
    """
    if supplier == "viral":
        try:
            from alibabot.normalizers.viral_name import extract_viral_variant
            return extract_viral_variant(name)
        except Exception:
            return {}
    return {}
