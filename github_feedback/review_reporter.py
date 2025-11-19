"""Aggregate pull request reviews into an integrated annual report."""
from __future__ import annotations

import html
import json
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Iterable, List

import re

from .console import Console
from .constants import (
    STAT_WEIGHTS_CODE_QUALITY,
    STAT_WEIGHTS_COLLABORATION,
    STAT_WEIGHTS_GROWTH,
    STAT_WEIGHTS_PROBLEM_SOLVING,
    STAT_WEIGHTS_PRODUCTIVITY,
)
from .game_elements import GameRenderer, LevelCalculator
from .llm import LLMClient
from .models import (
    ActionPlanItem,
    BenchmarkItem,
    GrowthIndicator,
    ImprovementArea,
    PersonalDevelopmentAnalysis,
    ProgressMetric,
    ReviewPoint,
    StrengthPoint,
    TLDRSummary,
)
from .prompts import (
    get_personal_development_system_prompt,
    get_personal_development_user_prompt,
    get_team_report_system_prompt,
    get_team_report_user_prompt,
)
from .utils import pad_to_width

PR_NUMBER_PATTERN = re.compile(r"PR #(\d+)")

console = Console()


@dataclass(slots=True)
class StoredReview:
    """Stored review summary reconstructed from cached artefacts."""

    number: int
    title: str
    author: str
    html_url: str
    created_at: datetime
    overview: str
    strengths: List[ReviewPoint]
    improvements: List[ReviewPoint]
    body: str = ""
    review_bodies: List[str] | None = None
    review_comments: List[str] | None = None
    additions: int = 0
    deletions: int = 0
    changed_files: int = 0


