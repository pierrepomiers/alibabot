"""Extract fin system (Thruster, Quad, Twin, ...) from item name and tags.

Apply only to items with category == 'fins'.
"""
from __future__ import annotations
import re
from typing import Iterable


CANONICAL_SYSTEMS: tuple[str, ...] = (
    "Twinzer",
    "Thruster",
    "Quad",
    "Trailer",
    "Single",
    "Keel",
    "Twin",
    "Longboard",
)


SYSTEM_ALIASES: dict[str, str] = {
    "thruster": "Thruster",
    "tri fin": "Thruster",
    "tri fins": "Thruster",
    "tri ": "Thruster",
    "quad fin": "Quad",
    "quad fins": "Quad",
    "quad": "Quad",
    "twinzer": "Twinzer",
    "twin fin": "Twin",
    "twin fins": "Twin",
    "twin + 1": "Twin",
    "twin": "Twin",
    "single fin": "Single",
    "single": "Single",
    "trailer": "Trailer",
    "center fin": "Trailer",
    "keel": "Keel",
    "longboard fin": "Longboard",
    "longboard": "Longboard",
}


def _extract_from_tags(tags: Iterable[str]) -> str | None:
    """Try to extract a fin_system from tags (FCS pattern : 'Category:Thruster')."""
    if not tags:
        return None
    for tag in tags:
        if not tag:
            continue
        tag_low = tag.lower().strip()
        if ":" in tag_low:
            _, _, value = tag_low.partition(":")
            value = value.strip()
            if value in SYSTEM_ALIASES:
                return SYSTEM_ALIASES[value]
        if tag_low in SYSTEM_ALIASES:
            return SYSTEM_ALIASES[tag_low]
    return None


def _extract_from_name(name: str) -> str | None:
    """Try to extract a fin_system from the product name.

    Look for canonical aliases as whole-word matches, prioritizing longer matches first.
    """
    if not name:
        return None
    name_low = name.lower()

    sorted_aliases = sorted(SYSTEM_ALIASES.keys(), key=len, reverse=True)

    for alias in sorted_aliases:
        pattern = r"(?:^|[^a-z])" + re.escape(alias) + r"(?:[^a-z]|$)"
        try:
            if re.search(pattern, name_low):
                return SYSTEM_ALIASES[alias]
        except re.error:
            continue
    return None


def extract_fin_system(name: str, tags: Iterable[str] | None = None) -> str | None:
    """Returns the canonical fin system or None if undetectable.

    Strategy:
    1. Tags first (most reliable, FCS uses 'Category:Thruster' etc.)
    2. Name fallback (Viral uses 'Dérives Thruster - ...')
    """
    via_tags = _extract_from_tags(tags or [])
    if via_tags:
        return via_tags
    return _extract_from_name(name or "")
