"""UI 컴포넌트 렌더링 메소드."""
from __future__ import annotations

from typing import Dict, List

from ..constants import COLOR_PALETTE


class UIComponentRenderer:
    """UI 컴포넌트 렌더링 클래스."""

    @staticmethod
    def render_info_box(
        title: str,
        content: str,
        emoji: str = "💡",
        bg_color: str = "#eef2ff",
        border_color: str = "#667eea"
    ) -> List[str]:
        """정보 박스 렌더링.

        Args:
            title: 박스 제목
            content: 박스 내용
            emoji: 이모지
            bg_color: 배경색
            border_color: 테두리 색

        Returns:
            마크다운 라인 리스트
        """
        lines = []

        lines.append(f'<div style="border-left: 4px solid {border_color}; background: {bg_color}; padding: 16px; margin: 16px 0; border-radius: 4px;">')
        lines.append(f'  <div style="display: flex; align-items: center; margin-bottom: 8px;">')
        lines.append(f'    <span style="font-size: 1.5em; margin-right: 8px;">{emoji}</span>')
        lines.append(f'    <h4 style="margin: 0; color: #2d3748; font-size: 1.1em;">{title}</h4>')
        lines.append(f'  </div>')
        lines.append(f'  <div style="color: #4a5568; line-height: 1.6; white-space: pre-wrap;">{content}</div>')
        lines.append('</div>')
        lines.append("")

        return lines

    @staticmethod
    def render_awards_grid(
        awards: List[Dict[str, str]],
        columns: int = 2
    ) -> List[str]:
        """어워즈 그리드 렌더링.

        Args:
            awards: 어워즈 딕셔너리 리스트
                   각 딕셔너리는 {"category": "...", "description": "...", "emoji": "...", "count": "..."}
            columns: 열 개수

        Returns:
            마크다운 라인 리스트
        """
        lines = []

        lines.append(f'<div style="display: grid; grid-template-columns: repeat({columns}, 1fr); gap: 16px; margin: 16px 0;">')

        for award in awards:
            category = award.get("category", "")
            description = award.get("description", "")
            emoji = award.get("emoji", "🏆")
            count = award.get("count", "0")

            # 어워드 카드
            lines.append('  <div style="border: 2px solid #fbbf24; border-radius: 8px; padding: 16px; background: linear-gradient(135deg, #fef3c7 0%, #fde68a 100%); box-shadow: 0 2px 4px rgba(251, 191, 36, 0.3);">')
            lines.append(f'    <div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 8px;">')
            lines.append(f'      <span style="font-size: 2em;">{emoji}</span>')
            lines.append(f'      <span style="background: #f59e0b; color: white; padding: 4px 8px; border-radius: 12px; font-size: 0.85em; font-weight: bold;">{count}</span>')
            lines.append(f'    </div>')
            lines.append(f'    <h4 style="margin: 0 0 4px 0; color: #78350f; font-size: 1.1em;">{category}</h4>')
            lines.append(f'    <p style="margin: 0; color: #92400e; font-size: 0.9em; line-height: 1.4;">{description}</p>')
            lines.append('  </div>')

        lines.append('</div>')
        lines.append("")

        return lines

    @staticmethod
    def render_loading_skeleton(
        num_rows: int = 3,
        title: str = "로딩 중..."
    ) -> List[str]:
        """스켈레톤 로딩 UI 렌더링.

        Args:
            num_rows: 스켈레톤 행 개수
            title: 로딩 메시지

        Returns:
            마크다운 라인 리스트
        """
        lines = []

        lines.append(f'<div style="border: 2px solid {COLOR_PALETTE["gray_200"]}; border-radius: 12px; padding: 24px; margin: 16px 0; background: white; box-shadow: 0 4px 6px rgba(0,0,0,0.1);">')
        lines.append(f'  <div style="display: flex; align-items: center; gap: 12px; margin-bottom: 20px;">')
        lines.append(f'    <div class="skeleton" style="width: 40px; height: 40px; border-radius: 50%;"></div>')
        lines.append(f'    <div style="flex: 1;">')
        lines.append(f'      <div style="font-weight: bold; color: {COLOR_PALETTE["gray_600"]};">{title}</div>')
        lines.append(f'    </div>')
        lines.append(f'  </div>')

        for _ in range(num_rows):
            lines.append(f'  <div class="skeleton" style="height: 20px; margin-bottom: 12px; border-radius: 4px;"></div>')

        lines.append('</div>')
        lines.append("")

        return lines

    @staticmethod
    def render_progress_indicator(
        current: int,
        total: int,
        label: str = "진행 중...",
        show_percentage: bool = True
    ) -> List[str]:
        """프로그레스 인디케이터 렌더링 (보고서 생성 진행 상황 표시).

        Args:
            current: 현재 진행 값
            total: 전체 값
            label: 진행 레이블
            show_percentage: 백분율 표시 여부

        Returns:
            마크다운 라인 리스트
        """
        lines = []

        percentage = (current / total * 100) if total > 0 else 0

        lines.append(f'<div style="border: 2px solid {COLOR_PALETTE["primary"]}; border-radius: 12px; padding: 24px; margin: 16px 0; background: linear-gradient(135deg, {COLOR_PALETTE["bg_gradient_purple_start"]}15 0%, {COLOR_PALETTE["bg_gradient_purple_end"]}15 100%); box-shadow: 0 4px 6px rgba(0,0,0,0.1);">')

        # 레이블 및 카운터
        lines.append(f'  <div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 12px;">')
        lines.append(f'    <div style="font-weight: bold; color: {COLOR_PALETTE["gray_800"]}; font-size: 1.1em;">{label}</div>')
        if show_percentage:
            lines.append(f'    <div style="font-weight: bold; color: {COLOR_PALETTE["primary"]}; font-size: 1.2em;">{int(percentage)}%</div>')
        else:
            lines.append(f'    <div style="color: {COLOR_PALETTE["gray_600"]}; font-size: 0.95em;">{current} / {total}</div>')
        lines.append(f'  </div>')

        # 프로그레스 바
        lines.append(f'  <div style="background: {COLOR_PALETTE["gray_200"]}; border-radius: 12px; height: 24px; overflow: hidden; position: relative; box-shadow: inset 0 2px 4px rgba(0,0,0,0.1);">')
        lines.append(f'    <div style="background: linear-gradient(90deg, {COLOR_PALETTE["primary"]} 0%, {COLOR_PALETTE["secondary"]} 100%); height: 100%; width: {percentage}%; transition: width 0.5s cubic-bezier(0.4, 0, 0.2, 1); position: relative; overflow: hidden; box-shadow: 0 0 15px {COLOR_PALETTE["primary"]}60;">')
        lines.append(f'      <div style="position: absolute; top: 0; left: 0; right: 0; bottom: 0; background: linear-gradient(90deg, transparent 0%, rgba(255,255,255,0.4) 50%, transparent 100%); animation: shimmer 1.5s infinite;"></div>')
        lines.append(f'    </div>')
        lines.append(f'  </div>')

        # 상세 정보
        lines.append(f'  <div style="margin-top: 12px; text-align: center; color: {COLOR_PALETTE["gray_600"]}; font-size: 0.9em;">')
        lines.append(f'    처리 중: {current} / {total} 항목 완료')
        lines.append(f'  </div>')

        lines.append('</div>')
        lines.append("")

        return lines

    @staticmethod
    def render_spinner(
        message: str = "처리 중...",
        size: int = 40
    ) -> List[str]:
        """스피너 애니메이션 렌더링.

        Args:
            message: 스피너와 함께 표시할 메시지
            size: 스피너 크기 (픽셀)

        Returns:
            마크다운 라인 리스트
        """
        lines = []

        lines.append('<div style="display: flex; align-items: center; justify-content: center; padding: 40px; margin: 20px 0;">')
        lines.append(f'  <div style="display: flex; flex-direction: column; align-items: center; gap: 16px;">')

        # SVG 스피너
        lines.append(f'    <svg width="{size}" height="{size}" viewBox="0 0 {size} {size}" xmlns="http://www.w3.org/2000/svg">')
        lines.append(f'      <circle cx="{size/2}" cy="{size/2}" r="{size/2 - 4}" stroke="{COLOR_PALETTE["gray_200"]}" stroke-width="4" fill="none"/>')
        lines.append(f'      <circle cx="{size/2}" cy="{size/2}" r="{size/2 - 4}" stroke="{COLOR_PALETTE["primary"]}" stroke-width="4" fill="none" stroke-dasharray="{size * 1.5} {size * 3}" stroke-linecap="round" style="animation: spin 1s linear infinite; transform-origin: center;">')
        lines.append('        <animateTransform attributeName="transform" type="rotate" from="0 20 20" to="360 20 20" dur="1s" repeatCount="indefinite"/>')
        lines.append('      </circle>')
        lines.append('    </svg>')

        # 메시지
        lines.append(f'    <div style="font-weight: 500; color: {COLOR_PALETTE["gray_700"]}; font-size: 1.1em;">{message}</div>')

        lines.append('  </div>')
        lines.append('</div>')
        lines.append("")

        # CSS for spin animation
        lines.append('<style>')
        lines.append('@keyframes spin {')
        lines.append('  from { transform: rotate(0deg); }')
        lines.append('  to { transform: rotate(360deg); }')
        lines.append('}')
        lines.append('</style>')
        lines.append("")

        return lines


__all__ = ["UIComponentRenderer"]
