# 🚀 GitHub Feedback Analysis

As a developer, do you want feedback but don't know where to start with your year-end retrospective? A CLI tool that analyzes **your activity** on GitHub and automatically generates insightful reports. Supports both GitHub.com and GitHub Enterprise, with LLM-powered automated review capabilities.

English | [한국어](../README.md) | [简体中文](README_ZH.md) | [日本語](README_JA.md) | [Español](README_ES.md)

## ✨ Key Features

- 📊 **Personal Activity Analysis**: Aggregate and analyze **your** commits, issues, and review activity in specific repositories by period
- 🤖 **LLM-Based Feedback**: Detailed analysis of your commit messages, PR titles, review tone, and issue quality
- 🎯 **Integrated Retrospective Report**: Comprehensive insights with personal activity metrics
- 🏆 **Achievement Visualization**: Automatically generate awards and highlights based on your contributions
- 💡 **Repository Discovery**: List accessible repositories and suggest active ones
- 🎨 **Interactive Mode**: User-friendly interface for direct repository selection

## 📋 Prerequisites

- Python 3.11 or higher
- [uv](https://docs.astral.sh/uv/) or your preferred package manager
- GitHub Personal Access Token
  - Private repositories: `repo` permission
  - Public repositories: `public_repo` permission
- LLM API endpoint (OpenAI-compatible format)

## 🔑 Generating GitHub Personal Access Token

<details>
<summary><b>📖 View Token Generation Guide (Click to Expand)</b></summary>

You need a GitHub Personal Access Token (PAT) to use this tool.

### How to Generate

1. **Access GitHub Settings**
   - Go to [GitHub Settings → Developer settings → Personal access tokens → Tokens (classic)](https://github.com/settings/tokens)
   - Or: GitHub Profile → Settings → Developer settings → Personal access tokens

2. **Generate New Token**
   - Click "Generate new token" → "Generate new token (classic)"
   - Note: Enter token purpose (e.g., "GitHub Feedback Analysis")
   - Expiration: Set expiration period (recommended: 90 days or Custom)

3. **Select Permissions**
   - **Public repositories only**: Check `public_repo`
   - **Including private repositories**: Check entire `repo`
   - Other permissions are not required

4. **Generate and Copy Token**
   - Click "Generate token"
   - Copy the generated token (starts with ghp_) and store it securely
   - ⚠️ **Important**: You won't be able to see this token again after leaving the page

5. **Use Token**
   - Enter the copied token when running `gfa init`

### Using Fine-grained Personal Access Token (Optional)

To use the newer fine-grained tokens:
1. Go to [Personal access tokens → Fine-grained tokens](https://github.com/settings/personal-access-tokens/new)
2. Repository access: Select repositories to analyze
3. Set Permissions:
   - **Contents**: Read-only (required)
   - **Metadata**: Read-only (automatically selected)
   - **Pull requests**: Read-only (required)
   - **Issues**: Read-only (required)

### For GitHub Enterprise Users

If you're using GitHub Enterprise in your organization:
1. **Access Enterprise Server Token Page**
   - `https://github.your-company.com/settings/tokens` (replace with your company domain)
   - Or: Profile → Settings → Developer settings → Personal access tokens

2. **Permission Settings Remain the Same**
   - Private repositories: `repo` permission
   - Public repositories: `public_repo` permission

3. **Specify Enterprise Host During Initial Setup**
   ```bash
   gfa init --enterprise-host https://github.your-company.com
   ```

4. **Contact Administrator**
   - PAT generation may be restricted in some Enterprise environments
   - Contact your GitHub administrator if you encounter issues

### References

- [GitHub Docs: Managing Personal Access Tokens](https://docs.github.com/en/authentication/keeping-your-account-and-data-secure/managing-your-personal-access-tokens)
- [GitHub Docs: Fine-grained PAT](https://docs.github.com/en/authentication/keeping-your-account-and-data-secure/managing-your-personal-access-tokens#fine-grained-personal-access-tokens)
- [GitHub Enterprise Server Documentation](https://docs.github.com/en/enterprise-server@latest/authentication/keeping-your-account-and-data-secure/managing-your-personal-access-tokens)

</details>

## 🔧 Installation

```bash
# Copy the repository
git clone https://github.com/goonbamm/github-feedback-analysis.git
cd github-feedback-analysis

# Create and activate virtual environment
uv venv
source .venv/bin/activate  # Windows: .venv\Scripts\activate

# Install package (all required dependencies are installed automatically)
uv pip install -e .
```

## 🚀 Quick Start

### 1️⃣ Initialize Configuration

```bash
gfa init
```

When prompted, enter the following information:
- GitHub Personal Access Token (stored securely in system keyring)
- LLM endpoint (e.g., `http://localhost:8000/v1/chat/completions`)
- LLM model (e.g., `gpt-4`)
- GitHub Enterprise host (optional, only if not using github.com)

### 2️⃣ Analyze Your Activity

```bash
gfa feedback
```

You can choose from a list of recommended repositories or enter one directly to analyze **your activity** in that repository.

After analysis completes, the following files are generated in the `reports/` directory:
- `metrics.json` - Analysis data
- `report.md` - Markdown report
- `report.html` - HTML report (with visualization charts)
- `charts/` - SVG chart files
- `prompts/` - LLM prompt files

### 3️⃣ View Results

```bash
cat reports/report.md
```

## 📚 Command Reference

<details>
<summary><b>🎯 gfa init - Initial Configuration</b></summary>

Store GitHub access information and LLM settings.

#### Basic Usage (Interactive)

```bash
gfa init
```

#### Example: GitHub.com + Local LLM

```bash
gfa init \
  --pat ghp_xxxxxxxxxxxxxxxxxxxx \
  --llm-endpoint http://localhost:8000/v1/chat/completions \
  --llm-model gpt-4 \
  --months 12
```

#### Example: GitHub Enterprise

```bash
gfa init \
  --pat ghp_xxxxxxxxxxxxxxxxxxxx \
  --enterprise-host https://github.company.com \
  --llm-endpoint http://localhost:8000/v1/chat/completions \
  --llm-model gpt-4
```

#### Options

| Option | Description | Required | Default |
|--------|-------------|----------|---------|
| `--pat` | GitHub Personal Access Token | ✅ | - |
| `--llm-endpoint` | LLM API endpoint | ✅ | - |
| `--llm-model` | LLM model identifier | ✅ | - |
| `--months` | Default analysis period (months) | ❌ | 12 |
| `--enterprise-host` | GitHub Enterprise host | ❌ | github.com |

</details>

<details>
<summary><b>📊 gfa feedback - Personal Activity Analysis</b></summary>

Analyze **your activity** in a specific repository and generate detailed feedback reports.

> **Important**: This command analyzes only the authenticated user's (PAT owner's) personal activity. It collects and analyzes only **your** commits, PRs, reviews, and issues, not the entire repository.

#### Basic Usage

```bash
gfa feedback --repo owner/repo-name
```

#### Interactive Mode

Select repository from recommended list without specifying repository directly.

```bash
gfa feedback --interactive
```

Or

```bash
gfa feedback  # Run without --repo option
```

#### Examples

```bash
# Analyze public repository you contributed to
gfa feedback --repo torvalds/linux

# Analyze personal repository you contributed to
gfa feedback --repo myusername/my-private-repo

# Analyze organization repository you contributed to
gfa feedback --repo microsoft/vscode

# Interactive mode for repository selection
gfa feedback --interactive
```

#### Options

| Option | Description | Required | Default |
|--------|-------------|----------|---------|
| `--repo`, `-r` | Repository (owner/name) | ❌ | - |
| `--output`, `-o` | Output directory | ❌ | reports |
| `--interactive`, `-i` | Interactive repository selection | ❌ | false |

#### Generated Reports

After analysis completes, the following files are created in the `reports/` directory:

```
reports/
├── metrics.json                     # Raw analysis data (JSON)
├── report.md                        # Analysis report (Markdown)
├── integrated_full_report.md        # Integrated report (brief + PR reviews)
├── prompts/                         # LLM prompt files
│   ├── strengths_overview.txt
│   ├── collaboration_improvements.txt
│   ├── quality_balance.txt
│   ├── growth_story.txt
│   └── next_half_goals.txt
└── reviews/                         # PR reviews (subdirectories)
    └── {repo_name}/
        ├── pr-{number}/
        │   ├── artefacts.json       # Raw PR data
        │   ├── review_summary.json  # Structured review
        │   ├── review.md            # Markdown review
        │   └── personal_development.json  # Personal growth analysis
        └── integrated_report.md     # Integrated PR review report
```

#### Analysis Content

- ✅ **Activity Aggregation**: Count your commits, PRs, reviews, and issues
- 🎯 **Quality Analysis**: Your commit messages, PR titles, review tone, and issue description quality
- 🏆 **Awards**: Automatic awards based on your contributions
- 📈 **Trends**: Your monthly activity trends and velocity analysis
- 🤝 **Collaboration Analysis**: Collaborator network who worked with you
- 💻 **Tech Stack**: Languages and technologies in files you worked on

</details>

<details>
<summary><b>⚙️ gfa config - Configuration Management</b></summary>

View or modify configuration settings.

#### `gfa config show` - View Configuration

View currently stored configuration.

```bash
gfa config show
```

**Example Output:**

```
┌─────────────────────────────────────┐
│ GitHub Feedback Configuration       │
├─────────────┬───────────────────────┤
│ Section     │ Values                │
├─────────────┼───────────────────────┤
│ auth        │ pat = <set>           │
├─────────────┼───────────────────────┤
│ server      │ api_url = https://... │
│             │ web_url = https://... │
├─────────────┼───────────────────────┤
│ llm         │ endpoint = http://... │
│             │ model = gpt-4         │
└─────────────┴───────────────────────┘
```

> **Note:** The `gfa show-config` command is deprecated and has been replaced with `gfa config show`.

#### `gfa config set` - Set Configuration Values

Modify individual configuration values.

```bash
gfa config set <key> <value>
```

**Examples:**

```bash
# Change LLM model
gfa config set llm.model gpt-4

# Change LLM endpoint
gfa config set llm.endpoint http://localhost:8000/v1/chat/completions

# Change default analysis period
gfa config set defaults.months 6
```

#### `gfa config get` - Get Configuration Values

Retrieve specific configuration values.

```bash
gfa config get <key>
```

**Examples:**

```bash
# Check LLM model
gfa config get llm.model

# Check default analysis period
gfa config get defaults.months
```

</details>

<details>
<summary><b>🔍 gfa list-repos - List Repositories</b></summary>

List accessible repositories.

```bash
gfa list-repos
```

#### Examples

```bash
# List repositories (default: 20 most recently updated)
gfa list-repos

# Change sort criteria
gfa list-repos --sort stars --limit 10

# Filter by specific organization
gfa list-repos --org myorganization

# Sort by creation date
gfa list-repos --sort created --limit 50
```

#### Options

| Option | Description | Default |
|--------|-------------|---------|
| `--sort`, `-s` | Sort criteria (updated, created, pushed, full_name) | updated |
| `--limit`, `-l` | Maximum number to display | 20 |
| `--org`, `-o` | Filter by organization name | - |

</details>

<details>
<summary><b>💡 gfa suggest-repos - Repository Suggestions</b></summary>

Suggest active repositories suitable for analysis.

```bash
gfa suggest-repos
```

Automatically selects repositories with recent activity. Comprehensively considers stars, forks, issues, and recent updates.

#### Examples

```bash
# Default suggestions (within last 90 days, 10 repositories)
gfa suggest-repos

# Suggest 5 repositories active within last 30 days
gfa suggest-repos --limit 5 --days 30

# Sort by stars
gfa suggest-repos --sort stars

# Sort by activity score (comprehensive evaluation)
gfa suggest-repos --sort activity
```

#### Options

| Option | Description | Default |
|--------|-------------|---------|
| `--limit`, `-l` | Maximum number of suggestions | 10 |
| `--days`, `-d` | Recent activity period (days) | 90 |
| `--sort`, `-s` | Sort criteria (updated, stars, activity) | activity |

</details>

## 📁 Configuration File

<details>
<summary><b>⚙️ Configuration File Structure</b></summary>

Configuration is stored in `~/.config/github_feedback/config.toml` and is automatically created when running `gfa init`.

### Configuration File Example

```toml
[version]
version = "1.0.0"

[auth]
# PAT is stored securely in system keyring (not in this file)

[server]
api_url = "https://api.github.com"
graphql_url = "https://api.github.com/graphql"
web_url = "https://github.com"

[llm]
endpoint = "http://localhost:8000/v1/chat/completions"
model = "gpt-4"
timeout = 60
max_files_in_prompt = 10
max_retries = 3

[defaults]
months = 12
```

### Manual Configuration Editing

If needed, you can edit the configuration file directly or use the `gfa config` commands:

```bash
# Method 1: Use config commands (recommended)
gfa config set llm.model gpt-4
gfa config show

# Method 2: Direct editing
nano ~/.config/github_feedback/config.toml
```

</details>

## 📊 Generated File Structure

<details>
<summary><b>📁 Output File Structure</b></summary>

### `gfa feedback` Output

```
reports/
├── metrics.json                     # 📈 Personal activity analysis data (JSON)
├── report.md                        # 📄 Markdown report
├── integrated_full_report.md        # 🎯 Integrated report (brief + PR reviews)
├── prompts/                         # 💬 LLM prompt packets
│   ├── strengths_overview.txt
│   ├── collaboration_improvements.txt
│   ├── quality_balance.txt
│   ├── growth_story.txt
│   └── next_half_goals.txt
└── reviews/                         # 🔍 PR reviews (subdirectories)
    └── {repo_name}/
        ├── pr-{number}/
        │   ├── artefacts.json       # Raw PR data
        │   ├── review_summary.json  # Structured review
        │   ├── review.md            # Markdown review
        │   └── personal_development.json  # Personal growth analysis
        └── integrated_report.md     # Integrated PR review report
```

</details>

## 💡 Usage Examples

<details>
<summary><b>📚 Usage Scenario Examples</b></summary>

### Example 1: Quick Start - Interactive Mode

```bash
# 1. Configuration (first time only)
gfa init

# 2. Get repository suggestions
gfa suggest-repos

# 3. Analyze your activity in interactive mode
gfa feedback --interactive

# 4. View report
cat reports/report.md
```

### Example 2: Open Source Contribution Analysis

```bash
# 1. Configuration (first time only)
gfa init

# 2. Analyze your contributions to open source project
gfa feedback --repo facebook/react

# 3. View report (only your contributions are shown)
cat reports/report.md
```

### Example 3: Personal Project Retrospective

```bash
# Check my repository list
gfa list-repos --sort updated --limit 10

# Analyze your activity in your project
gfa feedback --repo myname/my-awesome-project

# View report
cat reports/report.md
```

### Example 4: Team Project Performance Review

```bash
# Check organization repository list
gfa list-repos --org mycompany --limit 20

# Set analysis period (last 6 months)
gfa config set defaults.months 6

# Analyze your activity in organization repository
gfa feedback --repo mycompany/product-service

# View report (only your activity is shown)
cat reports/report.md
```

</details>

## 🎯 Award System

<details>
<summary><b>🏆 Award List</b></summary>

Awards are automatically granted based on repository activity:

### Commit-Based Awards
- 💎 **Code Legend** (1000+ commits)
- 🏆 **Code Master** (500+ commits)
- 🥇 **Code Blacksmith** (200+ commits)
- 🥈 **Code Craftsman** (100+ commits)
- 🥉 **Code Apprentice** (50+ commits)

### PR-Based Awards
- 💎 **Release Legend** (200+ PRs)
- 🏆 **Deployment Admiral** (100+ PRs)
- 🥇 **Release Captain** (50+ PRs)
- 🥈 **Release Navigator** (25+ PRs)
- 🥉 **Deployment Sailor** (10+ PRs)

### Review-Based Awards
- 💎 **Knowledge Propagator** (200+ reviews)
- 🏆 **Mentoring Master** (100+ reviews)
- 🥇 **Review Expert** (50+ reviews)
- 🥈 **Growth Mentor** (20+ reviews)
- 🥉 **Code Supporter** (10+ reviews)

### Special Awards
- ⚡ **Lightning Developer** (50+ commits/month)
- 🤝 **Collaboration Master** (20+ PRs+reviews/month)
- 🏗️ **Large-Scale Architect** (5000+ lines changed)
- 📅 **Consistency Master** (6+ months continuous activity)
- 🌟 **Multi-Talented** (Balanced contributions across all areas)

</details>

## 🐛 Troubleshooting

<details>
<summary><b>🔧 Troubleshooting Guide</b></summary>

### PAT Permission Error

```
Error: GitHub API rejected the provided PAT
```

**Solution**: Verify PAT has appropriate permissions
- Private repositories: `repo` permission required
- Public repositories: `public_repo` permission required
- Check at [GitHub Settings → Developer settings → Personal access tokens](https://github.com/settings/tokens)

### LLM Endpoint Connection Failure

```
Warning: Detailed feedback analysis failed: Connection refused
```

**Solution**:
1. Verify LLM server is running
2. Verify endpoint URL is correct (`gfa config show`)
3. Reinitialize configuration if needed: `gfa init`

### Repository Not Found

```
Error: Repository not found
```

**Solution**:
- Verify repository name format: `owner/repo` (e.g., `torvalds/linux`)
- For private repositories, verify PAT permissions
- For GitHub Enterprise, verify `--enterprise-host` configuration

### No Data in Analysis Period

```
No activity detected during analysis period.
```

**Solution**:
- Try increasing analysis period: `gfa init --months 24`
- Verify repository is active

</details>

## 👩‍💻 Developer Guide

<details>
<summary><b>🛠️ Development Environment Setup</b></summary>

### Development Environment Setup

```bash
# Copy repository
git clone https://github.com/goonbamm/github-feedback-analysis.git
cd github-feedback-analysis

# Install in development mode (includes test dependencies)
uv pip install -e .[test]

# Run tests
pytest

# Run specific tests
pytest tests/test_analyzer.py -v

# Check coverage
pytest --cov=github_feedback --cov-report=html
```

### Key Dependencies

**Core Runtime Dependencies:**
- **typer >= 0.9** - CLI framework
- **rich >= 13.0** - Terminal UI, progress bars
- **pydantic >= 2.5** - Data validation and serialization
- **requests >= 2.31** - HTTP client
- **requests-cache >= 1.0** - SQLite-based response caching
- **keyring >= 24.0** - System credential storage
- **keyrings.alt >= 5.0** - Fallback encrypted file keyring
- **tomli >= 2.0** - TOML file parsing (Python < 3.11)
- **tomli-w >= 1.0** - TOML file writing

**Development/Test Dependencies:**
- **pytest >= 7.4** - Testing framework

**System Requirements:**
- Python 3.11+ (async/type hints required)
- System keyring or accessible file system
- GitHub Personal Access Token (classic or fine-grained)
- LLM endpoint compatible with OpenAI API format

### Code Structure

```
github_feedback/
├── cli.py              # 🖥️  CLI entry point and commands (1,791 lines)
├── llm.py             # 🤖 LLM API client (1,409 lines, with retry logic)
├── reporter.py         # 📄 Report generation (1,358 lines, brief format)
├── retrospective.py    # 📅 Year-end retrospective analysis (1,021 lines)
├── analyzer.py         # 📊 Metric analysis and calculation (959 lines)
├── review_reporter.py  # 📝 Integrated review reports (749 lines)
├── config.py          # ⚙️  Configuration management (529 lines, keyring integration)
├── models.py          # 📦 Pydantic data models (525 lines)
├── pr_collector.py     # 🔍 PR data collection (439 lines)
├── award_strategies.py # 🏆 Award calculation strategies (419 lines, 100+ awards)
├── api_client.py      # 🌐 GitHub REST API client (416 lines)
├── reviewer.py         # 🎯 PR review logic (416 lines)
├── collector.py        # 📡 Data collection facade (397 lines)
├── commit_collector.py # 📝 Commit data collection (263 lines)
├── review_collector.py # 👀 Review data collection (256 lines)
├── repository_manager.py # 📂 Repository management (250 lines)
├── filters.py         # 🔍 Language detection and filtering (234 lines)
├── exceptions.py      # ⚠️  Exception hierarchy (235 lines, 24+ exception types)
└── utils.py           # 🔧 Utility functions
```

### Architecture and Design Patterns

- **Facade Pattern**: `Collector` class orchestrates specialized collectors
- **Strategy Pattern**: 100+ strategies used in award calculation
- **Repository Pattern**: `GitHubApiClient` abstracts API access
- **Builder Pattern**: Report and metric construction
- **Thread Pool Pattern**: Parallel data collection (4x speed improvement)

### Performance Optimizations

- **Request Caching**: SQLite-based cache (`~/.cache/github_feedback/api_cache.sqlite`)
  - Default expiration: 1 hour
  - Caches GET/HEAD requests only
  - 60-70% speed improvement on repeated runs
- **Parallel Collection**: Concurrent data collection using ThreadPoolExecutor
- **Retry Logic**: Exponential backoff for LLM requests (max 3 attempts)

</details>

## 🔒 Security

- **PAT Storage**: GitHub tokens are stored securely in the system keyring (not in plain text files)
  - System keyring support: gnome-keyring, macOS Keychain, Windows Credential Manager
  - Linux fallback: Encrypted file keyring (`keyrings.alt`)
  - Thread-safe keyring initialization (prevents race conditions)
- **Configuration Backup**: Automatically creates backups before overwriting configuration
- **Input Validation**: Validates all user inputs (PAT format, URL format, repository format)
- **Cache Security**: SQLite cache file has user-only read/write permissions
- **API Security**: Bearer token authentication, HTTPS-only communication

## 📄 License

This project is licensed under the MIT License.

## 🤝 Contributing

Bug reports, feature suggestions, and PRs are always welcome!

1. Fork the repository
2. Create your feature branch (`git checkout -b feature/amazing-feature`)
3. Commit your changes (`git commit -m 'Add amazing feature'`)
4. Push to the branch (`git push origin feature/amazing-feature`)
5. Open a Pull Request

## 💬 Feedback

If you have issues or suggestions, please register them in [Issues](https://github.com/goonbamm/github-feedback-analysis/issues)!
