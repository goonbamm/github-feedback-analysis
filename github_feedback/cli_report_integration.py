"""Report integration functionality for CLI."""

from __future__ import annotations

import json
import re
from datetime import datetime
from pathlib import Path
from typing import Optional

from .console import Console

console = Console()


def extract_section_content(content: str, section_header: str, next_section_prefix: str = "##") -> str:
    """Extract content of a specific section from markdown.

    Args:
        content: Full markdown content
        section_header: Header to look for (e.g., "## 🏆 Awards Cabinet")
        next_section_prefix: Prefix for next section (default "##")

    Returns:
        Extracted section content or empty string if not found
    """
    # Escape special regex characters in header
    escaped_header = re.escape(section_header)

    # Find section start
    pattern = rf'^{escaped_header}\s*$'
    match = re.search(pattern, content, re.MULTILINE)
    if not match:
        return ""

    start_pos = match.end()

    # Find next section of same or higher level
    next_section_pattern = rf'^{re.escape(next_section_prefix)} '
    next_match = re.search(next_section_pattern, content[start_pos:], re.MULTILINE)

    if next_match:
        end_pos = start_pos + next_match.start()
        return content[start_pos:end_pos].strip()

    return content[start_pos:].strip()


def create_executive_summary(brief_content: str, feedback_content: str, output_dir: Path) -> str:
    """Create executive summary from brief and feedback reports.

    Args:
        brief_content: Brief report content
        feedback_content: Feedback report content
        output_dir: Output directory to find personal_development.json

    Returns:
        Executive summary markdown section
    """
    lines = ["## 🎯 한눈에 보기 (Executive Summary)", ""]
    lines.append("> 핵심 성과와 개선 포인트를 빠르게 파악하세요")
    lines.append("")

    # Extract key achievements from brief (awards section)
    awards_section = extract_section_content(brief_content, "## 🏆 Awards Cabinet")
    if awards_section:
        # Count total awards
        award_matches = re.findall(r'\|\s*[^|]+\s*\|\s*([^|]+)\s*\|', awards_section)
        total_awards = len([m for m in award_matches if m.strip() and m.strip() not in ['어워드', '-----']])
        if total_awards > 0:
            lines.append(f"**🏆 획득 어워드**: {total_awards}개")

    # Extract highlights from brief
    highlights_section = extract_section_content(brief_content, "## ✨ Growth Highlights")
    if highlights_section:
        highlight_matches = re.findall(r'\|\s*\d+\s*\|\s*([^|]+)\s*\|', highlights_section)
        if highlight_matches and len(highlight_matches) > 0:
            lines.append("")
            lines.append("**✨ 주요 성과 Top 3:**")
            for i, highlight in enumerate(highlight_matches[:3], 1):
                lines.append(f"{i}. {highlight.strip()}")

    # Extract improvement areas from personal development
    personal_dev_path = output_dir / "reviews" / "_temp_personal_dev.json"
    # Try to find personal_development.json in reviews subdirectories
    reviews_dir = output_dir / "reviews"
    if reviews_dir.exists():
        for repo_dir in reviews_dir.iterdir():
            if repo_dir.is_dir():
                pd_path = repo_dir / "personal_development.json"
                if pd_path.exists():
                    personal_dev_path = pd_path
                    break

    if personal_dev_path.exists():
        try:
            with open(personal_dev_path, "r", encoding="utf-8") as f:
                pd_data = json.load(f)

            improvements = pd_data.get("improvement_areas", [])[:2]
            if improvements:
                lines.append("")
                lines.append("**💡 주요 개선점 Top 2:**")
                for i, imp in enumerate(improvements, 1):
                    category = imp.get("category", "")
                    desc = imp.get("description", "")
                    lines.append(f"{i}. **{category}**: {desc}")

            # Extract next focus areas
            next_focus = pd_data.get("next_focus_areas", [])[:3]
            if next_focus:
                lines.append("")
                lines.append("**🎯 다음 집중 영역:**")
                for i, focus in enumerate(next_focus, 1):
                    lines.append(f"{i}. {focus}")
        except (json.JSONDecodeError, OSError):
            pass

    lines.append("")
    lines.append("---")
    lines.append("")
    return "\n".join(lines)


