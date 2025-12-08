# 성능 개선 가능 영역 분석

## 📊 요약

GitHub Feedback Analysis 프로젝트의 성능을 분석한 결과, **7개의 주요 개선 영역**을 발견했습니다. 현재 코드베이스는 이미 ThreadPoolExecutor를 사용한 병렬 처리와 캐싱을 잘 활용하고 있지만, 추가 최적화를 통해 **30-50% 성능 향상**이 가능할 것으로 예상됩니다.

---

## 🎯 주요 개선 영역

### 1. LLM 분석 병렬화 강화 ⭐⭐⭐

**현재 상태:**
```python
# llm.py:913-920
with ThreadPoolExecutor(max_workers=2) as executor:
    comm_future = executor.submit(self.complete, comm_messages, ...)
    code_future = executor.submit(self.complete, code_messages, ...)
```

**문제점:**
- `analyze_personal_development`에서 2개의 워커만 사용
- 다른 LLM 분석 메서드들(commit messages, PR titles, review tone, issue quality)이 순차적으로 실행될 가능성
- `max_workers_llm_analysis: 4`로 설정되어 있지만 완전히 활용되지 않음

**개선 방안:**
```python
# constants.py
PARALLEL_CONFIG = {
    'max_workers_llm_analysis': 6,  # 4 → 6 증가
    # ...
}

# analyzer.py 또는 호출 코드에서
def analyze_all_feedback_parallel(self, ...):
    """모든 피드백 분석을 병렬로 실행"""
    with ThreadPoolExecutor(max_workers=6) as executor:
        futures = {
            'commits': executor.submit(llm_client.analyze_commit_messages, commits),
            'pr_titles': executor.submit(llm_client.analyze_pr_titles, pr_titles),
            'review_tone': executor.submit(llm_client.analyze_review_tone, reviews),
            'issue_quality': executor.submit(llm_client.analyze_issue_quality, issues),
            'personal_dev': executor.submit(llm_client.analyze_personal_development, ...),
            # ... 다른 분석 작업들
        }

        results = {}
        for key, future in futures.items():
            try:
                results[key] = future.result(timeout=180)
            except TimeoutError:
                logger.warning(f"{key} analysis timed out")
                results[key] = None

        return results
```

**예상 효과:**
- LLM 분석 단계에서 **40-60% 시간 단축** (5개 분석이 순차적이면 5x → 병렬이면 1x)
- 전체 워크플로우에서 **20-30% 시간 단축**

---

### 2. 데이터 수집 병렬 처리 증가 ⭐⭐⭐

**현재 상태:**
```python
# constants.py:249-252
PARALLEL_CONFIG = {
    'max_workers_data_collection': 3,  # Phase 1
    'max_workers_pr_data': 2,          # Phase 2
    # ...
}
```

**문제점:**
- 데이터 수집 Phase 1에서 3개 워커만 사용 (commits, PRs, issues)
- PR 데이터 처리 Phase 2에서 2개 워커만 사용
- 대부분의 시스템에서 더 많은 동시 실행 가능

**개선 방안:**
```python
# constants.py
PARALLEL_CONFIG = {
    'max_workers_data_collection': 5,  # 3 → 5 증가
    'max_workers_pr_data': 4,          # 2 → 4 증가
    'max_workers_pr_fetch': 8,         # 5 → 8 증가 (pr_collector.py:122)
    # ...
}
```

**동적 워커 수 설정 (선택적):**
```python
import os

def get_optimal_workers(task_type: str) -> int:
    """CPU 코어 수에 기반한 최적 워커 수 계산"""
    cpu_count = os.cpu_count() or 4

    if task_type == 'io_bound':  # API 호출, LLM
        return min(cpu_count * 2, 10)  # I/O bound는 2x
    elif task_type == 'cpu_bound':  # 분석, 계산
        return cpu_count
    else:
        return 4
```

**예상 효과:**
- Phase 1 데이터 수집: **15-25% 시간 단축**
- Phase 2 PR 처리: **25-40% 시간 단축**

---

### 3. API 캐시 전략 최적화 ⭐⭐

**현재 상태:**
```python
# api_client.py:91, constants.py:387
cache_expire_after=3600,  # 모든 엔드포인트에 1시간
```

