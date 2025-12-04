"""Awards, game elements, and reporting configuration."""

from __future__ import annotations

# =============================================================================
# Reporter Categories and Labels
# =============================================================================

# Award categories for organizing achievements
AWARD_CATEGORIES = {
    'basic': '🎖️ 기본 성취',
    'speed': '⚡ 속도 & 효율성',
    'collaboration': '🤝 협업 & 리뷰',
    'quality': '🎯 품질 & 안정성',
    'special': '🎨 특별 기여',
    'top_honors': '👑 최고 영예',
}

# Keywords for categorizing awards
AWARD_KEYWORDS = {
    'basic': ['다이아몬드', '플래티넘', '골드', '실버', '브론즈'],
    'speed': ['번개', '속도', '스프린터', '스피드', '스프린트', '머신', '광속', '생산성'],
    'collaboration': ['협업', '리뷰', '멘토', '팀', '지식 전파', '감시자', '챔피언', '전파자', '매니아', '광신도'],
    'quality': ['품질', '안정', '테스트', '버그', '수호자', '지킴이', '머지', '옹호자', '스쿼셔'],
    'special': ['문서', '리팩터링', '기능', '빅뱅', '미세', '아키텍트', '빌더', '건축가', '화산', '공장', '영웅'],
    'top_honors': ['르네상스', '다재다능', '올라운더', '일관성의 왕', '균형', '불멸', '전설', '정복자', '얼리버드', '나이트'],
}

# Table of contents sections
TOC_SECTIONS = [
    ('📊 Executive Summary', '한눈에 보는 핵심 지표'),
    ('🏆 Awards Cabinet', '획득한 어워드'),
    ('✨ Growth Highlights', '성장 하이라이트'),
    ('📈 Monthly Trends', '월별 활동 트렌드'),
    ('💡 Detailed Feedback', '상세 피드백'),
    ('🎯 Spotlight Examples', '주요 기여 사례'),
    ('💻 Tech Stack', '기술 스택 분석'),
    ('🤝 Collaboration', '협업 네트워크'),
    ('🤔 Reflection', '회고 질문'),
    ('📊 Detailed Metrics', '상세 메트릭'),
    ('🔗 Evidence', '증거 링크'),
]

# Feedback section configurations
FEEDBACK_SECTIONS = {
    'commit': {
        'title': '### 📝 Commit Messages',
        'emoji': '✅',
        'metrics_label': '지표',
        'value_label': '값',
    },
    'pr_title': {
        'title': '### 🔀 PR Titles',
        'emoji': '✅',
        'metrics_label': '지표',
        'value_label': '값',
    },
    'review_tone': {
        'title': '### 👀 Review Tone',
        'emoji': '✅',
        'metrics_label': '지표',
        'value_label': '값',
    },
    'issue': {
        'title': '### 🐛 Issue Quality',
        'emoji': '✅',
        'metrics_label': '지표',
        'value_label': '값',
    },
}

# =============================================================================
# Game Elements Configuration
# =============================================================================

# 게임 컨셉 가이드라인:
# - 종합 보고서 (Year in Review): 강한 게임 은유 (던전/퀘스트/경험치) + 99레벨 시스템
# - 개별 보고서 (Review Reporter): 중간 게임 요소 (스킬/레벨) + 티어 시스템
# - 일반 보고서 (Reporter): 약한 게임 요소 (스탯만) + 티어 시스템

# 99레벨 시스템 (종합 보고서용)
LEVEL_99_TITLES = [
    (500, 99, "전설의 코드마스터", "👑"),
    (300, 80, "그랜드마스터", "💎"),
    (150, 60, "마스터", "🏆"),
    (75, 40, "전문가", "⭐"),
    (30, 20, "숙련자", "💫"),
    (10, 10, "초보자", "🌱"),
    (0, 1, "견습생", "✨"),
]

# 티어 시스템 (개별/일반 보고서용)
TIER_SYSTEM = [
    (90, 6, "그랜드마스터", "👑"),
    (75, 5, "마스터", "🏆"),
    (60, 4, "전문가", "⭐"),
    (40, 3, "숙련자", "💎"),
    (20, 2, "견습생", "🎓"),
    (0, 1, "초보자", "🌱"),
]

# 특성 타이틀 매핑
SPECIALTY_TITLES = {
    "코드 품질": "코드 아키텍트",
    "협업력": "팀 플레이어",
    "문제 해결력": "문제 해결사",
    "생산성": "스피드 러너",
    "성장성": "라이징 스타",
}

