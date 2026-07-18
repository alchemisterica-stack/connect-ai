import os
import json
import time
import sys

# Append current directory to path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))
from blog_post_generator import auto_publish_post

def main():
    if len(sys.argv) > 1:
        draft_path = os.path.abspath(sys.argv[1])
    else:
        draft_path = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", "..", "sessions", "blog_post_trendy_banchan.md"))
        
    if not os.path.exists(draft_path):
        print(f"[ERROR] Draft not found at: {draft_path}")
        sys.exit(1)

    print(f"[INFO] Reading draft from: {draft_path}")
    with open(draft_path, "r", encoding="utf-8") as f:
        content = f.read()

    category = "recipe"
    subject = "요리/반찬"
    
    parent_dir = os.path.basename(os.path.dirname(draft_path))
    base_name = os.path.basename(draft_path)
    if parent_dir and parent_dir not in ["sessions", "tools", "blog", ""]:
        target_file_name = f"session_{parent_dir}_{base_name}"
    else:
        target_file_name = base_name

    print(f"[INFO] Publishing cooking blog draft to WordPress and Blogger...")
    
    # Run publishing routine (which also generates the dynamic recipe banner)
    urls = auto_publish_post(content, category, subject, target_file_name)
    wp_url = urls.get("wp_url", "")
    blogger_url = urls.get("blogger_url", "")

    print(f"[SUCCESS] WordPress URL: {wp_url}")
    print(f"[SUCCESS] Blogger URL: {blogger_url}")

    # Record to blog_queue.json to show on Schedule Calendar
    queue_path = os.path.join(os.path.dirname(__file__), "blog_queue.json")
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
        "subject": subject,
        "lesson": target_file_name,
        "date": today_str,
        "draft_path": draft_path,
        "status": "published" if (wp_url or blogger_url) else "draft",
        "url": wp_url or blogger_url,
        "wp_url": wp_url,
        "blogger_url": blogger_url
    }

    if "completed_lessons" not in queue_data:
        queue_data["completed_lessons"] = []
    
    # Check if there is already a completed entry for this file to avoid duplicates
    existing_idx = -1
    for idx, entry in enumerate(queue_data["completed_lessons"]):
        if entry.get("lesson") == target_file_name and entry.get("subject") == subject:
            existing_idx = idx
            break
            
    if existing_idx != -1:
        queue_data["completed_lessons"][existing_idx] = completed_entry
        print("[INFO] Updated existing calendar entry for cooking blog.")
    else:
        queue_data["completed_lessons"].append(completed_entry)
        print("[INFO] Appended new calendar entry for cooking blog.")

    with open(queue_path, "w", encoding="utf-8") as f:
        json.dump(queue_data, f, indent=2, ensure_ascii=False)

    print("[SUCCESS] Successfully updated blog_queue.json and recorded to calendar!")

if __name__ == "__main__":
    main()
