"""Word picture rewards as real emoji images (Twemoji).

The public entry point is :func:`image_url_for`, which maps an illustration id
(or raw word) to a **real PNG image URL** from Twemoji — the standard, open
emoji image set maintained by the community (https://github.com/jdecked/twemoji).
No hand-drawn SVG: each word resolves to a genuine emoji image such as a cat 🐱
or an apple 🍎.

The mapping is: word -> emoji character -> Twemoji codepoint filename -> URL.
Words with no known emoji fall back to a generic sparkle so there is always a
friendly picture. Building the URL is pure Python with no dependencies; only the
browser fetches the actual image at render time.
"""

from __future__ import annotations

# Twemoji 72x72 PNG assets, served from jsDelivr (a stable, standard CDN).
_TWEMOJI_BASE = "https://cdn.jsdelivr.net/gh/jdecked/twemoji@latest/assets/72x72/"

# Fallback emoji used when a word has no dedicated mapping.
_FALLBACK_EMOJI = "🌟"


# Standard emoji keyed by common (lower-case) words / illustration ids.
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


def _twemoji_filename(emoji: str) -> str:
    """Return the Twemoji filename stem for *emoji*, e.g. ``"1f431"`` for 🐱.

    Twemoji names each asset by its Unicode code points, lower-case hex, joined
    with ``-``. Variation selectors (U+FE0F) are stripped, matching Twemoji's
    own naming (e.g. ☀️ -> ``2600`` not ``2600-fe0f``).
    """
    points = [f"{ord(ch):x}" for ch in emoji if ch != "️"]
    return "-".join(points)


def emoji_for(image_id_or_word: str) -> str:
    """Return the standard emoji character for *image_id_or_word*.

    Falls back to a sparkle when no emoji is mapped for the word.
    """
    key = (image_id_or_word or "").strip().lower()
    return _EMOJI.get(key, _FALLBACK_EMOJI)


def image_url_for(image_id_or_word: str) -> str:
    """Return a real emoji PNG image URL illustrating *image_id_or_word*.

    The argument may be an explicit illustration id (e.g. ``"cat"``) or a raw
    word. It is mapped to a standard emoji and then to the corresponding
    Twemoji PNG asset URL. Words without a known emoji use a friendly sparkle.
    """
    emoji = emoji_for(image_id_or_word)
    return f"{_TWEMOJI_BASE}{_twemoji_filename(emoji)}.png"


def available_ids() -> list[str]:
    """Return the sorted list of ids that have a dedicated emoji image."""
    return sorted(_EMOJI)
