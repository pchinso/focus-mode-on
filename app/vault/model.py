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
    """A checklist item inside a thread — the node of an unbounded task tree.

    Tasks nest without limit: any task may contain child tasks (subtasks),
    which may themselves contain further children. On disk this is a nested
    Markdown checklist (indented ``- [ ]`` items).

    Attributes:
        title: Human-readable task text.
        done: Whether the task is completed.
        completed: Completion date, set when ``done`` is True.
        children: Nested subtasks (may be arbitrarily deep).
    """

    title: str
    done: bool = False
    completed: date | None = None
    children: list["Task"] = field(default_factory=list)

    @property
    def has_children(self) -> bool:
        """True when this task has at least one subtask."""
        return bool(self.children)

    def ordered_children(self) -> list["Task"]:
        """Return children with completed ones first (stable within a level)."""
        return order_tasks(self.children)


def order_tasks(tasks: list[Task]) -> list[Task]:
    """Order a list of sibling tasks with completed ones before pending ones.

    Relative order within each group is preserved. Applied at every level of
    the tree so completed items rise to the top consistently.
    """
    done = [t for t in tasks if t.done]
    pending = [t for t in tasks if not t.done]
    return done + pending


def count_pending(tasks: list[Task]) -> int:
    """Count not-done tasks across a whole subtree (recursively)."""
    total = 0
    for task in tasks:
        if not task.done:
            total += 1
        total += count_pending(task.children)
    return total


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
        accent: Optional hex accent color for this thread's identity.
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
    accent: str | None = None
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
        """Number of not-yet-done tasks in this thread, counting all subtasks."""
        return count_pending(self.tasks)

    def sorted_tasks(self) -> list[Task]:
        """Return top-level tasks with completed ones first (stable)."""
        return order_tasks(self.tasks)

    def ordered_tasks(self) -> list[Task]:
        """Alias of :meth:`sorted_tasks`; the top of the recursive task tree."""
        return order_tasks(self.tasks)


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
