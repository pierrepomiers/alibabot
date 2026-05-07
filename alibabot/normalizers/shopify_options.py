"""Map Shopify variant options to normalized {size, color}."""
from __future__ import annotations


SIZE_KEYS = {"size", "taille", "length", "longueur", "size_us", "size_eu"}
COLOR_KEYS = {"colour", "color", "couleur"}


def normalize_shopify_options(options: dict[str, str]) -> dict[str, str]:
    """Convert Shopify variant options into a normalized {size?, color?} dict.

    Examples:
        >>> normalize_shopify_options({"Size": "MED", "Material": "Glass", "Colour": "Black"})
        {'size': 'MED', 'color': 'Black'}
        >>> normalize_shopify_options({"TAILLE": "MEDIUM", "COULEUR": "BLACK WHITE"})
        {'size': 'MEDIUM', 'color': 'BLACK WHITE'}
    """
    out: dict[str, str] = {}
    for k, v in options.items():
        if not v:
            continue
        kl = k.lower().strip()
        v_clean = v.strip()
        if kl in SIZE_KEYS and "size" not in out:
            out["size"] = v_clean
        elif kl in COLOR_KEYS and "color" not in out:
            out["color"] = v_clean
    return out
