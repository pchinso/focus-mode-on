"""Runtime configuration, read from environment variables.

All secrets and paths come from the environment so nothing sensitive lives in
the repository. Sensible defaults let the app boot for local use out of the
box; a warning is logged when the default password is in effect.
"""

from __future__ import annotations

import logging
import os
import secrets
from dataclasses import dataclass
from pathlib import Path

logger = logging.getLogger("focus_mode_on")

DEFAULT_PASSWORD = "focus"


def _load_dotenv() -> None:
    """Load a project-root ``.env`` into the environment, if present.

    Best-effort: does nothing when ``python-dotenv`` is unavailable. Real
    environment variables always take precedence over ``.env`` values.
    """
    try:
        from dotenv import load_dotenv
    except ImportError:
        return
    env_path = Path(__file__).resolve().parent.parent / ".env"
    if env_path.exists():
        load_dotenv(env_path, override=False)


def _sanitize_tls_env() -> None:
    """Drop TLS CA-bundle env vars that point to a nonexistent file.

    Some corporate setups leave ``SSL_CERT_FILE`` / ``REQUESTS_CA_BUNDLE``
    pointing at a certificate path that does not exist. Python's ssl/httpx read
    those variables, so a missing file makes *every* HTTPS client (including the
    OpenAI SDK) fail to initialize — which silently disables AI features. When
    the referenced file is missing we remove the variable so TLS falls back to
    the default trust store (certifi), restoring outbound HTTPS.
    """
    for var in ("SSL_CERT_FILE", "REQUESTS_CA_BUNDLE"):
        path = os.environ.get(var)
        if path and not Path(path).exists():
            logger.warning(
                "%s points to a missing file (%s); ignoring it so HTTPS can use "
                "the default trust store.",
                var,
                path,
            )
            del os.environ[var]


def _enable_os_truststore() -> None:
    """Make Python verify TLS against the operating-system trust store.

    On corporate networks an inspecting proxy presents certificates signed by a
    company root CA that lives in the OS trust store (so browsers work) but not
    in certifi's public bundle — which makes outbound HTTPS (e.g. the OpenAI
    API) fail with ``CERTIFICATE_VERIFY_FAILED``. ``truststore`` routes
    verification through the OS store, fixing this transparently. Best-effort:
    if ``truststore`` is unavailable, verification falls back to certifi.
    """
    try:
        import truststore

        truststore.inject_into_ssl()
    except Exception:  # noqa: BLE001 - never let cert setup crash startup
        pass


@dataclass(frozen=True)
class Settings:
    """Effective application settings.

    Attributes:
        vault_dir: Absolute path to the Markdown vault.
        password: Plain password required to log in.
        secret_key: Key used to sign the session cookie.
        openai_key: OpenAI API key, or None to disable AI features.
        using_default_password: True when the fallback password is in use.
    """

    vault_dir: Path
    password: str
    secret_key: str
    openai_key: str | None
    using_default_password: bool


def load_settings() -> Settings:
    """Build :class:`Settings` from the process environment.

    Returns:
        The resolved settings. Missing ``APP_SECRET_KEY`` yields a random,
        per-process key (sessions reset on restart); missing ``APP_PASSWORD``
        falls back to :data:`DEFAULT_PASSWORD` with a warning.
    """
    _load_dotenv()
    _sanitize_tls_env()
    _enable_os_truststore()

    default_vault = Path(__file__).resolve().parent.parent / "vault"
    vault_dir = Path(os.environ.get("VAULT_DIR", str(default_vault))).resolve()

    password = os.environ.get("APP_PASSWORD")
    using_default = password is None
    if using_default:
        password = DEFAULT_PASSWORD
        logger.warning(
            "APP_PASSWORD not set; using the default password %r. "
            "Set APP_PASSWORD before exposing this app.",
            DEFAULT_PASSWORD,
        )

    secret_key = os.environ.get("APP_SECRET_KEY") or secrets.token_hex(32)
    openai_key = os.environ.get("OPENAI_API_KEY") or None

    return Settings(
        vault_dir=vault_dir,
        password=password,
        secret_key=secret_key,
        openai_key=openai_key,
        using_default_password=using_default,
    )