class ReviewReporter:
    """Build integrated Korean reports from individual pull request reviews."""

    def __init__(self, *, output_dir: Path = Path("reports/reviews"), llm: LLMClient | None = None) -> None:
        self.output_dir = output_dir
        self.llm = llm

    # ------------------------------------------------------------------
    # Internal helpers
    # ------------------------------------------------------------------

    def _repo_dir(self, repo: str) -> Path:
        safe_repo = repo.replace("/", "__")
        return self.output_dir / safe_repo

    @staticmethod
    def _load_points(raw_points: Iterable[dict]) -> List[ReviewPoint]:
        points: List[ReviewPoint] = []
        for payload in raw_points:
            if not isinstance(payload, dict):
                continue
            message = str(payload.get("message") or "").strip()
            if not message:
                continue
            example_raw = payload.get("example")
            example = str(example_raw).strip() if example_raw else None
            points.append(ReviewPoint(message=message, example=example))
        return points

    def _load_reviews(self, repo: str) -> List[StoredReview]:
        repo_dir = self._repo_dir(repo)
        if not repo_dir.exists():
            return []

        reviews: List[StoredReview] = []
        for pr_dir in sorted(repo_dir.glob("pr-*")):
            summary_data = self._load_json_payload(pr_dir / "review_summary.json")
            artefact_data = self._load_json_payload(pr_dir / "artefacts.json")
            if not summary_data or not artefact_data:
                continue

            stored_review = self._build_stored_review(summary_data, artefact_data, pr_dir)
            if stored_review:
                reviews.append(stored_review)

        reviews.sort(key=lambda item: (item.created_at, item.number))
        return reviews

    def _load_json_payload(self, path: Path) -> dict | None:
        if not path.exists():
            return None

        try:
            text = path.read_text(encoding="utf-8").strip()
        except OSError:
            console.log("Skipping unreadable artefact", str(path))
            return None

        if not text:
            console.log("Skipping empty review artefact", str(path.parent))
            return None

        try:
            payload = json.loads(text)
        except json.JSONDecodeError:
            console.log("Skipping invalid review artefact", str(path.parent))
            return None

        if not isinstance(payload, dict):
            console.log("Skipping unexpected review artefact", str(path.parent))
            return None

        return payload

    def _build_stored_review(
        self, summary_data: dict, artefact_data: dict, pr_dir: Path
    ) -> StoredReview | None:
        try:
            number = int(artefact_data.get("number"))
            title = str(artefact_data.get("title") or "").strip()
            author = str(artefact_data.get("author") or "unknown").strip()
            html_url = str(artefact_data.get("html_url") or "").strip()
            created_at_raw = artefact_data.get("created_at")
            created_at = (
                datetime.fromisoformat(created_at_raw)
                if isinstance(created_at_raw, str)
                else datetime.now(timezone.utc)
            )
        except Exception:  # pragma: no cover - defensive parsing guard
            console.log("Skipping malformed artefact", str(pr_dir))
            return None

        overview = str(summary_data.get("overview") or "").strip()
        strengths = self._load_points(summary_data.get("strengths", []))
        improvements = self._load_points(summary_data.get("improvements", []))

        body = str(artefact_data.get("body") or "").strip()
        review_bodies = artefact_data.get("review_bodies", [])
        review_comments = artefact_data.get("review_comments", [])
        additions = int(artefact_data.get("additions", 0))
        deletions = int(artefact_data.get("deletions", 0))
        changed_files = int(artefact_data.get("changed_files", 0))

        return StoredReview(
            number=number,
            title=title,
            author=author,
            html_url=html_url,
            created_at=created_at,
            overview=overview,
            strengths=strengths,
            improvements=improvements,
            body=body,
            review_bodies=review_bodies if isinstance(review_bodies, list) else [],
            review_comments=review_comments if isinstance(review_comments, list) else [],
            additions=additions,
            deletions=deletions,
            changed_files=changed_files,
        )

    def _build_prompt_context(self, repo: str, reviews: List[StoredReview]) -> str:
        lines: List[str] = []
        lines.append(f"Repository: {repo}")
        lines.append(f"총 리뷰 PR 수: {len(reviews)}")
        lines.append("")
        lines.append("Pull Request 요약:")
        for review in reviews:
            # Include code change metrics for better analysis
            code_metrics = f"+{review.additions}/-{review.deletions}, {review.changed_files}개 파일 변경"
            lines.append(
                f"- PR #{review.number} {review.title} (작성자: {review.author}, 생성일: {review.created_at.date()}, 코드 변경: {code_metrics})"
            )
            if review.html_url:
                lines.append(f"  URL: {review.html_url}")

            # Include PR body for analyzing description quality
            # Increased from 600 to 1000 chars for richer context
            if review.body:
                body_preview = review.body[:1000] + "..." if len(review.body) > 1000 else review.body
                lines.append(f"  PR 설명: {body_preview}")

            if review.overview:
                lines.append(f"  Overview: {review.overview}")

            # Include review comments for tone analysis
            # Increased from 10 to 15 comments and from 300 to 500 chars for better analysis
            if review.review_comments:
                lines.append(f"  리뷰 코멘트 ({len(review.review_comments)}개):")
                for idx, comment in enumerate(review.review_comments[:15], 1):  # Show first 15 comments
                    comment_preview = comment[:500] + "..." if len(comment) > 500 else comment
                    lines.append(f"    {idx}. {comment_preview}")
                if len(review.review_comments) > 15:
                    lines.append(f"    ... 외 {len(review.review_comments) - 15}개 코멘트")

            if review.strengths:
                lines.append("  Strengths:")
                for point in review.strengths:
                    lines.append(f"    • {point.message}")
                    if point.example:
                        lines.append(f"      예시: {point.example}")
            if review.improvements:
                lines.append("  Improvements:")
                for point in review.improvements:
                    lines.append(f"    • {point.message}")
                    if point.example:
                        lines.append(f"      예시: {point.example}")
            lines.append("")

        return "\n".join(lines).strip()

    def _analyze_personal_development(
        self, repo: str, reviews: List[StoredReview]
    ) -> PersonalDevelopmentAnalysis:
        """Analyze personal development based on PR reviews using LLM."""
        if not self.llm or not reviews:
            return self._fallback_personal_development(reviews)

        try:
            messages = self._build_personal_development_messages(repo, reviews)
            import json as json_module

            # Increased temperature from 0.4 to 0.6 for better response quality
            # Increased max_retries to 5 for more robust analysis
            content = self.llm.complete(messages, temperature=0.6, max_retries=5)
            data = json_module.loads(content)
            return self._build_personal_development_analysis(data)
        except Exception as exc:  # pragma: no cover
            console.log("LLM 개인 발전 분석 실패", str(exc))
            return self._fallback_personal_development(reviews)

    def _split_reviews_for_growth(self, reviews: List[StoredReview]) -> tuple[List[StoredReview], List[StoredReview]]:
        """Split reviews into early and recent lists for growth analysis."""
        midpoint = len(reviews) // 2
        if midpoint <= 0:
            return [], reviews
        return reviews[:midpoint], reviews[midpoint:]

    def _build_personal_development_messages(
        self, repo: str, reviews: List[StoredReview]
    ) -> List[dict]:
        """Create LLM messages used for the personal development prompt."""
        context = self._build_prompt_context(repo, reviews)
        early_reviews, recent_reviews = self._split_reviews_for_growth(reviews)

        return [
            {
                "role": "system",
                "content": get_personal_development_system_prompt(),
            },
            {
                "role": "user",
                "content": get_personal_development_user_prompt(
                    context, len(early_reviews), len(recent_reviews)
                ),
            },
        ]

    def _build_personal_development_analysis(self, data: dict) -> PersonalDevelopmentAnalysis:
        """Convert parsed LLM response into domain objects."""
        if not isinstance(data, dict):  # pragma: no cover - defensive guard
            raise ValueError("LLM response must be a JSON object")

        return PersonalDevelopmentAnalysis(
            strengths=self._parse_strength_points(data.get("strengths", [])),
            improvement_areas=self._parse_improvement_areas(
                data.get("improvement_areas", [])
            ),
            growth_indicators=self._parse_growth_indicators(
                data.get("growth_indicators", [])
            ),
            tldr_summary=self._parse_tldr_summary(data.get("tldr_summary")),
        )

    def _parse_tldr_summary(self, payload: object) -> TLDRSummary | None:
        if not isinstance(payload, dict):
            return None
        return TLDRSummary(
            top_strength=str(payload.get("top_strength", "")),
            primary_focus=str(payload.get("primary_focus", "")),
            measurable_goal=str(payload.get("measurable_goal", "")),
        )

    def _parse_strength_points(self, payload: object) -> List[StrengthPoint]:
        points: List[StrengthPoint] = []
        if not isinstance(payload, list):
            return points
        for item in payload:
            if not isinstance(item, dict):
                continue
            points.append(
                StrengthPoint(
                    category=str(item.get("category", "기타")),
                    description=str(item.get("description", "")),
                    evidence=list(item.get("evidence", [])),
                    impact=str(item.get("impact", "medium")),
                )
            )
        return points

    def _parse_improvement_areas(self, payload: object) -> List[ImprovementArea]:
        areas: List[ImprovementArea] = []
        if not isinstance(payload, list):
            return areas
        for item in payload:
            if not isinstance(item, dict):
                continue
            areas.append(
                ImprovementArea(
                    category=str(item.get("category", "기타")),
                    description=str(item.get("description", "")),
                    evidence=list(item.get("evidence", [])),
                    suggestions=list(item.get("suggestions", [])),
                    priority=str(item.get("priority", "medium")),
                )
            )
        return areas

    def _parse_growth_indicators(self, payload: object) -> List[GrowthIndicator]:
        indicators: List[GrowthIndicator] = []
        if not isinstance(payload, list):
            return indicators
        for item in payload:
            if not isinstance(item, dict):
                continue
            indicators.append(
                GrowthIndicator(
                    aspect=str(item.get("aspect", "")),
                    description=str(item.get("description", "")),
                    before_examples=list(item.get("before_examples", [])),
                    after_examples=list(item.get("after_examples", [])),
                    progress_summary=str(item.get("progress_summary", "")),
                )
            )
        return indicators

    def _fallback_personal_development(
        self, reviews: List[StoredReview]
    ) -> PersonalDevelopmentAnalysis:
        """Provide basic personal development analysis without LLM."""
        # Collect all strengths and improvements from reviews
        all_strengths: List[tuple[StoredReview, ReviewPoint]] = []
        all_improvements: List[tuple[StoredReview, ReviewPoint]] = []

        for review in reviews:
            all_strengths.extend((review, point) for point in review.strengths)
            all_improvements.extend((review, point) for point in review.improvements)

        # Create basic strength points
        strengths = []
        for review, point in all_strengths[:5]:
            strengths.append(
                StrengthPoint(
                    category="코드 품질",
                    description=point.message,
                    evidence=[f"PR #{review.number}: {point.example or review.title}"],
                    impact="medium",
                )
            )

        # Create basic improvement areas
        improvement_areas = []
        for review, point in all_improvements[:5]:
            improvement_areas.append(
                ImprovementArea(
                    category="개선 영역",
                    description=point.message,
                    evidence=[f"PR #{review.number}: {point.example or review.title}"],
                    suggestions=["코드 리뷰 피드백을 참고하여 개선"],
                    priority="medium",
                )
            )

        # Basic growth analysis
        growth_indicators = []
        if len(reviews) >= 2:
            growth_indicators.append(
                GrowthIndicator(
                    aspect="지속적인 기여",
                    description=f"총 {len(reviews)}개의 PR을 통해 꾸준히 기여하고 있습니다.",
                    before_examples=[f"PR #{reviews[0].number}: {reviews[0].title}"],
                    after_examples=[f"PR #{reviews[-1].number}: {reviews[-1].title}"],
                    progress_summary="지속적으로 PR을 작성하며 프로젝트에 기여하고 있습니다.",
                )
            )

        return PersonalDevelopmentAnalysis(
            strengths=strengths,
            improvement_areas=improvement_areas,
            growth_indicators=growth_indicators,
            overall_assessment=f"총 {len(reviews)}개의 PR을 통해 프로젝트에 기여하고 있습니다.",
            key_achievements=[f"{len(reviews)}개의 PR 작성 및 리뷰 완료"],
            next_focus_areas=["코드 품질 향상", "테스트 커버리지 개선"],
        )

    # ------------------------------------------------------------------
    # Reporting
    # ------------------------------------------------------------------

    def _render_tldr_section(self, analysis: PersonalDevelopmentAnalysis) -> List[str]:
        """Render 30-second summary section."""
        lines: List[str] = []
        if not analysis.tldr_summary:
            return lines

        lines.append("## ⚡ 30초 요약 (TL;DR)")
        lines.append("")
        lines.append(f"- ✅ **가장 잘하고 있는 것**: {analysis.tldr_summary.top_strength}")
        lines.append(f"- 🎯 **이번 달 집중할 것**: {analysis.tldr_summary.primary_focus}")
        lines.append(f"- 📈 **측정 목표**: {analysis.tldr_summary.measurable_goal}")
        lines.append("")
        return lines

    def _calculate_character_stats(self, reviews: List[StoredReview]) -> dict:
        """Calculate RPG-style character stats from PR reviews."""
        if not reviews:
            return {
                "code_quality": 0,
                "collaboration": 0,
                "problem_solving": 0,
                "productivity": 0,
                "growth": 0,
            }

        total_prs = len(reviews)
        total_additions = sum(r.additions for r in reviews)
        total_deletions = sum(r.deletions for r in reviews)
        total_files = sum(r.changed_files for r in reviews)
        total_strengths = sum(len(r.strengths) for r in reviews)
        total_improvements = sum(len(r.improvements) for r in reviews)

        # Code Quality (0-100): Based on strength ratio and file organization
        avg_files_per_pr = total_files / total_prs if total_prs > 0 else 0
        strength_ratio = total_strengths / max(total_strengths + total_improvements, 1)

        w_cq = STAT_WEIGHTS_CODE_QUALITY
        code_quality = min(100, int(
            (strength_ratio * w_cq['strength_contribution']) +
            (min(avg_files_per_pr / w_cq['optimal_files_per_pr'], 1) * w_cq['file_organization']) +
            (w_cq['experience_bonus'] if total_prs >= w_cq['experience_pr_threshold']
             else (total_prs / w_cq['experience_pr_threshold']) * w_cq['experience_bonus'])
        ))

        # Collaboration (0-100): Based on review engagement
        has_reviews = sum(1 for r in reviews if r.review_bodies or r.review_comments)
        collaboration_rate = has_reviews / total_prs if total_prs > 0 else 0
        avg_feedback = (total_strengths + total_improvements) / total_prs if total_prs > 0 else 0

        w_col = STAT_WEIGHTS_COLLABORATION
        collaboration = min(100, int(
            (collaboration_rate * w_col['review_engagement']) +
            (min(avg_feedback / w_col['optimal_feedback_per_pr'], 1) * w_col['feedback_quality']) +
            (w_col['participation_bonus'] if total_prs >= w_col['participation_pr_threshold']
             else (total_prs / w_col['participation_pr_threshold']) * w_col['participation_bonus'])
        ))

        # Problem Solving (0-100): Based on PR complexity and scope
        avg_changes = (total_additions + total_deletions) / total_prs if total_prs > 0 else 0

        w_ps = STAT_WEIGHTS_PROBLEM_SOLVING
        problem_solving = min(100, int(
            (min(avg_changes / w_ps['optimal_changes_per_pr'], 1) * w_ps['change_complexity']) +
            (min(avg_files_per_pr / w_ps['optimal_files_per_pr'], 1) * w_ps['scope_breadth']) +
            (w_ps['problem_count'] if total_prs >= w_ps['problem_pr_threshold']
             else (total_prs / w_ps['problem_pr_threshold']) * w_ps['problem_count'])
        ))

        # Productivity (0-100): Based on output volume
        w_prod = STAT_WEIGHTS_PRODUCTIVITY
        productivity = min(100, int(
            (min(total_prs / w_prod['optimal_pr_count'], 1) * w_prod['pr_count']) +
            (min(total_additions / w_prod['optimal_additions'], 1) * w_prod['code_output']) +
            (min(total_files / w_prod['optimal_file_count'], 1) * w_prod['file_coverage'])
        ))

        # Growth (0-100): Based on consistent improvement
        # Calculate trend from first half vs second half
        w_growth = STAT_WEIGHTS_GROWTH
        if total_prs >= w_growth['min_prs_for_trend']:
            mid_point = total_prs // 2
            first_half = reviews[:mid_point]
            second_half = reviews[mid_point:]

            first_avg_strengths = sum(len(r.strengths) for r in first_half) / len(first_half)
            second_avg_strengths = sum(len(r.strengths) for r in second_half) / len(second_half)

            improvement_rate = (second_avg_strengths - first_avg_strengths) / max(first_avg_strengths, 1)
            growth = min(100, max(0, int(
                w_growth['base_growth'] +
                (improvement_rate * w_growth['improvement_trend']) +
                (w_growth['consistency_bonus'] if total_prs >= w_growth['consistency_pr_threshold']
                 else (total_prs / w_growth['consistency_pr_threshold']) * w_growth['consistency_bonus'])
            )))
        else:
            # Base growth for new developers
            growth = min(100, int(
                (total_prs / w_growth['min_prs_for_trend']) * w_growth['new_developer_multiplier'] +
                w_growth['new_developer_base']
            ))

        return {
            "code_quality": code_quality,
            "collaboration": collaboration,
            "problem_solving": problem_solving,
            "productivity": productivity,
            "growth": growth,
        }


    def _render_character_stats(self, reviews: List[StoredReview]) -> List[str]:
        """Render RPG-style character stats visualization (티어 시스템 사용)."""
        lines: List[str] = []

        stats = self._calculate_character_stats(reviews)
        avg_stat = sum(stats.values()) / len(stats) if stats else 0

        # 티어 시스템으로 등급 계산
        tier, title, rank_emoji = LevelCalculator.calculate_tier(avg_stat)

        # 특성 타이틀 결정
        specialty_title = LevelCalculator.get_specialty_title(stats)

        # 뱃지 생성
        total_prs = len(reviews)
        badges = LevelCalculator.get_badges_from_stats(
            stats,
            total_commits=0,  # PR 보고서에는 커밋 수 없음
            total_prs=total_prs,
            total_repos=0  # PR 보고서에는 저장소 수 없음
        )

        # PR 기반 뱃지 추가
        if total_prs >= 50:
            badges.append("💯 PR 마라토너")
        elif total_prs >= 20:
            badges.append("📝 활발한 기여자")

        # GameRenderer로 캐릭터 스탯 렌더링 (티어 시스템 사용)
        lines.append("## 🎮 개발자 캐릭터 스탯")
        lines.append("")

        # 경험치 데이터 없이 렌더링 (PR 보고서는 경험치 섹션 불필요)
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
        return lines

    def _render_skill_tree_section(
        self, analysis: PersonalDevelopmentAnalysis, pr_map: dict[int, StoredReview]
    ) -> List[str]:
        """Render skill tree section with consolidated table."""
        lines: List[str] = []
        lines.append("## 🎮 스킬 트리")
        lines.append("")
        lines.append("> 획득한 스킬과 습득 가능한 스킬을 확인하세요")
        lines.append("")

        # Collect all skills
        acquired_skills = []
        growing_skills = []
        available_skills = []

        # 1. Acquired Skills (from strengths)
        if analysis.strengths:
            for strength in analysis.strengths[:5]:  # Top 5 strengths
                # Calculate mastery based on impact
                mastery = {"high": 90, "medium": 75, "low": 60}.get(strength.impact, 70)

                # Determine skill type based on category
                skill_type = "패시브" if "품질" in strength.category or "코드" in strength.category else "액티브"

                # Get skill emoji based on category
                category_emojis = {
                    "코드 품질": "💻",
                    "협업": "🤝",
                    "문서화": "📝",
                    "테스트": "🧪",
                    "설계": "🏗️",
                }
                skill_emoji = next((emoji for key, emoji in category_emojis.items() if key in strength.category), "💎")

                acquired_skills.append({
                    "name": strength.category,
                    "type": skill_type,
                    "mastery": mastery,
                    "effect": strength.description,
                    "evidence": strength.evidence[:5],
                    "emoji": skill_emoji
                })

        # 2. Growing Skills (from growth indicators)
        if analysis.growth_indicators:
            for growth in analysis.growth_indicators[:3]:  # Top 3 growth areas
                # 성장 증거 준비
                growth_evidence = []
                if growth.progress_summary:
                    growth_evidence.append(growth.progress_summary)
                if growth.before_examples:
                    growth_evidence.append(f"Before: {growth.before_examples[0]}")
                if growth.after_examples:
                    growth_evidence.append(f"After: {growth.after_examples[0]}")

                growing_skills.append({
                    "name": growth.aspect,
                    "type": "성장중",
                    "mastery": 65,  # Growing skills are around 65%
                    "effect": growth.description,
                    "evidence": growth_evidence[:5],
                    "emoji": "🌱"
                })

        # 3. Available Skills (from improvement areas)
        if analysis.improvement_areas:
            # Sort by priority
            priority_order = {"critical": 0, "important": 1, "nice-to-have": 2}
            sorted_improvements = sorted(
                analysis.improvement_areas[:3],  # Top 3
                key=lambda area: priority_order.get(area.priority, 1),
            )

            for area in sorted_improvements:
                # Calculate mastery based on priority (lower for more critical)
                mastery = {"critical": 30, "important": 40, "nice-to-have": 50}.get(area.priority, 40)

                # Get skill emoji based on category
                category_emojis = {
                    "코드 품질": "💻",
                    "커밋": "📝",
                    "PR": "🔀",
                    "리뷰": "👀",
                    "테스트": "🧪",
                }
                skill_emoji = next((emoji for key, emoji in category_emojis.items() if key in area.category), "🎯")

                # 개선 제안 또는 증거 준비
                improvement_evidence = []
                if area.suggestions:
                    improvement_evidence.extend(area.suggestions[:5])
                elif area.evidence:
                    improvement_evidence.extend(area.evidence[:5])

                available_skills.append({
                    "name": area.category,
                    "type": "미습득",
                    "mastery": mastery,
                    "effect": area.description,
                    "evidence": improvement_evidence,
                    "emoji": skill_emoji
                })

        # Render all skills in one consolidated table
        lines.extend(GameRenderer.render_skill_tree_table(
            acquired_skills=acquired_skills,
            growing_skills=growing_skills,
            available_skills=available_skills
        ))

        lines.append("---")
        lines.append("")
        return lines

    def _render_personal_development(
        self, analysis: PersonalDevelopmentAnalysis, reviews: List[StoredReview]
    ) -> List[str]:
        """Render personal development analysis section with simplified structure."""
        lines: List[str] = []
        lines.append("## 👤 개인 피드백 리포트")
        lines.append("")

        # 1. TLDR section (30초 요약)
        lines.extend(self._render_tldr_section(analysis))
        lines.append("---")
        lines.append("")

        pr_map = {review.number: review for review in reviews}

        # 2. Skill Tree (스킬 트리로 모든 정보 통합)
        lines.extend(self._render_skill_tree_section(analysis, pr_map))

        return lines

    def _render_new_strengths_section(
        self, analysis: PersonalDevelopmentAnalysis, pr_map: dict[int, StoredReview]
    ) -> List[str]:
        """Render strengths in a clear, readable format."""
        lines: List[str] = []
        lines.append("## ✅ 잘하고 있는 것")
        lines.append("")

        if not analysis.strengths:
            lines.append("_분석된 강점이 없습니다._")
            lines.append("")
            return lines

        for idx, strength in enumerate(analysis.strengths, 1):
            # Title with impact indicator
            impact_emoji = {"high": "🔥", "medium": "⭐", "low": "💫"}.get(strength.impact, "⭐")
            lines.append(f"### {idx}. {strength.category} {impact_emoji}")
            lines.append("")

            # Description
            lines.append(f"**무엇이 좋은가**: {strength.description}")
            lines.append("")

            # Evidence with PR links
            if strength.evidence:
                lines.append("**구체적 근거**:")
                for evidence in strength.evidence:
                    # Try to extract PR numbers and add links
                    pr_num = self._extract_pr_number(evidence)
                    if pr_num and pr_num in pr_map:
                        review = pr_map[pr_num]
                        lines.append(f"- {evidence} ([보기]({review.html_url}))")
                    else:
                        lines.append(f"- {evidence}")
                lines.append("")

        return lines

    def _render_new_improvements_section(
        self, analysis: PersonalDevelopmentAnalysis, pr_map: dict[int, StoredReview]
    ) -> List[str]:
        """Render improvements in a clear, actionable format."""
        lines: List[str] = []
        lines.append("## 🔧 보완하면 좋을 것")
        lines.append("")

        if not analysis.improvement_areas:
            lines.append("_분석된 개선점이 없습니다._")
            lines.append("")
            return lines

        # Sort by priority
        priority_order = {"critical": 0, "important": 1, "nice-to-have": 2}
        sorted_improvements = sorted(
            analysis.improvement_areas,
            key=lambda area: priority_order.get(area.priority, 1),
        )

        for idx, area in enumerate(sorted_improvements, 1):
            # Title with priority indicator
            priority_emoji = {
                "critical": "🚨",
                "important": "⚠️",
                "nice-to-have": "💭",
            }.get(area.priority, "⚠️")
            lines.append(f"### {idx}. {area.category} {priority_emoji}")
            lines.append("")

            # Description
            lines.append(f"**현재 상황**: {area.description}")
            lines.append("")

            # Evidence with PR links
            if area.evidence:
                lines.append("**구체적 예시**:")
                for evidence in area.evidence:
                    pr_num = self._extract_pr_number(evidence)
                    if pr_num and pr_num in pr_map:
                        review = pr_map[pr_num]
                        lines.append(f"- {evidence} ([보기]({review.html_url}))")
                    else:
                        lines.append(f"- {evidence}")
                lines.append("")

            # Suggestions
            if area.suggestions:
                lines.append("**개선 제안**:")
                for suggestion in area.suggestions:
                    lines.append(f"- {suggestion}")
                lines.append("")

        return lines

    def _render_new_growth_section(
        self, analysis: PersonalDevelopmentAnalysis, pr_map: dict[int, StoredReview]
    ) -> List[str]:
        """Render growth indicators in a before/after format."""
        lines: List[str] = []
        lines.append("## 📈 성장한 점")
        lines.append("")

        if not analysis.growth_indicators:
            return lines

        for idx, growth in enumerate(analysis.growth_indicators, 1):
            lines.append(f"### {idx}. {growth.aspect}")
            lines.append("")
            lines.append(f"{growth.description}")
            lines.append("")

            # Before examples
            if growth.before_examples:
                lines.append("**Before (초기)**:")
                for example in growth.before_examples:
                    pr_num = self._extract_pr_number(example)
                    if pr_num and pr_num in pr_map:
                        review = pr_map[pr_num]
                        lines.append(f"- {example} ([보기]({review.html_url}))")
                    else:
                        lines.append(f"- {example}")
                lines.append("")

            # After examples
            if growth.after_examples:
                lines.append("**After (최근)**:")
                for example in growth.after_examples:
                    pr_num = self._extract_pr_number(example)
                    if pr_num and pr_num in pr_map:
                        review = pr_map[pr_num]
                        lines.append(f"- {example} ([보기]({review.html_url}))")
                    else:
                        lines.append(f"- {example}")
                lines.append("")

            # Progress summary
            if growth.progress_summary:
                lines.append(f"**성장 요약**: {growth.progress_summary}")
                lines.append("")

        return lines

    @staticmethod
    def _append_section_separator(lines: List[str]) -> None:
        lines.append("---")
        lines.append("")

    @staticmethod
    def _extract_pr_number(evidence: str) -> int | None:
        match = PR_NUMBER_PATTERN.search(evidence)
        return int(match.group(1)) if match else None

    @staticmethod
    def _build_links(evidences: Iterable[str] | None, pr_map: dict[int, StoredReview]) -> str:
        links: List[str] = []
        if not evidences:
            return "-"

        for evidence in evidences:
            pr_num = ReviewReporter._extract_pr_number(evidence)
            if pr_num is None:
                continue
            review = pr_map.get(pr_num)
            if review and review.html_url:
                links.append(f"[PR #{pr_num}]({review.html_url})")

        return "<br>".join(links) if links else "-"

    def _render_statistics_dashboard(self, reviews: List[StoredReview]) -> List[str]:
        """Render key metrics dashboard with HTML visual cards."""
        lines: List[str] = []

        # Calculate statistics
        total_prs = len(reviews)
        total_additions = sum(r.additions for r in reviews)
        total_deletions = sum(r.deletions for r in reviews)
        total_files_changed = sum(r.changed_files for r in reviews)
        avg_additions = total_additions // total_prs if total_prs > 0 else 0
        avg_deletions = total_deletions // total_prs if total_prs > 0 else 0

        # Count authors
        unique_authors = len(set(r.author for r in reviews))

        lines.append("## 📊 핵심 지표 대시보드")
        lines.append("")

        # Build metrics cards
        metrics_data = [
            {
                "title": "총 PR 수",
                "value": f"{total_prs}개",
                "emoji": "📝",
                "color": "#667eea"
            },
            {
                "title": "참여 인원",
                "value": f"{unique_authors}명",
                "emoji": "👥",
                "color": "#764ba2"
            },
            {
                "title": "총 코드 추가",
                "value": f"+{total_additions:,}줄",
                "emoji": "➕",
                "color": "#10b981"
            },
            {
                "title": "총 코드 삭제",
                "value": f"-{total_deletions:,}줄",
                "emoji": "➖",
                "color": "#ef4444"
            },
            {
                "title": "변경된 파일",
                "value": f"{total_files_changed:,}개",
                "emoji": "📁",
                "color": "#f59e0b"
            },
            {
                "title": "평균 코드 변경",
                "value": f"+{avg_additions}/-{avg_deletions}줄",
                "emoji": "📈",
                "color": "#8b5cf6"
            }
        ]

        lines.extend(GameRenderer.render_metric_cards(metrics_data, columns=3))

        lines.append("---")
        lines.append("")

        return lines

    def _render_pr_activity_timeline(self, reviews: List[StoredReview]) -> List[str]:
        """Render PR activity timeline using HTML table."""
        if not reviews:
            return []

        lines: List[str] = []
        lines.append("## 📅 PR 활동 타임라인")
        lines.append("")
        lines.append("> PR 활동의 시간 순서를 확인하세요")
        lines.append("")

        # Build table data - show all PRs in chronological order
        headers = ["#", "PR 번호", "제목", "작성자", "생성일", "코드 변경", "링크"]
        rows = []

        for idx, review in enumerate(reviews, 1):
            date_str = review.created_at.strftime("%Y-%m-%d")
            title_raw = review.title[:50] + "..." if len(review.title) > 50 else review.title
            title_short = html.escape(title_raw, quote=False)

            # Code changes with color indicators
            code_changes = f'<span style="color: #10b981;">+{review.additions}</span> / <span style="color: #ef4444;">-{review.deletions}</span>'

            # Author with emoji
            author_display = f"👤 {html.escape(review.author, quote=False)}"

            # Link
            if review.html_url:
                url = html.escape(review.html_url, quote=True)
                link = f"[보기]({url})"
            else:
                link = "-"

            rows.append([
                str(idx),
                f"#{review.number}",
                title_short,
                author_display,
                html.escape(date_str, quote=False),
                code_changes,
                link
            ])

        # Render as HTML table
        lines.extend(GameRenderer.render_html_table(
            headers=headers,
            rows=rows,
            title="",
            description="",
            striped=True,
            escape_cells=False
        ))

        lines.append("---")
        lines.append("")

        return lines

    def _render_code_changes_visualization(self, reviews: List[StoredReview]) -> List[str]:
        """Render code changes as visual bar charts (HTML version)."""
        if not reviews:
            return []

        lines: List[str] = []
        lines.append("## 📊 PR별 코드 변경량 분석")
        lines.append("")

        # Sort by total changes
        sorted_reviews = sorted(reviews, key=lambda r: r.additions + r.deletions, reverse=True)

        # Show top 10 PRs with most changes
        lines.append("### 상위 10개 PR (변경량 기준)")
        lines.append("")

        # Build table data
        headers = ["PR", "제목", "추가", "삭제", "총 변경", "시각화"]
        rows = []

        for review in sorted_reviews[:10]:
            total_changes = review.additions + review.deletions
            max_bar_length = 20

            # Create visual bars
            if total_changes > 0:
                add_ratio = review.additions / total_changes
                add_bar_length = int(max_bar_length * add_ratio)
                del_bar_length = max_bar_length - add_bar_length
            else:
                add_bar_length = 0
                del_bar_length = 0

            visual_bar = f"{'🟩' * add_bar_length}{'🟥' * del_bar_length}"
            title_raw = review.title[:30] + "..." if len(review.title) > 30 else review.title
            title_short = html.escape(title_raw, quote=False)

            rows.append([
                f"[#{review.number}]({html.escape(review.html_url, quote=True)})",
                title_short,
                f"+{review.additions:,}",
                f"-{review.deletions:,}",
                f"{total_changes:,}",
                visual_bar
            ])

        # Render as HTML table
        lines.extend(GameRenderer.render_html_table(
            headers=headers,
            rows=rows,
            title="",
            description="",
            striped=True,
            escape_cells=False
        ))

        # Add distribution chart using HTML table
        lines.append("### 코드 변경량 분포")
        lines.append("")

        total_additions = sum(r.additions for r in reviews)
        total_deletions = sum(r.deletions for r in reviews)
        total_changes = total_additions + total_deletions

        # Build table data for code change distribution
        headers = ["구분", "줄 수", "비율", "시각화"]
        rows = []

        # Calculate percentages
        add_percentage = (total_additions / total_changes * 100) if total_changes > 0 else 0
        del_percentage = (total_deletions / total_changes * 100) if total_changes > 0 else 0

        # Create visual bars
        add_bar_width = int(add_percentage)
        del_bar_width = int(del_percentage)

        add_visual = f'<div style="background: linear-gradient(90deg, #10b981 0%, #059669 100%); height: 20px; width: {add_bar_width}%; border-radius: 4px;"></div>'
        del_visual = f'<div style="background: linear-gradient(90deg, #ef4444 0%, #dc2626 100%); height: 20px; width: {del_bar_width}%; border-radius: 4px;"></div>'

        rows.append([
            "코드 추가",
            f"<span style='color: #10b981; font-weight: bold;'>+{total_additions:,}줄</span>",
            f"{add_percentage:.1f}%",
            add_visual
        ])
        rows.append([
            "코드 삭제",
            f"<span style='color: #ef4444; font-weight: bold;'>-{total_deletions:,}줄</span>",
            f"{del_percentage:.1f}%",
            del_visual
        ])
        rows.append([
            "**전체 변경**",
            f"**{total_changes:,}줄**",
            "100%",
            ""
        ])

        # Render as HTML table
        lines.extend(GameRenderer.render_html_table(
            headers=headers,
            rows=rows,
            title="",
            description="",
            striped=True,
            escape_cells=False
        ))

        lines.append("---")
        lines.append("")

        return lines

    def _fallback_report(self, repo: str, reviews: List[StoredReview]) -> str:
        lines: List[str] = []
        lines.append("# 🎯 개발자 성장 리포트")
        lines.append("")
        lines.append(f"**저장소**: {repo}")
        lines.append(f"**분석 기간**: 총 {len(reviews)}개의 PR")
        lines.append("")
        lines.append("> 💡 **보고서 활용 팁**: 스탯을 먼저 확인하고, 장점과 성장한 점에서 자신감을 얻은 후, 보완점에서 다음 목표를 찾아보세요!")
        lines.append("")
        lines.append("---")
        lines.append("")

        # ============ 1. 게임 캐릭터 스탯 (맨 처음!) ============
        lines.extend(self._render_character_stats(reviews))

        # ============ 2. 개인 피드백 리포트 (30초 요약 → 장점 → 성장 → 보완점) ============
        personal_dev = self._fallback_personal_development(reviews)
        lines.extend(self._render_personal_development(personal_dev, reviews))

        # ============ 3. 통계 대시보드 ============
        lines.extend(self._render_statistics_dashboard(reviews))

        # ============ 4. PR 활동 타임라인 ============
        lines.extend(self._render_pr_activity_timeline(reviews))

        # ============ 5. 코드 변경량 분석 ============
        lines.extend(self._render_code_changes_visualization(reviews))

        # ============ 6. 개별 PR 하이라이트 ============
        lines.append("## 📝 전체 PR 목록")
        lines.append("")
        lines.append("> 분석에 포함된 모든 PR 목록입니다")
        lines.append("")

        # Build table data
        headers = ["#", "PR", "제목", "날짜", "링크"]
        rows = []
        for i, review in enumerate(reviews, 1):
            date_str = review.created_at.strftime("%Y-%m-%d")
            title_short = review.title[:50] + "..." if len(review.title) > 50 else review.title
            link = f"[보기]({review.html_url})" if review.html_url else "-"
            rows.append([str(i), f"#{review.number}", title_short, date_str, link])

        # Render as HTML table
        lines.extend(GameRenderer.render_html_table(
            headers=headers,
            rows=rows,
            title="",
            description="",
            striped=True
        ))

        lines.append("---")
        lines.append("")

        # ============ 7. 마무리 메시지 ============
        lines.append("## 🎉 마무리")
        lines.append("")
        lines.append(
            f"총 **{len(reviews)}개의 PR**을 통해 꾸준히 성장하고 있습니다! 🚀\n\n"
            "이 보고서가 여러분의 강점을 확인하고, 다음 성장 목표를 설정하는 데 도움이 되었기를 바랍니다. "
            "기억하세요: **모든 PR은 성장의 기회**입니다! 💪\n\n"
            "다음 리포트에서 더 멋진 성장을 기대합니다! 🌟"
        )
        lines.append("")

        return "\n".join(lines).strip()

    def _generate_report_text(self, repo: str, reviews: List[StoredReview]) -> str:
        """Generate integrated report with consistent structure regardless of LLM availability.

        Structure:
        1. Header and intro
        2. Character stats (RPG-style)
        3. Personal development analysis (strengths, growth, improvements)
        4. Team report (if LLM available) or statistics
        5. PR activity visualizations
        6. PR list and closing
        """
        lines: List[str] = []

        # Add font styles at the beginning
        lines.append('<style>')
        lines.append('  @import url("https://fonts.googleapis.com/css2?family=Noto+Sans+KR:wght@300;400;500;700&display=swap");')
        lines.append('  * {')
        lines.append('    font-family: "Noto Sans KR", -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, "Helvetica Neue", Arial, sans-serif;')
        lines.append('  }')
        lines.append('</style>')
        lines.append('')

        # ============ 1. Header ============
        lines.append("# 🎯 개발자 성장 리포트")
        lines.append("")
        lines.append(f"**저장소**: {repo}")
        lines.append(f"**분석 기간**: 총 {len(reviews)}개의 PR")
        lines.append("")
        lines.append("> 💡 **보고서 활용 팁**: 스탯을 먼저 확인하고, 장점과 성장한 점에서 자신감을 얻은 후, 보완점에서 다음 목표를 찾아보세요!")
        lines.append("")
        lines.append("---")
        lines.append("")

        # ============ 2. Character Stats (RPG-style) ============
        lines.extend(self._render_character_stats(reviews))

        # ============ 3. Personal Development Analysis ============
        personal_dev = self._analyze_personal_development(repo, reviews)
        lines.extend(self._render_personal_development(personal_dev, reviews))

        # ============ 4. Team Report (if LLM available) ============
        if self.llm:
            try:
                context = self._build_prompt_context(repo, reviews)
                messages = [
                    {
                        "role": "system",
                        "content": get_team_report_system_prompt(),
                    },
                    {
                        "role": "user",
                        "content": get_team_report_user_prompt(context),
                    },
                ]
                # Increased temperature from 0.4 to 0.5 for better response quality
                # Increased max_retries to 5 for more robust analysis
                team_report = self.llm.complete(messages, temperature=0.5, max_retries=5)
                if team_report.strip():
                    lines.append("---")
                    lines.append("")
                    lines.append(team_report.strip())
                    lines.append("")
                    lines.append("---")
                    lines.append("")
            except Exception as exc:  # pragma: no cover
                console.log("LLM 팀 보고서 생성 실패, 기본 통계로 대체", str(exc))
                lines.extend(self._render_statistics_dashboard(reviews))
        else:
            lines.extend(self._render_statistics_dashboard(reviews))

        # ============ 5. PR Activity Visualizations ============
        lines.extend(self._render_pr_activity_timeline(reviews))
        lines.extend(self._render_code_changes_visualization(reviews))

        # ============ 6. PR List and Closing ============
        lines.append("## 📝 전체 PR 목록")
        lines.append("")
        lines.append("> 분석에 포함된 모든 PR 목록입니다")
        lines.append("")

        # Build table data
        headers = ["#", "PR", "제목", "날짜", "링크"]
        rows = []
        for i, review in enumerate(reviews, 1):
            date_str = review.created_at.strftime("%Y-%m-%d")
            title_short = review.title[:50] + "..." if len(review.title) > 50 else review.title
            link = f"[보기]({review.html_url})" if review.html_url else "-"
            rows.append([str(i), f"#{review.number}", title_short, date_str, link])

        # Render as HTML table
        lines.extend(GameRenderer.render_html_table(
            headers=headers,
            rows=rows,
            title="",
            description="",
            striped=True
        ))

        lines.append("---")
        lines.append("")

        lines.append("## 🎉 마무리")
        lines.append("")
        lines.append(
            f"총 **{len(reviews)}개의 PR**을 통해 꾸준히 성장하고 있습니다! 🚀\n\n"
            "이 보고서가 여러분의 강점을 확인하고, 다음 성장 목표를 설정하는 데 도움이 되었기를 바랍니다. "
            "기억하세요: **모든 PR은 성장의 기회**입니다! 💪\n\n"
            "다음 리포트에서 더 멋진 성장을 기대합니다! 🌟"
        )
        lines.append("")

        return "\n".join(lines).strip()

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    def create_integrated_report(self, repo: str) -> Path:
        """Create or refresh the integrated review report for a repository.

        The report structure is consistent regardless of LLM availability:
        1. Header with repository info
        2. Character stats (RPG-style visualization)
        3. Personal development analysis (strengths, growth, improvements)
        4. Team report (if LLM available) or statistics
        5. PR activity visualizations
        6. PR list and closing message
        """
        repo_input = repo.strip()
        if not repo_input:
            raise ValueError("Repository cannot be empty")

        reviews = self._load_reviews(repo_input)
        if not reviews:
            raise ValueError("No review summaries found for the given repository")

        # Generate integrated report with all sections
        console.log("통합 보고서 생성 중... (캐릭터 스탯 + 개인 피드백 + 팀 분석)")
        report_text = self._generate_report_text(repo_input, reviews)

        # Save report
        from .utils import FileSystemManager

        repo_dir = self._repo_dir(repo_input)
        FileSystemManager.ensure_directory(repo_dir)
        report_path = repo_dir / "integrated_report.md"
        report_path.write_text(report_text, encoding="utf-8")

        # Also save personal development analysis as JSON for programmatic access
        console.log("개인 성장 분석 JSON 저장 중...")
        personal_dev = self._analyze_personal_development(repo_input, reviews)
        personal_dev_path = repo_dir / "personal_development.json"
        personal_dev_path.write_text(
            json.dumps(personal_dev.to_dict(), indent=2, ensure_ascii=False),
            encoding="utf-8",
        )

        console.log(f"✅ 통합 보고서 완성: {report_path}")
        console.log(f"✅ 개인 성장 분석: {personal_dev_path}")
        return report_path


__all__ = ["ReviewReporter", "StoredReview"]
