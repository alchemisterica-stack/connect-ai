#!/usr/bin/env python3
import os
import sys
import json
import re
import time

try:
    import requests
except ImportError:
    print("[ERROR] requests library is required. Run 'pip install requests'.")
    sys.exit(1)

# Paths
HERE = os.path.dirname(os.path.abspath(__file__))
CONFIG_PATH = os.path.abspath(os.path.join(HERE, "..", "config.md"))
BLOG_ACCOUNT_PATH = os.path.abspath(os.path.join(HERE, "..", "..", "blog", "tools", "blog_account.json"))

def load_instagram_config():
    tokens = {}
    if os.path.exists(CONFIG_PATH):
        try:
            with open(CONFIG_PATH, "r", encoding="utf-8") as f:
                for line in f:
                    if line.strip().startswith("- "):
                        parts = line.strip()[2:].split(":", 1)
                        if len(parts) == 2:
                            tokens[parts[0].strip()] = parts[1].strip()
        except Exception as e:
            print(f"[WARN] Failed to read config.md: {e}")
    return tokens

def upload_image_to_wordpress(local_image_path):
    if not os.path.exists(local_image_path):
        print(f"[ERROR] Local image not found: {local_image_path}")
        return None

    if not os.path.exists(BLOG_ACCOUNT_PATH):
        print(f"[ERROR] WordPress credentials not found at: {BLOG_ACCOUNT_PATH}")
        return None

    try:
        with open(BLOG_ACCOUNT_PATH, "r", encoding="utf-8") as f:
            wp_cfg = json.load(f)
    except Exception as e:
        print(f"[ERROR] Failed to load WordPress credentials: {e}")
        return None

    wp_domain = wp_cfg.get("WP_DOMAIN", "").strip().rstrip("/")
    wp_user = wp_cfg.get("WP_USERNAME", "").strip()
    wp_pass = wp_cfg.get("WP_APP_PASSWORD", "").strip()

    if not (wp_domain and wp_user and wp_pass):
        print("[ERROR] WordPress configuration is incomplete in blog_account.json")
        return None

    xmlrpc_url = wp_domain if wp_domain.endswith("xmlrpc.php") else f"{wp_domain}/xmlrpc.php"
    
    import xmlrpc.client
    import mimetypes
    
    try:
        client = xmlrpc.client.ServerProxy(xmlrpc_url)
        mime_type, _ = mimetypes.guess_type(local_image_path)
        if not mime_type:
            mime_type = "image/png"
            
        with open(local_image_path, "rb") as f:
            image_data = f.read()
            
        filename = f"insta_upload_{int(os.path.getmtime(local_image_path))}_{os.path.basename(local_image_path)}"
        res = client.wp.uploadFile(0, wp_user, wp_pass, {
            "name": filename,
            "type": mime_type,
            "bits": xmlrpc.client.Binary(image_data),
            "overwrite": True
        })
        
        wp_url = res.get("url")
        if wp_url:
            if wp_url.startswith("http://"):
                wp_url = wp_url.replace("http://", "https://", 1)
            return wp_url
        return None
    except Exception as e:
        print(f"[ERROR] WordPress XML-RPC upload failed: {e}")
        return None

def upload_image_to_catbox(local_image_path):
    if not os.path.exists(local_image_path):
        return None
    url = "https://catbox.moe/user/api.php"
    payload = {"reqtype": "fileupload", "userhash": ""}
    try:
        print(f"[INFO] Uploading local file to Catbox.moe: {os.path.basename(local_image_path)}")
        with open(local_image_path, "rb") as f:
            files = {"fileToUpload": f}
            r = requests.post(url, data=payload, files=files, timeout=45)
        if r.status_code == 200 and r.text.strip().startswith("https://"):
            cat_url = r.text.strip()
            print(f"[SUCCESS] Catbox upload succeeded! Public URL: {cat_url}")
            return cat_url
        else:
            print(f"[ERROR] Catbox upload failed: {r.text}")
            return None
    except Exception as e:
        print(f"[ERROR] Failed to upload to Catbox: {e}")
        return None

def verify_connection():
    cfg = load_instagram_config()
    token = cfg.get("META_ACCESS_TOKEN", "").strip()
    biz_id = cfg.get("INSTAGRAM_BUSINESS_ID", "").strip()

    if not token or not biz_id:
        print("[ERROR] META_ACCESS_TOKEN or INSTAGRAM_BUSINESS_ID is missing in config.md")
        return False

    url = f"https://graph.facebook.com/v20.0/{biz_id}?fields=username,name,profile_picture_url&access_token={token}"
    try:
        r = requests.get(url, timeout=15)
        if r.status_code == 200:
            data = r.json()
            print(f"[SUCCESS] Instagram Connection Verified!")
            print(f" - 계정 ID: {data.get('id')}")
            print(f" - 사용자명: @{data.get('username')}")
            print(f" - 프로필명: {data.get('name')}")
            return True
        else:
            print(f"[ERROR] Verification failed (Status {r.status_code}): {r.text}")
            return False
    except Exception as e:
        print(f"[ERROR] API Call Error: {e}")
        return False

