import os
import json
import time
import sys
import xmlrpc.client
import re
import requests

# Set directories
HERE = os.path.dirname(os.path.abspath(__file__))
COMPANY_DIR = os.path.abspath(os.path.join(HERE, "..", "..", ".."))
DRAFT_DIR = r"C:\Users\User\my-ai-office\_company\자료"

def upload_file_to_wp(client, username, password, file_path, name):
    if not os.path.exists(file_path):
        print(f"[ERROR] Upload file not found: {file_path}")
        return ""
    
    mime_type = "image/png" if file_path.lower().endswith(".png") else "image/jpeg"
    with open(file_path, "rb") as f:
        data = f.read()
        
    print(f"[INFO] Uploading {name} to WordPress...")
    try:
        res = client.wp.uploadFile(0, username, password, {
            "name": name,
            "type": mime_type,
            "bits": xmlrpc.client.Binary(data),
            "overwrite": True
        })
        url = res.get("url")
        print(f"[SUCCESS] Uploaded {name} -> {url}")
        return url
    except Exception as e:
        print(f"[ERROR] Failed to upload {name}: {e}")
        return ""

def md_to_html(text):
    # Basic markdown to HTML converter for Blogger compatibility
    # Bold
    text = re.sub(r'\*\*(.*?)\*\*', r'<b>\1</b>', text)
    # Headings
    text = re.sub(r'^#### (.*?)$', r'<h4>\1</h4>', text, flags=re.MULTILINE)
    text = re.sub(r'^### (.*?)$', r'<h3>\1</h3>', text, flags=re.MULTILINE)
    text = re.sub(r'^## (.*?)$', r'<h2>\1</h2>', text, flags=re.MULTILINE)
    text = re.sub(r'^# (.*?)$', r'<h1>\1</h1>', text, flags=re.MULTILINE)
    # Horizontal rule
    text = text.replace("---", "<hr>")
    # Bullet points
    text = re.sub(r'^\*\s+(.*?)$', r'<li>\1</li>', text, flags=re.MULTILINE)
    # Wrap adjacent list items in <ul>
    text = re.sub(r'(<li>.*?</li>\s*)+', lambda m: f"<ul>{m.group(0)}</ul>", text)
    # Paragraphs (replace newlines with <br>)
    text = text.replace("\n", "<br>")
    return text

