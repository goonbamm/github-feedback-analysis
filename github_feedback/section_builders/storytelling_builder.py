"""Storytelling section builder for narrative-style reports."""

from __future__ import annotations

from typing import List

from github_feedback.models import MetricSnapshot

from .base_builder import SectionBuilder


class StorytellingBuilder(SectionBuilder):
    """Builder for narrative storytelling section."""

    def build(self) -> List[str]:
        """Build the storytelling section with RPG quest narrative."""
        lines = []

        lines.append("## 📖 개발자의 여정: RPG 퀘스트 로그")
        lines.append("")

        # Generate chapter-based narrative
        chapters = self._generate_quest_chapters()

        for i, chapter in enumerate(chapters, 1):
            lines.append(f"### Chapter {i}: {chapter['title']}")
            lines.append("")
            lines.append(chapter['content'])
            lines.append("")

        # Epic moments
        if self.metrics.highlights:
            lines.append("### 🌟 에픽 순간들")
            lines.append("")
            lines.append(self._render_epic_moments())
            lines.append("")

        # Character progression
        lines.append("### ⚔️ 캐릭터 성장 일지")
        lines.append("")
        lines.append(self._generate_character_progression())
        lines.append("")

        return lines

    def _generate_quest_chapters(self) -> List[dict]:
        """Generate quest-style narrative chapters."""
        chapters = []

        # Calculate some metrics
        total_activity = (
            self.metrics.stats.get('활동', {}).get('커밋', 0) +
            self.metrics.stats.get('활동', {}).get('Pull Requests', 0) +
            self.metrics.stats.get('활동', {}).get('리뷰', 0)
        )

        commits = self.metrics.stats.get('활동', {}).get('커밋', 0)
        prs = self.metrics.stats.get('활동', {}).get('Pull Requests', 0)
        reviews = self.metrics.stats.get('활동', {}).get('리뷰', 0)

        # Chapter 1: The Beginning
        chapters.append({
            'title': '모험의 시작',
            'content': f'''🗺️ **퀘스트 시작!**

이 기간 동안 당신은 총 **{total_activity:.0f}번의 행동**을 통해 코드베이스의 던전을 탐험했습니다.

{self._get_journey_description(commits, prs, reviews)}

> *"모든 위대한 여정은 첫 커밋에서 시작된다."*'''
        })

        # Chapter 2: The Challenge
        if self.metrics.awards:
            top_award = self.metrics.awards[0] if self.metrics.awards else "성장 씨앗 상"
            chapters.append({
                'title': '시련과 성장',
                'content': f'''⚔️ **보스 전투!**

수많은 버그와 이슈라는 몬스터들을 물리치며, 당신은 다음의 타이틀을 획득했습니다:

**{top_award}**

이는 당신의 헌신과 노력의 결과입니다. 각 커밋은 경험치가 되었고, 각 PR은 레벨업의 기회가 되었습니다.'''
            })

        # Chapter 3: Allies and Collaboration
        if reviews > 0 or prs > 0:
            chapters.append({
                'title': '동료들과의 협력',
                'content': f'''🤝 **파티 플레이!**

혼자서는 이룰 수 없는 것들이 있습니다. 당신은:
- **{prs:.0f}개의 Pull Request**로 팀원들과 아이디어를 공유했습니다
- **{reviews:.0f}번의 코드 리뷰**로 동료들의 성장을 도왔습니다

> *"함께 가면 더 멀리 갈 수 있다."*'''
            })

        # Chapter 4: The Legacy
        chapters.append({
            'title': '남겨진 유산',
            'content': f'''🏆 **레거시 구축!**

당신의 기여는 단순한 코드를 넘어섰습니다:

{self._get_legacy_description()}

이 모든 것이 다음 세대 개발자들을 위한 발판이 됩니다.

> *"우리는 코드를 작성하는 것이 아니라, 미래를 만들고 있다."*'''
        })

        return chapters

    def _get_journey_description(self, commits: float, prs: float, reviews: float) -> str:
        """Get description of the development journey."""
        if commits > 100:
            commit_desc = f"**{commits:.0f}번의 커밋**으로 코드의 숲을 개척하고"
        elif commits > 50:
            commit_desc = f"**{commits:.0f}번의 커밋**으로 꾸준히 전진하며"
        else:
            commit_desc = f"**{commits:.0f}번의 커밋**으로 한 걸음씩 나아가며"

        if prs > 50:
            pr_desc = f"**{prs:.0f}개의 Pull Request**로 협업의 다리를 놓았으며"
        elif prs > 20:
            pr_desc = f"**{prs:.0f}개의 Pull Request**로 팀과 소통했고"
        else:
            pr_desc = f"**{prs:.0f}개의 Pull Request**로 아이디어를 나눴습니다"

        return f"{commit_desc}, {pr_desc}."

    def _get_legacy_description(self) -> str:
        """Get description of the developer's legacy."""
        legacy_items = []

        # Check highlights
        if self.metrics.highlights:
            if len(self.metrics.highlights) >= 3:
                legacy_items.append("✨ 수많은 주목할 만한 성과")

        # Check awards
        if self.metrics.awards:
            if len(self.metrics.awards) >= 3:
                legacy_items.append("🏅 여러 개의 영예로운 업적")

        # Check consistency
        if self.metrics.monthly_insights:
            if self.metrics.monthly_insights.consistency_score >= 0.7:
                legacy_items.append("📊 일관된 기여 패턴")

        # Default items
        if not legacy_items:
            legacy_items = [
                "💪 꾸준한 노력과 헌신",
                "🌱 지속적인 성장 마인드",
                "🎯 명확한 목표 의식"
            ]

        return "\n".join(f"- {item}" for item in legacy_items)

    def _render_epic_moments(self) -> str:
        """Render epic moments from highlights."""
        if not self.metrics.highlights:
            return "Epic moments are being created every day..."

        lines = []
        lines.append('<div style="display: grid; gap: 12px; margin: 16px 0;">')

        for i, highlight in enumerate(self.metrics.highlights[:5], 1):
            gradient = self._get_epic_gradient(i)
            lines.append(
                f'''<div style="background: {gradient}; border-radius: 8px; padding: 16px; color: white; box-shadow: 0 4px 6px rgba(0,0,0,0.2);">
    <div style="display: flex; align-items: start; gap: 12px;">
        <div style="font-size: 28px;">⭐</div>
        <div>
            <div style="font-weight: 600; margin-bottom: 4px;">Epic Moment #{i}</div>
            <div style="opacity: 0.95; line-height: 1.5;">{highlight}</div>
        </div>
    </div>
</div>'''
            )

        lines.append('</div>')

        return "\n".join(lines)

    def _get_epic_gradient(self, index: int) -> str:
        """Get gradient for epic moment card."""
        gradients = [
            "linear-gradient(135deg, #667eea 0%, #764ba2 100%)",
            "linear-gradient(135deg, #f093fb 0%, #f5576c 100%)",
            "linear-gradient(135deg, #4facfe 0%, #00f2fe 100%)",
            "linear-gradient(135deg, #43e97b 0%, #38f9d7 100%)",
            "linear-gradient(135deg, #fa709a 0%, #fee140 100%)",
        ]
        return gradients[(index - 1) % len(gradients)]

    def _generate_character_progression(self) -> str:
        """Generate character progression narrative."""
        lines = []

        # Get character stats if available
        code_quality = self.metrics.stats.get('스탯', {}).get('코드 품질', 50)
        productivity = self.metrics.stats.get('스탯', {}).get('생산성', 50)
        collaboration = self.metrics.stats.get('스탯', {}).get('협업', 50)

        lines.append("당신의 개발자 캐릭터는 이번 여정을 통해:")
        lines.append("")

        if code_quality >= 70:
            lines.append("- ⚔️ **코드 품질** 스탯이 고급 단계에 도달했습니다!")
        elif code_quality >= 50:
            lines.append("- ⚔️ **코드 품질** 스탯이 중급 단계로 성장했습니다!")
        else:
            lines.append("- ⚔️ **코드 품질** 스탯을 수련 중입니다!")

        if productivity >= 70:
            lines.append("- 🏃 **생산성** 스탯이 달인 수준에 이르렀습니다!")
        elif productivity >= 50:
            lines.append("- 🏃 **생산성** 스탯이 숙련 단계로 향상되었습니다!")
        else:
            lines.append("- 🏃 **생산성** 스탯을 꾸준히 키워가고 있습니다!")

        if collaboration >= 70:
            lines.append("- 🤝 **협업** 스탯이 마스터 레벨입니다!")
        elif collaboration >= 50:
            lines.append("- 🤝 **협업** 스탯이 견습 단계를 넘어섰습니다!")
        else:
            lines.append("- 🤝 **협업** 스탯을 발전시켜가고 있습니다!")

        lines.append("")
        lines.append("🎮 **다음 레벨까지:** 계속해서 커밋하고, PR을 만들고, 리뷰를 남기세요!")

        return "\n".join(lines)
