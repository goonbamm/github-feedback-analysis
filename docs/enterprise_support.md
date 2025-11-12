# GitHub Enterprise 호환성 검증 보고서

## 개요
`github-feedback-analysis`는 이제 GitHub Enterprise(Server) 환경을 정식 지원합니다. PAT 기반 인증을 포함해 REST/GraphQL 엔드포인트, 웹 UI 주소를 자동으로 구성하며, 실시간으로 GitHub API를 호출해 지표를 계산합니다. 아래는 코드 수준 검증 결과입니다.

## 주요 확인 사항

1. **Enterprise 호스트 자동 구성 지원**
   - 설정 모델에 `ServerConfig`가 추가되어 REST API, GraphQL, 웹 URL을 저장합니다.【F:github_feedback/config.py†L13-L88】
   - `gfa init` 명령의 Enterprise 호스트 프롬프트에 한 번만 입력해도 각 URL이 자동으로 채워지며, 설정 파일(`~/.config/github_feedback/config.toml`)에 즉시 반영됩니다.【F:github_feedback/cli.py†L42-L104】

2. **PAT 기반 인증과 실제 데이터 수집**
   - `Collector`는 초기화 시 PAT가 없으면 오류를 발생시키며, `requests.Session`에 `Authorization: Bearer <PAT>` 헤더를 설정합니다.【F:github_feedback/collector.py†L16-L46】
   - 커밋, PR, 리뷰, 이슈를 GitHub REST API로 페이지네이션하면서 수집하며, Enterprise 엔드포인트로도 동일하게 동작합니다.【F:github_feedback/collector.py†L48-L175】
   - 봇 계정 필터링, 브랜치 한정, 리뷰 시점 필터링 등을 통해 Enterprise 저장소에서도 동일한 품질의 데이터를 제공합니다.【F:github_feedback/collector.py†L117-L175】

3. **보고서 링크의 호스트 커스터마이징**
   - 분석기는 구성된 웹 베이스 URL을 사용해 증거 링크를 생성합니다. Enterprise UI 주소가 자동으로 반영됩니다.【F:github_feedback/analyzer.py†L14-L41】

4. **테스트 기반 보장**
   - 새로 추가된 단위 테스트는 수집기 로직이 봇 계정을 제외하고 각 리소스를 정확히 집계하는지 검증합니다.【F:tests/test_collector.py†L1-L53】

## Enterprise 환경 체크리스트

1. `gfa init` 실행 시 프롬프트에서 Enterprise 호스트를 입력하거나 `--enterprise-host https://<host>` 옵션을 사용하면 API/GraphQL/Web URL이 한 번에 구성됩니다.【F:github_feedback/cli.py†L56-L100】
2. Enterprise에서 발급한 PAT에 `repo`, `read:org`, `read:user` 권한을 부여합니다.【F:README.md†L133-L147】

상세 사용법은 [README](../README.md#github-enterprise-사용-가이드)를 참고하세요.
