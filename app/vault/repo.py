"""High-level vault operations used by the web layer.

``VaultRepo`` is the single entry point the app uses to read and mutate the
vault. It serializes writes with a lock, keeps the on-disk Markdown canonical,
and records every mutation as a git commit when a repository is present.
"""

from __future__ import annotations

import shutil
import threading
from datetime import date, datetime
from pathlib import Path

from . import sync
from .model import (
    ARCHIVE_DIR,
    ROOTS,
    THREAD_FILE,
    Task,
    Thread,
    order_tasks,
    slugify,
)
from .parser import load_tree, parse_thread_file
from .writer import write_thread


class VaultError(Exception):
    """Raised when a vault operation cannot be completed."""


class VaultRepo:
    """Read/write access to a Markdown vault rooted at ``base``.

    Args:
        base: Absolute path to the vault directory.
        today: Callable returning the current date (injectable for tests).
        now: Callable returning the current datetime (injectable for tests).
    """

    def __init__(self, base: Path, today=date.today, now=datetime.now) -> None:
        self.base = Path(base)
        self._today = today
        self._now = now
        self._lock = threading.RLock()
        self.base.mkdir(parents=True, exist_ok=True)
        for root in ROOTS:
            (self.base / root).mkdir(exist_ok=True)

    # -- reads -------------------------------------------------------------

    def roots(self) -> list[Thread]:
        """Return the top-level root threads (work, personal) with children."""
        with self._lock:
            result: list[Thread] = []
            for root in ROOTS:
                node = Thread(title=root.title(), rel_path=root)
                node.children = load_tree(self.base, root)
                result.append(node)
            return result

    def get(self, rel_path: str) -> Thread:
        """Load a single thread (with children) by its relative path."""
        rel_path = _clean_rel(rel_path)
        with self._lock:
            folder = self.base / rel_path
            if not folder.is_dir():
                raise VaultError(f"Thread not found: {rel_path}")
            md = folder / THREAD_FILE
            if md.exists():
                thread = parse_thread_file(md, rel_path)
            else:
                thread = Thread(title=folder.name.title(), rel_path=rel_path)
            thread.children = load_tree(self.base, rel_path)
            return thread

    def archived(self) -> list[Thread]:
        """Return the top-most archived threads under the archive directory.

        The archive mirrors the vault's folder structure, so intermediate
        mirror folders (``work``/``personal``) are skipped; only threads whose
        own ``status`` is ``archived`` are returned, and their children are not
        descended into (they were archived together with the parent).
        """
        with self._lock:
            result: list[Thread] = []

            def collect(threads: list[Thread]) -> None:
                for thread in threads:
                    if thread.status == "archived":
                        result.append(thread)
                    else:
                        collect(thread.children)

            collect(load_tree(self.base, ARCHIVE_DIR))
            return result

    # -- mutations ---------------------------------------------------------

    def create_thread(
        self, parent_rel: str, title: str, description: str = "", icon: str | None = None
    ) -> Thread:
        """Create a child thread under ``parent_rel``.

        Args:
            parent_rel: Relative path of the parent (a root like ``work`` or a
                nested thread).
            title: Title of the new thread.
            description: Optional free-text description.
            icon: Optional icon filename.

        Returns:
            The created Thread.
        """
        parent_rel = _clean_rel(parent_rel)
        if parent_rel.split("/", 1)[0] not in ROOTS:
            raise VaultError(f"Parent must live under {ROOTS}: {parent_rel}")
        with self._lock:
            slug = self._unique_slug(parent_rel, slugify(title))
            rel = f"{parent_rel}/{slug}"
            thread = Thread(
                title=title.strip(),
                rel_path=rel,
                description=description.strip(),
                created=self._today(),
                icon=icon,
            )
            write_thread(self.base, thread)
            self._record(f"Create thread {rel}")
            return thread

    def set_icon(self, rel_path: str, icon_name: str) -> None:
        """Set a thread's icon filename in its frontmatter (lock-safe).

        Safe to call from a background thread: the read-modify-write is
        serialized under the vault lock.
        """
        with self._lock:
            thread = self.get(rel_path)
            thread.icon = icon_name
            write_thread(self.base, thread)

    def add_task(
        self, rel_path: str, title: str, parent_path: list[int] | None = None
    ) -> Thread:
        """Add a task, optionally nested under an existing task.

        Args:
            rel_path: Thread to add the task to.
            title: Task text.
            parent_path: Index-path of the parent task (see :meth:`toggle_task`)
                to nest under; ``None`` or empty appends at the top level.

        Returns:
            The reloaded thread.
        """
        with self._lock:
            thread = self.get(rel_path)
            new_task = Task(title=title.strip(), done=False, created=self._now())
            if parent_path:
                parent = _resolve_task(thread.tasks, parent_path)
                parent.children.append(new_task)
                where = f"{thread.rel_path} under “{parent.title}”"
            else:
                thread.tasks.append(new_task)
                where = thread.rel_path
            write_thread(self.base, thread)
            self._record(f"Add task to {where}: {title.strip()}")
            return thread

    def toggle_task(self, rel_path: str, path: list[int]) -> Thread:
        """Toggle the done state of the task at an index-path.

        The index-path addresses a node in the completed-first ordered task
        tree: ``[0]`` is the first top-level task, ``[0, 2]`` is that task's
        third child, and so on — supporting unlimited depth.

        Args:
            rel_path: Thread containing the task.
            path: Non-empty list of indices into the ordered task tree.

        Returns:
            The reloaded thread.
        """
        with self._lock:
            thread = self.get(rel_path)
            task = _resolve_task(thread.tasks, path)
            task.done = not task.done
            task.completed = self._today() if task.done else None
            write_thread(self.base, thread)
            state = "done" if task.done else "pending"
            self._record(f"Mark task {state} in {thread.rel_path}: {task.title}")
            return thread

    def move_task(self, rel_path: str, path: list[int], delta: int) -> Thread:
        """Move a task up (delta -1) or down (delta +1) among its siblings.

        Operates within the same completion group (a pending task cannot move
        above a completed one, since completed tasks always sort first). A move
        that would cross that boundary or run off the ends is a no-op.
        """
        with self._lock:
            thread = self.get(rel_path)
            container, task = _resolve_container(thread.tasks, path)
            ordered = order_tasks(container)
            src = path[-1]
            dst = src + delta
            if 0 <= dst < len(ordered) and ordered[dst].done == task.done:
                other = ordered[dst]
                ci, cj = container.index(task), container.index(other)
                container[ci], container[cj] = container[cj], container[ci]
                write_thread(self.base, thread)
                self._record(f"Reorder task in {thread.rel_path}: {task.title}")
            return thread

    def move_thread(self, rel_path: str, new_parent: str) -> str:
        """Re-parent a thread by moving its folder under ``new_parent``.

        Args:
            rel_path: Thread to move.
            new_parent: A root (``work``/``personal``) or an existing thread
                path to move it under. Cannot be the thread itself or one of
                its own descendants.

        Returns:
            The thread's new relative path.
        """
        rel_path = _clean_rel(rel_path)
        new_parent = _clean_rel(new_parent)
        if new_parent.split("/", 1)[0] not in ROOTS:
            raise VaultError(f"Parent must live under {ROOTS}: {new_parent}")
        if new_parent == rel_path or new_parent.startswith(rel_path + "/"):
            raise VaultError("Cannot move a thread into itself or its subtree")
        with self._lock:
            src = self.base / rel_path
            if not src.is_dir():
                raise VaultError(f"Thread not found: {rel_path}")
            slug = self._unique_slug(new_parent, rel_path.rsplit("/", 1)[-1])
            dest_rel = f"{new_parent}/{slug}"
            dest = self.base / dest_rel
            dest.parent.mkdir(parents=True, exist_ok=True)
            shutil.move(str(src), str(dest))
            self._record(f"Move thread {rel_path} -> {dest_rel}")
            return dest_rel

    def set_accent(self, rel_path: str, accent: str | None) -> Thread:
        """Set (or clear) a thread's accent color in its frontmatter."""
        with self._lock:
            thread = self.get(rel_path)
            thread.accent = accent or None
            write_thread(self.base, thread)
            self._record(f"Set accent {accent} on {thread.rel_path}")
            return thread

    def bulk_apply(
        self, rel_path: str, paths: list[list[int]], action: str
    ) -> Thread:
        """Apply a bulk action (``complete`` or ``delete``) to many tasks.

        All paths are resolved against the current tree *before* any mutation,
        so index shifts during the batch cannot mis-target. Deleting a task that
        was already removed with an ancestor is a no-op.
        """
        with self._lock:
            thread = self.get(rel_path)
            targets = []
            for path in paths:
                try:
                    container, task = _resolve_container(thread.tasks, path)
                    targets.append((container, task))
                except VaultError:
                    continue
            if action == "complete":
                for _, task in targets:
                    if not task.done:
                        task.done = True
                        task.completed = self._today()
            elif action == "delete":
                for container, task in targets:
                    try:
                        container.remove(task)
                    except ValueError:
                        pass
            else:
                raise VaultError(f"Unknown bulk action: {action}")
            write_thread(self.base, thread)
            self._record(f"Bulk {action} {len(targets)} task(s) in {thread.rel_path}")
            return thread

    def set_note(self, rel_path: str, path: list[int], note: str) -> Thread:
        """Set (or clear) a task's single-line note."""
        with self._lock:
            thread = self.get(rel_path)
            task = _resolve_task(thread.tasks, path)
            task.note = note.strip()
            write_thread(self.base, thread)
            self._record(f"Set note in {thread.rel_path}: {task.title}")
            return thread

    def cycle_priority(self, rel_path: str, path: list[int]) -> Thread:
        """Cycle a task's priority: normal → high → low → normal."""
        order = {"normal": "high", "high": "low", "low": "normal"}
        with self._lock:
            thread = self.get(rel_path)
            task = _resolve_task(thread.tasks, path)
            task.priority = order.get(task.priority, "high")
            write_thread(self.base, thread)
            self._record(f"Set priority {task.priority} in {thread.rel_path}: {task.title}")
            return thread

    def set_due(self, rel_path: str, path: list[int], due: date | None) -> Thread:
        """Set (or clear) a task's due date."""
        with self._lock:
            thread = self.get(rel_path)
            task = _resolve_task(thread.tasks, path)
            task.due = due
            write_thread(self.base, thread)
            self._record(f"Set due {due} in {thread.rel_path}: {task.title}")
            return thread

    def rename_task(self, rel_path: str, path: list[int], new_title: str) -> Thread:
        """Rename the task at an index-path, preserving its state and children."""
        with self._lock:
            thread = self.get(rel_path)
            task = _resolve_task(thread.tasks, path)
            task.title = new_title.strip()
            write_thread(self.base, thread)
            self._record(f"Rename task in {thread.rel_path}: {task.title}")
            return thread

    def delete_task(self, rel_path: str, path: list[int]) -> Thread:
        """Delete the task (and its subtree) at an index-path."""
        with self._lock:
            thread = self.get(rel_path)
            container, task = _resolve_container(thread.tasks, path)
            container.remove(task)
            write_thread(self.base, thread)
            self._record(f"Delete task in {thread.rel_path}: {task.title}")
            return thread

    def complete_task_by_title(self, rel_path: str, title: str) -> bool:
        """Mark the best-matching pending task (at any depth) as done."""
        with self._lock:
            thread = self.get(rel_path)
            pending = _all_pending(thread.tasks)
            match = _best_match(title, pending)
            if match is None:
                return False
            match.done = True
            match.completed = self._today()
            write_thread(self.base, thread)
            self._record(f"Complete task in {thread.rel_path}: {match.title}")
            return True

    def complete_thread(self, rel_path: str) -> str:
        """Archive a thread by moving its folder under the archive directory.

        Returns:
            The new relative path inside the archive.
        """
        rel_path = _clean_rel(rel_path)
        with self._lock:
            src = self.base / rel_path
            if not src.is_dir():
                raise VaultError(f"Thread not found: {rel_path}")
            dest_rel = f"{ARCHIVE_DIR}/{rel_path}"
            dest = self.base / dest_rel
            dest.parent.mkdir(parents=True, exist_ok=True)
            if dest.exists():
                dest_rel = self._dedupe_archive(rel_path)
                dest = self.base / dest_rel
            shutil.move(str(src), str(dest))
            md = dest / THREAD_FILE
            if md.exists():
                thread = parse_thread_file(md, dest_rel)
                thread.status = "archived"
                thread.completed = self._today()
                thread.children = load_tree(self.base, dest_rel)
                write_thread(self.base, thread)
            self._record(f"Archive thread {rel_path}")
            return dest_rel

    def purge_thread(self, archive_rel: str) -> None:
        """Permanently delete an archived thread's folder from the vault.

        Irreversible. Only paths under the archive directory may be purged, so
        an active thread can never be destroyed by this call.

        Raises:
            VaultError: If the path is not under the archive or does not exist.
        """
        archive_rel = _clean_rel(archive_rel)
        if not archive_rel.startswith(ARCHIVE_DIR + "/"):
            raise VaultError(f"Not an archived path: {archive_rel}")
        with self._lock:
            target = self.base / archive_rel
            if not target.is_dir():
                raise VaultError(f"Archived thread not found: {archive_rel}")
            shutil.rmtree(target)
            self._record(f"Delete archived thread {archive_rel}")

    def purge_all_archived(self) -> int:
        """Permanently delete every archived thread. Returns the count removed."""
        with self._lock:
            removed = len(self.archived())
            archive = self.base / ARCHIVE_DIR
            if archive.exists():
                shutil.rmtree(archive)
            self._record("Delete all archived threads")
            return removed

    def restore_thread(self, archive_rel: str) -> str:
        """Restore an archived thread back to its original location.

        Args:
            archive_rel: Relative path under the archive directory.

        Returns:
            The restored relative path.
        """
        archive_rel = _clean_rel(archive_rel)
        if not archive_rel.startswith(ARCHIVE_DIR + "/"):
            raise VaultError(f"Not an archived path: {archive_rel}")
        with self._lock:
            src = self.base / archive_rel
            if not src.is_dir():
                raise VaultError(f"Archived thread not found: {archive_rel}")
            dest_rel = archive_rel[len(ARCHIVE_DIR) + 1 :]
            dest = self.base / dest_rel
            dest.parent.mkdir(parents=True, exist_ok=True)
            if dest.exists():
                raise VaultError(f"Cannot restore, path exists: {dest_rel}")
            shutil.move(str(src), str(dest))
            md = dest / THREAD_FILE
            if md.exists():
                thread = parse_thread_file(md, dest_rel)
                thread.status = "active"
                thread.completed = None
                thread.children = load_tree(self.base, dest_rel)
                write_thread(self.base, thread)
            self._record(f"Restore thread {dest_rel}")
            return dest_rel

    # -- helpers -----------------------------------------------------------

    def _unique_slug(self, parent_rel: str, slug: str) -> str:
        """Return a slug that does not collide with an existing sibling."""
        parent = self.base / parent_rel
        candidate = slug
        n = 2
        while (parent / candidate).exists():
            candidate = f"{slug}-{n}"
            n += 1
        return candidate

    def _dedupe_archive(self, rel_path: str) -> str:
        """Return a non-colliding archive path for ``rel_path``."""
        base_rel = f"{ARCHIVE_DIR}/{rel_path}"
        candidate = base_rel
        n = 2
        while (self.base / candidate).exists():
            candidate = f"{base_rel}-{n}"
            n += 1
        return candidate

    def _record(self, message: str) -> None:
        """Commit the mutation to git if the vault is a repository."""
        sync.commit(self.base, message)


