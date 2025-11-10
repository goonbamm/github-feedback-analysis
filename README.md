# 🚀 GitHub Feedback Analysis

GitHub Feedback Analysis는 GitHub 저장소 활동을 수집하고 핵심 지표를 계산해, 마크다운 보고서를 자동으로 만들어 주는 CLI 도구입니다. GitHub.com은 물론 Enterprise(Server) 환경에서도 동일하게 동작합니다.

## ✨ 주요 명령
- `gf init` : Personal Access Token과 기본 분석 옵션을 설정 파일에 저장합니다.
- `gf analyze` : 저장소 데이터를 수집하고 `reports/` 디렉터리에 분석 결과를 생성합니다.
- `gf report` : 최근에 저장된 지표(`reports/metrics.json`)로 보고서를 다시 만듭니다.
- `gf show-config` : 현재 적용 중인 설정 값을 확인합니다.

## 🛠️ 설치
```bash
git clone https://github.com/<your-account>/github-feedback-analysis.git
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
- PAT과 기본 분석 기간을 입력하면 `~/.config/github_feedback/config.toml` 파일이 생성됩니다.
- Enterprise를 사용한다면 호스트만 입력하면 API/GraphQL/Web URL이 자동으로 채워집니다.

### 2. 저장소 분석
```bash
gf analyze --repo owner/name --months 6 --include-language py
```
- 저장소명을 생략하면 프롬프트에서 `owner/name` 형식을 입력할 수 있습니다.
- 브랜치, 경로, 언어 필터로 원하는 영역만 분석할 수 있습니다.
- 실행 후 `reports/report.md`와 `reports/metrics.json` 파일이 생성됩니다.

### 3. 보고서 재생성
```bash
gf report
```
캐시된 지표가 있을 때 보고서를 다시 생성합니다.

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