**문제점:**
- 모든 API 엔드포인트에 동일한 캐시 만료 시간 적용
- Commits/tags는 거의 변경되지 않음 → 더 길게 캐싱 가능
- Issues/PRs는 자주 변경됨 → 짧은 캐싱이 더 적절할 수 있음

**개선 방안:**
```python
# api_client.py
class GitHubApiClient:
    # 엔드포인트별 캐시 TTL 매핑
    CACHE_TTL_MAP = {
        'commits': 86400,      # 24시간 (커밋은 변경되지 않음)
        'tags': 86400,         # 24시간
        'branches': 7200,      # 2시간
        'pulls': 1800,         # 30분 (자주 변경)
        'issues': 1800,        # 30분
        'reviews': 3600,       # 1시간
        'default': 3600,       # 1시간
    }

    def _get_cache_ttl(self, path: str) -> int:
        """엔드포인트 경로에 기반한 캐시 TTL 반환"""
        for key, ttl in self.CACHE_TTL_MAP.items():
            if key in path:
                return ttl
        return self.CACHE_TTL_MAP['default']

    def _get_session(self) -> requests.Session:
        if self.session is None:
            if self.enable_cache:
                # URL 패턴별로 다른 TTL 적용
                from requests_cache import CachedSession
                from requests_cache.policy import ExpirationTime

                self.session = CachedSession(
                    cache_name=str(cache_path),
                    backend="sqlite",
                    expire_after=self._build_expiry_map(),
                    allowable_codes=[200, 301, 302],
                    allowable_methods=["GET", "HEAD"],
                )
```

**대안 - 캐시 워밍 (Cache Warming):**
```python
def warm_cache(self, repo: str, months: int):
    """자주 사용되는 데이터를 미리 캐싱"""
    # 백그라운드에서 주요 엔드포인트 사전 로딩
    endpoints = [
        f"repos/{repo}/commits",
        f"repos/{repo}/pulls",
        f"repos/{repo}/branches",
    ]

    with ThreadPoolExecutor(max_workers=3) as executor:
        futures = [executor.submit(self.request_list, ep) for ep in endpoints]
        # 결과는 캐시에 저장됨
```

**예상 효과:**
- 캐시 히트율 **10-20% 증가**
- 반복 실행 시 **15-25% 시간 단축**

---

### 4. Phase 1/2 오버래핑 실행 ⭐⭐

**현재 상태:**
```python
# collector.py:116-119
phase1_result = self._collect_phase_one(repo, since, filters, author)
pull_request_examples, reviews = self._collect_phase_two(
    repo, since, filters, phase1_result.pr_metadata
)
```

**문제점:**
- Phase 1이 완전히 끝난 후에만 Phase 2 시작
- Phase 2는 PR 메타데이터만 필요하므로 Phase 1의 일부 완료 후 시작 가능

**개선 방안:**
```python
# collector.py
def collect(self, repo: str, months: int, filters: Optional[AnalysisFilters] = None, author: Optional[str] = None):
    """Overlapping Phase 1 and Phase 2 execution"""

    from queue import Queue
    pr_metadata_queue = Queue()

    def phase_one_with_streaming():
        """Phase 1 실행하면서 PR 메타데이터를 큐에 스트리밍"""
        # commits, issues 수집
        commits = self.commit_collector.count_commits(...)
        issues = self.issue_collector.count_issues(...)

        # PR 수집하면서 메타데이터를 큐에 전달
        pull_requests, pr_metadata = self.pr_collector.list_pull_requests(...)
        pr_metadata_queue.put(pr_metadata)  # Phase 2가 시작할 수 있게 신호

        return commits, pull_requests, issues

    def phase_two_consumer():
        """큐에서 PR 메타데이터를 받아 Phase 2 시작"""
        pr_metadata = pr_metadata_queue.get()  # Phase 1 PR 수집 완료 대기
        return self._collect_phase_two(repo, since, filters, pr_metadata)

    # 두 Phase를 병렬로 실행
    with ThreadPoolExecutor(max_workers=2) as executor:
        phase1_future = executor.submit(phase_one_with_streaming)
        phase2_future = executor.submit(phase_two_consumer)

        commits, pull_requests, issues = phase1_future.result()
        pull_request_examples, reviews = phase2_future.result()
```

**예상 효과:**
- Phase 간 대기 시간 **제거**
- 전체 데이터 수집 **10-15% 시간 단축**

---

### 5. SQLite 캐시 DB 최적화 ⭐

