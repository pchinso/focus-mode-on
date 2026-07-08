"""Generate semantically relevant thread icons via the OpenAI image API.

Icon generation is entirely optional. When the API is unavailable the app uses
a deterministic fallback glyph (thread initials on a token-colored chip),
rendered client-side, so threads always have a visual identity.
"""

from __future__ import annotations

import base64
import logging
import os
from pathlib import Path

logger = logging.getLogger("focus_mode_on")

ICON_FILE = "icon.png"
# gpt-image-1 only supports 1024x1024 / 1024x1536 / 1536x1024 / auto.
ICON_SIZE = "1024x1024"
# The UI shows icons at ~42px; store a small square to keep the vault light.
ICON_STORE_PX = 256


def _downscale_png(raw: bytes, size: int = ICON_STORE_PX) -> bytes:
    """Downscale a PNG to a small square to save space; passthrough on failure.

    Args:
        raw: Original PNG bytes from the image API (typically ~1 MB at 1024px).
        size: Target maximum edge length in pixels.

    Returns:
        Optimized PNG bytes at ``size`` px, or the original bytes if Pillow is
        unavailable or the image cannot be processed.
    """
    try:
        import io

        from PIL import Image

        with Image.open(io.BytesIO(raw)) as img:
            img = img.convert("RGBA")
            img.thumbnail((size, size), Image.LANCZOS)
            out = io.BytesIO()
            img.save(out, format="PNG", optimize=True)
            return out.getvalue()
    except Exception:  # noqa: BLE001 - never fail icon writing over resizing
        return raw


class IconGenerator:
    """Create one small icon image per thread, cached in its folder.

    Args:
        api_key: OpenAI API key; falls back to ``OPENAI_API_KEY`` env var.
        model: Image model id.
    """

    def __init__(self, api_key: str | None = None, model: str = "gpt-image-1") -> None:
        self._api_key = api_key or os.environ.get("OPENAI_API_KEY")
        self._model = model
        self._client = self._build_client()

    @property
    def available(self) -> bool:
        """Whether image generation is usable."""
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

    def generate(self, folder: Path, title: str, description: str = "") -> str | None:
        """Generate and cache an icon for a thread.

        Args:
            folder: Absolute thread folder to write ``icon.png`` into.
            title: Thread title, used to prompt the image.
            description: Optional extra context for the prompt.

        Returns:
            The icon filename on success, or None if generation was skipped or
            failed (the caller then relies on the fallback glyph).
        """
        if self._client is None:
            return None
        prompt = (
            "A minimal, flat, single-subject icon on a plain background "
            "representing: "
            f"{title}. {description}".strip()
        )
        try:
            result = self._client.images.generate(
                model=self._model,
                prompt=prompt,
                size=ICON_SIZE,
                quality="low",
                n=1,
            )
            b64 = result.data[0].b64_json
            if not b64:
                return None
            folder.mkdir(parents=True, exist_ok=True)
            png = _downscale_png(base64.b64decode(b64))
            (folder / ICON_FILE).write_bytes(png)
            return ICON_FILE
        except Exception as exc:  # noqa: BLE001 - non-blocking per spec
            # Best-effort: log so failures are diagnosable, but never raise.
            logger.warning("Icon generation failed for %r: %s", title, exc)
            return None
