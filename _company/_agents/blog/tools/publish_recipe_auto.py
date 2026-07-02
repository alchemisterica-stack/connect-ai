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

sys.path.append(r"C:\Users\User\my-ai-office\scripts")
try:
    import automation_utils
except ImportError:
    automation_utils = None

def get_recipe_topic():
    if len(sys.argv) > 1:
        print(f"[INFO] Using manual CLI recipe topic: {sys.argv[1]}")
        return sys.argv[1]
        
    default_topic = "여름철 더위를 시원하게 날려주는 오이냉국"
    
    # Load completed lessons from blog_queue.json
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

    print(f"[INFO] Completed dishes list: {completed_dishes}")

    if os.path.exists(REPORT_PATH):
        try:
            with open(REPORT_PATH, "r", encoding="utf-8") as f:
                content = f.read()
            
            # Extract the recipe section
            recipe_section = re.search(r'### 2\.\s*\[요리/반찬\]([\s\S]*?)(?:###|$)', content)
            if recipe_section:
                section_text = recipe_section.group(1)
                # Clean asterisks to make regex matching robust
                clean_section = section_text.replace("**", "")
                
                # Find all suggested titles or bullet points
                candidates = []
                titles = re.findall(r'제목 초안 \d+:\s*(.*)', clean_section)
                for t in titles:
                    candidates.append(t.strip())
                
                points = re.findall(r'-\s*(.*)', clean_section)
                for p in points:
                    if "제목 초안" not in p and "포스팅 주제" not in p:
                        candidates.append(p.strip())
                        
                # Pick the first one that is NOT already published
                for candidate in candidates:
                    # Clean the candidate to find dish name using LLM
                    dish_name = ""
                    
                    # Load account config for API key
                    gemini_api_key = ""
                    if os.path.exists(ACCOUNT_PATH):
                        try:
                            with open(ACCOUNT_PATH, "r", encoding="utf-8") as f_acc:
                                config = json.load(f_acc)
                                gemini_api_key = config.get("GEMINI_API_KEY", "").strip()
                        except Exception:
                            pass
                            
                    try:
                        extract_prompt = f"다음 문장에서 구체적인 핵심 요리명(음식 이름) 단 하나만 명사 형태로 추출해 주세요. 어떠한 설명이나 기호 없이 단어만 출력하세요. (예: '새콤달콤 맛있는 열무비빔밥 만들기' -> '열무비빔밥')\n\n문장: {candidate}"
                        extracted = ask_llm("http://127.0.0.1:11434", "gemma2:2b", extract_prompt, gemini_api_key).strip()
                        extracted = re.sub(r'[^\uac00-\ud7a3\w]', '', extracted)
                        if extracted and len(extracted) < 15 and extracted not in ["레시피", "요리", "반찬", "간식", "야식"]:
                            dish_name = extracted
                            print(f"[INFO] LLM extracted candidate dish name: {dish_name}")
                    except Exception as extract_err:
                        print(f"[WARN] Failed to extract candidate dish name via LLM: {extract_err}")
                        
                    # Fallback if LLM fails
                    if not dish_name:
                        for word in ["메밀국수", "오이냉국", "감자떡", "이모모찌", "김치찌개", "된장찌개", "깻잎장아찌", "열무비빔밥"]:
                            if word in candidate:
                                dish_name = word
                                break
                    if not dish_name:
                        dish_name = re.sub(r'[^\uac00-\ud7a3\w]', '', candidate)[:12]
                    
                    if dish_name.lower() not in completed_dishes:
                        print(f"[INFO] Selected unpublished topic from trend report: {candidate} (Extracted: {dish_name})")
                        return candidate
                    else:
                        print(f"[INFO] Skipping already published topic: {candidate} ({dish_name})")
                        
        except Exception as e:
            print(f"[WARN] Failed to parse trend report: {e}. Using default topic.")
    
    # Fallback to default if not already published
    default_dish = "오이냉국"
    if default_dish.lower() not in completed_dishes:
        return default_topic
        
    return default_topic

