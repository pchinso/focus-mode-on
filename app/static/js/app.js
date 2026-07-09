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
  // Show an immediate "working" state in a swap target so the UI never looks
  // frozen while a slow AI request is in flight.
  function showLoading(targetSel, label) {
    const node = document.querySelector(targetSel);
    if (!node) return;
    node.innerHTML =
      '<div class="loading" role="status" aria-live="polite">' +
      '<span class="spinner" aria-hidden="true"></span>' +
      "<span>" +
      (label || "Working…") +
      "</span></div>";
  }

  // If a swapped-in result reports that it changed the vault (data-applied),
  // refresh the whole screen so new threads/tasks appear — after briefly
  // showing the confirmation (preserved across the reload via sessionStorage).
  function maybeReloadAfter(node) {
    if (!node || !node.querySelector("[data-applied]")) return;
    try {
      sessionStorage.setItem("fmo-command-result", node.innerHTML);
    } catch (e) {
      /* ignore */
    }
    setTimeout(function () {
      window.location.reload();
    }, 1100);
  }

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
        const loading = form.getAttribute("data-loading");
        if (loading) showLoading(target, loading);
        const node = await submitSwap(
          form.action,
          "POST",
          new FormData(form),
          target
        );
        if (form.hasAttribute("data-reset")) form.reset();
        const focusSel = form.getAttribute("data-refocus");
        if (focusSel) {
          const el = form.querySelector(focusSel);
          if (el) el.focus();
        }
        maybeReloadAfter(node);
      });
    });
  }

  // Delegated handler: collapse/expand a task's subtree via its caret.
  document.addEventListener("click", (ev) => {
    const caret = ev.target.closest("[data-toggle-collapse]");
    if (!caret) return;
    ev.preventDefault();
    const item = caret.closest(".task-item");
    if (item) item.classList.toggle("collapsed");
  });

  // Delegated handler: reveal a task's inline "add subtask" form.
  document.addEventListener("click", (ev) => {
    const btn = ev.target.closest("[data-add-sub]");
    if (!btn) return;
    ev.preventDefault();
    const item = btn.closest(".task-item");
    const form = item && item.querySelector(":scope > .subtask-form");
    if (form) {
      form.hidden = !form.hidden;
      if (!form.hidden) {
        const input = form.querySelector('input[type="text"]');
        if (input) input.focus();
      }
    }
  });

  // Delegated handler: reveal a task's inline rename form (prefilled).
  document.addEventListener("click", (ev) => {
    const btn = ev.target.closest("[data-rename]");
    if (!btn) return;
    ev.preventDefault();
    const item = btn.closest(".task-item");
    const form = item && item.querySelector(":scope > .rename-form");
    if (form) {
      form.hidden = !form.hidden;
      if (!form.hidden) {
        const input = form.querySelector('input[type="text"]');
        if (input) {
          input.focus();
          input.select();
        }
      }
    }
  });

  // After a queue row is resolved, remove it; if the queue is now empty,
  // refresh the page (approved) or show a note (all discarded).
  function resolveQueueRow(item, approvedAny) {
    const queue = item.closest("#action-queue");
    item.remove();
    if (queue && !queue.querySelector("[data-queue-item]")) {
      if (approvedAny) {
        window.location.reload();
      } else {
        const form = queue.closest("form");
        if (form) form.outerHTML = '<p class="empty">All actions discarded.</p>';
      }
    }
  }

  // Delegated handler: discard one action from the review queue.
  document.addEventListener("click", (ev) => {
    const btn = ev.target.closest("[data-discard]");
    if (!btn) return;
    ev.preventDefault();
    const item = btn.closest("[data-queue-item]");
    if (item) resolveQueueRow(item, false);
  });

  // Delegated handler: discard the whole queue at once.
  document.addEventListener("click", (ev) => {
    const btn = ev.target.closest("[data-discard-all]");
    if (!btn) return;
    ev.preventDefault();
    const form = btn.closest("form");
    if (form) form.outerHTML = '<p class="empty">All actions discarded.</p>';
  });

  // Delegated handler: approve (OK) one action from the review queue.
  document.addEventListener("click", async (ev) => {
    const btn = ev.target.closest("[data-approve]");
    if (!btn) return;
    ev.preventDefault();
    const item = btn.closest("[data-queue-item]");
    if (!item) return;
    const val = (n) => {
      const el = item.querySelector("input[name='" + n + "']");
      return el ? el.value : "";
    };
    const body = new URLSearchParams();
    body.append("action", val("action"));
    body.append("thread_path", val("thread_path"));
    body.append("title", val("title"));
    btn.disabled = true;
    btn.textContent = "…";
    try {
      await fetch("/apply", {
        method: "POST",
        body: body,
        headers: { "X-Requested-With": "fetch" },
      });
    } catch (e) {
      /* ignore — the row is still removed; user can retry via Run */
    }
    resolveQueueRow(item, true);
  });

  // Command tips: hide once the user starts typing; the Examples button and
  // clicking a tip toggle/insert them.
  function syncTips() {
    const ta = document.getElementById("command-input");
    const tips = document.getElementById("command-tips");
    if (!ta || !tips) return;
    tips.hidden = ta.value.trim().length > 0;
  }

  document.addEventListener("input", (ev) => {
    if (ev.target && ev.target.id === "command-input") syncTips();
  });

  document.addEventListener("click", (ev) => {
    if (ev.target.closest("#examples-toggle")) {
      ev.preventDefault();
      const tips = document.getElementById("command-tips");
      if (tips) tips.hidden = !tips.hidden;
      return;
    }
    const tip = ev.target.closest(".tip");
    if (tip) {
      ev.preventDefault();
      const ta = document.getElementById("command-input");
      if (ta) {
        ta.value = tip.getAttribute("data-template") || tip.textContent.trim();
        ta.focus();
        syncTips();
      }
    }
  });

  // Ctrl/Cmd+Enter submits the multi-line command box (plain Enter = newline).
  document.addEventListener("keydown", (ev) => {
    if (ev.key !== "Enter" || !(ev.ctrlKey || ev.metaKey)) return;
    const ta = ev.target.closest("textarea[name='text']");
    if (!ta) return;
    const form = ta.closest("form[data-swap]");
    if (form) {
      ev.preventDefault();
      form.requestSubmit();
    }
  });

  /* ---- Dashboard search / filter ---- */
  document.addEventListener("input", (ev) => {
    if (!ev.target || ev.target.id !== "dashboard-search") return;
    const q = ev.target.value.trim().toLowerCase();
    const cards = document.querySelectorAll("#thread-cards .card");
    let shown = 0;
    cards.forEach((card) => {
      const name = (card.querySelector(".name") || {}).textContent || "";
      const match = name.toLowerCase().indexOf(q) !== -1;
      card.style.display = match ? "" : "none";
      if (match) shown++;
    });
    const empty = document.getElementById("search-empty");
    if (empty) empty.hidden = shown !== 0 || cards.length === 0;
  });

  /* ---- Command palette (Ctrl/Cmd+K) ---- */
  let paletteItems = [];
  let paletteIndex = 0;
  let paletteThreads = null;

  function paletteCommands() {
    return [
      { label: "Go to Dashboard", run: () => (window.location.href = "/") },
      { label: "Open Archive", run: () => (window.location.href = "/archive") },
      {
        label: "Switch to WORK mode",
        run: () =>
          fetch("/mode/work", { method: "POST" }).then(
            () => (window.location.href = "/")
          ),
      },
      {
        label: "Switch to PERSONAL mode",
        run: () =>
          fetch("/mode/personal", { method: "POST" }).then(
            () => (window.location.href = "/")
          ),
      },
      { label: "Toggle light/dark theme", run: toggleTheme },
    ];
  }

  async function openPalette() {
    const overlay = document.getElementById("palette-overlay");
    const input = document.getElementById("palette-input");
    if (!overlay || !input) return;
    overlay.hidden = false;
    input.value = "";
    input.focus();
    if (paletteThreads === null) {
      try {
        const resp = await fetch("/threads.json", {
          headers: { "X-Requested-With": "fetch" },
        });
        const data = await resp.json();
        paletteThreads = (data.threads || []).map((t) => ({
          label: t.title + "  ·  " + t.path,
          run: () => (window.location.href = "/thread/" + t.path),
        }));
      } catch (e) {
        paletteThreads = [];
      }
    }
    renderPalette("");
  }

  function closePalette() {
    const overlay = document.getElementById("palette-overlay");
    if (overlay) overlay.hidden = true;
  }

  function renderPalette(query) {
    const list = document.getElementById("palette-list");
    if (!list) return;
    const all = paletteCommands().concat(paletteThreads || []);
    const q = query.trim().toLowerCase();
    paletteItems = q
      ? all.filter((i) => i.label.toLowerCase().indexOf(q) !== -1)
      : all;
    paletteIndex = 0;
    list.innerHTML = paletteItems
      .map(
        (i, n) =>
          '<li class="palette-item' +
          (n === 0 ? " sel" : "") +
          '" data-i="' +
          n +
          '">' +
          i.label.replace(/</g, "&lt;") +
          "</li>"
      )
      .join("");
  }

  function paletteMove(delta) {
    if (!paletteItems.length) return;
    paletteIndex = (paletteIndex + delta + paletteItems.length) % paletteItems.length;
    const list = document.getElementById("palette-list");
    if (!list) return;
    list.querySelectorAll(".palette-item").forEach((el, n) => {
      el.classList.toggle("sel", n === paletteIndex);
      if (n === paletteIndex) el.scrollIntoView({ block: "nearest" });
    });
  }

  function paletteActivate() {
    const item = paletteItems[paletteIndex];
    closePalette();
    if (item) item.run();
  }

  document.addEventListener("keydown", (ev) => {
    if ((ev.ctrlKey || ev.metaKey) && (ev.key === "k" || ev.key === "K")) {
      ev.preventDefault();
      openPalette();
      return;
    }
    const overlay = document.getElementById("palette-overlay");
    if (!overlay || overlay.hidden) return;
    if (ev.key === "ArrowDown") {
      ev.preventDefault();
      paletteMove(1);
    } else if (ev.key === "ArrowUp") {
      ev.preventDefault();
      paletteMove(-1);
    } else if (ev.key === "Enter") {
      ev.preventDefault();
      paletteActivate();
    } else if (ev.key === "Escape") {
      ev.preventDefault();
      closePalette();
    }
  });

  document.addEventListener("input", (ev) => {
    if (ev.target && ev.target.id === "palette-input") renderPalette(ev.target.value);
  });

  document.addEventListener("click", (ev) => {
    const li = ev.target.closest(".palette-item");
    if (li) {
      paletteIndex = parseInt(li.getAttribute("data-i"), 10) || 0;
      paletteActivate();
      return;
    }
    // Click outside the panel closes the palette.
    const overlay = document.getElementById("palette-overlay");
    if (overlay && !overlay.hidden && ev.target === overlay) closePalette();
  });

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
      const loading = el.getAttribute("data-loading");
      if (loading) showLoading(target, loading);
      const node = await submitSwap(
        el.getAttribute("data-post"),
        "POST",
        body,
        target
      );
      maybeReloadAfter(node);
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

  // Trigger the toggle (checkbox) inside a focused task row.
  function clickToggle(row) {
    if (!row) return;
    const toggle = row.querySelector("[data-post]");
    if (toggle) toggle.click();
  }

  // Collapse or expand the subtree of a focused task row.
  function setCollapsed(row, collapsed) {
    if (!row) return;
    const item = row.closest(".task-item");
    if (!item || !item.querySelector(":scope > .subtasks")) return;
    item.classList.toggle("collapsed", collapsed);
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
          if (item.dataset.nav === "task") clickToggle(item);
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
          clickToggle(item);
        }
        break;
      }
      case "ArrowRight":
        setCollapsed(activeItem(), false);
        break;
      case "ArrowLeft":
        setCollapsed(activeItem(), true);
        break;
      case "+":
      case "s": {
        // Add a subtask under the focused task.
        const item = activeItem();
        const btn = item && item.querySelector("[data-add-sub]");
        if (btn) {
          ev.preventDefault();
          btn.click();
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
      case "m": {
        const form = document.getElementById("mode-toggle-form");
        if (form) {
          ev.preventDefault();
          form.submit();
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
    // Restore a command confirmation that survived a post-command reload.
    try {
      const saved = sessionStorage.getItem("fmo-command-result");
      if (saved) {
        const cr = document.getElementById("command-result");
        if (cr) cr.innerHTML = saved;
        sessionStorage.removeItem("fmo-command-result");
      }
    } catch (e) {
      /* ignore */
    }
    // Undo toast: dismiss on click or after a few seconds.
    const toast = document.getElementById("toast");
    if (toast) {
      const close = document.getElementById("toast-close");
      if (close) close.addEventListener("click", () => (toast.hidden = true));
      setTimeout(() => {
        toast.hidden = true;
      }, 7000);
    }
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
