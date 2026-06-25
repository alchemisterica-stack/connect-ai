import os
import sys

# Set standard output encoding
if sys.platform.startswith('win'):
    import io
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')

file_path = r"C:\Users\User\my-ai-office\assets\webview\dashboard.js"

if not os.path.exists(file_path):
    print("dashboard.js not found")
    sys.exit(1)

with open(file_path, "r", encoding="utf-8", errors="replace") as f:
    lines = f.readlines()

search_terms = ["getAutoSchedule", "autoScheduleData", "modal", "시간표", "schedule", "asOv"]

print("=== Search Results inside dashboard.js ===")
for idx, line in enumerate(lines):
    for term in search_terms:
        if term in line:
            print(f"Line {idx+1}: {line.strip()[:150]}")
            break
