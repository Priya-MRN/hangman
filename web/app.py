"""Flask web app: a joyful, fully responsive kids' Hangman.

Design note - POSITIVE THEME
----------------------------
Classic Hangman shows a stick figure being hanged, which is morbid and not
kid-appropriate. This game instead uses a *"fill the rainbow / save the day"*
theme: each wrong guess fills in one band of a rainbow and removes one heart.
There is never a hanging figure. Losing is gentle and encouraging.

Endpoints
---------
* ``GET  /``                 - language picker page.
* ``GET  /play/<code>``      - game page for a language.
* ``POST /api/new``          - start a new round, returns state.
* ``POST /api/guess``        - submit a guess, returns updated state.
* ``GET  /api/state``        - current round state.
* ``POST /api/upload-pack``  - upload a new language pack (JSON).
* ``GET  /api/image/<id>``   - redirect to the real emoji image (Twemoji PNG).

The current round is kept in the Flask session, so play is per-user without a
database.
"""

from __future__ import annotations

import random
import sys
from pathlib import Path

from flask import (
    Flask,
    Response,
    jsonify,
    redirect,
    render_template,
    request,
    session,
)

# Make the package importable whether or not it is pip-installed.
_SRC = Path(__file__).resolve().parent.parent / "src"
if _SRC.is_dir() and str(_SRC) not in sys.path:
    sys.path.insert(0, str(_SRC))

from hangman import __version__, images, packs  # noqa: E402
from hangman.game import HangmanGame, choose_word, tokenize  # noqa: E402

app = Flask(__name__, template_folder="templates", static_folder="static")
app.secret_key = "hangman-kids-secret-change-me"  # session signing only


# --- Helpers ---------------------------------------------------------------


def _build_keyboard(game: HangmanGame, pack: dict) -> list[str]:
    """Tokens shown on the on-screen keyboard.

    For packs with a fixed ``alphabet`` (e.g. English) we use it. For packs
    without one (e.g. Tamil), the keyboard is the union of the word's own
    clusters plus distractor clusters drawn from other words, shuffled.
    """
    if pack.get("alphabet"):
        return list(pack["alphabet"])
    needed = list(dict.fromkeys(game.tokens))
    distractors: list[str] = []
    for entry in pack["words"]:
        for tok in tokenize(entry["word"], pack["code"]):
            if tok not in needed and tok not in distractors:
                distractors.append(tok)
    random.shuffle(distractors)
    keyboard = needed + distractors[: max(8, len(needed))]
    random.shuffle(keyboard)
    return keyboard


def _new_game(code: str) -> tuple[HangmanGame, dict]:
    """Create a new round for language *code* and store it in the session."""
    pack = packs.get_pack(code)
    entry = choose_word(pack["words"])
    game = HangmanGame(
        word=entry["word"], lang=pack["code"],
        hint=entry.get("hint", ""), image=entry.get("image", ""),
    )
    keyboard = _build_keyboard(game, pack)
    session["game"] = {
        "word": game.word,
        "lang": game.lang,
        "hint": game.hint,
        "image": game.image,
        "guessed": [],
        "wrong": [],
        "keyboard": keyboard,
        "direction": pack["direction"],
        "language": pack["language"],
    }
    return game, session["game"]


def _load_game() -> tuple[HangmanGame | None, dict | None]:
    """Rebuild the HangmanGame from the session, if any."""
    data = session.get("game")
    if not data:
        return None, None
    game = HangmanGame(
        word=data["word"], lang=data["lang"],
        hint=data["hint"], image=data["image"],
    )
    game.guessed = set(data["guessed"])
    game.wrong = list(data["wrong"])
    return game, data


def _state_response(game: HangmanGame, data: dict) -> Response:
    """Build the JSON state, including the win image URL and keyboard."""
    won_url = (
        images.image_url_for(game.image or game.word) if game.is_won else None
    )
    state = game.state(won_image_url=won_url)
    state["keyboard"] = data["keyboard"]
    state["direction"] = data["direction"]
    state["language"] = data["language"]
    return jsonify(state)


# --- Pages -----------------------------------------------------------------


@app.route("/")
def index() -> str:
    """Language picker page."""
    return render_template(
        "index.html", languages=packs.list_languages(), version=__version__
    )


@app.route("/play/<code>")
def play(code: str) -> str:
    """Game page for a chosen language."""
    try:
        pack = packs.get_pack(code)
    except packs.PackError:
        return render_template(
            "index.html",
            languages=packs.list_languages(),
            version=__version__,
            error=f"Unknown language '{code}'.",
        )
    return render_template("game.html", code=code, language=pack["language"],
                           version=__version__)


# --- API -------------------------------------------------------------------


@app.route("/api/new", methods=["POST"])
def api_new() -> Response:
    """Start a new round. Body: ``{"code": "en"}``."""
    code = (request.get_json(silent=True) or {}).get("code", "en")
    try:
        game, data = _new_game(code)
    except packs.PackError as exc:
        return jsonify({"error": str(exc)}), 400
    return _state_response(game, data)


@app.route("/api/guess", methods=["POST"])
def api_guess() -> Response:
    """Submit a guess. Body: ``{"token": "A"}``."""
    game, data = _load_game()
    if game is None:
        return jsonify({"error": "No game in progress. Start a new one."}), 400
    token = (request.get_json(silent=True) or {}).get("token", "")
    if token:
        game.guess(token)
        data["guessed"] = sorted(game.guessed)
        data["wrong"] = list(game.wrong)
        session["game"] = data
    return _state_response(game, data)


@app.route("/api/state", methods=["GET"])
def api_state() -> Response:
    """Return the current round state."""
    game, data = _load_game()
    if game is None:
        return jsonify({"error": "No game in progress."}), 404
    return _state_response(game, data)


@app.route("/api/upload-pack", methods=["POST"])
def api_upload_pack() -> Response:
    """Upload a new language pack (JSON file or raw text)."""
    text = ""
    if "file" in request.files:
        text = request.files["file"].read().decode("utf-8", errors="replace")
    elif request.is_json:
        # Allow posting the pack object directly.
        import json

        text = json.dumps(request.get_json())
    else:
        text = request.form.get("text", "") or request.get_data(as_text=True)

    if not text.strip():
        return jsonify({"error": "No pack data received."}), 400

    try:
        pack = packs.save_uploaded_pack(text)
    except packs.PackError as exc:
        return jsonify({"error": str(exc)}), 400
    return jsonify({
        "ok": True,
        "code": pack["code"],
        "language": pack["language"],
        "count": len(pack["words"]),
    })


@app.route("/api/image/<image_id>")
def api_image(image_id: str) -> Response:
    """Redirect to the real emoji image (Twemoji PNG) for *image_id*."""
    return redirect(images.image_url_for(image_id))


if __name__ == "__main__":  # pragma: no cover
    app.run(debug=True, host="127.0.0.1", port=5000)
