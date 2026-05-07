"""Map Shopify variant options to normalized {size, color}."""
from __future__ import annotations

from alibabot.normalizers.values import canonicalize_color, normalize_size_value


SIZE_KEYS = {"size", "taille", "length", "longueur", "size_us", "size_eu"}
COLOR_KEYS = {"colour", "color", "couleur", "couleurs"}


def normalize_shopify_options(options: dict[str, str]) -> dict[str, str]:
    """Convert Shopify variant options into a normalized {size?, color?} dict.

    Values are canonicalized:
    - Colors: FR→EN mapping + TitleCase (e.g., "noir" → "Black", "BLACK SILVER" → "Black Silver")
    - Sizes: TitleCase / preserved formats (e.g., "MEDIUM" → "Medium", "9'0''" untouched)
    """
    out: dict[str, str] = {}
    for k, v in options.items():
        if not v:
            continue
        kl = k.lower().strip()
        v_clean = v.strip()
        if kl in SIZE_KEYS and "size" not in out:
            out["size"] = normalize_size_value(v_clean)
        elif kl in COLOR_KEYS and "color" not in out:
            out["color"] = canonicalize_color(v_clean)
    return out
