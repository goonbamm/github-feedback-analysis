# 🚀 GitHub Feedback Analysis

GitHub 저장소의 활동을 분석하고 인사이트를 담은 보고서를 자동으로 생성하는 CLI 도구입니다. GitHub.com과 GitHub Enterprise 환경을 지원하며, LLM을 활용한 자동 리뷰 기능을 제공합니다.

한국어 | [English](README_EN.md)

## ✨ 주요 기능

- 📊 **저장소 분석**: 커밋, 이슈, 리뷰 활동을 기간별로 집계하고 분석
- 🤖 **LLM 기반 피드백**: 커밋 메시지, PR 제목, 리뷰 톤, 이슈 품질에 대한 상세 분석
- 🎯 **PR 자동 리뷰**: 인증된 사용자의 PR을 자동으로 리뷰하고 통합 회고 보고서 생성
- 🏆 **성과 시각화**: 기여도에 따른 어워드 및 하이라이트 자동 생성

## 📋 준비물

- Python 3.11 이상
- [uv](https://docs.astral.sh/uv/) 또는 선호하는 패키지 매니저
- GitHub Personal Access Token
  - 비공개 저장소: `repo` 권한
  - 공개 저장소: `public_repo` 권한
- LLM API 엔드포인트 (OpenAI 호환 형식)

## 🔧 설치

```bash
# 저장소 클론
git clone https://github.com/goonbamm/github-feedback-analysis.git
cd github-feedback-analysis

# 가상 환경 생성 및 활성화
uv venv
source .venv/bin/activate  # Windows: .venv\Scripts\activate

# 패키지 설치
uv pip install -e .
```

## 🚀 빠른 시작

### 1️⃣ 설정 초기화

```bash
gf init
```

대화형 프롬프트가 나타나면 다음 정보를 입력하세요:
- GitHub Personal Access Token
- LLM 엔드포인트 (예: `http://localhost:8000/v1/chat/completions`)
- LLM 모델 (예: `gpt-4`)
- GitHub Enterprise 호스트 (선택사항, github.com이 아닌 경우만)

### 2️⃣ 저장소 분석

```bash
gf brief --repo goonbamm/github-feedback-analysis
```

분석이 완료되면 `reports/` 디렉터리에 다음 파일들이 생성됩니다:
- `metrics.json` - 분석 데이터
- `report.md` - 마크다운 보고서
- `prompts/` - LLM 프롬프트 파일들

### 3️⃣ 결과 확인

```bash
cat reports/report.md
```

## 📚 명령어 상세 가이드

### 🎯 `gf init` - 초기 설정

GitHub 접속 정보와 LLM 설정을 저장합니다.

#### 기본 사용법 (대화형)

```bash
gf init
```

#### 예시: GitHub.com + 로컬 LLM 사용

```bash
gf init \
  --pat ghp_xxxxxxxxxxxxxxxxxxxx \
  --llm-endpoint http://localhost:8000/v1/chat/completions \
  --llm-model gpt-4 \
  --months 12
```

#### 예시: GitHub Enterprise 사용

```bash
gf init \
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

### 📊 `gf brief` - 저장소 분석

저장소를 분석하고 상세 피드백 보고서를 생성합니다.

#### 기본 사용법

```bash
gf brief --repo owner/repo-name
```

#### 예시

```bash
# 공개 저장소 분석
gf brief --repo torvalds/linux

# 개인 저장소 분석
gf brief --repo myusername/my-private-repo

# 조직 저장소 분석
gf brief --repo microsoft/vscode
```

#### 생성되는 보고서

분석이 완료되면 `reports/` 디렉터리에 다음 파일들이 생성됩니다:

```
reports/
├── metrics.json              # 원본 데이터 (JSON)
├── report.md                 # 분석 보고서 (마크다운)
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

### 🎯 `gf feedback` - PR 자동 리뷰

인증된 사용자(PAT 소유자)의 PR을 자동으로 리뷰하고 통합 회고 보고서를 생성합니다.

#### 기본 사용법

```bash
gf feedback --repo owner/repo-name
```

#### 예시

```bash
# 모든 PR 리뷰 (열린 것 + 닫힌 것)
gf feedback --repo myusername/my-project --state all

# 열린 PR만 리뷰
gf feedback --repo myusername/my-project --state open

# 닫힌 PR만 리뷰
gf feedback --repo myusername/my-project --state closed
```

#### 옵션 설명

| 옵션 | 설명 | 필수 | 기본값 |
|------|------|------|--------|
| `--repo` | 저장소 (owner/name) | ✅ | - |
| `--state` | PR 상태 (`open`, `closed`, `all`) | ❌ | `all` |

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

### ⚙️ `gf show-config` - 설정 확인

현재 저장된 설정을 확인합니다.

```bash
gf show-config
```

#### 출력 예시

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

## 📁 설정 파일

설정은 `~/.config/github_feedback/config.toml`에 저장되며, `gf init` 실행 시 자동으로 생성됩니다.

### 설정 파일 예시

```toml
[auth]
pat = "<set>"  # 보안을 위해 실제 값은 표시되지 않음

[server]
api_url = "https://api.github.com"
graphql_url = "https://api.github.com/graphql"
web_url = "https://github.com"

[llm]
endpoint = "http://localhost:8000/v1/chat/completions"
model = "gpt-4"

[defaults]
months = 12
```

### 수동 설정 편집

필요한 경우 설정 파일을 직접 편집할 수 있습니다:

```bash
# 설정 파일 위치 확인
gf show-config

# 편집기로 열기
nano ~/.config/github_feedback/config.toml
```

## 📊 생성되는 파일 구조

### `gf brief` 출력

```
reports/
├── metrics.json              # 📈 분석 지표 원본 데이터
├── report.md                 # 📄 마크다운 보고서
└── prompts/
    ├── commit_feedback.txt   # 💬 커밋 메시지 품질 분석
    ├── pr_feedback.txt       # 🔀 PR 제목 분석
    ├── review_feedback.txt   # 👀 리뷰 톤 분석
    └── issue_feedback.txt    # 🐛 이슈 품질 분석
```

### `gf feedback` 출력

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

## 💡 사용 예시

### 예시 1: 오픈소스 프로젝트 분석

```bash
# 1. 설정 (최초 1회)
gf init

# 2. 유명 오픈소스 프로젝트 분석
gf brief --repo facebook/react

# 3. 보고서 확인
cat reports/report.md
```

### 예시 2: 개인 프로젝트 회고

```bash
# 내 프로젝트 분석
gf brief --repo myname/my-awesome-project

# 내가 작성한 PR 자동 리뷰
gf feedback --repo myname/my-awesome-project --state all

# 통합 회고 보고서 확인
cat reviews/myname_my-awesome-project/integrated_report.md
```

### 예시 3: 팀 프로젝트 성과 리뷰

```bash
# 조직 저장소 분석 (지난 6개월)
gf init --months 6
gf brief --repo mycompany/product-service

# 팀원별 PR 리뷰 (각자 PAT로 실행)
gf feedback --repo mycompany/product-service --state closed
```

## 🎯 어워드 시스템

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

## 🐛 문제 해결

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
2. 엔드포인트 URL이 올바른지 확인 (`gf show-config`)
3. 필요시 설정 재초기화: `gf init`

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
- 분석 기간을 늘려보세요: `gf init --months 24`
- 저장소가 활성화된 저장소인지 확인

## 👩‍💻 개발자 가이드

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