def record_to_calendar(caption, permalink):
    # Update blog_queue.json if it exists
    if os.path.exists(BLOG_ACCOUNT_PATH):
        queue_path = os.path.join(os.path.dirname(BLOG_ACCOUNT_PATH), "blog_queue.json")
        if os.path.exists(queue_path):
            try:
                with open(queue_path, "r", encoding="utf-8") as qf:
                    queue_data = json.load(qf)
                
                if "completed_lessons" not in queue_data:
                    queue_data["completed_lessons"] = []
                    
                today_str = time.strftime("%Y-%m-%d")
                clean_title = caption.split("\n")[0][:25]
                clean_title = re.sub(r'[^\uac00-\ud7a3\w\s]', '', clean_title).strip()
                if not clean_title:
                    clean_title = "인스타그램 포스팅"
                    
                completed_entry = {
                    "subject": "인스타그램",
                    "lesson": f"{clean_title}.md",
                    "date": today_str,
                    "draft_path": os.path.abspath(os.path.join(HERE, "..", "drafts", "instagram_post_draft.md")),
                    "status": "published",
                    "url": permalink if permalink else "",
                    "wp_url": "",
                    "blogger_url": ""
                }
                
                queue_data["completed_lessons"].append(completed_entry)
                
                with open(queue_path, "w", encoding="utf-8") as qf:
                    json.dump(queue_data, qf, indent=2, ensure_ascii=False)
                print("[INFO] Successfully recorded Instagram post to calendar database (blog_queue.json).")
            except Exception as q_err:
                print(f"[WARN] Failed to write to blog_queue.json: {q_err}")

def get_public_url(source):
    if source.startswith("http://") or source.startswith("https://"):
        return source
    # Upload to WordPress first
    url = upload_image_to_wordpress(source)
    if url:
        return url
    # Fallback to Catbox
    return upload_image_to_catbox(source)

def create_item_container(image_source, token, biz_id):
    """Creates a container for a single item of a carousel"""
    url = get_public_url(image_source)
    if not url:
        return None
        
    container_url = f"https://graph.facebook.com/v20.0/{biz_id}/media"
    payload = {
        "image_url": url,
        "is_carousel_item": "true",
        "access_token": token
    }
    
    # Attempt 1 (WordPress or original URL)
    r = requests.post(container_url, data=payload, timeout=20)
    if r.status_code != 200:
        err_code = r.json().get("error", {}).get("code")
        if err_code == 9004 and not (image_source.startswith("http://") or image_source.startswith("https://")):
            print(f"[WARN] Meta failed to download item from WordPress. Trying Catbox.moe fallback...")
            cat_url = upload_image_to_catbox(image_source)
            if cat_url:
                payload["image_url"] = cat_url
                r = requests.post(container_url, data=payload, timeout=20)
                
    if r.status_code == 200:
        return r.json().get("id")
    else:
        print(f"[ERROR] Failed to create item container: {r.text}")
        return None

