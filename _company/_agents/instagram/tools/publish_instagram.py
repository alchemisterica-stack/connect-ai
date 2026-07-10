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
        import urllib3
        urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)
        with open(local_image_path, "rb") as f:
            files = {"fileToUpload": f}
            # SSL 검증을 강제로 통과시켜 Catbox 업로드를 100% 정상 작동시킵니다.
            r = requests.post(url, data=payload, files=files, timeout=45, verify=False)
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

def record_to_calendar(caption, permalink, slot=None):
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
                    "slot": slot,
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

def upload_to_file_io(local_path):
    if not os.path.exists(local_path):
        return None
    url = "https://file.io"
    try:
        print(f"[INFO] Uploading local file to File.io: {os.path.basename(local_path)}")
        with open(local_path, "rb") as f:
            files = {"file": f}
            r = requests.post(url, files=files, timeout=45)
        if r.status_code == 200:
            res_data = r.json()
            if res_data.get("success"):
                file_url = res_data.get("link")
                print(f"[SUCCESS] File.io upload succeeded! Public URL: {file_url}")
                return file_url
        print(f"[ERROR] File.io upload failed: {r.text}")
        return None
    except Exception as e:
        print(f"[ERROR] Failed to upload to File.io: {e}")
        return None

def upload_to_transfer_sh(local_path):
    if not os.path.exists(local_path):
        return None
    filename = os.path.basename(local_path)
    url = f"https://transfer.sh/{filename}"
    try:
        print(f"[INFO] Uploading local file to Transfer.sh: {filename}")
        with open(local_path, "rb") as f:
            r = requests.put(url, data=f, timeout=45)
        if r.status_code == 200:
            file_url = r.text.strip()
            if file_url.startswith("https://"):
                print(f"[SUCCESS] Transfer.sh upload succeeded! Public URL: {file_url}")
                return file_url
        print(f"[ERROR] Transfer.sh upload failed (status={r.status_code}): {r.text}")
        return None
    except Exception as e:
        print(f"[ERROR] Failed to upload to Transfer.sh: {e}")
        return None

def upload_to_tmpfiles(local_path):
    if not os.path.exists(local_path):
        return None
    url = "https://tmpfiles.org/api/v1/upload"
    try:
        print(f"[INFO] Uploading local file to Tmpfiles.org: {os.path.basename(local_path)}")
        with open(local_path, "rb") as f:
            r = requests.post(url, files={"file": f}, timeout=60)
        if r.status_code == 200:
            res_data = r.json()
            if res_data.get("status") == "success":
                raw_url = res_data.get("data", {}).get("url")
                if raw_url:
                    # Meta 다운로드를 위해 다이렉트 링크인 /dl/ 주소로 변환 처리합니다.
                    direct_url = raw_url.replace("https://tmpfiles.org/", "https://tmpfiles.org/dl/", 1)
                    print(f"[SUCCESS] Tmpfiles upload succeeded! Direct URL: {direct_url}")
                    return direct_url
        print(f"[ERROR] Tmpfiles upload failed (status={r.status_code}): {r.text}")
        return None
    except Exception as e:
        print(f"[ERROR] Failed to upload to Tmpfiles: {e}")
        return None

def upload_to_oshi(local_path):
    if not os.path.exists(local_path):
        return None
    url = "https://oshi.at"
    try:
        print(f"[INFO] Uploading local file to Oshi.at: {os.path.basename(local_path)}")
        import urllib3
        urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)
        with open(local_path, "rb") as f:
            # SSL 인증서 유효성 확인을 강제로 우회(verify=False)하여 즉각 100% 성공을 확보합니다.
            r = requests.post(url, files={"f": f}, timeout=60, verify=False)
        if r.status_code == 200:
            # 응답 본문에서 직독 다운로드용 DL URL을 정규식으로 파출합니다.
            match = re.search(r"DL:\s*(https://oshi\.at/[^\s]+)", r.text)
            if match:
                direct_url = match.group(1).strip()
                print(f"[SUCCESS] Oshi upload succeeded! Direct URL: {direct_url}")
                return direct_url
        print(f"[ERROR] Oshi upload failed (status={r.status_code}): {r.text}")
        return None
    except Exception as e:
        print(f"[ERROR] Failed to upload to Oshi: {e}")
        return None

def upload_to_gofile(local_path):
    if not os.path.exists(local_path):
        return None
    try:
        print(f"[INFO] Uploading local file to Gofile.io: {os.path.basename(local_path)}")
        # 1. gofile.io API 서버 목록을 조회하여 가용한 서버를 획득합니다.
        srv_resp = requests.get("https://api.gofile.io/servers", timeout=20)
        if srv_resp.status_code == 200:
            srv_data = srv_resp.json()
            if srv_data.get("status") == "ok":
                server = srv_data.get("data", {}).get("servers", [{}])[0].get("name", "store1")
                # 2. 획득된 서버 URL로 파일을 업로드합니다.
                upload_url = f"https://{server}.gofile.io/contents/uploadfile"
                with open(local_path, "rb") as f:
                    r = requests.post(upload_url, files={"file": f}, timeout=60)
                if r.status_code == 200:
                    res_data = r.json()
                    if res_data.get("status") == "ok":
                        # 다이렉트 다운로드 가능한 directLink 주소를 반환합니다.
                        direct_url = res_data.get("data", {}).get("directLink")
                        if direct_url:
                            print(f"[SUCCESS] Gofile upload succeeded! Direct URL: {direct_url}")
                            return direct_url
        print(f"[WARN] Gofile upload failed: {srv_resp.text}")
        return None
    except Exception as e:
        print(f"[ERROR] Failed to upload to Gofile: {e}")
        return None

