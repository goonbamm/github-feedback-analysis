# 🚀 GitHub Feedback Analysis

개발자로서 피드백 받고 싶은데, 연말을 회고하고 싶은데 어떻게 해야 할지 모르겠다면? GitHub에서 **나의 활동**을 분석하고 인사이트를 담은 보고서를 자동으로 생성하는 CLI 도구입니다. GitHub.com과 GitHub Enterprise 환경을 지원하며, LLM을 활용한 자동 리뷰 기능을 제공합니다.

한국어 | [English](translations/README_EN.md) | [简体中文](translations/README_ZH.md) | [日本語](translations/README_JA.md) | [Español](translations/README_ES.md)

## ✨ 주요 기능

- 📊 **개인 활동 분석**: 특정 저장소에서 **나의** 커밋, 이슈, 리뷰 활동을 기간별로 집계하고 분석
- 🤖 **LLM 기반 피드백**: 나의 커밋 메시지, PR 제목, 리뷰 톤, 이슈 품질에 대한 상세 분석
- 🎯 **통합 회고 보고서**: 개인 활동 지표와 함께 종합적인 인사이트 제공
- 🎊 **연간 회고 (Year in Review)**: 올해 활동한 모든 저장소를 자동으로 분석하여 종합 연간 보고서 생성
- 🏆 **성과 시각화**: 나의 기여도에 따른 어워드 및 하이라이트 자동 생성
- 💡 **저장소 탐색**: 접근 가능한 저장소 목록 조회 및 활성 저장소 추천
- 🎨 **대화형 모드**: 저장소를 직접 선택할 수 있는 사용자 친화적 인터페이스

## 📋 준비물

