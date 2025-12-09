"""Prediction section builder for future insights and challenges."""

from __future__ import annotations

from typing import List

from github_feedback.models import MetricSnapshot

from .base_builder import SectionBuilder


class PredictionBuilder(SectionBuilder):
    """Builder for predictions and challenges section."""

    def build(self) -> List[str]:
        """Build the predictions section."""
        if not self.metrics.predictions:
            return []

        predictions = self.metrics.predictions
        lines = []

        lines.append("## 🔮 미래 예측 & 도전 과제")
        lines.append("")

        # Motivational message
        if predictions.motivational_message:
            lines.append(f"### {predictions.motivational_message}")
            lines.append("")

        # Predictions
        if predictions.predictions:
            lines.append("### 📈 다음 달 예상 활동")
            lines.append("")
            lines.append("| 지표 | 현재 (월평균) | 예측값 | 신뢰도 | 근거 |")
            lines.append("|------|---------------|--------|--------|------|")

            for pred in predictions.predictions:
                confidence_icon = self._get_confidence_icon(pred.confidence)
                change = pred.predicted_value - pred.current_value
                change_str = f"{change:+.1f}"

                lines.append(
                    f"| {pred.metric} | {pred.current_value:.1f} | {pred.predicted_value:.1f} ({change_str}) | {confidence_icon} {pred.confidence} | {pred.reasoning} |"
                )

            lines.append("")

        # Suggested challenges
        if predictions.suggested_challenges:
            lines.append("### 🎯 개인 맞춤 도전 과제")
            lines.append("")

            lines.append('<div style="display: grid; gap: 12px; margin: 16px 0;">')

            for i, challenge in enumerate(predictions.suggested_challenges, 1):
                color = self._get_challenge_color(i)
                lines.append(self._render_challenge_card(challenge, color))

            lines.append('</div>')
            lines.append("")

        # Interactive goal tracker (placeholder for future enhancement)
        lines.append("### 📋 이번 달 목표")
        lines.append("")
        lines.append("> 💡 **팁:** 작은 목표부터 시작하세요! 꾸준함이 가장 중요합니다.")
        lines.append("")

        return lines

    def _get_confidence_icon(self, confidence: str) -> str:
        """Get icon for confidence level."""
        if confidence.lower() == "high":
            return "🟢"
        elif confidence.lower() == "medium":
            return "🟡"
        else:
            return "🟠"

    def _get_challenge_color(self, index: int) -> str:
        """Get gradient color for challenge card."""
        colors = [
            "linear-gradient(135deg, #667eea 0%, #764ba2 100%)",
            "linear-gradient(135deg, #f093fb 0%, #f5576c 100%)",
            "linear-gradient(135deg, #4facfe 0%, #00f2fe 100%)",
            "linear-gradient(135deg, #43e97b 0%, #38f9d7 100%)",
            "linear-gradient(135deg, #fa709a 0%, #fee140 100%)",
        ]
        return colors[(index - 1) % len(colors)]

    def _render_challenge_card(self, challenge: str, gradient: str) -> str:
        """Render a challenge card."""
        return f'''<div style="background: {gradient}; border-radius: 8px; padding: 16px; color: white; box-shadow: 0 2px 4px rgba(0,0,0,0.1);">
    <div style="display: flex; align-items: center; gap: 12px;">
        <div style="font-size: 24px;">🎯</div>
        <div style="flex: 1; font-size: 14px; font-weight: 500; line-height: 1.5;">{challenge}</div>
    </div>
</div>'''
