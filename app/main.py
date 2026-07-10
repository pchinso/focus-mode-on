"""FastAPI application: routes, auth wiring, and the AI command bar.

The vault is the source of truth; every route reads or mutates it through
:class:`app.vault.repo.VaultRepo`. AI features are optional and degrade to a
local heuristic when no OpenAI key is configured.
"""

from __future__ import annotations

import logging
import re
from datetime import date, datetime
from pathlib import Path
from urllib.parse import quote

from fastapi import BackgroundTasks, Depends, FastAPI, Form, HTTPException, Request
from fastapi.responses import HTMLResponse, RedirectResponse, Response
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates

from . import __version__
from .ai.commands import AICommandLayer, Intent
from .ai.icons import IconGenerator
from .auth import SESSION_COOKIE, Auth
from .config import load_settings
from .vault.model import (
    ARCHIVE_DIR,
    ROOTS,
    collect_pending,
    due_bucket,
    human_age,
    is_stale,
    slugify,
)
from .vault.repo import VaultError, VaultRepo

MODE_COOKIE = "focus_mode"
DEFAULT_MODE = "work"

logger = logging.getLogger("focus_mode_on")

BASE_DIR = Path(__file__).resolve().parent
settings = load_settings()

app = FastAPI(title="Focus Mode On", version=__version__)
app.mount("/static", StaticFiles(directory=BASE_DIR / "static"), name="static")

templates = Jinja2Templates(directory=BASE_DIR / "templates")
templates.env.globals["app_version"] = __version__
templates.env.globals["ROOTS"] = ROOTS
templates.env.globals["now"] = datetime.now
templates.env.globals["human_age"] = human_age
templates.env.globals["is_stale"] = is_stale
templates.env.globals["pending_list"] = collect_pending
templates.env.globals["due_bucket"] = due_bucket
templates.env.globals["today"] = date.today

repo = VaultRepo(settings.vault_dir)
auth = Auth(settings.password, settings.secret_key)
ai = AICommandLayer(settings.openai_key)
icons = IconGenerator(settings.openai_key)
# Available everywhere now that the command bar lives in the base layout.
templates.env.globals["ai_available"] = ai.available


# -- auth plumbing ---------------------------------------------------------


def require_login(request: Request) -> None:
    """Dependency that rejects requests without a valid session."""
    if not auth.valid_token(request.cookies.get(SESSION_COOKIE)):
        raise HTTPException(status_code=303, headers={"Location": "/login"})


def _client_key(request: Request) -> str:
    """Best-effort client identifier for rate limiting."""
    return request.client.host if request.client else "unknown"


def current_mode(request: Request) -> str:
    """Return the active app mode (``work`` or ``personal``).

    Reads the mode cookie and falls back to :data:`DEFAULT_MODE` (WORK) when it
    is absent or invalid.
    """
    mode = request.cookies.get(MODE_COOKIE, DEFAULT_MODE)
    return mode if mode in ROOTS else DEFAULT_MODE


@app.exception_handler(303)
async def _redirect_on_auth(_request: Request, exc: HTTPException) -> Response:
    """Turn the auth 303 into an actual redirect to the login page."""
    return RedirectResponse(exc.headers["Location"], status_code=303)


# -- login / logout --------------------------------------------------------


@app.get("/login", response_class=HTMLResponse)
async def login_form(request: Request, error: str | None = None) -> Response:
    """Render the login page."""
    return templates.TemplateResponse(
        request, "login.html", {"error": error}
    )


@app.post("/login")
async def login_submit(request: Request, password: str = Form("")) -> Response:
    """Validate the password, rate-limit failures, and start a session."""
    key = _client_key(request)
    if auth.rate_limiter.blocked(key):
        return templates.TemplateResponse(
            request,
            "login.html",
            {"error": "Too many attempts. Wait a few minutes and try again."},
            status_code=429,
        )
    if not auth.check_password(password):
        auth.rate_limiter.record_failure(key)
        return templates.TemplateResponse(
            request, "login.html", {"error": "Incorrect password."}, status_code=401
        )
    auth.rate_limiter.reset(key)
    response = RedirectResponse("/", status_code=303)
    response.set_cookie(
        SESSION_COOKIE,
        auth.issue_token(),
        httponly=True,
        samesite="lax",
        max_age=60 * 60 * 24 * 14,
    )
    return response


