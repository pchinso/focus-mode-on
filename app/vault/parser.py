"""Parse on-disk Markdown thread files into :mod:`app.vault.model` objects."""

from __future__ import annotations

import re
from datetime import date, datetime
from pathlib import Path

import frontmatter

from .model import THREAD_FILE, Task, Thread


# Matches a task line: "- [x] Title ✅ 2026-07-08" or "- [ ] Title".
_TASK_RE = re.compile(r"^\s*-\s*\[(?P<mark>[ xX])\]\s*(?P<body>.+?)\s*$")
# Trailing completion stamp appended to done tasks, e.g. "✅ 2026-07-08".
_DONE_STAMP_RE = re.compile(r"\s*✅\s*(?P<d>\d{4}-\d{2}-\d{2})\s*$")


def _parse_date(value: object) -> date | None:
    """Coerce a frontmatter value into a ``date`` if possible."""
    if isinstance(value, date):
        return value
    if isinstance(value, datetime):
        return value.date()
    if isinstance(value, str) and value.strip() and value.strip() != "null":
        try:
            return date.fromisoformat(value.strip())
        except ValueError:
            return None
    return None


def _split_body(body: str) -> tuple[str, list[Task]]:
    """Split a thread body into its description and its task list.

    Args:
        body: Markdown body below the frontmatter.

    Returns:
        A tuple of (description text, parsed tasks).
    """
    lines = body.splitlines()
    desc_lines: list[str] = []
    tasks: list[Task] = []
    in_tasks = False
    for line in lines:
        stripped = line.strip()
        if stripped.lower().startswith("## tasks"):
            in_tasks = True
            continue
        if in_tasks:
            m = _TASK_RE.match(line)
            if m:
                tasks.append(_parse_task(m))
            continue
        # Skip a leading "# Title" heading; keep the rest as description.
        if stripped.startswith("# "):
            continue
        desc_lines.append(line)
    return "\n".join(desc_lines).strip(), tasks


def _parse_task(match: re.Match[str]) -> Task:
    """Build a Task from a regex match of a checklist line."""
    done = match.group("mark").lower() == "x"
    body = match.group("body")
    completed: date | None = None
    stamp = _DONE_STAMP_RE.search(body)
    if stamp:
        completed = _parse_date(stamp.group("d"))
        body = _DONE_STAMP_RE.sub("", body).strip()
    return Task(title=body.strip(), done=done, completed=completed)


def parse_thread_file(md_path: Path, rel_path: str) -> Thread:
    """Parse a single ``thread.md`` into a Thread (without children).

    Args:
        md_path: Absolute path to the ``thread.md`` file.
        rel_path: Vault-relative POSIX path of the thread folder.

    Returns:
        A populated Thread with tasks but an empty ``children`` list.
    """
    post = frontmatter.load(md_path)
    description, tasks = _split_body(post.content)
    meta = post.metadata
    title = str(meta.get("title") or rel_path.rsplit("/", 1)[-1] or "Untitled")
    return Thread(
        title=title,
        rel_path=rel_path,
        description=description,
        status=str(meta.get("status") or "active"),
        created=_parse_date(meta.get("created")),
        completed=_parse_date(meta.get("completed")),
        icon=(str(meta["icon"]) if meta.get("icon") else None),
        tasks=tasks,
    )


def load_tree(base: Path, rel_path: str = "") -> list[Thread]:
    """Recursively load child threads under a vault-relative path.

    Args:
        base: Absolute vault root directory.
        rel_path: Relative path whose children should be loaded; empty means
            the vault root (returns the top-level roots such as work/personal).

    Returns:
        Child threads sorted by title, each with its own ``children`` filled.
    """
    current = base / rel_path if rel_path else base
    if not current.is_dir():
        return []
    threads: list[Thread] = []
    for entry in sorted(current.iterdir(), key=lambda p: p.name.lower()):
        if not entry.is_dir() or entry.name.startswith((".", "_")):
            continue
        child_rel = f"{rel_path}/{entry.name}" if rel_path else entry.name
        md = entry / THREAD_FILE
        if md.exists():
            thread = parse_thread_file(md, child_rel)
        else:
            thread = Thread(title=entry.name.title(), rel_path=child_rel)
        thread.children = load_tree(base, child_rel)
        threads.append(thread)
    return sorted(threads, key=lambda t: t.title.lower())
