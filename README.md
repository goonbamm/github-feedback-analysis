# 🚀 GitHub Feedback Analysis

GitHub 저장소의 활동을 분석하고 인사이트를 담은 보고서를 자동으로 생성하는 CLI 도구입니다. GitHub.com과 GitHub Enterprise 환경을 지원하며, LLM을 활용한 자동 리뷰 기능을 제공합니다.

한국어 | [English](translations/README_EN.md) | [简体中文](translations/README_ZH.md) | [日本語](translations/README_JA.md) | [Español](translations/README_ES.md)

## ✨ 주요 기능

- 📊 **저장소 분석**: 커밋, 이슈, 리뷰 활동을 기간별로 집계하고 분석
- 🤖 **LLM 기반 피드백**: 커밋 메시지, PR 제목, 리뷰 톤, 이슈 품질에 대한 상세 분석
- 🎯 **PR 자동 리뷰**: 인증된 사용자의 PR을 자동으로 리뷰하고 통합 회고 보고서 생성
- 🏆 **성과 시각화**: 기여도에 따른 어워드 및 하이라이트 자동 생성
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
   ```bash
   gfa init --enterprise-host https://github.your-company.com
   ```

4. **관리자 문의**
   - 일부 Enterprise 환경에서는 PAT 생성이 제한될 수 있습니다
   - 문제 발생 시 GitHub 관리자에게 문의하세요

### 참고 자료

