#!/usr/bin/env python3
"""Blog Trend Reader (블로그 트랜드 읽기)

Scrapes or simulates trending Naver search keywords and suggests high-traffic topics
specifically optimized for study summaries, cooking side dishes, and mental wellness.
Incorporates duplicate checking for recipe topics and creates latest_trend_report.md.
"""
import os
import json
import sys
import time
import datetime
import re

# Set paths
HERE = os.path.dirname(os.path.abspath(__file__))
CONFIG_PATH = os.path.join(HERE, "blog_account.json")
QUEUE_PATH = os.path.join(HERE, "blog_queue.json")

# Calculate report path
COMPANY_DIR = os.path.abspath(os.path.join(HERE, "..", "..", ".."))
SESSIONS_DIR = os.path.join(COMPANY_DIR, "sessions")
REPORT_PATH = os.path.join(SESSIONS_DIR, "latest_trend_report.md")

def load_config():
    if not os.path.exists(CONFIG_PATH):
        return {}
    with open(CONFIG_PATH, "r", encoding="utf-8") as f:
        return json.load(f)

def get_completed_recipes():
    completed = set()
    if os.path.exists(QUEUE_PATH):
        try:
            with open(QUEUE_PATH, "r", encoding="utf-8") as f:
                queue_data = json.load(f)
            for entry in queue_data.get("completed_lessons", []):
                if entry.get("subject") == "요리/반찬":
                    lesson = entry.get("lesson", "")
                    match = re.search(r'recipe_(.*?)_\d+', lesson)
                    if match:
                        completed.add(match.group(1).strip())
                    elif lesson.endswith(".md"):
                        clean = lesson.replace("recipe_", "").replace(".md", "")
                        completed.add(clean.strip())
        except Exception as e:
            print(f"[WARN] Failed to read queue history: {e}")
    return completed

def select_recipe(pool, completed):
    for item in pool:
        if not any(comp in item or item in comp for comp in completed):
            return item
    return pool[0] if pool else "요리"

def search_web(query, num_results=3):
    """Performs a light web search using DuckDuckGo HTML service and returns top results."""
    import urllib.parse
    import urllib.request
    print(f"[TREND-SEARCH] Querying web for: '{query}'")
    try:
        encoded_query = urllib.parse.quote(query)
        url = f"https://html.duckduckgo.com/html/?q={encoded_query}"
        headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
        }
        req = urllib.request.Request(url, headers=headers)
        with urllib.request.urlopen(req, timeout=15) as response:
            html = response.read().decode('utf-8', errors='replace')
            
        result_blocks = html.split('<div class="links_main')
        results = []
        for block in result_blocks[1:]:
            if len(results) >= num_results:
                break
            url_match = re.search(r'class="result__url"\s+href="([^"]+)"[^>]*>([\s\S]*?)</a>', block)
            snippet_match = re.search(r'class="result__snippet"[^>]*>([\s\S]*?)</a>', block)
            if url_match:
                raw_url = url_match.group(1)
                parsed_url = urllib.parse.urlparse(raw_url)
                if parsed_url.netloc == "duckduckgo.com" and "uddg=" in parsed_url.query:
                    qs = urllib.parse.parse_qs(parsed_url.query)
                    final_url = qs.get("uddg", [raw_url])[0]
                else:
                    final_url = raw_url
                title = re.sub(r'<[^>]*>', '', url_match.group(2))
                title = re.sub(r'\s+', ' ', title).strip()
                snippet = ""
                if snippet_match:
                    snippet = re.sub(r'<[^>]*>', '', snippet_match.group(1))
                    snippet = re.sub(r'\s+', ' ', snippet).strip()
                if title and final_url:
                    results.append({"title": title, "url": final_url, "snippet": snippet})
        return results
    except Exception as e:
        print(f"[WARN] Trend web search failed: {e}")
        return []