@app.post("/logout")
async def logout() -> Response:
    """Clear the session cookie and return to login."""
    response = RedirectResponse("/login", status_code=303)
    response.delete_cookie(SESSION_COOKIE)
    return response


# -- read views ------------------------------------------------------------


@app.get("/", response_class=HTMLResponse, dependencies=[Depends(require_login)])
async def dashboard(request: Request) -> Response:
    """Render the dashboard for the active mode's root (default WORK)."""
    mode = current_mode(request)
    active = next((r for r in repo.roots() if r.rel_path == mode), None)
    return templates.TemplateResponse(
        request,
        "dashboard.html",
        {
            "mode": mode,
            "modes": ROOTS,
            "active": active,
            "ai_available": ai.available,
            "using_default_password": settings.using_default_password,
        },
    )


@app.post("/mode/{mode}", dependencies=[Depends(require_login)])
async def set_mode(mode: str) -> Response:
    """Persist the active app mode and return to the dashboard."""
    chosen = mode if mode in ROOTS else DEFAULT_MODE
    response = RedirectResponse("/", status_code=303)
    response.set_cookie(
        MODE_COOKIE,
        chosen,
        httponly=False,
        samesite="lax",
        max_age=60 * 60 * 24 * 365,
    )
    return response


@app.get(
    "/capture", response_class=HTMLResponse, dependencies=[Depends(require_login)]
)
async def capture_view(request: Request) -> Response:
    """Quick-capture page: add tasks to the active mode's Inbox rapidly."""
    mode = current_mode(request)
    try:
        inbox = repo.get(f"{mode}/inbox")
    except VaultError:
        inbox = None
    return templates.TemplateResponse(
        request, "capture.html", {"mode": mode, "inbox": inbox}
    )


@app.post("/capture", dependencies=[Depends(require_login)])
async def capture_add(request: Request, text: str = Form("")) -> Response:
    """Add a captured task to the active mode's Inbox, then return for more."""
    mode = current_mode(request)
    if text.strip():
        rel = f"{mode}/inbox"
        try:
            repo.get(rel)
        except VaultError:
            repo.create_thread(mode, "Inbox")
        repo.add_task(rel, text)
    return RedirectResponse("/capture", status_code=303)


@app.get(
    "/insights", response_class=HTMLResponse, dependencies=[Depends(require_login)]
)
async def insights_view(request: Request) -> Response:
    """Per-mode stats: threads, pending/done tasks, stale count, completion."""
    stats = [_mode_stats(root) for root in repo.roots()]
    return templates.TemplateResponse(request, "insights.html", {"stats": stats})


def _mode_stats(root) -> dict:
    """Aggregate counts for a root and its whole subtree."""
    now = datetime.now()
    acc = {"title": root.title, "root": root.rel_path, "threads": 0,
           "pending": 0, "done": 0, "stale": 0}

    def walk_tasks(tasks) -> None:
        for t in tasks:
            if t.done:
                acc["done"] += 1
            else:
                acc["pending"] += 1
                if is_stale(t.created, now):
                    acc["stale"] += 1
            walk_tasks(t.children)

    def walk(node) -> None:
        for child in node.children:
            acc["threads"] += 1
            walk_tasks(child.tasks)
            walk(child)

    walk(root)
    total = acc["pending"] + acc["done"]
    acc["total"] = total
    acc["pct"] = round(100 * acc["done"] / total) if total else 0
    return acc


@app.get(
    "/search", response_class=HTMLResponse, dependencies=[Depends(require_login)]
)
async def search(request: Request, q: str = "") -> Response:
    """Full-text search over threads and tasks; empty query shows stale tasks."""
    threads: list = []
    tasks: list = []
    stale: list = []
    query = q.strip()
    if query:
        threads, tasks = _search_vault(query)
    else:
        now = datetime.now()
        for root in repo.roots():
            for task, owner in collect_pending(root):
                if is_stale(task.created, now):
                    stale.append((task, owner))
        stale.sort(key=lambda pr: pr[0].created or datetime.min)
    return templates.TemplateResponse(
        request,
        "search.html",
        {"q": query, "threads": threads, "tasks": tasks, "stale": stale},
    )


