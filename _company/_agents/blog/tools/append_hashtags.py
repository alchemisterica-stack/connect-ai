import os
import json
import sys
import xmlrpc.client
import requests

HERE = os.path.dirname(os.path.abspath(__file__))

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
    
    xmlrpc_url = wp_domain if wp_domain.endswith("xmlrpc.php") else f"{wp_domain}/xmlrpc.php"
    client = xmlrpc.client.ServerProxy(xmlrpc_url)
    
    hashtags_text = "\n\n#감자떡 #이모모찌 #감자요리 #간단간식 #아이간식 #집밥레시피 #반찬만들기 #겉바속촉 #단짠단짠 #홈쿡 #감자전분 #치즈감자떡 #인기레시피"
    hashtags_html = "<br><br>#감자떡 #이모모찌 #감자요리 #간단간식 #아이간식 #집밥레시피 #반찬만들기 #겉바속촉 #단짠단짠 #홈쿡 #감자전분 #치즈감자떡 #인기레시피"

    # 1. Update WordPress Post (ID: 165)
    wp_post_id = 165
    print(f"[INFO] Fetching WordPress post {wp_post_id}...")
    try:
        post = client.metaWeblog.getPost(wp_post_id, wp_user, wp_pass)
        updated_description = post.get("description", "") + hashtags_text
        post_data = {
            "title": post.get("title"),
            "description": updated_description,
            "post_status": "publish",
            "categories": post.get("categories", ["요리/반찬"])
        }
        client.metaWeblog.editPost(wp_post_id, wp_user, wp_pass, post_data, True)
        print("[SUCCESS] Appended hashtags to WordPress post!")
    except Exception as e:
        print(f"[ERROR] Failed to update WordPress: {e}")

    # 2. Update Blogger Post
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
                
                # Fetch recent Blogger posts
                api_url = f"https://www.googleapis.com/blogger/v3/blogs/{blogger_id}/posts"
                headers = {
                    "Authorization": f"Bearer {access_token}",
                    "Content-Type": "application/json",
                    "User-Agent": "Connect-AI-Agent"
                }
                
                print("[INFO] Fetching Blogger posts...")
                import urllib3
                urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)
                res = requests.get(api_url, headers=headers, timeout=15, verify=False)
                if res.status_code == 200:
                    posts = res.json().get("items", [])
                    target_post = None
                    for p in posts:
                        if "blog-post_473.html" in p.get("url", ""):
                            target_post = p
                            break
                    
                    if target_post:
                        post_id = target_post.get("id")
                        print(f"[INFO] Found Blogger post ID: {post_id}. Updating...")
                        
                        updated_content = target_post.get("content", "") + hashtags_html
                        update_payload = {
                            "kind": "blogger#post",
                            "blog": {"id": blogger_id},
                            "title": target_post.get("title"),
                            "content": updated_content,
                            "labels": target_post.get("labels", ["요리/반찬"])
                        }
                        
                        update_url = f"{api_url}/{post_id}"
                        up_res = requests.put(update_url, json=update_payload, headers=headers, timeout=15, verify=False)
                        if up_res.status_code == 200:
                            print("[SUCCESS] Appended hashtags to Blogger post!")
                        else:
                            print(f"[ERROR] Blogger update API failed: {up_res.text}")
                    else:
                        print("[ERROR] Could not find the specific Blogger post with the URL matching 'blog-post_473.html' in the list.")
                else:
                    print(f"[ERROR] Failed to fetch Blogger posts: {res.text}")
        except Exception as e:
            print(f"[ERROR] Blogger update failed: {e}")

if __name__ == "__main__":
    main()
