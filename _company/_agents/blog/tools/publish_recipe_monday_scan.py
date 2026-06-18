#!/usr/bin/env python3
import os
import re
import json
import sys
import time

HERE = os.path.dirname(os.path.abspath(__file__))
COMPANY_DIR = os.path.abspath(os.path.join(HERE, "..", "..", ".."))
SESSIONS_DIR = os.path.join(COMPANY_DIR, "sessions")
QUEUE_PATH = os.path.join(HERE, "blog_queue.json")
ACCOUNT_PATH = os.path.join(HERE, "blog_account.json")

# Import publishing function and LLM wrapper from blog_post_generator
sys.path.append(HERE)
from blog_post_generator import auto_publish_post, ask_llm

def scan_custom_dishes():
    """
    Scans custom_recipe_photos and 자료 directories for custom recipe photos.
    Groups them by dish name (prefix before the suffix).
    """
    user_home = os.path.expanduser("~")
    folders = [
        os.path.join(user_home, "my-ai-office", "assets", "custom_recipe_photos"),
        os.path.join(user_home, "my-ai-office", "_company", "자료")
    ]
    
    found_dishes = set()
    for folder in folders:
        if not os.path.exists(folder):
            continue
        try:
            for f in os.listdir(folder):
                if not f.lower().endswith(('.png', '.jpg', '.jpeg')):
                    continue
                
                # Match suffix patterns like: _ing, _fin, _step*, _wp_fin, _blogger_fin, _cozy_nori, _finished, _modern_plain
                match = re.match(r'^([^\s_]+)(_(ing|fin|step\d+|wp_fin|blogger_fin|cozy_nori|finished|modern_plain|cozy))\b', f, re.IGNORECASE)
                if match:
                    dish = match.group(1).strip()
                    # Exclude known generic agent/app files
                    if dish in ["blog", "quiz", "temp_wp", "temp_blogger", "youth", "book"]:
                        continue
                    
                    # Exclude files that are too small (placeholder or broken)
                    file_path = os.path.join(folder, f)
                    if os.path.getsize(file_path) > 1000:
                        found_dishes.add(dish)
        except Exception as e:
            print(f"[WARN] Failed to scan directory {folder}: {e}")
            
    return sorted(list(found_dishes))

def get_completed_dishes():
    completed_dishes = []
    if os.path.exists(QUEUE_PATH):
        try:
            with open(QUEUE_PATH, "r", encoding="utf-8") as f:
                queue_data = json.load(f)
                for entry in queue_data.get("completed_lessons", []):
                    if entry.get("subject") == "요리/반찬":
                        lesson = entry.get("lesson", "")
                        # Extract dish name from lesson name, e.g., recipe_메밀국수_1781236183.md -> 메밀국수
                        cleaned = lesson.replace("recipe_", "").replace(".md", "")
                        cleaned = re.sub(r'_\d+$', '', cleaned)
                        cleaned = cleaned.replace("_", "").strip()
                        if cleaned:
                            completed_dishes.append(cleaned.lower())
        except Exception as q_err:
            print(f"[WARN] Failed to load completed lessons: {q_err}")
    return completed_dishes