- [GitHub 공식 문서: Personal Access Token 관리](https://docs.github.com/ko/authentication/keeping-your-account-and-data-secure/managing-your-personal-access-tokens)
- [GitHub 공식 문서: Fine-grained PAT](https://docs.github.com/ko/authentication/keeping-your-account-and-data-secure/managing-your-personal-access-tokens#fine-grained-personal-access-tokens)
- [GitHub Enterprise Server 문서](https://docs.github.com/en/enterprise-server@latest/authentication/keeping-your-account-and-data-secure/managing-your-personal-access-tokens)

</details>

## 🔧 설치

```bash
# 저장소 클론
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
- GitHub Enterprise 호스트 (선택사항, github.com이 아닌 경우만)

### 2️⃣ 저장소 분석

```bash
gfa feedback --repo goonbamm/github-feedback-analysis
```

분석이 완료되면 `reports/` 디렉터리에 다음 파일들이 생성됩니다:
- `metrics.json` - 분석 데이터
- `report.md` - 마크다운 보고서
- `report.html` - HTML 보고서 (시각화 차트 포함)
- `charts/` - SVG 차트 파일들
- `prompts/` - LLM 프롬프트 파일들

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

</details>

<details>
<summary><b>📊 gfa feedback - 저장소 분석</b></summary>

저장소를 분석하고 상세 피드백 보고서를 생성합니다.

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
# 공개 저장소 분석
gfa feedback --repo torvalds/linux

# 개인 저장소 분석
gfa feedback --repo myusername/my-private-repo

# 조직 저장소 분석
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
├── metrics.json              # 원본 데이터 (JSON)
├── report.md                 # 분석 보고서 (마크다운)
├── report.html               # 분석 보고서 (HTML, 차트 포함)
├── charts/                   # 시각화 차트
│   ├── quality.svg          # 품질 지표 차트
│   ├── activity.svg         # 활동 지표 차트
│   └── ...                  # 기타 도메인별 차트
└── prompts/
    ├── commit_feedback.txt   # 커밋 메시지 피드백
    ├── pr_feedback.txt       # PR 제목 피드백
    ├── review_feedback.txt   # 리뷰 톤 피드백
    └── issue_feedback.txt    # 이슈 품질 피드백
```

#### 분석 내용

- ✅ **활동 집계**: 커밋, PR, 리뷰, 이슈 수 계산
- 🎯 **품질 분석**: 커밋 메시지, PR 제목, 리뷰 톤, 이슈 설명 품질
- 🏆 **어워드**: 기여도에 따른 자동 어워드 부여
- 📈 **트렌드**: 월별 활동 추이 및 속도 분석

</details>

<details>
<summary><b>🎯 gfa feedback - PR 자동 리뷰</b></summary>

인증된 사용자(PAT 소유자)의 PR을 자동으로 리뷰하고 통합 회고 보고서를 생성합니다.

#### 기본 사용법

```bash
gfa feedback --repo owner/repo-name
```

#### 예시

```bash
# 내가 작성한 모든 PR 리뷰
gfa feedback --repo myusername/my-project
```

#### 옵션 설명

| 옵션 | 설명 | 필수 | 기본값 |
|------|------|------|--------|
| `--repo` | 저장소 (owner/name) | ✅ | - |

#### 실행 과정

1. **PR 검색** 🔍
   - PAT로 인증된 사용자가 작성한 PR 목록 조회

2. **개별 리뷰 생성** 📝
   - 각 PR의 코드 변경사항, 리뷰 코멘트 수집
   - LLM을 사용한 상세 리뷰 생성
   - `reviews/owner_repo/pr-{번호}/` 디렉터리에 저장

3. **통합 회고 보고서** 📊
   - 모든 PR을 종합한 인사이트 생성
   - `reviews/owner_repo/integrated_report.md` 저장

#### 생성되는 파일

```
reviews/
└── owner_repo/
    ├── pr-123/
    │   ├── artefacts.json          # PR 원본 데이터
    │   ├── review_summary.json     # LLM 분석 결과
    │   └── review.md               # 마크다운 리뷰
    ├── pr-456/
    │   └── ...
    └── integrated_report.md        # 통합 회고 보고서
```

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
├── metrics.json              # 📈 분석 지표 원본 데이터
├── report.md                 # 📄 마크다운 보고서
├── report.html               # 🎨 HTML 보고서 (시각화 차트 포함)
├── charts/                   # 📊 시각화 차트 (SVG)
│   ├── quality.svg          # 품질 지표 차트
│   ├── activity.svg         # 활동 지표 차트
│   ├── engagement.svg       # 참여도 차트
│   └── ...                  # 기타 도메인별 차트
└── prompts/
    ├── commit_feedback.txt   # 💬 커밋 메시지 품질 분석
    ├── pr_feedback.txt       # 🔀 PR 제목 분석
    ├── review_feedback.txt   # 👀 리뷰 톤 분석
    └── issue_feedback.txt    # 🐛 이슈 품질 분석
```

### `gfa feedback` 출력

```
reviews/
└── owner_repo/
    ├── pr-123/
    │   ├── artefacts.json          # 📦 PR 원본 데이터 (코드, 리뷰 등)
    │   ├── review_summary.json     # 🤖 LLM 분석 결과 (구조화된 데이터)
    │   └── review.md               # 📝 마크다운 리뷰 보고서
    ├── pr-456/
    │   └── ...
    └── integrated_report.md        # 🎯 통합 회고 보고서 (모든 PR 종합)
```

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

# 3. 대화형 모드로 분석
gfa feedback --interactive

# 4. 보고서 확인
cat reports/report.md
```

### 예시 2: 오픈소스 프로젝트 분석

```bash
# 1. 설정 (최초 1회)
gfa init

# 2. 유명 오픈소스 프로젝트 분석
gfa feedback --repo facebook/react

# 3. 보고서 확인
cat reports/report.md
```

### 예시 3: 개인 프로젝트 회고

```bash
# 내 저장소 목록 확인
gfa list-repos --sort updated --limit 10

# 내 프로젝트 분석
gfa feedback --repo myname/my-awesome-project

# 내가 작성한 PR 자동 리뷰
gfa feedback --repo myname/my-awesome-project

# 통합 회고 보고서 확인
cat reviews/myname_my-awesome-project/integrated_report.md
```

### 예시 4: 팀 프로젝트 성과 리뷰

```bash
# 조직 저장소 목록 확인
gfa list-repos --org mycompany --limit 20

# 분석 기간 설정 (지난 6개월)
gfa config set defaults.months 6

# 조직 저장소 분석
gfa feedback --repo mycompany/product-service

# 팀원별 PR 리뷰 (각자 PAT로 실행)
gfa feedback --repo mycompany/product-service
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

</details>

## 👩‍💻 개발자 가이드

<details>
<summary><b>🛠️ 개발 환경 설정 보기</b></summary>

### 개발 환경 설정

```bash
# 저장소 클론
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

### 코드 구조

```
github_feedback/
├── cli.py              # 🖥️  CLI 진입점 및 명령어
├── collector.py        # 📡 GitHub API 데이터 수집
├── analyzer.py         # 📊 메트릭 분석 및 계산
├── reporter.py         # 📄 보고서 생성 (brief)
├── reviewer.py         # 🎯 PR 리뷰 로직
├── review_reporter.py  # 📝 통합 리뷰 보고서
├── llm.py             # 🤖 LLM API 클라이언트
├── config.py          # ⚙️  설정 관리
├── models.py          # 📦 데이터 모델
└── utils.py           # 🔧 유틸리티 함수
```

</details>

## 🔒 보안

- **PAT 저장**: GitHub 토큰은 시스템 키링에 안전하게 저장됩니다 (평문 파일에 저장되지 않음)
- **설정 백업**: 설정 파일 덮어쓰기 전 자동으로 백업 생성
- **입력 검증**: 모든 사용자 입력 검증 (PAT 형식, URL 형식, 저장소 형식)

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
