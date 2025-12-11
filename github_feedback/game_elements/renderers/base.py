"""게임 렌더러 유틸리티 메소드."""
from __future__ import annotations

from typing import List

from ..constants import COLOR_PALETTE


class GameRendererBase:
    """게임 렌더러의 베이스 클래스 (유틸리티 메소드 포함)."""

    @staticmethod
    def _wrap_text(text: str, max_width: int) -> List[str]:
        """텍스트를 최대 너비로 나누어 여러 줄로 반환.

        Args:
            text: 나눌 텍스트
            max_width: 한 줄의 최대 디스플레이 너비

        Returns:
            나누어진 텍스트 줄 리스트
        """
        from ...core.utils import display_width

        if display_width(text) <= max_width:
            return [text]

        lines = []
        current_line = ""
        words = text.split()

        for word in words:
            test_line = f"{current_line} {word}".strip()
            if display_width(test_line) <= max_width:
                current_line = test_line
            else:
                if current_line:
                    lines.append(current_line)
                current_line = word

        if current_line:
            lines.append(current_line)

        return lines if lines else [text[:max_width]]

    @staticmethod
    def _convert_markdown_links_to_html(text: str) -> str:
        """마크다운 링크를 HTML 링크로 변환.

        Args:
            text: 변환할 텍스트 (마크다운 링크 포함 가능)

        Returns:
            HTML 링크로 변환된 텍스트
        """
        import re
        # 마크다운 링크 패턴: [텍스트](URL)
        pattern = r'\[([^\]]+)\]\(([^\)]+)\)'
        # HTML 링크로 변환: <a href="URL">텍스트</a>
        return re.sub(pattern, r'<a href="\2" target="_blank" style="color: #3b82f6; text-decoration: underline;">\1</a>', text)

    @staticmethod
    def get_trend_indicator(
        direction: str,
        percentage: float,
        size: str = "medium"
    ) -> str:
        """Get HTML for trend indicator with arrow and color.

        Args:
            direction: "up" or "down"
            percentage: Percentage value (positive number)
            size: "small", "medium", or "large"

        Returns:
            HTML string for trend indicator
        """
        # Size mappings
        sizes = {
            "small": {"font": "12px", "icon": "14px"},
            "medium": {"font": "14px", "icon": "16px"},
            "large": {"font": "16px", "icon": "20px"}
        }

        size_config = sizes.get(size, sizes["medium"])

        if direction == "up":
            color = COLOR_PALETTE["success"]
            arrow = "↑"
        else:
            color = COLOR_PALETTE["danger"]
            arrow = "↓"

        return f'<span style="color: {color}; font-size: {size_config["icon"]}; font-weight: 600;">{arrow} {percentage:.1f}%</span>'

    @staticmethod
    def get_trend_badge(
        label: str,
        value: float,
        trend_direction: str = None,
        trend_percentage: float = None
    ) -> str:
        """Get HTML for metric badge with optional trend.

        Args:
            label: Metric label
            value: Metric value
            trend_direction: Optional "up" or "down"
            trend_percentage: Optional percentage value

        Returns:
            HTML string for metric badge
        """
        trend_html = ""
        if trend_direction and trend_percentage is not None:
            if trend_direction == "up":
                color = COLOR_PALETTE["success"]
                arrow = "↑"
            else:
                color = COLOR_PALETTE["danger"]
                arrow = "↓"
            trend_html = f' <span style="color: {color}; font-size: 12px;">({arrow}{trend_percentage:.0f}%)</span>'

        return f'''<span style="
            display: inline-block;
            padding: 6px 12px;
            background: {COLOR_PALETTE["gray_100"]};
            border-radius: 6px;
            font-size: 14px;
            font-weight: 500;
            color: {COLOR_PALETTE["gray_800"]};
            margin: 4px;
        ">{label}: <strong>{value}</strong>{trend_html}</span>'''


__all__ = ["GameRendererBase"]
