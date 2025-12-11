"""Configuration management commands for the CLI."""

from __future__ import annotations

import os
import sys
from pathlib import Path
from typing import Optional

import requests
import typer

try:
    from rich import box
    from rich.table import Table
except ModuleNotFoundError:
    Table = None
    box = None

from . import helpers
from . import repository
from ..core.config import Config
from ..core.console import Console
from ..core.utils import validate_pat_format, validate_url, validate_months

console = Console()


def init(
    pat: Optional[str] = typer.Option(
        None,
        "--pat",
        help="GitHub Personal Access Token (requires 'repo' scope for private repos)",
        hide_input=True,
    ),
    months: int = typer.Option(12, "--months", help="Default analysis window in months"),
    enterprise_host: Optional[str] = typer.Option(
        None,
        "--enterprise-host",
        help=(
            "Base URL of your GitHub Enterprise host (e.g. https://github.example.com). "
            "When provided, API, GraphQL, and web URLs are derived automatically."
        ),
    ),
    llm_endpoint: Optional[str] = typer.Option(
        None,
        "--llm-endpoint",
        help="LLM endpoint URL (e.g. https://api.openai.com/v1/chat/completions)",
    ),
    llm_model: Optional[str] = typer.Option(
        None,
        "--llm-model",
        help="Model identifier for the LLM",
    ),
    test_connection: bool = typer.Option(
        True,
        "--test/--no-test",
        help="Test LLM connection after configuration",
    ),
) -> None:
    """Initialize configuration and store credentials securely.

    This command sets up your GitHub access token, LLM endpoint, and other
    configuration options. Run this once before using other commands.

    Interactive mode: Run without options to be prompted for each value.
    Non-interactive mode: Provide all required options for scripting.
    """

    # Determine if we're in interactive mode
    is_interactive = sys.stdin.isatty()

    # Prompt for missing required values only in interactive mode
    with cli_helpers.handle_user_interruption("Configuration cancelled by user."):
        if pat is None:
            if is_interactive:
                pat = typer.prompt("GitHub Personal Access Token", hide_input=True)
            else:
                console.print("[danger]Error:[/] --pat is required in non-interactive mode")
                raise typer.Exit(code=1)

        if llm_endpoint is None:
            if is_interactive:
                llm_endpoint = typer.prompt("LLM API endpoint (OpenAI-compatible format)")
            else:
                console.print("[danger]Error:[/] --llm-endpoint is required in non-interactive mode")
                raise typer.Exit(code=1)

        if llm_model is None:
            if is_interactive:
                llm_model = typer.prompt("LLM model name (e.g. gpt-4, claude-3-5-sonnet-20241022)")
            else:
                console.print("[danger]Error:[/] --llm-model is required in non-interactive mode")
                raise typer.Exit(code=1)

        # Enterprise host selection with interactive menu
        should_save_host = False
        if enterprise_host is None and is_interactive:
            # Load config to get custom hosts
            temp_config = Config.load()
            result = cli_repository.select_enterprise_host_interactive(temp_config.server.custom_enterprise_hosts)
            if result is None:
                # User cancelled
                console.print("\n[warning]Configuration cancelled by user.[/]")
                raise typer.Exit(code=0)
            enterprise_host, should_save_host = result

    # Validate inputs
    try:
        validate_pat_format(pat)
        validate_months(months)
        validate_url(llm_endpoint, "LLM endpoint")
    except ValueError as exc:
        console.print_validation_error(str(exc))
        raise typer.Exit(code=1) from exc

    host_input = (enterprise_host or "").strip()
    if host_input:
        try:
            # Add scheme if missing
            if not host_input.startswith(("http://", "https://")):
                host_input = f"https://{host_input}"
            validate_url(host_input, "Enterprise host")
            host = host_input.rstrip("/")
        except ValueError as exc:
            console.print_validation_error(str(exc))
            raise typer.Exit(code=1) from exc

        api_url = f"{host}/api/v3"
        graphql_url = f"{host}/api/graphql"
        web_url = host
    else:
        api_url = "https://api.github.com"
        graphql_url = "https://api.github.com/graphql"
        web_url = "https://github.com"

    config = Config.load()
    config.update_auth(pat)
    config.server.api_url = api_url
    config.server.graphql_url = graphql_url
    config.server.web_url = web_url
    config.llm.endpoint = llm_endpoint
    config.llm.model = llm_model
    config.defaults.months = months

    # Save custom enterprise host if requested
    if should_save_host and host_input and host_input not in config.server.custom_enterprise_hosts:
        config.server.custom_enterprise_hosts.append(host_input)
        console.print(f"[success]✓ Saved '{host_input}' to your custom host list[/]")

    # Test LLM connection if requested
    if test_connection:
        console.print()
        with console.status("[accent]Testing LLM connection...", spinner="dots"):
            try:
                from .llm import LLMClient
                test_client = LLMClient(
                    endpoint=llm_endpoint,
                    model=llm_model,
                    timeout=10,
                )
                test_client.test_connection()
                console.print("[success]✓ LLM connection successful[/]")
            except KeyboardInterrupt:
                console.print("\n[warning]Configuration cancelled by user.[/]")
                raise typer.Exit(code=0)
            except (requests.RequestException, ValueError, ConnectionError) as exc:
                console.print(f"[warning]⚠ LLM connection test failed: {exc}[/]")
                with cli_helpers.handle_user_interruption("Configuration cancelled by user."):
                    if is_interactive and not typer.confirm("Save configuration anyway?", default=True):
                        console.print("[info]Configuration not saved[/]")
                        raise typer.Exit(code=1)

    config.dump()
    console.print("[success]✓ Configuration saved successfully[/]")
    console.print("[success]✓ GitHub token stored securely in system keyring[/]")
    console.print()
    print_config_summary()


