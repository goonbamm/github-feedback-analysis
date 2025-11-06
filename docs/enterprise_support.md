# GitHub Enterprise 호환성 검증 보고서

## 개요
사내 전용 GitHub Enterprise(Server) 환경에서 `github-feedback-analysis` CLI가 정상적으로 동작할 수 있는지 코드와 동작 경로를 기반으로 검증했습니다. 현재 리포지토리는 실제 GitHub API 연동 대신 더미 데이터를 반환하는 초기 프로토타입 구조를 사용하고 있으며, 다음과 같은 한계가 식별되었습니다.

## 주요 확인 사항

1. **실제 GitHub API 호출 미구현**  
   - `Collector.collect()`는 저장소 이름을 기반으로 한 결정적 더미 수치를 생성할 뿐 API 요청을 전혀 수행하지 않습니다.【F:github_feedback/collector.py†L15-L54】  
   - 따라서 GitHub Enterprise 도메인을 포함해 어떤 GitHub 인스턴스에도 연결되지 않으며, PAT를 입력해도 인증이 사용되지 않습니다.

2. **GitHub Enterprise 호스트 구성 옵션 부재**  
   - 구성 파일 모델(`Config`, `AuthConfig`)에는 PAT 외에 API 베이스 URL이나 GraphQL/REST 엔드포인트를 설정할 필드가 존재하지 않습니다.【F:github_feedback/config.py†L13-L77】  
   - CLI 명령(`gf init`, `gf analyze`)에서도 Enterprise 전용 호스트를 지정하거나 HTTPS 인증서를 제어하는 옵션이 제공되지 않습니다.【F:github_feedback/cli.py†L31-L135】

3. **보고서 링크가 github.com 도메인에 고정**  
   - 분석 결과의 증거 링크는 `https://github.com/{repo}` 형식으로 하드코딩되어 있어 Enterprise 전용 도메인을 반영하지 못합니다.【F:github_feedback/analyzer.py†L43-L63】

4. **PDF/리포트 생성은 로컬에서만 동작**  
   - 보고서 생성(`Reporter`)은 로컬 파일 시스템에 의존하므로 Enterprise 환경과 무관하게 동작하지만, 핵심 데이터 수집이 이루어지지 않아 유의미한 결과를 얻을 수 없습니다.【F:github_feedback/reporter.py†L19-L119】

## 결론
현 시점의 `github-feedback-analysis`는 실제 GitHub API 연동이 구현되어 있지 않고, Enterprise 서버를 대상으로 한 호스트/인증 설정도 제공하지 않습니다. 따라서 사내 GitHub Enterprise 환경에서는 **분석 기능을 수행할 수 없습니다**. Enterprise 호환성을 확보하려면 다음이 필요합니다.

- REST/GraphQL 호출 구현과 오류 처리, PAT 기반 인증 로직 추가
- 구성 파일 및 CLI 옵션에 Enterprise 전용 호스트(URL)와 인증 설정을 확장
- 분석 결과에서 사용하는 증거 링크를 구성 가능한 베이스 URL로 전환

위 개선 사항이 적용되기 전까지 본 도구는 데모용 더미 리포트 생성에만 사용할 수 있습니다.
