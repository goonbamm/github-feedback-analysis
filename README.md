# 🚀 GitHub Feedback Analysis

GitHub Feedback Analysis는 GitHub 저장소의 활동 데이터를 수집하고, 핵심 지표를 계산하며, 요약 리포트를 자동으로 만들어주는 CLI 도구입니다. 한 번의 명령으로 저장소를 분석하고, 마크다운 보고서를 받아볼 수 있습니다. GitHub.com뿐 아니라 GitHub Enterprise(Server) 환경에서도 API 엔드포인트만 지정하면 동일한 플로우로 동작합니다.

## ✨ 주요 기능

- `gf init` : GitHub Personal Access Token(PAT)과 기본 분석 옵션을 `~/.config/github_feedback/config.toml`에 저장합니다.
- `gf analyze` : 지정한 저장소의 활동을 수집하고 지표를 계산한 뒤 `reports/` 디렉터리에 보고서를 생성합니다.
- `gf report` : 최근에 저장된 지표(`reports/metrics.json`)를 활용해 보고서를 다시 생성합니다.
- `gf suggest-templates` : PR 템플릿 등 저장소 거버넌스에 도움이 되는 기본 파일을 만들어줍니다.

## 🔍 어떻게 작동하나요?

GitHub Feedback Analysis는 크게 세 단계로 저장소 활동을 이해합니다.

1. **수집(Collector)**: `gf analyze` 명령을 실행하면 저장된 PAT과 Enterprise 설정을 바탕으로 GitHub REST/GraphQL API에서 커밋, 풀 리퀘스트, 리뷰, 이슈 데이터를 가져옵니다. 브랜치·경로·언어 필터로 원하는 범위를 좁힐 수도 있습니다.
2. **분석(Analyzer)**: 수집된 활동 데이터를 사용해 기여자별 커밋 수, 리뷰 응답 속도, 머지 리드타임 등 핵심 지표를 계산하고, 구성된 웹 URL을 활용해 증거 링크를 만듭니다.
3. **보고(Reporter)**: 계산된 지표는 `reports/metrics.json`에 저장되며, 마크다운 템플릿을 통해 읽기 쉬운 리포트로 변환됩니다. LLM 관련 설정을 채워 두면 향후 AI 기반 인사이트 기능과도 연동할 수 있습니다.

모든 과정은 로컬에서 수행되며 `~/.config/github_feedback/config.toml`에 저장된 자격 증명과 기본 옵션을 재사용합니다.

## 🛠️ 설치 방법

### uv (격리된 가상환경 권장)

```bash
git clone https://github.com/<your-account>/github-feedback-analysis.git
cd github-feedback-analysis
uv venv
source .venv/bin/activate
uv pip install -e .
```

테스트 의존성까지 포함하려면 `uv pip install -e .[test]`를 실행하세요. `uv`는 `pip`와 호환되는 인터페이스를 제공하며, 필요한 의존성(`tomli` 등)을 자동으로 설치합니다.

위 명령을 실행하면 현재 파이썬 환경에서 `gf` CLI를 사용할 수 있습니다.

## 🚦 빠른 시작

### 1. 초기 설정 (`gf init`)

```bash
gf init
```

실행 시 CLI가 다음 옵션을 입력받습니다.

| 옵션 | 기본값 | 설명 |
| --- | --- | --- |
| `--pat` | (필수) | GitHub PAT. 명령 실행 중 프롬프트에서 안전하게 입력합니다. |
| `--months` | `12` | 기본 분석 기간(개월). 나중에 `gf analyze`에서 별도 지정하지 않으면 이 값이 사용됩니다. |
| `--enterprise-host` | 없음 | GitHub Enterprise(Server) 기본 웹 주소. 프롬프트에서 바로 입력하거나, GitHub.com을 사용할 경우 Enter로 건너뛰면 됩니다. 입력하면 아래 URL 옵션이 자동으로 채워집니다. |
| `--api-url` | `https://api.github.com` | REST API 베이스 URL. GitHub Enterprise(Server)의 경우 `https://<host>/api/v3` 형태로 입력합니다. |
| `--graphql-url` | `https://api.github.com/graphql` | GraphQL 엔드포인트 URL. Enterprise 기본값은 `https://<host>/api/graphql`입니다. |
| `--web-url` | `https://github.com` | 보고서에서 링크를 생성할 때 사용할 웹 URL. Enterprise 웹 UI 주소로 변경하세요. |
| `--verify-ssl` | `True` | Enterprise 환경에서 사설 인증서를 사용할 경우 `False`로 비활성화할 수 있습니다. |
| `--llm-endpoint` | `http://localhost:8000/v1/chat/completions` | 추후 AI 분석에 사용할 LLM 엔드포인트 주소. |
| `--llm-model` | 빈 문자열 | 기본 LLM 모델 ID. 필요 시만 입력합니다. |

초기화 과정에서는 PAT과 Enterprise 호스트를 차례대로 질문합니다. 기본 GitHub.com을 사용한다면 Enterprise 호스트 프롬프트에서 Enter만 누르면 됩니다. 호스트를 입력하거나 `--enterprise-host` 옵션으로 지정하면 `--api-url`, `--graphql-url`, `--web-url` 값을 별도로 입력하지 않아도 됩니다. 저장된 설정은 `gf show-config`로 언제든 확인할 수 있으며, PAT은 마스킹되어 노출되지 않습니다.

#### 예시 시나리오

가상의 인물 **이지은**이 가상의 회사 **네오브릿지(NeoBridge)** 의 GitHub Enterprise 인스턴스를 분석하려고 한다고 가정해 봅니다. Enterprise 주소가 `https://github.neobridge.example`라면 다음과 같이 초기 설정을 수행할 수 있습니다.

