"""Configuration utilities for the GitHub feedback CLI."""

from __future__ import annotations

import shutil
import threading
from dataclasses import dataclass, field
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, Optional

try:
    import tomllib as tomli  # Python 3.11+
except ModuleNotFoundError:  # pragma: no cover - fallback for older runtimes
    import tomli  # type: ignore[no-redef]
from pydantic import BaseModel, ValidationError, field_validator
from tomli_w import dump as toml_dump
import keyring
from keyring.errors import KeyringError

CONFIG_DIR = Path.home() / ".config" / "github_feedback"
CONFIG_FILE = CONFIG_DIR / "config.toml"
CONFIG_VERSION = "1.0.0"
KEYRING_SERVICE = "github-feedback"
KEYRING_USERNAME = "github-pat"

# Lock for thread-safe keyring fallback setup
_keyring_lock = threading.Lock()
_keyring_fallback_attempted = False


def _setup_keyring_fallback() -> bool:
    """Set up a fallback keyring backend if the default backend fails.

    This is particularly useful on Linux systems where the D-Bus secrets service
    may not have a 'login' collection or may not be accessible.

    Thread-safe: Uses a lock to prevent race conditions when multiple threads
    try to set up the fallback keyring simultaneously.

    Returns:
        True if a working keyring backend was set up, False otherwise.
    """
    import sys
    import warnings

    global _keyring_fallback_attempted

    # Fast path: if we already tried, don't do it again
    if _keyring_fallback_attempted:
        return False

    # Use lock to ensure only one thread sets up the fallback
    with _keyring_lock:
        # Double-check pattern: another thread might have set it up while we waited
        if _keyring_fallback_attempted:
            return False

        _keyring_fallback_attempted = True

        try:
            # First try encrypted file backend if keyrings.alt is available
            try:
                from keyrings.alt.file import EncryptedKeyring
                keyring.set_keyring(EncryptedKeyring())
                # Test the backend
                try:
                    keyring.get_password(KEYRING_SERVICE, "test")
                    return True
                except Exception:
                    # EncryptedKeyring is available but needs to be initialized
                    # This is fine, it will work when we try to set a password
                    return True
            except ImportError:
                # keyrings.alt is not available, try other backends
                pass

            # If keyrings.alt is not available, try other available backends
            from keyring.backends import fail

            # Get all available backends
            available = keyring.backend.get_all_keyring()

            # Filter out fail/null backends and sort by priority
            viable = [
                b for b in available
                if not isinstance(b, fail.Keyring) and b.priority > 0
            ]

            if viable:
                # Sort by priority (highest first) and use the best one
                viable.sort(key=lambda x: x.priority, reverse=True)

                # Try each backend until we find one that works
                for backend in viable:
                    backend_name = backend.__class__.__name__
                    # Skip SecretService backend if we're trying fallbacks
                    # (it likely already failed)
                    if 'SecretService' in backend_name:
                        continue

                    try:
                        # Test the backend
                        keyring.set_keyring(backend)
                        keyring.get_password(KEYRING_SERVICE, "test")
                        # If we get here, it works
                        return True
                    except Exception:
                        continue

                # No working backend found
                warnings.warn(
                    "System keyring is not accessible. "
                    "Install 'keyrings.alt' for secure storage: pip install keyrings.alt",
                    UserWarning
                )
                return False
            else:
                warnings.warn(
                    "No secure keyring backend available. "
                    "Install 'keyrings.alt' for secure storage: pip install keyrings.alt",
                    UserWarning
                )
                return False

        except Exception as e:
            # If all else fails, warn the user
            warnings.warn(
                f"Failed to set up keyring fallback: {e}. "
                "Install 'keyrings.alt' for secure storage: pip install keyrings.alt",
                UserWarning
            )
            return False


class ServerConfig(BaseModel):
    """Server connection details for GitHub deployments."""

    api_url: str = "https://api.github.com"
    graphql_url: str = "https://api.github.com/graphql"
    web_url: str = "https://github.com"
    custom_enterprise_hosts: list[str] = []