- Python 3.11 이상
- [uv](https://docs.astral.sh/uv/) 또는 선호하는 패키지 매니저
- GitHub Personal Access Token
  - 비공개 저장소: `repo` 권한
  - 공개 저장소: `public_repo` 권한
- LLM API 엔드포인트 (OpenAI 호환 형식)

## 🔑 GitHub Personal Access Token 발급

<details>
<summary><b>📖 토큰 발급 방법 보기 (클릭하여 펼치기)</b></summary>

이 도구를 사용하려면 GitHub Personal Access Token(PAT)이 필요합니다.

### 발급 방법

1. **GitHub 설정 페이지 접속**
   - [GitHub Settings → Developer settings → Personal access tokens → Tokens (classic)](https://github.com/settings/tokens) 페이지로 이동
   - 또는: GitHub 프로필 → Settings → Developer settings → Personal access tokens

2. **새 토큰 생성**
   - "Generate new token" → "Generate new token (classic)" 클릭
   - Note: 토큰 용도 입력 (예: "GitHub Feedback Analysis")
   - Expiration: 만료 기간 설정 (권장: 90일 또는 Custom)

3. **권한 선택**
   - **공개 저장소만 분석**: `public_repo` 체크
   - **비공개 저장소 포함**: `repo` 전체 체크
   - 기타 권한은 선택하지 않아도 됩니다

4. **토큰 생성 및 복사**
   - "Generate token" 클릭
   - 생성된 토큰(ghp_로 시작)을 복사하여 안전하게 보관
   - ⚠️ **중요**: 이 페이지를 벗어나면 토큰을 다시 확인할 수 없습니다

5. **토큰 사용**
   - `gfa init` 실행 시 복사한 토큰을 입력하세요

### Fine-grained Personal Access Token 사용 (선택사항)

최신 fine-grained 토큰을 사용하려면:
1. [Personal access tokens → Fine-grained tokens](https://github.com/settings/personal-access-tokens/new) 페이지로 이동
2. Repository access: 분석할 저장소 선택
3. Permissions 설정:
   - **Contents**: Read-only (필수)
   - **Metadata**: Read-only (자동 선택됨)
   - **Pull requests**: Read-only (필수)
   - **Issues**: Read-only (필수)

### GitHub Enterprise 사용자를 위한 안내

사내 GitHub Enterprise를 사용하는 경우:
1. **Enterprise 서버의 토큰 페이지 접속**
   - `https://github.your-company.com/settings/tokens` (회사 도메인으로 변경)
   - 또는: 프로필 → Settings → Developer settings → Personal access tokens

2. **권한 설정은 동일**
   - 비공개 저장소: `repo` 권한
   - 공개 저장소: `public_repo` 권한

3. **초기 설정 시 Enterprise 호스트 지정**

   **인터랙티브 모드 (권장):**
   ```bash
   gfa init
   ```
   초기화 시 Enterprise 호스트 선택 메뉴가 표시됩니다:
   - 기본 github.com 선택
   - 예시 Enterprise 호스트 목록에서 선택
   - 저장된 커스텀 호스트에서 선택
   - 직접 URL 입력 (자동으로 저장 여부 확인)

   **CLI 옵션 사용:**
   ```bash
   gfa init --enterprise-host https://github.your-company.com
   ```

4. **저장된 Enterprise 호스트 관리**
   ```bash
   # 저장된 호스트 목록 보기
   gfa config hosts list

   # 새 호스트 추가
   gfa config hosts add https://github.your-company.com

   # 호스트 제거
   gfa config hosts remove https://github.your-company.com
   ```

5. **관리자 문의**
   - 일부 Enterprise 환경에서는 PAT 생성이 제한될 수 있습니다
   - 문제 발생 시 GitHub 관리자에게 문의하세요

### 참고 자료

- [GitHub 공식 문서: Personal Access Token 관리](https://docs.github.com/ko/authentication/keeping-your-account-and-data-secure/managing-your-personal-access-tokens)
- [GitHub 공식 문서: Fine-grained PAT](https://docs.github.com/ko/authentication/keeping-your-account-and-data-secure/managing-your-personal-access-tokens#fine-grained-personal-access-tokens)
- [GitHub Enterprise Server 문서](https://docs.github.com/en/enterprise-server@latest/authentication/keeping-your-account-and-data-secure/managing-your-personal-access-tokens)

</details>

## 🔧 설치

```bash
# 저장소 복사
git clone https://github.com/goonbamm/github-feedback-analysis.git
cd github-feedback-analysis

# 가상 환경 생성 및 활성화
uv venv
source .venv/bin/activate  # Windows: .venv\Scripts\activate

# 패키지 설치 (필요한 모든 의존성 자동 설치)
uv pip install -e .
```

## 🚀 빠른 시작

### 1️⃣ 설정 초기화

```bash
gfa init
```

대화형 프롬프트가 나타나면 다음 정보를 입력하세요:
- GitHub Personal Access Token
- LLM 엔드포인트 (예: `http://localhost:8000/v1/chat/completions`)
- LLM 모델 (예: `gpt-4`)
- GitHub Enterprise 호스트 (선택사항)
  - 번호로 선택하거나 직접 URL 입력 가능
  - 새로운 호스트를 입력하면 저장 여부를 물어봅니다

### 2️⃣ 개인 활동 분석

```bash
# 선택한 저장소 분석
gfa feedback

# 올해 전체 활동을 자동으로 분석 (Year in Review)
gfa feedback -y
```

추천 저장소 목록에서 선택하거나 직접 입력하여 **나의 활동**을 분석할 수 있습니다. `-y` 옵션을 사용하면 별도의 저장소 선택 없이 올해 활동한 모든 저장소를 모아 연간 회고 보고서를 바로 생성할 수 있습니다.

분석이 완료되면 `reports/` 디렉터리에 다음 파일들이 생성됩니다:
- `metrics.json` - 분석 데이터
- `report.md` - 마크다운 보고서
- `integrated_full_report.md` - **통합 보고서** (레포지토리 분석 + PR 리뷰를 하나로 통합)
- `prompts/` - LLM 프롬프트 파일들
- `reviews/` - 개별 PR 리뷰 및 개인 성장 분석

### 3️⃣ 결과 확인

```bash
cat reports/report.md
```

## 📚 명령어 상세 가이드

<details>
<summary><b>🎯 gfa init - 초기 설정</b></summary>

GitHub 접속 정보와 LLM 설정을 저장합니다.

#### 기본 사용법 (대화형)

```bash
gfa init
```

#### 예시: GitHub.com + 로컬 LLM 사용

```bash
gfa init \
  --pat ghp_xxxxxxxxxxxxxxxxxxxx \
  --llm-endpoint http://localhost:8000/v1/chat/completions \
  --llm-model gpt-4 \
  --months 12
```

#### 예시: GitHub Enterprise 사용

```bash
gfa init \
  --pat ghp_xxxxxxxxxxxxxxxxxxxx \
  --enterprise-host https://github.company.com \
  --llm-endpoint http://localhost:8000/v1/chat/completions \
  --llm-model gpt-4
```

#### 옵션 설명

| 옵션 | 설명 | 필수 | 기본값 |
|------|------|------|--------|
| `--pat` | GitHub Personal Access Token | ✅ | - |
| `--llm-endpoint` | LLM API 엔드포인트 | ✅ | - |
| `--llm-model` | LLM 모델 식별자 | ✅ | - |
| `--months` | 기본 분석 기간 (개월) | ❌ | 12 |
| `--enterprise-host` | GitHub Enterprise 호스트 | ❌ | github.com |
| `--test/--no-test` | LLM 연결 테스트 실행 여부 | ❌ | `--test` |

> LLM 엔드포인트가 아직 준비되지 않았다면 `gfa init --no-test` 옵션으로 연결 검증 단계를 건너뛸 수 있습니다.

</details>

<details>
<summary><b>📊 gfa feedback - 개인 활동 분석</b></summary>

특정 저장소에서 **나의 활동**을 분석하고 상세 피드백 보고서를 생성합니다.

> **중요**: 이 명령어는 인증된 사용자(PAT 소유자)의 개인 활동만 분석합니다. 저장소 전체가 아닌, **나의** 커밋, PR, 리뷰, 이슈만 수집하고 분석합니다.

#### 기본 사용법

```bash
gfa feedback --repo owner/repo-name
```

#### 대화형 모드

저장소를 직접 지정하지 않고 추천 목록에서 선택할 수 있습니다.

```bash
gfa feedback --interactive
```

또는

```bash
gfa feedback  # --repo 옵션 없이 실행
```

#### 예시

```bash
# 내가 기여한 공개 저장소 분석
gfa feedback --repo torvalds/linux

# 내가 기여한 개인 저장소 분석
gfa feedback --repo myusername/my-private-repo

# 🎊 연간 회고 보고서 (올해 활동한 모든 저장소 종합 분석)
gfa feedback --year-in-review

# 특정 연도의 회고 보고서
gfa feedback --year-in-review --year 2024

# 내가 기여한 조직 저장소 분석
gfa feedback --repo microsoft/vscode

# 대화형 모드로 저장소 선택
gfa feedback --interactive
```

#### 옵션 설명

| 옵션 | 설명 | 필수 | 기본값 |
|------|------|------|--------|
| `--repo`, `-r` | 저장소 (owner/name) | ❌ | - |
| `--output`, `-o` | 출력 디렉터리 | ❌ | reports |
| `--interactive`, `-i` | 대화형 저장소 선택 | ❌ | false |

#### 생성되는 보고서

분석이 완료되면 `reports/` 디렉터리에 다음 파일들이 생성됩니다:

```
reports/
├── metrics.json                     # 원본 데이터 (JSON)
├── report.md                        # 분석 보고서 (마크다운)
├── integrated_full_report.md        # 통합 보고서 (brief + PR 리뷰)
├── prompts/                         # LLM 프롬프트 파일들
│   ├── strengths_overview.txt
│   ├── collaboration_improvements.txt
│   └── ...
└── reviews/                         # PR 리뷰 (서브디렉토리)
    └── {repo_name}/
        ├── pr-{number}/
        │   ├── artefacts.json
        │   ├── review_summary.json
        │   └── review.md
        └── integrated_report.md
```

#### 분석 내용

- ✅ **활동 집계**: 나의 커밋, PR, 리뷰, 이슈 수 계산
- 🎯 **품질 분석**: 나의 커밋 메시지, PR 제목, 리뷰 톤, 이슈 설명 품질
- 🏆 **어워드**: 나의 기여도에 따른 자동 어워드 부여
- 📈 **트렌드**: 나의 월별 활동 추이 및 속도 분석
- 🤝 **협업 분석**: 나와 함께 작업한 협업자 네트워크
- 💻 **기술 스택**: 내가 작업한 파일의 언어 및 기술 분석

</details>

<details>
<summary><b>⚙️ gfa config - 설정 관리</b></summary>

설정을 확인하거나 수정합니다.

#### `gfa config show` - 설정 확인

현재 저장된 설정을 확인합니다.

```bash
gfa config show
```

**출력 예시:**

```
┌─────────────────────────────────────┐
│ GitHub Feedback Configuration       │
├─────────────┬───────────────────────┤
│ Section     │ Values                │
├─────────────┼───────────────────────┤
│ auth        │ pat = <set>           │
├─────────────┼───────────────────────┤
│ server      │ api_url = https://... │
│             │ web_url = https://... │
├─────────────┼───────────────────────┤
│ llm         │ endpoint = http://... │
│             │ model = gpt-4         │
└─────────────┴───────────────────────┘
```

> **참고:** `gfa show-config` 명령어는 deprecated되었으며 `gfa config show`로 대체되었습니다.

#### `gfa config set` - 설정 값 변경

개별 설정 값을 변경합니다.

```bash
gfa config set <key> <value>
```

**예시:**

```bash
# LLM 모델 변경
gfa config set llm.model gpt-4

# LLM 엔드포인트 변경
gfa config set llm.endpoint http://localhost:8000/v1/chat/completions

# 기본 분석 기간 변경
gfa config set defaults.months 6
```

#### `gfa config get` - 설정 값 조회

특정 설정 값을 조회합니다.

```bash
gfa config get <key>
```

**예시:**

```bash
# LLM 모델 확인
gfa config get llm.model

# 기본 분석 기간 확인
gfa config get defaults.months
```

</details>

<details>
<summary><b>🧹 gfa clear-cache - 캐시 초기화</b></summary>

GitHub API 응답을 빠르게 재사용할 수 있도록 CLI는 `~/.cache/github_feedback/api_cache.sqlite`에 결과를 저장합니다. 캐시가 손상되거나 오래된 데이터 때문에 문제가 발생할 경우 이 명령어로 캐시를 제거하고 새 데이터를 받아올 수 있습니다.

#### 기본 사용법

```bash
gfa clear-cache
```

#### 사용 시나리오

- `sqlite3.OperationalError` 등 캐시 파일 관련 오류가 발생할 때
- 최신 활동이 반영되지 않아 강제로 새 데이터를 받고 싶을 때
- 트러블슈팅 가이드에서 캐시 초기화를 권장할 때

명령어 실행 후 다음 `gfa feedback` 호출 시 GitHub API에서 데이터를 다시 가져옵니다.

</details>

<details>
<summary><b>🔍 gfa list-repos - 저장소 목록</b></summary>

접근 가능한 저장소 목록을 조회합니다.

```bash
gfa list-repos
```

#### 예시

```bash
# 저장소 목록 조회 (기본: 최근 업데이트순 20개)
gfa list-repos

# 정렬 기준 변경
gfa list-repos --sort stars --limit 10

# 특정 조직 저장소만 조회
gfa list-repos --org myorganization

# 생성일순으로 정렬
gfa list-repos --sort created --limit 50
```

#### 옵션 설명

| 옵션 | 설명 | 기본값 |
|------|------|--------|
| `--sort`, `-s` | 정렬 기준 (updated, created, pushed, full_name) | updated |
| `--limit`, `-l` | 최대 표시 개수 | 20 |
| `--org`, `-o` | 조직 이름으로 필터링 | - |

</details>

<details>
<summary><b>💡 gfa suggest-repos - 저장소 추천</b></summary>

분석하기 좋은 활성 저장소를 추천합니다.

```bash
gfa suggest-repos
```

최근 활동이 활발한 저장소를 자동으로 선별하여 추천합니다. Stars, forks, 이슈 수, 최근 업데이트 등을 종합적으로 고려합니다.

#### 예시

```bash
# 기본 추천 (최근 90일 이내 활동, 10개)
gfa suggest-repos

# 최근 30일 이내 활동한 저장소 5개 추천
gfa suggest-repos --limit 5 --days 30

# Stars 순으로 정렬
gfa suggest-repos --sort stars

# 활동 점수 기준으로 정렬 (종합 평가)
gfa suggest-repos --sort activity
```

#### 옵션 설명

| 옵션 | 설명 | 기본값 |
|------|------|--------|
| `--limit`, `-l` | 최대 추천 개수 | 10 |
| `--days`, `-d` | 최근 활동 기간 (일) | 90 |
| `--sort`, `-s` | 정렬 기준 (updated, stars, activity) | activity |

</details>

## 📁 설정 파일

<details>
<summary><b>⚙️ 설정 파일 구조 보기</b></summary>

설정은 `~/.config/github_feedback/config.toml`에 저장되며, `gfa init` 실행 시 자동으로 생성됩니다.

### Enterprise 호스트 설정 (`hosts.config.json`)

프로젝트의 `.config/hosts.config.json` 파일을 편집하여 회사별 GitHub Enterprise 호스트를 커스터마이즈할 수 있습니다.

```json
{
  "description": "Default GitHub Enterprise host examples shown in the host selection menu",
  "default_hosts": [
    "github.com (Default)",
    "github.company.com",
    "github.enterprise.local",
    "ghe.example.com"
  ]
}
```

**커스터마이징 방법:**
1. `.config/hosts.config.json` 파일을 열어서 편집
2. `default_hosts` 배열에 회사의 GitHub Enterprise 호스트를 추가하거나 수정
3. 첫 번째 항목은 "github.com (Default)"로 유지하는 것을 권장
4. 저장 후 `gfa init` 실행 시 수정된 호스트 목록이 표시됩니다

**예시 (회사별 커스터마이즈):**

```json
{
  "description": "Company-specific GitHub Enterprise hosts",
  "default_hosts": [
    "github.com (Default)",
    "github.mycompany.com",
    "ghe.internal.corp",
    "github.dev.mycompany.net"
  ]
}
```

> 파일이 없거나 형식이 잘못된 경우 자동으로 기본값이 사용됩니다.

### 설정 파일 예시

```toml
[version]
version = "1.0.0"

[auth]
# PAT는 시스템 키링에 안전하게 저장됩니다 (이 파일에 저장되지 않음)

[server]
api_url = "https://api.github.com"
graphql_url = "https://api.github.com/graphql"
web_url = "https://github.com"

[llm]
endpoint = "http://localhost:8000/v1/chat/completions"
model = "gpt-4"
timeout = 60
max_files_in_prompt = 10
max_retries = 3

[defaults]
months = 12
```

### 수동 설정 편집

필요한 경우 설정 파일을 직접 편집하거나 `gfa config` 명령어를 사용할 수 있습니다:

```bash
# 방법 1: config 명령어 사용 (권장)
gfa config set llm.model gpt-4
gfa config show

# 방법 2: 직접 편집
nano ~/.config/github_feedback/config.toml
```

</details>

## 📊 생성되는 파일 구조

<details>
<summary><b>📁 출력 파일 구조 보기</b></summary>

### `gfa feedback` 출력

```
reports/
├── metrics.json                     # 📈 개인 활동 분석 데이터 (JSON)
├── report.md                        # 📄 마크다운 보고서
├── integrated_full_report.md        # 🎯 통합 보고서 (brief + PR 리뷰)
├── reviews/                         # 🔍 PR 리뷰 (서브디렉토리)
│   └── {owner}__{repo_name}/        # 저장소별 리뷰 (owner__repo 형식)
│       ├── pr-{number}/
│       │   ├── artefacts.json       # 원본 PR 데이터
│       │   ├── review_summary.json  # 구조화된 리뷰
│       │   └── review.md            # 마크다운 리뷰
│       ├── integrated_report.md     # 통합 PR 리뷰 보고서
│       └── personal_development.json  # 개인 성장 분석
└── year-in-review/                  # 🎊 연간 회고 (--year-in-review 옵션 사용 시)
    ├── year_{year}_in_review.md     # 연간 종합 보고서
    └── metrics/                     # 저장소별 커뮤니케이션/디테일 데이터
        └── {owner}__{repo}.json     # 각 저장소의 detailed metrics 스냅샷
```

### 📊 통합 보고서 구조 (`integrated_full_report.md`)

통합 보고서는 사용자 중심으로 설계되어 빠르게 핵심 정보를 파악할 수 있습니다:

#### 1. 🎯 한눈에 보기 (Executive Summary)
- 획득 어워드 총 개수
- 주요 성과 Top 3
- 주요 개선점 Top 2
- 다음 집중 영역 Top 3

#### 2. 🏆 주요 성과
- 획득한 모든 어워드 목록
- 성장 하이라이트

#### 3. 💡 개선 피드백
- 개인 성장 분석 (장점, 보완점, 성장 지표)
- 코드 품질 피드백 (커밋 메시지, PR 제목, 리뷰 톤, 이슈 품질)

#### 4. 📊 상세 분석
- 월별 활동 트렌드
- 기술 스택 분석
- 협업 네트워크
- 심층 회고 분석

#### 5. 📝 부록
- 개별 PR 리뷰 상세 내역
- 구체적 사례 및 증거

</details>

## 💡 사용 예시

<details>
<summary><b>📚 사용 시나리오 예시 보기</b></summary>

### 예시 1: 빠른 시작 - 대화형 모드

```bash
# 1. 설정 (최초 1회)
gfa init

# 2. 저장소 추천 받기
gfa suggest-repos

# 3. 대화형 모드로 나의 활동 분석
gfa feedback --interactive

# 4. 보고서 확인
cat reports/report.md
```

### 예시 2: 오픈소스 기여 활동 분석

```bash
# 1. 설정 (최초 1회)
gfa init

# 2. 내가 기여한 오픈소스 프로젝트 활동 분석
gfa feedback --repo facebook/react

# 3. 보고서 확인 (나의 기여 활동만 표시됨)
cat reports/report.md
```

### 예시 3: 개인 프로젝트 회고

```bash
# 내 저장소 목록 확인
gfa list-repos --sort updated --limit 10

# 내 프로젝트에서 나의 활동 분석
gfa feedback --repo myname/my-awesome-project

# 보고서 확인
cat reports/report.md
```

### 예시 4: 팀 프로젝트에서 나의 성과 리뷰

```bash
# 조직 저장소 목록 확인
gfa list-repos --org mycompany --limit 20

# 분석 기간 설정 (지난 6개월)
gfa config set defaults.months 6

# 조직 저장소에서 나의 활동 분석
gfa feedback --repo mycompany/product-service

# 보고서 확인 (나의 활동만 표시됨)
cat reports/report.md
```

</details>

## 🎯 어워드 시스템

<details>
<summary><b>🏆 어워드 목록 보기</b></summary>

저장소 활동에 따라 자동으로 어워드가 부여됩니다:

### 커밋 기반 어워드
- 💎 **코드 전설** (1000+ 커밋)
- 🏆 **코드 마스터** (500+ 커밋)
- 🥇 **코드 대장장이** (200+ 커밋)
- 🥈 **코드 장인** (100+ 커밋)
- 🥉 **코드 견습생** (50+ 커밋)

### PR 기반 어워드
- 💎 **릴리스 전설** (200+ PR)
- 🏆 **배포 제독** (100+ PR)
- 🥇 **릴리스 선장** (50+ PR)
- 🥈 **릴리스 항해사** (25+ PR)
- 🥉 **배포 선원** (10+ PR)

### 리뷰 기반 어워드
- 💎 **지식 전파자** (200+ 리뷰)
- 🏆 **멘토링 대가** (100+ 리뷰)
- 🥇 **리뷰 전문가** (50+ 리뷰)
- 🥈 **성장 멘토** (20+ 리뷰)
- 🥉 **코드 지원자** (10+ 리뷰)

### 특별 어워드
- ⚡ **번개 개발자** (월 50+ 커밋)
- 🤝 **협업 마스터** (월 20+ PR+리뷰)
- 🏗️ **대규모 아키텍트** (5000줄+ 변경)
- 📅 **꾸준함의 달인** (6개월 이상 지속적 활동)
- 🌟 **다재다능** (모든 영역 균형있는 기여)

</details>

## 🐛 문제 해결

<details>
<summary><b>🔧 트러블슈팅 가이드 보기</b></summary>

### PAT 권한 오류

```
Error: GitHub API rejected the provided PAT
```

**해결방법**: PAT에 적절한 권한이 있는지 확인
- 비공개 저장소: `repo` 권한 필요
- 공개 저장소: `public_repo` 권한 필요
- [GitHub Settings → Developer settings → Personal access tokens](https://github.com/settings/tokens)에서 확인

### LLM 엔드포인트 연결 실패

```
Warning: Detailed feedback analysis failed: Connection refused
```

**해결방법**:
1. LLM 서버가 실행 중인지 확인
2. 엔드포인트 URL이 올바른지 확인 (`gfa config show`)
3. 필요시 설정 재초기화: `gfa init`

### 저장소를 찾을 수 없음

```
Error: Repository not found
```

**해결방법**:
- 저장소 이름 형식 확인: `owner/repo` (예: `torvalds/linux`)
- 비공개 저장소의 경우 PAT 권한 확인
- GitHub Enterprise 사용 시 `--enterprise-host` 설정 확인

### 분석 기간 내 데이터 없음

```
분석 기간 동안 뚜렷한 활동이 감지되지 않았습니다.
```

**해결방법**:
- 분석 기간을 늘려보세요: `gfa init --months 24`
- 저장소가 활성화된 저장소인지 확인

### Timeout 에러 발생

```
⚠ <작업> timed out after <시간>s
```

**해결방법**:
- **걱정하지 마세요!** `gfa feedback` 명령을 다시 실행하면 이미 수집된 데이터를 활용하여 작업을 이어서 진행합니다
- Timeout이 발생한 작업만 다시 시도되므로, 처음부터 다시 시작하지 않습니다
- 캐시된 데이터 덕분에 재실행 시 60-70% 더 빠르게 완료됩니다
- 네트워크가 불안정한 경우, 잠시 후 다시 시도하세요
- 반복적으로 timeout이 발생하면:
  - LLM 엔드포인트의 응답 속도를 확인하세요
  - 네트워크 연결 상태를 확인하세요
  - GitHub API rate limit을 확인하세요

### 캐시 오류 또는 데이터 손상 경고

```
Error: Failed to parse cached response
```

**해결방법**:
- `gfa clear-cache`를 실행해 `~/.cache/github_feedback/api_cache.sqlite` 파일을 삭제하고 새 데이터를 받아오세요
- 캐시 초기화 이후에도 문제가 지속되면 `gfa feedback` 실행 로그를 이슈에 첨부하여 공유해주세요

</details>

## 👩‍💻 개발자 가이드

<details>
<summary><b>🛠️ 개발 환경 설정 보기</b></summary>

### 개발 환경 설정

```bash
# 저장소 복사
git clone https://github.com/goonbamm/github-feedback-analysis.git
cd github-feedback-analysis

# 개발 모드로 설치 (테스트 의존성 포함)
uv pip install -e .[test]

# 테스트 실행
pytest

# 특정 테스트 실행
pytest tests/test_analyzer.py -v

# 커버리지 확인
pytest --cov=github_feedback --cov-report=html
```

### 주요 의존성

**핵심 런타임 의존성:**
- **typer >= 0.9** - CLI 프레임워크
- **rich >= 13.0** - 터미널 UI, 진행 표시줄
- **pydantic >= 2.5** - 데이터 검증 및 직렬화
- **requests >= 2.31** - HTTP 클라이언트
- **requests-cache >= 1.0** - SQLite 기반 응답 캐싱
- **keyring >= 24.0** - 시스템 자격 증명 저장소
- **keyrings.alt >= 5.0** - 폴백 암호화 파일 키링
- **tomli >= 2.0** - TOML 파일 파싱 (Python < 3.11)
- **tomli-w >= 1.0** - TOML 파일 쓰기

**개발/테스트 의존성:**
- **pytest >= 7.4** - 테스트 프레임워크

**시스템 요구사항:**
- Python 3.11+ (async/타입 힌트 필수)
- 시스템 키링 또는 접근 가능한 파일 시스템
- GitHub Personal Access Token (classic 또는 fine-grained)
- OpenAI API 형식과 호환되는 LLM 엔드포인트

### 코드 구조

```
github_feedback/
├── cli.py              # 🖥️  CLI 진입점, 인터랙티브 초기 설정과 보고서 워크플로우
├── llm.py              # 🤖 LLM API 클라이언트, 재시도·배치 처리 및 연결 진단
├── reporter.py         # 📄 통합 보고서/브리프 생성기
├── retrospective.py    # 📅 연말 회고 및 행동 패턴 분석 엔진
├── analyzer.py         # 📊 메트릭 계산, 지표 요약, 어워드 산출
├── review_reporter.py  # 📝 PR 리뷰 결과를 통합 보고서로 변환
├── config.py           # ⚙️  설정 로딩/저장, 키링 연동 및 호스트 관리
├── models.py           # 📦 Pydantic 데이터 모델 정의
├── pr_collector.py     # 🔍 PR 데이터 수집 및 필터링 로직
├── award_strategies.py # 🏆 어워드 계산 전략 모음 (100+ 규칙)
├── api_client.py       # 🌐 GitHub REST API/GraphQL 호출 추상화
├── reviewer.py         # 🎯 PR 리뷰 분석 및 LLM 프롬프트 구성
├── collector.py        # 📡 데이터 수집 파사드, 병렬 수집 오케스트레이션
├── commit_collector.py # 📝 커밋 데이터 수집기
├── review_collector.py # 👀 리뷰 데이터 수집기
├── repository_manager.py # 📂 저장소 조회 및 캐싱
├── filters.py          # 🔍 활동/언어 필터링 유틸리티
├── exceptions.py       # ⚠️  예외 계층 구조 및 사용자 친화 메시지
└── utils.py            # 🔧 공통 유틸리티 함수
```

### 아키텍처 및 디자인 패턴

- **Facade Pattern**: `Collector` 클래스가 전문화된 수집기들을 조율
- **Strategy Pattern**: 어워드 계산에서 100+ 전략 사용
- **Repository Pattern**: `GitHubApiClient`가 API 접근 추상화
- **Builder Pattern**: 보고서 및 메트릭 구성
- **Thread Pool Pattern**: 병렬 데이터 수집 (4배 속도 향상)

### 성능 최적화

- **요청 캐싱**: SQLite 기반 캐시 (`~/.cache/github_feedback/api_cache.sqlite`)
  - 기본 만료 시간: 1시간
  - GET/HEAD 요청만 캐싱
  - 반복 실행 시 60-70% 속도 향상
- **병렬 수집**: ThreadPoolExecutor를 사용한 동시 데이터 수집
- **재시도 로직**: LLM 요청에 지수 백오프 적용 (최대 3회 시도)

</details>

## 🔒 보안

- **PAT 저장**: GitHub 토큰은 시스템 키링에 안전하게 저장됩니다 (평문 파일에 저장되지 않음)
  - 시스템 키링 지원: gnome-keyring, macOS Keychain, Windows Credential Manager
  - Linux 폴백: 암호화된 파일 키링 (`keyrings.alt`)
  - Thread-safe 키링 초기화 (race condition 방지)
- **설정 백업**: 설정 파일 덮어쓰기 전 자동으로 백업 생성
- **입력 검증**: 모든 사용자 입력 검증 (PAT 형식, URL 형식, 저장소 형식)
- **캐시 보안**: SQLite 캐시 파일은 사용자 전용 읽기/쓰기 권한
- **API 보안**: Bearer 토큰 인증, HTTPS 전용 통신

## 📄 라이선스

이 프로젝트는 MIT 라이선스를 따릅니다.

## 🤝 기여하기

버그 리포트, 기능 제안, PR은 언제나 환영합니다!

1. Fork the repository
2. Create your feature branch (`git checkout -b feature/amazing-feature`)
3. Commit your changes (`git commit -m 'Add amazing feature'`)
4. Push to the branch (`git push origin feature/amazing-feature`)
5. Open a Pull Request

## 💬 피드백

문제가 있거나 제안사항이 있다면 [Issues](https://github.com/goonbamm/github-feedback-analysis/issues)에 등록해주세요!
