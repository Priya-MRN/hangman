"""Pytest suite for the Hangman game (no network access required)."""

from __future__ import annotations

import random
import sys
from pathlib import Path

import pytest

# Make the src package importable when running pytest from the project root.
SRC = Path(__file__).resolve().parent.parent / "src"
if str(SRC) not in sys.path:
    sys.path.insert(0, str(SRC))

from hangman import images, packs  # noqa: E402
from hangman.game import HangmanGame, choose_word, tokenize  # noqa: E402


# --- Tokenization ----------------------------------------------------------


def test_tokenize_english_is_per_letter():
    assert tokenize("CAT", "en") == ["C", "A", "T"]


def test_tokenize_tamil_groups_clusters():
    # பூனை = பூ + னை (two grapheme clusters), not 4 code points.
    clusters = tokenize("பூனை", "ta")
    assert clusters == ["பூ", "னை"]
    assert len(clusters) == 2


def test_tokenize_tamil_with_virama():
    # மீன் = மீ + ன் (ன + virama attaches to previous base).
    clusters = tokenize("மீன்", "ta")
    assert clusters == ["மீ", "ன்"]


# --- Win / lose logic ------------------------------------------------------


def test_win_detection():
    game = HangmanGame("CAT", "en")
    for letter in "CAT":
        game.guess(letter)
    assert game.is_won
    assert game.is_over
    assert not game.is_lost


def test_lose_after_max_wrong_guesses():
    game = HangmanGame("CAT", "en")
    for letter in "ZXQWVB":  # 6 wrong letters
        game.guess(letter)
    assert game.is_lost
    assert game.is_over
    assert game.wrong_count == 6
    assert game.remaining == 0


def test_repeated_guess_does_not_count_twice():
    game = HangmanGame("CAT", "en")
    game.guess("Z")
    game.guess("Z")
    assert game.wrong_count == 1


def test_masked_hides_unguessed_tokens():
    game = HangmanGame("CAT", "en")
    game.guess("C")
    assert game.masked() == ["C", "_", "_"]
    assert game.masked_display() == "C _ _"


def test_tamil_win_by_clusters():
    game = HangmanGame("பூனை", "ta")
    assert not game.is_won
    game.guess("பூ")
    game.guess("னை")
    assert game.is_won


# --- Pack loading / validation ---------------------------------------------


def test_builtin_packs_load():
    langs = {p["code"] for p in packs.list_languages()}
    assert "en" in langs
    assert "ta" in langs


def test_get_pack_returns_words():
    pack = packs.get_pack("en")
    assert pack["language"] == "English"
    assert len(pack["words"]) >= 20
    assert all("word" in w for w in pack["words"])


def test_validate_pack_rejects_missing_words():
    with pytest.raises(packs.PackError):
        packs.validate_pack({"language": "X", "code": "x"})


def test_validate_pack_rejects_non_object():
    with pytest.raises(packs.PackError):
        packs.validate_pack(["not", "a", "dict"])


def test_parse_pack_text_roundtrip():
    text = (
        '{"language":"Test","code":"tx","words":'
        '[{"word":"HI","hint":"greeting","image":"heart"}]}'
    )
    pack = packs.parse_pack_text(text)
    assert pack["code"] == "tx"
    assert pack["words"][0]["word"] == "HI"


# --- Images ----------------------------------------------------------------


def test_image_url_for_known_id():
    url = images.image_url_for("cat")
    # A real Twemoji PNG image URL for the cat emoji (U+1F431).
    assert url.startswith("https://")
    assert url.endswith(".png")
    assert "1f431" in url


def test_image_url_for_unknown_uses_fallback():
    url = images.image_url_for("zzz-unknown")
    assert url.startswith("https://")
    assert url.endswith(".png")


def test_emoji_for_maps_and_falls_back():
    assert images.emoji_for("cat") == "🐱"
    assert images.emoji_for("zzz-unknown") == "🌟"


def test_available_ids_nonempty():
    assert "cat" in images.available_ids()


# --- Random selection ------------------------------------------------------


def test_choose_word_within_pack():
    pack = packs.get_pack("en")
    rng = random.Random(42)
    entry = choose_word(pack["words"], rng)
    assert entry in pack["words"]


def test_choose_word_empty_raises():
    with pytest.raises(ValueError):
        choose_word([])