def _search_vault(query: str):
    """Return (matching threads, matching (task, owner)) for a query string."""
    ql = query.lower()
    thread_hits: list = []
    task_hits: list = []

    def walk_tasks(tasks, owner: str) -> None:
        for t in tasks:
            if ql in t.title.lower():
                task_hits.append((t, owner))
            walk_tasks(t.children, owner)

    def walk(node) -> None:
        for child in node.children:
            if ql in child.title.lower() or ql in (child.description or "").lower():
                thread_hits.append(child)
            walk_tasks(child.tasks, child.rel_path)
            walk(child)

    for root in repo.roots():
        walk(root)
    return thread_hits, task_hits


@app.get(
    "/agenda", response_class=HTMLResponse, dependencies=[Depends(require_login)]
)
async def agenda_view(request: Request) -> Response:
    """Pending tasks grouped by due-date bucket across both roots."""
    today = date.today()
    buckets: dict[str, list] = {
        "overdue": [],
        "today": [],
        "week": [],
        "later": [],
        "none": [],
    }
    for root in repo.roots():
        for task, owner in collect_pending(root):
            buckets[due_bucket(task.due, today)].append((task, owner))
    for key in ("overdue", "today", "week", "later"):
        buckets[key].sort(key=lambda pr: pr[0].due or date.max)
    return templates.TemplateResponse(
        request, "agenda.html", {"buckets": buckets}
    )


@app.get(
    "/tree", response_class=HTMLResponse, dependencies=[Depends(require_login)]
)
async def tree_view(request: Request) -> Response:
    """Hierarchical overview of both roots: threads, subthreads, tasks."""
    return templates.TemplateResponse(
        request,
        "tree.html",
        {"roots": repo.roots(), "mode": current_mode(request)},
    )


@app.get(
    "/archive", response_class=HTMLResponse, dependencies=[Depends(require_login)]
)
async def archive_view(request: Request) -> Response:
    """List archived threads with restore actions."""
    return templates.TemplateResponse(
        request, "archive.html", {"archived": repo.archived()}
    )


@app.get(
    "/thread/{rel_path:path}",
    response_class=HTMLResponse,
    dependencies=[Depends(require_login)],
)
async def thread_view(request: Request, rel_path: str) -> Response:
    """Render a single thread: children, description and task list."""
    try:
        thread = repo.get(rel_path)
    except VaultError:
        raise HTTPException(status_code=404, detail="Thread not found")
    # Candidate re-parent targets: roots + other threads, excluding self and
    # this thread's own subtree.
    rel = thread.rel_path
    move_targets = list(ROOTS) + [
        p for p in _all_paths() if p != rel and not p.startswith(rel + "/")
    ]
    return templates.TemplateResponse(
        request,
        "thread.html",
        {"thread": thread, "move_targets": move_targets},
    )


# -- mutations (HTMX partials) --------------------------------------------


@app.post(
    "/thread/{rel_path:path}/task",
    response_class=HTMLResponse,
    dependencies=[Depends(require_login)],
)
async def add_task(
    request: Request,
    rel_path: str,
    title: str = Form(...),
    parent: str = Form(""),
) -> Response:
    """Add a task (optionally a subtask) and return the task-list partial.

    ``parent`` is a dotted index-path (e.g. ``0.2``) of the task to nest under;
    empty means a top-level task.
    """
    if title.strip():
        try:
            repo.add_task(rel_path, title, _parse_task_path(parent))
        except VaultError:
            raise HTTPException(status_code=400, detail="Invalid parent task")
    thread = repo.get(rel_path)
    return templates.TemplateResponse(
        request, "_tasks.html", {"thread": thread}
    )


@app.post(
    "/thread/{rel_path:path}/toggle/{task_path}",
    response_class=HTMLResponse,
    dependencies=[Depends(require_login)],
)
async def toggle_task(request: Request, rel_path: str, task_path: str) -> Response:
    """Toggle a task at a dotted index-path and return the task-list partial."""
    try:
        repo.toggle_task(rel_path, _parse_task_path(task_path))
    except VaultError:
        raise HTTPException(status_code=400, detail="Invalid task")
    thread = repo.get(rel_path)
    return templates.TemplateResponse(
        request, "_tasks.html", {"thread": thread}
    )


@app.post(
    "/thread/{rel_path:path}/rename/{task_path}",
    response_class=HTMLResponse,
    dependencies=[Depends(require_login)],
)
async def rename_task(
    request: Request, rel_path: str, task_path: str, title: str = Form(...)
) -> Response:
    """Rename a task at a dotted index-path; returns the task-list partial."""
    if title.strip():
        try:
            repo.rename_task(rel_path, _parse_task_path(task_path), title)
        except VaultError:
            raise HTTPException(status_code=400, detail="Invalid task")
    thread = repo.get(rel_path)
    return templates.TemplateResponse(request, "_tasks.html", {"thread": thread})


