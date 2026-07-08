"""FastAPI application: routes, auth wiring, and the AI command bar.

The vault is the source of truth; every route reads or mutates it through
:class:`app.vault.repo.VaultRepo`. AI features are optional and degrade to a
local heuristic when no OpenAI key is configured.
"""

from __future__ import annotations

import logging
from pathlib import Path

from fastapi import Depends, FastAPI, Form, HTTPException, Request
from fastapi.responses import HTMLResponse, RedirectResponse, Response
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates

from . import __version__
from .ai.commands import AICommandLayer, Intent
from .ai.icons import IconGenerator
from .auth import SESSION_COOKIE, Auth
from .config import load_settings
from .vault.model import ARCHIVE_DIR, ROOTS
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

repo = VaultRepo(settings.vault_dir)
auth = Auth(settings.password, settings.secret_key)
ai = AICommandLayer(settings.openai_key)
icons = IconGenerator(settings.openai_key)


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
    return templates.TemplateResponse(
        request, "thread.html", {"thread": thread}
    )


# -- mutations (HTMX partials) --------------------------------------------


@app.post(
    "/thread/{rel_path:path}/task",
    response_class=HTMLResponse,
    dependencies=[Depends(require_login)],
)
async def add_task(request: Request, rel_path: str, title: str = Form(...)) -> Response:
    """Add a task and return the refreshed task-list partial."""
    if title.strip():
        repo.add_task(rel_path, title)
    thread = repo.get(rel_path)
    return templates.TemplateResponse(
        request, "_tasks.html", {"thread": thread}
    )


@app.post(
    "/thread/{rel_path:path}/toggle/{index}",
    response_class=HTMLResponse,
    dependencies=[Depends(require_login)],
)
async def toggle_task(request: Request, rel_path: str, index: int) -> Response:
    """Toggle a task and return the refreshed task-list partial."""
    try:
        repo.toggle_task(rel_path, index)
    except VaultError:
        raise HTTPException(status_code=400, detail="Invalid task")
    thread = repo.get(rel_path)
    return templates.TemplateResponse(
        request, "_tasks.html", {"thread": thread}
    )


@app.post("/complete/{rel_path:path}", dependencies=[Depends(require_login)])
async def complete_thread(rel_path: str) -> Response:
    """Archive a thread and redirect to its parent (or dashboard)."""
    try:
        repo.complete_thread(rel_path)
    except VaultError:
        raise HTTPException(status_code=404, detail="Thread not found")
    parent = rel_path.rsplit("/", 1)[0] if "/" in rel_path else ""
    target = f"/thread/{parent}" if parent else "/"
    return RedirectResponse(target, status_code=303)


@app.post("/restore/{rel_path:path}", dependencies=[Depends(require_login)])
async def restore_thread(rel_path: str) -> Response:
    """Restore an archived thread and return to the archive view."""
    archive_rel = rel_path if rel_path.startswith(ARCHIVE_DIR) else f"{ARCHIVE_DIR}/{rel_path}"
    try:
        repo.restore_thread(archive_rel)
    except VaultError as exc:
        raise HTTPException(status_code=400, detail=str(exc))
    return RedirectResponse("/archive", status_code=303)


# -- AI command bar --------------------------------------------------------


@app.post(
    "/command", response_class=HTMLResponse, dependencies=[Depends(require_login)]
)
async def command(
    request: Request, text: str = Form(""), confirm: str = Form("")
) -> Response:
    """Interpret a natural-language note and apply high-confidence intents.

    Low-confidence intents are returned for one-click confirmation unless the
    request already carries ``confirm`` for a specific intent.
    """
    mode = current_mode(request)
    paths = _all_paths()
    result = ai.interpret(text, paths, default_root=mode)
    applied: list[str] = []
    pending: list[Intent] = []
    for intent in result.intents:
        if intent.needs_confirmation and confirm != _intent_key(intent):
            pending.append(intent)
            continue
        applied.append(_apply_intent(intent, mode))
    return templates.TemplateResponse(
        request,
        "_command_result.html",
        {
            "applied": [a for a in applied if a],
            "pending": pending,
            "source": result.source,
            "note": result.note,
            "raw": text,
            "intent_key": _intent_key,
        },
    )


def _apply_intent(intent: Intent, mode: str = DEFAULT_MODE) -> str:
    """Execute a single intent, returning a human-readable summary line.

    Args:
        intent: The intent to apply.
        mode: Active app mode, used as the default root for new threads when
            the intent does not name one.
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
            parent = intent.thread_path or mode
            thread = repo.create_thread(parent, intent.title)
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


def _maybe_icon(rel_path: str, title: str) -> None:
    """Attempt (best-effort) icon generation for a freshly created thread."""
    if not icons.available:
        return
    folder = settings.vault_dir / rel_path
    name = icons.generate(folder, title)
    if name:
        try:
            thread = repo.get(rel_path)
            thread.icon = name
            from .vault.writer import write_thread

            write_thread(settings.vault_dir, thread)
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
