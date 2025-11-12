# 🚀 GitHub Feedback Analysis

A CLI tool that analyzes GitHub repository activity and automatically generates insightful reports. Supports both GitHub.com and GitHub Enterprise, with LLM-powered automated review capabilities.

English | [한국어](../README.md) | [简体中文](README_ZH.md) | [日本語](README_JA.md) | [Español](README_ES.md)

## ✨ Key Features

- 📊 **Repository Analysis**: Aggregate and analyze commits, issues, and review activity by period
- 🤖 **LLM-Based Feedback**: Detailed analysis of commit messages, PR titles, review tone, and issue quality
- 🎯 **Automated PR Reviews**: Automatically review authenticated user's PRs and generate integrated retrospective reports
- 🏆 **Achievement Visualization**: Automatically generate awards and highlights based on contributions
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
# Clone the repository
git clone https://github.com/goonbamm/github-feedback-analysis.git
cd github-feedback-analysis

# Create and activate virtual environment
uv venv
source .venv/bin/activate  # Windows: .venv\Scripts\activate

# Install package
uv pip install -e .

# (Optional) Install keyrings.alt if system keyring is not available
# Required on Linux systems without gnome-keyring or kwallet
uv pip install keyrings.alt
```

> **💡 Note for Linux users**: If your system doesn't have a keyring service (gnome-keyring, kwallet, etc.), install `keyrings.alt`. See [docs/KEYRING_TROUBLESHOOTING.md](../docs/KEYRING_TROUBLESHOOTING.md) for details.

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

### 2️⃣ Analyze Repository

```bash
gfa feedback --repo goonbamm/github-feedback-analysis
```

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
<summary><b>📊 gfa feedback - Repository Analysis</b></summary>

Analyze repository and generate detailed feedback reports.

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
# Analyze public repository
gfa feedback --repo torvalds/linux

# Analyze personal repository
gfa feedback --repo myusername/my-private-repo

# Analyze organization repository
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
├── metrics.json              # 📈 Raw analysis data
├── report.md                 # 📄 Markdown report
├── report.html               # 🎨 HTML report (with visualization charts)
├── charts/                   # 📊 Visualization charts (SVG)
│   ├── quality.svg          # Quality metrics chart
│   ├── activity.svg         # Activity metrics chart
│   ├── engagement.svg       # Engagement chart
│   └── ...                  # Other domain-specific charts
└── prompts/
    ├── commit_feedback.txt   # 💬 Commit message quality analysis
    ├── pr_feedback.txt       # 🔀 PR title analysis
    ├── review_feedback.txt   # 👀 Review tone analysis
    └── issue_feedback.txt    # 🐛 Issue quality analysis
```

#### Analysis Content

- ✅ **Activity Aggregation**: Count commits, PRs, reviews, and issues
- 🎯 **Quality Analysis**: Commit messages, PR titles, review tone, issue description quality
- 🏆 **Awards**: Automatic awards based on contributions
- 📈 **Trends**: Monthly activity trends and velocity analysis

</details>

<details>
<summary><b>🎯 gfa feedback - Automated PR Review</b></summary>

Automatically review authenticated user's (PAT owner's) PRs and generate integrated retrospective report.

#### Basic Usage

```bash
gfa feedback --repo owner/repo-name
```

#### Examples

```bash
# Review all PRs authored by you
gfa feedback --repo myusername/my-project
```

#### Options

| Option | Description | Required | Default |
|--------|-------------|----------|---------|
| `--repo` | Repository (owner/name) | ✅ | - |

#### Execution Process

1. **PR Search** 🔍
   - Retrieve list of PRs authored by PAT-authenticated user

2. **Generate Individual Reviews** 📝
   - Collect code changes and review comments for each PR
   - Generate detailed reviews using LLM
   - Save to `reviews/owner_repo/pr-{number}/` directory

3. **Integrated Retrospective Report** 📊
   - Generate insights combining all PRs
   - Save to `reviews/owner_repo/integrated_report.md`

#### Generated Files

```
reviews/
└── owner_repo/
    ├── pr-123/
    │   ├── artefacts.json          # PR raw data
    │   ├── review_summary.json     # LLM analysis results
    │   └── review.md               # Markdown review
    ├── pr-456/
    │   └── ...
    └── integrated_report.md        # Integrated retrospective report
```

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
├── metrics.json              # 📈 Raw analysis data
├── report.md                 # 📄 Markdown report
├── report.html               # 🎨 HTML report (with visualization charts)
├── charts/                   # 📊 Visualization charts (SVG)
│   ├── quality.svg          # Quality metrics chart
│   ├── activity.svg         # Activity metrics chart
│   ├── engagement.svg       # Engagement chart
│   └── ...                  # Other domain-specific charts
└── prompts/
    ├── commit_feedback.txt   # 💬 Commit message quality analysis
    ├── pr_feedback.txt       # 🔀 PR title analysis
    ├── review_feedback.txt   # 👀 Review tone analysis
    └── issue_feedback.txt    # 🐛 Issue quality analysis
```

### `gfa feedback` Output

```
reviews/
└── owner_repo/
    ├── pr-123/
    │   ├── artefacts.json          # 📦 PR raw data (code, reviews, etc.)
    │   ├── review_summary.json     # 🤖 LLM analysis results (structured data)
    │   └── review.md               # 📝 Markdown review report
    ├── pr-456/
    │   └── ...
    └── integrated_report.md        # 🎯 Integrated retrospective report (all PRs combined)
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

# 3. Analyze with interactive mode
gfa feedback --interactive

# 4. View report
cat reports/report.md
```

### Example 2: Open Source Project Analysis

```bash
# 1. Configuration (first time only)
gfa init

# 2. Analyze popular open source project
gfa feedback --repo facebook/react

# 3. View report
cat reports/report.md
```

### Example 3: Personal Project Retrospective

```bash
# Check my repository list
gfa list-repos --sort updated --limit 10

# Analyze my project
gfa feedback --repo myname/my-awesome-project

# Auto-review my PRs
gfa feedback --repo myname/my-awesome-project

# View integrated retrospective report
cat reviews/myname_my-awesome-project/integrated_report.md
```

### Example 4: Team Project Performance Review

```bash
# Check organization repository list
gfa list-repos --org mycompany --limit 20

# Set analysis period (last 6 months)
gfa config set defaults.months 6

# Analyze organization repository
gfa feedback --repo mycompany/product-service

# Review team member PRs (each runs with their own PAT)
gfa feedback --repo mycompany/product-service
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
# Clone repository
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

### Code Structure

```
github_feedback/
├── cli.py              # 🖥️  CLI entry point and commands
├── collector.py        # 📡 GitHub API data collection
├── analyzer.py         # 📊 Metric analysis and calculation
├── reporter.py         # 📄 Report generation (brief)
├── reviewer.py         # 🎯 PR review logic
├── review_reporter.py  # 📝 Integrated review reports
├── llm.py             # 🤖 LLM API client
├── config.py          # ⚙️  Configuration management
├── models.py          # 📦 Data models
└── utils.py           # 🔧 Utility functions
```

</details>

## 🔒 Security

- **PAT Storage**: GitHub tokens are stored securely in the system keyring (not in plain text files)
- **Configuration Backup**: Automatically creates backups before overwriting configuration
- **Input Validation**: Validates all user inputs (PAT format, URL format, repository format)

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
