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

### 2.5 Thread identity

- Per-thread **accent color** and optional emoji, stored in frontmatter, so
  threads are distinguishable beyond their generated icon.
- **Regenerate icon** action on demand (v1.0 only generates on creation).

---

## 3. UI Improvements

- **App logo**: a vector "focus target" mark in the header and as the favicon
  (delivered in v1.0's tail; formalized here as part of the identity).
- **Denser, calmer dashboard**: consistent card sizing, clearer section
  headers, subtle hover/selection motion (respecting reduced-motion).
- **Sticky command bar** that collapses to a single line on scroll and expands
  on focus, keeping the 10-row compose area when needed.
- **Breadcrumb + mini thread map** on thread pages for deep hierarchies.
- **Better empty states** with a one-click example to seed a first thread.
- **Responsive layout** that works on a narrow window / tablet.
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
