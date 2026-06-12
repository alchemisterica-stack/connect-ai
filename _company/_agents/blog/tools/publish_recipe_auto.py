#!/usr/bin/env python3
import os
import re
import json
import sys
import time

# Encoding is handled by blog_post_generator import

HERE = os.path.dirname(os.path.abspath(__file__))
COMPANY_DIR = os.path.abspath(os.path.join(HERE, "..", "..", ".."))
SESSIONS_DIR = os.path.join(COMPANY_DIR, "sessions")
REPORT_PATH = os.path.join(SESSIONS_DIR, "latest_trend_report.md")
DRAFT_PATH = os.path.join(SESSIONS_DIR, "blog_post_trendy_banchan.md")
QUEUE_PATH = os.path.join(HERE, "blog_queue.json")
ACCOUNT_PATH = os.path.join(HERE, "blog_account.json")

# Import publishing function and LLM wrapper from blog_post_generator
sys.path.append(HERE)
from blog_post_generator import auto_publish_post, ask_llm

def get_recipe_topic():
    topic = "여름철 더위를 시원하게 날려주는 오이냉국"
    if os.path.exists(REPORT_PATH):
        try:
            with open(REPORT_PATH, "r", encoding="utf-8") as f:
                content = f.read()
            # Extract the recipe section
            recipe_section = re.search(r'### 2\.\s*\[요리/반찬\]([\s\S]*?)(?:###|$)', content)
            if recipe_section:
                section_text = recipe_section.group(1)
                # Find the first suggested title or topic
                titles = re.findall(r'제목 초안 \d+:\s*(.*)', section_text)
                if titles:
                    topic = titles[0].strip()
                    print(f"[INFO] Parsed topic from trend report: {topic}")
                else:
                    # Look for bullet points
                    points = re.findall(r'-\s*(.*)', section_text)
                    if points:
                        topic = points[0].strip()
                        print(f"[INFO] Parsed topic from bullet points: {topic}")
        except Exception as e:
            print(f"[WARN] Failed to parse trend report: {e}. Using default topic.")
    else:
        print(f"[INFO] Trend report not found at: {REPORT_PATH}. Using default topic.")
    return topic

def generate_recipe_post(topic, gemini_api_key):
    prompt = f"""당신은 요리 및 집밥 전문 파워 블로거입니다.
아래 제공된 [오늘의 요리 주제]를 바탕으로 워드프레스(WordPress)와 구글 블로거(Blogger)에 각각 업로드할 두 가지 버전의 레시피 글을 작성하세요.

[중요 지시사항]
1. 두 블로그는 완전히 다른 독자층을 대상으로 독립적으로 운영되므로, 두 버전의 문체와 내용 구성이 완전히 다르게(차별화되게) 작성되어야 합니다. 동일한 내용을 단순히 문장만 바꾼 형태여서는 절대 안 됩니다.
2. 한 블로그 내용에 여러 요리를 함께 나열하지 마십시오. 반드시 [오늘의 요리 주제]에 나오는 단 '하나'의 요리(단일 요리)만을 선정하여 그 요리 하나만 깊고 상세하게 설명해야 합니다. 다른 반찬이나 여러 요리를 곁들여 소개하지 마십시오.
3. 본문 내에 절대로 '자가진단', '퀴즈', '자가진단 QUIZ' 또는 학습용 질문/평가 문제를 포함하지 마십시오.
4. [가독성 극대화 지시사항] 문장 중간에 어색하게 엔터를 입력하여 줄바꿈을 하지 마십시오. 문장은 끊김 없이 끝까지 자연스럽게 이어 쓰되, 약 1~2개 문장마다 적절히 빈칸 줄바꿈(엔터)을 넣어 문단을 짧고 깔끔하게 쪼개어 가독성을 높여 주십시오.
- [문단 간격 지시사항] 문단과 문단 사이(혹은 내용 단위 사이)에는 반드시 빈 줄을 2줄 이상(엔터 3번) 띄워서 문단 간격이 충분히 넓고 쾌적하게 보이도록 하십시오.
5. [포스팅 하단 태그 삽입] 모든 버전의 본문 가장 최하단(본문 내용이 완전히 끝난 후)에는 해당 요리 레시피와 관련이 깊은 핵심 단어들을 해시태그 형식(예: #요리레시피 #집밥반찬 등)으로 5~10개 반드시 첨부하십시오.

[오늘의 요리 주제]
{topic}

[출력 요구사항 및 포맷]
반드시 다음 구분자(Delimiter)를 정확히 사용하여 각각 다른 스타일로 작성하세요.

========== WORDPRESS VERSION ==========
# [워드프레스용 제목]
(본문은 이웃집 다정한 이웃이 본인의 일상 이야기나 가족과의 추억, 요리하는 과정에서 느낀 소소한 감정을 털어놓는 듯한 '친근하고 따뜻한 스토리텔링 어조'로 작성해 주세요. 요리에 담긴 사연이나 요리할 때 집안에 풍기는 냄새, 맛에 대한 묘사 등 풍성한 이야기 중심의 글이어야 합니다. 요리 순서도 딱딱한 개조식이 아니라 자연스럽게 이야기하듯 풀어내어 정겨움을 주도록 작성하세요. 글자 수 1000자 이상으로 길고 상세히 작성하세요. 마지막에 해시태그를 추가해 주세요.)

========== BLOGGER VERSION ==========
# [블로거용 제목]
(본문은 깔끔하고 명확하며 군더더기 없는 '구조적이고 전문적인 레시피 카드 어조'로 작성해 주세요. 불필요한 일상 이야기나 감정 묘사는 일체 배제하고, 필요한 재료 목록(정량 표기 포함)을 표(Table) 또는 명확한 리스트 형식으로 정리해 제시하십시오. 조리 단계(Step-by-step)를 시간순으로 명확하고 간결하게 기입하고, 불을 다룰 때의 주의점이나 맛을 더하는 비법 팁을 객관적인 어조로 정리해 주십시오. 마크다운 기호 # 나 ** 는 제거하여 가독성을 높여 주시고 글자 수 1000자 이상으로 상세히 작성하세요. 마지막에 해시태그를 추가해 주세요.)
"""

    cfg = {"OLLAMA_URL": "http://127.0.0.1:11434", "MODEL": "gemma2:2b"}
    
    print(f"[INFO] Calling Gemini/LLM to generate cooking blog for topic: {topic}")
    result = ask_llm(cfg["OLLAMA_URL"], cfg["MODEL"], prompt, gemini_api_key)
    return result