def create_improved_toc() -> str:
    """Create improved table of contents with better structure."""
    lines = ["## 📑 목차", ""]

    sections = [
        ("1", "🎯 한눈에 보기", "핵심 성과와 개선점 요약"),
        ("2", "🏆 주요 성과", "어워드와 성장 하이라이트"),
        ("3", "💡 개선 피드백", "장점, 보완점, 실행 계획"),
        ("4", "📊 상세 분석", "월별 트렌드, 기술 스택, 협업, 회고"),
        ("5", "📝 부록", "개별 PR 리뷰 및 상세 사례"),
    ]

    for num, title, desc in sections:
        lines.append(f"{num}. **{title}** - {desc}")

    lines.append("")
    lines.append("---")
    lines.append("")
    return "\n".join(lines)


def read_feedback_report(feedback_report_path: Path) -> str:
    """Read feedback report with comprehensive error handling.

    Args:
        feedback_report_path: Path to feedback report file

    Returns:
        Feedback report content

    Raises:
        RuntimeError: If file operations fail
    """
    try:
        with open(feedback_report_path, "r", encoding="utf-8") as f:
            return f.read()
    except FileNotFoundError:
        console.print(f"[warning]Feedback report not found at {feedback_report_path}[/]")
        return "_Feedback report not available._"
    except PermissionError as exc:
        console.print(f"[warning]Permission denied reading {feedback_report_path}[/]")
        raise RuntimeError(f"Permission denied reading feedback report: {exc}") from exc
    except OSError as exc:
        console.print(f"[warning]Error reading feedback report: {exc}[/]")
        raise RuntimeError(f"Failed to read feedback report: {exc}") from exc


def extract_sections_from_brief(brief_content: str) -> dict[str, str]:
    """Extract all key sections from brief report.

    Args:
        brief_content: Brief report markdown content

    Returns:
        Dictionary mapping section names to content
    """
    return {
        "awards": extract_section_content(brief_content, "## 🏆 Awards Cabinet"),
        "highlights": extract_section_content(brief_content, "## ✨ Growth Highlights"),
        "monthly_trends": extract_section_content(brief_content, "## 📈 Monthly Trends"),
        "feedback": extract_section_content(brief_content, "## 💡 Detailed Feedback"),
        "retrospective": extract_section_content(brief_content, "## 🔍 Deep Retrospective Analysis"),
        "tech_stack": extract_section_content(brief_content, "## 💻 Tech Stack Analysis"),
        "collaboration": extract_section_content(brief_content, "## 🤝 PR 활동 요약"),
        "witch": extract_section_content(brief_content, "## 🔮 마녀의 독설"),
    }


def extract_sections_from_feedback(feedback_content: str) -> dict[str, str]:
    """Extract all key sections from feedback report.

    Args:
        feedback_content: Feedback report markdown content

    Returns:
        Dictionary mapping section names to content
    """
    return {
        "personal_dev": extract_section_content(feedback_content, "## 👤 개인 성장 분석"),
        "strengths": extract_section_content(feedback_content, "## ✨ 장점"),
        "improvements": extract_section_content(feedback_content, "## 💡 보완점"),
        "growth": extract_section_content(feedback_content, "## 🌱 올해 성장한 점"),
    }


