"""Witch critique section builder."""

from typing import List

from ..models import MetricSnapshot
from .base_builder import SectionBuilder


class WitchCritiqueBuilder(SectionBuilder):
    """Builder for witch's critique section with dark theme."""

    def build(self) -> List[str]:
        """Build witch's critique section.

        Returns:
            List of markdown lines for witch critique section
        """
        # Always display the witch critique section, even if data is missing
        lines = ["## 🔮 마녀의 독설", ""]
        lines.append("> 수정 구슬이 보여주는 너의 약점들... 귀 기울여 들어봐.")
        lines.append("")

        # If witch_critique is missing or has no critiques, create a fallback
        if not self.metrics.witch_critique or not self.metrics.witch_critique.critiques:
            lines.append("_🔮 크리스탈 볼이 말하길... 너한테 할 말이 좀 있대._")
            lines.append("")

            # Create a fallback critique card
            lines.append(f'<div style="border-left: 4px solid #4b0082; background: linear-gradient(135deg, #1a002e 0%, #1a1a2e 100%); padding: 20px; margin: 20px 0; border-radius: 8px; box-shadow: 0 4px 6px rgba(0,0,0,0.3);">')
            lines.append(f'  <div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 12px;">')
            lines.append(f'    <h3 style="margin: 0; color: #e0e0e0; font-size: 1.2em;">개발자 성장</h3>')
            lines.append(f'    <span style="background: #4b0082; color: white; padding: 4px 12px; border-radius: 12px; font-size: 0.85em; font-weight: bold;">💫 조언</span>')
            lines.append(f'  </div>')
            lines.append(f'  <div style="color: #ff6b9d; font-size: 1.1em; font-weight: 500; margin-bottom: 16px; line-height: 1.6;">')
            lines.append(f'    💬 겉으로는 괜찮아 보이지만, 안주하면 퇴보하는 법이야. 지금이 딱 다음 레벨로 올라갈 때야.')
            lines.append(f'  </div>')
            lines.append(f'  <div style="background: rgba(0,0,0,0.3); padding: 12px; border-radius: 4px; margin-bottom: 12px;">')
            lines.append(f'    <div style="color: #9ca3af; font-size: 0.9em; margin-bottom: 4px;"><strong>📊 증거:</strong></div>')
            lines.append(f'    <div style="color: #d1d5db;">활동 패턴 분석 완료</div>')
            lines.append(f'  </div>')
            lines.append(f'  <div style="background: rgba(139,0,0,0.2); padding: 12px; border-radius: 4px; margin-bottom: 12px;">')
            lines.append(f'    <div style="color: #fca5a5; font-size: 0.9em; margin-bottom: 4px;"><strong>⚠️ 결과:</strong></div>')
            lines.append(f'    <div style="color: #fecaca;">현상 유지는 곧 뒤처지는 거야. 기술은 매일 발전하는데 너만 그 자리면?</div>')
            lines.append(f'  </div>')
            lines.append(f'  <div style="background: rgba(34,197,94,0.15); padding: 12px; border-radius: 4px;">')
            lines.append(f'    <div style="color: #86efac; font-size: 0.9em; margin-bottom: 4px;"><strong>💊 처방:</strong></div>')
            lines.append(f'    <div style="color: #bbf7d0;">새로운 기술 하나 배워봐. 오픈소스 기여하거나, 더 어려운 문제에 도전해봐.</div>')
            lines.append(f'  </div>')
            lines.append(f'</div>')
            lines.append("")

            lines.append(f'<div style="background: linear-gradient(135deg, #4a0e4e 0%, #1a1a2e 100%); padding: 16px; border-radius: 8px; border: 2px solid #9333ea; margin: 20px 0;">')
            lines.append(f'  <p style="color: #c084fc; font-style: italic; margin: 0; text-align: center; font-size: 1.05em;">')
            lines.append(f'    💫 마녀의 조언은 여기까지. 듣든 말든 너 맘이지만, 1년 후 더 나은 개발자가 되고 싶다면... 뭐, 알아서 해.')
            lines.append(f'  </p>')
            lines.append(f'</div>')
            lines.append("")
            lines.append("---")
            lines.append("")
            return lines

        # Opening curse
        lines.append(f"_{self.metrics.witch_critique.opening_curse}_")
        lines.append("")

        # Render each critique as a dark-themed card
        for i, critique in enumerate(self.metrics.witch_critique.critiques, 1):
            # Determine severity color
            severity_colors = {
                "🔥 치명적": ("#8b0000", "#2b0000"),  # Dark red
                "⚡ 심각": ("#b8860b", "#2b1d00"),     # Dark goldenrod
                "💀 위험": ("#4b0082", "#1a002e"),     # Dark purple
                "🕷️ 경고": ("#2f4f4f", "#0f1f1f"),     # Dark slate gray
            }
            border_color, bg_color = severity_colors.get(
                critique.severity,
                ("#4b0082", "#1a002e")  # Default to purple
            )

            # Create card with dark theme
            lines.append(f'<div style="border-left: 4px solid {border_color}; background: linear-gradient(135deg, {bg_color} 0%, #1a1a2e 100%); padding: 20px; margin: 20px 0; border-radius: 8px; box-shadow: 0 4px 6px rgba(0,0,0,0.3);">')

            # Header with category and severity
            lines.append(f'  <div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 12px;">')
            lines.append(f'    <h3 style="margin: 0; color: #e0e0e0; font-size: 1.2em;">{critique.category}</h3>')
            lines.append(f'    <span style="background: {border_color}; color: white; padding: 4px 12px; border-radius: 12px; font-size: 0.85em; font-weight: bold;">{critique.severity}</span>')
            lines.append(f'  </div>')

            # Critique (main message)
            lines.append(f'  <div style="color: #ff6b9d; font-size: 1.1em; font-weight: 500; margin-bottom: 16px; line-height: 1.6;">')
            lines.append(f'    💬 {critique.critique}')
            lines.append(f'  </div>')

            # Evidence
            lines.append(f'  <div style="background: rgba(0,0,0,0.3); padding: 12px; border-radius: 4px; margin-bottom: 12px;">')
            lines.append(f'    <div style="color: #9ca3af; font-size: 0.9em; margin-bottom: 4px;"><strong>📊 증거:</strong></div>')
            lines.append(f'    <div style="color: #d1d5db;">{critique.evidence}</div>')
            lines.append(f'  </div>')

            # Consequence
            lines.append(f'  <div style="background: rgba(139,0,0,0.2); padding: 12px; border-radius: 4px; margin-bottom: 12px;">')
            lines.append(f'    <div style="color: #fca5a5; font-size: 0.9em; margin-bottom: 4px;"><strong>⚠️ 결과:</strong></div>')
            lines.append(f'    <div style="color: #fecaca;">{critique.consequence}</div>')
            lines.append(f'  </div>')

            # Remedy
            lines.append(f'  <div style="background: rgba(34,197,94,0.15); padding: 12px; border-radius: 4px;">')
            lines.append(f'    <div style="color: #86efac; font-size: 0.9em; margin-bottom: 4px;"><strong>💊 처방:</strong></div>')
            lines.append(f'    <div style="color: #bbf7d0;">{critique.remedy}</div>')
            lines.append(f'  </div>')

            lines.append(f'</div>')
            lines.append("")

        # Closing prophecy
        lines.append(f'<div style="background: linear-gradient(135deg, #4a0e4e 0%, #1a1a2e 100%); padding: 16px; border-radius: 8px; border: 2px solid #9333ea; margin: 20px 0;">')
        lines.append(f'  <p style="color: #c084fc; font-style: italic; margin: 0; text-align: center; font-size: 1.05em;">')
        lines.append(f'    {self.metrics.witch_critique.closing_prophecy}')
        lines.append(f'  </p>')
        lines.append(f'</div>')
        lines.append("")

        lines.append("---")
        lines.append("")
        return lines
