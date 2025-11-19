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


# ============================================
# 🎮 RPG 장비 시스템 설정
# ============================================

# 기술별 카테고리 분류 (언어, 프레임워크, 도구/DB)
TECH_CATEGORIES = {
    # 프로그래밍 언어 (주무기)
    "Python": "language",
    "JavaScript": "language",
    "TypeScript": "language",
    "Java": "language",
    "Go": "language",
    "Rust": "language",
    "C++": "language",
    "C": "language",
    "C#": "language",
    "Ruby": "language",
    "PHP": "language",
    "Swift": "language",
    "Kotlin": "language",
    "Dart": "language",
    "Scala": "language",
    "R": "language",
    "Shell": "language",
    "Bash": "language",
    "PowerShell": "language",
    "Lua": "language",
    "Perl": "language",
    "Haskell": "language",
    "Elixir": "language",
    "Clojure": "language",

    # 프레임워크 & 라이브러리 (보조무기)
    "React": "framework",
    "Vue": "framework",
    "Angular": "framework",
    "Next.js": "framework",
    "Nuxt.js": "framework",
    "Svelte": "framework",
    "Django": "framework",
    "Flask": "framework",
    "FastAPI": "framework",
    "Express": "framework",
    "NestJS": "framework",
    "Spring": "framework",
    "Spring Boot": "framework",
    "Rails": "framework",
    "Laravel": "framework",
    "ASP.NET": "framework",
    "Node.js": "framework",
    "Deno": "framework",
    "TensorFlow": "framework",
    "PyTorch": "framework",
    "Pandas": "framework",
    "NumPy": "framework",
    "Scikit-learn": "framework",

    # 도구, DB, 인프라 (장신구/악세서리)
    "Docker": "tool",
    "Kubernetes": "tool",
    "PostgreSQL": "tool",
    "MySQL": "tool",
    "MongoDB": "tool",
    "Redis": "tool",
    "Elasticsearch": "tool",
    "RabbitMQ": "tool",
    "Kafka": "tool",
    "Git": "tool",
    "GitHub Actions": "tool",
    "Jenkins": "tool",
    "CircleCI": "tool",
    "Terraform": "tool",
    "Ansible": "tool",
    "AWS": "tool",
    "GCP": "tool",
    "Azure": "tool",
    "Nginx": "tool",
    "Apache": "tool",
    "GraphQL": "tool",
    "REST API": "tool",
    "gRPC": "tool",
    "WebSocket": "tool",
    "HTML": "tool",
    "CSS": "tool",
    "SCSS": "tool",
    "Tailwind": "tool",
    "Webpack": "tool",
    "Vite": "tool",
    "Babel": "tool",
    "ESLint": "tool",
    "Prettier": "tool",
    "Jest": "tool",
    "Pytest": "tool",
    "Cypress": "tool",
    "Selenium": "tool",
}

