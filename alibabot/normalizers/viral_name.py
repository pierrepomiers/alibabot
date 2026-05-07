"""Extract {size, color} from a product name.

Used for:
- Viral PrestaShop (no structured variants — info is in the name).
- Deflow Shopify (each color sold as a separate product, info is in the name).

Patterns observed (sample):
- "Dérives Thruster - Eric Arakawa - Large - fiberglass black / grey, FUTURES."
- "Leash surf Premium - Regular Knee 9'0'' x 7mm - Noir, JUST"
- "Pad surf - Rouleau - 200 x 50 cm - Noir, JUST"
- "Longboard sock cover 9'2'' - Housse de surf, JUST"
- "V.2 Granite", "Rocket Cherry"  (Deflow)
"""
from __future__ import annotations

import re

from alibabot.normalizers.values import canonicalize_color, normalize_size_value


# Couleurs reconnues, triées par longueur décroissante pour matcher
# les composées avant les simples ("Black White" avant "Black", "Acid Lemon" avant "Acid")
KNOWN_COLORS_RAW = [
    # Composés FR/EN courants
    "Black White", "Black & White", "Black / White", "Black/grey", "Black / grey",
    "Grey Black", "Red White Blue Fade", "Noir & Jaune Fluo",
    # Couleurs simples — français
    "Noir", "Blanc", "Bleu", "Rouge", "Jaune", "Vert", "Gris",
    "Crème", "Argent", "Bordeaux", "Rose", "Violet", "Marron",
    # Couleurs simples — anglais
    "Black", "White", "Blue", "Red", "Yellow", "Green", "Grey", "Gray",
    "Cream", "Smoke", "Clear", "Pink", "Purple", "Brown", "Orange",
    "Silver", "Gold",
    # Couleurs spécifiques Deflow / signature shapers
    "Granite", "Burgundy", "Cherry", "Mint", "Mustard", "Avocado",
    "Coral", "Olive", "Navy", "Teal", "Khaki", "Beige", "Sand", "Sage",
    "Acid Lemon", "Acid",
    # Couleurs surf classiques
    "Tranquil Blue", "Steel Grey", "Warm Grey", "Mango", "Alpine",
    "Pacific Blue", "Light Blue", "Dark Blue",
    # Modificateurs courants
    "Rainbow", "Fluo", "Neon",
]
KNOWN_COLORS = sorted(set(KNOWN_COLORS_RAW), key=len, reverse=True)


SIZE_PATTERNS = [
    # Dimensions explicites (rouleaux pads) : "200 x 50 cm"
    (re.compile(r"\b(\d+\s*x\s*\d+\s*(?:cm|mm))\b", re.IGNORECASE), "dimension"),
    # Longueurs en pieds/pouces : "9'0''", "6'7", "9.5", "10'0\""
    (re.compile(r"\b(\d{1,2}'\d{1,2}(?:''|\")?)\b"), "feet_inches"),
    # Pieds décimal : "9.5"  (utilisé seul dans certains noms longboard)
    (re.compile(r"-\s*(\d{1,2}\.\d)\b"), "feet_decimal"),
    # Lettres : XS, S, M, L, XL, XXL, PRO, M/L
    (re.compile(r"\b(XS|XXL|XL|M/L|PRO|S|M|L)\b"), "letter"),
    # Mots français explicites : "Taille M", "Taille L"
    (re.compile(r"\bTaille\s+([A-Z]+)\b", re.IGNORECASE), "taille_word"),
    # Mots taille en clair : "Large", "Medium", "Small", "Petite"
    (re.compile(r"\b(Large|Medium|Small|Petite)\b", re.IGNORECASE), "word"),
]


SIZE_BLACKLIST = {"3/2", "5/3"}


def _strip_brand_suffix(name: str) -> str:
    """Retire le suffixe ', BRAND.' à la fin du nom Viral."""
    return re.sub(r",\s*[A-Z][A-Z .&]+\.?$", "", name).strip()


def _extract_color(name: str) -> str | None:
    """Cherche une couleur connue dans le nom (case-insensitive, word-boundary)."""
    for color in KNOWN_COLORS:
        pattern = r"(?i)(?:^|[^A-Za-zÀ-ÿ])" + re.escape(color) + r"(?:[^A-Za-zÀ-ÿ]|$)"
        if re.search(pattern, name):
            return color
    return None


def _extract_size(name: str) -> str | None:
    """Cherche un pattern de taille dans le nom (premier match gagne)."""
    for regex, _kind in SIZE_PATTERNS:
        for m in regex.finditer(name):
            value = m.group(1).strip()
            if value in SIZE_BLACKLIST:
                continue
            return value
    return None


def extract_viral_variant(name: str) -> dict[str, str]:
    """Extract {size?, color?} from a product name (Viral and Deflow).

    Returns a possibly-empty dict. Coverage is best-effort (~70-80%).
    Values are canonicalized (Noir → Black, MEDIUM → Medium, etc.).
    """
    if not name:
        return {}

    body = _strip_brand_suffix(name)

    out: dict[str, str] = {}
    color = _extract_color(body)
    if color:
        out["color"] = canonicalize_color(color)
    size = _extract_size(body)
    if size:
        out["size"] = normalize_size_value(size)
    return out
