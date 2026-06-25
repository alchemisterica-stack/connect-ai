import os
import sys

# Set standard output encoding
if sys.platform.startswith('win'):
    import io
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')

file_path = r"C:\Users\User\my-ai-office\src\extension.ts"

with open(file_path, "r", encoding="utf-8", errors="replace") as f:
    lines = f.readlines()

start_idx = 13245
end_idx = 13450

print(f"=== Printing extension.ts from line {start_idx} to {end_idx} ===")
for i in range(start_idx - 1, end_idx):
    if i < len(lines):
        print(f"L{i+1}: {lines[i].rstrip()}")
