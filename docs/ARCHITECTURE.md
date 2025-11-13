# GitHub Feedback Analysis - Architecture Documentation

## Overview

GitHub Feedback Analysis (GFA) is a Python-based CLI tool that analyzes GitHub repository activity and generates comprehensive feedback reports using LLM-powered insights.

## System Architecture

### High-Level Architecture

```
┌─────────────────────────────────────────────────────────────────┐
│                         CLI Interface                            │
│                         (cli.py)                                 │
└─────────────────┬───────────────────────────────────────────────┘
                  │
                  ├─────────────────────────────────────────────────┐
                  │                                                 │
    ┌─────────────▼──────────┐              ┌────────────────────▼─┐
    │   Configuration        │              │   Data Collection     │
    │   (config.py)          │              │   (collector.py)      │
    │                        │              │                       │
    │ - Config Management    │              │ - Commits            │
    │ - Keyring Integration  │              │ - Pull Requests      │
    │ - PAT Storage          │              │ - Reviews            │
    └────────────────────────┘              │ - Issues             │
                                            └───────┬───────────────┘
                                                    │
                  ┌─────────────────────────────────┼───────────────┐
                  │                                 │               │
    ┌─────────────▼──────────┐      ┌──────────────▼─────┐  ┌──────▼────────┐
    │   API Client           │      │   Analysis         │  │   LLM Client  │
    │   (api_client.py)      │      │   (analyzer.py)    │  │   (llm.py)    │
    │                        │      │                    │  │               │
    │ - GitHub REST API      │      │ - Metrics          │  │ - Code Review │
    │ - Request Caching      │      │ - Trends           │  │ - Analysis    │
    │ - Retry Logic          │      │ - Collaboration    │  │ - Insights    │
    │ - Authentication       │      │ - Tech Stack       │  │ - Retry Logic │
    └────────────────────────┘      └──────────┬─────────┘  └───────────────┘
                                               │
                                 ┌─────────────▼──────────────┐
                                 │   Report Generation        │
                                 │   (reporter.py)            │
                                 │                            │
                                 │ - Markdown Reports         │
                                 │ - JSON Metrics             │
                                 │ - Integrated Reports       │
                                 │ - Retrospective Analysis   │
                                 └────────────────────────────┘
```

## Core Components

### 1. CLI Layer (`cli.py`)

**Purpose**: User interface and command orchestration

**Responsibilities**:
- Command-line argument parsing (using Typer)
- User interaction and prompts
- Workflow orchestration
- Progress reporting (using Rich)
- Error handling and user feedback

**Key Commands**:
- `gfa init`: Initialize configuration
- `gfa feedback`: Generate feedback report
- `gfa config`: Manage configuration
- `gfa repos`: Repository management

**Design Patterns**:
- Command Pattern (via Typer)
- Facade Pattern (orchestrates other components)

### 2. Configuration Layer (`config.py`)

**Purpose**: Manage application configuration and credentials

**Responsibilities**:
- Load/save configuration files (TOML)
- Secure credential storage (keyring)
- Configuration validation (Pydantic)
- Keyring fallback mechanism

**Key Classes**:
- `Config`: Main configuration container
- `ServerConfig`: GitHub server settings
- `ApiConfig`: API-related settings
- `LlmConfig`: LLM endpoint configuration

**Thread Safety**:
- Uses threading locks for keyring initialization
- Prevents race conditions in concurrent scenarios

### 3. Data Collection Layer

#### API Client (`api_client.py`)

**Purpose**: GitHub API communication

**Responsibilities**:
- HTTP request/response handling
- Authentication (Bearer token)
- Pagination support
- Rate limiting
- Error handling
- **Request caching** (using requests-cache)

**Key Features**:
- Connection pooling
- Configurable timeouts
- Retry logic with exponential backoff
- SQLite-based response caching

**Caching Strategy**:
- Cache location: `~/.cache/github_feedback/api_cache`
- Default expiration: 1 hour
- Only caches GET/HEAD requests
- Respects HTTP status codes (200, 301, 302, 304)

