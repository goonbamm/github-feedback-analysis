"""연말 결산 보고서 생성 - 여러 저장소를 종합하여 게임 캐릭터 테마로 시각화합니다.

이 모듈은 backward compatibility를 위해 유지됩니다.
실제 구현은 year_in_review/ 패키지로 분리되었습니다.
"""

# Backward compatibility: Re-export from refactored modules
from .year_in_review import (
    EQUIPMENT_SLOTS,
    RepositoryAnalysis,
    TECH_CATEGORIES,
    TECH_CUSTOM_ICONS,
    WEAPON_TIERS,
    YearInReviewReporter,
)

__all__ = [
    "YearInReviewReporter",
    "RepositoryAnalysis",
    "TECH_CATEGORIES",
    "TECH_CUSTOM_ICONS",
    "WEAPON_TIERS",
    "EQUIPMENT_SLOTS",
]
