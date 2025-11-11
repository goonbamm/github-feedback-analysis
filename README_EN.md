# 🚀 GitHub Feedback Analysis

A CLI tool that analyzes GitHub repository activity and automatically generates insightful reports. Supports both GitHub.com and GitHub Enterprise, with LLM-powered automated review capabilities.

[한국어 문서](README.md) | English

## ✨ Key Features

- 📊 **Repository Analysis**: Aggregate and analyze commits, issues, and review activity by period
- 🤖 **LLM-Based Feedback**: Detailed analysis of commit messages, PR titles, review tone, and issue quality
- 🎯 **Automated PR Reviews**: Automatically review authenticated user's PRs and generate integrated retrospective reports
- 🏆 **Achievement Visualization**: Automatically generate awards and highlights based on contributions

## 📋 Prerequisites

- Python 3.11 or higher
- [uv](https://docs.astral.sh/uv/) or your preferred package manager
- GitHub Personal Access Token
  - Private repositories: `repo` permission
  - Public repositories: `public_repo` permission
- LLM API endpoint (OpenAI-compatible format)

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
```

## 🚀 Quick Start

### 1️⃣ Initialize Configuration

```bash
ghfinit
```

When prompted, enter the following information:
- GitHub Personal Access Token (stored securely in system keyring)
- LLM endpoint (e.g., `http://localhost:8000/v1/chat/completions`)
- LLM model (e.g., `gpt-4`)
- GitHub Enterprise host (optional, only if not using github.com)

### 2️⃣ Analyze Repository

```bash
ghfbrief --repo goonbamm/github-feedback-analysis
```

After analysis completes, the following files are generated in the `reports/` directory:
- `metrics.json` - Analysis data
- `report.md` - Markdown report
- `prompts/` - LLM prompt files

### 3️⃣ View Results

```bash
cat reports/report.md
```

## 📚 Command Reference

### 🎯 `ghfinit` - Initial Configuration

Store GitHub access information and LLM settings.

#### Basic Usage (Interactive)

```bash
ghfinit
```

#### Example: GitHub.com + Local LLM

```bash
ghfinit \
  --pat ghp_xxxxxxxxxxxxxxxxxxxx \
  --llm-endpoint http://localhost:8000/v1/chat/completions \
  --llm-model gpt-4 \
  --months 12
```

#### Example: GitHub Enterprise

```bash
ghfinit \
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

### 📊 `ghfbrief` - Repository Analysis

Analyze repository and generate detailed feedback reports.

#### Basic Usage

```bash
ghfbrief --repo owner/repo-name
```

#### Examples

```bash
# Analyze public repository
ghfbrief --repo torvalds/linux

# Analyze personal repository
ghfbrief --repo myusername/my-private-repo

# Analyze organization repository
ghfbrief --repo microsoft/vscode
```

#### Generated Reports

After analysis completes, the following files are created in the `reports/` directory:

```
reports/
├── metrics.json              # Raw data (JSON)
├── report.md                 # Analysis report (Markdown)
└── prompts/
    ├── commit_feedback.txt   # Commit message feedback
    ├── pr_feedback.txt       # PR title feedback
    ├── review_feedback.txt   # Review tone feedback
    └── issue_feedback.txt    # Issue quality feedback
```

#### Analysis Content

- ✅ **Activity Aggregation**: Count commits, PRs, reviews, and issues
- 🎯 **Quality Analysis**: Commit messages, PR titles, review tone, issue description quality
- 🏆 **Awards**: Automatic awards based on contributions
- 📈 **Trends**: Monthly activity trends and velocity analysis

### 🎯 `ghffeedback` - Automated PR Review

Automatically review authenticated user's (PAT owner's) PRs and generate integrated retrospective report.

#### Basic Usage

```bash
ghffeedback --repo owner/repo-name
```

#### Examples

```bash
# Review all PRs (open + closed)
ghffeedback --repo myusername/my-project --state all

# Review only open PRs
ghffeedback --repo myusername/my-project --state open

# Review only closed PRs
ghffeedback --repo myusername/my-project --state closed
```

#### Options

| Option | Description | Required | Default |
|--------|-------------|----------|---------|
| `--repo` | Repository (owner/name) | ✅ | - |
| `--state` | PR state (`open`, `closed`, `all`) | ❌ | `all` |

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

### ⚙️ `ghfshow-config` - View Configuration

View currently stored configuration.

```bash
ghfshow-config
```

#### Example Output

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

## 📁 Configuration File

Configuration is stored in `~/.config/github_feedback/config.toml` and is automatically created when running `ghfinit`.

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

If needed, you can edit the configuration file directly:

```bash
# Check configuration file location
ghfshow-config

# Open in editor
nano ~/.config/github_feedback/config.toml
```

## 🎯 Award System

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

## 🐛 Troubleshooting

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
2. Verify endpoint URL is correct (`ghfshow-config`)
3. Reinitialize configuration if needed: `ghfinit`

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
- Try increasing analysis period: `ghfinit --months 24`
- Verify repository is active

## 👩‍💻 Developer Guide

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