# 특정 기술에 대한 커스텀 아이콘 및 무기명
TECH_CUSTOM_ICONS = {
    # 언어
    "Python": {"icon": "🐍", "weapon_name": "파이썬의 마법봉"},
    "JavaScript": {"icon": "⚡", "weapon_name": "자바스크립트의 성검"},
    "TypeScript": {"icon": "🛡️", "weapon_name": "타입가드의 방패"},
    "Java": {"icon": "☕", "weapon_name": "자바의 대검"},
    "Go": {"icon": "🐹", "weapon_name": "고퍼의 신속검"},
    "Rust": {"icon": "🦀", "weapon_name": "러스트의 안전갑옷"},
    "C++": {"icon": "⚙️", "weapon_name": "C++의 전투도끼"},
    "Ruby": {"icon": "💎", "weapon_name": "루비의 보석검"},
    "PHP": {"icon": "🐘", "weapon_name": "PHP의 전설활"},
    "Swift": {"icon": "🦅", "weapon_name": "스위프트의 날개"},
    "Kotlin": {"icon": "🎯", "weapon_name": "코틀린의 정밀창"},
    "Dart": {"icon": "🎯", "weapon_name": "다트의 비수"},

    # 프레임워크
    "React": {"icon": "⚛️", "weapon_name": "리액트의 오브"},
    "Vue": {"icon": "💚", "weapon_name": "뷰의 마법서"},
    "Angular": {"icon": "🅰️", "weapon_name": "앵귤러의 실드"},
    "Django": {"icon": "🎸", "weapon_name": "장고의 연금술"},
    "Flask": {"icon": "🧪", "weapon_name": "플라스크의 물약"},
    "FastAPI": {"icon": "⚡", "weapon_name": "FastAPI의 번개창"},
    "Spring": {"icon": "🌱", "weapon_name": "스프링의 생명나무"},
    "Next.js": {"icon": "▲", "weapon_name": "Next.js의 차원검"},
    "Express": {"icon": "🚂", "weapon_name": "익스프레스의 질주"},
    "Node.js": {"icon": "🟢", "weapon_name": "노드의 마력핵"},

    # 도구
    "Docker": {"icon": "🐋", "weapon_name": "컨테이너의 갑옷"},
    "Kubernetes": {"icon": "☸️", "weapon_name": "쿠버네티스의 지휘봉"},
    "PostgreSQL": {"icon": "🐘", "weapon_name": "포스트그레의 저장고"},
    "MySQL": {"icon": "🐬", "weapon_name": "MySQL의 데이터 보관함"},
    "MongoDB": {"icon": "🍃", "weapon_name": "몽고DB의 문서철"},
    "Redis": {"icon": "🔴", "weapon_name": "레디스의 신속부적"},
    "Git": {"icon": "🌿", "weapon_name": "깃의 시간마법"},
    "GitHub Actions": {"icon": "🤖", "weapon_name": "자동화 골렘"},
    "AWS": {"icon": "☁️", "weapon_name": "클라우드의 날개"},
    "GraphQL": {"icon": "◆", "weapon_name": "그래프QL의 질의석"},
}

# 7단계 무기 등급 시스템
WEAPON_TIERS = [
    {
        "threshold": 60,  # 기준 상향 (50->60)
        "name": "신화",
        "prefix": "💎",
        "suffix": "신화 무기",
        "color": "#ec4899",
        "glow": "rgba(236, 72, 153, 0.3)"
    },
    {
        "threshold": 40,  # 기준 상향 (30->40)
        "name": "전설",
        "prefix": "⚔️",
        "suffix": "전설 무기",
        "color": "#fbbf24",
        "glow": "rgba(251, 191, 36, 0.3)"
    },
    {
        "threshold": 28,  # 기준 상향 (20->28)
        "name": "영웅",
        "prefix": "🗡️",
        "suffix": "영웅 무기",
        "color": "#f97316",
        "glow": "rgba(249, 115, 22, 0.3)"
    },
    {
        "threshold": 18,  # 기준 상향 (10->18)
        "name": "희귀",
        "prefix": "⚡",
        "suffix": "희귀 무기",
        "color": "#8b5cf6",
        "glow": "rgba(139, 92, 246, 0.3)"
    },
    {
        "threshold": 10,  # 기준 상향 (5->10)
        "name": "고급",
        "prefix": "🔪",
        "suffix": "고급 무기",
        "color": "#3b82f6",
        "glow": "rgba(59, 130, 246, 0.3)"
    },
    {
        "threshold": 5,  # 기준 상향 (2->5)
        "name": "일반",
        "prefix": "🔨",
        "suffix": "일반 무기",
        "color": "#10b981",
        "glow": "rgba(16, 185, 129, 0.3)"
    },
    {
        "threshold": 0,
        "name": "보조",
        "prefix": "🔧",
        "suffix": "보조 도구",
        "color": "#6b7280",
        "glow": "rgba(107, 114, 128, 0.3)"
    }
]

