"""Aggregate pull request reviews into an integrated annual report."""

from __future__ import annotations

import json
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Iterable, List

from .console import Console
from .llm import LLMClient
from .models import ReviewPoint

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


class ReviewReporter:
    """Build integrated Korean reports from individual pull request reviews."""

    def __init__(self, *, output_dir: Path = Path("reviews"), llm: LLMClient | None = None) -> None:
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
                summary_data = json.loads(summary_path.read_text(encoding="utf-8"))
                artefact_data = json.loads(artefact_path.read_text(encoding="utf-8"))
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
            lines.append(
                f"- PR #{review.number} {review.title} (작성자: {review.author}, 생성일: {review.created_at.date()})"
            )
            if review.html_url:
                lines.append(f"  URL: {review.html_url}")
            if review.overview:
                lines.append(f"  Overview: {review.overview}")
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

    # ------------------------------------------------------------------
    # Reporting
    # ------------------------------------------------------------------

    def _fallback_report(self, repo: str, reviews: List[StoredReview]) -> str:
        lines: List[str] = []
        lines.append("# 🎯 통합 코드 리뷰 보고서")
        lines.append("")
        lines.append(f"**저장소**: {repo}")
        lines.append(f"**검토한 PR 수**: {len(reviews)}건")
        lines.append("")
        lines.append("---")
        lines.append("")

        # Table of contents
        lines.append("## 📑 목차")
        lines.append("")
        lines.append("1. **✨ 장점** - 뛰어났던 점들")
        lines.append("2. **💡 보완점** - 개선할 수 있는 부분")
        lines.append("3. **🌱 올해 성장한 점** - 성장 여정")
        lines.append("4. **🎊 전체 총평** - 종합 평가")
        lines.append("5. **📝 개별 PR 하이라이트** - 주요 PR 목록")
        lines.append("")
        lines.append("---")
        lines.append("")

        def _render_points(title: str, emoji: str, entries: List[tuple[StoredReview, ReviewPoint]]) -> None:
            lines.append(f"## {emoji} {title}")
            lines.append("")
            if not entries:
                lines.append("- 수집된 항목이 없습니다.")
                lines.append("")
                return

            for i, (review, point) in enumerate(entries, 1):
                bullet = f"{i}. **PR #{review.number}** `{review.title}`"
                lines.append(bullet)
                lines.append(f"   - {point.message}")
                if point.example:
                    lines.append(f"   - 💡 예시: `{point.example}`")
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
                "content": (
                    "당신은 기술 리더로서 팀의 성장을 돕는 통합 보고서를 작성합니다.\n\n"
                    "**보고서 목적:**\n"
                    "1. 데이터 기반 인사이트 제공\n"
                    "2. 실행 가능한 개선 방안 제시\n"
                    "3. 팀의 성장 과정 가시화\n"
                    "4. 다음 분기 목표 설정 근거 마련\n\n"
                    "**분석 관점:**\n"
                    "- 시간에 따른 트렌드 (개선 또는 악화)\n"
                    "- 반복되는 패턴 (좋은 것, 나쁜 것)\n"
                    "- 팀원별/영역별 강점과 개선점\n"
                    "- 기술 부채 누적 여부\n"
                    "- 코드 품질 지표 변화\n\n"
                    "**보고서 구조:**\n\n"
                    "# 🎯 통합 코드 리뷰 보고서\n\n"
                    "## 📊 핵심 지표 요약\n"
                    "- 전체 PR 수, 리뷰 참여율\n"
                    "- 평균 리뷰 시간, 병합까지 기간\n"
                    "- 주요 개선 트렌드 (↗ 또는 ↘)\n\n"
                    "## ✨ 주요 성과\n"
                    "- 데이터로 입증된 긍정적 변화\n"
                    "- 특히 잘한 부분 (구체적 PR 인용)\n"
                    "- 영향도가 큰 순으로 정렬\n\n"
                    "## 💡 개선 영역\n"
                    "- 우선순위별 정렬 (Critical → Nice-to-have)\n"
                    "- 각 항목에 구체적 액션 플랜\n"
                    "- 예상 개선 효과 명시\n\n"
                    "## 📈 트렌드 분석\n"
                    "- 지난 기간 대비 변화\n"
                    "- 반복되는 이슈 패턴\n"
                    "- 새롭게 발견된 문제\n\n"
                    "## 🎯 다음 분기 권장 사항\n"
                    "1. 즉시 실행 가능한 액션 아이템 (1-3개)\n"
                    "2. 중기 개선 목표 (1-2개월)\n"
                    "3. 장기 투자 영역\n\n"
                    "## 📝 개별 PR 하이라이트\n"
                    "- 학습 가치가 높은 PR들\n"
                    "- 모범 사례와 반면교사\n\n"
                    "**작성 원칙:**\n"
                    "- 추상적 표현 대신 구체적 데이터와 예시\n"
                    "- 비난보다 성장 관점\n"
                    "- 실행 가능성 최우선\n"
                    "- 팀 맥락과 문화 고려\n\n"
                    "출력은 Markdown 형식, 이모지는 적절히 사용하세요. 모든 응답은 한국어로 작성하세요."
                ),
            },
            {
                "role": "user",
                "content": (
                    f"다음 데이터를 분석하여 통합 보고서를 작성하세요:\n\n"
                    f"{context}\n\n"
                    "추가 분석 포인트:\n"
                    "1. 이 기간 동안 가장 큰 변화는?\n"
                    "2. 가장 시급한 개선 사항은?\n"
                    "3. 팀의 강점을 더 강화하려면?\n"
                    "4. 다음 달까지 달성 가능한 목표 1가지는?"
                ),
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

        report_text = self._generate_report_text(repo_input, reviews)

        repo_dir = self._repo_dir(repo_input)
        repo_dir.mkdir(parents=True, exist_ok=True)
        report_path = repo_dir / "integrated_report.md"
        report_path.write_text(report_text, encoding="utf-8")
        return report_path


__all__ = ["ReviewReporter", "StoredReview"]
