"""Core, language-agnostic Hangman game logic.

The game operates on a list of *tokens*. A token is the smallest unit a
player guesses:

* For alphabetic languages (e.g. English) a token is a single letter.
* For Tamil a token is a *grapheme cluster* (a base consonant/vowel plus any
  combining marks) so that children guess whole readable characters rather
  than the underlying Unicode code points. See ``tokenize`` for details.

This keeps the engine simple and identical for every language: it only ever
sees a list of opaque tokens and a set of "guessed" tokens.
"""

from __future__ import annotations

import random
import unicodedata
from dataclasses import dataclass, field
from typing import Iterable

# Maximum number of wrong guesses before the game is lost. Six matches the
# classic Hangman drawing stages (head, body, 2 arms, 2 legs) and is a fair,
# kid-friendly amount of chances.
MAX_WRONG = 6


def tokenize(word: str, lang: str = "en") -> list[str]:
    """Split *word* into guessable tokens for the given language *lang*.

    For most languages each character is its own token. For Tamil (``lang ==
    "ta"``) we group each base character together with the combining marks
    that follow it, producing grapheme clusters such as ``"பூ"`` or ``"னை"``.
    This lets children guess whole syllable-like characters.

    Args:
        word: The word to split (case is preserved; callers usually upper-case
            Latin words first).
        lang: Language code (e.g. ``"en"`` or ``"ta"``).

    Returns:
        A list of token strings, in order.
    """
    word = word.strip()
    if not word:
        return []

    if lang == "ta":
        return _tamil_clusters(word)

    # Default: one token per character (works for English and most scripts).
    return list(word)


def _tamil_clusters(word: str) -> list[str]:
    """Group a Tamil string into grapheme clusters.

    A new cluster starts on any non-combining character. Combining marks
    (Unicode category starting with ``M``) and the virama/pulli (U+0BCD) and
    ZWJ/ZWNJ are attached to the preceding cluster.
    """
    clusters: list[str] = []
    for ch in word:
        category = unicodedata.category(ch)
        is_combining = category.startswith("M")
        is_joiner = ch in ("‍", "‌")  # ZWJ / ZWNJ
        if clusters and (is_combining or is_joiner):
            clusters[-1] += ch
        else:
            clusters.append(ch)
    return clusters


@dataclass
class HangmanGame:
    """A single round of Hangman.

    Attributes:
        word: The target word (display form).
        lang: Language code used for tokenization and keyboard building.
        hint: Optional hint shown on request.
        image: Optional illustration id used to look up an SVG on win.
        max_wrong: Number of wrong guesses allowed.
        tokens: The word split into guessable tokens (computed).
        guessed: Set of tokens the player has guessed (correct or not).
        wrong: List of wrong tokens, in order of guessing.
    """

    word: str
    lang: str = "en"
    hint: str = ""
    image: str = ""
    max_wrong: int = MAX_WRONG

    tokens: list[str] = field(init=False)
    guessed: set[str] = field(default_factory=set)
    wrong: list[str] = field(default_factory=list)

    def __post_init__(self) -> None:
        self.tokens = tokenize(self.word, self.lang)

    # --- Queries ---------------------------------------------------------

    @property
    def unique_tokens(self) -> set[str]:
        """The distinct tokens that make up the word."""
        return set(self.tokens)

    @property
    def wrong_count(self) -> int:
        """How many wrong guesses have been made."""
        return len(self.wrong)

    @property
    def remaining(self) -> int:
        """How many wrong guesses remain before losing."""
        return self.max_wrong - self.wrong_count

    @property
    def is_won(self) -> bool:
        """True when every token in the word has been guessed."""
        return self.unique_tokens.issubset(self.guessed)

    @property
    def is_lost(self) -> bool:
        """True when the player has exhausted all wrong guesses."""
        return self.wrong_count >= self.max_wrong

    @property
    def is_over(self) -> bool:
        """True when the round is finished (won or lost)."""
        return self.is_won or self.is_lost

    def masked(self, placeholder: str = "_") -> list[str]:
        """Return the word as a list of revealed tokens / placeholders.

        Guessed tokens are shown; everything else is the *placeholder*. When
        the game is lost the full word is revealed.
        """
        reveal_all = self.is_lost
        return [
            tok if (reveal_all or tok in self.guessed) else placeholder
            for tok in self.tokens
        ]

    def masked_display(self, placeholder: str = "_", sep: str = " ") -> str:
        """Human-readable masked word, e.g. ``"C _ T"``."""
        return sep.join(self.masked(placeholder))

    # --- Actions ---------------------------------------------------------

    def guess(self, token: str) -> bool:
        """Register a guess for *token*.

        Returns ``True`` if the token is in the word, ``False`` otherwise.
        Repeated guesses and guesses after the game is over are ignored and
        return whether the token is in the word.
        """
        if self.lang != "ta":
            token = token.upper()
        in_word = token in self.unique_tokens

        if self.is_over or token in self.guessed:
            return in_word

        self.guessed.add(token)
        if not in_word:
            self.wrong.append(token)
        return in_word

    # --- Serialization ---------------------------------------------------

    def state(self, won_image_url: str | None = None) -> dict:
        """Return a JSON-serializable snapshot of the game for the web UI."""
        data = {
            "lang": self.lang,
            "masked": self.masked(),
            "tokens_count": len(self.tokens),
            "guessed": sorted(self.guessed),
            "wrong": list(self.wrong),
            "wrong_count": self.wrong_count,
            "remaining": self.remaining,
            "max_wrong": self.max_wrong,
            "is_won": self.is_won,
            "is_lost": self.is_lost,
            "is_over": self.is_over,
            "hint": self.hint,
            "image": self.image,
        }
        if self.is_over:
            # Reveal the answer only once the round is finished.
            data["word"] = self.word
        if self.is_won and won_image_url is not None:
            # A real emoji image (Twemoji PNG) URL for the completed word.
            data["image_url"] = won_image_url
        return data


def choose_word(words: Iterable[dict], rng: random.Random | None = None) -> dict:
    """Pick a random word entry from *words*.

    Each entry is a dict like ``{"word": "CAT", "hint": "...", "image": "cat"}``.
    """
    rng = rng or random
    pool = list(words)
    if not pool:
        raise ValueError("Cannot choose a word from an empty word list.")
    return rng.choice(pool)