# 장비 슬롯 타입 (카테고리별)
EQUIPMENT_SLOTS = {
    "language": {"slot": "🎯 주무기", "priority": 1},
    "framework": {"slot": "🛡️ 보조무기", "priority": 2},
    "tool": {"slot": "💍 장신구", "priority": 3},
}


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
        repos_with_tech_stack = 0
        for repo in repository_analyses:
            if repo.tech_stack:
                repos_with_tech_stack += 1
                console.log(f"[dim]  {repo.full_name}: {len(repo.tech_stack)} technologies[/]")
                for lang, count in repo.tech_stack.items():
                    combined_tech_stack[lang] += count
            else:
                console.log(f"[warning]  {repo.full_name}: No tech stack data[/]")

        # Sort tech stack by usage
        sorted_tech_stack = sorted(
            combined_tech_stack.items(), key=lambda x: x[1], reverse=True
        )

        console.log(f"[dim]Tech stack aggregation: {repos_with_tech_stack}/{total_repos} repos with data, {len(sorted_tech_stack)} total technologies[/]")

        # Add font styles at the beginning
        font_styles = [
            '<style>',
            '  @import url("https://fonts.googleapis.com/css2?family=Noto+Sans+KR:wght@300;400;500;700&display=swap");',
            '  * {',
            '    font-family: "Noto Sans KR", -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, "Helvetica Neue", Arial, sans-serif;',
            '  }',
            '</style>',
            ''
        ]

        # Generate report with game character theme
        lines = font_styles[:]  # Start with font styles
        lines.extend(self._generate_header(year, username, total_repos, total_prs, total_commits))
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
        """무기 장비 분석 생성 - 7단계 등급 시스템 및 장비 슬롯 시스템."""
        lines = [
            "## ⚔️ 장착 무기 및 장비 (기술 스택)",
            "",
            "> 한 해 동안 사용한 언어와 프레임워크를 RPG 장비 시스템으로 시각화",
            "",
        ]

        if not tech_stack:
            lines.append("_기술 데이터가 없습니다._")
            lines.extend(["", "---", ""])
            return lines

        total_changes = sum(count for _, count in tech_stack)

        # 기술을 카테고리별로 분류
        categorized_tech = {
            "language": [],
            "framework": [],
            "tool": [],
            "unknown": []
        }

        for lang, count in tech_stack:
            percentage = (count / total_changes * 100) if total_changes > 0 else 0
            category = TECH_CATEGORIES.get(lang, "unknown")

            # 무기 등급 결정 (7단계)
            tier_info = None
            for tier in WEAPON_TIERS:
                if percentage >= tier["threshold"]:
                    tier_info = tier
                    break

            # 커스텀 아이콘 및 무기명 가져오기
            custom = TECH_CUSTOM_ICONS.get(lang, {})
            icon = custom.get("icon", "🔹")
            weapon_name = custom.get("weapon_name", lang)

            tech_info = {
                "name": lang,
                "count": count,
                "percentage": percentage,
                "tier": tier_info,
                "icon": icon,
                "weapon_name": weapon_name
            }

            categorized_tech[category].append(tech_info)

        # ============================================
        # 📦 장비창 시스템 (상위 10개만 슬롯에 표시)
        # ============================================
        lines.append("### 📦 캐릭터 장비창")
        lines.append("")
        lines.append("> 현재 장착 중인 최상위 장비들")
        lines.append("")

        # 카테고리별 최상위 기술 선택
        equipment_slots = []

        # 주무기 슬롯 (언어, 최대 3개)
        for tech in categorized_tech["language"][:3]:
            equipment_slots.append({
                "slot": "🎯 주무기",
                "tech": tech,
                "priority": 1
            })

        # 보조무기 슬롯 (프레임워크, 최대 3개)
        for tech in categorized_tech["framework"][:3]:
            equipment_slots.append({
                "slot": "🛡️ 보조무기",
                "tech": tech,
                "priority": 2
            })

        # 장신구 슬롯 (도구, 최대 4개)
        for tech in categorized_tech["tool"][:4]:
            equipment_slots.append({
                "slot": "💍 장신구",
                "tech": tech,
                "priority": 3
            })

        if equipment_slots:
            # 장비창 HTML 박스 생성
            lines.append('<div style="border: 3px solid #8b5cf6; border-radius: 12px; padding: 25px; margin: 20px 0; background: linear-gradient(135deg, #f3e8ff 0%, #e9d5ff 100%); box-shadow: 0 4px 8px rgba(139, 92, 246, 0.3);">')
            lines.append('  <h3 style="margin: 0 0 20px 0; color: #5b21b6; text-align: center; font-size: 1.5em;">⚔️ 장착 중인 장비 ⚔️</h3>')
            lines.append('  <div style="display: grid; gap: 12px;">')

            current_slot_type = None
            slot_count = {"🎯 주무기": 1, "🛡️ 보조무기": 1, "💍 장신구": 1}

            for item in equipment_slots:
                slot = item["slot"]
                tech = item["tech"]
                tier = tech["tier"]

                # 슬롯 타입이 바뀔 때마다 헤더 표시
                if current_slot_type != slot:
                    if current_slot_type is not None:
                        lines.append('    <div style="height: 8px;"></div>')
                    current_slot_type = slot

                slot_num = slot_count[slot]
                slot_count[slot] += 1

                # 장비 아이템 박스
                lines.append(f'    <div style="background: white; border: 2px solid {tier["color"]}; border-radius: 8px; padding: 15px; box-shadow: 0 2px 4px {tier["glow"]};">')
                lines.append(f'      <div style="display: flex; align-items: center; justify-content: space-between;">')
                lines.append(f'        <div style="display: flex; align-items: center; gap: 10px; flex: 1;">')
                lines.append(f'          <span style="font-size: 1.8em;">{tech["icon"]}</span>')
                lines.append(f'          <div style="flex: 1;">')
                lines.append(f'            <div style="font-weight: bold; color: #1f2937; font-size: 1.1em;">{slot} #{slot_num - 1}</div>')
                lines.append(f'            <div style="color: #6b7280; font-size: 0.95em; margin-top: 2px;">{tech["weapon_name"]}</div>')
                lines.append(f'          </div>')
                lines.append(f'        </div>')
                lines.append(f'        <div style="text-align: right;">')
                lines.append(f'          <div style="background: {tier["color"]}; color: white; padding: 4px 12px; border-radius: 12px; font-size: 0.85em; font-weight: bold; white-space: nowrap;">{tier["prefix"]} {tier["name"]}</div>')
                lines.append(f'          <div style="color: {tier["color"]}; font-weight: bold; font-size: 1.1em; margin-top: 4px;">{tech["percentage"]:.1f}%</div>')
                lines.append(f'        </div>')
                lines.append(f'      </div>')
                lines.append(f'    </div>')

            lines.append('  </div>')
            lines.append('</div>')
            lines.append("")
        else:
            lines.append("_장비를 장착하지 않았습니다._")
            lines.append("")

        # ============================================
        # 📊 전체 무기 목록 (카테고리별 분류)
        # ============================================
        lines.append("### 📊 무기 및 장비 인벤토리")
        lines.append("")
        lines.append("> 한 해 동안 사용한 모든 기술의 상세 통계")
        lines.append("")

        # 카테고리별 테이블 생성
        categories_to_display = [
            ("language", "🎯 주무기 (프로그래밍 언어)", categorized_tech["language"]),
            ("framework", "🛡️ 보조무기 (프레임워크 & 라이브러리)", categorized_tech["framework"]),
            ("tool", "💍 장신구 (도구, DB, 인프라)", categorized_tech["tool"]),
        ]

        for category_key, category_title, tech_list in categories_to_display:
            if not tech_list:
                continue

            lines.append(f"#### {category_title}")
            lines.append("")

            # 테이블 데이터 구성
            headers = ["순위", "아이콘", "장비명", "등급", "사용 횟수", "비율", "강화도"]
            rows = []

            for idx, tech in enumerate(tech_list[:15], 1):  # 카테고리별 상위 15개
                tier = tech["tier"]
                percentage = tech["percentage"]

                # 강화도 프로그레스 바
                progress_bar = f'<div style="background: #e5e7eb; border-radius: 4px; height: 20px; width: 100%; max-width: 200px;"><div style="background: {tier["color"]}; height: 100%; width: {percentage}%; border-radius: 4px; box-shadow: 0 0 10px {tier["glow"]};"></div></div>'

                # 등급 배지
                tier_badge = f'<span style="background: {tier["color"]}; color: white; padding: 4px 10px; border-radius: 12px; font-size: 0.85em; font-weight: bold; white-space: nowrap;">{tier["prefix"]} {tier["name"]}</span>'

                rows.append([
                    f"#{idx}",
                    f'<span style="font-size: 1.5em;">{tech["icon"]}</span>',
                    f'<strong>{tech["weapon_name"]}</strong><br><span style="color: #6b7280; font-size: 0.9em;">({tech["name"]})</span>',
                    tier_badge,
                    f'{tech["count"]:,}회',
                    f'<strong style="color: {tier["color"]};">{percentage:.1f}%</strong>',
                    progress_bar
                ])

            # HTML 테이블 렌더링
            lines.extend(GameRenderer.render_html_table(
                headers=headers,
                rows=rows,
                title="",
                description="",
                striped=True
            ))
            lines.append("")

        # Unknown 카테고리도 있으면 표시
        if categorized_tech["unknown"]:
            lines.append("#### 🔹 기타 기술")
            lines.append("")

            headers = ["순위", "기술명", "등급", "사용 횟수", "비율", "강화도"]
            rows = []

            for idx, tech in enumerate(categorized_tech["unknown"][:10], 1):
                tier = tech["tier"]
                percentage = tech["percentage"]

                progress_bar = f'<div style="background: #e5e7eb; border-radius: 4px; height: 20px; width: 100%; max-width: 200px;"><div style="background: {tier["color"]}; height: 100%; width: {percentage}%; border-radius: 4px;"></div></div>'
                tier_badge = f'<span style="background: {tier["color"]}; color: white; padding: 4px 10px; border-radius: 12px; font-size: 0.85em; font-weight: bold;">{tier["prefix"]} {tier["name"]}</span>'

                rows.append([
                    f"#{idx}",
                    f"**{tech['name']}**",
                    tier_badge,
                    f'{tech["count"]:,}회',
                    f'{percentage:.1f}%',
                    progress_bar
                ])

            lines.extend(GameRenderer.render_html_table(
                headers=headers,
                rows=rows,
                title="",
                description="",
                striped=True
            ))
            lines.append("")

        # ============================================
        # 📈 기술 스택 통계 요약
        # ============================================
        lines.append("### 📈 기술 스택 다양성 분석")
        lines.append("")

        diversity_stats = f"""
**📊 기술 통계**
- 🎯 주무기 (언어): {len(categorized_tech["language"])}개
- 🛡️ 보조무기 (프레임워크): {len(categorized_tech["framework"])}개
- 💍 장신구 (도구): {len(categorized_tech["tool"])}개
- 🔹 기타: {len(categorized_tech["unknown"])}개
- ⚡ **총 기술 스택**: {len(tech_stack)}개

**🏆 다양성 평가**
"""

        tech_count = len(tech_stack)
        if tech_count >= 20:
            diversity_stats += "- 💎 **전설급 다재다능**: 매우 다양한 기술 스택을 활용하고 있습니다!"
        elif tech_count >= 15:
            diversity_stats += "- ⚔️ **마스터 레벨**: 폭넓은 기술 스택을 보유하고 있습니다!"
        elif tech_count >= 10:
            diversity_stats += "- 🗡️ **숙련자 레벨**: 균형잡힌 기술 스택을 가지고 있습니다."
        elif tech_count >= 5:
            diversity_stats += "- 🔪 **성장 중**: 핵심 기술에 집중하고 있습니다."
        else:
            diversity_stats += "- 🔧 **전문가 지향**: 특정 기술에 깊이 있게 집중하고 있습니다."

        lines.extend(GameRenderer.render_info_box(
            title="🎯 기술 스택 종합 평가",
            content=diversity_stats.strip(),
            emoji="📊",
            bg_color="#f0f9ff",
            border_color="#3b82f6"
        ))

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
            (min(total_prs / 80, 1) * 50) +  # PR volume - 기준 상향
            (min(total_repos / 15, 1) * 30) +  # Repository diversity - 기준 상향
            0  # Base score - 기준 하향 (20->0)
        ))

        # 2. Productivity - based on commit count
        productivity = min(100, int(
            (min(total_commits / 300, 1) * 60) +  # Commit volume - 기준 상향
            (min(total_activity / 500, 1) * 40)  # Total activity - 기준 상향
        ))

        # 3. Collaboration - based on number of repositories
        collaboration = min(100, int(
            (min(total_repos / 8, 1) * 40) +  # Repository count - 기준 상향
            (min(total_prs / 50, 1) * 40) +  # PR engagement - 기준 상향
            0  # Base score - 기준 하향 (20->0)
        ))

        # 4. Consistency - based on activity distribution
        consistency = min(100, int(
            (min(total_activity / 300, 1) * 50) +  # Overall activity - 기준 상향
            10  # Base score - 기준 하향 (30->10)
        ))

        # 5. Growth - based on improvement indicators
        repos_with_growth = len([r for r in repository_analyses if r.growth_indicators])
        growth = min(100, int(
            30 +  # Base growth score - 기준 하향 (50->30)
            (min(repos_with_growth / len(repository_analyses) if repository_analyses else 0, 1) * 70)  # 보너스 증대 (50->70)
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
        if stats.get("consistency", 0) >= 85:  # 기준 상향 (80->85)
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