@app.post(
    "/thread/{rel_path:path}/delete/{task_path}",
    response_class=HTMLResponse,
    dependencies=[Depends(require_login)],
)
async def delete_task(request: Request, rel_path: str, task_path: str) -> Response:
    """Delete a task (and its subtree) at a dotted index-path."""
    try:
        repo.delete_task(rel_path, _parse_task_path(task_path))
    except VaultError:
        raise HTTPException(status_code=400, detail="Invalid task")
    thread = repo.get(rel_path)
    return templates.TemplateResponse(request, "_tasks.html", {"thread": thread})


@app.post(
    "/thread/{rel_path:path}/bulk/{action}",
    response_class=HTMLResponse,
    dependencies=[Depends(require_login)],
)
async def bulk_tasks(
    request: Request, rel_path: str, action: str, path: list[str] = Form(default=[])
) -> Response:
    """Apply a bulk action to the selected tasks; returns the task-list partial."""
    if action not in ("complete", "delete"):
        raise HTTPException(status_code=400, detail="Unknown action")
    paths = [_parse_task_path(p) for p in path if p.strip()]
    try:
        repo.bulk_apply(rel_path, paths, action)
    except VaultError:
        raise HTTPException(status_code=400, detail="Invalid task")
    thread = repo.get(rel_path)
    return templates.TemplateResponse(request, "_tasks.html", {"thread": thread})


@app.post(
    "/thread/{rel_path:path}/priority/{task_path}",
    response_class=HTMLResponse,
    dependencies=[Depends(require_login)],
)
async def cycle_priority(request: Request, rel_path: str, task_path: str) -> Response:
    """Cycle a task's priority and return the task-list partial."""
    try:
        repo.cycle_priority(rel_path, _parse_task_path(task_path))
    except VaultError:
        raise HTTPException(status_code=400, detail="Invalid task")
    thread = repo.get(rel_path)
    return templates.TemplateResponse(request, "_tasks.html", {"thread": thread})


@app.post(
    "/thread/{rel_path:path}/note/{task_path}",
    response_class=HTMLResponse,
    dependencies=[Depends(require_login)],
)
async def set_task_note(
    request: Request, rel_path: str, task_path: str, note: str = Form("")
) -> Response:
    """Set or clear a task's single-line note; returns the task-list partial."""
    try:
        repo.set_note(rel_path, _parse_task_path(task_path), note)
    except VaultError:
        raise HTTPException(status_code=400, detail="Invalid task")
    thread = repo.get(rel_path)
    return templates.TemplateResponse(request, "_tasks.html", {"thread": thread})


@app.post(
    "/thread/{rel_path:path}/due/{task_path}",
    response_class=HTMLResponse,
    dependencies=[Depends(require_login)],
)
async def set_task_due(
    request: Request, rel_path: str, task_path: str, due: str = Form("")
) -> Response:
    """Set or clear a task's due date; returns the task-list partial."""
    parsed: date | None = None
    if due.strip():
        try:
            parsed = date.fromisoformat(due.strip())
        except ValueError:
            raise HTTPException(status_code=400, detail="Bad date")
    try:
        repo.set_due(rel_path, _parse_task_path(task_path), parsed)
    except VaultError:
        raise HTTPException(status_code=400, detail="Invalid task")
    thread = repo.get(rel_path)
    return templates.TemplateResponse(request, "_tasks.html", {"thread": thread})


@app.post(
    "/thread/{rel_path:path}/move/{task_path}",
    response_class=HTMLResponse,
    dependencies=[Depends(require_login)],
)
async def move_task(
    request: Request, rel_path: str, task_path: str, direction: str = Form("up")
) -> Response:
    """Move a task up/down among its siblings; returns the task-list partial."""
    delta = -1 if direction == "up" else 1
    try:
        repo.move_task(rel_path, _parse_task_path(task_path), delta)
    except VaultError:
        raise HTTPException(status_code=400, detail="Invalid task")
    thread = repo.get(rel_path)
    return templates.TemplateResponse(request, "_tasks.html", {"thread": thread})


