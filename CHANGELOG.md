# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

### Added
- API request caching using requests-cache for improved performance (default 1-hour expiry for reusable GET/HEAD responses)
- Retry logic with exponential backoff for LLM API calls (default 5 retries with 2s base delay doubling each attempt)
- Comprehensive tests for retrospective analysis module
- Additional tests for review reporter module
- CONTRIBUTING.md with development guidelines
- CHANGELOG.md to track project changes
- Thread-safe keyring fallback initialization with locking mechanism

### Fixed
- Race condition in keyring access during concurrent initialization
- Potential None reference error in artifact label checking (cli.py:1228)

### Changed
- LLM client now supports configurable retry attempts and delays
- API client constructor now accepts cache configuration parameters
- **[Phase 1.1 Refactoring]** Broke down monolithic `constants.py` into organized modules:
  - `constants/analysis_thresholds.py` - Analysis thresholds and scoring
  - `constants/api_config.py` - API configuration constants
  - `constants/awards.py` - Award system constants
  - `constants/limits.py` - Rate limits and constraints
  - `constants/llm_config.py` - LLM configuration defaults
  - `constants/messages.py` - User-facing message templates
  - `constants/regex_patterns.py` - Compiled regex patterns
  - `constants/types.py` - Type definitions
  - `constants/ui_styles.py` - UI styling constants
- **[Phase 1.2 Refactoring]** Restructured CLI layer for better separation of concerns:
  - Created `cli/commands/` package with command implementations:
    - `init_command.py` - Initialization command
    - `config_command.py` - Configuration management
    - `cache_command.py` - Cache management
    - `repository_command.py` - Repository commands
  - Created `cli/formatters/` package for output formatting
  - Created `cli/orchestrators/` package for workflow coordination
  - Improved maintainability and testability of CLI components

## [0.1.0] - 2024-11-13

### Added
- Format feedback as tables for better readability
- Integrated full report generation combining multiple report types
- Retrospective analysis for year-end developer insights
- Code review workflow automation
- Interactive repository selection
- Parallel task execution for data collection
- LLM-powered feedback analysis
- Support for GitHub Enterprise
- Secure credential storage using system keyring
- Comprehensive CLI with multiple commands:
  - `gfa init` - Initialize configuration
  - `gfa feedback` - Generate feedback reports
  - `gfa config` - Manage configuration
  - `gfa repos` - Repository management
- Repository activity metrics collection:
  - Commits analysis
  - Pull requests tracking
  - Code reviews monitoring
  - Issues tracking
- Detailed reporting features:
  - Markdown reports
  - JSON metrics export
  - Interactive console output with Rich
- Collaboration network analysis
- Tech stack analysis
- Award calculation system
- Monthly trend analysis
- Multi-language support (Korean/English)

### Changed
- Consolidated report files to show only final integrated report
- Improved report formatting with better table layouts

### Fixed
- Cleanup unused files and improved prompts
- Enhanced error handling throughout the application
- Improved keyring fallback mechanism for Linux systems

### Security
- Implemented secure credential storage using keyring
- Added PAT validation and authentication checks
- Secure handling of GitHub API tokens

## [0.0.1] - 2024-01-01

### Added
- Initial project structure
- Basic GitHub API integration
- Command-line interface foundation
- Configuration management
- Data collection utilities

---

## Legend

- **Added**: New features
- **Changed**: Changes in existing functionality
- **Deprecated**: Soon-to-be removed features
- **Removed**: Removed features
- **Fixed**: Bug fixes
- **Security**: Security improvements

[Unreleased]: https://github.com/goonbamm/github-feedback-analysis/compare/v0.1.0...HEAD
[0.1.0]: https://github.com/goonbamm/github-feedback-analysis/releases/tag/v0.1.0
[0.0.1]: https://github.com/goonbamm/github-feedback-analysis/releases/tag/v0.0.1
