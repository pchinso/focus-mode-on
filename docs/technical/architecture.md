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
| `app/vault/model.py` | `Thread` / `Task` dataclasses, slugify |
| `app/vault/parser.py` | Markdown + frontmatter → model |
| `app/vault/writer.py` | Model → canonical, lint-clean Markdown (atomic write) |
| `app/vault/repo.py` | High-level operations, write lock, git recording |
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

Each thread is a folder with a `thread.md`: YAML frontmatter (`title`,
`status`, `created`, `completed`, optional `icon`) plus a body with a `#`
heading, a description, and a `## Tasks` checklist. Completed tasks carry a
`✅ YYYY-MM-DD` stamp and are written before pending ones. Archiving moves the
folder under `_archive/` preserving its relative path; restore reverses it.

The parser/writer round-trip is idempotent and markdownlint-clean — this is
covered by `tests/test_vault.py::test_write_then_parse_round_trip` and
`test_render_is_lint_clean_and_orders_done_first`.

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
