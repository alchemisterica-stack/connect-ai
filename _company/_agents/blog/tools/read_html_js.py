import os
import sys

# Set standard output encoding
if sys.platform.startswith('win'):
    import io
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')

file_path = r"C:\Users\User\my-ai-office\src\extension.ts"

with open(file_path, "r", encoding="utf-8", errors="replace") as f:
    lines = f.readlines()

start_idx = 12707
found_script = False
script_lines = []

for i in range(start_idx - 1, len(lines)):
    line = lines[i]
    if "<script>" in line:
        found_script = True
    if found_script:
        script_lines.append((i+1, line.rstrip()))
    if "</script>" in line:
        break

print(f"=== Found <script> block in _html() (Lines: {script_lines[0][0]} to {script_lines[-1][0]}) ===")
# Print the first 150 lines of the script block
for line_num, content in script_lines[:150]:
    print(f"L{line_num}: {content}")
