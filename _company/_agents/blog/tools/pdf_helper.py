#!/usr/bin/env python3
import os
import sys
import json
import re

if sys.platform.startswith('win'):
    import io
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')
    sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding='utf-8', errors='replace')

try:
    import pypdf
except ImportError:
    print("[ERROR] pypdf library is required. Run 'pip install pypdf'.")
    sys.exit(1)

# Paths
HERE = os.path.dirname(os.path.abspath(__file__))
# 00_Raw root directory: C:\Users\User\.connect-ai-brain\_company\00_Raw
RAW_ROOT = os.path.abspath(os.path.join(HERE, "..", "..", "..", "00_Raw"))

def split_pdf(pdf_path, subject_name, pages_per_part=8, lessons_per_week=2):
    if not os.path.exists(pdf_path):
        print(f"[ERROR] PDF file not found at: {pdf_path}")
        return False

    output_dir = os.path.join(RAW_ROOT, subject_name)
    os.makedirs(output_dir, exist_ok=True)

    print(f"[INFO] Loading master PDF: {pdf_path}")
    try:
        reader = pypdf.PdfReader(pdf_path)
    except Exception as e:
        print(f"[ERROR] Failed to load PDF file: {e}")
        return False

    total_pages = len(reader.pages)
    print(f"[INFO] Total Pages: {total_pages}, Pages per Part: {pages_per_part}, Lessons per Week: {lessons_per_week}")

    part_idx = 1
    start_page = 0

    while start_page < total_pages:
        end_page = min(start_page + pages_per_part, total_pages)
        writer = pypdf.PdfWriter()
        
        for i in range(start_page, end_page):
            writer.add_page(reader.pages[i])

        week = (part_idx - 1) // lessons_per_week + 1
        lesson = (part_idx - 1) % lessons_per_week + 1
        filename = f"{week}주차_{lesson}교시.pdf"
        filepath = os.path.join(output_dir, filename)

        try:
            with open(filepath, "wb") as out_f:
                writer.write(out_f)
            print(f"[SUCCESS] Saved part {part_idx} as '{filename}' (Pages {start_page+1} to {end_page})")
        except Exception as e:
            print(f"[ERROR] Failed to save {filename}: {e}")
            return False

        start_page = end_page
        part_idx += 1

    print(f"[SUCCESS] Successfully split PDF into {part_idx - 1} parts in folder: {output_dir}")
    return True

def extract_all_text(subject_name):
    subject_dir = os.path.join(RAW_ROOT, subject_name)
    if not os.path.exists(subject_dir):
        print(f"[ERROR] Subject directory not found: {subject_dir}")
        return False

    print(f"[INFO] Scanning directory: {subject_dir}")
    try:
        files = os.listdir(subject_dir)
    except Exception as e:
        print(f"[ERROR] Failed to list directory contents: {e}")
        return False

    pdf_files = [f for f in files if f.lower().endswith('.pdf')]
    if not pdf_files:
        print("[INFO] No PDF files found in this subject directory.")
        return True

    print(f"[INFO] Found {len(pdf_files)} PDF files to process.")

    success_count = 0
    for pdf_file in pdf_files:
        pdf_path = os.path.join(subject_dir, pdf_file)
        txt_name = pdf_file.rsplit('.', 1)[0] + '.txt'
        txt_path = os.path.join(subject_dir, txt_name)

        if os.path.exists(txt_path):
            print(f"[INFO] Skip '{pdf_file}': Text file counterpart already exists.")
            success_count += 1
            continue

        print(f"[INFO] Converting '{pdf_file}' to text...")
        try:
            reader = pypdf.PdfReader(pdf_path)
            text_list = []
            for page in reader.pages:
                text = page.extract_text()
                if text:
                    text_list.append(text)
            full_text = "\n".join(text_list)

            with open(txt_path, "w", encoding="utf-8") as txt_f:
                txt_f.write(full_text)
            print(f"[SUCCESS] Converted '{pdf_file}' -> '{txt_name}' ({len(full_text)} chars)")
            success_count += 1
        except Exception as e:
            print(f"[ERROR] Failed to convert '{pdf_file}': {e}")

    print(f"[INFO] Completed. Successfully processed {success_count}/{len(pdf_files)} files.")
    return True

def main():
    if len(sys.argv) < 3:
        print("[USAGE] python pdf_helper.py split <pdf_path> <subject_name> <pages_per_part> <lessons_per_week>")
        print("        python pdf_helper.py extract_all <subject_name>")
        sys.exit(1)

    cmd = sys.argv[1].lower()

    if cmd == "split":
        if len(sys.argv) < 4:
            print("[ERROR] Missing arguments for split command.")
            sys.exit(1)
        pdf_path = sys.argv[2]
        subject_name = sys.argv[3]
        pages_per_part = 8
        lessons_per_week = 2

        if len(sys.argv) >= 5:
            try:
                pages_per_part = int(sys.argv[4])
            except ValueError:
                pass
        if len(sys.argv) >= 6:
            try:
                lessons_per_week = int(sys.argv[5])
            except ValueError:
                pass

        success = split_pdf(pdf_path, subject_name, pages_per_part, lessons_per_week)
        sys.exit(0 if success else 1)

    elif cmd == "extract_all":
        subject_name = sys.argv[2]
        success = extract_all_text(subject_name)
        sys.exit(0 if success else 1)

    else:
        print(f"[ERROR] Unknown command: {cmd}")
        sys.exit(1)

if __name__ == "__main__":
    main()
