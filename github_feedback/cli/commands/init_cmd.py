"""Initialize command for GitHub Feedback Analysis CLI.

This module contains the init command which sets up configuration
and credentials for the GitHub feedback toolkit.
"""

from __future__ import annotations

import json
import sys
from contextlib import contextmanager
from pathlib import Path
from typing import Optional, Tuple

import requests
import typer

from ...config import Config
from ...console import Console
from ...utils import validate_pat_format, validate_months, validate_url
from ..utils.config_utils import print_config_summary

console = Console()


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


def _load_default_hosts() -> list[str]:
    """Load default hosts from config file.

    Returns:
        List of default host examples
    """
    # Default fallback hosts if config file is not found
    fallback_hosts = [
        "github.com (Default)",
        "github.company.com",
        "github.enterprise.local",
        "ghe.example.com",
    ]

    try:
        # Get the path to hosts.config.json in the .config directory
        config_path = Path(__file__).parent.parent.parent.parent / ".config" / "hosts.config.json"

        if config_path.exists():
            with open(config_path, 'r', encoding='utf-8') as f:
                config_data = json.load(f)
                return config_data.get("default_hosts", fallback_hosts)
        else:
            return fallback_hosts
    except Exception:
        # If any error occurs, use fallback
        return fallback_hosts


def _select_enterprise_host_interactive(custom_hosts: list[str]) -> Optional[Tuple[str, bool]]:
    """Interactive enterprise host selection with preset and custom options.

    Args:
        custom_hosts: List of user-configured custom enterprise hosts

    Returns:
        Tuple of (selected_host, should_save) or None if cancelled
        - selected_host: The enterprise host URL (empty string for github.com)
        - should_save: Whether to save this host to custom list
    """
    # Load default example hosts from config
    default_hosts = _load_default_hosts()

    console.print("\n[accent]Select GitHub Enterprise Host:[/]")
    console.print("[info]Choose from the list or enter a custom URL[/]\n")

    # Display options
    menu_option = 1

    # Show default github.com option
    console.print(f"  {menu_option}. [success]github.com[/] (Default)")
    github_com_idx = menu_option
    menu_option += 1

    # Show example hosts
    if len(default_hosts) > 1:
        console.print("\n[dim]Example Enterprise Hosts:[/]")
        for host in default_hosts[1:]:
            console.print(f"  {menu_option}. {host}")
            menu_option += 1

    # Show custom hosts if any
    if custom_hosts:
        console.print("\n[dim]Your Saved Hosts:[/]")
        custom_start_idx = menu_option
        for host in custom_hosts:
            console.print(f"  {menu_option}. [accent]{host}[/]")
            menu_option += 1
    else:
        custom_start_idx = menu_option

    console.print(f"\n[info]Or enter a custom host URL (e.g., https://github.example.com)[/]")

    while True:
        try:
            selection = typer.prompt("\nEnter number or custom URL", default="1").strip()

            # Check if it's a number selection
            if selection.isdigit():
                selection_num = int(selection)

                # GitHub.com selection
                if selection_num == github_com_idx:
                    console.print("[success]Selected:[/] github.com (Default)")
                    return ("", False)

                # Example host selection
                elif github_com_idx < selection_num < custom_start_idx:
                    example_idx = selection_num - 2  # -2 because we skip "github.com (Default)" in list
                    if 0 <= example_idx < len(default_hosts) - 1:
                        selected = default_hosts[example_idx + 1]
                        console.print(f"[info]Selected example:[/] {selected}")

                        # Ask if user wants to save this
                        save = typer.confirm("Save this host to your custom list?", default=True)
                        return (selected, save)

                # Custom host selection
                elif custom_hosts and custom_start_idx <= selection_num < custom_start_idx + len(custom_hosts):
                    custom_idx = selection_num - custom_start_idx
                    selected = custom_hosts[custom_idx]
                    console.print(f"[success]Selected:[/] {selected}")
                    return (selected, False)  # Already saved

                else:
                    console.print(f"[danger]Invalid selection.[/] Please enter a number between 1 and {menu_option - 1}")
                    continue

            # Custom URL input
            else:
                console.print(f"[info]Custom host:[/] {selection}")

                # Ask if user wants to save this
                save = typer.confirm("Save this host to your custom list for future use?", default=True)
                return (selection, save)

        except (typer.Abort, KeyboardInterrupt, EOFError):
            console.print("\n[warning]Selection cancelled.[/]")
            return None


def init(
    app: typer.Typer,
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
    with handle_user_interruption("Configuration cancelled by user."):
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
            result = _select_enterprise_host_interactive(temp_config.server.custom_enterprise_hosts)
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
                from ...llm import LLMClient
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
                with handle_user_interruption("Configuration cancelled by user."):
                    if is_interactive and not typer.confirm("Save configuration anyway?", default=True):
                        console.print("[info]Configuration not saved[/]")
                        raise typer.Exit(code=1)

    config.dump()
    console.print("[success]✓ Configuration saved successfully[/]")
    console.print("[success]✓ GitHub token stored securely in system keyring[/]")
    console.print()
    print_config_summary()


def register_command(app: typer.Typer) -> None:
    """Register the init command with the CLI app."""
    app.command()(lambda **kwargs: init(app, **kwargs))
