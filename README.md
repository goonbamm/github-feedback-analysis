# 🚀 GitHub Feedback Analysis

GitHub Feedback Analysis는 GitHub 저장소 활동을 수집하고 핵심 지표를 계산해, 마크다운 보고서를 자동으로 만들어 주는 CLI 도구입니다. GitHub.com은 물론 Enterprise(Server) 환경에서도 동일하게 동작합니다.

## ✨ 주요 명령
- `gf init` : Personal Access Token과 기본 분석 옵션을 설정 파일에 저장합니다.
- `gf analyze` : 저장소 데이터를 수집하고 `reports/` 디렉터리에 분석 결과를 생성합니다.
- `gf report` : 최근에 저장된 지표(`reports/metrics.json`)로 보고서를 다시 만듭니다.
- `gf show-config` : 현재 적용 중인 설정 값을 확인합니다.

## 🛠️ 설치
```bash
git clone https://github.com/goonbamm/github-feedback-analysis.git
cd github-feedback-analysis
uv venv
source .venv/bin/activate
uv pip install -e .
```

테스트 의존성까지 필요하다면 `uv pip install -e .[test]`를 사용하세요.

## 🚦 사용 방법
### 1. 초기 설정
```bash
gf init
```
- 실행하면 상호작용형 프롬프트가 뜨며 PAT, 기본 분석 기간, 기본 템플릿 경로 등을 저장합니다.
- Enterprise를 사용한다면 호스트만 입력하면 API/GraphQL/Web URL이 자동으로 채워집니다.
- `--non-interactive`와 `--config-path`를 활용해 CI에서 설정 파일을 미리 작성할 수 있습니다.

### 2. 저장소 분석
`gf analyze`는 실제 데이터를 수집하고 보고서를 만드는 핵심 명령입니다. 자주 사용하는 옵션은 다음과 같습니다.

| 옵션 | 기본값 | 설명 |
| --- | --- | --- |
| `--repo owner/name` | (필수) | 분석할 저장소를 `owner/name` 형식으로 지정합니다. 생략하면 프롬프트에서 입력할 수 있습니다. |
| `--months N` | `3` | 최근 N개월 간의 활동을 분석합니다. |
| `--branch main` | 기본 브랜치 | 특정 브랜치만 분석하고 싶을 때 지정합니다. |
| `--include-path path/` | 전체 | 지정된 경로 하위 파일만 포함합니다. 여러 개 지정 가능. |
| `--exclude-path path/` | 없음 | 지정된 경로를 제외합니다. |
| `--include-language py` | 전체 | 특정 언어 파일만 분석합니다. 여러 언어를 지정하려면 옵션을 반복합니다. |
| `--output-dir reports/` | `reports/` | 결과 파일을 저장할 디렉터리를 지정합니다. |

#### 자주 쓰는 예시
```bash
# 최근 6개월 동안 Python 파일만 분석
gf analyze --repo owner/name --months 6 --include-language py

# 특정 브랜치와 경로에 한정하여 분석
gf analyze --repo owner/name --branch develop --include-path src/ --include-path docs/

# 여러 저장소를 순차적으로 분석하고 결과 폴더를 따로 지정
gf analyze --repo owner/name --output-dir reports/owner-name
gf analyze --repo another/name --output-dir reports/another-name
```
- 실행 후 `reports/report.md`와 `reports/metrics.json` 파일이 생성됩니다.

### 3. 보고서 재생성
```bash
gf report --template docs/report_template.md
```
- 캐시된 지표가 있을 때 보고서를 다시 생성합니다.
- `--template`을 사용하면 커스텀 마크다운 템플릿으로 보고서를 생성할 수 있습니다.
- `--output` 옵션으로 보고서 파일명을 바꿀 수 있습니다. (예: `gf report --output reports/latest.md`)

## 🔐 설정 관리
- 설정 파일 경로: `~/.config/github_feedback/config.toml`
- `gf show-config` 명령으로 저장된 값을 확인할 수 있으며, PAT은 안전하게 마스킹됩니다.

## 🧪 개발 팁
```bash
uv pip install -e .[test]
pytest
```

## 📄 라이선스
MIT License