**현재 상태:**
- SQLite 캐시 사용 중이지만 인덱싱 정보 없음
- 연결 풀링 설정 없음

**개선 방안:**
```python
# api_client.py 또는 새로운 cache_optimizer.py
def optimize_cache_db(cache_path: Path):
    """캐시 DB에 인덱스 추가 및 최적화"""
    import sqlite3

    conn = sqlite3.connect(cache_path)
    cursor = conn.cursor()

    # 인덱스 추가 (requests-cache 테이블 구조에 맞게)
    try:
        cursor.execute("""
            CREATE INDEX IF NOT EXISTS idx_cache_key
            ON responses(key)
        """)
        cursor.execute("""
            CREATE INDEX IF NOT EXISTS idx_cache_expires
            ON responses(expires)
        """)

        # 만료된 캐시 정리
        cursor.execute("DELETE FROM responses WHERE expires < datetime('now')")

        # VACUUM으로 DB 파일 크기 최적화
        cursor.execute("VACUUM")

        conn.commit()
    except sqlite3.OperationalError as e:
        logger.warning(f"Cache optimization failed: {e}")
    finally:
        conn.close()

# 정기적으로 실행
def maintain_cache():
    """캐시 유지보수 - 만료된 항목 제거"""
    cache_path = Path.home() / ".cache" / "github_feedback" / "api_cache.sqlite"
    if cache_path.exists():
        optimize_cache_db(cache_path)
```

**SQLite 성능 튜닝:**
```python
# CachedSession 생성 시
import sqlite3
from requests_cache import CachedSession

# SQLite 연결 옵션 최적화
def create_optimized_cache(cache_path: str):
    session = CachedSession(
        cache_name=cache_path,
        backend="sqlite",
        expire_after=3600,
    )

    # 내부 SQLite 연결에 성능 설정 적용
    if hasattr(session.cache, 'connection'):
        conn = session.cache.connection()
        conn.execute("PRAGMA journal_mode=WAL")       # Write-Ahead Logging
        conn.execute("PRAGMA synchronous=NORMAL")      # 디스크 동기화 완화
        conn.execute("PRAGMA cache_size=-64000")       # 64MB 메모리 캐시
        conn.execute("PRAGMA temp_store=MEMORY")       # 임시 테이블을 메모리에

    return session
```

**예상 효과:**
- 캐시 조회 **20-30% 속도 향상**
- 캐시 저장 **15-25% 속도 향상**
- DB 파일 크기 **10-20% 감소**

---

### 6. 메모리 사용 최적화 ⭐

**현재 상태:**
- 대량의 PR 파일 리스트를 메모리에 모두 로드
- 큰 저장소에서 메모리 부족 가능성

**개선 방안:**
```python
# pr_collector.py
def collect_pull_request_details_streaming(self, repo: str, number: int) -> PullRequestReviewBundle:
    """PR 상세 정보를 스트리밍 방식으로 수집 (메모리 효율적)"""

    # 파일 수가 많은 경우 페이징 처리
    files_count = self.api_client.request_json(f"repos/{repo}/pulls/{number}")["changed_files"]

    if files_count > 100:  # 파일이 많으면 스트리밍
        files = []
        page = 1
        per_page = 30

        while len(files) < files_count:
            page_files = self.api_client.request_list(
                f"repos/{repo}/pulls/{number}/files",
                {"page": page, "per_page": per_page}
            )

            # 필요한 정보만 추출하여 메모리 절약
            for entry in page_files:
                files.append(
                    PullRequestFile(
                        filename=entry["filename"],
                        status=entry["status"],
                        additions=entry.get("additions", 0),
                        deletions=entry.get("deletions", 0),
                        changes=entry.get("changes", 0),
                        patch=None,  # 큰 patch는 제외 (필요시에만 로드)
                    )
                )

            if len(page_files) < per_page:
                break
            page += 1
    else:
        # 파일이 적으면 기존 방식
        files_payload = self.api_client.request_all(...)
        files = [PullRequestFile(...) for entry in files_payload]

    return PullRequestReviewBundle(files=files, ...)
```