def generate_recipe_post(dish_name, gemini_api_key):
    user_home = os.path.expanduser("~")
    folders = [
        os.path.join(user_home, "my-ai-office", "assets", "custom_recipe_photos"),
        os.path.join(user_home, "my-ai-office", "_company", "자료")
    ]
    
    memo_content = ""
    memo_file_found = None
    for folder in folders:
        if not os.path.exists(folder):
            continue
        for ext in ["_memo.txt", "_memo.md", "_초안.txt", "_draft.txt", " memo.txt", " 초안.txt"]:
            test_path = os.path.join(folder, f"{dish_name}{ext}")
            if os.path.exists(test_path):
                memo_file_found = test_path
                break
        if memo_file_found:
            break
            
    if memo_file_found:
        try:
            with open(memo_file_found, "r", encoding="utf-8") as mf:
                memo_content = mf.read().strip()
            print(f"[INFO] Found custom memo file for {dish_name}: {os.path.basename(memo_file_found)}")
        except UnicodeDecodeError:
            try:
                with open(memo_file_found, "r", encoding="cp949") as mf:
                    memo_content = mf.read().strip()
                print(f"[INFO] Found custom memo file for {dish_name} (CP949): {os.path.basename(memo_file_found)}")
            except Exception as e:
                print(f"[WARN] Failed to read memo file {memo_file_found}: {e}")
        except Exception as e:
            print(f"[WARN] Failed to read memo file {memo_file_found}: {e}")

    topic = f"사용자가 직접 준비한 실사 사진을 기반으로 요리하는 맛있는 {dish_name} 레시피"
    prompt = f"""당신은 요리 및 집밥 전문 파워 블로거입니다.
아래 제공된 [오늘의 요리 주제]를 바탕으로 워드프레스(WordPress)와 구글 블로거(Blogger)에 각각 업로드할 두 가지 버전의 레시피 글을 작성하세요.

[중요 지시사항]
1. 두 블로그는 완전히 다른 독자층을 대상으로 독립적으로 운영되므로, 두 버전의 문체와 내용 구성이 완전히 다르게(차별화되게) 작성되어야 합니다. 동일한 내용을 단순히 문장만 바꾼 형태여서는 절대 안 됩니다.
2. 한 블로그 내용에 여러 요리를 함께 나열하지 마십시오. 반드시 [오늘의 요리 주제]에 나오는 단 '하나'의 요리(단일 요리)만을 선정하여 그 요리 하나만 깊고 상세하게 설명해야 합니다. 다른 반찬이나 여러 요리를 곁들여 소개하지 마십시오.
3. 본문 내에 절대로 '자가진단', '퀴즈', '자가진단 QUIZ' 또는 학습용 질문/평가 문제를 포함하지 마십시오.
4. [마이크로 문단 및 충분한 여백 (네이버 블로그 스타일)]: 글을 쓸 때 1~2개 문장 단위로 매우 짧게 단락을 나누고, 문단과 문단 사이에는 반드시 빈 줄을 2줄 이상(엔터 3번) 띄워서 모바일 화면에서 쾌적하게 보이도록 충분한 숨구멍 여백을 확보하십시오.
5. [시각적 강약 조절 (강조와 구조화)]:
   - 각 요리 과정의 핵심 비법이나 주요 팁은 마크다운 굵게(**텍스트**)와 인용구(> ) 기호를 적극적으로 사용하여 시각적 강약을 뚜렷하게 구분해 주십시오.
   - 대제목은 `#`, 중제목은 `##`, 소제목은 `###`을 명확하게 표시하십시오.
   - 필요한 재료 목록은 반드시 표(Table) 또는 명확한 글머리 기호 리스트 형식으로 깔끔하게 정리해 한눈에 들어오게 제시하십시오.
6. [포스팅 하단 태그 삽입] 모든 버전의 본문 가장 최하단(본문 내용이 완전히 끝난 후)에는 해당 요리 레시피와 관련이 깊은 핵심 단어들을 해시태그 형식(예: #요리레시피 #집밥반찬 등)으로 5~10개 반드시 첨부하십시오.

[오늘의 요리 주제]
{topic}
"""

    if memo_content:
        prompt += f"\n[사용자 추가 요청 사항 및 레시피 메모]\n{memo_content}\n"

    prompt += """
[출력 요구사항 및 포맷]
반드시 다음 구분자(Delimiter)를 정확히 사용하여 각각 다른 스타일로 작성하세요.

========== WORDPRESS VERSION ==========
# [워드프레스용 제목]
(본문은 이웃집 다정한 이웃이 본인의 일상 이야기나 가족과의 추억, 요리하는 과정에서 느낀 소소한 감정을 털어놓는 듯한 '친근하고 따뜻한 스토리텔링 어조'로 작성해 주세요. 요리에 담긴 사연이나 요리할 때 집안에 풍기는 냄새, 맛에 대한 묘사 등 풍성한 이야기 중심의 글이어야 합니다. 요리 순서도 딱딱한 개조식이 아니라 자연스럽게 이야기하듯 풀어내어 정겨움을 주도록 작성하세요. 글자 수 1000자 이상으로 길고 상세히 작성하세요. 마지막에 해시태그를 추가해 주세요.)

========== BLOGGER VERSION ==========
# [블로거용 제목]
(본문은 깔끔하고 명확하며 군더더기 없는 '구조적이고 전문적인 레시피 카드 어조'로 작성해 주세요. 불필요한 일상 이야기나 감정 묘사는 일체 배제하고, 필요한 재료 목록(정량 표기 포함)을 표(Table) 또는 명확한 리스트 형식으로 정리해 제시하십시오. 조리 단계(Step-by-step)를 시간순으로 명확하고 간결하게 기입하되, 각 단계와 핵심 팁에는 적절히 마크다운 소제목(##, ###)과 강조 기호(**강조**) 및 인용구 기호(> )를 꼭 사용하여 시각적인 강약과 가독성을 확실하게 확보하십시오. 글자 수 1000자 이상으로 상세히 작성하세요. 마지막에 해시태그를 추가해 주세요.)
"""

    cfg = {"OLLAMA_URL": "http://127.0.0.1:11434", "MODEL": "gemma2:2b"}
    
    print(f"[INFO] Calling Gemini/LLM to generate cooking blog for dish: {dish_name}")
    result = ask_llm(cfg["OLLAMA_URL"], cfg["MODEL"], prompt, gemini_api_key)
    return result

