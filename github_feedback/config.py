"""Configuration utilities for the GitHub feedback CLI."""

from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Dict, Optional

import tomli
from pydantic import BaseModel, ValidationError
from tomli_w import dump as toml_dump

CONFIG_DIR = Path.home() / ".config" / "github_feedback"
CONFIG_FILE = CONFIG_DIR / "config.toml"


class AuthConfig(BaseModel):
    """Authentication configuration block."""

    pat: str


class ServerConfig(BaseModel):
    """Server connection details for GitHub deployments."""

    api_url: str = "https://api.github.com"
    graphql_url: str = "https://api.github.com/graphql"
    web_url: str = "https://github.com"
    verify_ssl: bool = True


class LLMConfig(BaseModel):
    """Configuration for the LLM backend."""

    endpoint: str = "http://localhost:8000/v1/chat/completions"
    model: str = ""


class DefaultsConfig(BaseModel):
    """Default values used when running analyses."""

    months: int = 12


@dataclass(slots=True)
class Config:
    """Top-level configuration container."""

    auth: Optional[AuthConfig] = None
    server: ServerConfig = field(default_factory=ServerConfig)
    llm: LLMConfig = field(default_factory=LLMConfig)
    defaults: DefaultsConfig = field(default_factory=DefaultsConfig)

    @classmethod
    def load(cls, path: Path = CONFIG_FILE) -> "Config":
        """Load configuration data from disk.

        Args:
            path: Optional override for the configuration file path.

        Returns:
            Config: The loaded configuration object.
        """

        if not path.exists():
            return cls()

        with path.open("rb") as handle:
            raw: Dict[str, Any] = tomli.load(handle)

        auth = None
        if "auth" in raw and raw["auth"]:
            try:
                auth = AuthConfig(**raw["auth"])
            except ValidationError as exc:
                raise ValueError(f"Invalid auth configuration: {exc}") from exc

        try:
            server = ServerConfig(**raw.get("server", {}))
            llm = LLMConfig(**raw.get("llm", {}))
            defaults = DefaultsConfig(**raw.get("defaults", {}))
        except ValidationError as exc:
            raise ValueError(f"Invalid configuration: {exc}") from exc

        return cls(auth=auth, server=server, llm=llm, defaults=defaults)

    def dump(self, path: Path = CONFIG_FILE) -> None:
        """Persist the configuration to disk."""

        CONFIG_DIR.mkdir(parents=True, exist_ok=True)

        payload: Dict[str, Any] = {
            "server": self.server.model_dump(),
            "llm": self.llm.model_dump(),
            "defaults": self.defaults.model_dump(),
        }
        if self.auth:
            payload["auth"] = self.auth.model_dump()

        with path.open("wb") as handle:
            toml_dump(payload, handle)

    def update_auth(self, pat: str) -> None:
        """Update the stored PAT."""

        self.auth = AuthConfig(pat=pat)

    def to_display_dict(self) -> Dict[str, Any]:
        """Return a serialisable representation for display purposes."""

        auth_display = "<set>" if self.auth else "<not set>"
        return {
            "auth": {"pat": auth_display},
            "server": self.server.model_dump(),
            "llm": self.llm.model_dump(),
            "defaults": self.defaults.model_dump(),
        }
