"""Helper utilities for CLI operations."""

from __future__ import annotations

import logging
from concurrent.futures import ThreadPoolExecutor, as_completed
from contextlib import contextmanager
from pathlib import Path
from typing import Any, Callable, Dict, List, Optional, Tuple

import typer

try:  # pragma: no cover - optional rich dependency
    from rich.progress import (
        BarColumn,
        Progress,
        SpinnerColumn,
        TaskProgressColumn,
        TextColumn,
        TimeRemainingColumn,
    )
except ModuleNotFoundError:  # pragma: no cover - fallback when rich is missing
    Progress = None

from .config import Config
from .console import Console
from .constants import TaskType
from .exceptions import (
    CollectionError,
    CollectionTimeoutError,
    LLMAnalysisError,
    LLMTimeoutError,
)

console = Console()
logger = logging.getLogger(__name__)


@contextmanager
def handle_user_interruption(message: str = "Operation cancelled by user."):
    """Context manager to handle user interruptions consistently.

    Args:
        message: Custom message to display when operation is cancelled

    Yields:
        None

    Raises:
        typer.Exit: Always exits with code 0 when interrupted
    """
    try:
        yield
    except (typer.Abort, KeyboardInterrupt, EOFError):
        console.print(f"\n[warning]{message}[/]")
        raise typer.Exit(code=0)


def validate_collected_data(data: Optional[List], data_type: str) -> List:
    """Validate and log collection results.

    Args:
        data: Collected data list or None
        data_type: Type of data being validated (for logging)

    Returns:
        Empty list if data is None or empty, otherwise the original data
    """
    if data is None:
        logger.warning(
            "Data collection failed",
            extra={
                "component": "feedback_collector",
                "data_type": data_type,
                "status": "failed",
                "count": 0
            }
        )
        return []
    elif not data:
        logger.info(
            "No data found for analysis",
            extra={
                "component": "feedback_collector",
                "data_type": data_type,
                "status": "empty",
                "count": 0
            }
        )
        return []
    else:
        logger.info(
            "Data collection completed",
            extra={
                "component": "feedback_collector",
                "data_type": data_type,
                "status": "success",
                "count": len(data)
            }
        )
        return data


def handle_task_exception(
    exception: Exception,
    key: str,
    label: str,
    timeout: int,
    task_type: TaskType,
) -> tuple[Exception, Any, str]:
    """Handle exceptions from parallel tasks with consistent error creation.

    Args:
        exception: The exception that occurred
        key: Task identifier
        label: Human-readable task label
        timeout: Timeout value in seconds
        task_type: Type of task (TaskType.COLLECTION or TaskType.ANALYSIS)

    Returns:
        Tuple of (error, default_result, status_indicator)
    """
    # Re-raise keyboard interrupts and system exits
    if isinstance(exception, (KeyboardInterrupt, SystemExit)):
        raise exception

    is_timeout = isinstance(exception, TimeoutError)
    is_analysis = task_type == TaskType.ANALYSIS

    if is_timeout:
        error = (
            LLMTimeoutError(f"{label} timed out after {timeout}s", analysis_type=key)
            if is_analysis
            else CollectionTimeoutError(f"{label} timed out after {timeout}s", source=key)
        )
        status_indicator = "⚠"
    else:
        error = (
            LLMAnalysisError(f"{label} failed: {exception}", analysis_type=key)
            if is_analysis
            else CollectionError(f"{label} failed: {exception}", source=key)
        )
        status_indicator = "✗"

    default_result = None if is_analysis else []
    return error, default_result, status_indicator


