import sys
import os
import json
import xmlrpc.client

def main():
    script_dir = os.path.dirname(os.path.abspath(__file__))
    config_path = os.path.join(script_dir, "blog_account.json")
    
    if not os.path.exists(config_path):
        print(f"ERROR: Configuration file not found at {config_path}")
        sys.exit(1)
        
    with open(config_path, "r", encoding="utf-8") as f:
        config = json.load(f)
        
    wp_domain = config.get("WP_DOMAIN", "").strip()
    wp_user = config.get("WP_USERNAME", "").strip()
    wp_pass = config.get("WP_APP_PASSWORD", "").strip()
    
    if not wp_domain or not wp_user or not wp_pass:
        print("ERROR: WP_DOMAIN, WP_USERNAME, and WP_APP_PASSWORD must be configured first.")
        sys.exit(1)
        
    domain = wp_domain
    if not domain.startswith("http://") and not domain.startswith("https://"):
        domain = "https://" + domain
    
    domain = domain.rstrip("/")
    xmlrpc_url = domain if domain.endswith("xmlrpc.php") else f"{domain}/xmlrpc.php"
    
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
            
    print(f"Connecting to WordPress XML-RPC: {xmlrpc_url} ...")
    try:
        client = xmlrpc.client.ServerProxy(xmlrpc_url)
        
        post = {
            "title": title,
            "description": content,
            "post_status": "publish"
        }
        
        print("Publishing post via XML-RPC...")
        post_id = client.metaWeblog.newPost("default", wp_user, wp_pass, post, True)
        
        print("SUCCESS: Post published successfully!")
        print(f"Post ID: {post_id}")
        print(f"URL: {domain}/?p={post_id}")
    except Exception as e:
        print(f"ERROR: Failed to publish to WordPress: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()
