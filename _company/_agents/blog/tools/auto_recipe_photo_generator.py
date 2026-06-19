#!/usr/bin/env python3
import os
import re
import sys
import time
import urllib.parse
import requests
import random
import io
from PIL import Image

HERE = os.path.dirname(os.path.abspath(__file__))
COMPANY_DIR = os.path.abspath(os.path.join(HERE, "..", "..", ".."))
REPORT_PATH = os.path.join(COMPANY_DIR, "sessions", "latest_trend_report.md")
SRC_DIR = r"C:\Users\User\my-ai-office\assets\custom_recipe_photos"

# Mapping Korean names to English descriptions for better AI prompts
DISH_PROMPT_MAP = {
    "감자떡": "Korean potato rice cake (Imo Mochi)",
    "이모모찌": "Korean potato rice cake (Imo Mochi)",
    "소고기애호박죽": "Korean beef zucchini porridge (Sogogi Aehobak Juk)",
    "애호박죽": "Korean beef zucchini porridge (Sogogi Aehobak Juk)",
    "깻잎장아찌": "Korean pickled sesame leaves (Kkaennip Jangajji)",
    "오이냉국": "Korean cold cucumber soup (Oi Naengguk)",
}

def parse_target_dishes():
    if not os.path.exists(REPORT_PATH):
        print(f"[ERROR] Trend report not found at: {REPORT_PATH}")
        return []
    
    try:
        with open(REPORT_PATH, "r", encoding="utf-8") as f:
            content = f.read()
    except Exception as e:
        print(f"[ERROR] Failed to read trend report: {e}")
        return []
        
    recipe_section = re.search(r'### 2\.\s*\[요리/반찬\]([\s\S]*?)(?:###|$)', content)
    if not recipe_section:
        print("[WARN] No recipe section found in trend report.")
        return []
        
    section_text = recipe_section.group(1)
    
    # Extract dish names
    found_dishes = set()
    for word in DISH_PROMPT_MAP.keys():
        # Handle spaces or slight variations
        pattern = r"\s*".join(list(word))
        if re.search(pattern, section_text):
            found_dishes.add(word)
            
    # Normalize synonyms
    if "이모모찌" in found_dishes and "감자떡" not in found_dishes:
        found_dishes.add("감자떡")
    if "애호박죽" in found_dishes and "소고기애호박죽" not in found_dishes:
        found_dishes.add("소고기애호박죽")
        
    return sorted(list(found_dishes))

def download_ai_image(prompt, filename):
    encoded_prompt = urllib.parse.quote(prompt)
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
    }
    
    filepath = os.path.join(SRC_DIR, filename)
    print(f"[INFO] Requesting AI image for '{filename}'...")
    
    for attempt in range(5):
        seed = random.randint(1, 100000)
        url = f"https://image.pollinations.ai/prompt/{encoded_prompt}?width=800&height=600&nologo=true&seed={seed}"
        try:
            res = requests.get(url, headers=headers, timeout=40, verify=False)
            if res.status_code == 200 and len(res.content) > 1000:
                img = Image.open(io.BytesIO(res.content))
                rgb_img = img.convert("RGB")
                rgb_img.save(filepath, "JPEG", quality=95)
                print(f"[SUCCESS] Saved AI image to: {filepath} on attempt {attempt+1}")
                return True
            else:
                print(f"[WARN] Attempt {attempt+1} failed with status code: {res.status_code}. Retrying after sleep...")
        except Exception as e:
            print(f"[WARN] Attempt {attempt+1} encountered error: {e}. Retrying after sleep...")
        
        # Sleep to avoid rate limiting
        time.sleep(10)
        
    return False

def main():
    print("==================================================")
    print(" [Cooking] Weekly Target Recipe Photo AI Generator")
    print(f" Time: {time.strftime('%Y-%m-%d %H:%M:%S')}")
    print("==================================================")
    
    os.makedirs(SRC_DIR, exist_ok=True)
    
    dishes = parse_target_dishes()
    print(f"[INFO] Target dishes detected for this week: {dishes}")
    
    if not dishes:
        print("[INFO] No dishes detected to process. Exiting.")
        sys.exit(0)
        
    for dish in dishes:
        # Normalize name for file writing
        # Use 감자떡 instead of 이모모찌 for consistent naming, etc.
        name_key = dish
        if dish == "이모모찌":
            name_key = "감자떡"
        elif dish == "애호박죽":
            name_key = "소고기애호박죽"
            
        english_desc = DISH_PROMPT_MAP.get(dish, "Korean food")
        
        wp_fin = f"{name_key}_wp_fin.jpg"
        blogger_fin = f"{name_key}_blogger_fin.jpg"
        default_fin = f"{name_key}_fin.jpg"
        
        wp_path = os.path.join(SRC_DIR, wp_fin)
        blogger_path = os.path.join(SRC_DIR, blogger_fin)
        default_path = os.path.join(SRC_DIR, default_fin)
        
        # 1. Generate Cozy Mint WordPress Image
        if not os.path.exists(wp_path):
            wp_prompt = (
                f"premium food photography of {english_desc} served in a warm ceramic dish, "
                "top-down flatlay, on a beautiful light mint green table mat, soft warm cozy kitchen lighting"
            )
            print(f"\n[INFO] Generating WordPress cozy image for: {name_key}")
            download_ai_image(wp_prompt, wp_fin)
            time.sleep(5)
        else:
            print(f"[INFO] WordPress image already exists: {wp_fin}")
            
        # 2. Generate White Modern Blogger Image
        if not os.path.exists(blogger_path):
            blogger_prompt = (
                f"professional culinary photography of {english_desc} in a clean modern bowl, "
                "bright natural daylight, on a clean white marble countertop background, minimalist table setup"
            )
            print(f"\n[INFO] Generating Blogger modern image for: {name_key}")
            download_ai_image(blogger_prompt, blogger_fin)
            time.sleep(5)
        else:
            print(f"[INFO] Blogger image already exists: {blogger_fin}")
            
        # 3. Create default fin by copying wp_fin
        if not os.path.exists(default_path) and os.path.exists(wp_path):
            import shutil
            shutil.copy2(wp_path, default_path)
            print(f"[INFO] Copied {wp_fin} to {default_fin}")
            
    print("\n[SUCCESS] Weekly target recipe photo generation workflow completed!")

if __name__ == "__main__":
    main()
