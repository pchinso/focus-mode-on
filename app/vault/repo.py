"""High-level vault operations used by the web layer.

``VaultRepo`` is the single entry point the app uses to read and mutate the
vault. It serializes writes with a lock, keeps the on-disk Markdown canonical,
and records every mutation as a git commit when a repository is present.
"""

from __future__ import annotations

import shutil
import threading
from datetime import date
from pathlib import Path

from . import sync
from .model import ARCHIVE_DIR, ROOTS, THREAD_FILE, Task, Thread, slugify
from .parser import load_tree, parse_thread_file
from .writer import write_thread


class VaultError(Exception):
    """Raised when a vault operation cannot be completed."""


class VaultRepo:
    """Read/write access to a Markdown vault rooted at ``base``.

    Args:
        base: Absolute path to the vault directory.
        today: Callable returning the current date (injectable for tests).
    """

    def __init__(self, base: Path, today=date.today) -> None:
        self.base = Path(base)
        self._today = today
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

    def add_task(self, rel_path: str, title: str) -> Thread:
        """Append a pending task to a thread."""
        with self._lock:
            thread = self.get(rel_path)
            thread.tasks.append(Task(title=title.strip(), done=False))
            write_thread(self.base, thread)
            self._record(f"Add task to {thread.rel_path}: {title.strip()}")
            return thread

    def toggle_task(self, rel_path: str, index: int) -> Thread:
        """Toggle the done state of the task at ``index`` (display order)."""
        with self._lock:
            thread = self.get(rel_path)
            ordered = thread.sorted_tasks()
            if not 0 <= index < len(ordered):
                raise VaultError(f"Task index out of range: {index}")
            task = ordered[index]
            task.done = not task.done
            task.completed = self._today() if task.done else None
            thread.tasks = ordered
            write_thread(self.base, thread)
            state = "done" if task.done else "pending"
            self._record(f"Mark task {state} in {thread.rel_path}: {task.title}")
            return thread

    def complete_task_by_title(self, rel_path: str, title: str) -> bool:
        """Mark the best-matching pending task as done. Returns success."""
        with self._lock:
            thread = self.get(rel_path)
            match = _best_match(title, [t for t in thread.tasks if not t.done])
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
