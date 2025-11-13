# Contributing to GitHub Feedback Analysis

Thank you for your interest in contributing to the GitHub Feedback Analysis (GFA) project! This document provides guidelines and instructions for contributing.

## Table of Contents

- [Code of Conduct](#code-of-conduct)
- [Getting Started](#getting-started)
- [Development Setup](#development-setup)
- [Making Changes](#making-changes)
- [Testing](#testing)
- [Code Style](#code-style)
- [Commit Messages](#commit-messages)
- [Pull Request Process](#pull-request-process)
- [Reporting Bugs](#reporting-bugs)
- [Suggesting Enhancements](#suggesting-enhancements)

## Code of Conduct

This project adheres to a code of conduct that all contributors are expected to follow. Please be respectful and constructive in all interactions.

## Getting Started

1. **Fork the repository** on GitHub
2. **Clone your fork** locally:
   ```bash
   git clone https://github.com/YOUR_USERNAME/github-feedback-analysis.git
   cd github-feedback-analysis
   ```
3. **Add upstream remote**:
   ```bash
   git remote add upstream https://github.com/goonbamm/github-feedback-analysis.git
   ```

## Development Setup

### Prerequisites

- Python 3.11 or higher
- pip or uv for package management

### Installation

1. **Create a virtual environment**:
   ```bash
   python -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   ```

2. **Install dependencies**:
   ```bash
   pip install -e .
   pip install -e ".[test]"
   ```

3. **Configure the tool**:
   ```bash
   gfa init
   ```

## Making Changes

1. **Create a feature branch**:
   ```bash
   git checkout -b feature/your-feature-name
   ```

2. **Make your changes** following the code style guidelines

3. **Add tests** for new functionality

4. **Run tests** to ensure everything works:
   ```bash
   pytest
   ```

5. **Update documentation** if needed

## Testing

We use pytest for testing. All new features should include comprehensive tests.

### Running Tests

```bash
# Run all tests
pytest

# Run with coverage
pytest --cov=github_feedback --cov-report=html

# Run specific test file
pytest tests/test_collector.py

# Run specific test
pytest tests/test_collector.py::test_collect_commits
```

### Writing Tests

- Place tests in the `tests/` directory
- Name test files `test_*.py`
- Name test functions `test_*`
- Use descriptive test names that explain what is being tested
- Include docstrings explaining the test purpose
- Use fixtures for common setup
- Mock external API calls

Example:
```python
def test_collector_handles_empty_repository(monkeypatch):
    """Test that collector gracefully handles empty repository."""
    # Setup
    mock_api = Mock()
    mock_api.get.return_value = []

    # Exercise
    collector = Collector(api_client=mock_api)
    result = collector.collect_commits("empty/repo", since=datetime.now())

    # Assert
    assert result == []
```

## Code Style

### Python Style Guide

- Follow [PEP 8](https://pep8.org/)
- Use type hints for function signatures
- Maximum line length: 100 characters
- Use meaningful variable and function names
- Write docstrings for all public functions and classes

### Type Hints

Always include type hints:
```python
def collect_commits(
    self,
    repo: str,
    since: datetime,
    limit: int = 100
) -> List[Dict[str, Any]]:
    """Collect commits from repository.

    Args:
        repo: Repository name in format 'owner/repo'
        since: Start date for collection
        limit: Maximum number of commits to collect

    Returns:
        List of commit dictionaries
    """
    ...
```

### Docstrings

Use Google-style docstrings:
```python
def function_name(param1: str, param2: int) -> bool:
    """Brief description of function.

    More detailed description if needed. Can span
    multiple lines.

    Args:
        param1: Description of param1
        param2: Description of param2

    Returns:
        Description of return value

    Raises:
        ValueError: When invalid input is provided
    """
```

## Commit Messages

Write clear, descriptive commit messages following these guidelines:

### Format

```
<type>(<scope>): <subject>

<body>

<footer>
```

### Types

- `feat`: New feature
- `fix`: Bug fix
- `docs`: Documentation changes
- `style`: Code style changes (formatting, etc.)
- `refactor`: Code refactoring
- `test`: Adding or updating tests
- `chore`: Maintenance tasks

### Examples

```
feat(collector): add support for draft pull requests

Adds ability to collect and analyze draft PRs alongside
regular PRs. Includes new filter option.

Closes #123
```

```
fix(api): resolve race condition in keyring access

Adds threading lock to prevent concurrent keyring
initialization attempts.
```

## Pull Request Process

1. **Update your branch** with latest upstream:
   ```bash
   git fetch upstream
   git rebase upstream/main
   ```

2. **Push your changes**:
   ```bash
   git push origin feature/your-feature-name
   ```

3. **Create Pull Request** on GitHub:
   - Use a clear, descriptive title
   - Reference related issues
   - Provide detailed description of changes
   - Include screenshots for UI changes
   - List any breaking changes

4. **Address review feedback**:
   - Make requested changes
   - Push updates to your branch
   - Respond to comments

5. **Merge requirements**:
   - All tests must pass
   - Code review approval required
   - No merge conflicts
   - Branch is up to date with main

## Reporting Bugs

When reporting bugs, please include:

### Required Information

- **Description**: Clear description of the issue
- **Steps to reproduce**: Detailed steps to reproduce the behavior
- **Expected behavior**: What you expected to happen
- **Actual behavior**: What actually happened
- **Environment**:
  - OS and version
  - Python version
  - GFA version
- **Logs**: Relevant log output or error messages
- **Screenshots**: If applicable

### Bug Report Template

```markdown
## Description
Brief description of the bug

## Steps to Reproduce
1. Step one
2. Step two
3. Step three

## Expected Behavior
What should happen

## Actual Behavior
What actually happens

## Environment
- OS: [e.g., Ubuntu 22.04]
- Python: [e.g., 3.11.5]
- GFA Version: [e.g., 0.1.0]

## Additional Context
Any other relevant information
```

## Suggesting Enhancements

We welcome enhancement suggestions! Please provide:

1. **Clear description** of the enhancement
2. **Use case**: Why this would be useful
3. **Proposed solution**: How you envision it working
4. **Alternatives considered**: Other approaches you've thought about
5. **Examples**: From other tools if applicable

## Development Tips

### Running in Development Mode

```bash
# Install in editable mode
pip install -e .

# Run directly
python -m github_feedback.cli feedback owner/repo
```

### Debugging

```bash
# Enable debug logging
export GFA_LOG_LEVEL=DEBUG
gfa feedback owner/repo
```

### Code Organization

- `github_feedback/`: Main package code
  - `cli.py`: Command-line interface
  - `collector.py`: Data collection logic
  - `analyzer.py`: Analysis algorithms
  - `reporter.py`: Report generation
  - `models.py`: Data models
  - `config.py`: Configuration management
- `tests/`: Test suite
- `docs/`: Documentation

### Performance Considerations

- Use caching for API requests (already implemented)
- Avoid loading large datasets into memory at once
- Use generators for processing large collections
- Profile code for bottlenecks before optimizing

### Security Considerations

- Never commit secrets or tokens
- Use keyring for credential storage
- Validate and sanitize all user input
- Be cautious with file operations (path traversal)
- Review dependencies for vulnerabilities

## Getting Help

- **Documentation**: Check the [README](README.md) and [docs/](docs/)
- **Issues**: Search existing issues for similar problems
- **Discussions**: Use GitHub Discussions for questions
- **Contact**: Reach out to maintainers for urgent matters

## Recognition

Contributors will be recognized in:
- GitHub contributors list
- Release notes for significant contributions
- CHANGELOG.md

Thank you for contributing to GitHub Feedback Analysis!
