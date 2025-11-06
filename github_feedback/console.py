"""Console helper that degrades gracefully when Rich is unavailable."""

from __future__ import annotations

from typing import Any

try:  # pragma: no cover - exercised implicitly
    from rich.console import Console  # type: ignore
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


__all__ = ["Console"]
