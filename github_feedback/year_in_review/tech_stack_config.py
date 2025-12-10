"""기술 스택 카테고리 및 RPG 장비 시스템 설정."""

# 기술별 카테고리 분류 (언어, 프레임워크, 도구/DB)
TECH_CATEGORIES = {
    # 프로그래밍 언어 (주무기)
    "Python": "language",
    "JavaScript": "language",
    "TypeScript": "language",
    "Java": "language",
    "Go": "language",
    "Rust": "language",
    "C++": "language",
    "C": "language",
    "C#": "language",
    "Ruby": "language",
    "PHP": "language",
    "Swift": "language",
    "Kotlin": "language",
    "Dart": "language",
    "Scala": "language",
    "R": "language",
    "Shell": "language",
    "Bash": "language",
    "PowerShell": "language",
    "Lua": "language",
    "Perl": "language",
    "Haskell": "language",
    "Elixir": "language",
    "Clojure": "language",

    # 프레임워크 & 라이브러리 (보조무기)
    "React": "framework",
    "Vue": "framework",
    "Angular": "framework",
    "Next.js": "framework",
    "Nuxt.js": "framework",
    "Svelte": "framework",
    "Django": "framework",
    "Flask": "framework",
    "FastAPI": "framework",
    "Express": "framework",
    "NestJS": "framework",
    "Spring": "framework",
    "Spring Boot": "framework",
    "Rails": "framework",
    "Laravel": "framework",
    "ASP.NET": "framework",
    "Node.js": "framework",
    "Deno": "framework",
    "TensorFlow": "framework",
    "PyTorch": "framework",
    "Pandas": "framework",
    "NumPy": "framework",
    "Scikit-learn": "framework",

    # 도구, DB, 인프라 (장신구/악세서리)
    "Docker": "tool",
    "Kubernetes": "tool",
    "PostgreSQL": "tool",
    "MySQL": "tool",
    "MongoDB": "tool",
    "Redis": "tool",
    "Elasticsearch": "tool",
    "RabbitMQ": "tool",
    "Kafka": "tool",
    "Git": "tool",
    "GitHub Actions": "tool",
    "Jenkins": "tool",
    "CircleCI": "tool",
    "Terraform": "tool",
    "Ansible": "tool",
    "AWS": "tool",
    "GCP": "tool",
    "Azure": "tool",
    "Nginx": "tool",
    "Apache": "tool",
    "GraphQL": "tool",
    "REST API": "tool",
    "gRPC": "tool",
    "WebSocket": "tool",
    "HTML": "tool",
    "CSS": "tool",
    "SCSS": "tool",
    "Tailwind": "tool",
    "Webpack": "tool",
    "Vite": "tool",
    "Babel": "tool",
    "ESLint": "tool",
    "Prettier": "tool",
    "Jest": "tool",
    "Pytest": "tool",
    "Cypress": "tool",
    "Selenium": "tool",
}

