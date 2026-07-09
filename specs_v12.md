# Focus Mode On — v1.2 Specification (Proposals)

> Forward-looking proposal that builds on the shipped v1.1 (see
> [specs_v11.md](specs_v11.md) and [spec.md](spec.md)). It sketches the next set
> of features and a UI evolution. The core principle is unchanged: the Markdown
> vault stays the single source of truth and every `.md` file stays readable
> outside the app.

| Field | Value |
| --- | --- |
| Document | specs_v12.md — v1.2 proposal |
| Builds on | v1.1 (palette, search, task editing, tree view, task age, …) |
| Status | Draft / for review |

---

## 1. Goals for v1.2

- Turn the vault from a structure you *browse* into one you can *plan against*:
  due dates, priorities, and views that answer "what should I do next?".
- Make finding anything instant — full-text across threads and tasks.
- Reduce friction on bulk work (multi-select, drag) and add gentle insight
  (trends, stale counts) without adding heaviness.
- Keep everything offline-first and installable.

---

## 2. Proposed Features

### 2.1 Dates, priorities, and planning

- **Due dates & scheduled dates** on tasks, stored as Obsidian-compatible
  stamps (`📅` due, `⏳` scheduled) alongside the existing `➕`/`✅`.
- **Priorities** (e.g. high / normal / low) via `🔺`/`🔽` stamps, reflected in
  ordering and a subtle marker.
- **Agenda / calendar view**: a `/agenda` page grouping pending tasks by
  due-date buckets (Overdue, Today, This week, Later, No date), each linking to
  its thread.

### 2.2 Search and smart views

- **Global full-text search** (`Ctrl`/`Cmd`+`P` or the palette): match thread
  titles, descriptions, and task text across the whole vault; jump to results.
- **Smart lists / saved filters**: built-ins like "Stale (>14d)", "Due soon",
  "High priority", and user-defined saved filters, surfaced on the dashboard
  and the tree view.

### 2.3 Faster editing

- **Drag-and-drop** reorder and re-parent for both tasks and threads (an
  upgrade from the current button controls), with keyboard equivalents kept.
- **Multi-select** tasks for bulk complete / move / delete, with an undo toast.

### 2.4 Insight

- **Insights panel**: completion trend over recent weeks, count of stale
  pending tasks, per-mode balance — small, themed, no external charts library
  (inline SVG following the dataviz palette).
- **Weekly review** (AI, optional): summarize what was completed and suggest
  next actions per thread.

### 2.5 Notes and capture

- **Task notes**: an optional free-text note under a task (still plain Markdown),
  for links and context.
- **Quick capture**: a global shortcut to jot a task into an inbox thread from
  anywhere, to be triaged later.

### 2.6 Platform

- **PWA / offline**: installable app with a service worker so the UI loads
  offline; vault writes queue and sync when back online (single user).
- **Import**: bring an existing Obsidian task vault in, mapping its stamps.

---

## 3. UI Improvements

- **Theme customization**: a small set of accent themes on top of the Cox
  tokens, plus a per-mode default accent.
- **Palette everywhere**: extend `Ctrl`/`Cmd`+`K` with actions (new thread,
  new task, toggle filters) beyond navigation.
- **Tree filters**: on `/tree`, filter to pending-only, stale-only, or by
  priority; remember the last choice.
- **Motion & focus polish**: subtle expand/collapse and toast transitions that
  respect `prefers-reduced-motion`; a persistent, visible focus ring audit.
- **Density toggle**: comfortable vs compact spacing for large hierarchies.

---

## 4. Non-Functional Requirements

- No regression to the vault contract: every new field round-trips through
  markdownlint-clean `.md` files and stays readable in Obsidian.
- Mode scoping and the approve/discard safety model are preserved.
- New AI work stays optional and off the UI thread (background tasks).
- Full light/dark parity and responsiveness for every new surface.

---

## 5. Acceptance Criteria (v1.2)

1. A task with a due date shows in the correct `/agenda` bucket and the stamp
   round-trips through its `.md` file.
2. Full-text search returns matches from task text (not just titles) and
   navigates to the owning thread.
3. A saved smart list ("Stale") lists exactly the pending tasks older than its
   threshold, across both modes when unfiltered.
4. Dragging a task to a new position or parent persists the new order/location
   to disk and is reversible via keyboard too.
5. Multi-selecting tasks and completing them updates all of them and offers a
   single undo.
6. The insights panel renders completion and stale figures with no external
   dependencies, in light and dark.
7. The app is installable and its shell loads with the network disabled.

---

## 6. Out of Scope (→ later)

- Multi-user collaboration or real-time sync (still single-user by design).
- A server-side database (file tree + git remains the store).
- Native mobile apps (responsive PWA only).

---

*Proposal for v1.2. Template lineage: `spec_vision.md`. Supersedes nothing in
v1.1 until implemented and merged.*
