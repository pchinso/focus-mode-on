# Focus Mode On

Personal task management over a plain-Markdown vault, with an optional
AI command bar. Activities live as hierarchical *threads* under two roots —
**WORK** and **PERSONAL** — and every thread is a readable `.md` file that
works outside the app (Obsidian, any editor).

See [spec.md](spec.md) for the full product and architecture specification.

## Quick start

```bash
python -m venv .venv
.venv\Scripts\activate        # Windows
pip install -e .              # core app (no AI)
# optional AI command bar + icon generation:
pip install -e ".[ai]"

uvicorn app.main:app --reload
```

Open <http://127.0.0.1:8000>. The default password is `focus` — set your own
before exposing the app:

```bash
set APP_PASSWORD=your-secret        # Windows (cmd)
$env:APP_PASSWORD = "your-secret"   # Windows (PowerShell)
```

## Configuration

All configuration is via environment variables:

| Variable | Purpose | Default |
| --- | --- | --- |
| `APP_PASSWORD` | Login password | `focus` (with a warning) |
| `APP_SECRET_KEY` | Session-cookie signing key | random per process |
| `VAULT_DIR` | Path to the Markdown vault | `./vault` |
| `OPENAI_API_KEY` | Enables the AI command bar and icon generation | unset (heuristic mode) |

Without an `OPENAI_API_KEY` the command bar still works using a local
heuristic parser, and threads use a generated initials glyph instead of an AI
icon. Every other feature is fully available.

## Keyboard shortcuts

`j`/`k` move · `Enter` open · `Space`/`x` toggle a task · `/` command bar ·
`a` add task · `c` complete thread · `?` help · `Esc` back.

## Running tests

```bash
pip install -e ".[dev]"
pytest
```

## How data is stored

Each thread is a folder with a `thread.md` (YAML frontmatter + a `## Tasks`
checklist). Completing a thread moves its folder under `vault/_archive/`,
preserving its path; restoring moves it back. When the vault is a git
repository, every mutation is committed automatically.