def _parse_task_path(raw: str) -> list[int]:
    """Parse a dotted index-path like ``0.2.1`` into ``[0, 2, 1]``.

    Returns an empty list for empty input. Raises no error on malformed
    segments beyond what int() would; callers treat failures as bad requests.
    """
    raw = (raw or "").strip()
    if not raw:
        return []
    try:
        return [int(part) for part in raw.split(".") if part != ""]
    except ValueError:
        raise HTTPException(status_code=400, detail="Malformed task path")


@app.post("/complete/{rel_path:path}", dependencies=[Depends(require_login)])
async def complete_thread(rel_path: str) -> Response:
    """Archive a thread and redirect with an undo toast to its parent."""
    try:
        title = repo.get(rel_path).title
        dest = repo.complete_thread(rel_path)
    except VaultError:
        raise HTTPException(status_code=404, detail="Thread not found")
    parent = rel_path.rsplit("/", 1)[0] if "/" in rel_path else ""
    base = f"/thread/{parent}" if parent else "/"
    flash = quote(f'Archived "{title}"')
    undo = quote(f"/restore/{dest}")
    return RedirectResponse(f"{base}?flash={flash}&undo={undo}", status_code=303)


@app.post("/restore/{rel_path:path}", dependencies=[Depends(require_login)])
async def restore_thread(rel_path: str) -> Response:
    """Restore an archived thread and return to the archive view."""
    archive_rel = rel_path if rel_path.startswith(ARCHIVE_DIR) else f"{ARCHIVE_DIR}/{rel_path}"
    try:
        repo.restore_thread(archive_rel)
    except VaultError as exc:
        raise HTTPException(status_code=400, detail=str(exc))
    return RedirectResponse("/archive", status_code=303)


@app.post("/new-thread/{rel_path:path}", dependencies=[Depends(require_login)])
async def new_subthread(
    rel_path: str, background: BackgroundTasks, title: str = Form(...)
) -> Response:
    """Create a child thread directly under ``rel_path`` (manual, no AI)."""
    if not title.strip():
        return RedirectResponse(f"/thread/{rel_path}", status_code=303)
    try:
        thread = repo.create_thread(rel_path, title)
    except VaultError as exc:
        raise HTTPException(status_code=400, detail=str(exc))
    if icons.available:
        background.add_task(_maybe_icon, thread.rel_path, thread.title)
    return RedirectResponse(f"/thread/{thread.rel_path}", status_code=303)


@app.post("/move-thread/{rel_path:path}", dependencies=[Depends(require_login)])
async def move_thread(rel_path: str, new_parent: str = Form(...)) -> Response:
    """Re-parent a thread and redirect to its new location."""
    try:
        dest = repo.move_thread(rel_path, new_parent)
    except VaultError as exc:
        raise HTTPException(status_code=400, detail=str(exc))
    return RedirectResponse(f"/thread/{dest}", status_code=303)


@app.post("/accent/{rel_path:path}", dependencies=[Depends(require_login)])
async def set_accent(rel_path: str, color: str = Form("")) -> Response:
    """Set (or clear) a thread's accent color, then return to its page."""
    chosen = color.strip() or None
    if chosen and not re.match(r"^#[0-9a-fA-F]{6}$", chosen):
        chosen = None
    try:
        repo.set_accent(rel_path, chosen)
    except VaultError:
        raise HTTPException(status_code=404, detail="Thread not found")
    return RedirectResponse(f"/thread/{rel_path}", status_code=303)


@app.post("/purge/{rel_path:path}", dependencies=[Depends(require_login)])
async def purge_thread(rel_path: str) -> Response:
    """Permanently delete an archived thread, then return to the archive."""
    archive_rel = rel_path if rel_path.startswith(ARCHIVE_DIR) else f"{ARCHIVE_DIR}/{rel_path}"
    try:
        repo.purge_thread(archive_rel)
    except VaultError as exc:
        raise HTTPException(status_code=400, detail=str(exc))
    return RedirectResponse("/archive", status_code=303)


@app.post("/purge-all", dependencies=[Depends(require_login)])
async def purge_all() -> Response:
    """Permanently delete all archived threads, then return to the archive."""
    repo.purge_all_archived()
    return RedirectResponse("/archive", status_code=303)