# 특정 기술에 대한 커스텀 아이콘 및 무기명
TECH_CUSTOM_ICONS = {
    # 언어
    "Python": {
        "icon": "🐍",
        "weapon_name": "파이썬 엑스칼리버",
        "weapon_traits": [
            "⚡ 강력한 범용성: 데이터 분석부터 웹 개발까지 모든 영역을 지배한다",
            "📚 방대한 라이브러리 군단: 무한한 패키지로 어떤 문제든 해결 가능",
            "🎯 가독성의 축복: 명확하고 우아한 코드로 팀원들의 찬사를 받는다"
        ]
    },
    "JavaScript": {
        "icon": "⚡",
        "weapon_name": "자바스크립트 소울캘리버",
        "weapon_traits": [
            "🌐 웹의 지배자: 브라우저와 서버를 모두 장악하는 양날의 검",
            "🔄 비동기 마법진: Promise와 async/await로 시공간을 자유자재로 다룬다",
            "🎨 유연성의 극의: 함수형과 객체지향을 넘나드는 카멜레온 같은 힘"
        ]
    },
    "TypeScript": {
        "icon": "🛡️",
        "weapon_name": "타입세이프 수호방패",
        "weapon_traits": [
            "🛡️ 타입 안전의 요새: 컴파일 타임에 버그를 차단하는 철벽 방어",
            "💡 인텔리센스 부스트: IDE의 자동완성으로 생산성 3배 증폭",
            "🔧 리팩토링의 신: 안전하게 대규모 코드베이스를 재구성한다"
        ]
    },
    "Java": {
        "icon": "☕",
        "weapon_name": "자바 레전더리 블레이드",
        "weapon_traits": [
            "🏢 엔터프라이즈의 왕: 대규모 시스템의 기둥이 되는 견고함",
            "♻️ JVM의 힘: 플랫폼 독립성으로 어디서든 실행 가능",
            "🎯 객체지향 완성형: SOLID 원칙을 체화한 설계의 교과서"
        ]
    },
    "Go": {
        "icon": "🐹",
        "weapon_name": "고랭 라이트닝 데거",
        "weapon_traits": [
            "⚡ 경이로운 속도: 컴파일과 실행 모두 초고속으로 처리",
            "🎯 동시성의 달인: 고루틴으로 수천 개의 작업을 우아하게 병렬 처리",
            "🔧 단순함의 미학: 최소한의 문법으로 최대의 효과를 발휘"
        ]
    },
    "Rust": {
        "icon": "🦀",
        "weapon_name": "러스트 이모탈 아머",
        "weapon_traits": [
            "🔒 메모리 안전 보장: 소유권 시스템으로 런타임 에러 zero",
            "⚡ C++ 급 성능: 가비지 컬렉터 없이도 극한의 속도 달성",
            "🛡️ 동시성 안전: 컴파일 타임에 데이터 레이스를 원천 차단"
        ]
    },
    "C++": {
        "icon": "⚙️",
        "weapon_name": "C++ 파워 배틀액스",
        "weapon_traits": [
            "💪 저수준 제어권: 하드웨어를 직접 제어하는 절대적인 성능",
            "🎮 게임 엔진의 심장: AAA급 게임을 탄생시키는 원동력",
            "⚙️ 템플릿 메타프로그래밍: 컴파일 타임에 최적화를 극대화"
        ]
    },
    "Ruby": {
        "icon": "💎",
        "weapon_name": "루비 크리스탈 블레이드",
        "weapon_traits": [
            "💎 개발자 행복 최우선: 가독성과 생산성을 극대화한 문법",
            "🚀 빠른 프로토타이핑: 아이디어를 즉시 실현하는 마법",
            "🎨 메타프로그래밍의 예술: 코드가 코드를 생성하는 경지"
        ]
    },
    "PHP": {
        "icon": "🐘",
        "weapon_name": "PHP 이터널 워보우",
        "weapon_traits": [
            "🌐 웹 개발의 전설: 전 세계 웹사이트의 80%를 구동",
            "🔄 지속적인 진화: PHP 8로 현대적인 기능 대폭 강화",
            "🎯 워드프레스 파워: CMS 생태계의 절대 강자"
        ]
    },
    "Swift": {
        "icon": "🦅",
        "weapon_name": "스위프트 윙즈 오브 프리덤",
        "weapon_traits": [
            "🍎 애플 생태계 지배: iOS/macOS 개발의 필수 무기",
            "⚡ 안전하면서도 빠름: 옵셔널로 null 안전성 확보",
            "🎨 모던한 문법: 함수형과 프로토콜 지향 프로그래밍의 조화"
        ]
    },
    "Kotlin": {
        "icon": "🎯",
        "weapon_name": "코틀린 프리시전 스피어",
        "weapon_traits": [
            "🎯 Null 안전 정밀타: Null 포인터 예외를 완벽히 차단",
            "☕ 자바와 100% 호환: 기존 코드와 매끄럽게 통합",
            "📱 안드로이드 공식언어: 구글이 인정한 모바일 개발의 미래"
        ]
    },
    "Dart": {
        "icon": "🎯",
        "weapon_name": "다트 플러터 섀도우 나이프",
        "weapon_traits": [
            "📱 크로스플랫폼의 달인: 하나의 코드로 iOS/Android 동시 정복",
            "🎨 핫 리로드 마법: 코드 변경을 즉시 화면에 반영",
            "⚡ 네이티브급 성능: AOT 컴파일로 빠른 실행 속도"
        ]
    },

    # 프레임워크
    "React": {
        "icon": "⚛️",
        "weapon_name": "리액트 코스믹 오브",
        "weapon_traits": [
            "⚛️ 컴포넌트 원자론: UI를 재사용 가능한 조각으로 분해",
            "🔄 가상 DOM 마법: 효율적인 렌더링으로 초고속 UI 업데이트",
            "🌊 단방향 데이터 흐름: 예측 가능한 상태 관리로 버그 최소화"
        ]
    },
    "Vue": {
        "icon": "💚",
        "weapon_name": "뷰 에메랄드 그리모어",
        "weapon_traits": [
            "📖 쉬운 학습 곡선: 직관적인 문법으로 빠른 습득 가능",
            "⚡ 리액티브 시스템: 데이터 변경을 자동으로 UI에 반영",
            "🔧 점진적 도입: 필요한 만큼만 사용하는 유연성"
        ]
    },
    "Angular": {
        "icon": "🅰️",
        "weapon_name": "앵귤러 포트리스 실드",
        "weapon_traits": [
            "🏢 대규모 앱의 기둥: 엔터프라이즈급 프로젝트에 최적화",
            "💉 의존성 주입: 테스트 가능하고 유지보수 쉬운 구조",
            "📦 올인원 솔루션: 라우팅, 폼, HTTP 모두 기본 제공"
        ]
    },
    "Django": {
        "icon": "🎸",
        "weapon_name": "장고 알케미 기타",
        "weapon_traits": [
            "🔐 보안 마법진: SQL 인젝션, CSRF 등을 자동으로 방어",
            "📦 배터리 포함: ORM, 인증, 관리자 페이지 등 모두 기본 제공",
            "🚀 빠른 개발: '완벽주의자를 위한 데드라인' 철학 구현"
        ]
    },
    "Flask": {
        "icon": "🧪",
        "weapon_name": "플라스크 마스터 포션",
        "weapon_traits": [
            "🧪 마이크로 프레임워크: 필요한 것만 골라 사용하는 자유",
            "🎯 유연성의 극대화: 어떤 구조든 원하는 대로 설계 가능",
            "📚 풍부한 확장 생태계: 필요한 기능을 플러그인으로 추가"
        ]
    },
    "FastAPI": {
        "icon": "⚡",
        "weapon_name": "FastAPI 썬더 랜스",
        "weapon_traits": [
            "⚡ 초고속 성능: Node.js, Go에 필적하는 속도",
            "📝 자동 문서화: API 문서가 자동으로 생성되는 마법",
            "🔍 타입 힌트 활용: Pydantic으로 데이터 검증 자동화"
        ]
    },
    "Spring": {
        "icon": "🌱",
        "weapon_name": "스프링 라이프트리 스태프",
        "weapon_traits": [
            "🌱 자바 생태계의 왕: 엔터프라이즈 개발의 표준",
            "💉 강력한 IoC/DI: 느슨한 결합으로 테스트와 유지보수 용이",
            "🔧 스프링 부트: 설정 최소화로 빠른 개발 시작"
        ]
    },
    "Next.js": {
        "icon": "▲",
        "weapon_name": "Next.js 디멘션 블레이드",
        "weapon_traits": [
            "🚀 SSR/SSG 마법: SEO와 성능을 동시에 잡는다",
            "📁 파일 기반 라우팅: 폴더 구조가 곧 URL 구조",
            "⚡ 제로 컨피그: 복잡한 설정 없이 바로 시작 가능"
        ]
    },
    "Express": {
        "icon": "🚂",
        "weapon_name": "익스프레스 하이퍼 트레인",
        "weapon_traits": [
            "🚂 Node.js의 기본템: 가장 인기 있는 백엔드 프레임워크",
            "🔧 미들웨어 체인: 요청 처리를 모듈화하여 조립",
            "🎯 미니멀리즘: 핵심만 제공하고 나머지는 자유롭게"
        ]
    },
    "Node.js": {
        "icon": "🟢",
        "weapon_name": "노드 마나 코어",
        "weapon_traits": [
            "🔄 논블로킹 I/O: 비동기 처리로 높은 동시 접속 처리",
            "📦 NPM 생태계: 100만 개 이상의 패키지 보물창고",
            "⚡ V8 엔진: 구글의 강력한 JavaScript 엔진 탑재"
        ]
    },

    # 도구
    "Docker": {
        "icon": "🐋",
        "weapon_name": "도커 컨테이너 플레이트",
        "weapon_traits": [
            "📦 환경 일관성: '내 컴퓨터에선 되는데?' 문제 완벽 해결",
            "🚢 이식성의 극의: 어떤 환경에서든 동일하게 실행",
            "⚡ 빠른 배포: 가상머신보다 훨씬 가볍고 빠르다"
        ]
    },
    "Kubernetes": {
        "icon": "☸️",
        "weapon_name": "쿠버네티스 오케스트라 배턴",
        "weapon_traits": [
            "🎼 컨테이너 오케스트라: 수백 개의 컨테이너를 지휘",
            "⚖️ 자동 스케일링: 트래픽에 따라 자동으로 확장/축소",
            "🔄 자가 치유: 문제 발생 시 자동으로 복구"
        ]
    },
    "PostgreSQL": {
        "icon": "🐘",
        "weapon_name": "포스트그레 데이터 볼트",
        "weapon_traits": [
            "🐘 강력한 RDBMS: ACID 보장과 복잡한 쿼리 처리",
            "📊 JSON 지원: NoSQL의 유연성도 함께 제공",
            "🔧 확장성: 커스텀 함수, 타입, 인덱스 생성 가능"
        ]
    },
    "MySQL": {
        "icon": "🐬",
        "weapon_name": "MySQL 크리스탈 아카이브",
        "weapon_traits": [
            "🌐 웹의 친구: 워드프레스 등 수많은 웹앱의 기반",
            "⚡ 빠른 읽기: 읽기 중심 워크로드에 최적화",
            "🔄 복제 기능: 마스터-슬레이브로 고가용성 확보"
        ]
    },
    "MongoDB": {
        "icon": "🍃",
        "weapon_name": "몽고DB 플렉시블 스크롤",
        "weapon_traits": [
            "📄 문서 지향: JSON 형태로 직관적인 데이터 저장",
            "🔄 스키마 유연성: 구조 변경이 자유로운 NoSQL",
            "📈 수평 확장: 샤딩으로 무한 확장 가능"
        ]
    },
    "Redis": {
        "icon": "🔴",
        "weapon_name": "레디스 스피드 탈리스만",
        "weapon_traits": [
            "⚡ 초고속 캐시: 메모리 기반으로 밀리초 응답",
            "🎯 다양한 자료구조: String, List, Set, Hash 등 지원",
            "🔄 Pub/Sub 메시징: 실시간 이벤트 처리에 최적"
        ]
    },
    "Git": {
        "icon": "🌿",
        "weapon_name": "깃 타임워프 스크롤",
        "weapon_traits": [
            "⏰ 시간 여행: 과거 어느 시점으로든 되돌릴 수 있다",
            "🌿 브랜치 마법: 무한한 분기로 안전한 실험 가능",
            "🤝 협업의 핵심: 여러 개발자의 작업을 효율적으로 병합"
        ]
    },
    "GitHub Actions": {
        "icon": "🤖",
        "weapon_name": "깃허브 오토메이션 골렘",
        "weapon_traits": [
            "🤖 CI/CD 자동화: 테스트와 배포를 자동으로 처리",
            "🔧 워크플로우 마법진: YAML로 복잡한 파이프라인 구성",
            "🌐 생태계 연동: 수천 개의 액션으로 무한 확장"
        ]
    },
    "AWS": {
        "icon": "☁️",
        "weapon_name": "AWS 클라우드 윙즈",
        "weapon_traits": [
            "☁️ 클라우드의 왕: 200개 이상의 서비스로 무엇이든 가능",
            "📈 무한 확장: 전 세계 어디서든 필요한 만큼 리소스 사용",
            "🔐 엔터프라이즈급 보안: 금융권도 신뢰하는 보안 체계"
        ]
    },
    "GraphQL": {
        "icon": "◆",
        "weapon_name": "GraphQL 쿼리 크리스탈",
        "weapon_traits": [
            "🎯 정확한 데이터 요청: 필요한 것만 정확히 받아온다",
            "🔗 관계형 쿼리: 여러 리소스를 한 번에 효율적으로 조회",
            "📝 자체 문서화: 스키마가 곧 API 문서"
        ]
    },
}

