"""Section builders for report generation."""

from .base_builder import MarkdownSectionBuilder, SectionBuilder
from .fun_stats_builder import FunStatsBuilder
from .prediction_builder import PredictionBuilder
from .storytelling_builder import StorytellingBuilder
from .streak_builder import StreakBuilder
from .time_machine_builder import TimeMachineBuilder

__all__ = [
    "MarkdownSectionBuilder",
    "SectionBuilder",
    "StreakBuilder",
    "TimeMachineBuilder",
    "FunStatsBuilder",
    "PredictionBuilder",
    "StorytellingBuilder",
]
