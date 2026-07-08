"""Colorful cross-platform command-line Hangman.

Run it with ``python -m hangman`` or the installed ``hangman`` script. The CLI
lets you pick a language, plays Hangman with a positive "rainbow" progress art
(instead of a morbid gallows), shows the word's emoji art on completion, and
uses encouraging messages throughout.

Colors use :mod:`colorama` when available (so they work on Windows terminals)
and degrade gracefully to plain text otherwise.
"""

from __future__ import annotations

import random
import sys

from . import packs
from .game import HangmanGame, choose_word, tokenize

# --- Color setup (graceful fallback if colorama is missing) ----------------
try:  # pragma: no cover - depends on environment
    import colorama
    from colorama import Fore, Style

    colorama.init()

    def c(text: str, color: str) -> str:
        return f"{color}{text}{Style.RESET_ALL}"

    YELLOW, GREEN, CYAN, RED, MAGENTA, BLUE = (
        Fore.YELLOW, Fore.GREEN, Fore.CYAN, Fore.RED, Fore.MAGENTA, Fore.BLUE,
    )
except Exception:  # pragma: no cover - fallback path

    def c(text: str, color: str) -> str:
        return text

    YELLOW = GREEN = CYAN = RED = MAGENTA = BLUE = ""


# A positive progress picture: the rainbow fills in with wrong guesses, then a
# happy sun appears. This keeps the game cheerful and kid-appropriate.
RAINBOW_BANDS = [
    ("  ~~~~~~~~~~  ", RED),
    (" ~~~~~~~~~~~~ ", YELLOW),
    ("~~~~~~~~~~~~~~", GREEN),
    (" ~~~~~~~~~~~~ ", CYAN),
    ("  ~~~~~~~~~~  ", BLUE),
    ("   ~~~~~~~~   ", MAGENTA),
]

# Emoji for completion art, reused from the image fallback table.
from .images import _EMOJI  # noqa: E402


def _draw_progress(wrong: int, total: int) -> str:
    """Show a rainbow that grows with each wrong guess (positive theme)."""
    lines = ["", c("      Save the day!", YELLOW)]
    shown = RAINBOW_BANDS[:wrong]
    for band, color in shown:
        lines.append(c(band, color))
    hearts = total - wrong
    lines.append("")
    lines.append("   Lives: " + c("♥ " * hearts, RED) + c("· " * wrong, ""))
    return "\n".join(lines)


def _pick_language() -> dict:
    """Prompt the player to choose a language pack."""
    langs = packs.list_languages()
    print(c("\n  Choose a language:", CYAN))
    for i, lang in enumerate(langs, 1):
        print(f"   {c(str(i), YELLOW)}. {lang['language']} "
              f"({lang['count']} words)")
    while True:
        choice = input(c("  Enter number: ", GREEN)).strip()
        if choice.isdigit() and 1 <= int(choice) <= len(langs):
            return packs.get_pack(langs[int(choice) - 1]["code"])
        print(c("  Please type a valid number.", RED))


def _build_keyboard(game: HangmanGame, pack: dict) -> list[str]:
    """Tokens the player may guess: pack alphabet, or word tokens + distractors."""
    if pack.get("alphabet"):
        return list(pack["alphabet"])
    # No fixed alphabet (e.g. Tamil): use the word's clusters plus distractors
    # gathered from other words in the pack.
    needed = list(dict.fromkeys(game.tokens))
    distractors: list[str] = []
    for entry in pack["words"]:
        for tok in tokenize(entry["word"], pack["code"]):
            if tok not in needed and tok not in distractors:
                distractors.append(tok)
    random.shuffle(distractors)
    keyboard = needed + distractors[: max(6, len(needed))]
    random.shuffle(keyboard)
    return keyboard


def _completion_art(game: HangmanGame) -> str:
    key = (game.image or game.word).strip().lower()
    glyph = _EMOJI.get(key, "🎉")
    return f"\n        {glyph}   {glyph}   {glyph}\n"


def play_round(pack: dict) -> None:
    """Play one round of Hangman with the given *pack*."""
    entry = choose_word(pack["words"])
    game = HangmanGame(
        word=entry["word"], lang=pack["code"],
        hint=entry.get("hint", ""), image=entry.get("image", ""),
    )
    keyboard = _build_keyboard(game, pack)
    hint_used = False

    print(c("\n  Let's play Hangman! 🎈", MAGENTA))
    print(c(f"  The word has {len(game.tokens)} letters.", CYAN))

    while not game.is_over:
        print(_draw_progress(game.wrong_count, game.max_wrong))
        print("\n   " + c("  ".join(game.masked()), YELLOW))
        if game.wrong:
            print(c("   Tried: " + " ".join(game.wrong), RED))
        print(c("   (type a letter, 'hint', or 'quit')", BLUE))

        guess = input(c("   Your guess: ", GREEN)).strip()
        if not guess:
            continue
        if guess.lower() in ("quit", "exit"):
            print(c("  Bye! Come back soon! 👋", MAGENTA))
            return
        if guess.lower() == "hint":
            if not hint_used and game.hint:
                print(c(f"   💡 Hint: {game.hint}", CYAN))
                hint_used = True
            else:
                print(c("   No more hints - you can do it!", CYAN))
            continue

        token = guess if pack["code"] == "ta" else guess.upper()
        correct = game.guess(token)
        if correct:
            print(c("   Yes! Great guess! ⭐", GREEN))
        else:
            print(c("   Not this time - keep trying! 💪", YELLOW))

    # Round over.
    if game.is_won:
        print(c("\n  🎉🎉 YOU WIN! Amazing job! 🎉🎉", GREEN))
        print(c(f"  The word was: {game.word}", YELLOW))
        print(_completion_art(game))
    else:
        print(c("\n  Aww, out of tries - but you tried so hard! 🌈", MAGENTA))
        print(c(f"  The word was: {game.word}", YELLOW))
        print(c("  Let's try another one!", CYAN))


def main(argv: list[str] | None = None) -> int:
    """CLI entry point. Returns a process exit code."""
    print(c("\n==============================", CYAN))
    print(c("   🎈  HANGMAN  for  KIDS  🎈", MAGENTA))
    print(c("==============================", CYAN))

    try:
        pack = _pick_language()
        while True:
            play_round(pack)
            again = input(c("\n  Play again? (y/n): ", GREEN)).strip().lower()
            if again not in ("y", "yes", ""):
                print(c("  Thanks for playing! 🌟", MAGENTA))
                break
    except (KeyboardInterrupt, EOFError):
        print(c("\n  Bye! 👋", MAGENTA))
    return 0


if __name__ == "__main__":  # pragma: no cover
    sys.exit(main())
