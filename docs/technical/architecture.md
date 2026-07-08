# Focus Mode On — Technical Documentation

Developer-facing notes on architecture, data flow, and how to build, run and
test the app. See [spec.md](../../spec.md) for the full specification.

## Architecture

A single FastAPI service serves server-rendered Jinja2 pages, progressively
enhanced by a small dependency-free JavaScript layer (`app/static/js/app.js`)
for AJAX partial swaps and keyboard navigation. The Markdown vault is the
single source of truth; the app is a stateless interpreter over it.

```text
Browser (Jinja pages + app.js)
      | HTTP (session cookie)
FastAPI (app/main.py)
      | auth (app/auth.py)
      | VaultRepo (app/vault/repo.py) --- reads/writes ---> Markdown vault
      | AICommandLayer / IconGenerator (app/ai/*) --- optional ---> OpenAI API
```

## Module responsibilities

| Module | Responsibility |
| --- | --- |
| `app/config.py` | Read settings from environment variables |
| `app/auth.py` | Password check, signed session cookies, rate limiting |
| `app/main.py` | Routes, request handling, intent application |
| `app/vault/model.py` | `Thread` / `Task` (recursive tree) dataclasses, `order_tasks`, `count_pending`, slugify |
| `app/vault/parser.py` | Markdown + frontmatter → model; nested checklist → task tree |
| `app/vault/writer.py` | Model → canonical, lint-clean Markdown with nested indentation (atomic write) |
| `app/vault/repo.py` | High-level operations (add/toggle by index-path, subtasks), write lock, git recording |
| `app/vault/sync.py` | Best-effort git pull/commit/push (no-op without git) |
| `app/ai/commands.py` | Natural language → structured intents (OpenAI or heuristic) |
| `app/ai/icons.py` | Optional per-thread icon image generation |

## Data flow: a command-bar update

1. The browser posts free text to `POST /command`.
2. `AICommandLayer.interpret` returns a list of `Intent`s (via OpenAI when a
   key is set; otherwise a local heuristic). Each carries a confidence score.
3. Intents at or above the confidence threshold (0.75) are applied through
   `VaultRepo`; lower-confidence intents are returned for one-click confirm.
4. Each applied intent mutates the vault: the writer produces canonical
   Markdown, the write is atomic, and `sync.commit` records it in git when the
   vault is a repository.
5. The refreshed partial is swapped into the page by `app.js`.

## Data model

The model is hierarchical at two levels, neither of which has a fixed depth
limit:

- **Threads** nest via the filesystem: a thread folder can contain child thread
  folders to any depth. `Thread.children` is filled recursively by
  `parser.load_tree`.
- **Tasks** nest via indented Markdown checklists: `Task.children` forms an
  unbounded tree. `parser._split_body` reconstructs the tree from each line's
  indentation using an indentation stack; `writer._render_tasks` emits a
  canonical two-space indent per level.

Each thread is a folder with a `thread.md`: YAML frontmatter (`title`,
`status`, `created`, `completed`, optional `icon`) plus a body with a `#`
heading, a description, and a nested `## Tasks` checklist. Completed tasks carry
a `✅ YYYY-MM-DD` stamp and are ordered before pending ones **at every level**
(`model.order_tasks`). Archiving moves the folder under `_archive/` preserving
its relative path; restore reverses it.

### Addressing tasks

Because tasks are a tree and reorder as they complete, the UI and server agree
on a **dotted index-path** into the completed-first ordered tree: `0` is the
first top-level task, `0.2` its third child, `0.2.1` that child's second child.
The renderer emits these paths; `repo._resolve_task` walks them (re-ordering at
each level) to find the target. Because the client re-fetches the whole task
partial after each mutation, paths are always recomputed from a fresh render,
so a reorder never mis-targets a subsequent action. Toggle and add-subtask
routes parse the path via `main._parse_task_path`.

The parser/writer round-trip is idempotent and markdownlint-clean, including
nested subtasks — covered by `tests/test_vault.py::test_write_then_parse_round_trip`,
`test_render_indents_nested_tasks`, and `test_nested_subtasks_add_and_persist`.

## Build, run, test

```bash
pip install -e ".[dev]"       # core + test deps
pip install -e ".[ai]"        # optional OpenAI integration
uvicorn app.main:app --reload # run
pytest                        # unit + integration + E2E
```

Configuration is entirely via environment variables (`APP_PASSWORD`,
`APP_SECRET_KEY`, `VAULT_DIR`, `OPENAI_API_KEY`); see the README table.

## Deployment

Deploy as a single container (`uvicorn app.main:app`) to a free-tier host.
The vault should be a private git repository so state survives ephemeral
disks: the app pulls on start and commits/pushes after each write. Push to
`main` to redeploy.

## Design decisions

- **Server-rendered + tiny JS, no SPA build**: matches a solo maintainer and
  free hosting; avoids a Node toolchain.
- **Vendored JS instead of a CDN**: the app works fully offline and has no
  external runtime dependency.
- **AI strictly optional**: every feature has a non-AI path so a missing or
  failing OpenAI service never blocks task management.
- **Git as history/backup**: no database in V1; the file tree plus git covers
  persistence, traceability, and off-app editing.