#### Collectors

**Base Collector** (`base_collector.py`):
- Abstract base class for specialized collectors
- Common pagination logic
- Error handling patterns

**Specialized Collectors**:
- `CommitCollector`: Collects commit history
- `PRCollector`: Collects pull request data
- `ReviewCollector`: Collects code review information
- `IssueCollector`: Collects issue data
- `AnalyticsCollector`: Aggregates statistics

**Design Pattern**: Repository Pattern

### 4. Analysis Layer (`analyzer.py`)

**Purpose**: Process collected data and extract insights

**Responsibilities**:
- Calculate metrics and statistics
- Identify trends over time
- Analyze collaboration patterns
- Detect tech stack usage
- Compute awards and achievements

**Key Classes**:
- `Analyzer`: Main analysis orchestrator
- `AwardCalculator`: Computes developer awards

**Analysis Types**:
- **Quantitative**: Commits, PRs, reviews, issues counts
- **Temporal**: Monthly trends, activity patterns
- **Collaborative**: Network analysis, interaction frequency
- **Technical**: Language usage, framework detection

### 5. LLM Integration Layer (`llm.py`)

**Purpose**: Interact with Language Models for advanced analysis

**Responsibilities**:
- Format prompts for LLM consumption
- Execute API calls to LLM endpoints
- Parse and validate LLM responses
- **Retry logic with exponential backoff**

**Key Features**:
- OpenAI-compatible API interface
- Configurable temperature and model
- JSON response parsing
- Korean-language prompts
- Automatic retry on failures

**Retry Strategy**:
- Default: 3 retry attempts
- Exponential backoff: 2s, 4s, 8s
- Smart retry logic (skips 4xx except 429, 408)
- Comprehensive error logging

**LLM Use Cases**:
- Code review analysis
- Commit message quality assessment
- PR description evaluation
- Actionable insights generation

### 6. Reporting Layer

#### Reporter (`reporter.py`)

**Purpose**: Generate comprehensive feedback reports

**Responsibilities**:
- Format data into readable Markdown
- Create visualizations (text-based)
- Generate multiple report types
- Export metrics as JSON

**Report Types**:
- Basic feedback report
- Integrated full report
- Review-specific reports
- Retrospective analysis

#### Review Reporter (`review_reporter.py`)

**Purpose**: Generate code review-focused reports

**Responsibilities**:
- Aggregate review feedback
- Summarize strengths and improvements
- Create integrated review reports
- LLM-powered synthesis (optional)

#### Retrospective Analyzer (`retrospective.py`)

**Purpose**: Generate year-end or period-based retrospective

**Key Components**:
- `TimeComparison`: Compare metrics across periods
- `BehaviorPattern`: Identify work patterns
- `LearningInsight`: Track skill development
- `ImpactAssessment`: Evaluate contributions
- `CollaborationInsight`: Analyze teamwork
- `BalanceMetrics`: Assess work-life balance
- `BlockerAnalysis`: Identify obstacles
- `CodeHealthAnalysis`: Evaluate code quality
- `ActionableInsight`: Generate recommendations

## Data Models (`models.py`)

### Core Models

**MetricSnapshot**: Point-in-time metrics
```python
@dataclass
class MetricSnapshot:
    total_commits: int
    total_prs: int
    total_reviews: int
    total_issues: int
    code_changes_added: int
    code_changes_deleted: int
    active_days: int
```

**MonthlyTrend**: Time-series data
```python
@dataclass
class MonthlyTrend:
    month: str
    commits: int
    prs_opened: int
    prs_merged: int
    reviews: int
    issues_opened: int
    issues_closed: int
```

**CollaborationNetwork**: Network analysis
```python
@dataclass
class CollaborationNetwork:
    nodes: List[CollaboratorNode]
    edges: List[CollaborationEdge]
    metrics: Dict[str, Any]
```

