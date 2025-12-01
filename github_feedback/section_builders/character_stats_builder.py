"""Character stats section builder."""

from typing import Dict, List

from ..game_elements import GameRenderer, LevelCalculator
from ..models import MetricSnapshot
from .base_builder import SectionBuilder


class CharacterStatsBuilder(SectionBuilder):
    """Builder for RPG-style character stats section."""

    def build(self) -> List[str]:
        """Build RPG-style character stats visualization.

        Returns:
            List of markdown lines for character stats section
        """
        lines: List[str] = []

        stats = self._calculate_repo_character_stats()
        avg_stat = sum(stats.values()) / len(stats) if stats else 0

        # 티어 시스템으로 등급 계산
        tier, title, rank_emoji = LevelCalculator.calculate_tier(avg_stat)

        # 특성 타이틀 결정
        specialty_title = LevelCalculator.get_specialty_title(stats)

        # 활동량 데이터
        total_commits = self.metrics.stats.get("commits", {}).get("total", 0)
        total_prs = self.metrics.stats.get("pull_requests", {}).get("total", 0)

        # 뱃지 생성
        badges = LevelCalculator.get_badges_from_stats(
            stats,
            total_commits=total_commits,
            total_prs=total_prs,
            total_repos=0  # 일반 보고서는 단일 저장소
        )

        # 저장소 특화 뱃지 추가
        if stats.get("growth", 0) >= 80:
            # "🚀 급성장 개발자"를 "🚀 급성장 저장소"로 교체
            badges = [b.replace("급성장 개발자", "급성장 저장소") for b in badges]

        # GameRenderer로 캐릭터 스탯 렌더링
        lines.append("## 🎮 저장소 캐릭터 스탯")
        lines.append("")
        lines.append("> 저장소의 활동을 RPG 캐릭터 스탯으로 시각화")
        lines.append("")

        character_lines = GameRenderer.render_character_stats(
            level=tier,
            title=title,
            rank_emoji=rank_emoji,
            specialty_title=specialty_title,
            stats=stats,
            experience_data={},  # 경험치 데이터 없음
            badges=badges,
            use_tier_system=True  # 티어 시스템 사용
        )

        lines.extend(character_lines)
        lines.append("---")
        lines.append("")
        return lines

    def _calculate_repo_character_stats(self) -> Dict[str, int]:
        """Calculate RPG-style character stats from repository metrics.

        Returns:
            Dictionary mapping stat names to values (0-100)
        """
        stats = self.metrics.stats

        # Extract key metrics with safe defaults
        commits = stats.get("commits", {})
        prs = stats.get("pull_requests", {})
        reviews = stats.get("reviews", {})

        total_commits = commits.get("total", 0)
        total_prs = prs.get("total", 0)
        total_reviews = reviews.get("total", 0)
        merged_prs = prs.get("merged", 0)

        # Code Quality (0-100): Based on PR merge rate, awards, and coding habits
        merge_rate = (merged_prs / total_prs) if total_prs > 0 else 0
        award_count = len(self.metrics.awards) if self.metrics.awards else 0

        # Calculate coding habits quality (commit messages + PR titles)
        coding_habits_score = 0
        if self.metrics.detailed_feedback:
            # Commit message quality
            if self.metrics.detailed_feedback.commit_feedback:
                cf = self.metrics.detailed_feedback.commit_feedback
                if cf.total_commits > 0:
                    commit_quality_ratio = cf.good_messages / cf.total_commits
                    coding_habits_score += commit_quality_ratio * 50  # 0-50 points

            # PR title quality
            if self.metrics.detailed_feedback.pr_title_feedback:
                pf = self.metrics.detailed_feedback.pr_title_feedback
                if pf.total_prs > 0:
                    pr_title_quality_ratio = pf.clear_titles / pf.total_prs
                    coding_habits_score += pr_title_quality_ratio * 50  # 0-50 points

            # Normalize to 0-20 range
            coding_habits_score = min(20, coding_habits_score / 5)

        code_quality = min(100, int(
            (merge_rate * 35) +  # Merge success rate (0-35)
            (min(award_count / 15, 1) * 25) +  # Award achievement (0-25)
            (20 if total_commits >= 100 else (total_commits / 100) * 20) +  # Experience (0-20)
            coding_habits_score  # Coding habits (0-20)
        ))

        # Collaboration (0-100): Based on reviews, PR engagement, and review tone
        collab_network = self.metrics.collaboration
        unique_collaborators = collab_network.unique_collaborators if collab_network else 0
        review_count = collab_network.review_received_count if collab_network else 0

        # Calculate review tone quality
        review_tone_score = 0
        if self.metrics.detailed_feedback and self.metrics.detailed_feedback.review_tone_feedback:
            rtf = self.metrics.detailed_feedback.review_tone_feedback
            total_tone_reviews = rtf.constructive_reviews + rtf.harsh_reviews + rtf.neutral_reviews
            if total_tone_reviews > 0:
                # Constructive reviews contribute positively, harsh reviews reduce score
                constructive_ratio = rtf.constructive_reviews / total_tone_reviews
                harsh_ratio = rtf.harsh_reviews / total_tone_reviews
                review_tone_score = (constructive_ratio - (harsh_ratio * 0.5)) * 20  # 0-20 points
                review_tone_score = max(0, min(20, review_tone_score))  # Clamp to 0-20

        collaboration = min(100, int(
            (min(total_reviews / 30, 1) * 35) +  # Review activity (0-35)
            (min(unique_collaborators / 15, 1) * 30) +  # Network size (0-30)
            (15 if review_count >= 50 else (review_count / 50) * 15) +  # Review received (0-15)
            review_tone_score  # Review tone quality (0-20)
        ))

        # Problem Solving (0-100): Based on PR diversity and tech stack
        tech_stack = self.metrics.tech_stack
        tech_diversity = tech_stack.diversity_score if tech_stack else 0
        language_count = len(tech_stack.top_languages) if tech_stack and tech_stack.top_languages else 0

        problem_solving = min(100, int(
            (min(total_prs / 25, 1) * 40) +  # PR production (0-40) - 기준 상향
            (tech_diversity * 35) +  # Technology breadth (0-35)
            (min(language_count / 7, 1) * 25)  # Language variety (0-25) - 기준 상향
        ))

        # Productivity (0-100): Based on total activity volume
        total_activity = total_commits + total_prs + total_reviews
        monthly_velocity = total_activity / self.metrics.months if self.metrics.months > 0 else 0

        productivity = min(100, int(
            (min(total_commits / 150, 1) * 35) +  # Commit volume (0-35) - 기준 상향
            (min(total_prs / 50, 1) * 35) +  # PR volume (0-35) - 기준 상향
            (min(monthly_velocity / 30, 1) * 30)  # Velocity (0-30) - 기준 상향
        ))

        # Growth (0-100): Based on highlights and retrospective insights
        highlight_count = len(self.metrics.highlights) if self.metrics.highlights else 0
        has_retrospective = self.metrics.retrospective is not None

        # Check for positive growth trends
        growth_indicators = 0
        if self.metrics.retrospective and hasattr(self.metrics.retrospective, 'time_comparisons'):
            positive_trends = sum(1 for tc in self.metrics.retrospective.time_comparisons
                                if tc.direction == "increasing")
            growth_indicators = min(positive_trends, 5)

        growth = min(100, int(
            30 +  # Base growth score - 기준 하향 (50->30)
            (min(highlight_count / 8, 1) * 25) +  # Highlights (0-25) - 기준 상향
            (15 if has_retrospective else 0) +  # Deep analysis bonus (0-15)
            (growth_indicators * 6)  # Positive trend bonus (0-30) - 보너스 증대
        ))

        return {
            "code_quality": code_quality,
            "collaboration": collaboration,
            "problem_solving": problem_solving,
            "productivity": productivity,
            "growth": growth,
        }