@app.post("/regen-icon/{rel_path:path}", dependencies=[Depends(require_login)])
async def regen_icon(rel_path: str, background: BackgroundTasks) -> Response:
    """Regenerate a thread's icon in the background, then return to its page."""
    try:
        thread = repo.get(rel_path)
    except VaultError:
        raise HTTPException(status_code=404, detail="Thread not found")
    if icons.available:
        background.add_task(_maybe_icon, thread.rel_path, thread.title)
    return RedirectResponse(f"/thread/{rel_path}", status_code=303)


@app.get(
    "/report/{rel_path:path}",
    response_class=HTMLResponse,
    dependencies=[Depends(require_login)],
)
async def thread_report(request: Request, rel_path: str) -> Response:
    """Render a self-contained, themed HTML report of a thread and its subtree."""
    try:
        thread = repo.get(rel_path)
    except VaultError:
        raise HTTPException(status_code=404, detail="Thread not found")
    return templates.TemplateResponse(
        request, "report.html", {"thread": thread}
    )


# -- AI command bar --------------------------------------------------------


@app.post(
    "/command", response_class=HTMLResponse, dependencies=[Depends(require_login)]
)
async def command(request: Request, text: str = Form("")) -> Response:
    """Ingest a note and return a review queue of identified actions.

    Nothing is applied here: in-mode intents are placed in a queue the user
    approves or discards; out-of-mode intents are reported as ignored. The AI
    is scoped to the active mode (WORK/PERSONAL) both in context and here.
    """
    mode = current_mode(request)
    paths = [p for p in _all_paths() if _root_of(p) == mode]
    result = ai.interpret(text, paths, default_root=mode)
    queue: list[Intent] = []
    skipped: list[Intent] = []
    for intent in result.intents:
        (queue if _intent_in_mode(intent, mode) else skipped).append(intent)
    return templates.TemplateResponse(
        request,
        "_command_result.html",
        {
            "queue": queue,
            "skipped": skipped,
            "mode": mode,
            "source": result.source,
            "note": result.note,
            "raw": text,
        },
    )


@app.post(
    "/apply", response_class=HTMLResponse, dependencies=[Depends(require_login)]
)
async def apply_actions(
    request: Request,
    background: BackgroundTasks,
    action: list[str] = Form(default=[]),
    thread_path: list[str] = Form(default=[]),
    title: list[str] = Form(default=[]),
) -> Response:
    """Apply the actions the user approved from the review queue.

    Receives parallel arrays (one entry per still-queued action). Each is
    re-checked against the active mode before applying, so a tampered target in
    the other root is ignored. Icon generation for new threads is deferred to a
    background task so the response returns immediately.
    """
    mode = current_mode(request)
    applied: list[str] = []
    for act, path, ttl in zip(action, thread_path, title):
        intent = Intent(action=act, thread_path=path, title=ttl, confidence=1.0)
        if not _intent_in_mode(intent, mode):
            continue
        line = _apply_intent(intent, mode, bg=background)
        if line:
            applied.append(line)
    return templates.TemplateResponse(
        request, "_applied.html", {"applied": applied}
    )


def _root_of(path: str) -> str:
    """Return the top-level root segment of a vault-relative path."""
    return (path or "").strip().strip("/").split("/", 1)[0]


def _intent_in_mode(intent: Intent, mode: str) -> bool:
    """Whether an intent is allowed in the active mode.

    ``create_thread`` is always allowed because its parent is forced into the
    active root. Every other action must target a thread already under the
    active mode's root, so WORK-mode input can never modify PERSONAL (or the
    reverse).
    """
    if intent.action == "create_thread":
        return True
    return _root_of(intent.thread_path) == mode


def _apply_intent(
    intent: Intent, mode: str = DEFAULT_MODE, bg: BackgroundTasks | None = None
) -> str:
    """Execute a single intent, returning a human-readable summary line.

    Args:
        intent: The intent to apply.
        mode: Active app mode, used as the default root for new threads when
            the intent does not name one.
        bg: Optional background-task queue. When present, icon generation for a
            newly created thread is scheduled on it instead of running inline,
            so the response returns immediately.
    """
    try:
        if intent.action == "create_task":
            thread = repo.add_task(intent.thread_path, intent.title)
            return f"Added task “{intent.title}” to {thread.rel_path}."
        if intent.action == "complete_task":
            ok = repo.complete_task_by_title(intent.thread_path, intent.title)
            return (
                f"Completed “{intent.title}” in {intent.thread_path}."
                if ok
                else f"No pending task matched “{intent.title}”."
            )
        if intent.action == "create_thread":
            parent = _resolve_parent(intent.thread_path, intent.title, mode)
            thread = repo.create_thread(parent, intent.title)
            if bg is not None:
                bg.add_task(_maybe_icon, thread.rel_path, intent.title)
            else:
                _maybe_icon(thread.rel_path, intent.title)
            return f"Created thread {thread.rel_path}."
        if intent.action == "complete_thread":
            dest = repo.complete_thread(intent.thread_path)
            return f"Archived {intent.thread_path} → {dest}."
        if intent.action == "restore_thread":
            dest = repo.restore_thread(intent.thread_path)
            return f"Restored {dest}."
    except VaultError as exc:
        return f"Could not apply intent: {exc}"
    return ""