def detect_surging_certificates():
    """
    1. 구글 트랜드 RSS를 읽어 실시간 핫 토픽 수집
    2. 뉴스 영역에서 '자격증 의무 선임 개정 가산점' 관련 급상승 언급 자격증 스캔
    """
    import urllib.request
    print("[INFO] Sensing Google Trends RSS (KR)...")
    trending_topics = []
    try:
        rss_url = "https://trends.google.co.kr/trends/trendingsearches/daily/rss?geo=KR"
        req = urllib.request.Request(rss_url, headers={"User-Agent": "Mozilla/5.0"})
        with urllib.request.urlopen(req, timeout=10) as response:
            xml_data = response.read()
        root = ET.fromstring(xml_data)
        for item in root.findall(".//item"):
            title = item.find("title")
            if title is not None and title.text:
                trending_topics.append(title.text.strip())
    except Exception as e:
        print(f"[WARN] Google Trends RSS fetch failed: {e}")

    # 2. 뉴스 영역에서 변동성 급상승 자격증 감지
    print("[INFO] Fetching real-time certificate news surge...")
    news_search = search_web("자격증 의무 선임 개정 가산점", 5)
    
    # 대표적인 추적 대상 자격증 후보 리스트
    candidate_certs = [
        "산업안전기사", "건설안전기사", "소방설비기사", "전기기사", "전기기능사",
        "SQLD", "ADsP", "정보처리기사", "국제무역사", "손해평가사", "컴퓨터활용능력",
        "사회복지사", "청소년지도사", "직업상담사", "토익", "오픽"
    ]
    
    surging_list = []
    seen_urls = set()
    
    # 뉴스 분석 루프
    for news in news_search:
        title_content = news["title"] + " " + news["snippet"]
        for cert in candidate_certs:
            if cert in title_content and news["url"] not in seen_urls:
                surging_list.append({
                    "subject": cert,
                    "title": news["title"],
                    "url": news["url"],
                    "snippet": news["snippet"],
                    "reason": "최신 뉴스 및 트랜드 내 언급량 검출"
                })
                seen_urls.add(news["url"])
                
    # 만약 뉴스에서 스파이크를 발견하지 못했다면 구글 실시간 검색어 기반 폴백 분석
    if not surging_list and trending_topics:
        for topic in trending_topics:
            for cert in candidate_certs:
                if (cert in topic or cert[:2] in topic) and cert not in [s["subject"] for s in surging_list]:
                    surging_list.append({
                        "subject": cert,
                        "title": f"실시간 검색 급상승 키워드: {topic}",
                        "url": "https://trends.google.co.kr",
                        "snippet": "구글 실시간 인기 급상승 검색어 트랜드 감지",
                        "reason": "구글 실시간 트랜드 차트 검출"
                    })
                    
    # 디폴트 폴백 (둘 다 감지되지 않을 시 업계 고정 핫 트랜드 제공)
    if not surging_list:
        surging_list = [
            {
                "subject": "산업안전기사",
                "title": "중대재해처벌법 및 안전 선임 개정 의무화 지속화",
                "url": "https://www.q-net.or.kr",
                "snippet": "최근 법정 의무 선임 자격 기준 개정안 통과로 안전보건관리직 수요 급증",
                "reason": "정부 규제 및 개정 법령 분석 기준"
            },
            {
                "subject": "전기기사",
                "title": "신재생 전력 설비 인프라 가산점 및 기술사 채용 확대",
                "url": "https://www.q-net.or.kr",
                "snippet": "전기설비 기술기준 개정 및 채용 가산점 확대로 대기업/공기업 필수 우대",
                "reason": "전력 기준 개정 트랜드 분석"
            }
        ]
        
    return surging_list[:3]

