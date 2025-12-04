"""Init command for GitHub feedback toolkit."""

from __future__ import annotations

import sys
from typing import Optional

import requests
import typer

from github_feedback import cli_helpers, cli_repository
from github_feedback.config import Config
from github_feedback.console import Console
from github_feedback.utils import validate_pat_format, validate_url, validate_months


class InitCommand:
    """Handles initialization and configuration setup."""

    def __init__(self, console: Console):
        """Initialize the command.

        Args:
            console: Console instance for output
        """
        self.console = console

    def execute(
        self,
        pat: Optional[str] = None,
        months: int = 12,
        enterprise_host: Optional[str] = None,
        llm_endpoint: Optional[str] = None,
        llm_model: Optional[str] = None,
        test_connection: bool = True,
    ) -> None:
        """Initialize configuration and store credentials securely.

        This command sets up your GitHub access token, LLM endpoint, and other
        configuration options. Run this once before using other commands.

        Interactive mode: Run without options to be prompted for each value.
        Non-interactive mode: Provide all required options for scripting.

        Args:
            pat: GitHub Personal Access Token
            months: Default analysis window in months
            enterprise_host: Base URL of GitHub Enterprise host
            llm_endpoint: LLM endpoint URL
            llm_model: Model identifier for the LLM
            test_connection: Test LLM connection after configuration
        """
        # Determine if we're in interactive mode
        is_interactive = sys.stdin.isatty()

        # Prompt for missing required values only in interactive mode
        pat, llm_endpoint, llm_model = self._get_required_inputs(
            pat, llm_endpoint, llm_model, is_interactive
        )

        # Enterprise host selection with interactive menu
        enterprise_host, should_save_host = self._get_enterprise_host(
            enterprise_host, is_interactive
        )

        # Validate inputs
        self._validate_inputs(pat, months, llm_endpoint, enterprise_host)

        # Configure server URLs
        api_url, graphql_url, web_url = self._configure_server_urls(enterprise_host)

        # Update and save configuration
        config = self._update_config(
            pat, api_url, graphql_url, web_url, llm_endpoint, llm_model, months
        )

        # Save custom enterprise host if requested
        if should_save_host and enterprise_host and enterprise_host not in config.server.custom_enterprise_hosts:
            config.server.custom_enterprise_hosts.append(enterprise_host)
            self.console.print(f"[success]✓ Saved '{enterprise_host}' to your custom host list[/]")

        # Test LLM connection if requested
        if test_connection:
            self._test_llm_connection(llm_endpoint, llm_model, is_interactive)

        # Save configuration
        config.dump()
        self._print_success_messages()

    def _get_required_inputs(
        self,
        pat: Optional[str],
        llm_endpoint: Optional[str],
        llm_model: Optional[str],
        is_interactive: bool,
    ) -> tuple[str, str, str]:
        """Get required inputs from user or validate provided values.

        Args:
            pat: GitHub Personal Access Token
            llm_endpoint: LLM endpoint URL
            llm_model: Model identifier
            is_interactive: Whether in interactive mode

        Returns:
            Tuple of (pat, llm_endpoint, llm_model)

        Raises:
            typer.Exit: If required values are missing in non-interactive mode
        """
        with cli_helpers.handle_user_interruption("Configuration cancelled by user."):
            if pat is None:
                if is_interactive:
                    pat = typer.prompt("GitHub Personal Access Token", hide_input=True)
                else:
                    self.console.print("[danger]Error:[/] --pat is required in non-interactive mode")
                    raise typer.Exit(code=1)

            if llm_endpoint is None:
                if is_interactive:
                    llm_endpoint = typer.prompt("LLM API endpoint (OpenAI-compatible format)")
                else:
                    self.console.print("[danger]Error:[/] --llm-endpoint is required in non-interactive mode")
                    raise typer.Exit(code=1)

            if llm_model is None:
                if is_interactive:
                    llm_model = typer.prompt("LLM model name (e.g. gpt-4, claude-3-5-sonnet-20241022)")
                else:
                    self.console.print("[danger]Error:[/] --llm-model is required in non-interactive mode")
                    raise typer.Exit(code=1)

        return pat, llm_endpoint, llm_model

    def _get_enterprise_host(
        self,
        enterprise_host: Optional[str],
        is_interactive: bool,
    ) -> tuple[Optional[str], bool]:
        """Get enterprise host configuration.

        Args:
            enterprise_host: Provided enterprise host URL
            is_interactive: Whether in interactive mode

        Returns:
            Tuple of (enterprise_host, should_save_host)

        Raises:
            typer.Exit: If user cancels
        """
        should_save_host = False
        if enterprise_host is None and is_interactive:
            # Load config to get custom hosts
            temp_config = Config.load()
            result = cli_repository.select_enterprise_host_interactive(
                temp_config.server.custom_enterprise_hosts
            )
            if result is None:
                # User cancelled
                self.console.print("\n[warning]Configuration cancelled by user.[/]")
                raise typer.Exit(code=0)
            enterprise_host, should_save_host = result

        return enterprise_host, should_save_host

    def _validate_inputs(
        self,
        pat: str,
        months: int,
        llm_endpoint: str,
        enterprise_host: Optional[str],
    ) -> Optional[str]:
        """Validate all inputs.

        Args:
            pat: GitHub Personal Access Token
            months: Analysis window in months
            llm_endpoint: LLM endpoint URL
            enterprise_host: Enterprise host URL

        Returns:
            Validated enterprise host URL or None

        Raises:
            typer.Exit: If validation fails
        """
        try:
            validate_pat_format(pat)
            validate_months(months)
            validate_url(llm_endpoint, "LLM endpoint")
        except ValueError as exc:
            self.console.print_validation_error(str(exc))
            raise typer.Exit(code=1) from exc

        host_input = (enterprise_host or "").strip()
        if host_input:
            try:
                # Add scheme if missing
                if not host_input.startswith(("http://", "https://")):
                    host_input = f"https://{host_input}"
                validate_url(host_input, "Enterprise host")
                return host_input.rstrip("/")
            except ValueError as exc:
                self.console.print_validation_error(str(exc))
                raise typer.Exit(code=1) from exc

        return None

    def _configure_server_urls(
        self, enterprise_host: Optional[str]
    ) -> tuple[str, str, str]:
        """Configure server URLs based on enterprise host.

        Args:
            enterprise_host: Enterprise host URL or None

        Returns:
            Tuple of (api_url, graphql_url, web_url)
        """
        if enterprise_host:
            api_url = f"{enterprise_host}/api/v3"
            graphql_url = f"{enterprise_host}/api/graphql"
            web_url = enterprise_host
        else:
            api_url = "https://api.github.com"
            graphql_url = "https://api.github.com/graphql"
            web_url = "https://github.com"

        return api_url, graphql_url, web_url

    def _update_config(
        self,
        pat: str,
        api_url: str,
        graphql_url: str,
        web_url: str,
        llm_endpoint: str,
        llm_model: str,
        months: int,
    ) -> Config:
        """Update configuration with provided values.

        Args:
            pat: GitHub Personal Access Token
            api_url: GitHub API URL
            graphql_url: GitHub GraphQL URL
            web_url: GitHub web URL
            llm_endpoint: LLM endpoint URL
            llm_model: LLM model identifier
            months: Default analysis window

        Returns:
            Updated Config instance
        """
        config = Config.load()
        config.update_auth(pat)
        config.server.api_url = api_url
        config.server.graphql_url = graphql_url
        config.server.web_url = web_url
        config.llm.endpoint = llm_endpoint
        config.llm.model = llm_model
        config.defaults.months = months
        return config

    def _test_llm_connection(
        self, llm_endpoint: str, llm_model: str, is_interactive: bool
    ) -> None:
        """Test LLM connection.

        Args:
            llm_endpoint: LLM endpoint URL
            llm_model: LLM model identifier
            is_interactive: Whether in interactive mode

        Raises:
            typer.Exit: If user cancels or declines to save after failed test
        """
        self.console.print()
        with self.console.status("[accent]Testing LLM connection...", spinner="dots"):
            try:
                from github_feedback.llm import LLMClient
                test_client = LLMClient(
                    endpoint=llm_endpoint,
                    model=llm_model,
                    timeout=10,
                )
                test_client.test_connection()
                self.console.print("[success]✓ LLM connection successful[/]")
            except KeyboardInterrupt:
                self.console.print("\n[warning]Configuration cancelled by user.[/]")
                raise typer.Exit(code=0)
            except (requests.RequestException, ValueError, ConnectionError) as exc:
                self.console.print(f"[warning]⚠ LLM connection test failed: {exc}[/]")
                with cli_helpers.handle_user_interruption("Configuration cancelled by user."):
                    if is_interactive and not typer.confirm("Save configuration anyway?", default=True):
                        self.console.print("[info]Configuration not saved[/]")
                        raise typer.Exit(code=1)

    def _print_success_messages(self) -> None:
        """Print success messages after configuration is saved."""
        from github_feedback.cli.formatters.display_formatter import print_config_summary

        self.console.print("[success]✓ Configuration saved successfully[/]")
        self.console.print("[success]✓ GitHub token stored securely in system keyring[/]")
        self.console.print()
        print_config_summary(self.console)
