"""Trends analysis modules."""

from .fun_statistics_analyzer import FunStatisticsAnalyzer
from .prediction_analyzer import PredictionAnalyzer
from .streak_analyzer import StreakAnalyzer
from .time_machine_analyzer import TimeMachineAnalyzer
from .trends_analyzer import (
    CollaborationNetworkBuilder,
    MonthlyInsightsGenerator,
    MonthlyTrendsBuilder,
    TechStackAnalyzer,
    TrendAnalyzer,
)

__all__ = [
    "CollaborationNetworkBuilder",
    "MonthlyInsightsGenerator",
    "MonthlyTrendsBuilder",
    "TechStackAnalyzer",
    "TrendAnalyzer",
    "StreakAnalyzer",
    "TimeMachineAnalyzer",
    "FunStatisticsAnalyzer",
    "PredictionAnalyzer",
]
