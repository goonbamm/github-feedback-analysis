"""헤더 섹션 생성 - 보고서 상단의 타이틀 및 요약 정보."""

from __future__ import annotations

from datetime import datetime
from typing import List

from ...game_elements import GameRenderer


def generate_header(
    year: int, username: str, total_repos: int, total_prs: int, total_commits: int
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


__all__ = ["generate_header"]
