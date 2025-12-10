"""데이터 모델 - 연말 결산 보고서용 데이터 구조."""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Any, Dict, List, Optional


@dataclass
class RepositoryAnalysis:
    """Individual repository analysis data."""

    full_name: str
    pr_count: int
    commit_count: int
    year_commits: int
    integrated_report_path: Optional[Path] = None
    personal_dev_path: Optional[Path] = None
    strengths: List[Dict[str, Any]] = None
    improvements: List[Dict[str, Any]] = None
    growth_indicators: List[Dict[str, Any]] = None
    tech_stack: Dict[str, int] = None
    # Communication skills data
    commit_message_quality: Optional[float] = None  # 0-100
    pr_title_quality: Optional[float] = None  # 0-100
    review_tone_quality: Optional[float] = None  # 0-100
    issue_quality: Optional[float] = None  # 0-100
    commit_stats: Optional[Dict[str, int]] = None  # {total, good, poor}
    pr_title_stats: Optional[Dict[str, int]] = None  # {total, clear, unclear}
    review_tone_stats: Optional[Dict[str, int]] = None  # {constructive, harsh, neutral}
    issue_stats: Optional[Dict[str, int]] = None  # {total, clear, unclear}

    def __post_init__(self):
        if self.strengths is None:
            self.strengths = []
        if self.improvements is None:
            self.improvements = []
        if self.growth_indicators is None:
            self.growth_indicators = []
        if self.tech_stack is None:
            self.tech_stack = {}
        if self.commit_stats is None:
            self.commit_stats = {}
        if self.pr_title_stats is None:
            self.pr_title_stats = {}
        if self.review_tone_stats is None:
            self.review_tone_stats = {}
        if self.issue_stats is None:
            self.issue_stats = {}


__all__ = ["RepositoryAnalysis"]