**TechStackAnalysis**: Technology usage
```python
@dataclass
class TechStackAnalysis:
    languages: Dict[str, int]
    frameworks: List[str]
    tools: List[str]
    patterns: List[str]
```

## Design Patterns

### 1. Repository Pattern
- `GitHubApiClient` abstracts API access
- Collectors use repository for data access
- Enables easy testing and mocking

### 2. Strategy Pattern
- `AwardCalculator` uses strategies for different award types
- Collectors use different strategies for pagination

### 3. Builder Pattern
- Metrics construction through progressive building
- Report building using incremental sections

### 4. Facade Pattern
- CLI orchestrates complex workflows
- Simplifies interaction with subsystems

### 5. Singleton Pattern (Implicit)
- Configuration typically instantiated once
- Session reuse in API client

## Data Flow

### Feedback Generation Flow

```
1. User runs: gfa feedback owner/repo

2. CLI validates configuration
   ├─> Load config from ~/.config/github_feedback/config.toml
   └─> Validate PAT and settings

3. Data Collection (Parallel)
   ├─> CommitCollector.collect_commits()
   ├─> PRCollector.collect_pull_requests()
   ├─> ReviewCollector.collect_reviews()
   └─> IssueCollector.collect_issues()

   Each collector:
   ├─> GitHubApiClient.get() [with caching]
   ├─> Handle pagination
   └─> Return structured data

4. Analysis
   ├─> Analyzer.calculate_metrics()
   ├─> Analyzer.analyze_trends()
   ├─> Analyzer.analyze_collaboration()
   └─> Analyzer.analyze_tech_stack()

5. LLM Enhancement (Optional)
   ├─> LLMClient.analyze_commit_messages()
   ├─> LLMClient.analyze_pr_descriptions()
   └─> LLMClient.review_pull_request() [with retry logic]

6. Report Generation
   ├─> Reporter.generate_feedback_report()
   ├─> Save Markdown report
   ├─> Save JSON metrics
   └─> Display summary in console

7. Output
   └─> Files saved to ./feedback-reports/owner__repo/
```

## Security Architecture

### Credential Storage

**Keyring Integration**:
- Primary: System keyring (gnome-keyring, Keychain, etc.)
- Fallback: Encrypted file keyring (keyrings.alt)
- Thread-safe initialization with locks

**Security Measures**:
- PATs never logged or exposed
- Configuration files don't contain secrets
- Secure transmission via HTTPS
- Bearer token authentication

### API Security

- Authentication headers on all requests
- Request/response validation
- Error sanitization (no secret leakage)
- Rate limit respect

## Performance Optimizations

### 1. Caching

**API Request Caching**:
- SQLite-based cache
- 1-hour default expiration
- Reduces redundant API calls
- Significant speedup for repeated analyses

**Cache Location**: `~/.cache/github_feedback/api_cache.sqlite`

### 2. Parallel Execution

**ThreadPoolExecutor**:
- Concurrent data collection
- 3-4 worker threads (configurable)
- Significant speedup (4x typical)

### 3. Pagination Strategy

- Fetch only required pages
- Configurable limits (default 100)
- Early termination on date boundaries

### 4. Memory Efficiency

- Use `slots=True` in dataclasses
- Stream large responses
- Lazy loading where possible

## Error Handling

### Exception Hierarchy

```
BaseException
└── GFAError (base)
    ├── ConfigurationError
    ├── ApiError
    │   ├── AuthenticationError
    │   └── RateLimitError
    ├── CollectionError
    ├── AnalysisError
    └── ReportError
```

### Error Handling Strategy

1. **Network Errors**: Retry with exponential backoff
2. **API Errors**: Context-aware error messages
3. **Configuration Errors**: Clear user guidance
4. **LLM Errors**: Graceful degradation, retry logic

### Logging

- Structured logging with Python logging module
- Log levels: DEBUG, INFO, WARNING, ERROR
- Sensitive data filtering
- Configurable via environment variables

## Testing Architecture

### Test Structure