def build_integrated_report_content(
    repo_name: str,
    exec_summary: str,
    toc: str,
    brief_sections: dict[str, str],
    feedback_sections: dict[str, str],
) -> str:
    """Build integrated report content from extracted sections.

    Args:
        repo_name: Repository name
        exec_summary: Executive summary content
        toc: Table of contents content
        brief_sections: Sections extracted from brief report
        feedback_sections: Sections extracted from feedback report

    Returns:
        Complete integrated report markdown content
    """
    return f"""# 📊 {repo_name} 통합 분석 보고서

> 레포지토리 전체 분석과 PR 리뷰를 통합한 종합 보고서입니다.

{exec_summary}

{toc}

## 2. 🏆 주요 성과

> 이번 기간 동안 달성한 어워드와 성장 하이라이트

### 🏅 획득 어워드

{brief_sections.get('awards') or "_어워드 정보가 없습니다._"}

### ✨ 성장 하이라이트

{brief_sections.get('highlights') or "_하이라이트 정보가 없습니다._"}

---

## 3. 💡 개선 피드백

> 구체적인 장점, 보완점, 실행 가능한 제안

{feedback_sections.get('personal_dev') or "_개인 성장 분석 정보가 없습니다._"}

### 🔮 마녀의 독설

{brief_sections.get('witch') or "_마녀의 독설 인사이트가 없습니다._"}

### 코드 품질 피드백

{brief_sections.get('feedback') or "_상세 피드백 정보가 없습니다._"}

---

## 4. 📊 상세 분석

> 데이터 기반의 심층 분석 (필요한 섹션을 클릭하여 펼쳐보세요)

<details>
<summary><b>📈 월별 활동 트렌드</b> (클릭하여 펼치기)</summary>

{brief_sections.get('monthly_trends') or "_월별 트렌드 정보가 없습니다._"}

</details>

<details>
<summary><b>💻 기술 스택 분석</b> (클릭하여 펼치기)</summary>

{brief_sections.get('tech_stack') or "_기술 스택 정보가 없습니다._"}

</details>

<details>
<summary><b>🤝 협업 분석</b> (클릭하여 펼치기)</summary>

{brief_sections.get('collaboration') or "_협업 정보가 없습니다._"}

</details>

<details>
<summary><b>🔍 심층 회고</b> (클릭하여 펼치기)</summary>

{brief_sections.get('retrospective') or "_회고 분석 정보가 없습니다._"}

</details>

---

## 5. 📝 부록

> 개별 PR 리뷰 및 상세 사례 (필요시 펼쳐보세요)

<details>
<summary><b>📝 상세 사례</b> (클릭하여 펼치기)</summary>

{feedback_sections.get('growth') or ""}

{feedback_sections.get('strengths') or ""}

{feedback_sections.get('improvements') or ""}

</details>

---

<div align="center">

*Generated by GitHub Feedback Analysis Tool*
*Report generated on: {datetime.now().strftime("%Y-%m-%d %H:%M:%S")}*

</div>
"""


def write_integrated_report(output_dir: Path, content: str) -> Path:
    """Write integrated report to file with comprehensive error handling.

    Args:
        output_dir: Output directory
        content: Report content to write

    Returns:
        Path to written report file

    Raises:
        RuntimeError: If file operations fail
    """
    from .utils import FileSystemManager

    try:
        FileSystemManager.ensure_directory(output_dir)
    except PermissionError as exc:
        raise RuntimeError(
            f"Permission denied creating directory {output_dir}: {exc}"
        ) from exc
    except OSError as exc:
        raise RuntimeError(
            f"Failed to create directory {output_dir}: {exc}"
        ) from exc

    integrated_report_path = output_dir / "integrated_full_report.md"

    # Validate path before writing
    if integrated_report_path.exists() and not integrated_report_path.is_file():
        raise RuntimeError(
            f"Cannot write to {integrated_report_path}: path exists but is not a file"
        )

    try:
        with open(integrated_report_path, "w", encoding="utf-8") as f:
            f.write(content)
    except PermissionError as exc:
        raise RuntimeError(
            f"Permission denied writing to {integrated_report_path}: {exc}"
        ) from exc
    except OSError as exc:
        # Check for specific errors
        if exc.errno == 28:  # ENOSPC - No space left on device
            raise RuntimeError(
                f"No space left on device while writing to {integrated_report_path}"
            ) from exc
        raise RuntimeError(
            f"Failed to write integrated report to {integrated_report_path}: {exc}"
        ) from exc

    return integrated_report_path


def generate_integrated_full_report(
    output_dir: Path,
    repo_name: str,
    brief_content: str,
    feedback_report_path: Path,
) -> Path:
    """Generate an improved integrated report with better UX.

    Args:
        output_dir: Output directory for the integrated report
        repo_name: Repository name in owner/repo format
        brief_content: Brief report markdown content (from memory)
        feedback_report_path: Path to the feedback integrated report markdown file

    Returns:
        Path to the generated integrated report

    Raises:
        RuntimeError: If file operations fail
    """
    # Read feedback report
    feedback_content = read_feedback_report(feedback_report_path)

    # Extract sections
    brief_sections = extract_sections_from_brief(brief_content)
    feedback_sections = extract_sections_from_feedback(feedback_content)

    # Create components
    exec_summary = create_executive_summary(brief_content, feedback_content, output_dir)
    toc = create_improved_toc()

    # Build integrated content
    integrated_content = build_integrated_report_content(
        repo_name=repo_name,
        exec_summary=exec_summary,
        toc=toc,
        brief_sections=brief_sections,
        feedback_sections=feedback_sections,
    )

    # Write to file
    return write_integrated_report(output_dir, integrated_content)
