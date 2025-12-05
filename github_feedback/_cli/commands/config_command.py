"""Config command for GitHub feedback toolkit."""

from __future__ import annotations

from typing import TYPE_CHECKING, Optional

import typer

from github_feedback.config import Config
from github_feedback.utils import validate_url

if TYPE_CHECKING:
    from github_feedback.console import Console


class ConfigCommand:
    """Handles configuration management commands."""

    def __init__(self, console: Console):
        """Initialize the command.

        Args:
            console: Console instance for output
        """
        self.console = console

    def show(self) -> None:
        """Display current configuration settings.

        Shows your GitHub server URLs, LLM endpoint, and default settings.
        Sensitive values like tokens are masked for security.
        """
        from github_feedback._cli.formatters.display_formatter import print_config_summary

        print_config_summary(self.console)

    def set(self, key: str, value: str) -> None:
        """Set a configuration value.

        Args:
            key: Configuration key in dot notation (e.g. llm.model)
            value: Value to set

        Examples:
            gfa config set llm.model gpt-4
            gfa config set llm.endpoint https://api.openai.com/v1/chat/completions
            gfa config set defaults.months 6

        Raises:
            typer.Exit: If configuration update fails
        """
        try:
            config = Config.load()
            config.set_value(key, value)
            config.dump()
            self.console.print(f"[success]✓ Configuration updated:[/] {key} = {value}")
        except ValueError as exc:
            self.console.print_error(exc)
            raise typer.Exit(code=1) from exc

    def get(self, key: str) -> None:
        """Get a configuration value.

        Args:
            key: Configuration key in dot notation (e.g. llm.model)

        Examples:
            gfa config get llm.model
            gfa config get defaults.months

        Raises:
            typer.Exit: If key not found
        """
        try:
            config = Config.load()
            value = config.get_value(key)
            self.console.print(f"{key} = {value}")
        except ValueError as exc:
            self.console.print_error(exc)
            raise typer.Exit(code=1) from exc

    def hosts(self, action: str, host: Optional[str] = None) -> None:
        """Manage custom enterprise hosts.

        Args:
            action: Action to perform: list, add, or remove
            host: Host URL (required for add/remove actions)

        Examples:
            gfa config hosts list
            gfa config hosts add https://github.company.com
            gfa config hosts remove https://github.company.com

        Raises:
            typer.Exit: If action fails or validation fails
        """
        try:
            config = Config.load()

            if action == "list":
                self._list_hosts(config)
            elif action == "add":
                self._add_host(config, host)
            elif action == "remove":
                self._remove_host(config, host)
            else:
                self.console.print_error(f"Unknown action '{action}'")
                self.console.print("[info]Valid actions:[/] list, add, remove")
                raise typer.Exit(code=1)

        except ValueError as exc:
            self.console.print_error(exc)
            raise typer.Exit(code=1) from exc

    def _list_hosts(self, config: Config) -> None:
        """List all custom enterprise hosts.

        Args:
            config: Configuration instance
        """
        if not config.server.custom_enterprise_hosts:
            self.console.print("[info]No custom enterprise hosts saved.[/]")
            self.console.print("[dim]Add hosts using:[/] gfa config hosts add <host-url>")
        else:
            self.console.print("[accent]Custom Enterprise Hosts:[/]\n")
            for idx, saved_host in enumerate(config.server.custom_enterprise_hosts, 1):
                self.console.print(f"  {idx}. {saved_host}")

    def _add_host(self, config: Config, host: Optional[str]) -> None:
        """Add a custom enterprise host.

        Args:
            config: Configuration instance
            host: Host URL to add

        Raises:
            typer.Exit: If host is None or validation fails
        """
        if not host:
            self.console.print("[danger]Error:[/] Host URL is required for 'add' action")
            self.console.print("[info]Usage:[/] gfa config hosts add <host-url>")
            raise typer.Exit(code=1)

        # Validate and normalize host
        host = host.strip()
        if not host.startswith(("http://", "https://")):
            host = f"https://{host}"

        try:
            validate_url(host, "Enterprise host")
        except ValueError as exc:
            self.console.print_validation_error(str(exc))
            raise typer.Exit(code=1) from exc

        host = host.rstrip("/")

        if host in config.server.custom_enterprise_hosts:
            self.console.print(f"[warning]Host '{host}' is already in your custom list[/]")
        else:
            config.server.custom_enterprise_hosts.append(host)
            config.dump()
            self.console.print(f"[success]✓ Added '{host}' to your custom host list[/]")

    def _remove_host(self, config: Config, host: Optional[str]) -> None:
        """Remove a custom enterprise host.

        Args:
            config: Configuration instance
            host: Host URL to remove

        Raises:
            typer.Exit: If host is None
        """
        if not host:
            self.console.print("[danger]Error:[/] Host URL is required for 'remove' action")
            self.console.print("[info]Usage:[/] gfa config hosts remove <host-url>")
            raise typer.Exit(code=1)

        # Normalize host for comparison
        host = host.strip().rstrip("/")
        if not host.startswith(("http://", "https://")):
            host = f"https://{host}"

        if host in config.server.custom_enterprise_hosts:
            config.server.custom_enterprise_hosts.remove(host)
            config.dump()
            self.console.print(f"[success]✓ Removed '{host}' from your custom host list[/]")
        else:
            self.console.print(f"[warning]Host '{host}' not found in your custom list[/]")
            self.console.print("[info]Use 'gfa config hosts list' to see saved hosts[/]")