```bash
gf init --months 6 --enterprise-host https://github.neobridge.example --llm-model neobridge-insight
```

명령을 실행하면 PAT 입력 프롬프트가 표시됩니다. 이지은은 Enterprise에서 발급받은 토큰(예: `ghp_example1234...`)을 입력한 뒤 Enter를 누르면 설정이 저장되고, 이후 `gf analyze` 명령을 바로 사용할 수 있습니다.

### 2. 저장소 분석 (`gf analyze`)

```bash
gf analyze --repo octocat/Hello-World --months 6 --include-branch main --include-language py
```

`gf analyze`를 인자 없이 실행하면 `owner/repo` 형식의 저장소명을 프롬프트에서 바로 입력할 수 있습니다. 기본 분석 기간 역시 `gf init`에서 저장된 값을 사용하므로, 최소한의 정보만으로도 빠르게 리포트를 생성할 수 있습니다.

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
분석이 완료되면 다음 파일이 생성됩니다.

- `reports/report.md` : 상세 분석 보고서 (마크다운)
- `reports/metrics.json` : 계산된 지표의 원본 데이터

#### 예시 시나리오

앞서 초기 설정을 마친 **이지은**은 이제 사내 프로젝트 `neobridge/customer-insights` 저장소를 분석합니다. 기간은 기본값(6개월)을 사용하고, 언어 필터만 추가해 파이썬 파일 위주로 살펴보려 합니다.

```bash
gf analyze
# 프롬프트 예시: Repository to analyse (owner/name): neobridge/customer-insights

gf analyze --include-language py
```

첫 번째 명령에서 CLI는 저장소명을 물어보고, `gf init`에서 저장한 기본 기간으로 분석을 수행합니다. 이후 두 번째 명령처럼 필요할 때만 추가 옵션을 덧붙여도 됩니다. 분석이 완료되면 보고서 파일 경로가 콘솔에 표시되며, `reports/` 디렉터리에서 언제든지 결과를 확인할 수 있습니다.

### 3. 보고서 재생성 (`gf report`)

```bash
gf report
```

`reports/metrics.json`이 존재할 때 사용할 수 있으며, 캐시된 지표로 마크다운 보고서를 다시 생성합니다.

### 4. 템플릿 생성 (`gf suggest-templates`)

```bash
gf suggest-templates
```

명령을 실행한 디렉터리에 다음과 같은 템플릿 파일이 생성됩니다.

- `pull_request_template.md`
- `REVIEW_GUIDE.md`
- `CONTRIBUTING.md`

## 🔐 GitHub PAT 발급 가이드

GitHub Personal Access Token(PAT)은 API 호출을 인증하기 위한 비밀번호와 같습니다. 다음 절차를 따르면 누구나 쉽게 발급받을 수 있습니다.

1. GitHub.com 또는 사내 GitHub Enterprise 웹 사이트에 로그인합니다.
2. 우측 상단 프로필 사진을 클릭한 뒤 **Settings** → **Developer settings** → **Personal access tokens**로 이동합니다.
3. **Tokens (classic)**에서 **Generate new token**을 선택하고, 토큰 설명에 용도를 적어 둡니다. (예: `github-feedback-report`)
4. 만료 기간을 조직 정책에 맞게 설정합니다. 가능하면 주기적으로 갱신되는 기간을 선택하는 것이 안전합니다.
5. 다음 권한을 체크합니다.
   - `repo`
   - `read:org`
   - `read:user`
6. **Generate token**을 클릭한 뒤 표시된 토큰 값을 복사해 `gf init` 실행 시 입력합니다.

> ⚠️ 보안상 토큰은 한 번만 표시됩니다. 발급 직후 안전한 비밀 저장소(예: 1Password, Vault)에 보관하고, 채팅이나 이슈에 평문으로 남기지 마세요.

## 💡 추가 팁

- `gf show-config` 명령으로 현재 설정을 빠르게 확인할 수 있습니다.
- PAT에는 최소 `repo`, `read:org`, `read:user` 권한이 있어야 안정적으로 메트릭을 수집할 수 있습니다.
- 대용량 저장소를 분석할 때는 GitHub API 속도 제한에 주의하세요. 너무 큰 기간을 한 번에 요청하면 시간이 오래 걸릴 수 있습니다.

## 🏢 GitHub Enterprise 사용 가이드

사내 GitHub Enterprise(Server) 인스턴스에서도 다음 설정만 맞추면 동일한 CLI 워크플로우를 사용할 수 있습니다.

1. `gf init` 실행 시 프롬프트에서 Enterprise 호스트를 입력하거나 `--enterprise-host https://github.example.com` 옵션을 사용하면 API/GraphQL/Web URL이 자동으로 구성됩니다.
   - 세부 값을 직접 지정하고 싶다면 기존처럼 `--api-url`, `--graphql-url`, `--web-url` 옵션을 사용해도 됩니다.
2. 사설 인증서를 사용한다면 `--verify-ssl False` 옵션을 지정하세요. (가능하다면 내부 신뢰 저장소에 루트 인증서를 배포하는 것을 권장합니다.)
3. Enterprise 인스턴스에서 발급한 PAT를 사용하고, 필요한 OAuth 권한(`repo`, `read:org`, `read:user`)을 부여합니다.

동일한 설정은 `~/.config/github_feedback/config.toml`에서 수동으로 수정할 수도 있습니다. 보다 자세한 작동 원리와 호환성 점검 내용은 [`docs/enterprise_support.md`](docs/enterprise_support.md)에서 확인할 수 있습니다.

## 🧪 개발 환경

테스트 및 개발에 필요한 의존성을 설치하고, 단위 테스트를 실행하려면 다음 명령을 활용하세요.

```bash
uv pip install -e .[test]
pytest
```

## 📄 라이선스

MIT License
