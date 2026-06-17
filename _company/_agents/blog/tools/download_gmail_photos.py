#!/usr/bin/env python3
import os
import sys
import json
import imaplib
import email
from email.header import decode_header
import shutil

HERE = os.path.dirname(os.path.abspath(__file__))
CONFIG_PATH = os.path.join(HERE, "gmail_account.json")
OUTPUT_DIR = r"C:\Users\User\my-ai-office\assets\custom_recipe_photos\temp_downloads"

def clean_output_dir(path):
    if os.path.exists(path):
        shutil.rmtree(path)
    os.makedirs(path, exist_ok=True)

def main():
    if not os.path.exists(CONFIG_PATH):
        print(f"[ERROR] Config file not found at: {CONFIG_PATH}")
        sys.exit(1)
        
    with open(CONFIG_PATH, "r", encoding="utf-8") as f:
        config = json.load(f)
        
    email_addr = config.get("GMAIL_ADDRESS", "").strip()
    app_passwd = config.get("GMAIL_APP_PASSWORD", "").strip()
    
    if not email_addr or not app_passwd:
        print("[ERROR] Email or App Password is missing in config.")
        sys.exit(1)
        
    # Remove spaces from app password if present
    app_passwd = app_passwd.replace(" ", "")
    
    print(f"[INFO] Connecting to Gmail IMAP for {email_addr}...")
    try:
        mail = imaplib.IMAP4_SSL("imap.gmail.com")
        mail.login(email_addr, app_passwd)
    except Exception as e:
        print(f"[ERROR] Connection/Login failed: {e}")
        sys.exit(1)
        
    print("[INFO] Selecting INBOX...")
    mail.select("inbox")
    
    # Search for all emails
    status, messages = mail.search(None, "ALL")
    if status != "OK":
        print("[ERROR] Failed to search emails.")
        sys.exit(1)
        
    mail_ids = messages[0].split()
    if not mail_ids:
        print("[WARN] No emails found in INBOX.")
        sys.exit(0)
        
    print(f"[INFO] Found {len(mail_ids)} emails. Searching for latest with attachments...")
    
    clean_output_dir(OUTPUT_DIR)
    downloaded_files = []
    found_email = False
    
    # Iterate from newest to oldest (only look at the latest 20 emails to prevent slow fetching)
    for mail_id in reversed(mail_ids[-20:]):
        status, data = mail.fetch(mail_id, "(RFC822)")
        if status != "OK":
            continue
            
        raw_email = data[0][1]
        msg = email.message_from_bytes(raw_email)
        
        # Decode email subject
        subject, encoding = decode_header(msg["Subject"])[0]
        if isinstance(subject, bytes):
            subject = subject.decode(encoding or "utf-8", errors="ignore")
            
        # Check if email is multipart and has attachments
        has_attachment = False
        temp_files = []
        
        for part in msg.walk():
            content_type = part.get_content_type()
            content_disposition = str(part.get("Content-Disposition"))
            
            # Look for attachments (specifically images)
            if "attachment" in content_disposition or content_type.startswith("image/"):
                filename = part.get_filename()
                if filename:
                    decoded_filename, encoding = decode_header(filename)[0]
                    if isinstance(decoded_filename, bytes):
                        filename = decoded_filename.decode(encoding or "utf-8", errors="ignore")
                    
                    # Clean filename
                    filename = os.path.basename(filename)
                    
                    # Only download image extensions
                    ext = os.path.splitext(filename)[1].lower()
                    if ext in [".jpg", ".jpeg", ".png", ".gif", ".bmp", ".webp"]:
                        has_attachment = True
                        filepath = os.path.join(OUTPUT_DIR, filename)
                        
                        # Save attachment
                        payload = part.get_payload(decode=True)
                        if payload:
                            with open(filepath, "wb") as f:
                                f.write(payload)
                            temp_files.append(filename)
                            
        if has_attachment:
            print(f"[SUCCESS] Found email: Subject='{subject}'")
            print(f"[INFO] Downloaded {len(temp_files)} images to: {OUTPUT_DIR}")
            for f in temp_files:
                print(f"  - {f}")
            downloaded_files = temp_files
            found_email = True
            break # Stop after finding the latest email with attachments
            
    mail.logout()
    
    if not found_email:
        print("[WARN] No emails with image attachments found in the inbox.")
    else:
        print("[INFO] Download completed successfully.")
        
if __name__ == "__main__":
    main()
