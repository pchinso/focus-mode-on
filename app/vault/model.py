"""Domain model for the Markdown vault.

A vault is a tree of *threads*. Every thread is a folder containing a
``thread.md`` file (frontmatter + description + a ``## Tasks`` checklist) and,
optionally, child thread folders. The models here are plain dataclasses; the
parser and writer modules convert between these and on-disk Markdown.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import date


THREAD_FILE = "thread.md"
ARCHIVE_DIR = "_archive"
ROOTS = ("work", "personal")


@dataclass
class Task:
    """A single checklist item inside a thread.

    Attributes:
        title: Human-readable task text.
        done: Whether the task is completed.
        completed: Completion date, set when ``done`` is True.
    """

    title: str
    done: bool = False
    completed: date | None = None


@dataclass
class Thread:
    """A node in the activity tree.

    Attributes:
        title: Display title of the thread.
        rel_path: POSIX-style path relative to the vault root
            (e.g. ``work/initiative-x/project-y``). Empty for the vault root.
        description: Free-text body shown under the title.
        status: ``active`` or ``archived``.
        created: Creation date.
        completed: Completion date, set when the thread is archived.
        icon: Relative icon filename inside the thread folder, if any.
        tasks: Checklist items. Completed tasks are listed before pending ones.
        children: Child threads, loaded lazily by the parser.
    """

    title: str
    rel_path: str
    description: str = ""
    status: str = "active"
    created: date | None = None
    completed: date | None = None
    icon: str | None = None
    tasks: list[Task] = field(default_factory=list)
    children: list["Thread"] = field(default_factory=list)

    @property
    def slug(self) -> str:
        """Return the folder name (last path segment) of this thread."""
        return self.rel_path.rsplit("/", 1)[-1] if self.rel_path else ""

    @property
    def root(self) -> str:
        """Return the top-level root segment (``work`` or ``personal``)."""
        return self.rel_path.split("/", 1)[0] if self.rel_path else ""

    @property
    def pending_count(self) -> int:
        """Number of not-yet-done tasks in this thread only."""
        return sum(1 for t in self.tasks if not t.done)

    def sorted_tasks(self) -> list[Task]:
        """Return tasks with completed ones first, preserving relative order."""
        done = [t for t in self.tasks if t.done]
        pending = [t for t in self.tasks if not t.done]
        return done + pending


def slugify(title: str) -> str:
    """Turn a title into a filesystem-safe kebab-case slug.

    Args:
        title: Arbitrary thread title.

    Returns:
        A lowercase slug containing only ``a-z``, ``0-9`` and hyphens.
    """
    out = []
    prev_dash = False
    for ch in title.strip().lower():
        if ch.isalnum():
            out.append(ch)
            prev_dash = False
        elif not prev_dash:
            out.append("-")
            prev_dash = True
    return "".join(out).strip("-") or "thread"