class LLMConfig(BaseModel):
    """Configuration for the LLM backend."""

    endpoint: str = ""
    model: str = ""
    timeout: int = 60
    max_files_in_prompt: int = 10
    max_files_with_patch_snippets: int = 5
    max_retries: int = 3

    @field_validator("timeout", "max_files_in_prompt", "max_files_with_patch_snippets", "max_retries")
    @classmethod
    def validate_positive(cls, v: int, info) -> int:
        """Validate that numeric fields are positive."""
        if v <= 0:
            raise ValueError(f"{info.field_name} must be positive, got {v}")
        return v

    @field_validator("endpoint")
    @classmethod
    def validate_endpoint(cls, v: str) -> str:
        """Validate endpoint URL format if provided."""
        if v and not v.startswith(("http://", "https://")):
            raise ValueError(f"endpoint must be a valid HTTP(S) URL, got: {v}")
        return v


class DefaultsConfig(BaseModel):
    """Default values used when running analyses."""

    months: int = 12

    @field_validator("months")
    @classmethod
    def validate_positive(cls, v: int) -> int:
        """Validate that months is positive."""
        if v <= 0:
            raise ValueError(f"months must be positive, got {v}")
        return v


class APIConfig(BaseModel):
    """Configuration for API requests."""

    timeout: int = 30
    max_retries: int = 3

    @field_validator("timeout", "max_retries")
    @classmethod
    def validate_positive(cls, v: int, info) -> int:
        """Validate that numeric fields are positive."""
        if v <= 0:
            raise ValueError(f"{info.field_name} must be positive, got {v}")
        return v


class ReporterConfig(BaseModel):
    """Configuration for report generation."""

    chart_width: int = 520
    chart_height_per_item: int = 24
    chart_bar_color: str = "#4CAF50"

    @field_validator("chart_width", "chart_height_per_item")
    @classmethod
    def validate_positive(cls, v: int, info) -> int:
        """Validate that chart dimensions are positive."""
        if v <= 0:
            raise ValueError(f"{info.field_name} must be positive, got {v}")
        return v


