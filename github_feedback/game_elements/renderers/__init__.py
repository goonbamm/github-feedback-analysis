"""게임 렌더러 통합 모듈."""
from __future__ import annotations

from typing import Any, Dict, List

from .base import GameRendererBase
from .cards import CardRenderer
from .charts import ChartRenderer
from .interactive import InteractiveRenderer
from .tables import TableRenderer
from .ui_components import UIComponentRenderer


class GameRenderer:
    """게임 스타일 시각화 렌더러 (모든 렌더링 메소드를 통합)."""

    # ===== Base utility methods =====
    _wrap_text = staticmethod(GameRendererBase._wrap_text)
    _convert_markdown_links_to_html = staticmethod(GameRendererBase._convert_markdown_links_to_html)
    get_trend_indicator = staticmethod(GameRendererBase.get_trend_indicator)
    get_trend_badge = staticmethod(GameRendererBase.get_trend_badge)

    # ===== Card rendering methods =====
    render_skill_card = staticmethod(CardRenderer.render_skill_card)
    render_metric_cards = staticmethod(CardRenderer.render_metric_cards)
    render_character_stats = staticmethod(CardRenderer.render_character_stats)

    # ===== Table rendering methods =====
    render_html_table = staticmethod(TableRenderer.render_html_table)
    render_skill_tree_table = staticmethod(TableRenderer.render_skill_tree_table)

    # ===== Chart rendering methods =====
    render_monthly_chart = staticmethod(ChartRenderer.render_monthly_chart)
    render_line_chart = staticmethod(ChartRenderer.render_line_chart)
    render_donut_chart = staticmethod(ChartRenderer.render_donut_chart)
    render_radar_chart = staticmethod(ChartRenderer.render_radar_chart)

    # ===== UI component methods =====
    render_info_box = staticmethod(UIComponentRenderer.render_info_box)
    render_awards_grid = staticmethod(UIComponentRenderer.render_awards_grid)
    render_loading_skeleton = staticmethod(UIComponentRenderer.render_loading_skeleton)
    render_progress_indicator = staticmethod(UIComponentRenderer.render_progress_indicator)
    render_spinner = staticmethod(UIComponentRenderer.render_spinner)

    # ===== Interactive component methods =====
    render_collapsible_section = staticmethod(InteractiveRenderer.render_collapsible_section)
    render_filterable_list = staticmethod(InteractiveRenderer.render_filterable_list)


__all__ = [
    "GameRenderer",
    "GameRendererBase",
    "CardRenderer",
    "TableRenderer",
    "ChartRenderer",
    "UIComponentRenderer",
    "InteractiveRenderer",
]