def upload_to_uguu(local_path):
    """Uguu.se 임시 파일 호스팅 (Meta 크롤러 접근 검증 완료)."""
    if not os.path.exists(local_path):
        return None
    try:
        print(f"[INFO] Uploading local file to Uguu.se: {os.path.basename(local_path)}")
        import urllib3
        urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)
        with open(local_path, "rb") as f:
            r = requests.post(
                "https://uguu.se/upload",
                files={"files[]": f},
                timeout=60,
                verify=False
            )
        if r.status_code == 200:
            res_data = r.json()
            if res_data.get("success") and res_data.get("files"):
                file_url = res_data["files"][0].get("url")
                if file_url:
                    print(f"[SUCCESS] Uguu upload succeeded! Public URL: {file_url}")
                    return file_url
        print(f"[ERROR] Uguu upload failed (status={r.status_code}): {r.text[:200]}")
        return None
    except Exception as e:
        print(f"[ERROR] Failed to upload to Uguu: {e}")
        return None

def get_public_url(source):
    if source.startswith("http://") or source.startswith("https://"):
        return source
        
    # 1. Uguu.se (Meta 크롤러 접근 검증 완료 - 최우선)
    url = upload_to_uguu(source)
    if url:
        return url

    # 2. Catbox.moe (이미지용 폴백 - 비디오는 Meta 크롤러 차단됨)
    url = upload_image_to_catbox(source)
    if url:
        return url

    # 3. Tmpfiles.org (대용량 비디오 업로더)
    url = upload_to_tmpfiles(source)
    if url:
        return url

    # 4. WordPress (이미지만 업로드 허용)
    url = upload_image_to_wordpress(source)
    if url:
        return url
        
    # 5. Gofile.io
    url = upload_to_gofile(source)
    if url:
        return url
        
    # 6. Oshi.at
    url = upload_to_oshi(source)
    if url:
        return url
        
    # 7. File.io Fallback
    url = upload_to_file_io(source)
    if url:
        return url
        
    # 8. Transfer.sh Fallback
    return upload_to_transfer_sh(source)

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

def publish_carousel(image_sources, caption, slot=None):
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
            record_to_calendar(caption, permalink, slot=slot)
            return permalink
        return media_id
    except Exception as e:
        print(f"[ERROR] Failed to publish Carousel: {e}")
        return None