def main():
    topic = get_recipe_topic()
    
    # Load account config for API key
    gemini_api_key = ""
    if os.path.exists(ACCOUNT_PATH):
        try:
            with open(ACCOUNT_PATH, "r", encoding="utf-8") as f:
                config = json.load(f)
                gemini_api_key = config.get("GEMINI_API_KEY", "").strip()
        except Exception:
            pass

    result = generate_recipe_post(topic, gemini_api_key)
    if not result:
        print("[ERROR] Failed to generate recipe blog post content.")
        sys.exit(1)

    print(f"[INFO] Writing generated content to draft: {DRAFT_PATH}")
    os.makedirs(SESSIONS_DIR, exist_ok=True)
    with open(DRAFT_PATH, "w", encoding="utf-8") as f:
        f.write(result)

    # Extract a clean dish name for a unique lesson key
    dish_name = None
    for word in ["메밀국수", "오이냉국", "야식", "간식", "김치찌개", "된장찌개", "반찬", "레시피"]:
        if word in topic:
            dish_name = word
            break
    if not dish_name:
        match = re.search(r'[\'"]([^\'"]+)[\'"]', topic)
        if match:
            dish_name = match.group(1)
    if not dish_name:
        clean_text = re.sub(r'[^\uac00-\ud7a3\w]', '', topic)
        dish_name = clean_text[:12] if clean_text else "요리"
        
    lesson_name = f"recipe_{dish_name}_{int(time.time())}.md"

    print("[INFO] Uploading cooking blog post to WordPress and Blogger...")
    urls = auto_publish_post(result, "recipe", "요리/반찬", lesson_name)
    wp_url = urls.get("wp_url", "")
    blogger_url = urls.get("blogger_url", "")

    print(f"[SUCCESS] WordPress URL: {wp_url}")
    print(f"[SUCCESS] Blogger URL: {blogger_url}")

    # Update blog_queue.json
    if os.path.exists(QUEUE_PATH):
        with open(QUEUE_PATH, "r", encoding="utf-8") as f:
            queue_data = json.load(f)
    else:
        queue_data = {
            "current_subject": "청소년복지론",
            "current_lesson_index": 0,
            "queue": [],
            "completed_history": [],
            "completed_lessons": []
        }

    today_str = time.strftime("%Y-%m-%d")
    completed_entry = {
        "subject": "요리/반찬",
        "lesson": lesson_name,
        "date": today_str,
        "draft_path": DRAFT_PATH,
        "status": "published" if (wp_url or blogger_url) else "draft",
        "url": wp_url or blogger_url,
        "wp_url": wp_url,
        "blogger_url": blogger_url
    }

    if "completed_lessons" not in queue_data:
        queue_data["completed_lessons"] = []

    # Update or append based on unique lesson_name
    existing_idx = -1
    for idx, entry in enumerate(queue_data["completed_lessons"]):
        if entry.get("lesson") == lesson_name and entry.get("subject") == "요리/반찬":
            existing_idx = idx
            break

    if existing_idx != -1:
        queue_data["completed_lessons"][existing_idx] = completed_entry
        print("[INFO] Updated existing calendar entry for cooking blog.")
    else:
        queue_data["completed_lessons"].append(completed_entry)
        print("[INFO] Appended new calendar entry for cooking blog.")

    with open(QUEUE_PATH, "w", encoding="utf-8") as f:
        json.dump(queue_data, f, indent=2, ensure_ascii=False)

    print("[SUCCESS] Successfully updated blog_queue.json and recorded to calendar!")

if __name__ == "__main__":
    main()
