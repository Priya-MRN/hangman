# 🎈 Hangman for Kids — Developer Documentation

Developer-facing guide to the Hangman project: architecture, design decisions,
install/run, the language-pack format, the JSON API, and testing. For the
screenshot tour and folder layout, see the [root README](../README.md).

An elevated take on the classic **Hangman** game (CodeAlpha Task 1) — versatile,
multilingual, kid-friendly and joyful. Ships with **English** and **Tamil**, a
colorful terminal version, and a bright, fully responsive web UI with confetti
celebrations.

> The game logic runs offline; the only network asset is the **word picture
> reward**, a real emoji image served from the standard [Twemoji](https://github.com/jdecked/twemoji)
> set via CDN.

---

## ✨ Vision & Features

| Pillar | What it means here |
| --- | --- |
| **Versatile & Multilingual** | Play in any language via simple JSON **language packs**. Ships with English + Tamil. Players can **upload their own packs** (file drop or web form) — packs are auto-discovered at runtime. |
| **Kid-friendly** | Only simple, curated easy words (animals, fruits, colors, common objects), each with a friendly hint. |
| **Images** | When a word is completed, a big, colorful **real emoji image** of that word appears (a Twemoji PNG, mapped from the word); unknown words fall back to a friendly sparkle. |
| **Joyful / Positive** | Bright, cheerful palette (sunny yellows, soft greens, sky blues, playful pinks), **confetti** on win, encouraging messages, gentle "good try" on loss — never harsh. |
| **Responsive** | The web UI works on phones, tablets, and desktops with an **on-screen tappable keyboard** and large touch targets. |

---

## 🎨 Design Decision: a Positive Theme (no gallows!)

Classic Hangman draws a stick figure being hanged — morbid and not suitable for
children. This project replaces it with a **"fill the rainbow / save the day"**
theme:

- Each **wrong guess fills in one band of a rainbow** and removes one ❤️ heart.
- There is **never a hanging figure**.
- Six wrong guesses still ends the round, but the message is gentle and
  encouraging ("Good try! Let's try a new word!").

This keeps the experience cheerful and age-appropriate while preserving the
classic 6-mistakes gameplay.

---

## 🔤 Design Decision: Tamil Cluster Guessing

English (and most alphabets) are guessed **one letter at a time**. Tamil is an
*abugida*: a written character is often a base consonant plus combining
vowel/virama marks (e.g. `பூ`, `னை`). Guessing raw Unicode code points would be
confusing for a child.

So for Tamil the game guesses at the **grapheme-cluster level**:

- `tokenize("பூனை", "ta")` → `["பூ", "னை"]` (2 readable characters), not 4 code points.
- The on-screen keyboard for a Tamil round is built from the **clusters in the
  current word plus shuffled distractor clusters** drawn from other words in the
  pack (since a fixed "Tamil alphabet" keyboard would be impractically large).

This is implemented in `src/hangman/game.py` (`tokenize` / `_tamil_clusters`)
and the keyboard builders in `cli.py` / `web/app.py`.

---

## 🎯 Design Decision: Hint shown on load

Each word ships with a friendly hint, and the web UI **shows it automatically
when a new word loads** (see `newGame()` in `web/static/game.js`) so a player
always knows what they're guessing — the 💡 Hint button just re-displays it.

---

## 🧩 Language Pack Format

A language pack is a small UTF-8 **JSON** file:

```json
{
  "language": "English",
  "code": "en",
  "direction": "ltr",
  "alphabet": ["A", "B", "C", "...", "Z"],
  "words": [
    { "word": "CAT", "hint": "A pet that says meow", "image": "cat" }
  ]
}
```

| Field | Required | Notes |
| --- | --- | --- |
| `language` | ✅ | Human-readable name shown in the picker. |
| `code` | ✅ | Short unique id (used in URLs and filenames). |
| `words` | ✅ | Non-empty list of word entries. |
| `words[].word` | ✅ | The word to guess. |
| `words[].hint` | optional | Friendly hint. |
| `words[].image` | optional | Illustration id (see `images.py`) shown on win. |
| `alphabet` | optional | Fixed on-screen keyboard tokens. **Omit** for scripts like Tamil — the keyboard is then built from word clusters + distractors. |
| `direction` | optional | `"ltr"` (default) or `"rtl"`. |

### Adding a language

1. **By file:** drop a `<code>.json` pack into
   `src/hangman/languages/` (built-in) or `src/hangman/languages/uploads/`
   (user packs). It is auto-discovered next time the app reads packs.
2. **By web form:** on the home page, expand **"➕ Add a new language pack"** and
   upload your `.json`. It is validated, saved to the uploads folder, and the
   picker reloads with your new language.

Invalid packs are rejected with a friendly message (and a single bad upload
never breaks the game — see `packs.discover_packs`).

---

## 🖼️ Picture Rewards

`src/hangman/images.py` maps a word to a **real emoji image** from the standard
[Twemoji](https://github.com/jdecked/twemoji) set — no hand-drawn SVG. The flow
is `word -> emoji -> Twemoji codepoint filename -> PNG URL`:

- `emoji_for(id_or_word) -> str` — the emoji character (cat → 🐱, sun → ☀️,
  mango → 🥭, …), falling back to a sparkle 🌟 when no emoji is mapped.
- `image_url_for(id_or_word) -> str` — the corresponding Twemoji PNG URL, e.g.
  `.../assets/72x72/1f431.png` for 🐱.

The web UI renders this URL in an `<img>` on win, and `GET /api/image/<id>`
redirects to it. Building the URL is pure Python with no dependencies; only the
browser fetches the image.

---

## 🚀 Install

```bash
# from the project root
python -m pip install -r requirements.txt
# optional: editable install so the `hangman` command is available
python -m pip install -e .
```

Python 3.10+ required.

---

## 🕹️ Run the CLI

```bash
python -m hangman
# or, after `pip install -e .`
hangman
```

A colorful terminal game: pick a language, guess letters/clusters, watch the
rainbow fill, and see emoji art when you win. Uses `colorama` for cross-platform
color (with a graceful plain-text fallback).

---

## 🌈 Run the Web App

```bash
python web/app.py
# then open http://127.0.0.1:5000
```

- **Home:** language picker + pack upload form.
- **Game:** big masked word, positive rainbow progress, tappable keyboard,
  hint button, confetti + real emoji image on win, gentle encouragement on loss.

### JSON API

| Method | Path | Purpose |
| --- | --- | --- |
| `POST` | `/api/new` | Start a round: `{"code":"en"}` |
| `POST` | `/api/guess` | Guess a token: `{"token":"A"}` |
| `GET` | `/api/state` | Current round state |
| `POST` | `/api/upload-pack` | Upload a pack (file or JSON) |
| `GET` | `/api/image/<id>` | Redirect to the real emoji image (Twemoji PNG) |

---

## 🧪 Testing

```bash
python -m pytest -q
```

Covers: English & Tamil tokenization (including clusters/virama), win/lose
logic, max wrong guesses, masked display, pack loading & validation, image
image URL mapping (word → emoji → Twemoji PNG URL), and random word selection
within a pack. No network access required for the tests.

---

## 🎬 Media assets

The screenshots shown in the [root README](../README.md) and the demo video live
here in `docs/`:

| File | What it shows |
| --- | --- |
| `demo.mp4` | Full screen recording — English + Tamil rounds, wins, confetti *(not committed to git; kept locally)* |
| `demo-thumbnail.png` | Poster frame for the video (an English "You Win!" screen) |
| `screenshot-landing.png` | Home / language picker |
| `screenshot-game.png` | English game in progress (rainbow, hearts, keyboard) |
| `screenshot-win.png` | Win overlay — confetti + emoji picture reward |
| `screenshot-tamil.png` | Tamil round with the syllable-cluster keyboard |

All screenshots were extracted from `demo.mp4`. To refresh them, re-run the app
(`python web/app.py`) and recapture, keeping the same filenames.