# 스탯 이모지 매핑
STAT_EMOJIS = {
    "code_quality": "💻",
    "collaboration": "🤝",
    "problem_solving": "🧩",
    "productivity": "⚡",
    "consistency": "📅",
    "growth": "📈",
}

# 스탯 한글 이름
STAT_NAMES_KR = {
    "code_quality": "코드 품질",
    "collaboration": "협업력",
    "problem_solving": "문제 해결력",
    "productivity": "생산성",
    "consistency": "꾸준함",
    "growth": "성장성",
}

# 스킬 타입 이모지
SKILL_TYPE_EMOJIS = {
    "패시브": "🟢",
    "액티브": "🔵",
    "성장중": "🟡",
    "미습득": "🔴",
}

# 뱃지 임계값
BADGE_THRESHOLDS = {
    # 스탯 기반 뱃지 (80 이상)
    'stat_threshold': 80,

    # 활동량 기반 뱃지
    'commit_marathon': 200,
    'commit_active': 100,
    'pr_master': 50,
    'pr_contributor': 20,
    'repo_multiverse': 10,
    'repo_crawler': 5,
}

# =============================================================================
# Skill & Mastery Configuration
# =============================================================================

# Skill mastery calculation
SKILL_MASTERY = {
    # Award-based skill mastery
    'base_mastery': 100,  # Starting mastery for top awards
    'mastery_reduction_per_rank': 10,  # Reduction per award rank
    'highlight_mastery': 80,  # Mastery for skills from highlights

    # Skill name formatting
    'skill_name_max_length': 60,  # Maximum characters for skill names
    'max_top_awards_for_skills': 3,  # Number of top awards to convert to skills
    'max_skills_total': 5,  # Maximum total skills to display

    # Communication skill quality thresholds
    'excellent_quality_ratio': 0.8,  # >= 80% is excellent
    'good_quality_ratio': 0.6,  # >= 60% is good
    'acceptable_quality_ratio': 0.4,  # >= 40% is acceptable
}

# =============================================================================
# Stat Calculation Weights
# =============================================================================

# Code Quality stat calculation weights (review_reporter.py)
STAT_WEIGHTS_CODE_QUALITY = {
    'strength_contribution': 50,  # Max points from strength ratio
    'file_organization': 25,  # Max points from file organization
    'experience_bonus': 25,  # Max points from PR experience
    'experience_pr_threshold': 10,  # PRs needed for full experience bonus
    'optimal_files_per_pr': 10,  # Optimal average files per PR
}

# Collaboration stat calculation weights
STAT_WEIGHTS_COLLABORATION = {
    'review_engagement': 50,  # Max points from review engagement
    'feedback_quality': 30,  # Max points from feedback quality
    'participation_bonus': 20,  # Max points from participation
    'participation_pr_threshold': 5,  # PRs needed for full participation bonus
    'optimal_feedback_per_pr': 5,  # Optimal average feedback points per PR
}

# Problem Solving stat calculation weights
STAT_WEIGHTS_PROBLEM_SOLVING = {
    'change_complexity': 40,  # Max points from code changes
    'scope_breadth': 30,  # Max points from file scope
    'problem_count': 30,  # Max points from PR count
    'problem_pr_threshold': 8,  # PRs needed for full problem count bonus
    'optimal_changes_per_pr': 500,  # Optimal average changes per PR
    'optimal_files_per_pr': 15,  # Optimal average files per PR for scope
}

# Productivity stat calculation weights
STAT_WEIGHTS_PRODUCTIVITY = {
    'pr_count': 40,  # Max points from PR volume
    'code_output': 35,  # Max points from code additions
    'file_coverage': 25,  # Max points from file coverage
    'optimal_pr_count': 20,  # Optimal total PRs
    'optimal_additions': 5000,  # Optimal total additions
    'optimal_file_count': 100,  # Optimal total files
}

# Growth stat calculation weights
STAT_WEIGHTS_GROWTH = {
    'base_growth': 50,  # Base growth score
    'improvement_trend': 30,  # Max points from improvement trend
    'consistency_bonus': 20,  # Max points from consistency
    'consistency_pr_threshold': 15,  # PRs needed for full consistency bonus
    'min_prs_for_trend': 4,  # Minimum PRs to calculate trend
    'new_developer_base': 40,  # Base score for developers with < 4 PRs
    'new_developer_multiplier': 60,  # Multiplier for PR count (< 4 PRs)
}
