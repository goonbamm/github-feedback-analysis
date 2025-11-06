# GitHub Feedback Analysis

GitHub Feedback Analysis는 GitHub 저장소의 활동 데이터를 수집하고, 핵심 지표를 계산하며, 요약 리포트를 자동으로 만들어주는 CLI 도구입니다. 한 번의 명령으로 저장소를 분석하고, 마크다운 및 PDF 보고서를 받아볼 수 있습니다. GitHub.com뿐 아니라 GitHub Enterprise(Server) 환경에서도 API 엔드포인트만 지정하면 동일한 플로우로 동작합니다.

## 주요 기능

- `gf init` : GitHub Personal Access Token(PAT)과 기본 분석 옵션을 `~/.config/github_feedback/config.toml`에 저장합니다.
- `gf analyze` : 지정한 저장소의 활동을 수집하고 지표를 계산한 뒤 `reports/` 디렉터리에 보고서를 생성합니다.
- `gf report` : 최근에 저장된 지표(`reports/metrics.json`)를 활용해 보고서를 다시 생성합니다.
- `gf suggest-templates` : PR 템플릿 등 저장소 거버넌스에 도움이 되는 기본 파일을 만들어줍니다.

## 설치 방법

```bash
git clone https://github.com/<your-account>/github-feedback-analysis.git
cd github-feedback-analysis
pip install -e .
```

위 명령을 실행하면 현재 파이썬 환경에서 `gf` CLI를 사용할 수 있습니다.

## 빠른 시작

### 1. 초기 설정 (`gf init`)

```bash
gf init
```

실행 시 CLI가 다음 옵션을 입력받습니다.

| 옵션 | 기본값 | 설명 |
| --- | --- | --- |
| `--pat` | (필수) | GitHub PAT. 명령 실행 중 프롬프트에서 안전하게 입력합니다. |
| `--months` | `12` | 기본 분석 기간(개월). 나중에 `gf analyze`에서 별도 지정하지 않으면 이 값이 사용됩니다. |
| `--api-url` | `https://api.github.com` | REST API 베이스 URL. GitHub Enterprise(Server)의 경우 `https://<host>/api/v3` 형태로 입력합니다. |
| `--graphql-url` | `https://api.github.com/graphql` | GraphQL 엔드포인트 URL. Enterprise 기본값은 `https://<host>/api/graphql`입니다. |
| `--web-url` | `https://github.com` | 보고서에서 링크를 생성할 때 사용할 웹 URL. Enterprise 웹 UI 주소로 변경하세요. |
| `--verify-ssl` | `True` | Enterprise 환경에서 사설 인증서를 사용할 경우 `False`로 비활성화할 수 있습니다. |
| `--llm-endpoint` | `http://localhost:8000/v1/chat/completions` | 추후 AI 분석에 사용할 LLM 엔드포인트 주소. |
| `--llm-model` | 빈 문자열 | 기본 LLM 모델 ID. 필요 시만 입력합니다. |

저장된 설정은 `gf show-config`로 언제든 확인할 수 있으며, PAT은 마스킹되어 노출되지 않습니다.

### 2. 저장소 분석 (`gf analyze`)

```bash
gf analyze --repo octocat/Hello-World --months 6 --include-branch main --include-language py
```

자주 사용하는 주요 옵션은 다음과 같습니다.

| 옵션 | 기본값 | 설명 |
| --- | --- | --- |
| `--repo` | (필수) | `owner/repo` 형식의 GitHub 저장소 식별자. |
| `--months` | 설정값 | 분석 기간(개월). 지정하지 않으면 `gf init`에서 저장한 기본값을 사용합니다. |
| `--include-branch` | 없음 | 특정 브랜치만 포함하고 싶을 때 사용합니다. 여러 브랜치를 분석하려면 명령을 반복 실행하세요. |
| `--exclude-branch` | 없음 | 지정한 브랜치를 제외합니다. |
| `--include-path` | 없음 | 특정 경로(프리픽스)만 분석에 포함합니다. 예: `src/`. |
| `--exclude-path` | 없음 | 특정 경로를 제외합니다. |
| `--include-language` | 없음 | 파일 확장자 기반으로 언어를 필터링합니다. 예: `py`, `ts`. |
| `--include-bots` | `False` | 기본적으로 봇 커밋은 제외되며, 이 옵션을 주면 포함합니다. |
| `--generate-pdf` | `True` | PDF 보고서 생성 여부. `--generate-pdf False`로 설정하면 마크다운만 생성합니다. |

분석이 완료되면 다음 파일이 생성됩니다.

- `reports/report.md` : 상세 분석 보고서 (마크다운)
- `reports/report.pdf` : PDF 버전 보고서 (옵션)
- `reports/metrics.json` : 계산된 지표의 원본 데이터

### 3. 보고서 재생성 (`gf report`)

```bash
gf report --formats md,pdf
```

`reports/metrics.json`이 존재할 때 사용할 수 있으며, `--formats` 옵션으로 생성할 포맷을 선택합니다.

- `md` : 마크다운 보고서만 생성
- `pdf` : PDF 보고서만 생성
- `md,pdf` : 둘 다 생성 (기본값)

### 4. 템플릿 생성 (`gf suggest-templates`)

```bash
gf suggest-templates
```

명령을 실행한 디렉터리에 다음과 같은 템플릿 파일이 생성됩니다.

- `pull_request_template.md`
- `REVIEW_GUIDE.md`
- `CONTRIBUTING.md`

## 추가 팁

- `gf show-config` 명령으로 현재 설정을 빠르게 확인할 수 있습니다.
- PAT에는 최소 `repo`, `read:org`, `read:user` 권한이 있어야 안정적으로 메트릭을 수집할 수 있습니다.
- 대용량 저장소를 분석할 때는 GitHub API 속도 제한에 주의하세요. 너무 큰 기간을 한 번에 요청하면 시간이 오래 걸릴 수 있습니다.

## GitHub Enterprise 사용 가이드

사내 GitHub Enterprise(Server) 인스턴스에서도 다음 설정만 맞추면 동일한 CLI 워크플로우를 사용할 수 있습니다.

1. `gf init` 실행 시 `--api-url`, `--graphql-url`, `--web-url`을 Enterprise 도메인에 맞게 입력합니다.
   - 예시) `gf init --api-url https://github.example.com/api/v3 --graphql-url https://github.example.com/api/graphql --web-url https://github.example.com`
2. 사설 인증서를 사용한다면 `--verify-ssl False` 옵션을 지정하세요. (가능하다면 내부 신뢰 저장소에 루트 인증서를 배포하는 것을 권장합니다.)
3. Enterprise 인스턴스에서 발급한 PAT를 사용하고, 필요한 OAuth 권한(`repo`, `read:org`, `read:user`)을 부여합니다.

동일한 설정은 `~/.config/github_feedback/config.toml`에서 수동으로 수정할 수도 있습니다. 보다 자세한 작동 원리와 호환성 점검 내용은 [`docs/enterprise_support.md`](docs/enterprise_support.md)에서 확인할 수 있습니다.

## 개발 환경

테스트 및 개발에 필요한 의존성을 설치하고, 단위 테스트를 실행하려면 다음 명령을 활용하세요.

```bash
pip install -e .[test]
pytest
```

## 라이선스

MIT License