**제너레이터 활용:**
```python
def iter_commits(self, repo: str, since: datetime, filters: AnalysisFilters):
    """커밋을 제너레이터로 반환하여 메모리 절약"""
    for branch in self._get_branches_to_process(repo, filters):
        params = build_commits_params(sha=branch, since=since.isoformat())

        page = 1
        while True:
            commits_page = self.api_client.request_list(
                f"repos/{repo}/commits",
                params | {"page": page, "per_page": 100}
            )

            if not commits_page:
                break

            for commit in commits_page:
                yield commit  # 한 번에 하나씩 반환

            page += 1
```

**예상 효과:**
- 메모리 사용량 **30-50% 감소**
- 큰 저장소에서 OOM(Out Of Memory) 오류 방지

---

### 7. GraphQL API 활용 (선택적) ⭐

**현재 상태:**
- 모든 데이터를 REST API로 수집
- 여러 번의 API 호출 필요

**개선 방안:**
```python
# graphql_client.py (새 파일)
def fetch_pr_with_reviews_graphql(repo: str, pr_numbers: List[int]) -> List[Dict]:
    """GraphQL로 PR과 리뷰를 한 번에 가져오기"""

    query = """
    query($owner: String!, $name: String!, $numbers: [Int!]!) {
      repository(owner: $owner, name: $name) {
        pullRequests(first: 100, numbers: $numbers) {
          nodes {
            number
            title
            body
            author { login }
            additions
            deletions
            changedFiles
            reviews(first: 100) {
              nodes {
                body
                author { login }
              }
            }
            comments(first: 100) {
              nodes {
                body
                author { login }
              }
            }
            files(first: 100) {
              nodes {
                path
                additions
                deletions
              }
            }
          }
        }
      }
    }
    """

    owner, name = repo.split('/')
    response = requests.post(
        "https://api.github.com/graphql",
        json={
            "query": query,
            "variables": {
                "owner": owner,
                "name": name,
                "numbers": pr_numbers
            }
        },
        headers={"Authorization": f"Bearer {pat}"}
    )

    return response.json()["data"]["repository"]["pullRequests"]["nodes"]
```

**REST vs GraphQL 비교:**
- **REST**: PR 10개 + 리뷰 10개 + 코멘트 10개 = **30 API 호출**
- **GraphQL**: **1 API 호출**로 모든 데이터 획득

**예상 효과:**
- API 호출 횟수 **70-90% 감소**
- 네트워크 레이턴시 **50-70% 감소**
- Rate limit 소비 **대폭 절감**

---

## 📈 구현 우선순위 및 예상 효과

| 우선순위 | 개선 영역 | 난이도 | 예상 효과 | 구현 시간 |
|---------|----------|--------|----------|---------|
| 1 | LLM 분석 병렬화 | ⭐⭐ | 20-30% 단축 | 2-4시간 |
| 2 | 데이터 수집 병렬 처리 증가 | ⭐ | 15-25% 단축 | 1-2시간 |
| 3 | API 캐시 전략 최적화 | ⭐⭐⭐ | 15-25% 단축 | 4-6시간 |
| 4 | SQLite 캐시 최적화 | ⭐⭐ | 10-15% 단축 | 2-3시간 |
| 5 | Phase 오버래핑 | ⭐⭐⭐ | 10-15% 단축 | 3-5시간 |
| 6 | 메모리 최적화 | ⭐⭐ | 메모리 절약 | 3-4시간 |
| 7 | GraphQL API | ⭐⭐⭐⭐ | 50-70% 단축 | 8-12시간 |

**전체 예상 효과:** 우선순위 1-4를 구현하면 **전체 실행 시간 40-60% 단축** 가능

---

## 🚀 빠른 시작 가이드

### 즉시 적용 가능한 개선 (5분 내)

**1. 워커 수 증가:**
```python
# github_feedback/constants.py 수정
PARALLEL_CONFIG = {
    'max_workers_data_collection': 5,  # 3 → 5
    'max_workers_pr_data': 4,          # 2 → 4
    'max_workers_llm_analysis': 6,     # 4 → 6
    'max_workers_pr_fetch': 8,         # 5 → 8
    # ... 나머지 동일
}
```

**2. 캐시 만료 시간 증가 (안정적인 데이터용):**
```python
# github_feedback/constants.py 수정
API_DEFAULTS = {
    'cache_expire_seconds': 7200,  # 3600 → 7200 (2시간)
    # ... 나머지 동일
}
```

### 중기 개선 (1-2일)

