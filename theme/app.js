/* ==========================================================================
   Rashed Hindash — behaviour
   No libraries. Roughly 4KB. Everything degrades if it fails to load.
   ========================================================================== */

(function () {
  "use strict";

  var root = document.documentElement;
  var reduced = window.matchMedia("(prefers-reduced-motion: reduce)").matches;

  /* ---- theme toggle --------------------------------------------------- */

  function systemTheme() {
    return window.matchMedia("(prefers-color-scheme: light)").matches ? "light" : "dark";
  }

  function currentTheme() {
    return root.getAttribute("data-theme") || systemTheme();
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