def _resolve_parent(thread_path: str, title: str, mode: str) -> str:
    """Resolve the parent folder for a new thread from a model-supplied path.

    The AI sometimes returns the *new* thread's full path in ``thread_path``
    (e.g. ``work/dev`` with title ``dev``) instead of just the parent, which
    would nest the thread inside an identically-named folder (``work/dev/dev``).
    This strips a trailing segment that duplicates the new thread's own slug,
    and falls back to the active mode's root when the parent is missing or not
    under a known root.

    Args:
        thread_path: Path the model provided (may be empty or a full new path).
        title: Title of the new thread.
        mode: Active app mode, used as the default root.

    Returns:
        A parent path guaranteed to live under a valid root.
    """
    parent = (thread_path or "").strip().strip("/")
    slug = slugify(title)
    if slug and parent.rsplit("/", 1)[-1] == slug:
        parent = parent.rsplit("/", 1)[0] if "/" in parent else ""
    # Force the new thread into the active mode's root: a missing/invalid
    # parent, or one under the OTHER root, is redirected to the active mode.
    if not parent or _root_of(parent) != mode:
        parent = mode
    return parent


def _maybe_icon(rel_path: str, title: str) -> None:
    """Generate a thread icon (best-effort); safe to run in the background.

    Runs the slow image call, then records the icon filename in the thread's
    frontmatter via a lock-serialized repo write.
    """
    if not icons.available:
        return
    folder = settings.vault_dir / rel_path
    name = icons.generate(folder, title)
    if name:
        try:
            repo.set_icon(rel_path, name)
        except VaultError:
            pass


@app.get("/icon/{rel_path:path}", dependencies=[Depends(require_login)])
async def icon(rel_path: str) -> Response:
    """Serve a thread's cached icon image."""
    from .vault.repo import _clean_rel

    try:
        clean = _clean_rel(rel_path)
    except VaultError:
        raise HTTPException(status_code=400, detail="Bad path")
    path = settings.vault_dir / clean / "icon.png"
    if not path.is_file():
        raise HTTPException(status_code=404, detail="No icon")
    return Response(path.read_bytes(), media_type="image/png")


# -- misc ------------------------------------------------------------------


@app.get("/threads.json", dependencies=[Depends(require_login)])
async def threads_json() -> dict[str, object]:
    """Flat list of all active threads (both roots) for the command palette."""
    items: list[dict[str, str]] = []

    def walk(threads) -> None:
        for t in threads:
            if t.rel_path and t.rel_path not in ROOTS:
                items.append({"path": t.rel_path, "title": t.title, "root": t.root})
            walk(t.children)

    walk(repo.roots())
    return {"threads": items}


@app.get("/sw.js")
async def service_worker() -> Response:
    """Serve the service worker from the root so it controls the whole app."""
    path = BASE_DIR / "static" / "sw.js"
    return Response(
        path.read_text(encoding="utf-8"),
        media_type="application/javascript",
        headers={"Service-Worker-Allowed": "/", "Cache-Control": "no-cache"},
    )


@app.get("/health")
async def health() -> dict[str, object]:
    """Liveness probe with feature availability."""
    return {
        "status": "ok",
        "version": __version__,
        "ai_available": ai.available,
        "vault": str(settings.vault_dir),
    }


def _all_paths() -> list[str]:
    """Flatten every active thread path for AI context."""
    out: list[str] = []

    def walk(threads) -> None:
        for t in threads:
            if t.rel_path:
                out.append(t.rel_path)
            walk(t.children)

    walk(repo.roots())
    return out


def _intent_key(intent: Intent) -> str:
    """Stable identifier used to confirm a specific pending intent."""
    return f"{intent.action}:{intent.thread_path}:{intent.title}"
