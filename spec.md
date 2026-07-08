# Focus Mode On — Product and Architecture Specification (v1.0)

**Focus Mode On**: a personal, browser-based task management app for a solo
developer that organizes work and personal life as hierarchical *activity
threads* stored in plain Markdown files, updated through natural-language
input via an AI layer.

| Field | Value |
| --- | --- |
| Document | spec.md — first integrable version |
| Date | 2026-07-08 |
| Location | `c:\_Dev\Python\Projects\focus-mode-on` |
| Status | Draft |
| Sources | `templates/cuestionario_inicio.md` (brief v1, 2026-07-08); Obsidian daily-note samples in `references/` (context only, not design input) |

---

## 1. Vision and Objective

Focus Mode On is a single-user web application for personal task management
and productivity. Activities are organized as **threads**: hierarchical
branches that start at one of two root nodes — **WORK** and **PERSONAL** —
and subdivide through initiatives and projects down to individual tasks.
The user records completed work and visualizes pending work entirely from
the app UI; an AI layer turns natural-language text into task operations,
eliminating manual editing of `.md` files.

Main capabilities (outcome-oriented):

- See, at a glance, all active activity threads and their pending/completed
  tasks from an entry dashboard.
- Update the vault by typing natural language ("finished the report, add a
  follow-up call for Friday") — the AI layer creates, completes, and archives
  tasks and threads accordingly.
- Keep every piece of data as a readable, well-formatted Markdown file that
  works outside the app (e.g., opened in Obsidian or any editor).
- Identify threads visually through semantically relevant generated
  images/icons per initiative or project.
- Operate the whole UI with the keyboard only, in light or dark mode.

### 1.1 Guiding Architectural Principle

> The Markdown vault is the single source of truth; the web app is a stateless
> interpreter over it, and the AI layer is the only writer besides the user's
> own editor.

Pattern **D — Web application** (from `spec_architecture.md`), chosen because
the brief requires browser access, free hosting, and update management via
GitHub. Alternatives discarded: A/B (desktop) contradict the browser
requirement; C (client + separate API service) adds infrastructure a
single-user app does not need; E (CLI/library) lacks the required visual UI.

```text
+--------------------- Browser (client) ----------------------+
| Dashboard | Thread view | Command bar (natural language)    |
+------------------------------|-------------------------------+
                               | HTTPS (password-protected session)
+------------------------------v-------------------------------+
|                FastAPI app (Python, single service)           |
|  auth | vault engine (read/write .md) | renderer | AI layer  |
+---------|-------------------------------------|--------------+
          |                                     |
   +------v-------+                     +-------v--------+
   | Markdown     |  git pull / push    | OpenAI API     |
   | vault (repo) | <---------------->  | (NL commands,  |
   | work/ pers./ |   private GitHub    |  icon images)  |
   +--------------+                     +----------------+
```

---

## 2. V1 Scope (First Integrable Version)

### 2.1 Included in V1

| # | Capability | Origin |
| --- | --- | --- |
| V1-1 | Entry dashboard displaying activity threads | new (brief §4.1) |
| V1-2 | Two top-level nodes: **WORK** and **PERSONAL** | new (brief §4.2) |
| V1-3 | Hierarchical sub-threads that evolve and subdivide; completing a thread archives it automatically, with restore option | new (brief §4.3) |
| V1-4 | Pending and completed task list at the end of each thread; completed tasks shown above pending ones | new (brief §4.4) |
| V1-5 | AI layer: natural-language text input creates/completes tasks and threads (OpenAI API) | new (brief §4.5) |
| V1-6 | Generated, semantically relevant images/icons per thread for fast visual identification | new (brief §4.6) |
| V1-7 | All data as readable, well-formatted Markdown files usable outside the app | new (brief §4.7) |
| V1-8 | Browser GUI renders the files as an attractive, interactive UI | new (brief §4.8) |
| V1-9 | Keyboard-only navigation throughout the UI | new (brief §4.9) |
| V1-10 | Password-protected access; data transport encrypted (HTTPS) | new (brief §9) |
| V1-11 | Light and dark mode, Cox visual identity | new (brief §10) |

### 2.2 Excluded from V1 (→ roadmap §9)

- Ingestion of external information for context building.
- Online search for relevant information.
- Semantic / vector database persistence (plain files are enough for V1).
- External collaborators on a project or thread (deferred decision, brief §13).
- HTML report export with visual identity (early V2 candidate, brief §11).
- Multi-user support of any kind (single user by design).

---

## 3. Visual Identity

Cox identity manual compliance — see `templates/spec_visual_id.md`. Specific
application for this app:

- Header with the corporate gradient (Planet Blue → Water Turquoise → Energy
  Coral) on the dashboard.
- Both light and dark modes, switchable from the header and persisted; all
  colors come from a single CSS custom-property token file (no hardcoded
  colors in components, no raw `white`/`#fff`).
- Red Hat Display packaged with the app (OFL license), fallback Segoe UI.
- Thread cards and task lists use Planet Blue for structure, Water Turquoise
  for informative accents (PERSONAL), Energy Coral for emphasis (WORK),
  following the water/energy accent rule.
- Generated thread icons are decorative content, not brand elements; they must
  not recolor or replace the Cox logo.

---

## 4. Application Architecture

### 4.1 Chosen Pattern and Rationale

**Pattern D — Web application**, as a single lightweight Python service
(FastAPI) that serves a server-rendered UI progressively enhanced with HTMX
and a small amount of vanilla JS (keyboard navigation, command bar). One
process, one deployable, no separate frontend build pipeline — this matches
"lightweight and fast framework, free hosting, simple updates via GitHub"
and a maintenance team of one. Discarded: SPA frameworks (build complexity
disproportionate to a solo tool) and pattern C (no need for an independent
API service with exactly one client).

### 4.2 Repository Structure

```text
focus-mode-on/
├── app/
│   ├── main.py            # FastAPI entry point, routes
│   ├── auth.py            # password login, session cookie
│   ├── vault/             # Markdown vault engine
│   │   ├── model.py       # Thread/Task dataclasses, statuses
│   │   ├── parser.py      # .md + frontmatter -> model
│   │   ├── writer.py      # model -> canonical, lint-clean .md
│   │   └── sync.py        # git pull/commit/push of the vault
│   ├── ai/
│   │   ├── commands.py    # NL input -> structured intents (OpenAI)
│   │   └── icons.py       # semantic icon/image generation (OpenAI)
│   ├── templates/         # Jinja2 views (dashboard, thread, login)
│   └── static/            # tokens.css, app.css, keyboard.js, fonts/
├── vault/                 # the Markdown data (or a separate private repo)
│   ├── work/
│   ├── personal/
│   └── _archive/
├── tests/
├── docs/
│   ├── user/              # user documentation (English)
│   └── technical/         # technical documentation (English)
├── spec.md
├── .markdownlint.jsonc
└── pyproject.toml
```

### 4.3 Boundaries and Interfaces

- **Browser ↔ app**: HTML over HTTPS; HTMX partial updates for task toggles,
  archiving, and command-bar results. No public JSON API in V1.
- **App ↔ vault**: the vault engine is the only code that reads/writes `.md`
  files. Writes are atomic (write temp file, rename) and always produce
  markdownlint-clean output.
- **App ↔ OpenAI (commands)**: one structured-output call per user input.
  Contract (JSON) returned by the model:

```json
{
  "intents": [
    {
      "action": "create_task | complete_task | create_thread | complete_thread | restore_thread",
      "thread_path": "work/initiative-x/project-y",
      "title": "Call supplier about quote",
      "confidence": 0.93
    }
  ]
}
```

  Intents with `confidence` below a threshold (0.75) are shown to the user
  for one-key confirmation instead of being applied silently.

- **App ↔ OpenAI (icons)**: on thread creation the app requests one small
  image from the thread title/description; the file is stored under the
  thread's folder as `icon.png` and referenced from frontmatter. Failure is
  non-blocking — a deterministic fallback glyph (initials + token color) is
  used until regeneration succeeds.

### 4.4 State and Persistence

- All state lives in the Markdown vault (see data model, §8). No database in
  V1; the brief's vector-DB idea moves to the roadmap.
- Free-tier hosts have ephemeral disks, so the vault is a **private GitHub
  repository**: the app pulls on startup and commits/pushes after each write
  (debounced). This also gives history, backup, and off-app editing for free.
- Configuration and secrets (app password hash, OpenAI key, vault repo token)
  are environment variables — never files in the repo.

### 4.5 Concurrency and Performance

- Single user, so no multi-writer concurrency; a per-vault asyncio lock
  serializes writes.
- OpenAI calls (commands, icon generation) and git pushes run as async /
  background tasks so the UI never blocks; the command bar shows a pending
  state and swaps in the result via HTMX.
- Local vault operations (parse/render/toggle) must be sub-second.

### 4.6 Packaging and Deployment

- Deployed from GitHub to a free-tier host (Render or Fly.io — final pick at
  implementation time) as a single container: `uvicorn app.main:app`.
- Updates = push to `main` → auto-deploy. Also runnable locally with one
  command (`uv run uvicorn ...`) against the local vault.

### 4.7 Testing Strategy

- **Unit**: parser/writer round-trip (`.md` → model → `.md` is idempotent and
  lint-clean); intent-application logic; archive/restore moves.
- **Integration**: FastAPI TestClient flows with a fixture vault; AI layer
  tested against recorded/mocked OpenAI responses (no live calls in CI).
- **End-to-end**: dashboard → open thread → complete task via command bar →
  file on disk changed correctly; keyboard-only navigation path.

---

## 5. Components / Modules

### 5.1 Vault Engine (`app/vault/`)

- **Function**: canonical read/write layer over the Markdown vault.
- **Logic**: parse frontmatter + task checkboxes into Thread/Task models;
  write back in canonical form (completed tasks listed above pending ones);
  move completed threads to `_archive/` mirroring their path; restore them.
- **Input**: vault directory. **Output**: models for the UI, `.md` files on
  disk. **Dependencies**: `python-frontmatter`, `markdown-it-py`, GitPython
  (sync). **Pending integration work**: canonical formatting rules, archive
  path collision handling.

### 5.2 AI Command Layer (`app/ai/commands.py`)

- **Function**: turn free-form user text into vault operations.
- **Logic**: prompt with the current thread tree as context; OpenAI
  structured output per the contract in §4.3; low-confidence intents require
  confirmation; every applied change is reported back in the UI.
- **Input**: user text + thread tree. **Output**: applied intents + summary.
- **Dependencies**: `openai` SDK, `OPENAI_API_KEY`. **Pending**: prompt
  design, confidence-threshold tuning.

### 5.3 Icon Generator (`app/ai/icons.py`)

- **Function**: one semantically relevant icon/image per thread.
- **Input**: thread title + description. **Output**: `icon.png` in the thread
  folder + frontmatter reference. **Dependencies**: OpenAI image API.
- **Pending**: style prompt so icons look like one coherent set; fallback
  glyph rendering.

### 5.4 Renderer / UI (`app/templates/`, `app/static/`)

- **Function**: interpret vault files into the visual, interactive UI.
- **Logic**: dashboard of thread cards; thread page with breadcrumb, children,
  and the task list (completed above pending); HTMX partials for mutations;
  keyboard layer (§6). **Dependencies**: Jinja2, HTMX, tokens.css.

---

## 6. GUI Functional Specification (V1)

- **Login**: single password field; session cookie on success; rate-limited.
- **Dashboard (entry point)**: two root sections, WORK and PERSONAL, each
  listing active thread cards (icon, title, pending count, last activity).
  A global **command bar** (focused with `/`) accepts natural-language input
  anywhere in the app.
- **Thread view**: breadcrumb from root; child threads as cards; task list at
  the end with completed tasks above pending ones; actions: add task, toggle
  task, complete thread (→ auto-archive with an undo/restore toast).
- **Archive view**: browsable archived threads with one-key restore.
- **Keyboard-only navigation**: `j`/`k` or arrows to move between cards and
  tasks, `Enter` to open, `Space`/`x` to toggle a task, `/` command bar,
  `a` add task, `c` complete thread, `u` restore, `?` shortcut help overlay,
  `Esc` back. Every interactive element reachable without a mouse; visible
  focus ring from theme tokens.
- **Header**: Cox gradient, app name, light/dark toggle, logout.
- **Help/About**: shortcut list, version, vault sync status.

---

## 7. Non-Functional Requirements

| Topic | Requirement |
| --- | --- |
| Platform | Cross-platform via browser; server is a Python container on a free-tier host; local run supported |
| Stack | Python 3.12+, FastAPI, Jinja2, HTMX, python-frontmatter, markdown-it-py, GitPython, openai |
| Performance | UI always fast and fluid; local vault operations sub-second; AI/git operations async and never block the UI |
| Robustness | Validate intents before applying; actionable error messages; OpenAI/network failures degrade gracefully (manual task editing still works) |
| Traceability | Every vault mutation becomes a git commit (what changed, when, from which input) |
| Security | Password-protected access (hashed, rate-limited login); HTTPS-only; vault in a private GitHub repo; secrets only in environment variables |
| Quality | pytest unit/integration/E2E per §4.7; CI on GitHub Actions |
| Language | UI in English; code identifiers, comments, and docstrings in English |
| Identity | Cox identity manual compliance (see §3 and `templates/spec_visual_id.md`) |
| Delivery conventions | **[NORMATIVE]** Numbers shown with 2 decimals and adjacent unit where applicable (V1 shows integer counters only — allowed exception); English code comments/docstrings; user and technical documentation in `docs/`; all `.md` files pass markdownlint (`.markdownlint.jsonc` at repo root). See `templates/spec_conventions.md` |

Licensing/protection (§7bis of the template) does **not** apply: the app is
not distributed to third parties. Access control is covered by the security
row above.

---

## 8. Data Model

The vault is a directory tree; hierarchy in the filesystem mirrors the thread
hierarchy. Every thread is a folder with a `thread.md`:

```text
vault/
├── work/
│   └── initiative-x/
│       ├── thread.md
│       ├── icon.png
│       └── project-y/
│           └── thread.md
├── personal/
│   └── ...
└── _archive/
    └── work/...          # archived threads keep their original path
```

`thread.md` format (readable and valid Markdown outside the app):

```markdown
---
title: Project Y
status: active            # active | archived
created: 2026-07-08
completed: null
icon: icon.png
---

# Project Y

Short free-text description of the thread.

## Tasks

- [x] Draft the kickoff note ✅ 2026-07-08
- [ ] Call supplier about quote
```

Conventions: dates in ISO `YYYY-MM-DD`; completed tasks carry a completion
date and are ordered above pending ones; folder names are kebab-case slugs of
the title; archiving moves the folder under `_archive/` and sets
`status: archived` plus `completed`.

---

## 9. Roadmap

| Version | Content | Plan phases |
| --- | --- | --- |
| **V1.0** | Scope of §2.1: vault engine, dashboard, thread views, AI command bar, icon generation, auth, light/dark, keyboard navigation, GitHub vault sync | 1. vault engine + models · 2. UI read-only · 3. mutations + archive · 4. AI layer · 5. icons, auth, deploy |
| **V1.1** | HTML report export with Cox identity; polish from daily use | after 2+ weeks of real use |
| **V2.0** | Context ingestion of external information; online search for relevant information; optional semantic/vector store over the vault | to be specified |
| **Later** | External collaborators on a thread (deferred decision) | to be specified |

---

## 10. V1 Acceptance Criteria

1. Opening the app URL without a session shows the login page; the correct
   password grants access and a wrong password is rejected with a rate limit.
2. The dashboard shows WORK and PERSONAL with all active threads from the
   vault, each with its icon (or fallback glyph), title, and pending count.
3. Creating a thread from the command bar ("start a new work project called
   Migration") creates the folder and a lint-clean `thread.md` under
   `vault/work/`, visible in the UI without a manual refresh.
4. Typing a completion in natural language ("I finished the supplier call in
   Project Y") marks exactly that task `[x]`, stamps the date, and reorders it
   above the pending tasks in the file on disk.
5. A low-confidence AI intent is not applied silently: the UI asks for
   one-key confirmation first.
6. Completing a thread moves its folder to `_archive/` preserving its path,
   and the restore action moves it back with `status: active`.
7. Every `.md` file the app writes passes markdownlint with the repo config
   and renders correctly in an external editor.
8. A full session — login, navigate to a nested thread, toggle a task, open
   the command bar, archive and restore — is possible using only the
   keyboard, with a visible focus indicator at every step.
9. Switching light/dark mode restyles the whole UI (charts/cards included)
   from theme tokens and persists across sessions; no component shows a
   hardcoded white background in dark mode.
10. With the OpenAI API unreachable, manual task operations keep working and
    the UI shows an actionable error for AI features.
11. After any mutation, a git commit exists in the vault repo describing the
    change; on restart the app restores state from the repo.

---

## 11. Risks and Open Decisions

| Risk / decision | Mitigation / proposal |
| --- | --- |
| UI fails to be both attractive and conceptually clear (main risk in brief) | Server-rendered thread-card design iterated early; ship a clickable V1 UI in phase 2 and iterate on real daily use before adding the AI layer |
| AI misinterprets natural language and corrupts the vault | Structured-output contract, confidence threshold with confirmation, every change is a git commit (trivially revertible) |
| Free-tier hosting has ephemeral disk / sleep-on-idle | Vault in a private GitHub repo, pull on start + push on write; app is stateless so cold starts are safe |
| Encryption-at-rest conflicts with "readable .md outside the app" | V1: private repo + HTTPS + password instead of file encryption; revisit client-side encryption only if the vault leaves GitHub |
| OpenAI cost/latency for icon generation | Icons generated once per thread, cached in the vault, deterministic fallback glyph |
| Host choice (Render vs Fly.io) | **[OPEN]** decide at deployment phase by free-tier limits at that time |
| Vector/semantic DB persistence | Deferred to V2; file tree + git history covers V1 needs |

---

*Document generated from `templates/cuestionario_inicio.md` (brief v1) using
the `templates/` specification kit. Template: `spec_vision.md`.*
