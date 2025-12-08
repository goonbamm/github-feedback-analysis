"""테이블 렌더링 메소드."""
from __future__ import annotations

import html
from typing import Any, Dict, List, Tuple

from ..constants import COLOR_PALETTE
from .base import GameRendererBase


class TableRenderer:
    """테이블 스타일 렌더링 클래스."""

    @staticmethod
    def render_html_table(
        headers: List[str],
        rows: List[List[str]],
        title: str = "",
        description: str = "",
        striped: bool = True,
        escape_cells: bool = True
    ) -> List[str]:
        """범용 HTML 테이블 렌더링.

        Args:
            headers: 테이블 헤더 리스트
            rows: 테이블 행 데이터 (각 행은 문자열 리스트)
            title: 테이블 제목 (선택)
            description: 테이블 설명 (선택)
            striped: 줄무늬 스타일 적용 여부
            escape_cells: True면 각 셀을 HTML 이스케이프하여 렌더링

        Returns:
            마크다운 라인 리스트
        """
        lines = []

        # 컨테이너 시작
        lines.append('<div style="border: 2px solid #e2e8f0; border-radius: 8px; padding: 16px; margin: 16px 0; background: white; box-shadow: 0 2px 4px rgba(0,0,0,0.1);">')

        # 제목 및 설명
        if title:
            lines.append(f'  <h4 style="margin: 0 0 8px 0; color: #2d3748; font-size: 1.2em;">{title}</h4>')
        if description:
            lines.append(f'  <p style="margin: 0 0 12px 0; color: #718096; font-size: 0.9em;">{description}</p>')

        # 테이블 시작
        lines.append('  <table style="width: 100%; border-collapse: collapse; font-size: 0.95em;">')

        # 헤더
        lines.append('    <thead>')
        lines.append('      <tr style="background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); color: white;">')
        for header in headers:
            lines.append(f'        <th style="padding: 12px; text-align: left; font-weight: 600;">{header}</th>')
        lines.append('      </tr>')
        lines.append('    </thead>')

        # 바디
        lines.append('    <tbody>')
        for idx, row in enumerate(rows):
            bg_color = '#f7fafc' if striped and idx % 2 == 0 else 'white'
            lines.append(f'      <tr style="background: {bg_color}; border-bottom: 1px solid #e2e8f0;">')
            for cell in row:
                cell_content = str(cell)
                if escape_cells:
                    cell_content = html.escape(cell_content)
                cell_with_links = GameRendererBase._convert_markdown_links_to_html(cell_content)
                lines.append(f'        <td style="padding: 10px; color: #2d3748;">{cell_with_links}</td>')
            lines.append('      </tr>')
        lines.append('    </tbody>')

        lines.append('  </table>')
        lines.append('</div>')
        lines.append("")

        return lines

    @staticmethod
    def render_skill_tree_table(
        acquired_skills: List[Dict[str, Any]],
        growing_skills: List[Dict[str, Any]],
        available_skills: List[Dict[str, Any]]
    ) -> List[str]:
        """스킬 트리를 하나의 HTML 테이블로 통합 렌더링.

        Args:
            acquired_skills: 획득한 스킬 리스트 (각 항목은 {"name": str, "type": str, "mastery": int, "effect": str, "evidence": List[str], "emoji": str})
            growing_skills: 성장 중인 스킬 리스트
            available_skills: 습득 가능한 스킬 리스트

        Returns:
            마크다운 라인 리스트
        """
        lines = []

        # 테이블 헤더
        headers = ["구분", "스킬명", "레벨", "마스터리", "효과", "증거/습득경로"]
        rows = []

        # 타입 이모지 매핑
        type_emojis = {
            "패시브": "🟢",
            "액티브": "🔵",
            "성장중": "🟡",
            "미습득": "🔴"
        }

        def _sanitize(text: str) -> str:
            return html.escape(text, quote=False)

        def _build_evidence(evidence_list: List[str]) -> str:
            evidence_html = "<br>".join(
                [
                    f"• {GameRendererBase._convert_markdown_links_to_html(_sanitize(ev))}"
                    for ev in evidence_list[:5]
                ]
            )
            if len(evidence_list) > 5:
                evidence_html += f"<br>... 외 {len(evidence_list) - 5}개"
            return evidence_html

        def _render_row(
            prefix: str,
            skill: Dict[str, Any],
            default_type: str,
            mastery_default: int,
            bar_colors: Tuple[str, str]
        ) -> None:
            mastery = skill.get("mastery", mastery_default)
            stars = min(5, mastery // 20)
            star_display = "★" * stars + "☆" * (5 - stars)
            level = min(5, (mastery // 20) + 1)

            skill_type_raw = skill.get("type", default_type)
            skill_type = _sanitize(skill_type_raw)
            type_emoji = type_emojis.get(skill_type_raw, "⚪")
            skill_name = _sanitize(skill.get("name", ""))

            mastery_bar = (
                f'<div style="background: {COLOR_PALETTE["gray_200"]}; border-radius: 6px; height: 10px; overflow: hidden; position: relative; box-shadow: inset 0 1px 3px rgba(0,0,0,0.1);">'
                f'<div style="background: linear-gradient(90deg, {bar_colors[0]} 0%, {bar_colors[1]} 100%); height: 100%; width: {mastery}%; transition: width 0.6s cubic-bezier(0.4, 0, 0.2, 1); box-shadow: 0 0 8px rgba(16, 185, 129, 0.4);"></div>'
                "</div>"
            )
            mastery_display = f'<span style="font-weight: bold; color: {bar_colors[1]};">{mastery}%</span><br>{mastery_bar}'

            evidence_list = skill.get("evidence", []) or []
            evidence_html = _build_evidence(evidence_list)

            effect_text = _sanitize(skill.get("effect", ""))

            rows.append([
                prefix,
                f'{skill.get("emoji", "💠")} <strong>{skill_name}</strong>',
                f'Lv.{level}<br>{star_display}',
                mastery_display,
                f'{type_emoji} {skill_type}<br><span style="color: #6b7280; font-size: 0.9em;">{GameRendererBase._convert_markdown_links_to_html(effect_text)}</span>',
                evidence_html if evidence_html else "-",
            ])

        for skill in acquired_skills:
            _render_row('💎 <strong>획득</strong>', skill, "패시브", 0, ("#4ade80", "#22c55e"))

        for skill in growing_skills:
            _render_row('🌱 <strong>성장중</strong>', skill, "성장중", 60, ("#fbbf24", "#f59e0b"))

        for skill in available_skills:
            _render_row('🎯 <strong>습득 가능</strong>', skill, "미습득", 40, ("#ef4444", "#dc2626"))

        # HTML 테이블 렌더링
        if rows:
            lines.extend(TableRenderer.render_html_table(
                headers=headers,
                rows=rows,
                title="",
                description="",
                striped=True,
                escape_cells=False
            ))

        return lines


__all__ = ["TableRenderer"]