def publish_carousel(image_sources, caption):
    """Publishes a carousel (multiple images) to Instagram"""
    cfg = load_instagram_config()
    token = cfg.get("META_ACCESS_TOKEN", "").strip()
    biz_id = cfg.get("INSTAGRAM_BUSINESS_ID", "").strip()

    if not token or not biz_id:
        print("[ERROR] META_ACCESS_TOKEN or INSTAGRAM_BUSINESS_ID is missing in config.md")
        return None

    print(f"[INFO] 1/3. Creating item containers for {len(image_sources)} images...")
    children_ids = []
    for idx, src in enumerate(image_sources):
        print(f" -> Processing image {idx+1}/{len(image_sources)}: {os.path.basename(src) if os.path.exists(src) else src}")
        cid = create_item_container(src, token, biz_id)
        if cid:
            children_ids.append(cid)
        else:
            print(f"[ERROR] Failed to process image {idx+1}. Aborting carousel publish.")
            return None

    print(f"[INFO] 2/3. Creating Carousel container with children: {children_ids}")
    carousel_url = f"https://graph.facebook.com/v20.0/{biz_id}/media"
    payload = {
        "media_type": "CAROUSEL",
        "children": json.dumps(children_ids),
        "caption": caption,
        "access_token": token
    }
    
    try:
        r = requests.post(carousel_url, data=payload, timeout=30)
        r.raise_for_status()
        creation_id = r.json().get("id")
        if not creation_id:
            print(f"[ERROR] Failed to get Carousel container ID. Response: {r.text}")
            return None
            
        print(f"[INFO] 3/3. Publishing Carousel container (ID: {creation_id})...")
        publish_url = f"https://graph.facebook.com/v20.0/{biz_id}/media_publish"
        publish_payload = {
            "creation_id": creation_id,
            "access_token": token
        }
        
        pr = requests.post(publish_url, data=publish_payload, timeout=25)
        pr.raise_for_status()
        media_id = pr.json().get("id")
        if not media_id:
            print(f"[ERROR] Failed to get Carousel media ID. Response: {pr.text}")
            return None
            
        # Get permalink
        link_url = f"https://graph.facebook.com/v20.0/{media_id}?fields=permalink&access_token={token}"
        lr = requests.get(link_url, timeout=10)
        permalink = lr.json().get("permalink")
        
        print(f"[SUCCESS] Instagram Carousel successfully published!")
        if permalink:
            print(f" - 포스트 링크: {permalink}")
            record_to_calendar(caption, permalink)
            return permalink
        return media_id
    except Exception as e:
        print(f"[ERROR] Failed to publish Carousel: {e}")
        return None

def publish_reels(video_source, caption):
    """Publishes a video (Reels) to Instagram"""
    cfg = load_instagram_config()
    token = cfg.get("META_ACCESS_TOKEN", "").strip()
    biz_id = cfg.get("INSTAGRAM_BUSINESS_ID", "").strip()

    if not token or not biz_id:
        print("[ERROR] META_ACCESS_TOKEN or INSTAGRAM_BUSINESS_ID is missing in config.md")
        return None

    # Get public URL for video
    url = get_public_url(video_source)
    if not url:
        print("[ERROR] Failed to get a public URL for the video.")
        return None

    print(f"[INFO] 1/3. Creating Reels container for video: {url}")
    container_url = f"https://graph.facebook.com/v20.0/{biz_id}/media"
    payload = {
        "media_type": "REELS",
        "video_url": url,
        "caption": caption,
        "share_to_feed": "true",
        "access_token": token
    }
    
    try:
        r = requests.post(container_url, data=payload, timeout=25)
        # Fallback to Catbox if WordPress upload gets blocked
        if r.status_code != 200:
            print(f"[ERROR] Meta Reels API failed (status={r.status_code}): {r.text}")
            err_code = r.json().get("error", {}).get("code")
            if err_code == 9004 and not (video_source.startswith("http://") or video_source.startswith("https://")):
                print(f"[WARN] Meta failed to download video from WordPress. Trying Catbox.moe fallback...")
                cat_url = upload_image_to_catbox(video_source) # upload_image works for videos too on Catbox
                if cat_url:
                    payload["video_url"] = cat_url
                    r = requests.post(container_url, data=payload, timeout=25)
                    if r.status_code != 200:
                        print(f"[ERROR] Meta Reels API fallback failed (status={r.status_code}): {r.text}")
                    
        r.raise_for_status()
        creation_id = r.json().get("id")
        if not creation_id:
            print(f"[ERROR] Failed to get Reels creation ID. Response: {r.text}")
            return None
            
        print(f"[INFO] 2/3. Polling video processing status for container: {creation_id}")
        # Wait until the video is finished processing on Meta's server
        status_url = f"https://graph.facebook.com/v20.0/{creation_id}?fields=status_code&access_token={token}"
        max_attempts = 30
        for attempt in range(max_attempts):
            sr = requests.get(status_url, timeout=10)
            status_code = sr.json().get("status_code", "").upper()
            print(f" -> Attempt {attempt+1}/{max_attempts}: Status is '{status_code}'")
            if status_code == "FINISHED":
                break
            elif status_code == "ERROR":
                print(f"[ERROR] Video processing failed on Meta side: {sr.text}")
                return None
            time.sleep(6)
        else:
            print("[ERROR] Video processing timed out.")
            return None

        print(f"[INFO] 3/3. Publishing Reels (ID: {creation_id})...")
        publish_url = f"https://graph.facebook.com/v20.0/{biz_id}/media_publish"
        publish_payload = {
            "creation_id": creation_id,
            "access_token": token
        }
        
        pr = requests.post(publish_url, data=publish_payload, timeout=20)
        pr.raise_for_status()
        media_id = pr.json().get("id")
        if not media_id:
            print(f"[ERROR] Failed to get Reels media ID. Response: {pr.text}")
            return None
            
        # Get permalink
        link_url = f"https://graph.facebook.com/v20.0/{media_id}?fields=permalink&access_token={token}"
        lr = requests.get(link_url, timeout=10)
        permalink = lr.json().get("permalink")
        
        print(f"[SUCCESS] Instagram Reels successfully published!")
        if permalink:
            print(f" - 포스트 링크: {permalink}")
            record_to_calendar(caption, permalink)
            return permalink
        return media_id
    except Exception as e:
        print(f"[ERROR] Failed to publish Reels: {e}")
        return None