**LLM 분석 병렬화 구현**
- `analyzer.py`에 `analyze_all_feedback_parallel()` 메서드 추가
- 기존 순차 호출을 병렬 호출로 변경

### 장기 개선 (1-2주)

**GraphQL API 마이그레이션**
- `graphql_client.py` 모듈 생성
- 핵심 데이터 수집 로직을 GraphQL로 전환
- 기존 REST API는 fallback으로 유지

---

## 🔍 성능 모니터링

개선 효과를 측정하기 위한 메트릭:

```python
# performance_monitor.py (새 파일)
import time
from contextlib import contextmanager
from dataclasses import dataclass
from typing import Dict

@dataclass
class PerformanceMetrics:
    """성능 메트릭 수집"""
    phase_timings: Dict[str, float]
    api_calls: int
    cache_hits: int
    cache_misses: int
    memory_peak_mb: float

@contextmanager
def measure_phase(phase_name: str, metrics: PerformanceMetrics):
    """각 단계의 실행 시간 측정"""
    start = time.time()
    try:
        yield
    finally:
        duration = time.time() - start
        metrics.phase_timings[phase_name] = duration
        logger.info(f"{phase_name} completed in {duration:.2f}s")

# 사용 예시
metrics = PerformanceMetrics(phase_timings={}, ...)

with measure_phase("data_collection", metrics):
    result = collector.collect(repo, months, filters)

with measure_phase("llm_analysis", metrics):
    analysis = analyzer.analyze(result)

print(f"Total time: {sum(metrics.phase_timings.values()):.2f}s")
print(f"Cache hit rate: {metrics.cache_hits / (metrics.cache_hits + metrics.cache_misses):.1%}")
```

---

## 💡 추가 고려사항

### Rate Limiting 관리
```python
# 병렬 처리 증가 시 GitHub API rate limit 주의
# api_client.py에 rate limit 체크 추가

def check_rate_limit(self) -> Dict[str, int]:
    """현재 rate limit 상태 확인"""
    response = self.request_json("/rate_limit")
    core = response["resources"]["core"]

    return {
        "remaining": core["remaining"],
        "limit": core["limit"],
        "reset_at": datetime.fromtimestamp(core["reset"])
    }

def wait_if_rate_limited(self):
    """Rate limit에 가까우면 대기"""
    status = self.check_rate_limit()

    if status["remaining"] < 100:  # 100개 미만이면 대기
        wait_seconds = (status["reset_at"] - datetime.now()).total_seconds()
        logger.warning(f"Rate limit low, waiting {wait_seconds:.0f}s")
        time.sleep(wait_seconds + 1)
```

### 에러 핸들링 강화
```python
# 병렬 처리 증가로 실패 확률 증가 → retry 로직 강화
from tenacity import retry, stop_after_attempt, wait_exponential

@retry(
    stop=stop_after_attempt(5),
    wait=wait_exponential(multiplier=1, min=2, max=10)
)
def resilient_api_call(self, path: str, params: dict):
    """재시도 로직이 강화된 API 호출"""
    return self.api_client.request_list(path, params)
```

---

## 📚 참고 자료

- [GitHub REST API Rate Limiting](https://docs.github.com/en/rest/overview/resources-in-the-rest-api#rate-limiting)
- [GitHub GraphQL API](https://docs.github.com/en/graphql)
- [Python ThreadPoolExecutor Best Practices](https://docs.python.org/3/library/concurrent.futures.html)
- [SQLite Performance Tuning](https://www.sqlite.org/pragma.html)
- [requests-cache Documentation](https://requests-cache.readthedocs.io/)

---

## 🎓 결론

이 프로젝트는 이미 많은 최적화가 적용되어 있습니다:
- ✅ ThreadPoolExecutor 병렬 처리
- ✅ SQLite 캐싱
- ✅ Early stopping 조건
- ✅ 중복 제거 로직

위에서 제안한 개선사항들을 단계적으로 적용하면:
1. **즉시 개선 (우선순위 1-2)**: 설정 변경만으로 **15-25% 성능 향상**
2. **중기 개선 (우선순위 3-5)**: 코드 리팩토링으로 **추가 20-30% 향상**
3. **장기 개선 (우선순위 6-7)**: 아키텍처 변경으로 **총 60-80% 향상 가능**

가장 빠른 효과를 위해서는 **우선순위 1-2번을 먼저 구현**하는 것을 추천드립니다.
