/* Focus Mode On — client behavior.
 *
 * Three small, dependency-free layers:
 *   1. Theme     — persist and toggle light/dark.
 *   2. Swap      — progressive-enhancement AJAX for forms/buttons.
 *   3. Keyboard  — full keyboard navigation of cards and tasks.
 */
(function () {
  "use strict";

  /* ---- 1. Theme ---- */
  const THEME_KEY = "focus-theme";

  function applyTheme(theme) {
    document.documentElement.setAttribute("data-theme", theme);
    try {
      localStorage.setItem(THEME_KEY, theme);
    } catch (e) {
      /* storage may be unavailable; ignore */
    }
  }

  function toggleTheme() {
    const current =
      document.documentElement.getAttribute("data-theme") ||
      (window.matchMedia("(prefers-color-scheme: dark)").matches
        ? "dark"
        : "light");
    applyTheme(current === "dark" ? "light" : "dark");
  }

  /* ---- 2. AJAX swap ---- */
  // A form/button with data-swap="#id" posts and replaces #id's innerHTML.
  async function submitSwap(url, method, body, target) {
    const resp = await fetch(url, {
      method: method,
      body: body,
      headers: { "X-Requested-With": "fetch" },
    });
    const html = await resp.text();
    const node = document.querySelector(target);
    if (node) {
      node.innerHTML = html;
      indexNavItems();
    }
    return node;
  }

  function wireSwaps(root) {
    root.querySelectorAll("form[data-swap]").forEach((form) => {
      if (form.dataset.wired) return;
      form.dataset.wired = "1";
      form.addEventListener("submit", async (ev) => {
        ev.preventDefault();
        const target = form.getAttribute("data-swap");
        await submitSwap(form.action, "POST", new FormData(form), target);
        if (form.hasAttribute("data-reset")) form.reset();
        const focusSel = form.getAttribute("data-refocus");
        if (focusSel) {
          const el = form.querySelector(focusSel);
          if (el) el.focus();
        }
      });
    });
  }

  // Delegated handler for elements that post on click (task toggles, confirms).
  document.addEventListener("click", async (ev) => {
    const el = ev.target.closest("[data-post]");
    if (!el) return;
    ev.preventDefault();
    const target = el.getAttribute("data-swap");
    const body = new FormData();
    (el.getAttribute("data-fields") || "")
      .split("&")
      .filter(Boolean)
      .forEach((pair) => {
        const [k, v] = pair.split("=");
        body.append(decodeURIComponent(k), decodeURIComponent(v || ""));
      });
    if (target) {
      await submitSwap(el.getAttribute("data-post"), "POST", body, target);
    }
  });

  /* ---- 3. Keyboard navigation ---- */
  let navItems = [];
  let navIndex = -1;

  function indexNavItems() {
    navItems = Array.from(document.querySelectorAll("[data-nav]")).filter(
      (el) => el.offsetParent !== null
    );
    if (navIndex >= navItems.length) navIndex = navItems.length - 1;
    highlight();
  }

  function highlight() {
    navItems.forEach((el, i) => el.classList.toggle("kbd-active", i === navIndex));
    if (navIndex >= 0 && navItems[navIndex]) {
      navItems[navIndex].scrollIntoView({ block: "nearest" });
    }
  }

  function move(delta) {
    if (!navItems.length) return;
    navIndex = (navIndex + delta + navItems.length) % navItems.length;
    highlight();
  }

  function activeItem() {
    return navIndex >= 0 ? navItems[navIndex] : null;
  }

  function isTyping(ev) {
    const t = ev.target;
    return (
      t &&
      (t.tagName === "INPUT" || t.tagName === "TEXTAREA" || t.isContentEditable)
    );
  }

  function focusCommand() {
    const bar = document.getElementById("command-input");
    if (bar) {
      bar.focus();
      bar.select();
    }
  }

  function focusAddTask() {
    const add = document.getElementById("task-input");
    if (add) add.focus();
  }

  function toggleHelp(force) {
    const overlay = document.getElementById("help-overlay");
    if (!overlay) return;
    const show = force !== undefined ? force : overlay.hidden;
    overlay.hidden = !show;
  }

  document.addEventListener("keydown", (ev) => {
    // Global escape works even while typing.
    if (ev.key === "Escape") {
      const overlay = document.getElementById("help-overlay");
      if (overlay && !overlay.hidden) {
        toggleHelp(false);
        return;
      }
      if (isTyping(ev)) {
        ev.target.blur();
        return;
      }
    }

    if (isTyping(ev)) return;

    switch (ev.key) {
      case "j":
      case "ArrowDown":
        ev.preventDefault();
        move(1);
        break;
      case "k":
      case "ArrowUp":
        ev.preventDefault();
        move(-1);
        break;
      case "Enter": {
        const item = activeItem();
        if (item) {
          ev.preventDefault();
          if (item.dataset.nav === "task") item.click();
          else if (item.href) window.location.href = item.href;
          else item.click();
        }
        break;
      }
      case " ":
      case "x": {
        const item = activeItem();
        if (item && item.dataset.nav === "task") {
          ev.preventDefault();
          item.click();
        }
        break;
      }
      case "/":
        ev.preventDefault();
        focusCommand();
        break;
      case "a":
        ev.preventDefault();
        focusAddTask();
        break;
      case "c": {
        const btn = document.getElementById("complete-thread");
        if (btn) {
          ev.preventDefault();
          btn.click();
        }
        break;
      }
      case "?":
        ev.preventDefault();
        toggleHelp();
        break;
      default:
        break;
    }
  });

  /* ---- init ---- */
  document.addEventListener("DOMContentLoaded", () => {
    const toggle = document.getElementById("theme-toggle");
    if (toggle) toggle.addEventListener("click", toggleTheme);
    const closeHelp = document.getElementById("help-close");
    if (closeHelp) closeHelp.addEventListener("click", () => toggleHelp(false));
    wireSwaps(document);
    indexNavItems();
    // Re-wire swaps for content injected later.
    new MutationObserver(() => wireSwaps(document)).observe(document.body, {
      childList: true,
      subtree: true,
    });
  });

  window.FocusMode = { toggleTheme: toggleTheme };
})();
