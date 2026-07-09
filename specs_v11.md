# Focus Mode On — v1.1 Specification (Features and UI)

> Forward-looking spec that builds on the shipped v1.0 (see [spec.md](spec.md)).
> It proposes the next set of features and a UI refresh. Nothing here changes
> the core principle: the Markdown vault stays the single source of truth and
> every `.md` file remains readable outside the app.

| Field | Value |
| --- | --- |
| Document | specs_v11.md — v1.1 proposal |
| Builds on | v1.0 (vault engine, AI review queue, modes, nested tasks) |
| Status | Draft / for review |

---

## 1. Goals for v1.1

- Make the app faster to drive and easier to read at a glance.
- Reduce friction in the AI review queue and in everyday task edits.
- Polish the visual identity (app logo, refined surfaces, motion) without
  breaking light/dark or the Cox tokens.
- Add the first reporting/export capability from the v1.0 roadmap.

---

## 2. Proposed Features

### 2.1 Command palette and search

- A `Ctrl`/`Cmd`+`K` **command palette** to jump to any thread by fuzzy name,
  switch mode, toggle theme, or open help — without leaving the keyboard.
- **Search/filter** on the dashboard: type to filter the visible thread cards
  and their pending tasks by text.

### 2.2 Editing tasks and threads

- **Rename** a task or thread inline (currently tasks are create/toggle only).
- **Reorder** sibling tasks and threads by drag or `Shift`+`J`/`K`, persisted
  to the `.md` order.
- **Move** a thread under a different parent (re-parent), updating the folder
  path and breadcrumb.
- **Delete** with an undo toast (soft-delete into `_archive/` like completion).
- **Task age**: each task records its creation date with an Obsidian-compatible
  `➕ YYYY-MM-DD` stamp; the UI shows how old a pending task is (e.g. "5d") so
  stale pending items are easy to find, and old ones are visually emphasized.

### 2.3 AI review queue improvements

- **Approve all / Discard all** buttons in addition to per-action controls.
- **Edit before approve**: tweak a queued action's title/target inline prior to
  OK, so a near-miss from the model is fixable without retyping the note.
- **Grouping**: queued actions grouped by target thread for long notes.

### 2.4 Reporting and export

- **HTML report** of a thread (or a whole mode) with the Cox visual identity,
  suitable for sharing or printing — the v1.0 roadmap item, now specified:
  a themed, self-contained `.html` with the thread tree and task states.

### 2.5 Tree overview (Family-Tree view)

- A dedicated **`/tree`** page giving a single hierarchical overview of
  everything: Threads at the root, Subthreads nested under their parent, and
  Tasks / Subtasks nested under their owning thread.
- **Work and Personal are clearly separated** — shown as two sections with a
  tab/filter (All · Work · Personal) to switch focus without mixing the data.
- Clean visual hierarchy: indentation + connector lines, thread nodes as rows
  (icon, title, pending count) linking to the thread page, task nodes as
  checklist leaves (state + age). Nodes with children **collapse/expand**.
- Fully responsive (no horizontal overflow — the tree scrolls within its own
  container on small screens), preserves the design system, has **empty states**
  when a section has no threads, and is keyboard-navigable.

### 2.6 Thread identity

- Per-thread **accent color** and optional emoji, stored in frontmatter, so
  threads are distinguishable beyond their generated icon.
- **Regenerate icon** action on demand (v1.0 only generates on creation).

---

## 3. UI Improvements

- **App logo**: a vector "focus target" mark in the header and as the favicon
  (delivered in v1.0's tail; formalized here as part of the identity).
- **Command bar everywhere**: the AI command box is present on every page (not
  just the dashboard), always ready to accept input — including while viewing a
  thread — and continues to scope to the active mode.
- **New sub-thread button**: the thread page has a direct control to create a
  child thread under the current one (a manual create, no AI round-trip).
- **Guarded Move control**: the thread "Move to…" re-parent button stays
  disabled until a real destination is chosen, so it can't submit an empty move.
- **Pending-tasks peek on cards**: each thread card has a `＋` button that
  expands a panel of that thread's pending tasks (including nested sub-threads),
  ordered oldest-first by creation date so stale work surfaces; each item shows
  and links to the sub-thread it belongs to. Works identically in WORK and
  PERSONAL modes.
- **Icon legibility in dark mode**: generated thread icons render on a constant
  light chip (contained, padded) so images with transparent or dark content
  stay visible in both light and dark themes.
- **Permanent delete from archive**: an archived thread can be discarded forever
  (its folder removed from the vault) via a "Delete forever" action that asks
  for confirmation, since it is irreversible.
- **Uniform buttons**: labeled action buttons share a consistent height and
  padding so rows of controls align cleanly.
- **Denser, calmer dashboard**: consistent card sizing, clearer section
  headers, subtle hover/selection motion (respecting reduced-motion).
- **Sticky command bar** that collapses to a single line on scroll and expands
  on focus, keeping the 10-row compose area when needed.
- **Breadcrumb + mini thread map** on thread pages for deep hierarchies.
- **Better empty states** with a one-click example to seed a first thread.
- **Fully responsive & adaptive**: the layout adapts to every screen size and
  orientation — phones, tablets, laptops, desktops, and large displays — using
  fluid grids, responsive typography (`clamp`), flexible spacing, and adaptive
  navigation. No fixed widths that cause overflow; content, buttons, menus,
  forms, and images stay clear and usable. Controls are sized for both touch
  and mouse (hover-only affordances are always shown on touch devices), and
  inputs avoid mobile auto-zoom.
- **Toasts** for reversible actions (archive, delete, restore) with an undo.

---

## 4. Non-Functional Requirements

- No regression to the vault contract: all edits still round-trip through
  markdownlint-clean `.md` files.
- Mode scoping and the approve/discard safety model are preserved.
- New network work (reports, AI edits) stays off the UI thread; background
  tasks as in v1.0.
- Light and dark parity for every new surface; zero hardcoded colors.

---

## 5. Acceptance Criteria (v1.1)

1. The command palette opens with `Ctrl`/`Cmd`+`K`, filters threads as you
   type, and navigates to the chosen thread with the keyboard only.
2. Renaming a task updates its text in the UI and in the `.md` file, preserving
   completion state and order.
3. Reordering sibling tasks persists the new order to disk and survives reload.
4. Approve all applies every queued action; Discard all clears the queue; both
   respect mode scoping.
5. An exported thread report is a single self-contained themed `.html` that
   renders the thread tree and opens offline.
6. A per-thread accent color set in frontmatter is reflected on its card and
   page in both light and dark modes.
7. Every new reversible action shows an undo toast that restores prior state.

---

## 6. Out of Scope (→ later)

- Multi-user or collaboration (still single-user by design).
- Vector/semantic database (file tree + git remains sufficient).
- Native mobile apps (responsive web only).

---

*Proposal for v1.1. Template lineage: `spec_vision.md`. Supersedes nothing in
v1.0 until implemented and merged.*
