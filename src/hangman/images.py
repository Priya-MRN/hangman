"""Offline word illustrations built from standard emoji.

The public entry point is :func:`svg_for`, which returns an SVG *string* for a
given illustration id (or word). Rather than hand-drawing shapes, it renders a
standard emoji (mapped from common words) on a soft card, falling back to the
first letter of the word when no emoji is known.

Everything here is pure Python with no third-party dependencies and works
entirely offline.
"""

from __future__ import annotations

# A bright, kid-friendly palette reused across illustrations.
SKY = "#aee9ff"

_HEADER = (
    '<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 200 200" '
    'width="200" height="200" role="img" aria-label="{label}">'
)


def _frame(inner: str, label: str, bg: str = "#fff8e7") -> str:
    """Wrap *inner* SVG markup in a rounded, soft-background card."""
    return (
        _HEADER.format(label=label)
        + f'<rect x="2" y="2" width="196" height="196" rx="24" '
        f'fill="{bg}" stroke="#ffe0a3" stroke-width="3"/>'
        + inner
        + "</svg>"
    )


# Friendly emoji used for the fallback card, keyed by common (lower-case) words.
_EMOJI = {
    "cat": "🐱", "dog": "🐶", "fish": "🐟", "apple": "🍎", "banana": "🍌",
    "sun": "☀️", "star": "⭐", "ball": "⚽", "tree": "🌳", "flower": "🌸",
    "house": "🏠", "car": "🚗", "bird": "🐦", "heart": "❤️", "moon": "🌙",
    "grapes": "🍇", "frog": "🐸", "duck": "🦆", "egg": "🥚", "milk": "🥛",
    "cow": "🐮", "pig": "🐷", "lion": "🦁", "bear": "🐻", "rabbit": "🐰",
    "bee": "🐝", "ant": "🐜", "owl": "🦉", "boat": "⛵", "kite": "🪁",
    "drum": "🥁", "book": "📖", "key": "🔑", "cup": "🥤", "hat": "🎩",
    "shoe": "👟", "leaf": "🍃", "rain": "🌧️", "snow": "❄️", "cake": "🎂",
    "orange": "🍊", "mango": "🥭", "lemon": "🍋", "rose": "🌹",
}


def _emoji_card(label: str) -> str:
    """A colorful card showing a standard emoji (or first letter) for *label*."""
    key = label.strip().lower()
    glyph = _EMOJI.get(key)
    if glyph is None:
        glyph = label.strip()[:1].upper() or "?"
    inner = (
        f'<circle cx="100" cy="100" r="70" fill="{SKY}"/>'
        f'<text x="100" y="100" font-size="80" text-anchor="middle" '
        f'dominant-baseline="central" font-family="Segoe UI Emoji, sans-serif">'
        f"{glyph}</text>"
    )
    return _frame(inner, label)


def svg_for(image_id_or_word: str) -> str:
    """Return an SVG string illustrating *image_id_or_word*.

    The argument may be an explicit illustration id (e.g. ``"cat"``) or a raw
    word. A standard emoji is rendered on a soft card when one is known for the
    word, otherwise its first letter is used. The result always starts with
    ``"<svg"`` and is safe to embed inline or serve directly.
    """
    return _emoji_card(image_id_or_word or "?")


def available_ids() -> list[str]:
    """Return the sorted list of ids that have a dedicated emoji."""
    return sorted(_EMOJI)