def main():
    if sys.platform.startswith('win'):
        try:
            sys.stdout.reconfigure(encoding='utf-8')
            sys.stderr.reconfigure(encoding='utf-8')
        except AttributeError:
            pass

    cfg = load_config()
    completed = get_completed_recipes()
    
    active_campaign_path = r"C:\Users\User\my-ai-office\scripts\active_campaign.json"
    active_subj = "청소년지도사"
    active_dish = None
    if os.path.exists(active_campaign_path):
        try:
            with open(active_campaign_path, "r", encoding="utf-8") as ac_f:
                ac_data = json.load(ac_f)
                active_subj = ac_data.get("subject", "청소년지도사")
                active_dish = ac_data.get("cooking_dish")
                print(f"[INFO] Sensed current business context: subject={active_subj}, dish={active_dish}")
        except Exception as ac_err:
            print(f"[WARN] Failed to load active_campaign.json: {ac_err}")

    # Fallback pools
    month = datetime.datetime.now().month
    if month in [6, 7, 8]:
        seasonal_pool = ["오이냉국", "열무비빔밥", "가지볶음", "메밀국수", "콩국수", "오이소박이", "호박볶음", "미역냉국"]
        toddler_pool = ["소고기 애호박 죽", "아기 계란찜", "닭고기 감자 진밥", "유아용 안매운 어묵볶음", "연두부 달걀탕"]
        banchan_pool = ["깻잎장아찌", "꽈리고추 멸치볶음", "오이무침", "소고기 장조림", "부추무침"]
    else:
        seasonal_pool = ["달래된장찌개", "냉이무침", "쑥국", "취나물무침", "봄조개 아욱국", "죽순볶음"]
        toddler_pool = ["소고기 쑥갓 죽", "아기 감자국", "아기 봄나물 비빔밥", "닭고기 완자전"]
        banchan_pool = ["마늘종무침", "계란장조림", "버섯볶음", "미역줄기볶음", "시금치나물"]

    selected_seasonal = select_recipe(seasonal_pool, completed)
    selected_toddler = select_recipe(toddler_pool, completed)
    selected_banchan = select_recipe(banchan_pool, completed)

    if active_dish:
        selected_seasonal = active_dish

    # 1. 대상 과목 및 요리 기본 서치
    print(f"[INFO] Running live web search for active subject: '{active_subj}'...")
    subj_query = f"{active_subj} 시험 공부 방법 과목"
    subj_search = search_web(subj_query, 3)
    
    print(f"[INFO] Running live web search for active cooking target: '{selected_seasonal}'...")
    dish_query = f"제철 {selected_seasonal} 요리법 비법"
    dish_search = search_web(dish_query, 3)

    # 2. 지능형 급상승(Surge) 자격증 및 무료 기출/자료 다운로드처 발굴
    surging_certs = detect_surging_certificates()
    
    print("[INFO] Running live web search for free study material resources...")
    download_search = search_web("자격증 기출문제 다운로드 cbt", 4)

    # Format search contexts for report
    subj_links_md = "\n".join([f"- [{r['title']}]({r['url']}): {r['snippet']}" for r in subj_search]) if subj_search else "- (실시간 검색 결과 없음)"
    dish_links_md = "\n".join([f"- [{r['title']}]({r['url']}): {r['snippet']}" for r in dish_search]) if dish_search else "- (실시간 검색 결과 없음)"
    
    surging_links_md = "\n".join([f"- [{s['subject']}]({s['url']}): **{s['title']}** - {s['snippet']} (감지 사유: {s['reason']})" for s in surging_certs])
    download_links_md = "\n".join([f"- [{r['title']}]({r['url']}): {r['snippet']}" for r in download_search]) if download_search else "- (무료 기출자료 링크 정보 없음)"

    # Generate latest_trend_report.md
    now_str = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    report_content = f"""# 🔍 실시간 트렌드 분석 리포트 — {now_str}

## 📡 인터넷 실시간 검색 결과 & 출처 링크
### 1. [{active_subj}] 실시간 정보
{subj_links_md}

### 2. [요리: {selected_seasonal}] 실시간 정보
{dish_links_md}

### 🚀 3. [실시간 급상승 자격증 & 공부자료/기출문제 다운로드 출처]
#### 📊 급상승 인기 자격증 트렌드
{surging_links_md}

#### 📥 무료 학습자료/기출문제 다운로드처 발굴
{download_links_md}

## 💡 카테고리별 글감 및 제목 기획

### 1. [학습/자격증]
- **포스팅 주제 1**: {active_subj} 최신 트렌드 분석 및 시험 과목 완벽 가이드
  - **제목 초안 1**: 독학러 필독! {active_subj} 단기 합격을 위한 과목별 핵심 공부법
- **포스팅 주제 2**: {active_subj} 수험생 필수 유의사항
  - **제목 초안 2**: {active_subj} 한 번에 패스하는 학습 암기 꿀팁 및 시험 일정

### 2. [요리/반찬]
- **포스팅 주제 1 (제철음식)**: {selected_seasonal} 카드뉴스 레시피
  - **제목 초안 1**: 요리 초보도 성공하는 {selected_seasonal} 정갈하고 맛있는 황금 레시피
- **포스팅 주제 2 (유아식단)**: 아이 입맛 살리는 {selected_toddler}
  - **제목 초안 2**: 영양 만점 초간단 {selected_toddler} 만들기

### 3. [심리/마음위로]
- **포스팅 주제 1**: 지친 마음에 주는 위로 문장
  - **제목 초안 1**: 자존감을 높이고 아침을 깨우는 따뜻한 긍정 명언 5가지

## 💡 추천 해시태그 목록
- **[학습/자격증]**: #학습팁 #자격증추천 #자기계발 #{active_subj.replace(' ', '')} #공부계획 #독학합격
- **[요리/반찬]**: #집밥레시피 #반찬만들기 #{selected_seasonal} #{selected_toddler} #{selected_banchan} #밑반찬추천 #이유식식단 #요리팁 #쉬운레시피
- **[심리/마음위로]**: #마음챙김 #힐링글귀 #심리상담 #감성치유 #자존감공부 #마인드컨트롤 #긍정명언 #위로글귀
"""

    try:
        os.makedirs(SESSIONS_DIR, exist_ok=True)
        with open(REPORT_PATH, "w", encoding="utf-8") as f:
            f.write(report_content)
        print(f"\n✅ 실시간 트렌드 분석 보고서가 동적 웹 검색 결과를 반영하여 갱신되었습니다: {REPORT_PATH}")
    except Exception as e:
        print(f"\n[WARN] 보고서 생성 실패: {e}")

if __name__ == "__main__":
    main()
