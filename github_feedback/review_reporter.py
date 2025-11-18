"""Aggregate pull request reviews into an integrated annual report."""
from __future__ import annotations

import json
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Iterable, List

import re

from .console import Console
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
            summary_path = pr_dir / "review_summary.json"
            artefact_path = pr_dir / "artefacts.json"
            if not summary_path.exists() or not artefact_path.exists():
                continue

            try:
                summary_text = summary_path.read_text(encoding="utf-8").strip()
                artefact_text = artefact_path.read_text(encoding="utf-8").strip()

                if not summary_text or not artefact_text:
                    console.log("Skipping empty review artefact", str(pr_dir))
                    continue

                summary_data = json.loads(summary_text)
                artefact_data = json.loads(artefact_text)
            except json.JSONDecodeError:
                console.log("Skipping invalid review artefact", str(pr_dir))
                continue

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
                continue

            overview = str(summary_data.get("overview") or "").strip()
            strengths = self._load_points(summary_data.get("strengths", []))
            improvements = self._load_points(summary_data.get("improvements", []))

            # Load additional fields from artefacts
            body = str(artefact_data.get("body") or "").strip()
            review_bodies = artefact_data.get("review_bodies", [])
            review_comments = artefact_data.get("review_comments", [])
            additions = int(artefact_data.get("additions", 0))
            deletions = int(artefact_data.get("deletions", 0))
            changed_files = int(artefact_data.get("changed_files", 0))

            reviews.append(
                StoredReview(
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
            )

        reviews.sort(key=lambda item: (item.created_at, item.number))
        return reviews

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

            # Include PR body for analyzing description quality (increased limit for better context)
            if review.body:
                body_preview = review.body[:600] + "..." if len(review.body) > 600 else review.body
                lines.append(f"  PR 설명: {body_preview}")

            if review.overview:
                lines.append(f"  Overview: {review.overview}")

            # Include review comments for tone analysis (increased count and length for better analysis)
            if review.review_comments:
                lines.append(f"  리뷰 코멘트 ({len(review.review_comments)}개):")
                for idx, comment in enumerate(review.review_comments[:10], 1):  # Show first 10 comments
                    comment_preview = comment[:300] + "..." if len(comment) > 300 else comment
                    lines.append(f"    {idx}. {comment_preview}")
                if len(review.review_comments) > 10:
                    lines.append(f"    ... 외 {len(review.review_comments) - 10}개 코멘트")

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

        context = self._build_prompt_context(repo, reviews)

        # Split reviews into early and recent for growth analysis
        midpoint = len(reviews) // 2
        early_reviews = reviews[:midpoint] if midpoint > 0 else []
        recent_reviews = reviews[midpoint:] if midpoint > 0 else reviews

        messages = [
            {
                "role": "system",
                "content": get_personal_development_system_prompt(),
            },
            {
                "role": "user",
                "content": get_personal_development_user_prompt(
                    context,
                    len(early_reviews),
                    len(recent_reviews)
                ),
            },
        ]

        try:
            import json as json_module

            content = self.llm.complete(messages, temperature=0.4)
            data = json_module.loads(content)

            # Parse TLDR summary
            tldr_summary = None
            if "tldr_summary" in data and data["tldr_summary"]:
                tldr_data = data["tldr_summary"]
                tldr_summary = TLDRSummary(
                    top_strength=tldr_data.get("top_strength", ""),
                    primary_focus=tldr_data.get("primary_focus", ""),
                    measurable_goal=tldr_data.get("measurable_goal", ""),
                )

            # Parse strengths
            strengths = []
            for item in data.get("strengths", []):
                strengths.append(
                    StrengthPoint(
                        category=item.get("category", "기타"),
                        description=item.get("description", ""),
                        evidence=item.get("evidence", []),
                        impact=item.get("impact", "medium"),
                    )
                )

            # Parse improvement areas
            improvement_areas = []
            for item in data.get("improvement_areas", []):
                improvement_areas.append(
                    ImprovementArea(
                        category=item.get("category", "기타"),
                        description=item.get("description", ""),
                        evidence=item.get("evidence", []),
                        suggestions=item.get("suggestions", []),
                        priority=item.get("priority", "medium"),
                    )
                )

            # Parse growth indicators
            growth_indicators = []
            for item in data.get("growth_indicators", []):
                growth_indicators.append(
                    GrowthIndicator(
                        aspect=item.get("aspect", ""),
                        description=item.get("description", ""),
                        before_examples=item.get("before_examples", []),
                        after_examples=item.get("after_examples", []),
                        progress_summary=item.get("progress_summary", ""),
                    )
                )

            return PersonalDevelopmentAnalysis(
                strengths=strengths,
                improvement_areas=improvement_areas,
                growth_indicators=growth_indicators,
                tldr_summary=tldr_summary,
            )
        except Exception as exc:  # pragma: no cover
            console.log("LLM 개인 발전 분석 실패", str(exc))
            return self._fallback_personal_development(reviews)

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
        code_quality = min(100, int(
            (strength_ratio * 50) +  # Strength contribution (0-50)
            (min(avg_files_per_pr / 10, 1) * 25) +  # File organization (0-25)
            (25 if total_prs >= 10 else (total_prs / 10) * 25)  # Experience bonus (0-25)
        ))

        # Collaboration (0-100): Based on review engagement
        has_reviews = sum(1 for r in reviews if r.review_bodies or r.review_comments)
        collaboration_rate = has_reviews / total_prs if total_prs > 0 else 0
        avg_feedback = (total_strengths + total_improvements) / total_prs if total_prs > 0 else 0
        collaboration = min(100, int(
            (collaboration_rate * 50) +  # Review engagement (0-50)
            (min(avg_feedback / 5, 1) * 30) +  # Feedback quality (0-30)
            (20 if total_prs >= 5 else (total_prs / 5) * 20)  # Participation bonus (0-20)
        ))

        # Problem Solving (0-100): Based on PR complexity and scope
        avg_changes = (total_additions + total_deletions) / total_prs if total_prs > 0 else 0
        problem_solving = min(100, int(
            (min(avg_changes / 500, 1) * 40) +  # Change complexity (0-40)
            (min(avg_files_per_pr / 15, 1) * 30) +  # Scope breadth (0-30)
            (30 if total_prs >= 8 else (total_prs / 8) * 30)  # Problem count (0-30)
        ))

        # Productivity (0-100): Based on output volume
        productivity = min(100, int(
            (min(total_prs / 20, 1) * 40) +  # PR count (0-40)
            (min(total_additions / 5000, 1) * 35) +  # Code output (0-35)
            (min(total_files / 100, 1) * 25)  # File coverage (0-25)
        ))

        # Growth (0-100): Based on consistent improvement
        # Calculate trend from first half vs second half
        if total_prs >= 4:
            mid_point = total_prs // 2
            first_half = reviews[:mid_point]
            second_half = reviews[mid_point:]

            first_avg_strengths = sum(len(r.strengths) for r in first_half) / len(first_half)
            second_avg_strengths = sum(len(r.strengths) for r in second_half) / len(second_half)

            improvement_rate = (second_avg_strengths - first_avg_strengths) / max(first_avg_strengths, 1)
            growth = min(100, max(0, int(
                50 +  # Base growth
                (improvement_rate * 30) +  # Improvement trend (±30)
                (20 if total_prs >= 15 else (total_prs / 15) * 20)  # Consistency bonus (0-20)
            )))
        else:
            growth = min(100, int((total_prs / 4) * 60 + 40))  # Base growth for new developers

        return {
            "code_quality": code_quality,
            "collaboration": collaboration,
            "problem_solving": problem_solving,
            "productivity": productivity,
            "growth": growth,
        }

    def _render_character_stats(self, reviews: List[StoredReview]) -> List[str]:
        """Render RPG-style character stats visualization."""
        lines: List[str] = []

        stats = self._calculate_character_stats(reviews)
        total_power = sum(stats.values())
        avg_stat = total_power / 5 if stats else 0

        # Determine level based on average stat
        if avg_stat >= 90:
            level = 6
            title = "그랜드마스터"
            rank_emoji = "👑"
        elif avg_stat >= 75:
            level = 5
            title = "마스터"
            rank_emoji = "🏆"
        elif avg_stat >= 60:
            level = 4
            title = "전문가"
            rank_emoji = "⭐"
        elif avg_stat >= 40:
            level = 3
            title = "숙련자"
            rank_emoji = "💎"
        elif avg_stat >= 20:
            level = 2
            title = "견습생"
            rank_emoji = "🎓"
        else:
            level = 1
            title = "초보자"
            rank_emoji = "🌱"

        # Determine specialties based on highest stats
        stat_names_kr = {
            "code_quality": "코드 품질",
            "collaboration": "협업력",
            "problem_solving": "문제 해결력",
            "productivity": "생산성",
            "growth": "성장성",
        }
        sorted_stats = sorted(stats.items(), key=lambda x: x[1], reverse=True)
        primary_specialty = stat_names_kr[sorted_stats[0][0]]

        # Assign title based on specialty
        specialty_titles = {
            "코드 품질": "코드 아키텍트",
            "협업력": "팀 플레이어",
            "문제 해결력": "문제 해결사",
            "생산성": "스피드 러너",
            "성장성": "라이징 스타",
        }
        specialty_title = specialty_titles.get(primary_specialty, "개발자")

        lines.append("## 🎮 개발자 캐릭터 스탯")
        lines.append("")
        lines.append("```")
        lines.append("╔═══════════════════════════════════════════════════════════╗")
        lines.append(f"║  {rank_emoji} Level {level}: {title:<20} 파워 레벨: {int(avg_stat):>3}/100  ║")
        lines.append(f"║  🏅 특성: {specialty_title:<43} ║")
        lines.append("╠═══════════════════════════════════════════════════════════╣")
        lines.append("║                      능력치 현황                          ║")
        lines.append("╠═══════════════════════════════════════════════════════════╣")

        # Render each stat with visual bar
        stat_emojis = {
            "code_quality": "💻",
            "collaboration": "🤝",
            "problem_solving": "🧩",
            "productivity": "⚡",
            "growth": "📈",
        }

        for stat_key, stat_value in stats.items():
            stat_name = stat_names_kr[stat_key]
            emoji = stat_emojis[stat_key]

            # Create visual bar (20 blocks for 100%)
            filled = stat_value // 5
            empty = 20 - filled
            bar = "▓" * filled + "░" * empty

            # Format line with proper spacing
            lines.append(f"║ {emoji} {stat_name:<12} [{bar}] {stat_value:>3}/100 ║")

        lines.append("╚═══════════════════════════════════════════════════════════╝")
        lines.append("```")
        lines.append("")

        # Add achievements/badges
        badges = []
        if stats["code_quality"] >= 80:
            badges.append("🏅 코드 마스터")
        if stats["collaboration"] >= 80:
            badges.append("🤝 협업 챔피언")
        if stats["problem_solving"] >= 80:
            badges.append("🧠 문제 해결 전문가")
        if stats["productivity"] >= 80:
            badges.append("⚡ 생산성 괴물")
        if stats["growth"] >= 80:
            badges.append("🚀 급성장 개발자")
        if total_prs := len(reviews):
            if total_prs >= 50:
                badges.append("💯 PR 마라토너")
            elif total_prs >= 20:
                badges.append("📝 활발한 기여자")

        if badges:
            lines.append("**🎖️ 획득한 뱃지:**")
            lines.append("")
            for badge in badges:
                lines.append(f"- {badge}")
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

        # 2. Strengths (잘하고 있는 것) - 펼쳐진 상태
        lines.extend(self._render_new_strengths_section(analysis, pr_map))
        lines.append("---")
        lines.append("")

        # 3. Improvements (보완하면 좋을 것) - 펼쳐진 상태
        lines.extend(self._render_new_improvements_section(analysis, pr_map))
        lines.append("---")
        lines.append("")

        # 4. Growth (성장한 점) - 펼쳐진 상태
        if analysis.growth_indicators:
            lines.extend(self._render_new_growth_section(analysis, pr_map))
            lines.append("---")
            lines.append("")

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
        """Render key metrics dashboard with visual cards."""
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
        lines.append("| 지표 | 값 | 시각화 |")
        lines.append("|------|-----|--------|")
        lines.append(f"| 📝 **총 PR 수** | {total_prs}개 | {'🟦' * min(total_prs, 20)} |")
        lines.append(f"| 👥 **참여 인원** | {unique_authors}명 | {'👤' * min(unique_authors, 10)} |")
        lines.append(f"| ➕ **총 코드 추가** | +{total_additions:,}줄 | {'🟩' * min(total_additions // 100, 20)} |")
        lines.append(f"| ➖ **총 코드 삭제** | -{total_deletions:,}줄 | {'🟥' * min(total_deletions // 100, 20)} |")
        lines.append(f"| 📁 **변경된 파일** | {total_files_changed:,}개 | {'📄' * min(total_files_changed // 10, 20)} |")
        lines.append(f"| 📈 **평균 코드 변경** | +{avg_additions}/-{avg_deletions}줄 | - |")
        lines.append("")
        lines.append("---")
        lines.append("")

        return lines

    def _render_pr_activity_timeline(self, reviews: List[StoredReview]) -> List[str]:
        """Render PR activity timeline using Mermaid diagram."""
        if not reviews:
            return []

        lines: List[str] = []
        lines.append("## 📅 PR 활동 타임라인")
        lines.append("")
        lines.append("```mermaid")
        lines.append("gantt")
        lines.append("    title PR 활동 현황")
        lines.append("    dateFormat YYYY-MM-DD")
        lines.append("    section PR 활동")

        # Show first 10 PRs to keep diagram readable
        for review in reviews[:10]:
            date_str = review.created_at.strftime("%Y-%m-%d")
            safe_title = review.title.replace(":", " -")[:30]  # Limit length and escape colons
            lines.append(f"    PR #{review.number} {safe_title} :{date_str}, 1d")

        if len(reviews) > 10:
            lines.append(f"    ... 외 {len(reviews) - 10}개 PR :crit, 2024-01-01, 1d")

        lines.append("```")
        lines.append("")
        lines.append("---")
        lines.append("")

        return lines

    def _render_code_changes_visualization(self, reviews: List[StoredReview]) -> List[str]:
        """Render code changes as visual bar charts."""
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
        lines.append("| PR | 제목 | 추가 | 삭제 | 총 변경 | 시각화 |")
        lines.append("|-----|------|------|------|---------|---------|")

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

            title_short = review.title[:30] + "..." if len(review.title) > 30 else review.title
            lines.append(
                f"| [#{review.number}]({review.html_url}) | {title_short} | "
                f"+{review.additions:,} | -{review.deletions:,} | "
                f"{total_changes:,} | {visual_bar} |"
            )

        lines.append("")

        # Add distribution chart using Mermaid
        lines.append("### 코드 변경량 분포")
        lines.append("")
        lines.append("```mermaid")
        lines.append("pie title 전체 코드 변경 구성")

        total_additions = sum(r.additions for r in reviews)
        total_deletions = sum(r.deletions for r in reviews)

        lines.append(f'    "코드 추가 (+{total_additions:,}줄)" : {total_additions}')
        lines.append(f'    "코드 삭제 (-{total_deletions:,}줄)" : {total_deletions}')
        lines.append("```")
        lines.append("")
        lines.append("---")
        lines.append("")

        return lines

    def _fallback_report(self, repo: str, reviews: List[StoredReview]) -> str:
        lines: List[str] = []
        lines.append("# 🎯 통합 코드 리뷰 보고서")
        lines.append("")
        lines.append(f"**저장소**: {repo}")
        lines.append(f"**검토한 PR 수**: {len(reviews)}건")
        lines.append("")
        lines.append("---")
        lines.append("")

        # Add statistics dashboard
        lines.extend(self._render_statistics_dashboard(reviews))

        # Add character stats (RPG-style)
        lines.extend(self._render_character_stats(reviews))

        # Add PR activity timeline
        lines.extend(self._render_pr_activity_timeline(reviews))

        # Add code changes visualization
        lines.extend(self._render_code_changes_visualization(reviews))

        # Table of contents
        lines.append("## 📑 목차")
        lines.append("")
        lines.append("1. **🎮 개발자 캐릭터 스탯** - 게임 스타일 능력치 시각화")
        lines.append("2. **👤 개인 성장 분석** - 장점, 보완점, 성장한 점")
        lines.append("3. **✨ 장점** - 뛰어났던 점들")
        lines.append("4. **💡 보완점** - 개선할 수 있는 부분")
        lines.append("5. **🌱 올해 성장한 점** - 성장 여정")
        lines.append("6. **🎊 전체 총평** - 종합 평가")
        lines.append("7. **📝 개별 PR 하이라이트** - 주요 PR 목록")
        lines.append("")
        lines.append("---")
        lines.append("")

        # Add personal development analysis
        personal_dev = self._fallback_personal_development(reviews)
        lines.extend(self._render_personal_development(personal_dev, reviews))

        def _render_points(title: str, emoji: str, entries: List[tuple[StoredReview, ReviewPoint]]) -> None:
            lines.append(f"## {emoji} {title}")
            lines.append("")
            if not entries:
                lines.append("수집된 항목이 없습니다.")
                lines.append("")
                return

            lines.append(f"| {title} | 근거/내용 | 링크 |")
            lines.append("|--------|-----------|------|")
            for review, point in entries:
                category = f"**PR #{review.number}**<br>`{review.title}`"

                # Combine message and example
                content_parts = [point.message]
                if point.example:
                    content_parts.append(f"<br>💡 **예시:**<br>`{point.example}`")
                content = "".join(content_parts)

                # Create link
                link_cell = f"[PR #{review.number}]({review.html_url})" if review.html_url else "-"
                lines.append(f"| {category} | {content} | {link_cell} |")
            lines.append("")
            lines.append("---")
            lines.append("")

        strength_entries: List[tuple[StoredReview, ReviewPoint]] = []
        improvement_entries: List[tuple[StoredReview, ReviewPoint]] = []

        for review in reviews:
            strength_entries.extend((review, point) for point in review.strengths)
            improvement_entries.extend((review, point) for point in review.improvements)

        _render_points("장점", "✨", strength_entries[:8])
        _render_points("보완점", "💡", improvement_entries[:8])

        lines.append("## 🌱 올해 성장한 점")
        lines.append("")
        growth_items = [review for review in reviews if review.overview]
        if not growth_items:
            lines.append("- 개별 리뷰 요약이 없어 성장 포인트를 추론하기 어렵습니다.")
        else:
            for i, review in enumerate(growth_items[:8], 1):
                lines.append(f"{i}. **PR #{review.number}** `{review.title}`")
                lines.append(f"   - {review.overview}")
                lines.append("")
        lines.append("---")
        lines.append("")

        lines.append("## 🎊 전체 총평")
        lines.append("")
        lines.append(
            "저장된 리뷰 요약을 바탕으로 팀이 지속해서 지식을 공유하고 있으며, "
            "통합 보고서를 통해 반복되는 강점과 개선점을 추적할 수 있습니다. "
            f"총 {len(reviews)}건의 PR을 통해 꾸준한 성장을 이어가고 있습니다."
        )
        lines.append("")
        lines.append("---")
        lines.append("")

        lines.append("## 📝 개별 PR 하이라이트")
        lines.append("")
        for i, review in enumerate(reviews, 1):
            date_str = review.created_at.strftime("%Y-%m-%d")
            highlight = f"{i}. **PR #{review.number}** `{review.title}` ({date_str})"
            lines.append(highlight)
            if review.html_url:
                lines.append(f"   - 🔗 [{review.html_url}]({review.html_url})")
            lines.append("")

        return "\n".join(lines).strip()

    def _generate_report_text(self, repo: str, reviews: List[StoredReview]) -> str:
        if not self.llm:
            return self._fallback_report(repo, reviews)

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

        try:
            content = self.llm.complete(messages, temperature=0.4)
            if content.strip():
                return content.strip()
        except Exception as exc:  # pragma: no cover - network errors hard to simulate
            console.log("LLM 통합 보고서 생성 실패", str(exc))

        return self._fallback_report(repo, reviews)

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    def create_integrated_report(self, repo: str) -> Path:
        """Create or refresh the integrated review report for a repository."""

        repo_input = repo.strip()
        if not repo_input:
            raise ValueError("Repository cannot be empty")

        reviews = self._load_reviews(repo_input)
        if not reviews:
            raise ValueError("No review summaries found for the given repository")

        # Generate personal development analysis
        console.log("개인 성장 분석 생성 중...")
        personal_dev = self._analyze_personal_development(repo_input, reviews)

        # Generate main report
        console.log("통합 보고서 생성 중...")
        report_text = self._generate_report_text(repo_input, reviews)

        # If LLM report doesn't include personal development section, add it at the beginning
        if "## 👤 개인 피드백 리포트" not in report_text and "개인 피드백 리포트" not in report_text:
            lines = report_text.split("\n")
            # Find where to insert (after the header and initial metadata)
            insert_idx = 0
            for i, line in enumerate(lines):
                if line.startswith("---") or line.startswith("##"):
                    insert_idx = i
                    break

            # Insert personal development section
            personal_dev_lines = self._render_personal_development(personal_dev, reviews)
            lines = lines[:insert_idx] + personal_dev_lines + lines[insert_idx:]
            report_text = "\n".join(lines)

        # Save report
        repo_dir = self._repo_dir(repo_input)
        repo_dir.mkdir(parents=True, exist_ok=True)
        report_path = repo_dir / "integrated_report.md"
        report_path.write_text(report_text, encoding="utf-8")

        # Also save personal development analysis as JSON for programmatic access
        personal_dev_path = repo_dir / "personal_development.json"
        personal_dev_path.write_text(
            json.dumps(personal_dev.to_dict(), indent=2, ensure_ascii=False),
            encoding="utf-8",
        )

        console.log(f"개인 성장 분석 저장: {personal_dev_path}")
        return report_path


__all__ = ["ReviewReporter", "StoredReview"]
