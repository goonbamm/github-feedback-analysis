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
        """게임 스타일 헤더 생성 (HTML 버전)."""
        lines = [
            f"# 🎮 {year}년 개발자 모험 결산 보고서",
            "",
        ]

        # HTML 헤더 박스
        lines.append('<div style="border: 3px solid #fbbf24; border-radius: 12px; padding: 30px; margin: 20px 0; background: linear-gradient(135deg, #fef3c7 0%, #fde68a 100%); text-align: center; box-shadow: 0 4px 6px rgba(251, 191, 36, 0.3);">')
        lines.append(f'  <h2 style="margin: 0; color: #78350f; font-size: 1.8em;">🏆 {username}의 {year}년 대모험 기록 🏆</h2>')
        lines.append(f'  <p style="margin: 10px 0 0 0; color: #92400e; font-size: 1.1em; font-style: italic;">"한 해 동안의 모든 코딩 여정이 여기에"</p>')
        lines.append('</div>')
        lines.append("")

        lines.append(f"**📅 보고서 생성일**: {datetime.now().strftime('%Y년 %m월 %d일 %H:%M')}")
        lines.append("")
        lines.append("---")
        lines.append("")

        lines.append("## 🎯 한눈에 보는 활동 요약")
        lines.append("")
        lines.append(f"{year}년 한 해 동안, 당신은 **{total_repos}개의 저장소 던전**을 탐험하며 **{total_prs}개의 PR 퀘스트**를 완료하고 **{total_commits}번의 커밋 스킬**을 발동했습니다!")
        lines.append("")

        # 핵심 지표 카드
        avg_quests = total_prs // total_repos if total_repos > 0 else 0
        metrics_data = [
            {
                "title": "탐험한 저장소 던전",
                "value": f"{total_repos}개",
                "emoji": "🏰",
                "color": "#667eea"
            },
            {
                "title": "완료한 PR 퀘스트",
                "value": f"{total_prs}개",
                "emoji": "⚔️",
                "color": "#f59e0b"
            },
            {
                "title": "발동한 커밋 스킬",
                "value": f"{total_commits}회",
                "emoji": "💫",
                "color": "#8b5cf6"
            },
            {
                "title": "던전당 평균 퀘스트",
                "value": f"{avg_quests}개",
                "emoji": "📈",
                "color": "#10b981"
            }
        ]

        lines.extend(GameRenderer.render_metric_cards(metrics_data, columns=4))

        lines.append("---")
        lines.append("")

        return lines

    def _generate_executive_summary(
        self, repository_analyses: List[RepositoryAnalysis], tech_stack: List[tuple]
    ) -> List[str]:
        """게임 스타일 최고 업적 섹션 생성 (HTML 버전)."""
        lines = [
            "## 🏆 전설의 업적",
            "",
            "> 한 해 동안 달성한 최고의 기록들",
            "",
        ]

        # Most active repository
        most_active = max(repository_analyses, key=lambda r: r.pr_count)
        most_commits = max(repository_analyses, key=lambda r: r.year_commits)

        # Build achievements list
        achievement_text = f"🥇 **최다 활동 던전**: {most_active.full_name}\n   └─ 완료 퀘스트: {most_active.pr_count}개"

        if most_commits.full_name != most_active.full_name:
            achievement_text += f"\n\n🥈 **최다 커밋 던전**: {most_commits.full_name}\n   └─ 커밋 횟수: {most_commits.year_commits}회"

        if tech_stack:
            top_3_tech = [tech[0] for tech in tech_stack[:3]]
            tech_str = ', '.join(top_3_tech)
            achievement_text += f"\n\n💻 **주력 무기(기술)**: {tech_str}"

        # Render as info box
        lines.extend(GameRenderer.render_info_box(
            title="🎖️ 최고 업적 🎖️",
            content=achievement_text,
            emoji="🏆",
            bg_color="#fef3c7",
            border_color="#fbbf24"
        ))

        lines.extend(["---", ""])
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

            # Build stats content
            stats_content = f"⚔️  **완료한 퀘스트 (PR)**: {repo.pr_count}개\n"
            stats_content += f"💫 **발동한 스킬 (커밋)**: {repo.year_commits}회 (올해)\n"
            stats_content += f"📊 **총 기여 횟수**: {repo.commit_count}회 (전체)"

            if repo.tech_stack:
                top_langs = sorted(repo.tech_stack.items(), key=lambda x: x[1], reverse=True)[:3]
                stats_content += "\n\n🔧 **사용한 주요 기술**:"
                for lang, count in top_langs:
                    stats_content += f"\n   • {lang}: {count}회"

            # Render as info box
            lines.extend(GameRenderer.render_info_box(
                title="던전 클리어 통계",
                content=stats_content,
                emoji="📊",
                bg_color="#eff6ff",
                border_color="#3b82f6"
            ))

            # Link to detailed report
            if repo.integrated_report_path:
                # Year-in-review report is in reports/year-in-review/
                # Integrated reports are in reports/reviews/
                # So we need to go up one level (../) from year-in-review to reports
                rel_from_reports = repo.integrated_report_path.relative_to(self.output_dir.parent)
                rel_from_year_in_review = Path("..") / rel_from_reports
                lines.append(f"📜 **[상세 보고서 보기]({rel_from_year_in_review})**")
                lines.append("")

            # Key insights from personal development - HTML 테이블 형식
            if repo.strengths:
                lines.append("#### ✨ 획득한 스킬")
                lines.append("")

                # Build table data
                headers = ["스킬", "설명", "영향도", "증거"]
                rows = []

                for strength in repo.strengths[:5]:  # Top 5 strengths
                    category = strength.get("category", "")
                    desc = strength.get("description", "")
                    impact = strength.get("impact", "medium")
                    evidence = strength.get("evidence", [])

                    # Impact emoji and text
                    impact_display = {
                        "high": "🔥 높음",
                        "medium": "💫 중간",
                        "low": "✨ 낮음"
                    }.get(impact, "💫 중간")

                    # Format evidence as list
                    evidence_html = ""
                    if evidence:
                        evidence_html = "<ul style='margin: 0; padding-left: 20px;'>"
                        for ev in evidence[:2]:  # Show top 2
                            evidence_html += f"<li style='margin-bottom: 4px;'>{ev}</li>"
                        evidence_html += "</ul>"
                    else:
                        evidence_html = "-"

                    rows.append([category, desc, impact_display, evidence_html])

                # Render as HTML table
                lines.extend(GameRenderer.render_html_table(
                    headers=headers,
                    rows=rows,
                    title="",
                    description="",
                    striped=True
                ))
                lines.append("")

            if repo.improvements:
                lines.append("#### 🎯 성장 기회")
                lines.append("")

                # Build table data
                headers = ["분야", "설명", "우선순위", "개선 방안"]
                rows = []

                for improvement in repo.improvements[:5]:  # Top 5 improvements
                    category = improvement.get("category", "")
                    desc = improvement.get("description", "")
                    priority = improvement.get("priority", "medium")
                    suggestions = improvement.get("suggestions", [])

                    # Priority emoji and text
                    priority_display = {
                        "critical": "🚨 긴급",
                        "important": "⚡ 중요",
                        "nice-to-have": "💡 권장"
                    }.get(priority, "⚡ 중요")

                    # Format suggestions as list
                    suggestions_html = ""
                    if suggestions:
                        suggestions_html = "<ul style='margin: 0; padding-left: 20px;'>"
                        for sug in suggestions[:3]:  # Show top 3
                            suggestions_html += f"<li style='margin-bottom: 4px;'>{sug}</li>"
                        suggestions_html += "</ul>"
                    else:
                        suggestions_html = "-"

                    rows.append([category, desc, priority_display, suggestions_html])

                # Render as HTML table
                lines.extend(GameRenderer.render_html_table(
                    headers=headers,
                    rows=rows,
                    title="",
                    description="",
                    striped=True
                ))
                lines.append("")

            if repo.growth_indicators:
                lines.append("#### 📈 성장 지표")
                lines.append("")

                # Build table data
                headers = ["측면", "진행 상황 요약"]
                rows = []

                for indicator in repo.growth_indicators[:5]:  # Top 5 growth indicators
                    aspect = indicator.get("aspect", "")
                    progress_summary = indicator.get("progress_summary", "")

                    rows.append([f"🚀 {aspect}", progress_summary])

                # Render as HTML table
                lines.extend(GameRenderer.render_html_table(
                    headers=headers,
                    rows=rows,
                    title="",
                    description="",
                    striped=True
                ))
                lines.append("")

            lines.append("---")
            lines.append("")

        return lines

    def _generate_tech_stack_analysis(self, tech_stack: List[tuple]) -> List[str]:
        """무기 장비 분석 생성 (테마 장비 시스템 사용)."""
        from .game_elements import EquipmentSystem

        lines = [
            "## ⚔️ 장착 무기 및 장비 (기술 스택)",
            "",
            "> 한 해 동안 사용한 언어와 프레임워크를 RPG 장비로 시각화",
            "",
        ]

        if not tech_stack:
            lines.append("_기술 데이터가 없습니다._")
            lines.extend(["", "---", ""])
            return lines

        total_changes = sum(count for _, count in tech_stack)

        # 장비 인벤토리 설명
        lines.extend([
            '<div style="background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); color: white; padding: 16px; border-radius: 8px; margin-bottom: 20px;">',
            '  <h3 style="margin: 0 0 8px 0; font-size: 1.2em;">🎒 장비 인벤토리</h3>',
            '  <p style="margin: 0; opacity: 0.95; line-height: 1.5;">',
            '    각 기술은 사용 빈도에 따라 전설(⭐⭐⭐), 희귀(⭐⭐), 일반(⭐) 등급으로 분류됩니다.<br>',
            '    장비마다 고유한 이름과 특성이 부여되어 당신의 기술 역량을 표현합니다!',
            '  </p>',
            '</div>',
            '',
        ])

        # 각 기술을 장비 카드로 렌더링
        for idx, (lang, count) in enumerate(tech_stack[:10], 1):  # Top 10
            percentage = (count / total_changes * 100) if total_changes > 0 else 0

            # 장비 정보 가져오기
            equipment_info = EquipmentSystem.get_equipment_info(lang, percentage)

            # 장비 카드 렌더링
            card_html = EquipmentSystem.render_equipment_card(
                rank=idx,
                tech_name=lang,
                equipment_info=equipment_info,
                usage_count=count,
                usage_percentage=percentage
            )

            lines.append(card_html)
            lines.append('')

        # 장비 통계 요약
        legendary_count = sum(1 for lang, count in tech_stack[:10]
                             if (count / total_changes * 100) >= 30)
        rare_count = sum(1 for lang, count in tech_stack[:10]
                        if 15 <= (count / total_changes * 100) < 30)
        common_count = sum(1 for lang, count in tech_stack[:10]
                          if 5 <= (count / total_changes * 100) < 15)

        lines.extend([
            '<div style="background: #f3f4f6; padding: 16px; border-radius: 8px; margin-top: 20px; border-left: 4px solid #667eea;">',
            '  <h4 style="margin: 0 0 12px 0; color: #2d3748;">📊 장비 등급 분포</h4>',
            '  <div style="display: grid; grid-template-columns: repeat(3, 1fr); gap: 12px;">',
            f'    <div style="text-align: center; padding: 12px; background: white; border-radius: 6px; border: 2px solid #fbbf24;">',
            f'      <div style="font-size: 1.5em; margin-bottom: 4px;">⭐⭐⭐</div>',
            f'      <div style="font-weight: bold; color: #f59e0b;">전설 {legendary_count}개</div>',
            f'    </div>',
            f'    <div style="text-align: center; padding: 12px; background: white; border-radius: 6px; border: 2px solid #8b5cf6;">',
            f'      <div style="font-size: 1.5em; margin-bottom: 4px;">⭐⭐</div>',
            f'      <div style="font-weight: bold; color: #7c3aed;">희귀 {rare_count}개</div>',
            f'    </div>',
            f'    <div style="text-align: center; padding: 12px; background: white; border-radius: 6px; border: 2px solid #3b82f6;">',
            f'      <div style="font-size: 1.5em; margin-bottom: 4px;">⭐</div>',
            f'      <div style="font-weight: bold; color: #2563eb;">일반 {common_count}개</div>',
            f'    </div>',
            '  </div>',
            '</div>',
            '',
        ])

        lines.extend(["---", ""])
        return lines


    def _generate_character_stats(
        self, year: int, total_repos: int, total_prs: int, total_commits: int,
        repository_analyses: List[RepositoryAnalysis]
    ) -> List[str]:
        """게임 캐릭터 스탯 생성 (HTML 버전, 99레벨 시스템 사용)."""
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

        # 스탯 딕셔너리 구성 (종합 보고서용)
        stats = {
            "code_quality": code_quality,
            "productivity": productivity,
            "collaboration": collaboration,
            "consistency": consistency,  # 종합 보고서는 "꾸준함" 사용
            "growth": growth,
        }

        # 특성 타이틀 결정
        specialty_title = LevelCalculator.get_specialty_title(stats)

        # 경험치 데이터 준비
        experience_data = {
            "🏰 탐험한 던전": total_repos,
            "⚔️  완료한 퀘스트": total_prs,
            "💫 발동한 스킬": total_commits,
            "🎯 총 경험치": f"{total_activity:,} EXP",
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

        # GameRenderer로 캐릭터 스탯 렌더링 (HTML 버전)
        # 종합 보고서는 99레벨 시스템 사용 (use_tier_system=False)
        character_lines = GameRenderer.render_character_stats(
            level=level,
            title=title,
            rank_emoji=rank_emoji,
            specialty_title=specialty_title,
            stats=stats,
            experience_data=experience_data,
            badges=badges,
            use_tier_system=False  # 99레벨 시스템 사용
        )

        lines.extend(character_lines)
        lines.append("---")
        lines.append("")
        return lines

    def _generate_goals_section(
        self, repository_analyses: List[RepositoryAnalysis], year: int
    ) -> List[str]:
        """다음 연도 목표 생성 (HTML 버전)."""
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

            # Build suggestion cards
            suggestion_content = ""
            for idx, suggestion in enumerate(unique_suggestions, 1):
                suggestion_content += f"{idx}. 🎯 {suggestion}\n"

            # Render as info box
            lines.extend(GameRenderer.render_info_box(
                title="다음 레벨로 올라가기 위한 핵심 포커스",
                content=suggestion_content.strip(),
                emoji="💡",
                bg_color="#f0fdf4",
                border_color="#10b981"
            ))

        lines.append("### 🚀 실행 액션 아이템")
        lines.append("")

        # Build action items as HTML checklist
        action_items = [
            "📖 각 저장소의 상세 피드백 검토하기",
            "🎯 주요 개선 영역에 대한 구체적이고 측정 가능한 목표 설정",
            "🔧 새로운 기술 탐험 또는 현재 스택의 전문성 심화",
            "🤝 협업 및 코드 리뷰 참여 확대",
            f"📊 {year + 1}년 내내 분기별 진행 상황 추적"
        ]

        lines.append('<div style="border: 2px solid #e2e8f0; border-radius: 8px; padding: 20px; margin: 16px 0; background: white; box-shadow: 0 2px 4px rgba(0,0,0,0.1);">')
        lines.append('  <h4 style="margin: 0 0 16px 0; color: #2d3748; font-size: 1.2em;">새로운 시즌을 준비하는 체크리스트</h4>')
        lines.append('  <div style="display: flex; flex-direction: column; gap: 12px;">')

        for item in action_items:
            lines.append('    <label style="display: flex; align-items: center; cursor: pointer; padding: 12px; background: #f7fafc; border-radius: 6px; transition: background 0.2s;">')
            lines.append('      <input type="checkbox" style="margin-right: 12px; width: 18px; height: 18px; cursor: pointer;">')
            lines.append(f'      <span style="color: #2d3748; font-size: 1em;">{item}</span>')
            lines.append('    </label>')

        lines.append('  </div>')
        lines.append('</div>')
        lines.append("")

        lines.append("---")
        lines.append("")
        return lines

    def _generate_footer(self) -> List[str]:
        """게임 스타일 푸터 생성 (HTML 버전)."""
        return [
            "## 🎉 모험의 마무리",
            "",
            '<div style="border: 3px solid #fbbf24; border-radius: 12px; padding: 30px; margin: 20px 0; background: linear-gradient(135deg, #fef3c7 0%, #fde68a 100%); text-align: center; box-shadow: 0 4px 6px rgba(251, 191, 36, 0.3);">',
            '  <div style="font-size: 2em; margin-bottom: 20px;">🌟</div>',
            '  <h2 style="margin: 0 0 20px 0; color: #78350f; font-size: 1.8em;">축하합니다, 용감한 개발자여!</h2>',
            '  <p style="margin: 0 0 20px 0; color: #92400e; font-size: 1.1em; line-height: 1.6;">',
            '    모든 커밋, PR, 리뷰가 당신의 성장에 기여했습니다.<br>',
            '    이 보고서로 성과를 축하하고 지속적인 성장을 계획하세요.',
            '  </p>',
            '  <div style="background: rgba(255,255,255,0.5); border-radius: 8px; padding: 16px; margin: 20px 0;">',
            '    <div style="font-size: 1.2em; color: #78350f; font-weight: bold; margin-bottom: 8px;">💡 기억하세요</div>',
            '    <div style="font-size: 1.1em; color: #92400e; font-style: italic;">"완벽한 한 번보다 꾸준한 진보가 더 강합니다!"</div>',
            '  </div>',
            '  <div style="font-size: 1.5em; margin-top: 20px; color: #78350f; font-weight: bold;">🚀 계속 전진하세요! 🚀</div>',
            '</div>',
            "",
            "---",
            "",
            '<div style="text-align: center; margin: 20px 0; padding: 20px; background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); border-radius: 8px; color: white;">',
            '  <div style="font-size: 1.2em; margin-bottom: 8px;">⚔️ Generated by GitHub Feedback Analysis Tool ⚔️</div>',
            '  <div style="font-style: italic; opacity: 0.9;">당신의 코딩 여정을 응원합니다!</div>',
            '</div>',
            "",
        ]


__all__ = ["YearInReviewReporter", "RepositoryAnalysis"]
