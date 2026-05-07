"""Canonicalize size and color values across all suppliers.

Goals
- Colors: French → English + Title Case (Noir → Black, BLACK SILVER → Black Silver)
- Sizes: Title Case but preserve formats (M, XL, M/L, 9'0'', 200 x 50 cm)

Reference cases:
    canonicalize_color("Noir")          == "Black"
    canonicalize_color("BLACK SILVER")  == "Black Silver"
    canonicalize_color("Black / grey")  == "Black / Grey"
    canonicalize_color("Cherry")        == "Cherry"
    canonicalize_color("Granite")       == "Granite"
    canonicalize_color("BLACK")         == "Black"
    normalize_size_value("MED")         == "MED"
    normalize_size_value("MEDIUM")      == "Medium"
    normalize_size_value("9'0''")       == "9'0''"
    normalize_size_value("200 x 50 cm") == "200 x 50 cm"
"""
from __future__ import annotations

import re


# Keys must be lowercase. Values are TitleCase canonical English.
COLOR_FR_TO_EN: dict[str, str] = {
    "noir": "Black",
    "blanc": "White",
    "bleu": "Blue",
    "rouge": "Red",
    "jaune": "Yellow",
    "vert": "Green",
    "gris": "Grey",
    "crème": "Cream",
    "creme": "Cream",
    "argent": "Silver",
    "bordeaux": "Burgundy",
    "rose": "Pink",
    "violet": "Purple",
    "marron": "Brown",
    "or": "Gold",
    "orange": "Orange",
    "fluo": "Fluo",
    "néon": "Neon",
    "neon": "Neon",
}


# Small connector words that stay lowercase inside a composed color name.
COLOR_KEEP_LOWER = {"and", "with", "of", "the", "a", "&"}


_SEPARATOR_RE = re.compile(r"\s+|/|&|\\")


def _titlecase_color(s: str) -> str:
    """Titlecase a color string while preserving separator chars (slash, ampersand)."""
    if not s:
        return s
    parts = re.split(r"(\s+|/|&|\\)", s)
    out: list[str] = []
    for p in parts:
        if not p or _SEPARATOR_RE.fullmatch(p):
            out.append(p)
            continue
        pl = p.lower()
        if pl in COLOR_KEEP_LOWER:
            out.append(pl)
        else:
            out.append(p.capitalize())
    return "".join(out).strip()


def canonicalize_color(value: str) -> str:
    """Apply FR→EN mapping word-by-word, then TitleCase."""
    if not value:
        return value
    v = re.sub(r"\s+", " ", value).strip()
    parts = re.split(r"(\s+|/|&|\\)", v)
    translated: list[str] = []
    for p in parts:
        if not p or _SEPARATOR_RE.fullmatch(p):
            translated.append(p)
            continue
        pl = p.lower()
        if pl in COLOR_FR_TO_EN:
            translated.append(COLOR_FR_TO_EN[pl])
        else:
            translated.append(p)
    joined = "".join(translated)
    return _titlecase_color(joined)


def normalize_size_value(value: str) -> str:
    """TitleCase a size value but preserve known formats."""
    if not value:
        return value
    v = value.strip()
    if re.search(r"[\d'\"]", v):
        return v
    if re.fullmatch(r"[A-Za-z]{1,4}(/[A-Za-z]{1,4})?", v):
        return v.upper()
    return v.title()
