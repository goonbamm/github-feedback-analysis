# 🚀 GitHub Feedback Analysis

GitHub Feedback Analysis는 조직이나 팀의 저장소 활동을 수집해 핵심 지표와 인사이트가 담긴 마크다운 보고서를 자동으로 만들어 주는 CLI 도구입니다. GitHub.com과 GitHub Enterprise(Server) 환경 모두에서 동일하게 사용할 수 있으며, LLM을 활용한 자동 리뷰 요약 기능도 제공합니다.

## 📚 목차
- [✨ 무엇을 할 수 있나요?](#-무엇을-할-수-있나요)
- [✅ 준비물](#-준비물)
- [🛠️ 설치](#️-설치)
- [🚀 빠른 시작](#-빠른-시작)
- [📦 명령어 요약](#-명령어-요약)
- [🧭 명령어 상세 가이드](#-명령어-상세-가이드)
- [🔐 설정 파일 구조](#-설정-파일-구조)
- [📝 생성되는 산출물](#-생성되는-산출물)
- [🧪 개발자 가이드](#-개발자-가이드)

## ✨ 무엇을 할 수 있나요?
- 저장소의 커밋, 이슈, 리뷰 활동량을 기간별로 집계합니다.
- PR, 코드 리뷰, 하이라이트 등의 서사를 자동으로 요약한 보고서를 생성합니다.
- 최신 메트릭을 재활용해 빠르게 보고서를 다시 만들 수 있습니다.
- 특정 브랜치, 경로, 언어만 포함하거나 봇 활동을 제외하도록 세밀하게 필터링할 수 있습니다.
- 개별 Pull Request에 대한 맥락과 리뷰 초안을 자동으로 수집할 수 있습니다.

## ✅ 준비물
- Python 3.11 이상
- [uv](https://docs.astral.sh/uv/) 또는 선호하는 패키지 매니저 (설치 예시는 uv 기준)
- GitHub Personal Access Token
  - 공개 저장소만 분석한다면 `public_repo`
  - 비공개 저장소까지 포함하려면 `repo`
  - 조직 정보를 함께 분석하려면 `read:org`

## 🛠️ 설치
```bash
git clone https://github.com/goonbamm/github-feedback-analysis.git
cd github-feedback-analysis
uv venv
source .venv/bin/activate
uv pip install -e .
```

테스트 의존성까지 설치하려면 `uv pip install -e .[test]`를 실행하세요.

## 🚀 빠른 시작
1. **초기 설정:** `gf init`을 실행해 PAT와 기본 옵션을 저장합니다. 모든 값을 옵션으로 넘기면 비대화형으로도 사용할 수 있습니다.
2. **데이터 수집 및 분석:** `gf analyze --repo owner/name`으로 분석을 수행합니다.
3. **보고서 확인:** 기본 경로인 `reports/` 폴더에서 `metrics.json`과 `report.md` 파일을 확인합니다.
4. **보고서 재생성:** 지표가 이미 있다면 `gf report`로 같은 데이터를 즉시 다시 생성할 수 있습니다.

## 📦 명령어 요약
| 명령 | 설명 |
| --- | --- |
| `gf init` | PAT와 서버/LLM 정보를 포함한 기본 설정을 저장합니다. |
| `gf analyze` | 저장소 데이터를 수집하고 보고서를 생성합니다. |
| `gf report` | 저장된 지표(`reports/metrics.json`)로 보고서를 다시 만듭니다. |
| `gf show-config` | 현재 저장된 설정을 확인합니다. 민감 정보는 마스킹됩니다. |
| `gf review` | 특정 PR의 변경 파일, 리뷰, 댓글을 모아 LLM 리뷰 초안을 생성합니다. |

## 🧭 명령어 상세 가이드
### `gf init`
GitHub 접속 정보와 기본 분석 옵션을 설정합니다. 처음 실행하면 필요한 값을 순서대로 묻습니다.

```bash
gf init
```

| 옵션 | 기본값 | 설명 |
| --- | --- | --- |
| `--pat TEXT` | (필수) | GitHub Personal Access Token. 인자가 없으면 안전하게 입력하도록 프롬프트가 뜹니다. |
| `--months INTEGER` | `12` | 기본 분석 기간(개월). 분석 시 별도 입력이 없으면 이 값이 사용됩니다. |
| `--enterprise-host TEXT` | `github.com` | GitHub Enterprise 호스트 주소. 입력하면 REST/GraphQL/Web URL이 자동으로 채워집니다. |
| `--llm-endpoint TEXT` | (필수) | 리뷰 생성에 사용할 LLM API 엔드포인트. |
| `--llm-model TEXT` | (필수) | 사용할 LLM 모델 식별자. |

CI나 자동화 스크립트에서 사용하고 싶다면 모든 옵션을 명시적으로 전달하면 프롬프트 없이 실행됩니다. 예시는 다음과 같습니다.

```bash
gf init \
  --pat ghp_xxxxxxxxxxxxxxxxxxxx \
  --enterprise-host https://github.example.com \
  --llm-endpoint https://llm.internal/api/v1/chat/completions \
  --llm-model gpt-5-codex
```

### `gf analyze`
지정한 저장소의 최근 활동을 수집하고 보고서를 생성하는 핵심 명령입니다.

```bash
gf analyze --repo owner/name
```

필터 옵션은 반복해서 지정할 수 있으며, 지정하지 않으면 전체 데이터를 대상으로 합니다.

| 옵션 | 기본값 | 설명 |
| --- | --- | --- |
| `--repo owner/name` | (필수) | 분석할 저장소. `owner/name` 형식으로 입력합니다. |
| `--months N` | 설정값 또는 `12` | 분석 기간(개월). |
| `--include-branch NAME` | 전체 | 포함할 브랜치 이름. 여러 개 입력하려면 옵션을 반복합니다. |
| `--exclude-branch NAME` | 없음 | 제외할 브랜치 이름. 여러 개 반복 입력 가능. |
| `--include-path PATH/` | 전체 | 포함할 경로 접두사. 여러 개 반복 입력 가능. |
| `--exclude-path PATH/` | 없음 | 제외할 경로 접두사. 여러 개 반복 입력 가능. |
| `--include-language EXT` | 전체 | 포함할 파일 확장자(예: `py`). 여러 개 반복 입력 가능. |
| `--include-bots` | 봇 제외 | 옵션을 지정하면 봇 활동도 포함합니다. 기본은 봇 제외입니다. |
| `--output-dir PATH` | `reports` | 지표와 보고서를 저장할 디렉터리. 경로가 없으면 자동으로 생성됩니다. |

#### 자주 쓰는 예시
```bash
# 최근 6개월 동안 Python 파일만 분석
gf analyze --repo owner/name --months 6 --include-language py

# 특정 브랜치와 경로에 한정하여 분석
gf analyze --repo owner/name --include-branch develop --include-path src/ --include-path docs/

# 여러 저장소를 순차적으로 분석하고 결과를 개별 폴더로 보관
gf analyze --repo owner/name --output-dir reports/owner-name
gf analyze --repo another/name --output-dir reports/another-name
```

분석이 완료되면 기본적으로 `reports/metrics.json`과 `reports/report.md`가 생성되고, 터미널에 하이라이트가 요약되어 출력됩니다. `--output-dir`를 사용하면 해당 경로 아래에 동일한 파일 구조가 만들어집니다.

### `gf report`
이전에 저장한 지표로 기본 보고서를 다시 생성합니다.

```bash
gf report --output-dir reports/owner-name
```

지정한 디렉터리(기본값은 `reports`)에서 `metrics.json`을 찾아 `report.md`/`report.html`을 다시 생성합니다. 템플릿을 변경하고 싶다면 `github_feedback/reporter.py`를 수정하거나 별도의 스크립트에서 `MetricSnapshot`을 활용하세요.

### `gf show-config`
현재 저장된 설정을 확인합니다. PAT 등 민감한 값은 `<set>` 형태로 마스킹됩니다.

```bash
gf show-config
```

### `gf review`
특정 PR의 리뷰 맥락을 수집하고 LLM을 통해 요약/리뷰 초안을 생성합니다.

```bash
gf review --repo owner/name --number 123
```

- `repo`: 저장소 식별자
- `number`: 리뷰할 PR 번호

결과로 PR 메타데이터, 리뷰 요약, 마크다운 리뷰 초안이 `reviews/` 디렉터리에 저장됩니다.

## 🔐 설정 파일 구조
- 저장 경로: `~/.config/github_feedback/config.toml`
- `gf init` 실행 시 자동으로 생성/갱신됩니다.
- 직접 편집해도 되지만, 형식 오류가 나면 로드에 실패하니 주의하세요.

구성은 다음과 같이 나뉩니다.
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

## 📝 생성되는 산출물
- `reports/metrics.json`: 분석 지표의 원본 데이터. `gf report`가 참조합니다.
- `reports/report.md`: 주요 지표와 하이라이트가 담긴 마크다운 보고서.
- `reviews/`: `gf review` 실행 시 PR 맥락(`artefact.json`), 요약(`summary.json`), 리뷰 초안(`review.md`)이 저장됩니다.

## 🧪 개발자 가이드
```bash
uv pip install -e .[test]
pytest
```

테스트는 네트워크 호출이 아닌 더미 요청으로 구성되어 있어 오프라인에서도 실행할 수 있습니다. 새로운 기능을 추가할 때는 CLI 동작과 페이징 로직에 대한 테스트를 함께 업데이트해 주세요.

문제가 생기면 [이슈](https://github.com/goonbamm/github-feedback-analysis/issues)에 남겨주세요.