def publish_single(image_source, caption):
    """Publishes a single photo post to Instagram"""
    cfg = load_instagram_config()
    token = cfg.get("META_ACCESS_TOKEN", "").strip()
    biz_id = cfg.get("INSTAGRAM_BUSINESS_ID", "").strip()

    if not token or not biz_id:
        print("[ERROR] META_ACCESS_TOKEN or INSTAGRAM_BUSINESS_ID is missing in config.md")
        return None

    url = get_public_url(image_source)
    if not url:
        print("[ERROR] Failed to obtain a public image URL.")
        return None

    print(f"[INFO] 1/2. Creating Instagram media container for image: {url}")
    container_url = f"https://graph.facebook.com/v20.0/{biz_id}/media"
    payload = {
        "image_url": url,
        "caption": caption,
        "access_token": token
    }
    
    try:
        r = requests.post(container_url, data=payload, timeout=20)
        if r.status_code != 200:
            err_code = r.json().get("error", {}).get("code")
            if err_code == 9004 and not (image_source.startswith("http://") or image_source.startswith("https://")):
                print(f"[WARN] Meta failed to download from WordPress URL. Trying Catbox.moe fallback...")
                cat_url = upload_image_to_catbox(image_source)
                if cat_url:
                    payload["image_url"] = cat_url
                    r = requests.post(container_url, data=payload, timeout=20)
            
        r.raise_for_status()
        creation_id = r.json().get("id")
        if not creation_id:
            print(f"[ERROR] Failed to get creation ID. Response: {r.text}")
            return None
            
        print(f"[INFO] 2/2. Publishing media container (ID: {creation_id})...")
        publish_url = f"https://graph.facebook.com/v20.0/{biz_id}/media_publish"
        publish_payload = {
            "creation_id": creation_id,
            "access_token": token
        }
        
        pr = requests.post(publish_url, data=publish_payload, timeout=20)
        pr.raise_for_status()
        media_id = pr.json().get("id")
        if not media_id:
            print(f"[ERROR] Failed to get media ID. Response: {pr.text}")
            return None
            
        # Get permalink
        link_url = f"https://graph.facebook.com/v20.0/{media_id}?fields=permalink&access_token={token}"
        lr = requests.get(link_url, timeout=10)
        permalink = lr.json().get("permalink")
        
        print(f"[SUCCESS] Instagram post successfully published!")
        if permalink:
            print(f" - 포스트 링크: {permalink}")
            record_to_calendar(caption, permalink)
            return permalink
        return media_id
    except Exception as e:
        print(f"[ERROR] Failed to publish to Instagram: {e}")
        return None

def main():
    if len(sys.argv) < 2:
        print("Usage:")
        print("  python publish_instagram.py verify")
        print("  python publish_instagram.py publish <image_path_or_url> <caption>")
        print("  python publish_instagram.py publish_carousel <image_path_1,image_path_2,...> <caption>")
        print("  python publish_instagram.py publish_reels <video_path_or_url> <caption>")
        sys.exit(1)

    cmd = sys.argv[1].lower()
    if cmd == "verify":
        verify_connection()
    elif cmd == "publish":
        if len(sys.argv) < 4:
            print("[ERROR] Usage: python publish_instagram.py publish <image_path_or_url> <caption>")
            sys.exit(1)
        publish_single(sys.argv[2], sys.argv[3])
    elif cmd == "publish_carousel":
        if len(sys.argv) < 4:
            print("[ERROR] Usage: python publish_instagram.py publish_carousel <img1,img2,...> <caption>")
            sys.exit(1)
        images = [x.strip() for x in sys.argv[2].split(",") if x.strip()]
        publish_carousel(images, sys.argv[3])
    elif cmd == "publish_reels":
        if len(sys.argv) < 4:
            print("[ERROR] Usage: python publish_instagram.py publish_reels <video_path_or_url> <caption>")
            sys.exit(1)
        publish_reels(sys.argv[2], sys.argv[3])
    else:
        print(f"[ERROR] Unknown command: {cmd}")
        sys.exit(1)

if __name__ == "__main__":
    main()
