/* Litera front-end behaviour.
 *
 * Rules this file follows, after the previous version broke several of them:
 *   1. Nothing here is required for content to be readable. Every reveal effect
 *      is additive: the hidden state is only ever applied by JS, so with JS off
 *      (or on error) the page renders fully visible.
 *   2. No initialiser assumes its target exists. Each one returns early.
 *   3. No initialiser is kept for a page that no longer exists.
 */
(function () {
  "use strict";

  var reduceMotion =
    window.matchMedia &&
    window.matchMedia("(prefers-reduced-motion: reduce)").matches;

  /* ---------------------------------------------------------------- utils */

  function each(selector, fn, root) {
    var nodes = (root || document).querySelectorAll(selector);
    Array.prototype.forEach.call(nodes, fn);
  }

  function onScroll(fn) {
    var queued = false;
    function handler() {
      if (queued) return;
      queued = true;
      window.requestAnimationFrame(function () {
        queued = false;
        fn();
      });
    }
    window.addEventListener("scroll", handler, { passive: true });
    handler();
  }

  /* --------------------------------------------------- reading progress */
  /* Drives #progress-bar (site default) and #scrollProgress (readers).
   * The old version also hijacked any `.h-full.bg-primary` inside an element
   * with `.bg-outline-variant`, which silently animated the chapter-position
   * meter as if it were a scroll bar. Removed. */

  function initScrollProgress() {
    var bars = [
      document.getElementById("progress-bar"),
      document.getElementById("scrollProgress"),
    ].filter(Boolean);

    if (!bars.length) return;

    onScroll(function () {
      var doc = document.documentElement;
      var scrollable = doc.scrollHeight - doc.clientHeight;
      var percent = scrollable > 0 ? (doc.scrollTop / scrollable) * 100 : 0;
      bars.forEach(function (bar) {
        bar.style.width = percent.toFixed(2) + "%";
      });
    });
  }

  /* ------------------------------------------------------------ navbar */

  function initNavbarScroll() {
    var nav = document.getElementById("main-nav");
    if (!nav) return;

    var scrolled = ["bg-white/80", "backdrop-blur-lg", "shadow-sm"];

    onScroll(function () {
      var isScrolled = window.scrollY > 8;
      scrolled.forEach(function (cls) {
        nav.classList.toggle(cls, isScrolled);
      });
      nav.classList.toggle("bg-surface", !isScrolled);
    });
  }

  /* ------------------------------------------------------- reveal effects */
  /* Additive: if IntersectionObserver is missing or motion is reduced, the
   * hidden classes are never applied at all. */

  function revealOnScroll(selector, hiddenClasses, options) {
    var nodes = document.querySelectorAll(selector);
    if (!nodes.length) return;
    if (reduceMotion || !("IntersectionObserver" in window)) return;

    var observer = new IntersectionObserver(
      function (entries) {
        entries.forEach(function (entry) {
          if (!entry.isIntersecting) return;
          hiddenClasses.forEach(function (cls) {
            entry.target.classList.remove(cls);
          });
          observer.unobserve(entry.target);
        });
      },
      options || { threshold: 0.1, rootMargin: "0px 0px -40px 0px" }
    );

    Array.prototype.forEach.call(nodes, function (node, index) {
      node.classList.add("transition-all", "duration-700", "ease-out");
      hiddenClasses.forEach(function (cls) {
        node.classList.add(cls);
      });
      node.style.transitionDelay = Math.min(index, 6) * 60 + "ms";
      observer.observe(node);
    });
  }

  function initBentoCards() {
    revealOnScroll(".bento-card", ["opacity-0", "translate-y-10"]);
  }

  function initFadeInSections() {
    revealOnScroll(".legal-content section, .fade-on-scroll", [
      "opacity-0",
      "translate-y-4",
    ]);
  }

  /* Dims strophes that are not in view, in the chapter reader. Uses a class
   * rather than an inline style so CSS keeps control of the value, and does
   * nothing at all when motion is reduced. */
  function initStanzaReveal() {
    var stanzas = document.querySelectorAll("[data-stanza]");
    if (!stanzas.length) return;
    if (reduceMotion || !("IntersectionObserver" in window)) return;

    var observer = new IntersectionObserver(
      function (entries) {
        entries.forEach(function (entry) {
          entry.target.classList.toggle("stanza-dim", !entry.isIntersecting);
        });
      },
      { threshold: 0.25, rootMargin: "-15% 0px -25% 0px" }
    );

    Array.prototype.forEach.call(stanzas, function (node) {
      observer.observe(node);
    });
  }

  /* -------------------------------------------------------- stanza cards */
  /* The markup previously carried an inline onclick that also toggled
   * .is-flipped, so a click fired twice and cancelled itself. The inline
   * handler is gone; this is the only place the class is toggled. */

  function initStanzaCards() {
    each("[data-stanza-flip]", function (card) {
      function toggle() {
        var flipped = card.classList.toggle("is-flipped");
        card.setAttribute("aria-expanded", flipped ? "true" : "false");
      }

      card.addEventListener("click", toggle);
      card.addEventListener("keydown", function (event) {
        if (event.key !== "Enter" && event.key !== " ") return;
        event.preventDefault();
        toggle();
      });
    });
  }

  /* ------------------------------------------------------ chapter select */

  function initChapterSelect() {
    each("[data-chapter-select]", function (select) {
      select.addEventListener("change", function () {
        if (select.value) window.location.href = select.value;
      });
    });
  }

  /* ------------------------------------------------------ password toggle */

  function initPasswordToggles() {
    each("[data-password-toggle]", function (button) {
      var wrapper = button.closest(".relative") || button.parentElement;
      if (!wrapper) return;
      var input = wrapper.querySelector("input");
      if (!input) return;

      button.addEventListener("click", function () {
        var show = input.type === "password";
        input.type = show ? "text" : "password";
        button.setAttribute("aria-label", show ? "Hide password" : "Show password");
        var icon = button.querySelector(".material-symbols-outlined");
        if (icon) icon.textContent = show ? "visibility_off" : "visibility";
      });
    });
  }

  /* -------------------------------------------------------------- flashes */

  function initFlashDismiss() {
    each(".auth-flash", function (flash) {
      flash.addEventListener("click", function () {
        flash.remove();
      });
      window.setTimeout(function () {
        flash.classList.add("is-leaving");
        window.setTimeout(function () {
          flash.remove();
        }, 400);
      }, 6000);
    });
  }

  /* ------------------------------------------------------ smooth anchors */

  function initSmoothAnchors() {
    each('a[href^="#"]', function (link) {
      link.addEventListener("click", function (event) {
        var id = link.getAttribute("href");
        if (!id || id === "#") return;
        var target = document.querySelector(id);
        if (!target) return;
        event.preventDefault();
        target.scrollIntoView({
          behavior: reduceMotion ? "auto" : "smooth",
          block: "start",
        });
      });
    });
  }

  /* ---------------------------------------------------------------- boot */

  function boot() {
    document.documentElement.classList.add("js");

    initScrollProgress();
    initNavbarScroll();
    initBentoCards();
    initFadeInSections();
    initStanzaReveal();
    initStanzaCards();
    initChapterSelect();
    initPasswordToggles();
    initFlashDismiss();
    initSmoothAnchors();
  }

  if (document.readyState === "loading") {
    document.addEventListener("DOMContentLoaded", boot);
  } else {
    boot();
  }
})();