def generate_recipe_post(topic, gemini_api_key):
    wp_prompt = f"""당신은 요리 및 집밥 전문 파워 블로거입니다.
아래 제공된 [오늘의 요리 주제]를 바탕으로 워드프레스(WordPress)용 레시피 글을 작성하세요.

[중요 지시사항]
1. 한 블로그 내용에 여러 요리를 함께 나열하지 마십시오. 반드시 [오늘의 요리 주제]에 나오는 단 '하나'의 요리(단일 요리)만을 선정하여 그 요리 하나만 깊고 상세하게 설명해야 합니다. 다른 반찬이나 여러 요리를 곁들여 소개하지 마십시오.
2. 본문 내에 절대로 '자가진단', '퀴즈', '자가진단 QUIZ' 또는 학습용 질문/평가 문제를 포함하지 마십시오.
3. [마이크로 문단 및 충분한 여백 (네이버 블로그 스타일)]: 글을 쓸 때 1~2개 문장 단위로 매우 짧게 단락을 나누고, 문단과 문단 사이에는 반드시 빈 줄을 2줄 이상(엔터 3번) 띄워서 모바일 화면에서 쾌적하게 보이도록 충분한 숨구멍 여백을 확보하십시오.
4. [시각적 강약 조절 (강조와 구조화)]:
   - 각 요리 과정의 핵심 비법이나 주요 팁은 마크다운 굵게(**텍스트**)와 인용구(> ) 기호를 적극적으로 사용하여 시각적 강약을 뚜렷하게 구분해 주십시오.
   - 대제목은 `#`, 중제목은 `##`, 소제목은 `###`을 명확하게 표시하십시오.
   - 필요한 재료 목록은 반드시 표(Table) 또는 명확한 글머리 기호 리스트 형식으로 깔끔하게 정리해 한눈에 들어오게 제시하십시오.
5. [포스팅 하단 태그 삽입] 본문 가장 최하단(본문 내용이 완전히 끝난 후)에는 해당 요리 레시피와 관련이 깊은 핵심 단어들을 해시태그 형식(예: #요리레시피 #집밥반찬 등)으로 5~10개 반드시 첨부하십시오.

[오늘의 요리 주제]
{topic}

[출력 요구사항 및 포맷]
반드시 본문 최상단에 다음 형식의 [METADATA] 블록을 제일 먼저 출력하고, 그 아래에 워드프레스 포스팅 본문을 작성하세요.

[METADATA]
Dish: (요리의 영어 이름, 예: Cucumber Cold Soup)
Ingredients: (핵심 한식 식재료 3~5가지 영단어 나열, 예: cucumber, vinegar, sesame seeds, water)
Step 1: (1단계 조리 장면에 대한 사실적인 영문 묘사, 예: slicing fresh green cucumber on a wooden cutting board)
Step 2: (2단계 조리 장면에 대한 사실적인 영문 묘사, 예: pouring clear cold water into a bowl with sliced cucumbers)
[END METADATA]

# [워드프레스용 제목]
(본문은 이웃집 다정한 이웃이 본인의 일상 이야기나 가족과의 추억, 요리하는 과정에서 느낀 소소한 감정을 털어놓는 듯한 '친근하고 따뜻한 스토리텔링 어조'로 작성해 주세요. 요리에 담긴 사연이나 요리할 때 집안에 풍기는 냄새, 맛에 대한 묘사 등 풍성한 이야기 중심의 글이어야 합니다. 요리 순서도 딱딱한 개조식이 아니라 자연스럽게 이야기하듯 풀어내어 정겨움을 주도록 작성하세요. 글자 수 1000자 이상으로 길고 상세히 작성하세요. 마지막에 해시태그를 추가해 주세요.)
"""

    blogger_prompt = f"""당신은 요리 및 집밥 전문 파워 블로거입니다.
아래 제공된 [오늘의 요리 주제]를 바탕으로 구글 블로거(Blogger)용 레시피 글을 작성하세요.

[중요 지시사항]
1. 한 블로그 내용에 여러 요리를 함께 나열하지 마십시오. 반드시 [오늘의 요리 주제]에 나오는 단 '하나'의 요리(단일 요리)만을 선정하여 그 요리 하나만 깊고 상세하게 설명해야 합니다. 다른 반찬이나 여러 요리를 곁들여 소개하지 마십시오.
2. 본문 내에 절대로 '자가진단', '퀴즈', '자가진단 QUIZ' 또는 학습용 질문/평가 문제를 포함하지 마십시오.
3. [마이크로 문단 및 충분한 여백 (네이버 블로그 스타일)]: 글을 쓸 때 1~2개 문장 단위로 매우 짧게 단락을 나누고, 문단과 문단 사이에는 반드시 빈 줄을 2줄 이상(엔터 3번) 띄워서 모바일 화면에서 쾌적하게 보이도록 충분한 숨구멍 여백을 확보하십시오.
4. [시각적 강약 조절 (강조와 구조화)]:
   - 각 요리 과정의 핵심 비법이나 주요 팁은 마크다운 굵게(**텍스트**)와 인용구(> ) 기호를 적극적으로 사용하여 시각적 강약을 뚜렷하게 구분해 주십시오.
   - 대제목은 `#`, 중제목은 `##`, 소제목은 `###`을 명확하게 표시하십시오.
   - 필요한 재료 목록은 반드시 표(Table) 또는 명확한 글머리 기호 리스트 형식으로 깔끔하게 정리해 한눈에 들어오게 제시하십시오.
5. [포스팅 하단 태그 삽입] 본문 가장 최하단(본문 내용이 완전히 끝난 후)에는 해당 요리 레시피와 관련이 깊은 핵심 단어들을 해시태그 형식(예: #요리레시피 #집밥반찬 등)으로 5~10개 반드시 첨부하십시오.

[오늘의 요리 주제]
{topic}

[출력 요구사항 및 포맷]
반드시 다음 형식으로 구글 블로거용 포스팅 본문을 작성하세요. (메타데이터 블록은 포함하지 마십시오.)

# [블로거용 제목]
(본문은 깔끔하고 명확하며 군더더기 없는 '구조적이고 전문적인 레시피 카드 어조'로 작성해 주세요. 불필요한 일상 이야기나 감정 묘사는 일체 배제하고, 필요한 재료 목록(정량 표기 포함)을 표(Table) 또는 명확한 리스트 형식으로 정리해 제시하십시오. 조리 단계(Step-by-step)를 시간순으로 명확하고 간결하게 기입하되, 각 단계와 핵심 팁에는 적절히 마크다운 소제목(##, ###)과 강조 기호(**강조**) 및 인용구 기호(> )를 꼭 사용하여 시각적인 강약과 가독성을 확실하게 확보하십시오. 글자 수 1000자 이상으로 상세히 작성하세요. 마지막에 해시태그를 추가해 주세요.)
"""

    cfg = {"OLLAMA_URL": "http://127.0.0.1:11434", "MODEL": "gemma2:2b"}
    
    print(f"[INFO] Calling Gemini/LLM to generate WordPress version recipe...")
    wp_res = ask_llm(cfg["OLLAMA_URL"], cfg["MODEL"], wp_prompt, gemini_api_key)
    
    print(f"[INFO] Calling Gemini/LLM to generate Blogger version recipe...")
    blogger_res = ask_llm(cfg["OLLAMA_URL"], cfg["MODEL"], blogger_prompt, gemini_api_key)
    
    # Extract metadata block from wp_res if it exists
    metadata_block = ""
    meta_match = re.search(r'\[METADATA\]([\s\S]*?)\[END METADATA\]', wp_res)
    if meta_match:
        metadata_block = meta_match.group(0)
        wp_res = wp_res.replace(metadata_block, "").strip()
        
    result = f"{metadata_block}\n\n========== WORDPRESS VERSION ==========\n{wp_res}\n\n========== BLOGGER VERSION ==========\n{blogger_res}"
    return result