@dataclass(slots=True)
class Config:
    """Top-level configuration container."""

    version: str = CONFIG_VERSION
    server: ServerConfig = field(default_factory=ServerConfig)
    llm: LLMConfig = field(default_factory=LLMConfig)
    api: APIConfig = field(default_factory=APIConfig)
    defaults: DefaultsConfig = field(default_factory=DefaultsConfig)
    reporter: ReporterConfig = field(default_factory=ReporterConfig)

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
            reporter = ReporterConfig(**raw.get("reporter", {}))
        except ValidationError as exc:
            raise ValueError(f"Invalid configuration: {exc}") from exc

        return cls(version=version, server=server, llm=llm, api=api, defaults=defaults, reporter=reporter)

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
            "reporter": self.reporter.model_dump(),
        }

        with path.open("wb") as handle:
            toml_dump(payload, handle)

    def update_auth(self, pat: str) -> None:
        """Update the stored PAT in system keyring.

        Args:
            pat: GitHub Personal Access Token to store securely.

        Raises:
            RuntimeError: If unable to store credentials in any keyring backend.
        """
        last_error = None

        # First attempt with default keyring
        try:
            keyring.set_password(KEYRING_SERVICE, KEYRING_USERNAME, pat)
            return  # Success!
        except Exception as e:
            last_error = e
            # Store the error but continue to try fallback

        # Try to set up fallback and retry
        if _setup_keyring_fallback():
            try:
                keyring.set_password(KEYRING_SERVICE, KEYRING_USERNAME, pat)
                return  # Success with fallback!
            except Exception as fallback_error:
                last_error = fallback_error

        # If all else fails, provide a helpful error message
        error_msg = (
            f"Failed to store credentials securely. "
            f"Error: {last_error}. "
            f"\n\n"
            f"To fix this issue:\n"
            f"1. Install keyrings.alt for file-based secure storage:\n"
            f"   pip install keyrings.alt\n"
            f"\n"
            f"2. Or set up your system keyring:\n"
            f"   - Linux: Install and configure gnome-keyring or kwallet\n"
            f"   - See docs/KEYRING_TROUBLESHOOTING.md for details"
        )
        raise RuntimeError(error_msg) from last_error

    def get_pat(self) -> Optional[str]:
        """Retrieve the stored PAT from system keyring.

        Returns:
            The stored PAT, or None if not set.

        Raises:
            RuntimeError: If unable to access the keyring backend.
        """
        last_error = None

        # First attempt with default keyring
        try:
            return keyring.get_password(KEYRING_SERVICE, KEYRING_USERNAME)
        except Exception as e:
            last_error = e
            # Store the error but continue to try fallback

        # Try to set up fallback and retry
        if _setup_keyring_fallback():
            try:
                return keyring.get_password(KEYRING_SERVICE, KEYRING_USERNAME)
            except Exception as fallback_error:
                last_error = fallback_error

        # If all else fails, provide a helpful error message
        error_msg = (
            f"Failed to retrieve credentials from keyring. "
            f"Error: {last_error}. "
            f"\n\n"
            f"To fix this issue:\n"
            f"1. Install keyrings.alt for file-based secure storage:\n"
            f"   pip install keyrings.alt\n"
            f"\n"
            f"2. Or set up your system keyring:\n"
            f"   - Linux: Install and configure gnome-keyring or kwallet\n"
            f"   - See docs/KEYRING_TROUBLESHOOTING.md for details"
        )
        raise RuntimeError(error_msg) from last_error

    def has_pat(self) -> bool:
        """Check if a PAT is stored in the keyring.

        Returns:
            True if PAT is set, False otherwise or if keyring is inaccessible.
        """
        try:
            return self.get_pat() is not None
        except RuntimeError:
            # If we can't access the keyring, assume no PAT is stored
            return False

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
        if not self.llm.endpoint:
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
            "reporter": self.reporter.model_dump(),
        }

    def set_value(self, key: str, value: str) -> None:
        """Set a configuration value using dot notation.

        Args:
            key: Configuration key in dot notation (e.g., 'llm.model', 'defaults.months')
            value: Value to set (will be converted to appropriate type)

        Raises:
            ValueError: If key is invalid or value cannot be converted
        """
        parts = key.split(".")
        if len(parts) != 2:
            raise ValueError(f"Invalid key format '{key}'. Expected format: section.field")

        section, field = parts

        # Map section names to config objects
        sections = {
            "server": self.server,
            "llm": self.llm,
            "api": self.api,
            "defaults": self.defaults,
            "reporter": self.reporter,
        }

        if section not in sections:
            valid_sections = ", ".join(sections.keys())
            raise ValueError(f"Invalid section '{section}'. Valid sections: {valid_sections}")

        config_obj = sections[section]

        # Check if field exists
        if not hasattr(config_obj, field):
            valid_fields = ", ".join(config_obj.model_fields.keys())
            raise ValueError(f"Invalid field '{field}' for section '{section}'. Valid fields: {valid_fields}")

        # Get field type and convert value
        field_info = config_obj.model_fields[field]
        field_type = field_info.annotation

        try:
            # Handle basic types
            if field_type == int or field_type == "int":
                converted_value = int(value)
            elif field_type == float or field_type == "float":
                converted_value = float(value)
            elif field_type == bool or field_type == "bool":
                converted_value = value.lower() in ("true", "1", "yes", "on")
            else:
                converted_value = value

            # Validate and set the value using Pydantic's validation
            # Create a new model instance with the updated value to trigger validators
            current_data = config_obj.model_dump()
            current_data[field] = converted_value
            validated_model = type(config_obj).model_validate(current_data)

            # Copy all fields from validated model to current config object
            for field_name in validated_model.model_fields.keys():
                setattr(config_obj, field_name, getattr(validated_model, field_name))

        except (ValueError, TypeError) as exc:
            raise ValueError(f"Cannot convert '{value}' to {field_type} for {key}") from exc
        except ValidationError as exc:
            # Extract error message from Pydantic validation error
            error_msg = "; ".join([f"{'.'.join(str(loc) for loc in e['loc'])}: {e['msg']}" for e in exc.errors()])
            raise ValueError(f"Validation error for {key}: {error_msg}") from exc

    def get_value(self, key: str) -> Any:
        """Get a configuration value using dot notation.

        Args:
            key: Configuration key in dot notation (e.g., 'llm.model')

        Returns:
            The configuration value

        Raises:
            ValueError: If key is invalid
        """
        parts = key.split(".")
        if len(parts) != 2:
            raise ValueError(f"Invalid key format '{key}'. Expected format: section.field")

        section, field = parts

        sections = {
            "server": self.server,
            "llm": self.llm,
            "api": self.api,
            "defaults": self.defaults,
            "reporter": self.reporter,
        }

        if section not in sections:
            valid_sections = ", ".join(sections.keys())
            raise ValueError(f"Invalid section '{section}'. Valid sections: {valid_sections}")

        config_obj = sections[section]

        if not hasattr(config_obj, field):
            valid_fields = ", ".join(config_obj.model_fields.keys())
            raise ValueError(f"Invalid field '{field}' for section '{section}'. Valid fields: {valid_fields}")

        return getattr(config_obj, field)
