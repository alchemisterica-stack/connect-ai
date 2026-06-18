import sys
import os
import json
import requests
from blog_post_generator import markdown_to_html_for_blogger

def main():
    script_dir = os.path.dirname(os.path.abspath(__file__))
    config_path = os.path.join(script_dir, "blog_account.json")
    
    if not os.path.exists(config_path):
        print(f"ERROR: Configuration file not found at {config_path}")
        sys.exit(1)
        
    with open(config_path, "r", encoding="utf-8") as f:
        config = json.load(f)
        
    blogger_id = config.get("BLOGGER_BLOG_ID", "").strip()
    api_key = config.get("BLOGGER_API_KEY", "").strip()
    
    if not blogger_id:
        print("ERROR: BLOGGER_BLOG_ID (Google Blogger ID) must be configured.")
        sys.exit(1)
        
    credentials_json = os.path.join(script_dir, "credentials.json")
    token_json = os.path.join(script_dir, "token.json")
    
    access_token = api_key
    if os.path.exists(credentials_json):
        print("Detected credentials.json. Using Google OAuth desktop app authentication flow...")
        try:
            from google_auth_oauthlib.flow import InstalledAppFlow
            from google.auth.transport.requests import Request
            from google.oauth2.credentials import Credentials
            
            scopes = ["https://www.googleapis.com/auth/blogger"]
            creds = None
            if os.path.exists(token_json):
                creds = Credentials.from_authorized_user_file(token_json, scopes)
            if not creds or not creds.valid:
                if creds and creds.expired and creds.refresh_token:
                    creds.refresh(Request())
                else:
                    flow = InstalledAppFlow.from_client_secrets_file(credentials_json, scopes)
                    creds = flow.run_local_server(port=0)
                with open(token_json, "w") as token_file:
                    token_file.write(creds.to_json())
            access_token = creds.token
            print("Successfully authenticated via Google OAuth!")
        except ImportError:
            print("ERROR: Google Auth libraries are missing for credentials.json authentication.")
            print("Please run: pip install google-auth-oauthlib google-auth-httplib2 google-api-python-client")
            sys.exit(1)
        except Exception as e:
            print(f"ERROR: Google OAuth flow failed: {e}")
            sys.exit(1)
    else:
        if not access_token:
            print("ERROR: Neither credentials.json nor BLOGGER_API_KEY is configured.")
            print("Please download credentials.json from Google Cloud Console and place it in the tools folder.")
            sys.exit(1)
            
    blog_id = blogger_id
    
    title = "새 블로그 포스팅"
    content = ""
    
    if len(sys.argv) > 2:
        title = sys.argv[1]
        content = sys.argv[2]
    elif len(sys.argv) == 2:
        file_path = sys.argv[1]
        if os.path.exists(file_path):
            with open(file_path, "r", encoding="utf-8") as f:
                raw_text = f.read()
                lines = raw_text.split("\n")
                if lines and lines[0].startswith("# "):
                    title = lines[0][2:].strip()
                    content = "\n".join(lines[1:])
                else:
                    title = "에이전트 자동 작성 포스팅"
                    content = raw_text
        else:
            print(f"ERROR: Specified file not found: {file_path}")
            sys.exit(1)
    else:
        drafts_dir = os.path.join(os.path.dirname(script_dir), "drafts")
        if os.path.exists(drafts_dir):
            drafts = [os.path.join(drafts_dir, d) for d in os.listdir(drafts_dir) if d.endswith(".md")]
            if drafts:
                latest_draft = max(drafts, key=os.path.getmtime)
                print(f"Found latest draft: {os.path.basename(latest_draft)}")
                with open(latest_draft, "r", encoding="utf-8") as f:
                    raw_text = f.read()
                    lines = raw_text.split("\n")
                    if lines and lines[0].startswith("# "):
                        title = lines[0][2:].strip()
                        content = "\n".join(lines[1:])
                    else:
                        title = "에이전트 자동 작성 포스팅"
                        content = raw_text
            else:
                print("ERROR: No drafts found in drafts directory and no arguments specified.")
                sys.exit(1)
        else:
            print("ERROR: Please specify a title and content, or a file path as an argument.")
            sys.exit(1)

    html_content = markdown_to_html_for_blogger(content)
    
    payload = {
        "kind": "blogger#post",
        "blog": {"id": blog_id},
        "title": title,
        "content": html_content
    }
    
    actual_blog_id = blog_id
    if not blog_id.isdigit():
        print(f"Resolving blog URL: https://{blog_id}.blogspot.com ...")
        resolve_url = f"https://www.googleapis.com/blogger/v3/blogs/byurl?url=https://{blog_id}.blogspot.com/&key={access_token}"
        try:
            import urllib3
            urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)
            r = requests.get(resolve_url, timeout=10, verify=False)
            if r.status_code == 200:
                actual_blog_id = r.json().get("id")
                print(f"Resolved Blog ID: {actual_blog_id}")
            else:
                r2 = requests.get(f"https://www.googleapis.com/blogger/v3/blogs/byurl?url=https://{blog_id}.blogspot.com/", headers={"Authorization": f"Bearer {access_token}"}, timeout=10, verify=False)
                if r2.status_code == 200:
                    actual_blog_id = r2.json().get("id")
                    print(f"Resolved Blog ID: {actual_blog_id}")
                else:
                    print("WARNING: Could not resolve Blogger name to numerical ID, using it as is.")
        except Exception as e:
            print(f"WARNING: Error resolving blog ID: {e}")

    api_url = f"https://www.googleapis.com/blogger/v3/blogs/{actual_blog_id}/posts"
    headers = {
        "Authorization": f"Bearer {access_token}",
        "Content-Type": "application/json",
        "User-Agent": "Connect-AI-Agent"
    }
    
    print(f"Attempting to publish to Blogger: {blog_id} (ID: {actual_blog_id}) ...")
    try:
        import urllib3
        urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)
        response = requests.post(api_url, json=payload, headers=headers, timeout=15, verify=False)
        if response.status_code == 200:
            data = response.json()
            print("SUCCESS: Post published to Google Blogger successfully!")
            print(f"Post ID: {data.get('id')}")
            print(f"URL: {data.get('url')}")
        else:
            print(f"FAILED: Blogger API responded with status code {response.status_code}")
            print(response.text)
            sys.exit(1)
    except Exception as e:
        print(f"ERROR: Failed to connect to Google Blogger API: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()
