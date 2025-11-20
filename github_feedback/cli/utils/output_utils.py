"""Output directory and path utilities."""

from pathlib import Path


def resolve_output_dir(value: Path | str | object) -> Path:
    """Normalise CLI path inputs for both Typer and direct function calls."""

    if isinstance(value, Path):
        return value.expanduser()

    default_candidate = getattr(value, "default", value)
    if isinstance(default_candidate, Path):
        return default_candidate.expanduser()

    return Path(str(default_candidate)).expanduser()
