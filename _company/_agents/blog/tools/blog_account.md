# 🔑 블로그 계정 및 공유 설정

각 블로그 플랫폼(네이버, 티스토리, 구글 블로거, 워드프레스) 연동 및 자동 발행을 위한 통합 설정입니다. 이 파일이 위치한 폴더의 `blog_account.json` 파일에 정보를 입력하시면 블로그 에이전트가 이를 읽어 자동으로 글 작성 및 발행을 수행합니다.

## 설정 항목 (blog_account.json 입력 가이드)

| 키 | 설명 | 채우는 법 |
|---|---|---|
| `WP_DOMAIN` | [워드프레스] 블로그 주소 | 만드신 워드프레스 주소 (예: `myblog.wordpress.com` 또는 개인 도메인) |
| `WP_USERNAME` | [워드프레스] 사용자 ID | 워드프레스 관리자 계정 ID 또는 이메일 주소 |
| `WP_APP_PASSWORD` | [워드프레스] 앱 비밀번호 | 워드프레스 관리자 → 사용자 → 프로필 메뉴 최하단에서 생성한 20자리 앱 비밀번호 |
| `BLOGGER_BLOG_ID` | [구글블로거] 블로그 주소 ID | 구글 블로거의 고유 식별 주소명 (예: `congcandy` 또는 숫자형 ID) |
| `BLOGGER_API_KEY` | [구글블로거] API 키/토큰 | 구글 클라우드 콘솔에서 발급한 Blogger API 키 또는 OAuth 액세스 토큰 |
| `NAVER_BLOG_ID` | [네이버] 블로그 ID | 네이버 블로그 ID (예: `naver_user_id`) |
| `TISTORY_BLOG_ID` | [티스토리] 블로그 ID | 티스토리 블로그 주소 ID (예: `blogname`) |
| `COMPETITOR_BLOGS` | 경쟁 또는 벤치마킹 블로그 목록 | 예: `["https://cooking-mom.tistory.com", "https://studystory.tistory.com"]` |
| `OLLAMA_URL` | 로컬 LLM 주소 | 기본 `http://127.0.0.1:11434`. |
| `MODEL` | 분석 및 초안 생성용 LLM 모델 명 | 기본값은 비워두거나 `gemma2:2b` 등 사용을 원하는 모델 기재. |

## 저장 위치 및 보안
`blog_account.json`은 개인 설정 파일이므로 Git에 공유되지 않고 로컬에 안전하게 보관됩니다.