def _clean_rel(rel_path: str) -> str:
    """Normalize and reject path traversal in a vault-relative path."""
    rel = rel_path.strip().strip("/").replace("\\", "/")
    parts = [p for p in rel.split("/") if p not in ("", ".")]
    if any(p == ".." for p in parts):
        raise VaultError(f"Illegal path: {rel_path}")
    return "/".join(parts)


def _resolve_task(tasks: list[Task], path: list[int]) -> Task:
    """Return the task addressed by ``path`` in the ordered task tree.

    Each index selects into the completed-first ordering of the current level,
    matching exactly what the UI renders and sends back.

    Raises:
        VaultError: If the path is empty or points outside the tree.
    """
    if not path:
        raise VaultError("Empty task path")
    level = order_tasks(tasks)
    task: Task | None = None
    for depth, index in enumerate(path):
        if not 0 <= index < len(level):
            raise VaultError(f"Task path out of range: {path}")
        task = level[index]
        level = order_tasks(task.children)
    assert task is not None  # non-empty path guarantees assignment
    return task


def _resolve_container(tasks: list[Task], path: list[int]) -> tuple[list[Task], Task]:
    """Return the real sibling list containing the addressed task, plus the task.

    Unlike :func:`_resolve_task`, this also returns the concrete parent list
    (``thread.tasks`` or a task's ``children``) so callers can remove/insert.
    """
    if not path:
        raise VaultError("Empty task path")
    container = tasks
    task: Task | None = None
    for depth, index in enumerate(path):
        ordered = order_tasks(container)
        if not 0 <= index < len(ordered):
            raise VaultError(f"Task path out of range: {path}")
        task = ordered[index]
        if depth < len(path) - 1:
            container = task.children
    assert task is not None
    return container, task


def _all_pending(tasks: list[Task]) -> list[Task]:
    """Flatten every not-done task in a subtree (pre-order)."""
    out: list[Task] = []
    for task in tasks:
        if not task.done:
            out.append(task)
        out.extend(_all_pending(task.children))
    return out


def _best_match(title: str, tasks: list[Task]) -> Task | None:
    """Pick the pending task whose title best matches ``title``.

    Uses a simple normalized token-overlap score; returns None if nothing
    shares any word with the query.
    """
    query = set(_norm(title).split())
    if not query:
        return None
    best: Task | None = None
    best_score = 0
    for task in tasks:
        words = set(_norm(task.title).split())
        score = len(query & words)
        if score > best_score:
            best_score = score
            best = task
    return best if best_score > 0 else None


def _norm(text: str) -> str:
    """Lowercase and strip punctuation for loose token matching."""
    return "".join(c if c.isalnum() or c.isspace() else " " for c in text.lower())
