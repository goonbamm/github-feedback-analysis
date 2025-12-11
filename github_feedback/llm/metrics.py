"""Metrics collection and monitoring for LLM API calls."""

from __future__ import annotations

import logging
import time
from dataclasses import dataclass, field
from threading import Lock
from typing import Any

logger = logging.getLogger(__name__)


@dataclass
class LLMCallMetrics:
    """Metrics for a single LLM API call."""

    operation: str  # e.g., "analyze_commits", "personal_development"
    duration_seconds: float
    prompt_tokens: int = 0
    completion_tokens: int = 0
    total_tokens: int = 0
    cache_hit: bool = False
    success: bool = True
    error_type: str | None = None
    retry_count: int = 0
    timestamp: float = field(default_factory=time.time)

    @property
    def cost_estimate(self) -> float:
        """Estimate cost in USD (rough approximation for GPT-4 pricing).

        Note: This is a rough estimate. Actual pricing varies by model.
        GPT-4 approximate pricing (as of 2024):
        - Input: $0.03 per 1K tokens
        - Output: $0.06 per 1K tokens
        """
        if self.cache_hit:
            return 0.0  # No cost for cache hits

        input_cost = (self.prompt_tokens / 1000) * 0.03
        output_cost = (self.completion_tokens / 1000) * 0.06
        return input_cost + output_cost


@dataclass
class AggregatedMetrics:
    """Aggregated metrics across multiple LLM calls."""

    total_calls: int = 0
    successful_calls: int = 0
    failed_calls: int = 0
    cache_hits: int = 0
    total_duration: float = 0.0
    total_prompt_tokens: int = 0
    total_completion_tokens: int = 0
    total_tokens: int = 0
    total_retries: int = 0
    operations: dict[str, int] = field(default_factory=dict)
    errors: dict[str, int] = field(default_factory=dict)

    @property
    def cache_hit_rate(self) -> float:
        """Calculate cache hit rate."""
        return self.cache_hits / self.total_calls if self.total_calls > 0 else 0.0

    @property
    def success_rate(self) -> float:
        """Calculate success rate."""
        return self.successful_calls / self.total_calls if self.total_calls > 0 else 0.0

    @property
    def avg_duration(self) -> float:
        """Calculate average duration per call."""
        return self.total_duration / self.total_calls if self.total_calls > 0 else 0.0

    @property
    def estimated_total_cost(self) -> float:
        """Estimate total cost in USD (rough approximation)."""
        input_cost = (self.total_prompt_tokens / 1000) * 0.03
        output_cost = (self.total_completion_tokens / 1000) * 0.06
        return input_cost + output_cost

    def format_summary(self) -> str:
        """Format a human-readable summary of metrics."""
        lines = [
            "=== LLM Metrics Summary ===",
            f"Total Calls: {self.total_calls}",
            f"Success Rate: {self.success_rate:.1%}",
            f"Cache Hit Rate: {self.cache_hit_rate:.1%}",
            f"Avg Duration: {self.avg_duration:.2f}s",
            f"Total Tokens: {self.total_tokens:,} (prompt: {self.total_prompt_tokens:,}, completion: {self.total_completion_tokens:,})",
            f"Estimated Cost: ${self.estimated_total_cost:.4f}",
            f"Total Retries: {self.total_retries}",
        ]

        if self.operations:
            lines.append("\nOperations:")
            for op, count in sorted(self.operations.items(), key=lambda x: x[1], reverse=True):
                lines.append(f"  - {op}: {count}")

        if self.errors:
            lines.append("\nErrors:")
            for error, count in sorted(self.errors.items(), key=lambda x: x[1], reverse=True):
                lines.append(f"  - {error}: {count}")

        return "\n".join(lines)


class LLMMetricsCollector:
    """Thread-safe collector for LLM metrics."""

    def __init__(self) -> None:
        self._metrics: list[LLMCallMetrics] = []
        self._lock = Lock()

    def record(self, metrics: LLMCallMetrics) -> None:
        """Record metrics for a single LLM call.

        Args:
            metrics: Metrics to record
        """
        with self._lock:
            self._metrics.append(metrics)

    def get_aggregated(self) -> AggregatedMetrics:
        """Get aggregated metrics across all recorded calls.

        Returns:
            AggregatedMetrics with summary statistics
        """
        with self._lock:
            metrics = self._metrics.copy()

        agg = AggregatedMetrics()

        for m in metrics:
            agg.total_calls += 1

            if m.success:
                agg.successful_calls += 1
            else:
                agg.failed_calls += 1
                if m.error_type:
                    agg.errors[m.error_type] = agg.errors.get(m.error_type, 0) + 1

            if m.cache_hit:
                agg.cache_hits += 1

            agg.total_duration += m.duration_seconds
            agg.total_prompt_tokens += m.prompt_tokens
            agg.total_completion_tokens += m.completion_tokens
            agg.total_tokens += m.total_tokens
            agg.total_retries += m.retry_count

            agg.operations[m.operation] = agg.operations.get(m.operation, 0) + 1

        return agg

    def clear(self) -> None:
        """Clear all collected metrics."""
        with self._lock:
            self._metrics.clear()

    def get_recent(self, n: int = 10) -> list[LLMCallMetrics]:
        """Get the N most recent metrics.

        Args:
            n: Number of recent metrics to retrieve

        Returns:
            List of recent metrics
        """
        with self._lock:
            return self._metrics[-n:].copy()


# Global metrics collector instance
_global_collector = LLMMetricsCollector()


def get_global_collector() -> LLMMetricsCollector:
    """Get the global metrics collector instance."""
    return _global_collector


def print_metrics_summary() -> None:
    """Print a summary of collected metrics to the logger."""
    collector = get_global_collector()
    agg = collector.get_aggregated()
    summary = agg.format_summary()
    logger.info(f"\n{summary}")
    print(f"\n{summary}")


__all__ = [
    "LLMCallMetrics",
    "AggregatedMetrics",
    "LLMMetricsCollector",
    "get_global_collector",
    "print_metrics_summary",
]
