"""Configuration utilities for the GitHub feedback CLI."""

from __future__ import annotations

import shutil
from dataclasses import dataclass, field
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, Optional

try:
    import tomllib as tomli  # Python 3.11+
except ModuleNotFoundError:  # pragma: no cover - fallback for older runtimes
    import tomli  # type: ignore[no-redef]
from pydantic import BaseModel, ValidationError
from tomli_w import dump as toml_dump
import keyring

CONFIG_DIR = Path.home() / ".config" / "github_feedback"
CONFIG_FILE = CONFIG_DIR / "config.toml"
CONFIG_VERSION = "1.0.0"
KEYRING_SERVICE = "github-feedback"
KEYRING_USERNAME = "github-pat"


class ServerConfig(BaseModel):
    """Server connection details for GitHub deployments."""

    api_url: str = "https://api.github.com"
    graphql_url: str = "https://api.github.com/graphql"
    web_url: str = "https://github.com"


class LLMConfig(BaseModel):
    """Configuration for the LLM backend."""

    endpoint: str = "http://localhost:8000/v1/chat/completions"
    model: str = ""
    timeout: int = 60
    max_files_in_prompt: int = 10
    max_retries: int = 3


class DefaultsConfig(BaseModel):
    """Default values used when running analyses."""

    months: int = 12


class APIConfig(BaseModel):
    """Configuration for API requests."""

    timeout: int = 30
    max_retries: int = 3


@dataclass(slots=True)
class Config:
    """Top-level configuration container."""

    version: str = CONFIG_VERSION
    server: ServerConfig = field(default_factory=ServerConfig)
    llm: LLMConfig = field(default_factory=LLMConfig)
    api: APIConfig = field(default_factory=APIConfig)
    defaults: DefaultsConfig = field(default_factory=DefaultsConfig)

    @classmethod
    def load(cls, path: Path = CONFIG_FILE) -> "Config":
        """Load configuration data from disk.

        Args:
            path: Optional override for the configuration file path.

        Returns:
            Config: The loaded configuration object.

        Raises:
            ValueError: If configuration file is corrupted or invalid.
        """

        if not path.exists():
            return cls()

        try:
            with path.open("rb") as handle:
                raw: Dict[str, Any] = tomli.load(handle)
        except Exception as exc:
            raise ValueError(f"Failed to parse configuration file: {exc}") from exc

        # Check version for future migrations
        version = raw.get("version", "0.0.0")
        if version != CONFIG_VERSION:
            # Future: handle migrations here
            pass

        try:
            server = ServerConfig(**raw.get("server", {}))
            llm = LLMConfig(**raw.get("llm", {}))
            api = APIConfig(**raw.get("api", {}))
            defaults = DefaultsConfig(**raw.get("defaults", {}))
        except ValidationError as exc:
            raise ValueError(f"Invalid configuration: {exc}") from exc

        return cls(version=version, server=server, llm=llm, api=api, defaults=defaults)

    def dump(self, path: Path = CONFIG_FILE, backup: bool = True) -> None:
        """Persist the configuration to disk.

        Args:
            path: Path to save the configuration file.
            backup: If True and config file exists, create a backup before overwriting.
        """

        CONFIG_DIR.mkdir(parents=True, exist_ok=True)

        # Create backup if file exists and backup is requested
        if backup and path.exists():
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            backup_path = path.parent / f"{path.stem}.{timestamp}.bak"
            shutil.copy2(path, backup_path)

        payload: Dict[str, Any] = {
            "version": self.version,
            "server": self.server.model_dump(),
            "llm": self.llm.model_dump(),
            "api": self.api.model_dump(),
            "defaults": self.defaults.model_dump(),
        }

        with path.open("wb") as handle:
            toml_dump(payload, handle)

    def update_auth(self, pat: str) -> None:
        """Update the stored PAT in system keyring.

        Args:
            pat: GitHub Personal Access Token to store securely.
        """
        keyring.set_password(KEYRING_SERVICE, KEYRING_USERNAME, pat)

    def get_pat(self) -> Optional[str]:
        """Retrieve the stored PAT from system keyring.

        Returns:
            The stored PAT, or None if not set.
        """
        return keyring.get_password(KEYRING_SERVICE, KEYRING_USERNAME)

    def has_pat(self) -> bool:
        """Check if a PAT is stored in the keyring.

        Returns:
            True if PAT is set, False otherwise.
        """
        return self.get_pat() is not None

    def validate_required_fields(self) -> None:
        """Validate that all required configuration fields are set.

        Raises:
            ValueError: If any required field is missing or invalid.
        """
        errors = []

        # Check PAT in keyring
        if not self.has_pat():
            errors.append("GitHub Personal Access Token is not set. Run 'gf init' to configure.")

        # Check LLM endpoint
        if not self.llm.endpoint or self.llm.endpoint == "http://localhost:8000/v1/chat/completions":
            errors.append("LLM endpoint is not configured.")

        # Check LLM model
        if not self.llm.model:
            errors.append("LLM model is not configured.")

        if errors:
            raise ValueError("Configuration is incomplete:\n  - " + "\n  - ".join(errors))

    def to_display_dict(self) -> Dict[str, Any]:
        """Return a serialisable representation for display purposes."""

        auth_display = "<set>" if self.has_pat() else "<not set>"
        return {
            "auth": {"pat": auth_display},
            "server": self.server.model_dump(),
            "llm": self.llm.model_dump(),
            "api": self.api.model_dump(),
            "defaults": self.defaults.model_dump(),
        }
