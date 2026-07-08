/* Hangman for Kids - front-end game controller.
   Talks to the Flask JSON API and renders a joyful, responsive UI. */

(function () {
  "use strict";

  const code = document.body.dataset.code;
  const RAINBOW_COLORS = ["#ff5d5d", "#ff9f45", "#ffd23f", "#7bd389", "#5aa9e6", "#b388eb"];
  const MAX = 6;

  const el = {
    word: document.getElementById("word"),
    message: document.getElementById("message"),
    keyboard: document.getElementById("keyboard"),
    rainbow: document.getElementById("rainbow"),
    hearts: document.getElementById("hearts"),
    hintBtn: document.getElementById("hint-btn"),
    newBtn: document.getElementById("new-btn"),
    hintDisplay: document.getElementById("hint-display"),
    overlay: document.getElementById("overlay"),
    overlayTitle: document.getElementById("overlay-title"),
    overlayImage: document.getElementById("overlay-image"),
    overlayWord: document.getElementById("overlay-word"),
    overlayMsg: document.getElementById("overlay-msg"),
    overlayAgain: document.getElementById("overlay-again"),
    confetti: document.getElementById("confetti"),
  };

  const WIN_MSGS = [
    "🎉 You did it! Super star!",
    "🌟 Amazing work! You're so clever!",
    "🥳 Hooray! You spelled it!",
    "🎈 Fantastic! Great job!",
  ];
  const TRY_MSGS = [
    "Keep going, you can do it! 💪",
    "Nice try! Try another letter! 🌈",
    "So close! Don't give up! ✨",
  ];

  let state = null;

  function pick(arr) {
    return arr[Math.floor(Math.random() * arr.length)];
  }

  function renderWord() {
    el.word.innerHTML = "";
    el.word.dir = state.direction || "ltr";
    state.masked.forEach((tok) => {
      const span = document.createElement("span");
      if (tok === "_") {
        span.className = "tile blank";
      } else {
        span.className = "tile";
        span.textContent = tok;
      }
      el.word.appendChild(span);
    });
  }

  function renderRainbow() {
    el.rainbow.innerHTML = "";
    const wrong = state.wrong_count;
    for (let i = 0; i < MAX; i++) {
      const band = document.createElement("div");
      band.className = "band" + (i < wrong ? " on" : "");
      const size = 230 - i * 34;
      band.style.width = size + "px";
      band.style.height = size / 2 + "px";
      band.style.borderColor = RAINBOW_COLORS[i];
      band.style.borderWidth = "16px";
      el.rainbow.appendChild(band);
    }
    const left = state.remaining;
    el.hearts.textContent = "❤️".repeat(left) + "🤍".repeat(MAX - left);
  }

  function renderKeyboard() {
    el.keyboard.innerHTML = "";
    el.keyboard.dir = state.direction || "ltr";
    state.keyboard.forEach((tok) => {
      const btn = document.createElement("button");
      btn.className = "key";
      btn.textContent = tok;
      const guessed = state.guessed.includes(tok) ||
        state.guessed.includes(tok.toUpperCase());
      if (guessed) {
        btn.disabled = true;
        btn.classList.add(state.wrong.includes(tok) ||
          state.wrong.includes(tok.toUpperCase()) ? "wrong" : "correct");
      }
      if (state.is_over) btn.disabled = true;
      btn.addEventListener("click", () => guess(tok));
      el.keyboard.appendChild(btn);
    });
  }

  function render() {
    renderWord();
    renderRainbow();
    renderKeyboard();
    if (!state.is_over) {
      el.message.textContent = state.wrong_count > 0
        ? pick(TRY_MSGS) : "Pick a letter! 🎈";
    }
    if (state.is_over) showOverlay();
  }

  async function api(path, body) {
    const opts = { method: body ? "POST" : "GET" };
    if (body) {
      opts.headers = { "Content-Type": "application/json" };
      opts.body = JSON.stringify(body);
    }
    const res = await fetch(path, opts);
    return res.json();
  }

  async function newGame() {
    hideOverlay();
    el.hintDisplay.textContent = "";
    state = await api("/api/new", { code: code });
    render();
    showHint();
  }

  async function guess(tok) {
    if (!state || state.is_over) return;
    state = await api("/api/guess", { token: tok });
    render();
  }

  function showHint() {
    if (state && state.hint) {
      el.hintDisplay.textContent = "💡 " + state.hint;
    } else {
      el.hintDisplay.textContent = "You've got this! 🌟";
    }
  }

  function showOverlay() {
    if (state.is_won) {
      el.overlayTitle.textContent = "🎉 You Win! 🎉";
      el.overlayImage.innerHTML = "";
      if (state.image_url) {
        const img = document.createElement("img");
        img.src = state.image_url;
        img.alt = state.word || "";
        img.className = "reward-img";
        el.overlayImage.appendChild(img);
      }
      el.overlayWord.textContent = state.word;
      el.overlayMsg.textContent = pick(WIN_MSGS);
      launchConfetti();
    } else {
      el.overlayTitle.textContent = "🌈 Good Try!";
      el.overlayImage.innerHTML = "";
      el.overlayWord.textContent = "The word was: " + (state.word || "");
      el.overlayMsg.textContent = "Don't worry - let's try a new word! 💛";
    }
    el.overlay.hidden = false;
  }

  function hideOverlay() {
    el.overlay.hidden = true;
  }

  // --- Simple confetti animation (no libraries) ---
  function launchConfetti() {
    const canvas = el.confetti;
    const ctx = canvas.getContext("2d");
    canvas.width = window.innerWidth;
    canvas.height = window.innerHeight;
    const colors = RAINBOW_COLORS.concat(["#ff8fab", "#aee9ff"]);
    const pieces = Array.from({ length: 140 }, () => ({
      x: Math.random() * canvas.width,
      y: Math.random() * -canvas.height,
      r: 5 + Math.random() * 7,
      c: pick(colors),
      vy: 2 + Math.random() * 4,
      vx: -2 + Math.random() * 4,
      rot: Math.random() * Math.PI,
      vr: -0.1 + Math.random() * 0.2,
    }));
    let frames = 0;
    function frame() {
      ctx.clearRect(0, 0, canvas.width, canvas.height);
      pieces.forEach((p) => {
        p.y += p.vy; p.x += p.vx; p.rot += p.vr;
        ctx.save();
        ctx.translate(p.x, p.y);
        ctx.rotate(p.rot);
        ctx.fillStyle = p.c;
        ctx.fillRect(-p.r / 2, -p.r / 2, p.r, p.r * 0.6);
        ctx.restore();
      });
      frames++;
      if (frames < 200) {
        requestAnimationFrame(frame);
      } else {
        ctx.clearRect(0, 0, canvas.width, canvas.height);
      }
    }
    frame();
  }

  // Keyboard support for desktop players.
  document.addEventListener("keydown", (e) => {
    if (!state || state.is_over) return;
    const k = e.key.toUpperCase();
    if (/^[A-Z]$/.test(k)) guess(k);
  });

  el.hintBtn.addEventListener("click", showHint);
  el.newBtn.addEventListener("click", newGame);
  el.overlayAgain.addEventListener("click", newGame);

  newGame();
})();
