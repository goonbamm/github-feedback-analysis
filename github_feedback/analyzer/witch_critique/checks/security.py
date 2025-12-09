"""Security awareness checker for witch critique."""

from __future__ import annotations

from typing import List, TYPE_CHECKING

if TYPE_CHECKING:
    from github_feedback.models import CollectionResult, WitchCritiqueItem

from github_feedback.models import WitchCritiqueItem


class SecurityChecker:
    """Check security awareness in development practices."""

    @staticmethod
    def check_security_awareness(collection, critiques: List[WitchCritiqueItem]) -> None:
        """Check if developer shows security awareness."""
        if not collection.pull_request_examples:
            return

        # Check for security-related PRs
        security_keywords = ['security', 'auth', 'permission', 'encrypt', 'sanitize',
                           'xss', 'csrf', 'injection', '보안', '인증', '권한', 'vulnerable']
        security_prs = [pr for pr in collection.pull_request_examples
                       if any(kw in pr.title.lower() for kw in security_keywords)]

        # If no security PRs among many PRs (suggests lack of security thinking)
        if len(collection.pull_request_examples) > 20 and len(security_prs) == 0:
            critiques.append(
                WitchCritiqueItem(
                    category="보안 인식",
                    severity="🔥 치명적",
                    critique=f"{len(collection.pull_request_examples)}개 PR 중 보안 관련이 하나도 없어? SQL Injection, XSS 뭔지 알아? 사용자 입력 믿고 그대로 쓰고 있지?",
                    evidence=f"{len(collection.pull_request_examples)}개 PR 중 보안 관련 0개",
                    consequence="해킹, 데이터 유출, 법적 책임, 회사 망함, 경력 끝, 뉴스 헤드라인.",
                    remedy="OWASP Top 10 공부. 입력 검증 필수. Prepared Statement. HTTPS. 비밀번호 해싱. 정기 보안 업데이트."
                )
            )

    @staticmethod
    def check_dependency_updates(collection, critiques: List[WitchCritiqueItem]) -> None:
        """Check for dependency management and updates."""
        if not collection.pull_request_examples:
            return

        # Check for dependency update PRs
        dep_keywords = ['dependency', 'dependencies', 'upgrade', 'bump', 'update',
                       'package', 'npm', 'yarn', 'pip', 'requirements', '의존성']
        dep_prs = [pr for pr in collection.pull_request_examples
                  if any(kw in pr.title.lower() for kw in dep_keywords)]

        # If very few dependency updates
        if len(collection.pull_request_examples) > 15 and len(dep_prs) < 2:
            critiques.append(
                WitchCritiqueItem(
                    category="의존성 관리",
                    severity="⚡ 심각",
                    critique=f"의존성 업데이트 PR이 {len(dep_prs)}개? 낡은 라이브러리 쓰면서 '잘 돌아가니까 괜찮다'고 생각해? 보안 취약점 쌓이고 있어.",
                    evidence=f"{len(collection.pull_request_examples)}개 PR 중 의존성 업데이트 {len(dep_prs)}개",
                    consequence="보안 취약점, 레거시 종속, 나중에 업그레이드 불가능, 해킹 위험.",
                    remedy="Dependabot/Renovate 활성화. 정기적 업데이트. 보안 알림 모니터링. npm audit/pip check."
                )
            )

    @staticmethod
    def check_secrets_management(collection, critiques: List[WitchCritiqueItem]) -> None:
        """Warn about potential secrets management issues."""
        if not collection.pull_request_examples:
            return

        # Check for environment/config related PRs
        config_keywords = ['config', 'env', 'secret', 'key', 'token', 'credential', '설정', 'password']
        config_prs = [pr for pr in collection.pull_request_examples
                     if any(kw in pr.title.lower() for kw in config_keywords)]

        # Give general advice if there's config activity
        if len(config_prs) > 3:
            critiques.append(
                WitchCritiqueItem(
                    category="비밀 정보 관리",
                    severity="💀 위험",
                    critique=f"설정 관련 PR이 {len(config_prs)}개나 있는데... API 키 하드코딩 안 했지? .env 파일 커밋 안 했지? 비밀번호 평문으로 안 넣었지?",
                    evidence=f"{len(config_prs)}개의 설정 관련 PR 발견",
                    consequence="비밀키 유출, AWS 크레딧 탈취, 데이터베이스 노출, 회사 파산, 법적 소송.",
                    remedy=".env를 .gitignore에. 환경 변수 사용. Vault/Secret Manager. Git history 스캔. Pre-commit hook."
                )
            )
