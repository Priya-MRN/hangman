/* Hangman for Kids - front-end game controller.
   Talks to the Flask JSON API and renders a joyful, responsive UI. */

(function () {
  "use strict";

  const code = document.body.dataset.code;
  const RAINBOW_COLORS = ["#ff5d5d", "#ff9f45", "#ffd23f", "#7bd389", "#5aa9e6", "#b388eb"];
  const MAX = 6;

  const reduceMotion = window.matchMedia &&
    window.matchMedia("(prefers-reduced-motion: reduce)").matches;

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
  let prevState = null; // snapshot before the last guess, for diffing
  let loading = false;

  function pick(arr) {
    return arr[Math.floor(Math.random() * arr.length)];
  }

  // --- Loading state while /api/new is in flight -----------------------------
  function showLoading() {
    loading = true;
    el.word.innerHTML = "";
    el.word.dir = "ltr";
    // A friendly row of shimmering skeleton tiles.
    for (let i = 0; i < 5; i++) {
      const span = document.createElement("span");
      span.className = "tile skeleton";
      el.word.appendChild(span);
    }
    el.message.innerHTML =
      '<span class="loading">Getting a new word ready' +
      '<span class="dots" aria-hidden="true"><i></i><i></i><i></i></span></span>';
    el.keyboard.innerHTML = "";
    el.rainbow.innerHTML = "";
    el.hearts.textContent = "";
    el.hintDisplay.textContent = "";
  }

  function renderWord() {
    // Which positions were still hidden before this guess? Those newly filled
    // tiles get a satisfying pop.
    const prevMasked = prevState ? prevState.masked : null;
    el.word.innerHTML = "";
    el.word.dir = state.direction || "ltr";
    state.masked.forEach((tok, i) => {
      const span = document.createElement("span");
      if (tok === "_") {
        span.className = "tile blank";
      } else {
        span.className = "tile";
        span.textContent = tok;
        const wasHidden = prevMasked && prevMasked[i] === "_";
        if (wasHidden && !reduceMotion) span.classList.add("reveal");
      }
      el.word.appendChild(span);
    });
  }

  function renderRainbow() {
    const prevWrong = prevState ? prevState.wrong_count : 0;
    el.rainbow.innerHTML = "";
    const wrong = state.wrong_count;
    for (let i = 0; i < MAX; i++) {
      const band = document.createElement("div");
      band.className = "band" + (i < wrong ? " on" : "");
      // The band that just lit up gets a celebratory pop.
      if (i < wrong && i >= prevWrong && !reduceMotion) band.classList.add("pop");
      const size = 236 - i * 34;
      band.style.width = size + "px";
      band.style.height = size / 2 + "px";
      band.style.borderColor = RAINBOW_COLORS[i];
      band.style.borderWidth = "16px";
      el.rainbow.appendChild(band);
    }
    const left = state.remaining;
    el.hearts.innerHTML = "";
    const lostNow = prevState ? (prevState.remaining - left) : 0;
    for (let i = 0; i < MAX; i++) {
      const heart = document.createElement("span");
      if (i < left) {
        heart.textContent = "❤️";
      } else {
        heart.textContent = "🤍";
        // Animate only the heart(s) lost on this guess.
        if (i >= left && i < left + lostNow && !reduceMotion) {
          heart.className = "heart-lost";
        }
      }
      el.hearts.appendChild(heart);
    }
  }

  function renderKeyboard() {
    el.keyboard.innerHTML = "";
    el.keyboard.dir = state.direction || "ltr";
    state.keyboard.forEach((tok) => {
      const btn = document.createElement("button");
      btn.className = "key";
      btn.textContent = tok;
      btn.type = "button";
      btn.setAttribute("aria-label", "Guess " + tok);
      const guessed = state.guessed.includes(tok) ||
        state.guessed.includes(tok.toUpperCase());
      if (guessed) {
        btn.disabled = true;
        btn.classList.add(state.wrong.includes(tok) ||
          state.wrong.includes(tok.toUpperCase()) ? "wrong" : "correct");
      }
      if (state.is_over) btn.disabled = true;
      btn.addEventListener("click", () => guess(tok, btn));
      el.keyboard.appendChild(btn);
    });
  }

  function render() {
    loading = false;
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
    prevState = null;
    showLoading();
    try {
      state = await api("/api/new", { code: code });
    } catch (err) {
      loading = false;
      el.message.textContent = "😅 Oops! Couldn't load. Tap 🔄 to try again.";
      return;
    }
    render();
    showHint();
  }

  async function guess(tok, btn) {
    if (!state || state.is_over || loading) return;
    // Instant tap feedback before the round-trip completes.
    if (btn && !reduceMotion) {
      btn.classList.remove("tapped");
      void btn.offsetWidth; // restart animation
      btn.classList.add("tapped");
    }
    prevState = state;
    state = await api("/api/guess", { token: tok });
    render();
    // A wrong guess shakes the word row.
    const gotWorse = state.wrong_count > (prevState ? prevState.wrong_count : 0);
    if (gotWorse && !state.is_over && !reduceMotion) {
      el.word.classList.remove("shake");
      void el.word.offsetWidth;
      el.word.classList.add("shake");
    }
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
    if (reduceMotion) return;
    const canvas = el.confetti;
    const ctx = canvas.getContext("2d");
    canvas.width = window.innerWidth;
    canvas.height = window.innerHeight;
    const colors = RAINBOW_COLORS.concat(["#ff8fab", "#aee9ff"]);
    const shapes = ["rect", "circle", "strip"];
    // A staggered burst feels more alive than everything falling at once.
    const pieces = Array.from({ length: 160 }, () => ({
      x: Math.random() * canvas.width,
      y: Math.random() * -canvas.height,
      r: 5 + Math.random() * 8,
      c: pick(colors),
      shape: pick(shapes),
      vy: 2 + Math.random() * 4,
      vx: -2.2 + Math.random() * 4.4,
      rot: Math.random() * Math.PI,
      vr: -0.14 + Math.random() * 0.28,
      sway: Math.random() * Math.PI * 2,
      swaySpeed: 0.02 + Math.random() * 0.04,
    }));
    let frames = 0;
    const TOTAL = 220;
    function frame() {
      ctx.clearRect(0, 0, canvas.width, canvas.height);
      const fade = frames > TOTAL - 40 ? (TOTAL - frames) / 40 : 1;
      ctx.globalAlpha = Math.max(0, fade);
      pieces.forEach((p) => {
        p.sway += p.swaySpeed;
        p.y += p.vy;
        p.x += p.vx + Math.sin(p.sway) * 0.8;
        p.rot += p.vr;
        ctx.save();
        ctx.translate(p.x, p.y);
        ctx.rotate(p.rot);
        ctx.fillStyle = p.c;
        if (p.shape === "circle") {
          ctx.beginPath();
          ctx.arc(0, 0, p.r / 2, 0, Math.PI * 2);
          ctx.fill();
        } else if (p.shape === "strip") {
          ctx.fillRect(-p.r / 2, -p.r / 4, p.r, p.r * 0.35);
        } else {
          ctx.fillRect(-p.r / 2, -p.r / 2, p.r, p.r * 0.6);
        }
        ctx.restore();
      });
      ctx.globalAlpha = 1;
      frames++;
      if (frames < TOTAL) {
        requestAnimationFrame(frame);
      } else {
        ctx.clearRect(0, 0, canvas.width, canvas.height);
      }
    }
    frame();
  }

  // Keyboard support for desktop players.
  document.addEventListener("keydown", (e) => {
    if (!state || state.is_over || loading) return;
    const k = e.key.toUpperCase();
    if (/^[A-Z]$/.test(k)) {
      // Light up the matching on-screen key for consistent feedback.
      const btn = Array.from(el.keyboard.querySelectorAll(".key"))
        .find((b) => b.textContent === k && !b.disabled);
      guess(k, btn);
    }
  });

  el.hintBtn.addEventListener("click", showHint);
  el.newBtn.addEventListener("click", newGame);
  el.overlayAgain.addEventListener("click", newGame);

  newGame();
})();
