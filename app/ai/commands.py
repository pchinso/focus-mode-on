"""Turn natural-language input into structured vault intents.

The layer prefers the OpenAI API (structured output) but always degrades to a
local heuristic parser when the ``openai`` package or an API key is missing, so
the command bar keeps working — just with lower accuracy. Callers apply intents
themselves; low-confidence intents are surfaced for confirmation.
"""

from __future__ import annotations

import json
import os
import re
from dataclasses import dataclass, field

CONFIDENCE_THRESHOLD = 0.75

_SYSTEM_PROMPT = """\
You convert a user's note about their personal task vault into a JSON list of \
intents. The vault has two roots: "work" and "personal", each containing \
nested threads (initiatives/projects) identified by a path like \
"work/website/launch". Return ONLY JSON of the form:
{"intents": [{"action": "...", "thread_path": "...", "title": "...", \
"confidence": 0.0}]}
Valid actions: create_task, complete_task, create_thread, complete_thread, \
restore_thread. "thread_path" is the target thread's path (best guess from the \
provided tree). "title" is the task text or new thread title. "confidence" is \
0..1. Only include intents clearly implied by the note."""


@dataclass
class Intent:
    """A single structured operation derived from user text.

    Attributes:
        action: One of the valid vault actions.
        thread_path: Target thread's vault-relative path.
        title: Task text or new-thread title (may be empty for some actions).
        confidence: Model/heuristic confidence in [0, 1].
    """

    action: str
    thread_path: str
    title: str = ""
    confidence: float = 0.5

    @property
    def needs_confirmation(self) -> bool:
        """True when confidence is below the auto-apply threshold."""
        return self.confidence < CONFIDENCE_THRESHOLD


@dataclass
class InterpretResult:
    """Outcome of interpreting a user note.

    Attributes:
        intents: Parsed intents.
        source: "openai" or "heuristic" — how they were produced.
        note: Optional human-readable message (e.g. degradation reason).
    """

    intents: list[Intent] = field(default_factory=list)
    source: str = "heuristic"
    note: str = ""


class AICommandLayer:
    """Interpret natural language into :class:`Intent` objects.

    Args:
        api_key: OpenAI API key; falls back to ``OPENAI_API_KEY`` env var.
        model: Chat model id to use when the API is available.
    """

    def __init__(self, api_key: str | None = None, model: str = "gpt-4o-mini") -> None:
        self._api_key = api_key or os.environ.get("OPENAI_API_KEY")
        self._model = model
        self._client = self._build_client()

    @property
    def available(self) -> bool:
        """Whether the OpenAI-backed path is usable."""
        return self._client is not None

    def _build_client(self):
        """Construct an OpenAI client, or None if unavailable."""
        if not self._api_key:
            return None
        try:
            from openai import OpenAI  # type: ignore
        except ImportError:
            return None
        try:
            return OpenAI(api_key=self._api_key)
        except Exception:
            return None

    def interpret(
        self, text: str, tree_paths: list[str], default_root: str = "work"
    ) -> InterpretResult:
        """Interpret ``text`` into intents given the available thread paths.

        Args:
            text: Raw user input from the command bar.
            tree_paths: Known thread paths, used as context/validation.
            default_root: Root (``work`` or ``personal``) to assume when the
                note does not clearly name one — set from the active app mode.

        Returns:
            An InterpretResult; never raises for ordinary failures.
        """
        text = text.strip()
        if not text:
            return InterpretResult(source="heuristic", note="Empty input.")
        if self._client is not None:
            try:
                return self._interpret_openai(text, tree_paths)
            except Exception as exc:  # noqa: BLE001 - degrade, never crash the UI
                fallback = _heuristic(text, tree_paths, default_root)
                fallback.note = f"AI unavailable ({exc.__class__.__name__}); used heuristic."
                return fallback
        result = _heuristic(text, tree_paths, default_root)
        result.note = "OpenAI key not configured; used local heuristic."
        return result

    def _interpret_openai(self, text: str, tree_paths: list[str]) -> InterpretResult:
        """Call the OpenAI API and parse its structured response."""
        context = "Known thread paths:\n" + ("\n".join(tree_paths) or "(none yet)")
        response = self._client.chat.completions.create(
            model=self._model,
            messages=[
                {"role": "system", "content": _SYSTEM_PROMPT},
                {"role": "user", "content": f"{context}\n\nNote: {text}"},
            ],
            response_format={"type": "json_object"},
            temperature=0,
        )
        payload = json.loads(response.choices[0].message.content or "{}")
        intents = [_intent_from_dict(d) for d in payload.get("intents", [])]
        return InterpretResult(intents=[i for i in intents if i], source="openai")


def _intent_from_dict(d: dict) -> Intent | None:
    """Build an Intent from a raw dict, returning None if invalid."""
    action = str(d.get("action", "")).strip()
    valid = {
        "create_task",
        "complete_task",
        "create_thread",
        "complete_thread",
        "restore_thread",
    }
    if action not in valid:
        return None
    try:
        confidence = float(d.get("confidence", 0.5))
    except (TypeError, ValueError):
        confidence = 0.5
    return Intent(
        action=action,
        thread_path=str(d.get("thread_path", "")).strip().strip("/"),
        title=str(d.get("title", "")).strip(),
        confidence=max(0.0, min(1.0, confidence)),
    )


# -- Local heuristic fallback ---------------------------------------------

_DONE_WORDS = re.compile(r"\b(done|finished|completed|complete)\b", re.I)
_NEW_THREAD = re.compile(r"\b(new|start|create)\b.*\b(project|initiative|thread)\b", re.I)


def _heuristic(
    text: str, tree_paths: list[str], default_root: str = "work"
) -> InterpretResult:
    """Cheap rule-based interpreter used when the API is not available."""
    root = "work" if re.search(r"\bwork\b", text, re.I) else (
        "personal" if re.search(r"\bpersonal\b", text, re.I) else default_root
    )
    target = _guess_path(text, tree_paths) or root
    if _NEW_THREAD.search(text):
        title = _strip_keywords(text)
        return InterpretResult(
            intents=[Intent("create_thread", root, title, 0.55)], source="heuristic"
        )
    if _DONE_WORDS.search(text):
        title = _DONE_WORDS.sub("", text).strip(" .")
        return InterpretResult(
            intents=[Intent("complete_task", target, title, 0.5)], source="heuristic"
        )
    # Default: treat the note as a new task on the best-guess thread.
    return InterpretResult(
        intents=[Intent("create_task", target, text.strip(), 0.55)], source="heuristic"
    )


def _guess_path(text: str, tree_paths: list[str]) -> str | None:
    """Return the known path whose last segment appears in the text."""
    lowered = text.lower()
    best = None
    best_len = 0
    for path in tree_paths:
        leaf = path.rsplit("/", 1)[-1].replace("-", " ")
        if leaf and leaf in lowered and len(leaf) > best_len:
            best = path
            best_len = len(leaf)
    return best


def _strip_keywords(text: str) -> str:
    """Remove new-thread trigger words to recover a plausible title."""
    cleaned = re.sub(
        r"\b(new|start|create|a|the|work|personal|project|initiative|thread|called|named)\b",
        " ",
        text,
        flags=re.I,
    )
    return re.sub(r"\s+", " ", cleaned).strip(" .:-") or "Untitled"