def run_parallel_tasks(
    tasks: Dict[str, Tuple[Callable, Tuple, str]],
    max_workers: int,
    timeout: int,
    task_type: TaskType = TaskType.COLLECTION,
) -> Dict[str, Any]:
    """Run multiple tasks in parallel with progress indicator and consistent error handling.

    Args:
        tasks: Dict mapping task keys to (func, args, label) tuples where:
            - func: Callable to execute
            - args: Tuple of arguments to pass to func
            - label: Human-readable task label for progress display
        max_workers: Maximum number of concurrent workers
        timeout: Timeout in seconds for each task
        task_type: Type of task (TaskType.COLLECTION or TaskType.ANALYSIS)

    Returns:
        Dict mapping task keys to results (None for failed tasks)
    """
    results = {}
    total = len(tasks)
    timeout_occurred = False

    # Use Rich Progress bar if available
    if Progress is not None:
        with Progress(
            SpinnerColumn(),
            TextColumn("[progress.description]{task.description}"),
            BarColumn(),
            TaskProgressColumn(),
            TimeRemainingColumn(),
            console=console.rich_console if hasattr(console, 'rich_console') else None
        ) as progress:
            task_id = progress.add_task(
                f"[cyan]{task_type.capitalize()}...",
                total=total
            )

            with ThreadPoolExecutor(max_workers=max_workers) as executor:
                futures = {
                    executor.submit(func, *args): (key, label)
                    for key, (func, args, label) in tasks.items()
                }

                for future in as_completed(futures, timeout=timeout):
                    key, label = futures[future]
                    try:
                        results[key] = future.result(timeout=timeout)
                        progress.update(task_id, advance=1, description=f"[green]✓ {label}")
                    except Exception as e:
                        error, default_result, status_indicator = handle_task_exception(
                            e, key, label, timeout, task_type
                        )
                        console.print(f"[warning]{status_indicator} {error}", style="warning")
                        results[key] = default_result
                        color = "yellow" if status_indicator == "⚠" else "red"
                        progress.update(task_id, advance=1, description=f"[{color}]{status_indicator} {label}")

                        # Track if timeout occurred
                        if status_indicator == "⚠":
                            timeout_occurred = True
    else:
        # Fallback to simple progress without Rich
        with ThreadPoolExecutor(max_workers=max_workers) as executor:
            futures = {
                executor.submit(func, *args): (key, label)
                for key, (func, args, label) in tasks.items()
            }

            completed = 0
            for future in as_completed(futures, timeout=timeout):
                key, label = futures[future]
                try:
                    results[key] = future.result(timeout=timeout)
                    completed += 1
                    console.print(f"[success]✓ {label} completed ({completed}/{total})", style="success")
                except Exception as e:
                    error, default_result, status_indicator = handle_task_exception(
                        e, key, label, timeout, task_type
                    )
                    console.print(f"[warning]{status_indicator} {error}", style="warning")
                    results[key] = default_result

                    # Track if timeout occurred
                    if status_indicator == "⚠":
                        timeout_occurred = True

    # Display guidance if timeout occurred
    if timeout_occurred:
        console.print()
        console.print("[cyan]💡 Timeout이 발생했나요?[/]")
        console.print("[dim]   걱정하지 마세요! 같은 명령어를 다시 실행하면 이미 수집된 데이터를 활용하여[/]")
        console.print("[dim]   작업을 이어서 진행합니다. 캐시 덕분에 60-70% 더 빠르게 완료됩니다.[/]")
        console.print()

    return results


def resolve_output_dir(value: Path | str | object) -> Path:
    """Normalise CLI path inputs for both Typer and direct function calls."""
    if isinstance(value, Path):
        return value.expanduser()

    default_candidate = getattr(value, "default", value)
    if isinstance(default_candidate, Path):
        return default_candidate.expanduser()

    return Path(str(default_candidate)).expanduser()


def load_config() -> Config:
    """Load and validate configuration.

    Returns:
        Validated Config instance

    Raises:
        typer.Exit: If configuration is invalid
    """
    try:
        config = Config.load()
        config.validate_required_fields()
        return config
    except ValueError as exc:
        error_msg = str(exc)
        # Check if it's a multi-line error with bullet points
        if "\n" in error_msg:
            lines = error_msg.split("\n")
            console.print(f"[danger]{lines[0]}[/]")
            for line in lines[1:]:
                if line.strip():
                    console.print(f"  {line}")
        else:
            console.print(f"[danger]Configuration error:[/] {error_msg}")
        console.print()
        console.print("[info]Run [accent]gfa init[/] to set up your configuration")
        raise typer.Exit(code=1) from exc
