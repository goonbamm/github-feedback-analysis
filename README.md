# GitHub Feedback Analysis

GitHub 저장소의 활동을 분석하고 인사이트를 담은 보고서를 자동으로 생성하는 CLI 도구입니다. GitHub.com과 GitHub Enterprise 환경을 지원하며, LLM을 활용한 자동 리뷰 기능을 제공합니다.

## 주요 기능
- 저장소의 커밋, 이슈, 리뷰 활동을 기간별로 집계하고 분석
- LLM 기반 상세 피드백 보고서 자동 생성
- 인증된 사용자의 PR 자동 리뷰 및 통합 회고 보고서 생성

## 준비물
- Python 3.11 이상
- [uv](https://docs.astral.sh/uv/) 또는 선호하는 패키지 매니저
- GitHub Personal Access Token (비공개 저장소는 `repo`, 공개 저장소는 `public_repo` 권한 필요)

## 설치
```bash
git clone https://github.com/goonbamm/github-feedback-analysis.git
cd github-feedback-analysis
uv venv
source .venv/bin/activate
uv pip install -e .
```

## 빠른 시작
1. `gf init` - PAT와 LLM 설정 저장
2. `gf brief --repo owner/name` - 저장소 분석 및 보고서 생성
3. `reports/` 폴더에서 `metrics.json`과 `report.md` 확인

## 명령어

### `gf init`
GitHub 접속 정보와 LLM 설정을 저장합니다.

```bash
gf init
```

주요 옵션:
- `--pat`: GitHub Personal Access Token (필수)
- `--months`: 기본 분석 기간 (기본값: 12개월)
- `--enterprise-host`: GitHub Enterprise 호스트 주소
- `--llm-endpoint`: LLM API 엔드포인트 (필수)
- `--llm-model`: LLM 모델 식별자 (필수)

### `gf brief`
저장소를 분석하고 상세 피드백 보고서를 생성합니다.

```bash
gf brief --repo owner/name
```

자동으로 다음을 수행합니다:
- 커밋, 이슈, PR, 리뷰 활동 집계
- LLM 기반 상세 피드백 분석 (커밋 메시지, PR 제목, 리뷰 톤, 이슈 품질)
- `reports/` 디렉터리에 `metrics.json`, `report.md` 생성

### `gf feedback`
인증된 사용자의 PR을 자동으로 리뷰하고 통합 회고 보고서를 생성합니다.

```bash
gf feedback --repo owner/name --state open
```

주요 옵션:
- `--repo`: 저장소 식별자 (필수)
- `--state`: PR 상태 필터 (`open`, `closed`, `all`, 기본값: `all`)

실행 과정:
1. PAT로 인증된 사용자가 작성한 PR 검색
2. 각 PR에 대해 LLM 기반 리뷰 생성 (`reviews/` 디렉터리에 저장)
3. 전체 PR을 아우르는 통합 회고 보고서 생성

### `gf show-config`
현재 저장된 설정을 확인합니다.

```bash
gf show-config
```

## 설정 파일
`~/.config/github_feedback/config.toml`에 저장되며, `gf init` 실행 시 자동으로 생성됩니다.

```toml
[auth]
pat = "<set>"

[server]
api_url = "https://api.github.com"
graphql_url = "https://api.github.com/graphql"
web_url = "https://github.com"

[llm]
endpoint = "http://localhost:8000/v1/chat/completions"
model = "gpt-5-codex"

[defaults]
months = 12
```

## 생성되는 파일
- `reports/metrics.json` - 분석 지표 원본 데이터
- `reports/report.md` - 마크다운 보고서
- `reviews/<owner>_<repo>/pr-<번호>/` - PR 리뷰 결과
  - `artefacts.json` - PR 원본 데이터
  - `review_summary.json` - LLM 리뷰 요약
  - `review.md` - 마크다운 리뷰 초안
- `reviews/<owner>_<repo>/integrated_report.md` - 통합 회고 보고서

## 개발
```bash
uv pip install -e .[test]
pytest
```