```
tests/
├── test_cli.py           # CLI command tests
├── test_config.py        # Configuration tests
├── test_collector.py     # Data collection tests
├── test_analyzer.py      # Analysis logic tests
├── test_reporter.py      # Report generation tests
├── test_review_reporter.py  # Review reporter tests
├── test_retrospective.py    # Retrospective tests
├── test_keyring_fix.py   # Keyring threading tests
├── test_integration.py   # End-to-end tests
└── test_review_workflow.py  # Review workflow tests
```

### Testing Strategies

**Unit Tests**:
- Mock external dependencies
- Test individual components
- Fast execution

**Integration Tests**:
- Test component interactions
- Use test fixtures
- Slower but comprehensive

**Mocking**:
- Mock GitHub API responses
- Mock LLM endpoints
- Use monkeypatch for isolation

## Configuration Management

### Configuration Hierarchy

1. **Default values** (hardcoded)
2. **Config file** (~/.config/github_feedback/config.toml)
3. **Environment variables** (future)
4. **Command-line arguments** (overrides all)

### Configuration Schema

```toml
[server]
api_url = "https://api.github.com"
graphql_url = "https://api.github.com/graphql"
web_url = "https://github.com"

[api]
timeout = 30
max_retries = 3
rate_limit_delay = 1

[llm]
endpoint = "https://api.openai.com/v1/chat/completions"
model = "gpt-4"
timeout = 60

[collection]
max_commits = 100
max_prs = 100
max_reviews = 100
```

## Extensibility Points

### 1. Custom Collectors

Extend `BaseCollector` to add new data sources:
```python
class CustomCollector(BaseCollector):
    def collect(self, repo: str, since: datetime) -> List[Dict]:
        # Implementation
        pass
```

### 2. Custom Analyzers

Add analysis modules:
```python
def custom_analysis(data: MetricSnapshot) -> Dict[str, Any]:
    # Custom analysis logic
    return results
```

### 3. Custom Report Formats

Implement reporters for different formats:
```python
class PDFReporter:
    def generate_report(self, data: DetailedFeedbackSnapshot) -> Path:
        # Generate PDF
        pass
```

### 4. LLM Provider Plugins

Support different LLM providers:
```python
class ClaudeClient(LLMClient):
    def complete(self, messages: List[Dict]) -> str:
        # Claude-specific implementation
        pass
```

## Future Improvements

### High Priority

1. **CLI Refactoring**: Split cli.py into modular commands
2. **Reporter Refactoring**: Extract section builders
3. **Test Coverage**: Increase to 80%+
4. **Documentation**: API docs with Sphinx

### Medium Priority

5. **Plugin System**: Support custom collectors/reporters
6. **Web Dashboard**: Interactive visualization
7. **Multiple LLM Providers**: Support Claude, local models
8. **Database Caching**: Replace in-memory with SQLite

### Low Priority

9. **Team Analytics**: Multi-user analysis
10. **Comparison Features**: Compare periods/developers
11. **Machine Learning**: Trend predictions
12. **CI/CD Integration**: GitHub Actions

## Performance Benchmarks

### Typical Performance

- **Small repo** (100 commits, 50 PRs): ~30 seconds
- **Medium repo** (500 commits, 200 PRs): ~2 minutes
- **Large repo** (1000+ commits, 500+ PRs): ~5 minutes

### Optimization Impact

- **Caching**: 60-70% speedup on repeated runs
- **Parallel collection**: 4x speedup vs sequential
- **Pagination limits**: 50% reduction in API calls

## Conclusion

GFA follows a clean, layered architecture with clear separation of concerns. The system is designed for:
- **Maintainability**: Modular design, clear responsibilities
- **Testability**: Dependency injection, mocking support
- **Extensibility**: Plugin points, custom implementations
- **Performance**: Caching, parallelization, optimization
- **Security**: Secure credential storage, proper error handling
- **Reliability**: Retry logic, graceful degradation

For questions or contributions, see [CONTRIBUTING.md](../CONTRIBUTING.md).
