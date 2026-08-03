/* ==========================================================================
   Rashed Hindash: behaviour
   No libraries. Roughly 4KB. Everything degrades if it fails to load.
   ========================================================================== */

(function () {
  "use strict";

  var root = document.documentElement;
  var reduced = window.matchMedia("(prefers-reduced-motion: reduce)").matches;

  /* ---- theme toggle --------------------------------------------------- */

  /* Dark unless the visitor has explicitly chosen otherwise. */
  function currentTheme() {
    return root.getAttribute("data-theme") || "dark";
  }

  var themeBtn = document.querySelector("[data-theme-toggle]");
  if (themeBtn) {
    themeBtn.addEventListener("click", function () {
      var next = currentTheme() === "dark" ? "light" : "dark";

      var apply = function () {
        root.setAttribute("data-theme", next);
        try { localStorage.setItem("theme", next); } catch (e) {}
      };

      // Let the browser cross-fade the whole page if it can.
      if (document.startViewTransition && !reduced) {
        document.startViewTransition(apply);
      } else {
        apply();
      }
    });
  }

  /* ---- mobile menu ---------------------------------------------------- */

  var menuBtn = document.querySelector("[data-menu-toggle]");
  var sheet = document.querySelector("[data-menu]");

  function closeMenu() {
    if (!sheet || sheet.hidden) return;
    sheet.classList.remove("is-open");
    menuBtn.setAttribute("aria-expanded", "false");
    document.body.style.overflow = "";
    window.setTimeout(function () { sheet.hidden = true; }, 260);
  }

  if (menuBtn && sheet) {
    menuBtn.addEventListener("click", function () {
      var open = menuBtn.getAttribute("aria-expanded") === "true";
      if (open) {
        closeMenu();
      } else {
        sheet.hidden = false;
        // next frame, so the opacity transition actually runs
        requestAnimationFrame(function () { sheet.classList.add("is-open"); });
        menuBtn.setAttribute("aria-expanded", "true");
        document.body.style.overflow = "hidden";
      }
    });

    sheet.addEventListener("click", function (event) {
      if (event.target.closest("a")) closeMenu();
    });

    document.addEventListener("keydown", function (event) {
      if (event.key === "Escape") closeMenu();
    });
  }

  /* ---- replay the brand bounce when the ball is clicked ---------------- */

  var ball = document.querySelector(".brand-ball");

  if (ball && !reduced) {
    ball.addEventListener("click", function (event) {
      // The ball sits inside the home link, so stop the click navigating.
      event.preventDefault();
      event.stopPropagation();

      [ball, ball.querySelector("i")].forEach(function (el) {
        if (!el) return;
        el.style.animation = "none";
        void el.offsetWidth; // force a reflow so the animation starts over
        el.style.animation = "";
      });
    });
  }

  /* ---- header state on scroll ----------------------------------------- */

  var head = document.querySelector("[data-head]");
  if (head) {
    var ticking = false;
    var onScroll = function () {
      if (ticking) return;
      ticking = true;
      requestAnimationFrame(function () {
        head.classList.toggle("is-stuck", window.scrollY > 12);
        ticking = false;
      });
    };
    window.addEventListener("scroll", onScroll, { passive: true });
    onScroll();
  }

  /* ---- reveal on scroll ----------------------------------------------- */

  var targets = document.querySelectorAll("[data-reveal]");

  if (!("IntersectionObserver" in window) || reduced) {
    Array.prototype.forEach.call(targets, function (el) { el.classList.add("is-in"); });
  } else {
    var observer = new IntersectionObserver(function (entries) {
      entries.forEach(function (entry) {
        if (!entry.isIntersecting) return;
        entry.target.classList.add("is-in");
        observer.unobserve(entry.target);
      });
    }, { rootMargin: "0px 0px -8% 0px", threshold: 0.06 });

    Array.prototype.forEach.call(targets, function (el) { observer.observe(el); });
  }

  /* ---- counts: downloads on rigs, views on videos ---------------------- */

  /* Base URL of the counts service. While this is empty every slot stays
     hidden and nothing is requested, so the page looks exactly as it did
     before counting existed. */
  var COUNT_API = "https://site-counts.rashed-hindash.workers.dev";

  var countSlots = {};

  /* Below this a figure says more about how new the page is than about the
     work, so it stays hidden. Nothing is invented to fill the gap; the
     counter simply appears once it carries information. */
  var COUNT_MIN = 1;

  /* KV serves reads from an edge cache that can lag a write by up to a
     minute, so a figure fetched just after a hit can come back lower than
     the one the visitor already saw. Keep the highest value seen for each
     key and never render a number going backwards. */
  function highest(key, value) {
    try {
      var prev = parseInt(localStorage.getItem("c2:" + key), 10);
      if (!isNaN(prev) && prev > value) return prev;
      localStorage.setItem("c2:" + key, String(value));
    } catch (e) {}
    return value;
  }

  function renderCount(key, value) {
    var slots = countSlots[key];
    if (!slots || typeof value !== "number" || value < 0) return;

    value = highest(key, value);
    if (value < COUNT_MIN) return;

    var noun = key.indexOf("rig:") === 0 ? "download" : "view";
    var text = value.toLocaleString("en-US") + " " + noun + (value === 1 ? "" : "s");

    Array.prototype.forEach.call(slots, function (el) {
      el.textContent = text;
      el.removeAttribute("hidden");
    });
  }

  function bumpCount(key) {
    var slots = countSlots[key];
    if (!slots || !slots.length) return;
    /* Read once and render once. Reading per slot would compound the
       increment on any page showing the same key twice. */
    var current = parseInt((slots[0].textContent || "").replace(/[^0-9]/g, ""), 10);
    /* While a count is still below the display threshold there is no figure
       on screen to read, so fall back to the last value we were told. */
    if (isNaN(current)) {
      try { current = parseInt(localStorage.getItem("c2:" + key), 10); } catch (e) {}
    }
    if (!isNaN(current)) renderCount(key, current + 1);
  }

  if (COUNT_API) {
    Array.prototype.forEach.call(document.querySelectorAll("[data-count]"), function (el) {
      var key = el.getAttribute("data-count");
      if (!key) return;
      if (!countSlots[key]) countSlots[key] = [];
      countSlots[key].push(el);
    });

    var keys = Object.keys(countSlots);

    if (keys.length && window.fetch) {
      fetch(COUNT_API + "/counts?keys=" + encodeURIComponent(keys.join(",")), {
        mode: "cors", credentials: "omit"
      })
        .then(function (r) { return r.ok ? r.json() : null; })
        .then(function (data) {
          if (!data) return;
          Object.keys(data).forEach(function (key) { renderCount(key, data[key]); });
        })
        .catch(function () { /* stay hidden, say nothing */ });
    }

    /* One hit per activation, counted every time. Repeats are deliberate. */
    document.addEventListener("click", function (event) {
      var target = event.target.closest("[data-hit]");
      if (!target) return;

      var key = target.getAttribute("data-hit");
      if (!key) return;

      bumpCount(key);

      var url = COUNT_API + "/hit/" + encodeURIComponent(key);
      /* sendBeacon survives the navigation a download link triggers. */
      if (navigator.sendBeacon) navigator.sendBeacon(url);
      else if (window.fetch) {
        fetch(url, { method: "POST", mode: "cors", credentials: "omit", keepalive: true })
          .catch(function () {});
      }
    });
  }

  /* ---- video embeds: load the iframe only when asked ------------------- */

  document.addEventListener("click", function (event) {
    var button = event.target.closest(".embed-play");
    if (!button) return;

    var src = button.getAttribute("data-embed");
    if (!src) return;

    var frame = document.createElement("iframe");
    frame.src = src;
    frame.title = "Video";
    frame.loading = "lazy";
    frame.allow = "autoplay; fullscreen; picture-in-picture; encrypted-media";
    frame.setAttribute("allowfullscreen", "");
    frame.setAttribute("referrerpolicy", "strict-origin-when-cross-origin");

    button.replaceWith(frame);
  });

  /* ---- hover previews on work cards ----------------------------------- */

  Array.prototype.forEach.call(document.querySelectorAll(".card"), function (card) {
    var clip = card.querySelector(".card-preview");
    if (!clip || reduced) return;

    card.addEventListener("pointerenter", function () {
      if (!clip.getAttribute("data-loaded")) {
        clip.load();
        clip.setAttribute("data-loaded", "1");
      }
      var playing = clip.play();
      if (playing && playing.catch) playing.catch(function () {});
    });

    card.addEventListener("pointerleave", function () {
      clip.pause();
      clip.currentTime = 0;
    });
  });

  /* ---- prefetch on hover, so navigation feels instant ------------------ */

  var prefetched = {};
  var slowConnection = navigator.connection &&
    (navigator.connection.saveData || /2g/.test(navigator.connection.effectiveType || ""));

  if (!slowConnection) {
    document.addEventListener("pointerover", function (event) {
      var link = event.target.closest("a[href]");
      if (!link) return;
      var href = link.getAttribute("href");
      if (!href || href.charAt(0) === "#" || link.target === "_blank") return;
      if (link.origin !== window.location.origin) return;
      if (prefetched[link.href]) return;

      prefetched[link.href] = true;
      var hint = document.createElement("link");
      hint.rel = "prefetch";
      hint.href = link.href;
      document.head.appendChild(hint);
    }, { passive: true });
  }

  /* ---- mark the page as alive (see the failsafe in <head>) ------------- */

  root.setAttribute("data-ready", "1");
})();
