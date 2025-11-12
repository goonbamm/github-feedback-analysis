"""Console helper that degrades gracefully when Rich is unavailable."""

from __future__ import annotations

from contextlib import contextmanager
from typing import Any, Generator

try:  # pragma: no cover - exercised implicitly
    from rich.console import Console as RichConsole
    from rich.theme import Theme
    from .christmas_theme import is_christmas_season, get_christmas_theme

    _default_theme = Theme(
        {
            "accent": "bold rgb(255,149,0)",
            "muted": "dim",
            "title": "bold rgb(120,200,255)",
            "repo": "bold italic rgb(191,160,255)",
            "label": "bold rgb(160,160,160)",
            "value": "rgb(240,240,240)",
            "success": "bold rgb(104,255,203)",
            "warning": "bold rgb(255,213,128)",
            "danger": "bold rgb(255,128,128)",
            "divider": "rgb(85,85,85)",
            "frame": "rgb(112,141,242)",
        }
    )

    class Console(RichConsole):
        """Rich console pre-configured with a custom theme."""

        def __init__(self, *args: Any, **kwargs: Any) -> None:  # noqa: D401 - mirror rich API
            # Use Christmas theme if in season (Nov 1 - Dec 31)
            import os
            disable_theme = os.getenv("GHF_NO_THEME", "").lower() in ("1", "true", "yes")

            if is_christmas_season() and not disable_theme:
                theme = kwargs.pop("theme", None) or get_christmas_theme()
            else:
                theme = kwargs.pop("theme", None) or _default_theme
            super().__init__(*args, theme=theme, **kwargs)
            self._verbose = False
            self._quiet = False

        def set_verbose(self, verbose: bool) -> None:
            """Enable or disable verbose output."""
            self._verbose = verbose

        def set_quiet(self, quiet: bool) -> None:
            """Enable or disable quiet mode."""
            self._quiet = quiet

        def is_verbose(self) -> bool:
            """Check if verbose mode is enabled."""
            return self._verbose

        def is_quiet(self) -> bool:
            """Check if quiet mode is enabled."""
            return self._quiet

        def print(self, *args: Any, **kwargs: Any) -> None:
            """Print with respect to quiet mode."""
            if not self._quiet:
                super().print(*args, **kwargs)

        def log(self, *args: Any, **kwargs: Any) -> None:
            """Log with respect to verbose mode."""
            if self._verbose and not self._quiet:
                super().log(*args, **kwargs)

except ModuleNotFoundError:  # pragma: no cover - fallback for constrained envs
    class Console:  # type: ignore[override]
        """Minimal stand-in for :class:`rich.console.Console`."""

        def print(self, *values: Any, **kwargs: Any) -> None:  # noqa: D401 - mimic rich API
            text = " ".join(str(value) for value in values)
            if kwargs:
                kw_text = " ".join(f"{key}={value}" for key, value in kwargs.items())
                if text:
                    text = f"{text} {kw_text}"
                else:
                    text = kw_text
            print(text)

        def log(self, *values: Any, **kwargs: Any) -> None:
            self.print(*values, **kwargs)

        @contextmanager
        def status(self, message: str, **_: Any) -> Generator[None, None, None]:
            self.print(message)
            yield

        def rule(self, title: str | None = None, **_: Any) -> None:
            line = "-" * 40
            if title:
                print(f"{line} {title} {line}")
            else:
                print(line)


__all__ = ["Console"]