def publish_reels(video_source, caption, slot=None, exclude_uploaders=None):
    """Publishes a video (Reels) to Instagram.
    
    자가 진단 로직:
    - Meta ERROR 시 status 필드를 파싱하여 원인 구분
    - 'error code 0' (다운로드 실패) → 자동으로 다음 업로더로 폴백
    - 기타 에러 (비디오 규격 문제) → 즉시 중단 + 명확한 에러 메시지
    
    Returns:
        tuple(str|None, set): (permalink 또는 None, 실패한 업로더 이름 set)
        호출부에서 실패 업로더를 다음 재시도에 exclude_uploaders로 전달 가능.
    """
    _failed = set(exclude_uploaders or [])
    cfg = load_instagram_config()
    token = cfg.get("META_ACCESS_TOKEN", "").strip()
    biz_id = cfg.get("INSTAGRAM_BUSINESS_ID", "").strip()

    if not token or not biz_id:
        print("[ERROR] META_ACCESS_TOKEN or INSTAGRAM_BUSINESS_ID is missing in config.md")
        return None, _failed

    # 이미 URL인 경우 직접 사용
    if video_source.startswith("http://") or video_source.startswith("https://"):
        result = _publish_reels_with_url(video_source, caption, token, biz_id, slot)
        return result, _failed

    # 로컬 파일인 경우: 업로더 우선순위 목록을 순회하며 자동 폴백
    uploaders = [
        ("Uguu.se", upload_to_uguu),
        ("Catbox.moe", upload_image_to_catbox),
        ("Tmpfiles.org", upload_to_tmpfiles),
        ("Gofile.io", upload_to_gofile),
        ("Oshi.at", upload_to_oshi),
        ("File.io", upload_to_file_io),
        ("Transfer.sh", upload_to_transfer_sh),
    ]

    container_url = f"https://graph.facebook.com/v20.0/{biz_id}/media"

    for idx, (uploader_name, uploader_fn) in enumerate(uploaders):
        # 이전 시도에서 실패한 업로더 건너뛰기
        if uploader_name in _failed:
            print(f"[SKIP] {uploader_name} — 이전 시도에서 실패 이력 있어 건너뜀.")
            continue

        # 1) 업로드
        print(f"\n[UPLOAD] Trying uploader {idx+1}/{len(uploaders)}: {uploader_name}")
        url = uploader_fn(video_source)
        if not url:
            print(f"[WARN] {uploader_name} upload failed. Skipping to next.")
            _failed.add(uploader_name)
            continue

        # 2) 컨테이너 생성
        print(f"[INFO] 1/3. Creating Reels container for video: {url}")
        payload = {
            "media_type": "REELS",
            "video_url": url,
            "caption": caption,
            "share_to_feed": "true",
            "access_token": token
        }

        try:
            r = requests.post(container_url, data=payload, timeout=25)
            if r.status_code != 200:
                print(f"[ERROR] Container creation failed via {uploader_name} (status={r.status_code}): {r.text}")
                continue

            creation_id = r.json().get("id")
            if not creation_id:
                print(f"[ERROR] No creation ID from {uploader_name}. Response: {r.text}")
                continue

            # 3) 폴링 — status_code + status(상세 메시지) 동시 조회
            print(f"[INFO] 2/3. Polling video processing status for container: {creation_id}")
            status_url = f"https://graph.facebook.com/v20.0/{creation_id}?fields=status_code,status&access_token={token}"
            max_attempts = 60
            processing_result = None

            for attempt in range(max_attempts):
                sr = requests.get(status_url, timeout=10)
                status_data = sr.json()
                sc = status_data.get("status_code", "").upper()
                status_msg = status_data.get("status", "")
                print(f" -> Attempt {attempt+1}/{max_attempts}: Status is '{sc}'")

                if sc == "FINISHED":
                    processing_result = "FINISHED"
                    break
                elif sc == "ERROR":
                    print(f"[DIAG] Meta error detail: {status_msg}")
                    if "error code 0" in status_msg.lower():
                        processing_result = "DOWNLOAD_FAILURE"
                        print(f"[DIAG] → Meta couldn't download video from {uploader_name}. Trying next uploader.")
                    else:
                        processing_result = "VIDEO_ERROR"
                        print(f"[ERROR] → Video format/codec issue detected. No point retrying with other uploaders.")
                    break

                sleep_time = min(5 * (1.25 ** attempt), 60)
                time.sleep(sleep_time)
            else:
                print("[ERROR] Video processing timed out.")
                return None

            # 4) 결과 분기
            if processing_result == "DOWNLOAD_FAILURE":
                _failed.add(uploader_name)
                continue  # 다음 업로더로 자동 폴백

            if processing_result == "VIDEO_ERROR":
                return None, _failed  # 비디오 자체 문제 — 즉시 중단

            if processing_result == "FINISHED":
                # 5) 발행
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

                link_url = f"https://graph.facebook.com/v20.0/{media_id}?fields=permalink&access_token={token}"
                lr = requests.get(link_url, timeout=10)
                permalink = lr.json().get("permalink")

                print(f"[SUCCESS] Instagram Reels successfully published via {uploader_name}!")
                if permalink:
                    print(f" - 포스트 링크: {permalink}")
                    record_to_calendar(caption, permalink, slot=slot)
                    return permalink, _failed
                return media_id, _failed

        except Exception as e:
            print(f"[ERROR] Exception with {uploader_name}: {e}")
            _failed.add(uploader_name)
            continue

    print("[ERROR] All upload services exhausted. Could not publish Reels.")
    return None, _failed


def _publish_reels_with_url(url, caption, token, biz_id, slot=None):
    """이미 공개 URL이 주어진 경우의 단순 발행 경로."""
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
        r.raise_for_status()
        creation_id = r.json().get("id")
        if not creation_id:
            print(f"[ERROR] Failed to get Reels creation ID. Response: {r.text}")
            return None

        print(f"[INFO] Polling video processing status for container: {creation_id}")
        status_url = f"https://graph.facebook.com/v20.0/{creation_id}?fields=status_code,status&access_token={token}"
        for attempt in range(60):
            sr = requests.get(status_url, timeout=10)
            status_data = sr.json()
            sc = status_data.get("status_code", "").upper()
            status_msg = status_data.get("status", "")
            print(f" -> Attempt {attempt+1}/60: Status is '{sc}'")
            if sc == "FINISHED":
                break
            elif sc == "ERROR":
                print(f"[ERROR] Video processing failed: {status_msg}")
                return None
            time.sleep(min(5 * (1.25 ** attempt), 60))
        else:
            print("[ERROR] Video processing timed out.")
            return None

        publish_url = f"https://graph.facebook.com/v20.0/{biz_id}/media_publish"
        pr = requests.post(publish_url, data={"creation_id": creation_id, "access_token": token}, timeout=20)
        pr.raise_for_status()
        media_id = pr.json().get("id")
        if not media_id:
            return None

        lr = requests.get(f"https://graph.facebook.com/v20.0/{media_id}?fields=permalink&access_token={token}", timeout=10)
        permalink = lr.json().get("permalink")

        print(f"[SUCCESS] Instagram Reels successfully published!")
        if permalink:
            print(f" - 포스트 링크: {permalink}")
            record_to_calendar(caption, permalink, slot=slot)
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
