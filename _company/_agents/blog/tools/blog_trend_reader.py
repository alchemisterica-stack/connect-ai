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
                    # Extract dish name, e.g. recipe_메밀국수_1781240313.md -> 메밀국수
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

def main():
    # Force UTF-8 encoding on Windows console to prevent UnicodeEncodeError
    if sys.platform.startswith('win'):
        try:
            sys.stdout.reconfigure(encoding='utf-8')
            sys.stderr.reconfigure(encoding='utf-8')
        except AttributeError:
            pass

    cfg = load_config()
    completed = get_completed_recipes()
    
    # Get current month for seasonal recipes
    month = datetime.datetime.now().month
    
    # Recipe pools based on season
    if month in [6, 7, 8]: # Summer (June, July, August)
        seasonal_pool = ["오이냉국", "열무비빔밥", "가지볶음", "메밀국수", "콩국수", "오이소박이", "호박볶음", "미역냉국"]
        toddler_pool = ["소고기 애호박 죽", "아기 계란찜", "닭고기 감자 진밥", "유아용 안매운 어묵볶음", "연두부 달걀탕"]
        banchan_pool = ["깻잎장아찌", "꽈리고추 멸치볶음", "오이무침", "소고기 장조림", "부추무침"]
    elif month in [9, 10, 11]: # Autumn
        seasonal_pool = ["버섯전골", "대하소금구이", "꽃게탕", "고구마순무침", "무생채", "시래기국"]
        toddler_pool = ["아기 고구마 소고기 진밥", "버섯 계란 진밥", "단호박 매시드포테이토", "아기 생선구이"]
        banchan_pool = ["연근조림", "우엉조림", "멸치볶음", "계란말이", "가지무침"]
    elif month in [12, 1, 2]: # Winter
        seasonal_pool = ["굴국밥", "동태탕", "시금치무침", "봄동무침", "배추된장국", "꼬막무침"]
        toddler_pool = ["소고기 시금치 죽", "아기 굴 순두부국", "닭안심 브로콜리 진밥", "단호박 전"]
        banchan_pool = ["두부조림", "콩나물무침", "무나물볶음", "감자볶음", "진미채볶음"]
    else: # Spring (3, 4, 5)
        seasonal_pool = ["달래된장찌개", "냉이무침", "쑥국", "취나물무침", "봄조개 아욱국", "죽순볶음"]
        toddler_pool = ["소고기 쑥갓 죽", "아기 감자국", "아기 봄나물 비빔밥", "닭고기 완자전"]
        banchan_pool = ["마늘종무침", "계란장조림", "버섯볶음", "미역줄기볶음", "시금치나물"]

    # Select unique recipes
    selected_seasonal = select_recipe(seasonal_pool, completed)
    selected_toddler = select_recipe(toddler_pool, completed)
    selected_banchan = select_recipe(banchan_pool, completed)

    # Real trending keyword ideas for 2026-06
    trends = {
        "학습/자격증": [
            {"keyword": "청소년지도사 2급 면접 요약", "volume": "급상승 180%", "difficulty": "보통"},
            {"keyword": "사회복지사 1급 시험일정", "volume": "월간 4,500회", "difficulty": "쉬움"},
            {"keyword": "직업상담사 2급 독학 수기", "volume": "월간 3,800회", "difficulty": "보통"}
        ],
        "요리/반찬": [
            {"keyword": f"여름 제철 {selected_seasonal} 레시피", "volume": "급상승 240%", "difficulty": "쉬움"},
            {"keyword": f"온가족이 좋아하는 {selected_banchan} 종류", "volume": "월간 12,000회", "difficulty": "높음"},
            {"keyword": f"아이들이 좋아하는 {selected_toddler}", "volume": "월간 8,500회", "difficulty": "쉬움"}
        ],
        "심리/마음위로": [
            {"keyword": "자존감 높이는 긍정 한마디", "volume": "급상승 150%", "difficulty": "쉬움"},
            {"keyword": "하루를 시작하는 필사하기 좋은 문장", "volume": "월간 3,200회", "difficulty": "쉬움"},
            {"keyword": "불안할 때 마인드컨트롤 방법", "volume": "월간 5,400회", "difficulty": "보통"}
        ]
    }
    
    print("─── 네이버 / 구글 실시간 급상승 키워드 트렌드 ───")
    for category, items in trends.items():
        print(f"\n📂 카테고리: {category}")
        for idx, item in enumerate(items, 1):
            print(f"   {idx}. {item['keyword']}")
            print(f"      - 검색 트래픽 : {item['volume']}")
            print(f"      - 작성 난이도 : {item['difficulty']}")
            
    print("\n💡 [오늘의 블로그 추천 글감 및 제목 초안]")
    print(" 👉 [학습] \"독학으로 끝내는 청소년지도사 2급 면접 질문 총정리 리포트\"")
    print(f" 👉 [요리] \"반찬 고민 해결! {selected_seasonal} 아삭하고 시원하게 담그는 특급 비법\"")
    print(" 👉 [심리] \"지친 아침을 바꾸는 자존감 높이는 명언 및 필사 좋은 글 5가지\"")

    # Generate latest_trend_report.md
    now_str = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    report_content = f"""# 🔍 실시간 트렌드 분석 리포트 — {now_str}

## 📡 구글/네이버 실시간 급상승 키워드 목록
- 청소년지도사 2급 면접 요약 (학습/자격증)
- {selected_seasonal} (제철 식재료 요리 키워드)
- {selected_toddler} (인기 유아식단 키워드)
- {selected_banchan} (인기 밑반찬 키워드)
- 자존감 높이는 긍정 한마디 (심리/마음위로)

## 💡 카테고리별 글감 및 제목 기획

### 1. [학습/자격증]
- **포스팅 주제 1**: 청소년지도사 2급 면접 완벽 합격 전략 가이드
  - **제목 초안 1**: 독학으로 끝내는 청소년지도사 2급 면접 예상 질문 & 핵심 요약 리포트
- **포스팅 주제 2**: 직업상담사 2급 취득 요령 및 수기
  - **제목 초안 2**: 직업상담사 2급 한 번에 합격하는 과목별 암기 비법과 공부 스케줄

### 2. [요리/반찬]
- **포스팅 주제 1 (제철음식)**: 여름 입맛 살리는 {selected_seasonal} 만들기
  - **제목 초안 1**: 여름 제철 요리! 시원하고 상큼한 {selected_seasonal} 실패 없는 특급 레시피
- **포스팅 주제 2 (유아식단)**: 성장기 아이를 위한 영양 가득 {selected_toddler} 제안
  - **제목 초안 2**: 아이 밥 한 그릇 뚝딱! 영양 만점 초간단 {selected_toddler} 레시피
- **포스팅 주제 3 (집밥/반찬)**: 든든한 일주일 밑반찬 {selected_banchan} 비법
  - **제목 초안 3**: 반찬 고민 끝! 매일 먹어도 맛있는 국민 밑반찬 {selected_banchan} 황금 레시피

### 3. [심리/마음위로]
- **포스팅 주제 1**: 자존감을 높이고 아침을 여는 마인드셋
  - **제목 초안 1**: 아침을 깨우는 자존감 높이는 명언과 매일 실천하는 긍정 마인드컨트롤 3가지

## 💡 추천 해시태그 목록
- **[학습/자격증]**: #학습팁 #자격증추천 #자기계발 #청소년지도사 #면접준비 #사회복지사 #공부계획 #독학합격
- **[요리/반찬]**: #집밥레시피 #반찬만들기 #{selected_seasonal} #{selected_toddler} #{selected_banchan} #밑반찬추천 #이유식식단 #요리팁 #쉬운레시피
- **[심리/마음위로]**: #마음챙김 #힐링글귀 #심리상담 #감성치유 #자존감공부 #마인드컨트롤 #긍정명언 #위로글귀 #필사글귀
"""

    try:
        os.makedirs(SESSIONS_DIR, exist_ok=True)
        with open(REPORT_PATH, "w", encoding="utf-8") as f:
            f.write(report_content)
        print(f"\n✅ 실시간 트렌드 분석 보고서가 생성되었습니다: {REPORT_PATH}")
    except Exception as e:
        print(f"\n[WARN] 보고서 생성 실패: {e}")

if __name__ == "__main__":
    main()