def main():
    config_path = os.path.join(HERE, "blog_account.json")
    if not os.path.exists(config_path):
        print(f"[ERROR] Configuration file not found at {config_path}")
        sys.exit(1)
        
    with open(config_path, "r", encoding="utf-8") as f:
        config = json.load(f)
        
    wp_domain = config.get("WP_DOMAIN", "").strip().rstrip("/")
    wp_user = config.get("WP_USERNAME", "").strip()
    wp_pass = config.get("WP_APP_PASSWORD", "").strip()
    blogger_id = config.get("BLOGGER_BLOG_ID", "").strip()
    
    if not wp_domain or not wp_user or not wp_pass:
        print("[ERROR] WP credentials not configured in blog_account.json")
        sys.exit(1)
        
    xmlrpc_url = wp_domain if wp_domain.endswith("xmlrpc.php") else f"{wp_domain}/xmlrpc.php"
    client = xmlrpc.client.ServerProxy(xmlrpc_url)
    
    # 1. Define files in 자료 folder
    img_dough = os.path.join(DRAFT_DIR, "20260615_154123.jpg")
    img_wp_pan = os.path.join(DRAFT_DIR, "20260615_154126.jpg")
    img_bg_pan = os.path.join(DRAFT_DIR, "20260615_154128.jpg")
    img_wp_fin = os.path.join(DRAFT_DIR, "imo_mochi_cozy_nori.png")
    img_bg_fin = os.path.join(DRAFT_DIR, "imo_mochi_modern_plain.png")
    
    # 2. Upload all images to WordPress media library to get URLs
    ts = int(time.time())
    url_dough = upload_file_to_wp(client, wp_user, wp_pass, img_dough, f"recipe_imo_dough_{ts}.jpg")
    url_wp_pan = upload_file_to_wp(client, wp_user, wp_pass, img_wp_pan, f"recipe_imo_pan_wp_{ts}.jpg")
    url_bg_pan = upload_file_to_wp(client, wp_user, wp_pass, img_bg_pan, f"recipe_imo_pan_bg_{ts}.jpg")
    url_wp_fin = upload_file_to_wp(client, wp_user, wp_pass, img_wp_fin, f"recipe_imo_fin_wp_{ts}.png")
    url_bg_fin = upload_file_to_wp(client, wp_user, wp_pass, img_bg_fin, f"recipe_imo_fin_bg_{ts}.png")
    
    if not url_dough or not url_wp_pan or not url_bg_pan or not url_wp_fin or not url_bg_fin:
        print("[ERROR] One or more image uploads failed. Cannot proceed with correct image linking.")
        sys.exit(1)
        
    # 3. Construct WordPress version (Channel A)
    wp_title = "비 오는 날 생각나는 쫀득함, 홋카이도식 감자떡 '이모모찌' 만들기 🪵"
    
    wp_body = f"""<img src="{url_wp_fin}" style="width: 80%; max-width: 80%; height: auto; display: block; margin: 15px auto;" alt="이모모찌 메인" />

안녕하세요, 여러분! 

오늘따라 주방 가득 고소하고 따뜻한 버터 냄새를 풍기고 싶어지는 날이네요. 냉장고 구석에 굴러다니던 감자 몇 개를 꺼내 들었습니다. 오늘의 주인공은 바로 일본 홋카이도의 영혼을 채워주는 소울푸드, **'이모모찌(일본식 감자떡)'**입니다. 

문득 요리를 굽다가 고소한 냄새에 취해 급하게 카메라를 들었어요. 과정 사진은 조금 서툴고 투박하지만, 그만큼 집에서 누구나 편안하게 따라 하실 수 있는 따스한 레시피랍니다.

<img src="{url_dough}" style="width: 80%; max-width: 80%; height: auto; display: block; margin: 15px auto;" alt="동글동글 뭉치기 직전의 반죽" />
처음에는 삶은 감자를 포크나 감자 으깨기로 잘게 부수어 줍니다. 여기에 감자전분을 넣어가며 치대주면 촉촉하고 부드러운 아기 엉덩이 같은 반죽이 완성돼요. 이때 소금을 한 꼬집 톡 넣어 간을 살짝 맞춰주는 것이 저만의 소소한 팁이랍니다.

<img src="{url_wp_pan}" style="width: 80%; max-width: 80%; height: auto; display: block; margin: 15px auto;" alt="지글지글 구워지는 감자떡" />
프라이팬에 기름을 두르고 감자떡을 노릇노릇 구워봅니다. 지글거리는 소리와 함께 겉면이 마법처럼 황금빛으로 물들어가기 시작하면 마음이 참 몽글몽글해져요. 뒤집기 직전에 버터 한 조각을 팬 가장자리에 톡 떨어뜨려 주면, 온 집안에 풍부한 풍미가 싹 스며듭니다.

마무리로 간장, 맛술, 설탕을 졸여서 만든 달콤 짭조름한 간장 소스를 붓고 앞뒤로 졸여내어 김 한 장을 삭 감싸줍니다. 

따끈한 차 한 잔과 함께 겉은 바삭하고 속은 쫀득한 이모모찌 한 입을 베어 물며 여유로운 오후를 채워보시는 건 어떨까요?

<img src="{url_wp_fin}" style="width: 80%; max-width: 80%; height: auto; display: block; margin: 20px auto;" alt="이모모찌 완성작" />
"""

    # 4. Construct Blogger version (Channel B)
    blogger_title = "남은 감자 요리 추천: 전분으로 쫀득함을 극대화한 '감자 치즈 떡' 황금 레시피"
    
    blogger_body_md = f"""<img src="{url_bg_fin}" style="width: 80%; max-width: 80%; height: auto; display: block; margin: 15px auto;" alt="이모모찌" />

냉장고에 남은 감자를 가장 맛있고 이색적으로 소비할 수 있는 레시피를 소개합니다. 오늘 소개해 드릴 요리는 쫀득쫀득한 식감이 일품인 일본식 감자전분 떡, **'이모모찌'**입니다. 

어려운 제과 계량 없이 으깬 감자와 전분의 비율만 맞추면 실패 없이 15분 만에 뚝딱 완성할 수 있습니다.

#### ■ 핵심 재료 (2인분 기준)
*   **기본**: 감자 3개(대), 감자전분 4큰술, 소금 0.5티스푼, 버터 1큰술, 식용유 적당량
*   **단짠 소스**: 간장 2큰술, 설탕 1.5큰술, 미림(맛술) 2큰술, 물 2큰술

---

#### ■ Step-by-Step 조리 순서

**Step 1. 감자 삶기 & 반죽 치대기**
감자는 삶거나 전자레인지에 익혀 뜨거울 때 부드럽게 으깨줍니다. 감자의 수분량에 따라 전분 양을 조절해야 하므로, 아래 사진처럼 뭉쳤을 때 갈라지지 않고 찰기가 도는 상태가 될 때까지 전분을 숟가락으로 조절해가며 섞어 줍니다.
<img src="{url_dough}" style="width: 80%; max-width: 80%; height: auto; display: block; margin: 15px auto;" alt="반죽 치대기" />

**Step 2. 팬 프라잉 (중약불 조리)**
중약불로 예열한 팬에 식용유를 두르고 반죽을 먹기 좋은 크기로 둥글납작하게 빚어 올립니다. 고온에서 구우면 겉만 타고 전분이 속까지 찰지게 익지 않으므로 아래 사진처럼 넉넉한 공간을 두고 약한 불에서 은근하게 구워줍니다.
<img src="{url_bg_pan}" style="width: 80%; max-width: 80%; height: auto; display: block; margin: 15px auto;" alt="이모모찌 팬 굽기" />

**Step 3. 소스 졸이기 및 완성**
앞뒤로 겉면이 단단하게 누룽지처럼 구워지면 약불로 줄이고 준비한 소스 재료를 부어 빠르게 앞뒤로 졸여내어 윤기를 코팅해줍니다. 기호에 따라 안에 모짜렐라 치즈를 넣으면 '치즈 감자떡'으로 한 단계 더 업그레이드할 수 있습니다.

<img src="{url_bg_fin}" style="width: 80%; max-width: 80%; height: auto; display: block; margin: 20px auto;" alt="이모모찌 완성" />
"""

    blogger_html = md_to_html(blogger_body_md)

    # 5. Write to local session draft file for logging
    target_session_file = os.path.join(COMPANY_DIR, "sessions", "recipe_감자떡.md")
    os.makedirs(os.path.dirname(target_session_file), exist_ok=True)
    with open(target_session_file, "w", encoding="utf-8") as f:
        f.write("========== WORDPRESS VERSION ==========\n")
        f.write(f"# {wp_title}\n\n")
        f.write(wp_body)
        f.write("\n\n========== BLOGGER VERSION ==========\n")
        f.write(f"# {blogger_title}\n\n")
        f.write(blogger_body_md)
    print(f"[INFO] Wrote final merged draft to: {target_session_file}")

    # 6. Publish to WordPress
    print("[INFO] Publishing to WordPress...")
    wp_url = ""
    try:
        wp_categories = []
        try:
            cats = client.wp.getCategories(0, wp_user, wp_pass)
            wp_categories = [c.get('categoryName') for c in cats]
        except Exception as cat_err:
            print(f"[WARN] Failed to fetch WordPress categories: {cat_err}")

        cat_name = "요리/반찬"
        if cat_name not in wp_categories:
            try:
                client.wp.newTerm(0, wp_user, wp_pass, {
                    "name": cat_name,
                    "taxonomy": "category"
                })
                print(f"[SUCCESS] Created WordPress category dynamically: {cat_name}")
            except Exception as create_err:
                print(f"[WARN] Failed to create WordPress category '{cat_name}': {create_err}")

        post_data = {
            "title": wp_title,
            "description": wp_body,
            "post_status": "publish",
            "categories": [cat_name]
        }
        post_id = client.metaWeblog.newPost("default", wp_user, wp_pass, post_data, True)
        wp_url = f"{wp_domain}/?p={post_id}"
        print(f"[SUCCESS] WordPress post published! URL: {wp_url}")
    except Exception as e:
        print(f"[ERROR] Failed to publish to WordPress: {e}")

    # 7. Publish to Blogger
    print("[INFO] Publishing to Blogger...")
    blogger_url = ""
    token_json = os.path.join(HERE, "token.json")
    if blogger_id and os.path.exists(token_json):
        try:
            from google.oauth2.credentials import Credentials
            from google.auth.transport.requests import Request
            
            creds = Credentials.from_authorized_user_file(token_json, ["https://www.googleapis.com/auth/blogger"])
            if creds and creds.expired and creds.refresh_token:
                creds.refresh(Request())
            if creds:
                access_token = creds.token
                
                payload = {
                    "kind": "blogger#post",
                    "blog": {"id": blogger_id},
                    "title": blogger_title,
                    "content": blogger_html,
                    "labels": [cat_name]
                }
                api_url = f"https://www.googleapis.com/blogger/v3/blogs/{blogger_id}/posts"
                headers = {
                    "Authorization": f"Bearer {access_token}",
                    "Content-Type": "application/json",
                    "User-Agent": "Connect-AI-Agent"
                }
                res = requests.post(api_url, json=payload, headers=headers, timeout=15, verify=False)
                if res.status_code == 200:
                    data = res.json()
                    blogger_url = data.get("url", "")
                    print(f"[SUCCESS] Blogger post published! URL: {blogger_url}")
                else:
                    print(f"[ERROR] Blogger API responded with status {res.status_code}: {res.text}")
        except Exception as e:
            print(f"[ERROR] Failed to publish to Blogger: {e}")

    # 8. Record to blog_queue.json to show on Schedule Calendar
    queue_path = os.path.join(HERE, "blog_queue.json")
    if os.path.exists(queue_path):
        with open(queue_path, "r", encoding="utf-8") as f:
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
        "subject": cat_name,
        "lesson": "recipe_감자떡.md",
        "date": today_str,
        "draft_path": target_session_file,
        "status": "published" if (wp_url or blogger_url) else "draft",
        "url": wp_url or blogger_url,
        "wp_url": wp_url,
        "blogger_url": blogger_url
    }

    if "completed_lessons" not in queue_data:
        queue_data["completed_lessons"] = []
        
    existing_idx = -1
    for idx, entry in enumerate(queue_data["completed_lessons"]):
        if entry.get("lesson") == "recipe_감자떡.md" and entry.get("subject") == cat_name:
            existing_idx = idx
            break
            
    if existing_idx != -1:
        queue_data["completed_lessons"][existing_idx] = completed_entry
        print("[INFO] Updated existing calendar entry in blog_queue.json")
    else:
        queue_data["completed_lessons"].append(completed_entry)
        print("[INFO] Appended new calendar entry in blog_queue.json")

    with open(queue_path, "w", encoding="utf-8") as f:
        json.dump(queue_data, f, indent=2, ensure_ascii=False)

    print("[SUCCESS] Full publishing process completed!")
    print(f"\nFinal Results:\n- WordPress: {wp_url}\n- Blogger: {blogger_url}")

if __name__ == "__main__":
    main()
