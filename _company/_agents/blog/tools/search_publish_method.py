import os
import sys

# Set standard output encoding
if sys.platform.startswith('win'):
    import io
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')

file_path = r"C:\Users\User\.connect-ai-brain\_company\_agents\blog\tools\blog_post_generator.py"

with open(file_path, "r", encoding="utf-8", errors="replace") as f:
    lines = f.readlines()

search_terms = ["wordpress", "blogger", "xmlrpc", "api", "except", "post_to", "wp_url", "blogger_url"]

print("=== Search Results inside blog_post_generator.py ===")
# Search from line 724 onwards (inside auto_publish_post)
for idx in range(723, len(lines)):
    line = lines[idx]
    # If the line defines a function or has a keyword
    if "def " in line or any(term in line.lower() for term in ["requests.post", "xmlrpc", "fault", "except Exception", "return {"]):
        print(f"Line {idx+1}: {line.strip()[:150]}")
