"""카드 렌더링 메소드."""
from __future__ import annotations

from typing import Any, Dict, List

from ..constants import COLOR_PALETTE


class CardRenderer:
    """카드 스타일 렌더링 클래스."""

    @staticmethod
    def render_skill_card(
        skill_name: str,
        skill_type: str,
        mastery_level: int,
        effect_description: str,
        evidence: List[str],
        skill_emoji: str = "💎"
    ) -> List[str]:
        """게임 스타일 스킬 카드 렌더링 (HTML 테이블 사용).

        Args:
            skill_name: 스킬 이름
            skill_type: 타입 (패시브/액티브/성장중/미습득)
            mastery_level: 마스터리 퍼센트 (0-100)
            effect_description: 스킬 효과 설명
            evidence: 증거/습득 경로 리스트
            skill_emoji: 스킬 이모지

        Returns:
            마크다운 라인 리스트
        """
        lines = []

        # 마스터리에서 레벨 계산 (0-5 별)
        stars = min(5, mastery_level // 20)
        star_display = "★" * stars + "☆" * (5 - stars)
        level = min(5, (mastery_level // 20) + 1)

        # 타입 이모지 매핑
        type_emojis = {
            "패시브": "🟢",
            "액티브": "🔵",
            "성장중": "🟡",
            "미습득": "🔴"
        }
        type_emoji = type_emojis.get(skill_type, "⚪")

        # 마스터리 바 (진행률을 시각적으로 표현)
        mastery_percentage = mastery_level
        bar_filled_width = mastery_percentage  # CSS에서 퍼센트로 사용

        # HTML 테이블로 스킬 카드 렌더링
        lines.append('<div style="border: 2px solid #444; border-radius: 8px; padding: 16px; margin: 16px 0; background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); color: white; font-family: \'Segoe UI\', Tahoma, Geneva, Verdana, sans-serif;">')

        # 스킬명 및 레벨
        lines.append(f'  <div style="font-size: 1.3em; font-weight: bold; margin-bottom: 8px; word-wrap: break-word; overflow-wrap: break-word; line-height: 1.4;">')
        lines.append(f'    {skill_emoji} {skill_name} <span style="background: rgba(255,255,255,0.2); padding: 2px 8px; border-radius: 4px; font-size: 0.8em;">Lv.{level}</span>')
        lines.append(f'  </div>')

        # 별 표시
        lines.append(f'  <div style="margin-bottom: 12px; font-size: 1.2em; color: #ffd700;">')
        lines.append(f'    {star_display}')
        lines.append(f'  </div>')

        # 스킬 타입
        lines.append(f'  <table style="width: 100%; border-collapse: collapse; margin-bottom: 8px;">')
        lines.append(f'    <tr>')
        lines.append(f'      <td style="padding: 8px; background: rgba(0,0,0,0.2); border-radius: 4px;"><strong>타입</strong></td>')
        lines.append(f'      <td style="padding: 8px; background: rgba(0,0,0,0.2); border-radius: 4px;">{type_emoji} {skill_type}</td>')
        lines.append(f'    </tr>')
        lines.append(f'  </table>')

        # 효과 설명
        lines.append(f'  <div style="background: rgba(0,0,0,0.2); padding: 12px; border-radius: 4px; margin-bottom: 12px;">')
        lines.append(f'    <div style="font-weight: bold; margin-bottom: 4px;">💫 효과</div>')
        lines.append(f'    <div style="opacity: 0.95; word-wrap: break-word; overflow-wrap: break-word; white-space: pre-wrap; line-height: 1.6;">{effect_description}</div>')
        lines.append(f'  </div>')

        # 마스터리 바 (개선된 버전 with 애니메이션)
        lines.append(f'  <div style="margin-bottom: 12px;">')
        lines.append(f'    <div style="display: flex; justify-content: space-between; margin-bottom: 6px;">')
        lines.append(f'      <span style="font-weight: bold; font-size: 0.95em;">마스터리</span>')
        lines.append(f'      <span style="font-weight: bold; color: {COLOR_PALETTE["success_light"]}; font-size: 0.95em;">{mastery_percentage}%</span>')
        lines.append(f'    </div>')
        lines.append(f'    <div style="background: rgba(0,0,0,0.3); border-radius: 12px; height: 24px; overflow: hidden; position: relative; box-shadow: inset 0 2px 4px rgba(0,0,0,0.2);">')
        lines.append(f'      <div style="background: linear-gradient(90deg, {COLOR_PALETTE["success"]} 0%, {COLOR_PALETTE["success_dark"]} 100%); height: 100%; width: {bar_filled_width}%; transition: width 0.8s cubic-bezier(0.4, 0, 0.2, 1); position: relative; overflow: hidden; box-shadow: 0 0 10px rgba(16, 185, 129, 0.5);">')
        lines.append(f'        <div style="position: absolute; top: 0; left: 0; right: 0; bottom: 0; background: linear-gradient(90deg, transparent 0%, rgba(255,255,255,0.3) 50%, transparent 100%); animation: shimmer 2s infinite;"></div>')
        lines.append(f'      </div>')
        lines.append(f'    </div>')
        lines.append(f'  </div>')

        # 습득 경로
        if evidence:
            lines.append(f'  <div style="background: rgba(0,0,0,0.2); padding: 12px; border-radius: 4px;">')
            lines.append(f'    <div style="font-weight: bold; margin-bottom: 8px;">📚 습득 경로</div>')
            lines.append(f'    <ol style="margin: 0; padding-left: 20px;">')
            for ev in evidence:  # 모든 증거 표시 (제한 제거)
                lines.append(f'      <li style="margin-bottom: 4px; opacity: 0.95; word-wrap: break-word; overflow-wrap: break-word; white-space: pre-wrap; line-height: 1.6;">{ev}</li>')
            lines.append(f'    </ol>')
            lines.append(f'  </div>')

        lines.append('</div>')
        lines.append("")

        return lines

    @staticmethod
    def render_metric_cards(
        metrics: List[Dict[str, str]],
        columns: int = 3
    ) -> List[str]:
        """메트릭 카드 그리드 렌더링.

        Args:
            metrics: 메트릭 딕셔너리 리스트
                    각 딕셔너리는 {"title": "...", "value": "...", "emoji": "...", "color": "#..."}
            columns: 열 개수 (기본 3)

        Returns:
            마크다운 라인 리스트
        """
        lines = []

        # 그리드 컨테이너
        lines.append(f'<div style="display: grid; grid-template-columns: repeat({columns}, 1fr); gap: 16px; margin: 16px 0;">')

        for metric in metrics:
            title = metric.get("title", "")
            value = metric.get("value", "")
            emoji = metric.get("emoji", "📊")
            color = metric.get("color", "#667eea")

            # 카드
            lines.append('  <div style="border: 2px solid #e2e8f0; border-radius: 8px; padding: 16px; background: white; box-shadow: 0 2px 4px rgba(0,0,0,0.1); text-align: center;">')
            lines.append(f'    <div style="font-size: 2em; margin-bottom: 8px;">{emoji}</div>')
            lines.append(f'    <div style="font-size: 0.9em; color: #718096; margin-bottom: 4px;">{title}</div>')
            lines.append(f'    <div style="font-size: 1.8em; font-weight: bold; color: {color};">{value}</div>')
            lines.append('  </div>')

        lines.append('</div>')
        lines.append("")

        return lines

    @staticmethod
    def render_character_stats(
        level: int,
        title: str,
        rank_emoji: str,
        specialty_title: str,
        stats: Dict[str, int],
        experience_data: Dict[str, int],
        badges: List[str],
        use_tier_system: bool = False
    ) -> List[str]:
        """RPG 스타일 캐릭터 스탯 시각화 렌더링 (HTML 테이블 사용).

        Args:
            level: 레벨 (1-99) 또는 티어 (1-6)
            title: 레벨 타이틀 (예: "마스터", "그랜드마스터")
            rank_emoji: 랭크 이모지 (예: "👑", "🏆")
            specialty_title: 특성 타이틀 (예: "코드 아키텍트")
            stats: 능력치 딕셔너리 {"code_quality": 85, ...}
            experience_data: 경험치 데이터 딕셔너리
            badges: 획득한 뱃지 리스트
            use_tier_system: True면 "Tier X", False면 "Lv.X" 표시

        Returns:
            마크다운 라인 리스트
        """
        lines = []
        avg_stat = sum(stats.values()) / len(stats) if stats else 0

        # HTML 캐릭터 스탯 카드
        lines.append('<div style="border: 3px solid #2d3748; border-radius: 12px; padding: 20px; margin: 20px 0; background: linear-gradient(135deg, #1a202c 0%, #2d3748 100%); color: white; font-family: \'Segoe UI\', Tahoma, Geneva, Verdana, sans-serif; box-shadow: 0 4px 6px rgba(0,0,0,0.3);">')

        # 헤더: 레벨, 타이틀, 파워
        level_display = f"Tier {level}" if use_tier_system else f"Lv.{level}"
        lines.append(f'  <div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 16px; padding-bottom: 16px; border-bottom: 2px solid #4a5568;">')
        lines.append(f'    <div>')
        lines.append(f'      <div style="font-size: 1.5em; font-weight: bold;">{rank_emoji} {level_display}: {title}</div>')
        lines.append(f'      <div style="font-size: 1.1em; color: #fbbf24; margin-top: 4px;">🏅 특성: {specialty_title}</div>')
        lines.append(f'    </div>')
        lines.append(f'    <div style="text-align: right;">')
        lines.append(f'      <div style="font-size: 0.9em; color: #cbd5e0;">총 파워</div>')
        lines.append(f'      <div style="font-size: 2em; font-weight: bold; color: #48bb78;">{int(avg_stat)}<span style="font-size: 0.6em; color: #cbd5e0;">/100</span></div>')
        lines.append(f'    </div>')
        lines.append(f'  </div>')

        # 능력치 현황
        lines.append(f'  <div style="margin-bottom: 16px;">')
        lines.append(f'    <h4 style="margin: 0 0 12px 0; color: #e2e8f0; font-size: 1.1em;">⚔️ 능력치 현황</h4>')

        # 각 스탯 렌더링
        stat_emojis = {
            "code_quality": "💻",
            "collaboration": "🤝",
            "problem_solving": "🧩",
            "productivity": "⚡",
            "consistency": "📅",
            "growth": "📈",
        }

        stat_names_kr = {
            "code_quality": "코드 품질",
            "collaboration": "협업력",
            "problem_solving": "문제 해결력",
            "productivity": "생산성",
            "consistency": "꾸준함",
            "growth": "성장성",
        }

        # 스탯 색상 정의
        stat_colors = {
            "code_quality": "#3b82f6",  # 파란색
            "collaboration": "#8b5cf6",  # 보라색
            "problem_solving": "#ec4899",  # 핑크색
            "productivity": "#f59e0b",  # 주황색
            "consistency": "#f97316",  # 진한 주황
            "growth": "#10b981",  # 초록색
        }

        for stat_key, stat_value in stats.items():
            stat_name = stat_names_kr.get(stat_key, stat_key)
            emoji = stat_emojis.get(stat_key, "📊")
            color = stat_colors.get(stat_key, "#6b7280")

            lines.append(f'    <div style="margin-bottom: 14px;">')
            lines.append(f'      <div style="display: flex; justify-content: space-between; margin-bottom: 6px;">')
            lines.append(f'        <span style="font-weight: bold; font-size: 0.95em;">{emoji} {stat_name}</span>')
            lines.append(f'        <span style="font-weight: bold; color: {color}; font-size: 0.95em;">{stat_value}/100</span>')
            lines.append(f'      </div>')
            lines.append(f'      <div style="background: rgba(255,255,255,0.1); border-radius: 12px; height: 18px; overflow: hidden; position: relative; box-shadow: inset 0 2px 4px rgba(0,0,0,0.3);">')
            lines.append(f'        <div style="background: linear-gradient(90deg, {color} 0%, {color}dd 100%); height: 100%; width: {stat_value}%; transition: width 0.8s cubic-bezier(0.4, 0, 0.2, 1); position: relative; overflow: hidden; box-shadow: 0 0 12px {color}80;">')
            lines.append(f'          <div style="position: absolute; top: 0; left: 0; right: 0; bottom: 0; background: linear-gradient(90deg, transparent 0%, rgba(255,255,255,0.2) 50%, transparent 100%); animation: shimmer 2.5s infinite;"></div>')
            lines.append(f'        </div>')
            lines.append(f'      </div>')
            lines.append(f'    </div>')

        lines.append(f'  </div>')

        # 경험치 데이터
        if experience_data:
            lines.append(f'  <div style="background: rgba(255,255,255,0.05); padding: 12px; border-radius: 8px; margin-bottom: 16px;">')
            lines.append(f'    <h4 style="margin: 0 0 8px 0; color: #e2e8f0;">✨ 획득 경험치</h4>')
            lines.append(f'    <table style="width: 100%; border-collapse: collapse;">')

            for key, value in experience_data.items():
                lines.append(f'      <tr>')
                lines.append(f'        <td style="padding: 6px 0; color: #cbd5e0;">{key}</td>')
                # Format numbers with commas, but keep strings as-is
                formatted_value = f'{value:,}' if isinstance(value, int) else value
                lines.append(f'        <td style="padding: 6px 0; text-align: right; font-weight: bold; color: #fbbf24;">{formatted_value}</td>')
                lines.append(f'      </tr>')

            lines.append(f'    </table>')
            lines.append(f'  </div>')

        lines.append('</div>')
        lines.append("")

        # 뱃지 표시 (HTML 뱃지 스타일)
        if badges:
            lines.append('<div style="margin: 16px 0;">')
            lines.append('  <h4 style="color: #2d3748; margin-bottom: 12px;">🎖️ 획득한 뱃지</h4>')
            lines.append('  <div style="display: flex; flex-wrap: wrap; gap: 8px;">')

            for badge in badges:
                lines.append(f'    <span style="display: inline-block; background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); color: white; padding: 6px 12px; border-radius: 16px; font-size: 0.9em; font-weight: 500; box-shadow: 0 2px 4px rgba(0,0,0,0.2);">{badge}</span>')

            lines.append('  </div>')
            lines.append('</div>')
            lines.append("")

        return lines


__all__ = ["CardRenderer"]
