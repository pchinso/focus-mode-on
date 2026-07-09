"""Serialize :mod:`app.vault.model` threads back into markdownlint-clean files.

The writer is the only code that produces ``thread.md`` content. Output is
canonical: completed tasks are listed before pending ones, headings are
surrounded by blank lines, and the file ends with a single newline.
"""

from __future__ import annotations

import os
import tempfile
from pathlib import Path

from .model import THREAD_FILE, Task, Thread, order_tasks


def _fmt_date(value: object) -> str:
    """Format a date value as ISO, or ``null`` when absent."""
    return value.isoformat() if value else "null"


def render_thread(thread: Thread) -> str:
    """Render a Thread to canonical Markdown text.

    Args:
        thread: The thread to serialize.

    Returns:
        Markdown text with frontmatter, description and a ``## Tasks`` section,
        ending with exactly one trailing newline.
    """
    lines: list[str] = ["---"]
    lines.append(f"title: {thread.title}")
    lines.append(f"status: {thread.status}")
    lines.append(f"created: {_fmt_date(thread.created)}")
    lines.append(f"completed: {_fmt_date(thread.completed)}")
    if thread.icon:
        lines.append(f"icon: {thread.icon}")
    if thread.accent:
        # Quote: a bare "#..." would be a YAML comment and get dropped.
        lines.append(f'accent: "{thread.accent}"')
    lines.append("---")
    lines.append("")
    lines.append(f"# {thread.title}")
    lines.append("")
    if thread.description.strip():
        lines.append(thread.description.strip())
        lines.append("")
    lines.append("## Tasks")
    lines.append("")
    _render_tasks(thread.tasks, 0, lines)
    lines.append("")
    return "\n".join(lines).rstrip("\n") + "\n"


def _render_tasks(tasks: list[Task], depth: int, lines: list[str]) -> None:
    """Append a nested checklist to ``lines``, completed-first at each level.

    Args:
        tasks: Sibling tasks to render.
        depth: Current nesting depth (two spaces of indent per level).
        lines: Output accumulator, mutated in place.
    """
    indent = "  " * depth
    for task in order_tasks(tasks):
        mark = "x" if task.done else " "
        prio = {"high": " 🔺", "low": " 🔽"}.get(task.priority, "")
        created = f" ➕ {_fmt_created(task.created)}" if task.created else ""
        due = f" 📅 {task.due.isoformat()}" if task.due else ""
        done_stamp = (
            f" ✅ {task.completed.isoformat()}" if task.done and task.completed else ""
        )
        lines.append(f"{indent}- [{mark}] {task.title}{prio}{created}{due}{done_stamp}")
        if task.children:
            _render_tasks(task.children, depth + 1, lines)


def _fmt_created(value) -> str:
    """Format a creation timestamp: date only at midnight, else ISO minutes."""
    if value.hour == 0 and value.minute == 0:
        return value.date().isoformat()
    return value.strftime("%Y-%m-%dT%H:%M")


def write_thread(base: Path, thread: Thread) -> Path:
    """Atomically write a thread's ``thread.md`` under the vault.

    Args:
        base: Absolute vault root directory.
        thread: Thread to persist (its ``rel_path`` selects the folder).

    Returns:
        The path to the written ``thread.md``.
    """
    folder = base / thread.rel_path
    folder.mkdir(parents=True, exist_ok=True)
    target = folder / THREAD_FILE
    _atomic_write(target, render_thread(thread))
    return target


def _atomic_write(target: Path, content: str) -> None:
    """Write ``content`` to ``target`` atomically via a temp file + rename."""
    fd, tmp = tempfile.mkstemp(dir=str(target.parent), suffix=".tmp")
    try:
        with os.fdopen(fd, "w", encoding="utf-8", newline="\n") as fh:
            fh.write(content)
        os.replace(tmp, target)
    except BaseException:
        if os.path.exists(tmp):
            os.unlink(tmp)
        raise