def main():
    print("[INFO] Starting Monday Scan for unpublished custom recipe photos...")
    
    # Scan files for custom dishes
    custom_dishes = scan_custom_dishes()
    print(f"[INFO] Detected custom dishes in folders: {custom_dishes}")
    
    # Get already published dishes
    completed_dishes = get_completed_dishes()
    print(f"[INFO] Already published dishes: {completed_dishes}")
    
    # Find unpublished custom dishes
    unpublished = [d for d in custom_dishes if d.lower() not in completed_dishes]
    
    if not unpublished:
        print("[INFO] No unpublished custom recipe photos found. Skipping Monday Scan.")
        sys.exit(0)
        
    # Select the first unpublished dish
    selected_dish = unpublished[0]
    print(f"[INFO] Selected unpublished dish for Monday Scan publishing: {selected_dish}")
    
    # Load account config for API key
    gemini_api_key = ""
    if os.path.exists(ACCOUNT_PATH):
        try:
            with open(ACCOUNT_PATH, "r", encoding="utf-8") as f:
                config = json.load(f)
                gemini_api_key = config.get("GEMINI_API_KEY", "").strip()
        except Exception:
            pass

    result = generate_recipe_post(selected_dish, gemini_api_key)
    if not result:
        print("[ERROR] Failed to generate recipe blog post content.")
        sys.exit(1)

    draft_filename = f"recipe_{selected_dish}.md"
    draft_path = os.path.join(SESSIONS_DIR, draft_filename)
    
    print(f"[INFO] Writing generated content to draft: {draft_path}")
    os.makedirs(SESSIONS_DIR, exist_ok=True)
    with open(draft_path, "w", encoding="utf-8") as f:
        f.write(result)

    timestamp = int(time.time())
    lesson_name = f"recipe_{selected_dish}_{timestamp}.md"

    print(f"[INFO] Uploading cooking blog post for '{selected_dish}' to WordPress and Blogger...")
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
        "draft_path": draft_path,
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
        print("[INFO] Updated existing calendar entry for Monday Scan cooking blog.")
    else:
        queue_data["completed_lessons"].append(completed_entry)
        print("[INFO] Appended new calendar entry for Monday Scan cooking blog.")

    with open(QUEUE_PATH, "w", encoding="utf-8") as f:
        json.dump(queue_data, f, indent=2, ensure_ascii=False)

    print("[SUCCESS] Successfully updated blog_queue.json and recorded Monday Scan post to calendar!")

if __name__ == "__main__":
    main()