def show_config() -> None:
    """Display current configuration settings.

    Shows your GitHub server URLs, LLM endpoint, and default settings.
    Sensitive values like tokens are masked for security.
    """
    print_config_summary()


def print_config_summary() -> None:
    """Render the current configuration in either table or plain format."""

    config = cli_helpers.load_config()
    data = config.to_display_dict()

    if Table is None:
        console.print("GitHub Feedback Configuration")
        for section, values in data.items():
            console.print(f"[{section}]")
            for key, value in values.items():
                console.print(f"{key} = {value}")
            console.print("")
        return

    table = Table(
        title="GitHub Feedback Configuration",
        box=box.ROUNDED,
        title_style="title",
        border_style="frame",
        expand=True,
        show_lines=True,
    )
    table.add_column("Section", style="label", no_wrap=True)
    table.add_column("Values", style="value")

    for section, values in data.items():
        rendered_values = "\n".join(f"[label]{k}[/]: [value]{v}[/]" for k, v in values.items())
        table.add_row(f"[accent]{section}[/]", rendered_values)

    console.print(table)


def config_set(
    key: str = typer.Argument(..., help="Configuration key in dot notation (e.g. llm.model)"),
    value: str = typer.Argument(..., help="Value to set"),
) -> None:
    """Set a configuration value.

    Examples:
        gfa config set llm.model gpt-4
        gfa config set llm.endpoint https://api.openai.com/v1/chat/completions
        gfa config set defaults.months 6
    """
    try:
        config = Config.load()
        config.set_value(key, value)
        config.dump()
        console.print(f"[success]✓ Configuration updated:[/] {key} = {value}")
    except ValueError as exc:
        console.print_error(exc)
        raise typer.Exit(code=1) from exc


def config_get(
    key: str = typer.Argument(..., help="Configuration key in dot notation (e.g. llm.model)"),
) -> None:
    """Get a configuration value.

    Examples:
        gfa config get llm.model
        gfa config get defaults.months
    """
    try:
        config = Config.load()
        value = config.get_value(key)
        console.print(f"{key} = {value}")
    except ValueError as exc:
        console.print_error(exc)
        raise typer.Exit(code=1) from exc


def config_hosts(
    action: str = typer.Argument(
        ...,
        help="Action to perform: list, add, or remove"
    ),
    host: Optional[str] = typer.Argument(
        None,
        help="Host URL (required for add/remove actions)"
    ),
) -> None:
    """Manage custom enterprise hosts.

    Examples:
        gfa config hosts list
        gfa config hosts add https://github.company.com
        gfa config hosts remove https://github.company.com
    """
    try:
        config = Config.load()

        if action == "list":
            if not config.server.custom_enterprise_hosts:
                console.print("[info]No custom enterprise hosts saved.[/]")
                console.print("[dim]Add hosts using:[/] gfa config hosts add <host-url>")
            else:
                console.print("[accent]Custom Enterprise Hosts:[/]\n")
                for idx, saved_host in enumerate(config.server.custom_enterprise_hosts, 1):
                    console.print(f"  {idx}. {saved_host}")

        elif action == "add":
            if not host:
                console.print("[danger]Error:[/] Host URL is required for 'add' action")
                console.print("[info]Usage:[/] gfa config hosts add <host-url>")
                raise typer.Exit(code=1)

            # Validate and normalize host
            host = host.strip()
            if not host.startswith(("http://", "https://")):
                host = f"https://{host}"

            try:
                validate_url(host, "Enterprise host")
            except ValueError as exc:
                console.print_validation_error(str(exc))
                raise typer.Exit(code=1) from exc

            host = host.rstrip("/")

            if host in config.server.custom_enterprise_hosts:
                console.print(f"[warning]Host '{host}' is already in your custom list[/]")
            else:
                config.server.custom_enterprise_hosts.append(host)
                config.dump()
                console.print(f"[success]✓ Added '{host}' to your custom host list[/]")

        elif action == "remove":
            if not host:
                console.print("[danger]Error:[/] Host URL is required for 'remove' action")
                console.print("[info]Usage:[/] gfa config hosts remove <host-url>")
                raise typer.Exit(code=1)

            # Normalize host for comparison
            host = host.strip().rstrip("/")
            if not host.startswith(("http://", "https://")):
                host = f"https://{host}"

            if host in config.server.custom_enterprise_hosts:
                config.server.custom_enterprise_hosts.remove(host)
                config.dump()
                console.print(f"[success]✓ Removed '{host}' from your custom host list[/]")
            else:
                console.print(f"[warning]Host '{host}' not found in your custom list[/]")
                console.print("[info]Use 'gfa config hosts list' to see saved hosts[/]")

        else:
            console.print_error(f"Unknown action '{action}'")
            console.print("[info]Valid actions:[/] list, add, remove")
            raise typer.Exit(code=1)

    except ValueError as exc:
        console.print_error(exc)
        raise typer.Exit(code=1) from exc


def show_config_deprecated() -> None:
    """Display current configuration settings (deprecated: use 'gfa config show')."""
    console.print("[warning]Note:[/] 'gfa show-config' is deprecated. Use 'gfa config show' instead.")
    console.print()
    print_config_summary()