def main():
    try:
        _main_impl()
    except Exception as err:
        import traceback
        err_msg = f"{err}\n{traceback.format_exc()}"
        print(f"[ERROR] Critical failure in publish_recipe_auto: {err_msg}")
        
        if automation_utils:
            try:
                automation_utils.log_automation_failure(
                    task_id="recipe_blog_publish",
                    task_name="요리 블로그 자동 발행",
                    stage="레시피 생성 또는 WordPress/Blogger API 발행 단계",
                    error_msg=str(err)
                )
            except Exception as log_err:
                print(f"[WARN] Failed to write failure task: {log_err}")
        sys.exit(1)

def _main_impl():
    # Today rate limit check
    today_str = time.strftime("%Y-%m-%d")
    if os.path.exists(QUEUE_PATH):
        try:
            with open(QUEUE_PATH, "r", encoding="utf-8") as f:
                queue_data = json.load(f)
            today_recipe_posts = [
                p for p in queue_data.get("completed_lessons", [])
                if p.get("subject") == "요리/반찬" and p.get("date") == today_str
            ]
            if len(today_recipe_posts) >= 1:
                print(f"[INFO] Daily limit reached. Today ({today_str}) already published recipe: {[p['lesson'] for p in today_recipe_posts]}")
                print("Skipping execution to avoid double-publishing.")
                sys.exit(0)

        except SystemExit:
            sys.exit(0)
        except Exception as q_err:
            print(f"[WARN] Failed to load completed lessons for rate limiting: {q_err}")

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

    # Check if a pre-generated approved draft already exists for this dish
    use_existing_draft = False
    result = ""
    if os.path.exists(DRAFT_PATH) and os.path.getsize(DRAFT_PATH) > 1000:
        try:
            with open(DRAFT_PATH, "r", encoding="utf-8") as f_draft:
                existing_content = f_draft.read()
            
            # Extract clean target dish name
            clean_target = topic.replace(" ", "").lower()
            for word in ["메밀국수", "오이냉국", "감자떡", "이모모찌", "김치찌개", "된장찌개", "제육볶음"]:
                if word in topic:
                    clean_target = word
                    break
            
            # Parse dish name from metadata block in existing draft
            meta_match = re.search(r'\[METADATA\]([\s\S]*?)\[END METADATA\]', existing_content)
            draft_dish = ""
            if meta_match:
                meta_text = meta_match.group(1).strip()
                for line in meta_text.split('\n'):
                    if ':' in line:
                        k, v = line.split(':', 1)
                        if k.strip().lower() == 'dish':
                            draft_dish = v.strip().replace(" ", "").lower()
                            break
            
            print(f"[DEBUG] DRAFT_PATH: {DRAFT_PATH}")
            print(f"[DEBUG] Exists: {os.path.exists(DRAFT_PATH)}, Size: {os.path.getsize(DRAFT_PATH)}")
            print(f"[DEBUG] clean_target: '{clean_target}', draft_dish: '{draft_dish}'")
            print(f"[DEBUG] clean_target in draft_dish?: {clean_target in draft_dish}")
            print(f"[DEBUG] clean_target in existing_content.lower()?: {clean_target in existing_content.lower()}")
            
            if clean_target and (clean_target in draft_dish or clean_target in existing_content.lower()):
                print(f"[INFO] Found matching existing approved draft for '{clean_target}'. Reusing it.")
                result = existing_content
                use_existing_draft = True
        except Exception as draft_err:
            print(f"[WARN] Failed to inspect existing draft: {draft_err}")

    print(f"[DEBUG] use_existing_draft flag: {use_existing_draft}")
    if not use_existing_draft:
        print("[INFO] Generating new recipe post from scratch...")
        result = generate_recipe_post(topic, gemini_api_key)
        if not result:
            print("[ERROR] Failed to generate recipe blog post content.")
            sys.exit(1)
        print(f"[INFO] Writing generated content to draft: {DRAFT_PATH}")
        os.makedirs(SESSIONS_DIR, exist_ok=True)
        with open(DRAFT_PATH, "w", encoding="utf-8") as f:
            f.write(result)

    # Extract a clean dish name for a unique lesson key using LLM
    dish_name = None
    try:
        extract_prompt = f"다음 문장에서 구체적인 핵심 요리명(음식 이름) 단 하나만 명사 형태로 추출해 주세요. 어떠한 설명이나 기호 없이 단어만 출력하세요. (예: '맛있는 메밀국수 레시피' -> '메밀국수')\n\n문장: {topic}"
        extracted = ask_llm("http://127.0.0.1:11434", "gemma2:2b", extract_prompt, gemini_api_key).strip()
        # Clean up the output to keep only Korean and English alphanumeric characters
        extracted = re.sub(r'[^\uac00-\ud7a3\w]', '', extracted)
        if extracted and len(extracted) < 15 and extracted not in ["레시피", "요리", "반찬", "간식", "야식"]:
            dish_name = extracted
            print(f"[INFO] LLM extracted clean dish name: {dish_name}")
    except Exception as extract_err:
        print(f"[WARN] Failed to extract dish name via LLM: {extract_err}")

    if not dish_name:
        for word in ["메밀국수", "오이냉국", "감자떡", "이모모찌", "김치찌개", "된장찌개"]:
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

    # Load from draft and parse metadata
    with open(DRAFT_PATH, "r", encoding="utf-8") as f:
        content_to_publish = f.read()

    metadata = {}
    meta_match = re.search(r'\[METADATA\]([\s\S]*?)\[END METADATA\]', content_to_publish)
    if meta_match:
        meta_text = meta_match.group(1).strip()
        for line in meta_text.split('\n'):
            if ':' in line:
                key, val = line.split(':', 1)
                metadata[key.strip()] = val.strip()
        content_to_publish = content_to_publish.replace(meta_match.group(0), '').strip()
        print(f"[INFO] Parsed recipe metadata: {metadata}")
    else:
        print("[WARN] Failed to find METADATA block in recipe content.")

    print("[INFO] Uploading cooking blog post to WordPress and Blogger...")
    urls = auto_publish_post(content_to_publish, "recipe", "요리/반찬", lesson_name, metadata=metadata)
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