# 7단계 무기 등급 시스템
WEAPON_TIERS = [
    {
        "threshold": 60,
        "name": "신화",
        "prefix": "💎",
        "suffix": "신화 무기",
        "color": "#ec4899",
        "glow": "rgba(236, 72, 153, 0.3)"
    },
    {
        "threshold": 40,
        "name": "전설",
        "prefix": "⚔️",
        "suffix": "전설 무기",
        "color": "#fbbf24",
        "glow": "rgba(251, 191, 36, 0.3)"
    },
    {
        "threshold": 28,
        "name": "영웅",
        "prefix": "🗡️",
        "suffix": "영웅 무기",
        "color": "#f97316",
        "glow": "rgba(249, 115, 22, 0.3)"
    },
    {
        "threshold": 18,
        "name": "희귀",
        "prefix": "⚡",
        "suffix": "희귀 무기",
        "color": "#8b5cf6",
        "glow": "rgba(139, 92, 246, 0.3)"
    },
    {
        "threshold": 10,
        "name": "고급",
        "prefix": "🔪",
        "suffix": "고급 무기",
        "color": "#3b82f6",
        "glow": "rgba(59, 130, 246, 0.3)"
    },
    {
        "threshold": 5,
        "name": "일반",
        "prefix": "🔨",
        "suffix": "일반 무기",
        "color": "#10b981",
        "glow": "rgba(16, 185, 129, 0.3)"
    },
    {
        "threshold": 0,
        "name": "보조",
        "prefix": "🔧",
        "suffix": "보조 도구",
        "color": "#6b7280",
        "glow": "rgba(107, 114, 128, 0.3)"
    }
]

# 장비 슬롯 타입 (카테고리별)
EQUIPMENT_SLOTS = {
    "language": {"slot": "🎯 주무기", "priority": 1},
    "framework": {"slot": "🛡️ 보조무기", "priority": 2},
    "tool": {"slot": "💍 장신구", "priority": 3},
}


__all__ = ["TECH_CATEGORIES", "TECH_CUSTOM_ICONS", "WEAPON_TIERS", "EQUIPMENT_SLOTS"]
