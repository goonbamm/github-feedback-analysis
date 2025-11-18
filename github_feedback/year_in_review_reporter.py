"""연말 결산 보고서 생성 - 여러 저장소를 종합하여 게임 캐릭터 테마로 시각화합니다."""
from __future__ import annotations

import json
from collections import defaultdict
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional

from .console import Console
from .game_elements import GameRenderer, LevelCalculator
from .utils import pad_to_width

console = Console()


@dataclass
class RepositoryAnalysis:
    """Individual repository analysis data."""

    full_name: str
    pr_count: int
    commit_count: int
    year_commits: int
    integrated_report_path: Optional[Path] = None
    personal_dev_path: Optional[Path] = None
    strengths: List[Dict[str, Any]] = None
    improvements: List[Dict[str, Any]] = None
    growth_indicators: List[Dict[str, Any]] = None
    tech_stack: Dict[str, int] = None

    def __post_init__(self):
        if self.strengths is None:
            self.strengths = []
        if self.improvements is None:
            self.improvements = []
        if self.growth_indicators is None:
            self.growth_indicators = []
        if self.tech_stack is None:
            self.tech_stack = {}


class YearInReviewReporter:
    """Generate comprehensive year-in-review reports."""

    def __init__(self, output_dir: Path = Path("reports/year-in-review")) -> None:
        self.output_dir = output_dir
        self.output_dir.mkdir(parents=True, exist_ok=True)

    def create_year_in_review_report(
        self,
        year: int,
        username: str,
        repository_analyses: List[RepositoryAnalysis],
    ) -> Path:
        """Create comprehensive year-in-review report.

        Args:
            year: Year being reviewed
            username: GitHub username
            repository_analyses: List of repository analysis data

        Returns:
            Path to the generated report
        """
        if not repository_analyses:
            raise ValueError("No repository analyses provided")

        # Aggregate statistics
        total_prs = sum(r.pr_count for r in repository_analyses)
        total_commits = sum(r.year_commits for r in repository_analyses)
        total_repos = len(repository_analyses)

        # Aggregate tech stack
        combined_tech_stack = defaultdict(int)
        for repo in repository_analyses:
            for lang, count in repo.tech_stack.items():
                combined_tech_stack[lang] += count

        # Sort tech stack by usage
        sorted_tech_stack = sorted(
            combined_tech_stack.items(), key=lambda x: x[1], reverse=True
        )

        # Generate report with game character theme
        lines = self._generate_header(year, username, total_repos, total_prs, total_commits)
        lines.extend(self._generate_character_stats(year, total_repos, total_prs, total_commits, repository_analyses))
        lines.extend(self._generate_executive_summary(repository_analyses, sorted_tech_stack))
        lines.extend(self._generate_tech_stack_analysis(sorted_tech_stack))
        lines.extend(self._generate_repository_breakdown(repository_analyses))
        lines.extend(self._generate_aggregated_insights(repository_analyses))
        lines.extend(self._generate_goals_section(repository_analyses, year))
        lines.extend(self._generate_footer())

        # Save report
        report_path = self.output_dir / f"year_{year}_in_review.md"
        report_path.write_text("\n".join(lines), encoding="utf-8")

        console.log(f"✅ Year-in-review report saved: {report_path}")
        return report_path

    def _generate_header(
        self, year: int, username: str, total_repos: int, total_prs: int, total_commits: int
    ) -> List[str]:
        """게임 스타일 헤더 생성."""
        lines = [
            f"# 🎮 {year}년 개발자 모험 결산 보고서",
            "",
            "```",
            "╔═══════════════════════════════════════════════════════════╗",
            "║                                                           ║",
            f"║          🏆  {username}의 {year}년 대모험 기록  🏆            ║",
            "║                                                           ║",
            "║       \"한 해 동안의 모든 코딩 여정이 여기에\"              ║",
            "║                                                           ║",
            "╚═══════════════════════════════════════════════════════════╝",
            "```",
            "",
            f"**📅 보고서 생성일**: {datetime.now().strftime('%Y년 %m월 %d일 %H:%M')}",
            "",
            "---",
            "",
            "## 🎯 한눈에 보는 활동 요약",
            "",
            f"{year}년 한 해 동안, 당신은 **{total_repos}개의 저장소 던전**을 탐험하며 **{total_prs}개의 PR 퀘스트**를 완료하고 **{total_commits}번의 커밋 스킬**을 발동했습니다!",
            "",
            "### 📊 핵심 지표",
            "",
            "```",
            "╔═══════════════════════════════════════════════════════════╗",
            "║                     활동 요약 대시보드                    ║",
            "╠═══════════════════════════════════════════════════════════╣",
            f"║  🏰 탐험한 저장소 던전        │  {total_repos:>4}개               ║",
            f"║  ⚔️  완료한 PR 퀘스트          │  {total_prs:>4}개               ║",
            f"║  💫 발동한 커밋 스킬          │  {total_commits:>4}회               ║",
            f"║  📈 던전당 평균 퀘스트        │  {total_prs // total_repos if total_repos > 0 else 0:>4}개               ║",
            "╚═══════════════════════════════════════════════════════════╝",
            "```",
            "",
            "---",
            "",
        ]
        return lines

    def _generate_executive_summary(
        self, repository_analyses: List[RepositoryAnalysis], tech_stack: List[tuple]
    ) -> List[str]:
        """게임 스타일 최고 업적 섹션 생성."""
        lines = [
            "## 🏆 전설의 업적",
            "",
            "> 한 해 동안 달성한 최고의 기록들",
            "",
        ]

        # Most active repository
        most_active = max(repository_analyses, key=lambda r: r.pr_count)
        lines.append("```")
        lines.append("╔═══════════════════════════════════════════════════════════╗")
        lines.append("║                      🎖️ 최고 업적 🎖️                      ║")
        lines.append("╠═══════════════════════════════════════════════════════════╣")

        # Most active repository
        repo_name = most_active.full_name[:45] if len(most_active.full_name) > 45 else most_active.full_name
        padded_repo = pad_to_width(repo_name, 45, align='left')
        lines.append(f"║  🥇 최다 활동 던전: {padded_repo}  ║")
        lines.append(f"║     └─ 완료 퀘스트: {most_active.pr_count}개                                   ║")

        # Most committed repository
        most_commits = max(repository_analyses, key=lambda r: r.year_commits)
        if most_commits.full_name != most_active.full_name:
            repo_name2 = most_commits.full_name[:45] if len(most_commits.full_name) > 45 else most_commits.full_name
            padded_repo2 = pad_to_width(repo_name2, 45, align='left')
            lines.append("║                                                           ║")
            lines.append(f"║  🥈 최다 커밋 던전: {padded_repo2}  ║")
            lines.append(f"║     └─ 커밋 횟수: {most_commits.year_commits}회                                    ║")

        # Primary technologies
        if tech_stack:
            top_3_tech = [tech[0] for tech in tech_stack[:3]]
            tech_str = ', '.join(top_3_tech)
            tech_padded = pad_to_width(tech_str[:50], 50, align='left')
            lines.append("║                                                           ║")
            lines.append(f"║  💻 주력 무기(기술): {tech_padded} ║")

        lines.append("╚═══════════════════════════════════════════════════════════╝")
        lines.append("```")
        lines.extend(["", "---", ""])
        return lines

    def _generate_repository_breakdown(
        self, repository_analyses: List[RepositoryAnalysis]
    ) -> List[str]:
        """던전별 탐험 기록 생성."""
        lines = [
            "## 🏰 던전 탐험 기록",
            "",
            "> 각 저장소 던전에서의 모험을 상세히 기록합니다",
            "",
        ]

        for idx, repo in enumerate(repository_analyses, 1):
            # Calculate dungeon difficulty based on activity
            total_activity = repo.pr_count + repo.year_commits
            if total_activity >= 100:
                difficulty = "⭐⭐⭐⭐⭐ (전설)"
                difficulty_emoji = "💎"
            elif total_activity >= 50:
                difficulty = "⭐⭐⭐⭐ (어려움)"
                difficulty_emoji = "🔥"
            elif total_activity >= 20:
                difficulty = "⭐⭐⭐ (보통)"
                difficulty_emoji = "⚔️"
            elif total_activity >= 10:
                difficulty = "⭐⭐ (쉬움)"
                difficulty_emoji = "🌟"
            else:
                difficulty = "⭐ (입문)"
                difficulty_emoji = "✨"

            lines.append(f"### {idx}. {difficulty_emoji} {repo.full_name}")
            lines.append("")
            lines.append(f"**난이도**: {difficulty}")
            lines.append("")

            lines.append("```")
            lines.append("╔═══════════════════════════════════════════════════════════╗")
            lines.append("║                      던전 클리어 통계                     ║")
            lines.append("╠═══════════════════════════════════════════════════════════╣")
            lines.append(f"║  ⚔️  완료한 퀘스트 (PR)       │  {repo.pr_count:>4}개               ║")
            lines.append(f"║  💫 발동한 스킬 (커밋)        │  {repo.year_commits:>4}회 (올해)        ║")
            lines.append(f"║  📊 총 기여 횟수              │  {repo.commit_count:>4}회 (전체)        ║")

            if repo.tech_stack:
                top_langs = sorted(repo.tech_stack.items(), key=lambda x: x[1], reverse=True)[:3]
                lines.append("╠═══════════════════════════════════════════════════════════╣")
                lines.append("║  🔧 사용한 주요 기술                                      ║")
                for lang, count in top_langs:
                    lang_padded = pad_to_width(lang, 30, align='left')
                    lines.append(f"║     • {lang_padded}  {count:>3}회    ║")

            lines.append("╚═══════════════════════════════════════════════════════════╝")
            lines.append("```")
            lines.append("")

            # Link to detailed report
            if repo.integrated_report_path:
                # Year-in-review report is in reports/year-in-review/
                # Integrated reports are in reports/reviews/
                # So we need to go up one level (../) from year-in-review to reports
                rel_from_reports = repo.integrated_report_path.relative_to(self.output_dir.parent)
                rel_from_year_in_review = Path("..") / rel_from_reports
                lines.append(f"📜 **[상세 보고서 보기]({rel_from_year_in_review})**")
                lines.append("")

            # Key insights from personal development
            if repo.strengths:
                lines.append("**✨ 획득한 스킬:**")
                for strength in repo.strengths[:2]:  # Top 2 strengths
                    category = strength.get("category", "")
                    desc = strength.get("description", "")
                    lines.append(f"- 💎 **{category}**: {desc}")
                lines.append("")

            if repo.improvements:
                lines.append("**🎯 성장 기회:**")
                for improvement in repo.improvements[:2]:  # Top 2 improvements
                    category = improvement.get("category", "")
                    desc = improvement.get("description", "")
                    lines.append(f"- 🌱 **{category}**: {desc}")
                lines.append("")

            lines.append("---")
            lines.append("")

        return lines

    def _generate_tech_stack_analysis(self, tech_stack: List[tuple]) -> List[str]:
        """무기 장비 분석 생성."""
        lines = [
            "## ⚔️ 장착 무기 및 장비 (기술 스택)",
            "",
            "> 한 해 동안 사용한 언어와 프레임워크",
            "",
        ]

        if not tech_stack:
            lines.append("_기술 데이터가 없습니다._")
            lines.extend(["", "---", ""])
            return lines

        total_changes = sum(count for _, count in tech_stack)

        lines.append("```")
        lines.append("╔═══════════════════════════════════════════════════════════╗")
        lines.append("║                     무기 사용 통계                        ║")
        lines.append("╠═══════════════════════════════════════════════════════════╣")

        for idx, (lang, count) in enumerate(tech_stack[:10], 1):  # Top 10
            percentage = (count / total_changes * 100) if total_changes > 0 else 0

            # Determine weapon tier
            if percentage >= 30:
                tier = "⚔️ 전설 무기"
            elif percentage >= 15:
                tier = "🗡️ 희귀 무기"
            elif percentage >= 5:
                tier = "🔪 일반 무기"
            else:
                tier = "🔧 보조 도구"

            # Visual bar (20 blocks for 100%)
            filled = int(percentage / 5)
            empty = 20 - filled
            bar = "▓" * filled + "░" * empty

            # Pad language name
            lang_padded = pad_to_width(lang, 18, align='left')
            lines.append(f"║  {idx:2}. {lang_padded} │ [{bar}] {percentage:>5.1f}%  ║")

        lines.append("╚═══════════════════════════════════════════════════════════╝")
        lines.append("```")
        lines.extend(["", "---", ""])
        return lines

    def _generate_aggregated_insights(
        self, repository_analyses: List[RepositoryAnalysis]
    ) -> List[str]:
        """종합 인사이트 생성."""
        lines = [
            "## 🌟 종합 성장 분석",
            "",
            "> 모든 던전에서 발견된 패턴과 성장 트렌드",
            "",
        ]

        # Collect all strengths and improvements
        all_strengths = defaultdict(int)
        all_improvements = defaultdict(int)

        for repo in repository_analyses:
            for strength in repo.strengths:
                category = strength.get("category", "기타")
                all_strengths[category] += 1

            for improvement in repo.improvements:
                category = improvement.get("category", "기타")
                all_improvements[category] += 1

        # Top recurring strengths
        if all_strengths:
            lines.append("### ✨ 반복적으로 발견된 강점 스킬")
            lines.append("")
            lines.append("> 여러 던전에서 빛을 발한 당신의 핵심 능력")
            lines.append("")
            sorted_strengths = sorted(all_strengths.items(), key=lambda x: x[1], reverse=True)
            for idx, (category, count) in enumerate(sorted_strengths[:5], 1):
                lines.append(f"{idx}. 💎 **{category}** - {count}개 던전에서 발휘")
            lines.append("")

        # Top recurring improvement areas
        if all_improvements:
            lines.append("### 🎯 공통 성장 기회")
            lines.append("")
            lines.append("> 여러 던전에서 발견된 레벨업 포인트")
            lines.append("")
            sorted_improvements = sorted(all_improvements.items(), key=lambda x: x[1], reverse=True)
            for idx, (category, count) in enumerate(sorted_improvements[:5], 1):
                lines.append(f"{idx}. 🌱 **{category}** - {count}개 던전에서 발견")
            lines.append("")

        # Growth indicators
        lines.append("### 📈 성장 지표")
        lines.append("")

        repos_with_growth = [r for r in repository_analyses if r.growth_indicators]
        if repos_with_growth:
            lines.append(f"🎊 **{len(repository_analyses)}개 던전 중 {len(repos_with_growth)}개에서 측정 가능한 성장을 달성했습니다!**")
            lines.append("")

            # Sample growth examples
            lines.append("**대표적인 성장 사례:**")
            lines.append("")
            for repo in repos_with_growth[:3]:
                if repo.growth_indicators:
                    indicator = repo.growth_indicators[0]
                    aspect = indicator.get("aspect", "")
                    summary = indicator.get("progress_summary", "")
                    lines.append(f"- 🚀 **{repo.full_name}**: {aspect} - {summary}")
            lines.append("")
        else:
            lines.append("💡 _특정 성장 지표는 아직 발견되지 않았지만, 꾸준한 활동으로 성장하고 있습니다!_")
            lines.append("")

        lines.extend(["", "---", ""])
        return lines

    def _generate_character_stats(
        self, year: int, total_repos: int, total_prs: int, total_commits: int,
        repository_analyses: List[RepositoryAnalysis]
    ) -> List[str]:
        """게임 캐릭터 스탯 생성 (99레벨 시스템 사용)."""
        lines = [
            "## 🎮 개발자 캐릭터 스탯",
            "",
            f"> {year}년 한 해 동안의 활동을 RPG 캐릭터 스탯으로 시각화",
            "",
        ]

        # Calculate overall stats based on activity
        total_activity = total_prs + total_commits

        # 99레벨 시스템으로 레벨 계산
        level, title, rank_emoji = LevelCalculator.calculate_level_99(total_activity)

        # Calculate stats (0-100 scale)
        # 1. Code Quality - based on PR count and diversity
        code_quality = min(100, int(
            (min(total_prs / 50, 1) * 50) +  # PR volume
            (min(total_repos / 10, 1) * 30) +  # Repository diversity
            20  # Base score
        ))

        # 2. Productivity - based on commit count
        productivity = min(100, int(
            (min(total_commits / 200, 1) * 60) +  # Commit volume
            (min(total_activity / 300, 1) * 40)  # Total activity
        ))

        # 3. Collaboration - based on number of repositories
        collaboration = min(100, int(
            (min(total_repos / 5, 1) * 40) +  # Repository count
            (min(total_prs / 30, 1) * 40) +  # PR engagement
            20  # Base score
        ))

        # 4. Consistency - based on activity distribution
        consistency = min(100, int(
            (min(total_activity / 200, 1) * 50) +  # Overall activity
            30  # Base score
        ))

        # 5. Growth - based on improvement indicators
        repos_with_growth = len([r for r in repository_analyses if r.growth_indicators])
        growth = min(100, int(
            50 +  # Base growth score
            (min(repos_with_growth / len(repository_analyses) if repository_analyses else 0, 1) * 50)
        ))

        # 스탯 딕셔너리 구성
        stats = {
            "code_quality": code_quality,
            "productivity": productivity,
            "collaboration": collaboration,
            "consistency": consistency,  # Note: 종합 보고서는 "꾸준함" 사용
            "growth": growth,
        }

        # 특성 타이틀 결정
        specialty_title = LevelCalculator.get_specialty_title(stats)

        # 경험치 데이터 준비
        experience_data = {
            "🏰 탐험한 던전": f"{total_repos:>4}개",
            "⚔️  완료한 퀘스트": f"{total_prs:>4}개",
            "💫 발동한 스킬": f"{total_commits:>4}회",
            "🎯 총 경험치": f"{total_activity:>4} EXP",
        }

        # 뱃지 생성
        badges = LevelCalculator.get_badges_from_stats(
            stats,
            total_commits=total_commits,
            total_prs=total_prs,
            total_repos=total_repos
        )

        # consistency를 꾸준함 뱃지로 교체 (종합 보고서 전용)
        if stats.get("consistency", 0) >= 80:
            badges = [b for b in badges if "협업 챔피언" not in b or b == "🤝 협업 챔피언"]
            badges.append("📅 꾸준함의 화신")

        # GameRenderer로 캐릭터 스탯 렌더링 (경험치 데이터 포함)
        # 하지만 종합 보고서는 커스텀 경험치 섹션이 필요하므로 직접 렌더링
        lines.append("```")
        lines.append("╔═══════════════════════════════════════════════════════════╗")

        # Title and level with proper padding
        title_padded = pad_to_width(title, 24, align='left')
        avg_stat = sum(stats.values()) / len(stats)
        lines.append(f"║  {rank_emoji} Lv.{level:>2} {title_padded} 파워: {int(avg_stat):>3}/100  ║")

        # 특성 표시
        specialty_padded = pad_to_width(specialty_title, 43, align='left')
        lines.append(f"║  🏅 특성: {specialty_padded} ║")
        lines.append("╠═══════════════════════════════════════════════════════════╣")
        lines.append("║                      능력치 현황                          ║")
        lines.append("╠═══════════════════════════════════════════════════════════╣")

        # Render each stat (종합 보고서용 순서: 코드품질, 생산성, 협업력, 꾸준함, 성장성)
        stat_order = [
            ("💻", "코드 품질", code_quality),
            ("⚡", "생산성", productivity),
            ("🤝", "협업력", collaboration),
            ("📅", "꾸준함", consistency),
            ("📈", "성장성", growth),
        ]

        for emoji, name, value in stat_order:
            # Create visual bar (20 blocks for 100%)
            filled = value // 5
            empty = 20 - filled
            bar = "▓" * filled + "░" * empty

            # Pad name to 12 display columns
            name_padded = pad_to_width(name, 12, align='left')
            lines.append(f"║ {emoji} {name_padded} [{bar}] {value:>3}/100 ║")

        lines.append("╠═══════════════════════════════════════════════════════════╣")
        lines.append("║                      획득 경험치                          ║")
        lines.append("╠═══════════════════════════════════════════════════════════╣")
        lines.append(f"║  🏰 탐험한 던전      │  {total_repos:>4}개                          ║")
        lines.append(f"║  ⚔️  완료한 퀘스트    │  {total_prs:>4}개                          ║")
        lines.append(f"║  💫 발동한 스킬      │  {total_commits:>4}회                          ║")
        lines.append(f"║  🎯 총 경험치        │  {total_activity:>4} EXP                      ║")
        lines.append("╚═══════════════════════════════════════════════════════════╝")
        lines.append("```")
        lines.append("")

        # 뱃지 표시
        if badges:
            lines.append("**🎖️ 획득한 업적 뱃지:**")
            lines.append("")
            # Display badges in rows of 3
            for i in range(0, len(badges), 3):
                badge_row = badges[i:i+3]
                lines.append("| " + " | ".join(badge_row) + " |")
            lines.append("")

        lines.append("---")
        lines.append("")
        return lines

    def _generate_goals_section(
        self, repository_analyses: List[RepositoryAnalysis], year: int
    ) -> List[str]:
        """다음 연도 목표 생성."""
        lines = [
            f"## 🎯 {year + 1}년 퀘스트 목표",
            "",
            f"> {year}년의 경험을 바탕으로 한 다음 시즌 추천 퀘스트",
            "",
        ]

        # Collect all improvement suggestions
        all_suggestions = []
        for repo in repository_analyses:
            for improvement in repo.improvements:
                suggestions = improvement.get("suggestions", [])
                all_suggestions.extend(suggestions)

        # Deduplicate and limit
        unique_suggestions = list(dict.fromkeys(all_suggestions))[:5]

        if unique_suggestions:
            lines.append("### 💡 추천 성장 방향")
            lines.append("")
            lines.append("> 다음 레벨로 올라가기 위한 핵심 포커스")
            lines.append("")
            for idx, suggestion in enumerate(unique_suggestions, 1):
                lines.append(f"{idx}. 🎯 {suggestion}")
            lines.append("")

        lines.append("### 🚀 실행 액션 아이템")
        lines.append("")
        lines.append("> 새로운 시즌을 준비하는 체크리스트")
        lines.append("")
        lines.append("- [ ] 📖 각 저장소의 상세 피드백 검토하기")
        lines.append("- [ ] 🎯 주요 개선 영역에 대한 구체적이고 측정 가능한 목표 설정")
        lines.append("- [ ] 🔧 새로운 기술 탐험 또는 현재 스택의 전문성 심화")
        lines.append("- [ ] 🤝 협업 및 코드 리뷰 참여 확대")
        lines.append(f"- [ ] 📊 {year + 1}년 내내 분기별 진행 상황 추적")
        lines.append("")

        lines.append("---")
        lines.append("")
        return lines

    def _generate_footer(self) -> List[str]:
        """게임 스타일 푸터 생성."""
        return [
            "## 🎉 모험의 마무리",
            "",
            "```",
            "╔═══════════════════════════════════════════════════════════╗",
            "║                                                           ║",
            "║              🌟  축하합니다, 용감한 개발자여!  🌟           ║",
            "║                                                           ║",
            "║   모든 커밋, PR, 리뷰가 당신의 성장에 기여했습니다.       ║",
            "║   이 보고서로 성과를 축하하고 지속적인 성장을 계획하세요. ║",
            "║                                                           ║",
            "║   💡 기억하세요:                                          ║",
            "║   \"완벽한 한 번보다 꾸준한 진보가 더 강합니다!\"          ║",
            "║                                                           ║",
            "║              🚀 계속 전진하세요! 🚀                        ║",
            "║                                                           ║",
            "╚═══════════════════════════════════════════════════════════╝",
            "```",
            "",
            "---",
            "",
            "<div align=\"center\">",
            "",
            "⚔️ *Generated by GitHub Feedback Analysis Tool* ⚔️",
            "",
            "_당신의 코딩 여정을 응원합니다!_",
            "",
            "</div>",
        ]


__all__ = ["YearInReviewReporter", "RepositoryAnalysis"]
