#!/usr/bin/env python3
import os
import json
import sys
import time

if sys.platform.startswith('win'):
    import io
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')
    sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding='utf-8', errors='replace')


try:
    import requests
except ImportError:
    print("[ERROR] requests library is required. Run 'pip install requests'.")
    sys.exit(1)

# Paths
HERE = os.path.dirname(os.path.abspath(__file__))
CONFIG_PATH = os.path.join(HERE, "blog_post_generator.json")
DRAFTS_ROOT = os.path.join(HERE, "..", "drafts")

# Default Config
DEFAULT_CONFIG = {
    "OLLAMA_URL": "http://127.0.0.1:11434",
    "MODEL": "llama3.2:1b"
}

import urllib.request
import urllib.parse
import re
import xml.etree.ElementTree as ET

# Paths
HERE = os.path.dirname(os.path.abspath(__file__))
CONFIG_PATH = os.path.join(HERE, "blog_post_generator.json")
DRAFTS_ROOT = os.path.join(HERE, "..", "drafts")

# Default Config
DEFAULT_CONFIG = {
    "OLLAMA_URL": "http://127.0.0.1:11434",
    "MODEL": "llama3.2:1b"
}

def fetch_online_context(query):
    return ""

def load_config():
    if not os.path.exists(CONFIG_PATH):
        try:
            with open(CONFIG_PATH, "w", encoding="utf-8") as f:
                json.dump(DEFAULT_CONFIG, f, indent=2, ensure_ascii=False)
        except Exception:
            pass
        return DEFAULT_CONFIG
    try:
        with open(CONFIG_PATH, "r", encoding="utf-8") as f:
            return json.load(f)
    except Exception:
        return DEFAULT_CONFIG

def ask_llm(ollama_url, model, prompt, gemini_api_key=None):
    if gemini_api_key:
        print("[LLM] Generating blog post draft using Google Gemini API...")
        try:
            url = f"https://generativelanguage.googleapis.com/v1beta/models/gemini-3.1-flash-lite:generateContent?key={gemini_api_key}"
            headers = {"Content-Type": "application/json"}
            payload = {
                "contents": [
                    {
                        "parts": [
                            {"text": prompt}
                        ]
                    }
                ]
            }
            r = requests.post(url, json=payload, headers=headers, timeout=60)
            r.raise_for_status()
            res_data = r.json()
            return res_data["candidates"][0]["content"]["parts"][0]["text"].strip()
        except Exception as e:
            print(f"[WARN] Gemini API request failed: {e}")
            print("Falling back to local Ollama...")

    print(f"[LLM] Generating blog post draft using model '{model}'...")
    try:
        r = requests.post(
            f"{ollama_url.rstrip('/')}/api/generate",
            json={"model": model, "prompt": prompt, "stream": False},
            timeout=1800
        )
        r.raise_for_status()
        return r.json().get("response", "").strip()
    except Exception as e:
        print(f"[WARN] Ollama request failed with error: {e}")
        if "11434" in ollama_url:
            fallback_url = "http://127.0.0.1:1234/v1/chat/completions"
            print(f"[WARN] Ollama failed, trying LM Studio ({fallback_url}) fallback...")
            try:
                r = requests.post(
                    fallback_url,
                    json={
                        "model": model,
                        "messages": [{"role": "user", "content": prompt}],
                        "stream": False
                    },
                    timeout=1800
                )
                r.raise_for_status()
                return r.json().get("choices", [{}])[0].get("message", {}).get("content", "").strip()
            except Exception as e2:
                print(f"[ERROR] LLM call failed: {e2}")
        return ""

def create_dynamic_banner(title, category, subject, output_path, is_blogger=False):
    import os
    import datetime
    import random
    try:
        from PIL import Image, ImageDraw, ImageFont
    except ImportError:
        print("[WARN] Pillow library not found. Cannot generate dynamic banner.")
        return
        
    width, height = 1200, 630
    
    if category in ["recipe", "mindset"]:
        # Draw text-free minimalist seasonal landscape banner
        img = Image.new("RGB", (width, height))
        draw = ImageDraw.Draw(img)
        
        month = datetime.datetime.now().month
        if month in [3, 4, 5]:
            season = "spring"
        elif month in [6, 7, 8]:
            season = "summer"
        elif month in [9, 10, 11]:
            season = "autumn"
        else:
            season = "winter"
            
        if season == "spring":
            if not is_blogger:
                # Sky: Soft pink to light sky blue gradient
                for y in range(height):
                    factor = y / height
                    r = int(224 + (186 - 224) * factor)
                    g = int(242 + (212 - 242) * factor)
                    b = int(254 + (235 - 254) * factor)
                    draw.line([(0, y), (width, y)], fill=(r, g, b))
                # Soft yellow sun
                draw.ellipse([850, 100, 970, 220], fill=(254, 240, 138))
                # Green Hills
                draw.ellipse([-100, 400, 700, 900], fill=(134, 239, 172))
                draw.ellipse([400, 350, 1300, 950], fill=(74, 222, 128))
                draw.ellipse([100, 480, 1000, 900], fill=(34, 197, 94))
            else:
                # Blogger Spring: Soft yellow-peach meadow with plant/blossom details
                for y in range(height):
                    factor = y / height
                    r = int(254 + (253 - 254) * factor)
                    g = int(243 + (186 - 243) * factor)
                    b = int(199 + (116 - 199) * factor)
                    draw.line([(0, y), (width, y)], fill=(r, g, b))
                # Sun
                draw.ellipse([150, 100, 270, 220], fill=(251, 146, 60))
                # Soft olive green and lavender meadow hills
                draw.ellipse([-150, 420, 600, 850], fill=(163, 230, 53))   # Light lime/olive
                draw.ellipse([500, 400, 1400, 900], fill=(167, 139, 250))  # Light purple/lavender
                draw.ellipse([150, 470, 1050, 900], fill=(101, 163, 13))   # Olive green
            
        elif season == "summer":
            if not is_blogger:
                # Sky: Deep blue to bright cyan gradient
                for y in range(height):
                    factor = y / height
                    r = int(14 + (6 - 14) * factor)
                    g = int(116 + (182 - 116) * factor)
                    b = int(144 + (212 - 144) * factor)
                    draw.line([(0, y), (width, y)], fill=(r, g, b))
                # Golden sun
                draw.ellipse([100, 80, 250, 230], fill=(253, 224, 71))
                # Beach & Sea
                draw.polygon([(0, 450), (450, 630), (0, 630)], fill=(254, 243, 199))
                draw.polygon([(0, 530), (1200, 400), (1200, 630), (0, 630)], fill=(3, 105, 161))
                draw.polygon([(350, 560), (1200, 470), (1200, 630), (350, 630)], fill=(2, 132, 199))
            else:
                # Blogger Summer: Forest & plants sunset meadow theme
                for y in range(height):
                    factor = y / height
                    r = int(253 + (254 - 253) * factor)
                    g = int(186 + (240 - 186) * factor)
                    b = int(116 + (138 - 116) * factor)
                    draw.line([(0, y), (width, y)], fill=(r, g, b))
                # Large setting orange sun
                draw.ellipse([800, 150, 980, 330], fill=(249, 115, 22))
                # Overlapping rolling forest green hills (plant-like layers)
                draw.ellipse([-300, 380, 700, 900], fill=(20, 83, 45))     # Very dark forest green
                draw.ellipse([400, 320, 1600, 950], fill=(22, 163, 74))    # Fresh green
                draw.ellipse([50, 440, 1100, 900], fill=(34, 197, 94))     # Emerald green
                # Minimalist plant/leaf shapes in foreground
                draw.ellipse([300, 410, 340, 490], fill=(21, 128, 61))
                draw.ellipse([330, 420, 360, 490], fill=(21, 128, 61))
            
        elif season == "autumn":
            if not is_blogger:
                # Sky: Sunset gradient (violet to orange)
                for y in range(height):
                    factor = y / height
                    r = int(109 + (249 - 109) * factor)
                    g = int(40 + (115 - 40) * factor)
                    b = int(217 + (22 - 217) * factor)
                    draw.line([(0, y), (width, y)], fill=(r, g, b))
                # Red Sun
                draw.ellipse([900, 150, 1020, 270], fill=(239, 68, 68))
                # Autumn Mountains
                draw.polygon([(200, 630), (550, 300), (900, 630)], fill=(120, 53, 4))
                draw.polygon([(-100, 630), (250, 350), (600, 630)], fill=(180, 83, 9))
                draw.polygon([(600, 630), (950, 380), (1300, 630)], fill=(146, 64, 14))
            else:
                # Blogger Autumn: Misty grey-blue sky with golden-yellow and red maple hills
                for y in range(height):
                    factor = y / height
                    r = int(203 + (148 - 203) * factor)
                    g = int(163 + (163 - 163) * factor) # Make it distinct grey-blue
                    b = int(225 + (184 - 225) * factor)
                    draw.line([(0, y), (width, y)], fill=(r, g, b))
                # Sun
                draw.ellipse([150, 120, 250, 220], fill=(251, 146, 60))
                # Golden and red maple hills
                draw.ellipse([-200, 420, 600, 900], fill=(234, 179, 8))     # Golden yellow
                draw.ellipse([500, 360, 1500, 950], fill=(185, 28, 28))     # Dark red
                draw.ellipse([100, 460, 1100, 900], fill=(217, 119, 6))     # Amber orange
            
        else:  # winter
            if not is_blogger:
                # Sky: Twilight indigo to purple
                for y in range(height):
                    factor = y / height
                    r = int(30 + (88 - 30) * factor)
                    g = int(58 + (28 - 58) * factor)
                    b = int(138 + (135 - 138) * factor)
                    draw.line([(0, y), (width, y)], fill=(r, g, b))
                # Moon
                draw.ellipse([800, 80, 920, 200], fill=(241, 245, 249))
                # Snow Hills
                draw.ellipse([-200, 450, 600, 900], fill=(226, 232, 240))
                draw.ellipse([400, 400, 1400, 1000], fill=(241, 245, 249))
                # Falling snow
                random.seed(42)
                for _ in range(50):
                    sx = random.randint(0, width)
                    sy = random.randint(0, height - 200)
                    sr = random.randint(2, 5)
                    draw.ellipse([sx - sr, sy - sr, sx + sr, sy + sr], fill=(255, 255, 255))
            else:
                # Blogger Winter: Ice-blue twilight sky with silver/white snow hills and evergreen tree shapes
                for y in range(height):
                    factor = y / height
                    r = int(15 + (8 - 15) * factor)
                    g = int(23 + (47 - 23) * factor)
                    b = int(42 + (73 - 42) * factor)
                    draw.line([(0, y), (width, y)], fill=(r, g, b))
                # Yellow moon
                draw.ellipse([200, 100, 300, 200], fill=(254, 240, 138))
                # White snow hills
                draw.ellipse([-300, 440, 500, 900], fill=(241, 245, 249))
                draw.ellipse([300, 410, 1300, 950], fill=(226, 232, 240))
                # Dark evergreen silhouettes in background
                draw.polygon([(650, 410), (670, 360), (690, 410)], fill=(30, 41, 59))
                draw.polygon([(700, 430), (720, 380), (740, 430)], fill=(30, 41, 59))
                
        img.convert("RGB").save(output_path, "PNG")
        print(f"[DYNAMIC BANNER] Created text-free {season} landscape banner for {category} at: {output_path}")
        return

    # Standard card banner for study summary
    img = Image.new("RGBA", (width, height), (0, 0, 0, 0))
    
    # 1. Gradient background selection
    color1 = (30, 58, 138, 255)  # #1e3a8a (Navy blue)
    color2 = (6, 182, 212, 255)  # #06b6d4 (Teal/cyan)
        
    # Draw linear gradient from top-left to bottom-right
    for y in range(height):
        for x in range(width):
            factor = (x / width + y / height) / 2
            r = int(color1[0] + (color2[0] - color1[0]) * factor)
            g = int(color1[1] + (color2[1] - color1[1]) * factor)
            b = int(color1[2] + (color2[2] - color1[2]) * factor)
            img.putpixel((x, y), (r, g, b, 255))
            
    # Redraw draw object
    draw = ImageDraw.Draw(img)
    
    # 2. Draw modern Card overlay
    card_margin = 60
    card_overlay = Image.new("RGBA", (width, height), (0, 0, 0, 0))
    card_draw = ImageDraw.Draw(card_overlay)
    card_draw.rounded_rectangle(
        [card_margin, card_margin, width - card_margin, height - card_margin],
        radius=24,
        fill=(255, 255, 255, 30),
        outline=(255, 255, 255, 60),
        width=2
    )
    img = Image.alpha_composite(img, card_overlay)
    draw = ImageDraw.Draw(img)
    
    # 3. Load font (Malgun Gothic or default)
    font_path = "C:\\Windows\\Fonts\\malgun.ttf"
    if not os.path.exists(font_path):
        font_path = "C:\\Windows\\Fonts\\arial.ttf"
        
    try:
        font_title = ImageFont.truetype(font_path, 48)
        font_subtitle = ImageFont.truetype(font_path, 32)
        font_tag = ImageFont.truetype(font_path, 22)
    except Exception:
        font_title = ImageFont.load_default()
        font_subtitle = ImageFont.load_default()
        font_tag = ImageFont.load_default()
        
    # 4. Draw Pill Badge tag
    tag_text = f"📚 {subject} 학습 요약"
        
    tag_w = 320
    tag_h = 42
    tag_x = width // 2 - tag_w // 2
    tag_y = card_margin + 40
    draw.rounded_rectangle(
        [tag_x, tag_y, tag_x + tag_w, tag_y + tag_h],
        radius=20,
        fill=(255, 255, 255, 50),
        outline=(255, 255, 255, 100),
        width=1
    )
    draw.text((width // 2, tag_y + tag_h // 2), tag_text, fill=(255, 255, 255, 255), font=font_tag, anchor="mm")
    
    # 5. Draw Title text
    import re
    title_text = title
    max_len = 24
    lines = []
    if len(title_text) > max_len:
        words = title_text.split()
        current_line = ""
        for word in words:
            if len(current_line + " " + word) <= max_len:
                current_line = (current_line + " " + word).strip()
            else:
                lines.append(current_line)
                current_line = word
        if current_line:
            lines.append(current_line)
    else:
        lines.append(title_text)
        
    lines = lines[:2]
    title_y = height // 2 - 20
    if len(lines) == 1:
        draw.text((width // 2, title_y), lines[0], fill=(255, 255, 255, 255), font=font_title, anchor="mm")
    else:
        draw.text((width // 2, title_y - 35), lines[0], fill=(255, 255, 255, 255), font=font_title, anchor="mm")
        draw.text((width // 2, title_y + 35), lines[1], fill=(255, 255, 255, 255), font=font_title, anchor="mm")
        
    # 6. Draw footer logo
    footer_text = "congcandy.wordpress.com" if not is_blogger else "congcandy.blogspot.com"
    draw.text((width // 2, height - card_margin - 60), footer_text, fill=(255, 255, 255, 180), font=font_subtitle, anchor="mm")
    
    img.convert("RGB").save(output_path, "PNG")
    print(f"[DYNAMIC BANNER] Created banner for '{title}' at: {output_path}")

def create_quiz_banner(subject, output_path, is_blogger=False):
    import os
    try:
        from PIL import Image, ImageDraw, ImageFont
    except ImportError:
        print("[WARN] Pillow library not found. Cannot generate quiz banner.")
        return
        
    width, height = 1000, 380
    img = Image.new("RGBA", (width, height), (0, 0, 0, 0))
    
    # Gradient: indigo to violet/pink
    color1 = (79, 70, 229, 255)   # #4f46e5 (Indigo)
    color2 = (219, 39, 119, 255)  # #db2777 (Deep pink)
    
    for y in range(height):
        for x in range(width):
            factor = (x / width + y / height) / 2
            r = int(color1[0] + (color2[0] - color1[0]) * factor)
            g = int(color1[1] + (color2[1] - color1[1]) * factor)
            b = int(color1[2] + (color2[2] - color1[2]) * factor)
            img.putpixel((x, y), (r, g, b, 255))
            
    draw = ImageDraw.Draw(img)
    
    # Card overlay
    card_margin = 35
    card_overlay = Image.new("RGBA", (width, height), (0, 0, 0, 0))
    card_draw = ImageDraw.Draw(card_overlay)
    card_draw.rounded_rectangle(
        [card_margin, card_margin, width - card_margin, height - card_margin],
        radius=20,
        fill=(255, 255, 255, 25),
        outline=(255, 255, 255, 50),
        width=1
    )
    img = Image.alpha_composite(img, card_overlay)
    draw = ImageDraw.Draw(img)
    
    # Fonts
    font_path = "C:\\Windows\\Fonts\\malgun.ttf"
    if not os.path.exists(font_path):
        font_path = "C:\\Windows\\Fonts\\arial.ttf"
        
    try:
        font_title = ImageFont.truetype(font_path, 42)
        font_subtitle = ImageFont.truetype(font_path, 22)
        font_tag = ImageFont.truetype(font_path, 18)
    except Exception:
        font_title = ImageFont.load_default()
        font_subtitle = ImageFont.load_default()
        font_tag = ImageFont.load_default()
        
    # Draw Subject Pill
    tag_text = f"📚 {subject}"
    tag_w = 220
    tag_h = 32
    tag_x = width // 2 - tag_w // 2
    tag_y = card_margin + 25
    draw.rounded_rectangle(
        [tag_x, tag_y, tag_x + tag_w, tag_y + tag_h],
        radius=16,
        fill=(255, 255, 255, 40),
        outline=(255, 255, 255, 80),
        width=1
    )
    draw.text((width // 2, tag_y + tag_h // 2), tag_text, fill=(255, 255, 255, 255), font=font_tag, anchor="mm")
    
    # Draw Quiz Title
    draw.text((width // 2, height // 2 + 10), "✓ 자가진단 QUIZ", fill=(255, 255, 255, 255), font=font_title, anchor="mm")
    
    # Draw Subtitle
    draw.text((width // 2, height // 2 + 65), "문제를 풀며 오늘 배운 핵심 내용을 최종 점검해 보세요!", fill=(255, 255, 255, 200), font=font_subtitle, anchor="mm")
    
    img.convert("RGB").save(output_path, "PNG")
    print(f"[DYNAMIC QUIZ BANNER] Created quiz banner at: {output_path}")

def auto_publish_post(result, category, current_subject, target_file_name):

    import re
    # Clean up title: e.g. "1주차_2교시.pdf" or "1주차 2교시.pdf" -> remove week/lesson parts
    cleaned_lesson = target_file_name.replace('.pdf','').replace('.txt','').replace('.hwp','')
    cleaned_lesson = re.sub(r'^\d+주차\s*\d+교시\.?\s*', '', cleaned_lesson)
    cleaned_lesson = re.sub(r'^\d+주차_\d+교시_?', '', cleaned_lesson)
    cleaned_lesson = re.sub(r'^\d+주차_?', '', cleaned_lesson)
    cleaned_lesson = cleaned_lesson.strip()

    wp_title = f"{current_subject} - {cleaned_lesson}"
    wp_content = ""
    blogger_title = f"{current_subject} - {cleaned_lesson}"
    blogger_content = ""

    wp_match = re.search(r'========== WORDPRESS VERSION ==========\s*(?:#\s*(.*?)\n)?([\s\S]*?)(?:==========|$)', result)
    if wp_match:
        if wp_match.group(1):
            t_val = wp_match.group(1).strip()
            # If AI includes instruction text in title header, strip it or fallback
            if "워드프레스" not in t_val and "wordpress" not in t_val.lower() and len(t_val) < 100:
                wp_title = t_val
            else:
                # If it had instructions, extract first line of content if suitable, or stick to default
                wp_title = f"{current_subject} - {cleaned_lesson}"
        wp_content = wp_match.group(2).strip()

    blogger_match = re.search(r'========== BLOGGER VERSION ==========\s*(?:#\s*(.*?)\n)?([\s\S]*?)(?:==========|$)', result)
    if blogger_match:
        if blogger_match.group(1):
            t_val_bg = blogger_match.group(1).strip()
            if "블로거" not in t_val_bg and "blogger" not in t_val_bg.lower() and len(t_val_bg) < 100:
                blogger_title = t_val_bg
            else:
                blogger_title = f"{current_subject} - {cleaned_lesson}"
        blogger_content = blogger_match.group(2).strip()

    if not wp_content:
        wp_content = result
    if not blogger_content:
        blogger_content = result

    # Strip instruction remnants in the first few lines (e.g. "(본문은 ~ 작성해 주세요)")
    def clean_remnants(text, strip_markdown=False):
        import re
        lines = text.split('\n')
        cleaned_lines = []
        for line in lines:
            line_strip = line.strip()
            # Remove brackets indicating instructions like (본문은 ... )
            if line_strip.startswith('(') and ('어조로' in line_strip or '작성해' in line_strip or '제거하고' in line_strip or '요약해' in line_strip):
                continue
            if '========== WORDPRESS VERSION ==========' in line_strip or '========== BLOGGER VERSION ==========' in line_strip:
                continue
            if strip_markdown:
                line = re.sub(r'^#+\s*', '', line)
            cleaned_lines.append(line)
        text = '\n'.join(cleaned_lines).strip()
        
        # Replace circular numbers ①, ②, ③, ④... with bullet points "-" or clear text
        # Replace circular numbers with bullet points or numbers safely using unicode values
        circle_map = {
            '\u2460': '1.', '\u2461': '2.', '\u2462': '3.', '\u2463': '4.', '\u2464': '5.',
            '\u2465': '6.', '\u2466': '7.', '\u2467': '8.', '\u2468': '9.', '\u2469': '10.'
        }
        for circ, rep in circle_map.items():
            text = text.replace(circ, rep)
            
        if strip_markdown:
            text = text.replace('**', '')
            text = text.replace('***', '')
            
        return text


    wp_content = clean_remnants(wp_content, strip_markdown=True)
    blogger_content = clean_remnants(blogger_content)
    
    # Also clean up the titles if they somehow still contain brackets/weeks/instructions
    wp_title = re.sub(r'^\d+주차\s*\d+교시\.?\s*', '', wp_title)
    wp_title = re.sub(r'^\d+주차_\d+교시_?', '', wp_title)
    wp_title = re.sub(r'^\[워드프레스용\s*제목\]\s*', '', wp_title)
    wp_title = re.sub(r'^\[워드프레스용\]\s*', '', wp_title)
    wp_title = wp_title.replace('[', '').replace(']', '').strip()
    
    blogger_title = re.sub(r'^\d+주차\s*\d+교시\.?\s*', '', blogger_title)
    blogger_title = re.sub(r'^\d+주차_\d+교시_?', '', blogger_title)
    blogger_title = re.sub(r'^\[블로거용\s*제목\]\s*', '', blogger_title)
    blogger_title = re.sub(r'^\[블로거용\]\s*', '', blogger_title)
    blogger_title = blogger_title.replace('[', '').replace(']', '').strip()
    
    wp_url = ""
    wp_banner_url = ""
    blogger_banner_url = ""
    try:
        config_path = os.path.join(HERE, "blog_account.json")
        if os.path.exists(config_path):
            with open(config_path, "r", encoding="utf-8") as f:
                config = json.load(f)
            wp_domain = config.get("WP_DOMAIN", "").strip().rstrip("/")
            wp_user = config.get("WP_USERNAME", "").strip()
            wp_pass = config.get("WP_APP_PASSWORD", "").strip()
            if wp_domain and wp_user and wp_pass:
                xmlrpc_url = wp_domain if wp_domain.endswith("xmlrpc.php") else f"{wp_domain}/xmlrpc.php"
                import xmlrpc.client
                client = xmlrpc.client.ServerProxy(xmlrpc_url)
                
                # Check for custom media uploaded by user
                custom_banner_path = None
                
                # Check 02_미디어 directory
                media_dir = os.path.abspath(os.path.join(HERE, "..", "..", "..", "02_미디어"))
                if os.path.exists(media_dir):
                    media_files = [f for f in os.listdir(media_dir) if f.lower().endswith(('.png', '.jpg', '.jpeg'))]
                    if media_files:
                        custom_banner_path = os.path.join(media_dir, media_files[0])
                        print(f"[INFO] Found custom user image in 02_미디어: {custom_banner_path}")
                        
                # Check subject raw directory
                if not custom_banner_path:
                    raw_subject_dir = os.path.abspath(os.path.join(HERE, "..", "..", "..", "00_Raw", current_subject))
                    if os.path.exists(raw_subject_dir):
                        raw_media = [f for f in os.listdir(raw_subject_dir) if f.lower().endswith(('.png', '.jpg', '.jpeg')) and not f.endswith('banner.png')]
                        if raw_media:
                            custom_banner_path = os.path.join(raw_subject_dir, raw_media[0])
                            print(f"[INFO] Found custom image in raw directory: {custom_banner_path}")
                            
                # Determine paths to upload
                if custom_banner_path and os.path.exists(custom_banner_path):
                    banner_path = custom_banner_path
                    blogger_banner_path = custom_banner_path
                else:
                    # Generate dynamic banner using Pillow
                    banner_path = os.path.join(HERE, "temp_wp_banner.png")
                    blogger_banner_path = os.path.join(HERE, "temp_blogger_banner.png")
                    try:
                        create_dynamic_banner(wp_title, category, current_subject, banner_path, is_blogger=False)
                        create_dynamic_banner(blogger_title, category, current_subject, blogger_banner_path, is_blogger=True)
                    except Exception as gen_err:
                        print(f"[WARN] Dynamic banner generation failed: {gen_err}")
                        # Fallback to default banners if they exist
                        banner_path = os.path.join(HERE, "youth_instructor_banner.png")
                        blogger_banner_path = os.path.join(HERE, "youth_instructor_banner_blogger.png")
                
                # Upload WordPress Banner
                if os.path.exists(banner_path):
                    try:
                        with open(banner_path, "rb") as f:
                            banner_data = f.read()
                        res = client.wp.uploadFile(0, wp_user, wp_pass, {
                            "name": f"blog_banner_{int(time.time())}_wp.png",
                            "type": "image/png",
                            "bits": xmlrpc.client.Binary(banner_data),
                            "overwrite": True
                        })
                        wp_banner_url = res.get("url")
                    except Exception as img_err:
                        print(f"[WARN] WordPress banner upload failed: {img_err}")

                # Upload Blogger Banner
                if os.path.exists(blogger_banner_path):
                    try:
                        with open(blogger_banner_path, "rb") as f:
                            blogger_data = f.read()
                        res = client.wp.uploadFile(0, wp_user, wp_pass, {
                            "name": f"blog_banner_{int(time.time())}_blogger.png",
                            "type": "image/png",
                            "bits": xmlrpc.client.Binary(blogger_data),
                            "overwrite": True
                        })
                        blogger_banner_url = res.get("url")
                    except Exception as img_err:
                        print(f"[WARN] Blogger banner upload failed: {img_err}")

                wp_body = wp_content
                
                # Generate and Upload WordPress Quiz Banner (ONLY for study summaries category)
                wp_quiz_url = ""
                if category == "study":
                    wp_quiz_path = os.path.join(HERE, "temp_wp_quiz.png")
                    try:
                        create_quiz_banner(current_subject, wp_quiz_path)
                        if os.path.exists(wp_quiz_path):
                            with open(wp_quiz_path, "rb") as f:
                                quiz_data = f.read()
                            res = client.wp.uploadFile(0, wp_user, wp_pass, {
                                "name": f"quiz_banner_{int(time.time())}_wp.png",
                                "type": "image/png",
                                "bits": xmlrpc.client.Binary(quiz_data),
                                "overwrite": True
                            })
                            wp_quiz_url = res.get("url")
                    except Exception as q_err:
                        print(f"[WARN] WordPress quiz banner failed: {q_err}")

                    if wp_quiz_url:
                        img_tag = f'\n\n<img src="{wp_quiz_url}" style="max-width:70%; height:auto; display:block; margin: 20px auto;" alt="Quiz Banner" />\n\n'
                        pattern = r'\[?이곳에\s*학습\s*퀴즈\s*관련\s*이미지가?\s*들어갈\s*자리입니다\.?\]?'
                        if re.search(pattern, wp_body):
                            wp_body = re.sub(pattern, img_tag, wp_body)
                        else:
                            quiz_pattern = r'(###?\s*(?:자가진단|퀴즈|평가|QUIZ|핵심\s*문제|문제))'
                            if re.search(quiz_pattern, wp_body):
                                wp_body = re.sub(quiz_pattern, img_tag + r'\1', wp_body, count=1)
                            else:
                                wp_body = wp_body + img_tag

                if wp_banner_url:
                    wp_body = f'<img src="{wp_banner_url}" style="max-width:70%; height:auto; display:block; margin: 15px auto;" alt="Banner" />\n\n' + wp_body

                post_data = {
                    "title": wp_title,
                    "description": wp_body,
                    "post_status": "publish"
                }
                post_id = client.metaWeblog.newPost("default", wp_user, wp_pass, post_data, True)
                wp_url = f"{wp_domain}/?p={post_id}"
                print(f"[SUCCESS] WordPress auto-published! URL: {wp_url}")
    except Exception as e:
        print(f"[WARN] WordPress auto-publishing failed: {e}")

    blogger_url = ""
    try:
        config_path = os.path.join(HERE, "blog_account.json")
        if os.path.exists(config_path):
            with open(config_path, "r", encoding="utf-8") as f:
                config = json.load(f)
            blogger_id = config.get("BLOGGER_BLOG_ID", "").strip()
            token_json = os.path.join(HERE, "token.json")
            if blogger_id and os.path.exists(token_json):
                from google.oauth2.credentials import Credentials
                from google.auth.transport.requests import Request
                creds = Credentials.from_authorized_user_file(token_json, ["https://www.googleapis.com/auth/blogger"])
                if creds and creds.expired and creds.refresh_token:
                    creds.refresh(Request())
                if creds:
                    access_token = creds.token
                    
                    blogger_body = blogger_content
                    
                    # Generate and Upload Blogger Quiz Banner (ONLY for study summaries category)
                    blogger_quiz_url = ""
                    if category == "study":
                        blogger_quiz_path = os.path.join(HERE, "temp_blogger_quiz.png")
                        try:
                            create_quiz_banner(current_subject, blogger_quiz_path)
                            if os.path.exists(blogger_quiz_path):
                                with open(blogger_quiz_path, "rb") as f:
                                    quiz_data = f.read()
                                res = client.wp.uploadFile(0, wp_user, wp_pass, {
                                    "name": f"quiz_banner_{int(time.time())}_blogger.png",
                                    "type": "image/png",
                                    "bits": xmlrpc.client.Binary(quiz_data),
                                    "overwrite": True
                                })
                                blogger_quiz_url = res.get("url")
                        except Exception as q_err:
                            print(f"[WARN] Blogger quiz banner failed: {q_err}")

                        if blogger_quiz_url:
                            img_tag = f'\n\n<img src="{blogger_quiz_url}" style="max-width:70%; height:auto; display:block; margin: 20px auto;" alt="Quiz Banner" />\n\n'
                            pattern = r'\[?이곳에\s*학습\s*퀴즈\s*관련\s*이미지가?\s*들어갈\s*자리입니다\.?\]?'
                            if re.search(pattern, blogger_body):
                                blogger_body = re.sub(pattern, img_tag, blogger_body)
                            else:
                                quiz_pattern = r'(###?\s*(?:자가진단|퀴즈|평가|QUIZ|핵심\s*문제|문제))'
                                if re.search(quiz_pattern, blogger_body):
                                    blogger_body = re.sub(quiz_pattern, img_tag + r'\1', blogger_body, count=1)
                                else:
                                    blogger_body = blogger_body + img_tag

                    if blogger_banner_url:
                        blogger_body = f'<img src="{blogger_banner_url}" style="max-width:70%; height:auto; display:block; margin: 15px auto;" alt="Banner" />\n\n' + blogger_body
                    elif wp_banner_url:
                        blogger_body = f'<img src="{wp_banner_url}" style="max-width:70%; height:auto; display:block; margin: 15px auto;" alt="Banner" />\n\n' + blogger_body
                        
                    html_content = blogger_body.replace("\n", "<br>")
                    payload = {
                        "kind": "blogger#post",
                        "blog": {"id": blogger_id},
                        "title": blogger_title,
                        "content": html_content
                    }
                    api_url = f"https://www.googleapis.com/blogger/v3/blogs/{blogger_id}/posts"
                    headers = {
                        "Authorization": f"Bearer {access_token}",
                        "Content-Type": "application/json",
                        "User-Agent": "Connect-AI-Agent"
                    }
                    response = requests.post(api_url, json=payload, headers=headers, timeout=15, verify=False)
                    if response.status_code == 200:
                        data = response.json()
                        blogger_url = data.get("url", "")
                        print(f"[SUCCESS] Blogger auto-published! URL: {blogger_url}")
    except Exception as e:
        print(f"[WARN] Blogger auto-publishing failed: {e}")

    return {
        "wp_url": wp_url,
        "blogger_url": blogger_url
    }

def main():
    auto_mode = False
    category = ""
    input_arg = ""
    
    if len(sys.argv) == 2 and sys.argv[1].lower() == "auto":
        auto_mode = True
    elif len(sys.argv) < 3:
        print("[USAGE] python blog_post_generator.py <category> <input_text_or_path>")
        print("        categories: study / mindset / recipe")
        print("        Or: python blog_post_generator.py auto")
        sys.exit(1)
    else:
        category = sys.argv[1].lower()
        input_arg = sys.argv[2]

    # Queue configuration paths
    queue_path = os.path.join(HERE, "blog_queue.json")
    current_subject = ""
    current_idx = 0
    subj_queue = []
    completed_history = []
    files = []
    
    # Auto Mode logic
    if auto_mode:
        if not os.path.exists(queue_path):
            print("[ERROR] blog_queue.json not found. Run standard mode or create it first.")
            sys.exit(1)
            
        with open(queue_path, "r", encoding="utf-8") as f:
            queue_data = json.load(f)
            
        current_subject = queue_data.get("current_subject", "")
        current_idx = queue_data.get("current_lesson_index", 0)
        subj_queue = queue_data.get("queue", [])
        completed_history = queue_data.get("completed_history", [])
        
        if not current_subject:
            if subj_queue:
                current_subject = subj_queue.pop(0)
                current_idx = 0
                queue_data["current_subject"] = current_subject
                queue_data["current_lesson_index"] = 0
                queue_data["queue"] = subj_queue
            else:
                print("[ERROR] No active subject and the queue is empty.")
                sys.exit(1)
                
        # Find raw folder
        raw_dir = os.path.join(HERE, "..", "..", "..", "00_Raw", current_subject)
        if not os.path.exists(raw_dir):
            print(f"[ERROR] Raw materials folder not found at: {raw_dir}")
            sys.exit(1)
            
        # List lesson files (pdf, txt, hwp)
        all_raw = os.listdir(raw_dir)
        files = []
        for f in all_raw:
            f_low = f.lower()
            if f_low.endswith(('.pdf', '.hwp')):
                files.append(f)
            elif f_low.endswith('.txt'):
                base = f.rsplit('.', 1)[0]
                if not (f"{base}.pdf" in all_raw or f"{base}.PDF" in all_raw or f"{base}.hwp" in all_raw or f"{base}.HWP" in all_raw):
                    files.append(f)
        if not files:
            print(f"[ERROR] No lesson files found in: {raw_dir}")
            sys.exit(1)
            
        # Numerical/Natural sorting
        def natural_sort_key(filename):
            nums = re.findall(r'\d+', filename)
            return [int(n) for n in nums] if nums else [999]
            
        files.sort(key=natural_sort_key)
        
        if current_idx >= len(files):
            # Already completed? This shouldn't happen normally, but let's rotate.
            if subj_queue:
                completed_history.append(current_subject)
                current_subject = subj_queue.pop(0)
                current_idx = 0
                queue_data["current_subject"] = current_subject
                queue_data["current_lesson_index"] = 0
                queue_data["queue"] = subj_queue
                queue_data["completed_history"] = completed_history
                with open(queue_path, "w", encoding="utf-8") as f:
                    json.dump(queue_data, f, indent=2, ensure_ascii=False)
                print(f"[INFO] Rotated to next subject '{current_subject}' because index was out of bounds.")
                # Reload files
                raw_dir = os.path.join(HERE, "..", "..", "..", "00_Raw", current_subject)
                all_raw = os.listdir(raw_dir)
                files = []
                for f in all_raw:
                    f_low = f.lower()
                    if f_low.endswith(('.pdf', '.hwp')):
                        files.append(f)
                    elif f_low.endswith('.txt'):
                        base = f.rsplit('.', 1)[0]
                        if not (f"{base}.pdf" in all_raw or f"{base}.PDF" in all_raw or f"{base}.hwp" in all_raw or f"{base}.HWP" in all_raw):
                            files.append(f)
                files.sort(key=natural_sort_key)
            else:
                print(f"[ERROR] All lessons for '{current_subject}' are completed and queue is empty.")
                sys.exit(1)
                
        target_file_name = files[current_idx]
        target_file_path = os.path.join(raw_dir, target_file_name)
        category = "study" # default to study for lectures
        
        print(f"[INFO] Auto Queue Selected: Subject='{current_subject}', Lesson='{target_file_name}' ({current_idx + 1}/{len(files)})")
        
        # Parse content
        content = ""
                # Check if a text file already exists or if we should auto-extract PDF to a text file first
        text_counterpart_name = target_file_name.rsplit('.', 1)[0] + '.txt'
        text_counterpart_path = os.path.join(raw_dir, text_counterpart_name)

        if os.path.exists(text_counterpart_path):
            print(f"[INFO] Found pre-extracted text file counterpart: {text_counterpart_name}")
            try:
                with open(text_counterpart_path, "r", encoding="utf-8") as f:
                    content = f.read()
            except Exception as e:
                print(f"[ERROR] Failed to read pre-extracted text file: {e}")
                sys.exit(1)
        elif target_file_name.lower().endswith('.pdf'):
            try:
                import pypdf
                print(f"[INFO] Auto-extracting PDF to text file: {text_counterpart_name}...")
                reader = pypdf.PdfReader(target_file_path)
                text_list = []
                for idx_p, page in enumerate(reader.pages):
                    t = page.extract_text()
                    if t:
                        text_list.append(t)
                full_pdf_text = "\n".join(text_list)
                
                # Automatically save the extracted text file to the Raw folder
                with open(text_counterpart_path, "w", encoding="utf-8") as f:
                    f.write(full_pdf_text)
                print(f"[SUCCESS] Extracted text saved to: {text_counterpart_path}")
                
                content = full_pdf_text
                print(f"[INFO] Extracted {len(content)} characters from PDF: {target_file_name}")
            except Exception as e:
                print(f"[ERROR] Failed to extract PDF text: {e}")
                sys.exit(1)
        else:
            try:
                with open(target_file_path, "r", encoding="utf-8") as f:
                    content = f.read()
            except Exception as e:
                print(f"[ERROR] Failed to read text file: {e}")
                sys.exit(1)
        
        # Standardize content to clean circular numbers and brackets directly before passing to LLM
        circle_map = {
            '\u2460': '1.', '\u2461': '2.', '\u2462': '3.', '\u2463': '4.', '\u2464': '5.',
            '\u2465': '6.', '\u2466': '7.', '\u2467': '8.', '\u2468': '9.', '\u2469': '10.'
        }
        for circ, rep in circle_map.items():
            content = content.replace(circ, rep)
        
        # Clean double hashes or weird unicode brackets in prompt content
        content = re.sub(r'#+', ' ', content)

        # ----------------------------------------
        # Search online context and run LLM
        # ----------------------------------------
        online_context = fetch_online_context(current_subject)
        
        prompt = ""
        if category == "study":
            prompt = f"""당신은 자격증 시험 전문 교육 블로거입니다.
아래 제공된 '청소년지도사' 관련 학습 텍스트 및 온라인 검색 참고자료를 바탕으로 워드프레스와 구글 블로거에 각각 업로드할 두 가지 버전의 글을 작성하세요.

[중요 지시사항]
- 반드시 처음부터 끝까지 완전하고 완벽한 '한국어'로만 작성하십시오.
- 영어(sớm, also, juga 등), 베트남어, 태국어 등 외래어 토큰이나 타국어 단어가 단 한 단어도 섞여서는 안 됩니다. 
- 한자(漢字) 역시 가급적 한글로 순화하고 한글로만 작성하십시오.
- AI 임의의 다국어 번역 혼동이나 깨진 토큰 사용을 철저히 금지합니다.
- [가독성 극대화 지시사항] 모든 본문 문장은 가로로 너무 길게 이어지지 않도록 하십시오. 의미 단위 또는 약 1~2개 문장마다 적절히 빈칸 줄바꿈(엔터)을 넣어 문단을 짧고 깔끔하게 쪼개어 가독성을 극대화해 주십시오.
- [포스팅 하단 태그 삽입] 모든 버전의 본문 가장 최하단(본문 및 퀴즈 내용이 완전히 끝난 후)에는 해당 포스팅 내용과 관련이 깊은 핵심 단어들을 해시태그 형식(예: #청소년지도사 #청소년복지론 등)으로 5~10개 반드시 첨부하십시오.

[요청 주제/키워드]
{content}

[온라인 검색 참고 자료]
{online_context if online_context else "자체 지식을 활용해 상세히 작성하세요"}

[출력 요구사항 및 포맷]
반드시 다음 구분자(Delimiter)를 정확히 사용하여 각각 다른 스타일로 작성하세요.

========== WORDPRESS VERSION ==========
# [워드프레스용 제목]
(본문은 아주 따뜻하고 친근하며 다정한 어조로 작성해 주세요. 불릿 포인트나 정리 표 등을 통해 상세히 설명해 주세요. 마크다운 예시 기호 # 나 bold 기호 ** 는 제거하고 줄바꿈과 텍스트 위주로 작성하세요. 본문과 퀴즈 사이에 빈칸 줄바꿈(엔터)을 2회 이상 넣고, "[이곳에 학습 퀴즈 관련 이미지가 들어갈 자리입니다]" 라는 안내 문구를 가독성 있게 표기하여 확실하게 물리적인 간격을 넓혀 주세요. 그 후 공부한 내용을 점검할 수 있도록 4지선다형 객관식 퀴즈 1문항과 정답 및 해설을 추가해 주세요. 마지막에 독자들을 응원하는 다정한 멘트와 해시태그를 작성해 주세요.)

========== BLOGGER VERSION ==========
# [블로거용 제목]
(본문은 담담하고 핵심 중심의 간결하며 정돈된 전문적인 어조로 작성해 주세요. 핵심 본문은 표(Table) 또는 구조화된 도표 형식을 적극 활용하여 한눈에 정리되게 작성해 주시고, 마크다운 기호 # 나 ** 는 제거하고 핵심만 빠르게 읽을 수 있도록 요약해 주세요. 본문과 퀴즈 사이에 빈칸 줄바꿈(엔터)을 2회 이상 넣고, "[이곳에 학습 퀴즈 관련 이미지가 들어갈 자리입니다]" 라는 안내 문구를 가독성 있게 표기하여 확실하게 물리적인 간격을 넓혀 주세요. 그 후 공부한 내용을 직관적으로 점검할 수 있도록 O/X 퀴즈 2문항과 각각의 정답 및 해설을 추가해 주세요. 마지막에 해시태그를 추가해 주세요.)
"""
        elif category == "mindset":
            prompt = f"""당신은 마음 치유 및 심리 전문 블로거입니다.
아래 키워드와 참고자료를 바탕으로 워드프레스와 구글 블로거에 각각 업로드할 두 가지 버전의 글을 작성하세요.

[중요 지시사항]
- [가독성 극대화 지시사항] 모든 본문 문장은 가로로 너무 길게 이어지지 않도록 하십시오. 의미 단위 또는 약 1~2개 문장마다 적절히 빈칸 줄바꿈(엔터)을 넣어 문단을 짧고 깔끔하게 쪼개어 가독성을 극대화해 주십시오.
- [포스팅 하단 태그 삽입] 모든 버전의 본문 가장 최하단(응원 멘트나 본문 내용이 완전히 끝난 후)에는 해당 포스팅 내용과 관련이 깊은 핵심 단어들을 해시태그 형식(예: #마인드셋 #심리테라피 등)으로 5~10개 반드시 첨부하십시오.

[요청 주제/키워드]
{content}

[온라인 검색 참고 자료]
{online_context if online_context else "자체 지식을 활용해 상세히 작성하세요"}

[출력 요구사항 및 포맷]
반드시 다음 구분자(Delimiter)를 정확히 사용하여 각각 다른 스타일로 작성하세요.

========== WORDPRESS VERSION ==========
# [워드프레스용 제목]
(본문은 따뜻하고 위로가 되는 친근한 어조로 작성해 주세요. 마지막에 해시태그를 추가해 주세요.)

========== BLOGGER VERSION ==========
# [블로거용 제목]
(본문은 정돈되고 전문적인 에세이 톤으로 작성해 주세요. 마지막에 해시태그를 추가해 주세요.)
"""
        elif category == "recipe":
            prompt = f"""당신은 요리 및 집밥 전문 파워 블로거입니다.
아래 제공된 정보 및 레시피 키워드를 바탕으로 워드프레스(WordPress)와 구글 블로거(Blogger)에 각각 업로드할 두 가지 버전의 글을 작성하세요.

[중요 지시사항]
1. 두 블로그는 완전히 다른 독자층을 대상으로 독립적으로 운영되므로, 두 버전의 문체와 내용 구성이 완전히 다르게(차별화되게) 작성되어야 합니다. 동일한 내용을 단순히 다듬기만 한 형태여서는 안 됩니다.
2. 한 블로그 내용에 여러 요리를 함께 나열하지 마십시오. 반드시 제시된 주제/키워드 중 단 '하나'의 요리(단일 요리)만을 선정하여 그 요리 하나만 깊고 상세하게 설명해야 합니다. (여러 요리나 다른 반찬 정보가 입력값에 섞여 있더라도, 단 하나의 핵심 요리만 집중적으로 파고드십시오.)
3. 본문 내에 절대로 '자가진단', '퀴즈', '자가진단 QUIZ' 또는 학습용 질문/평가 문제를 포함하지 마십시오.
4. [가독성 극대화 지시사항] 모든 본문 문장은 가로로 너무 길게 이어지지 않도록 하십시오. 의미 단위 또는 약 1~2개 문장마다 적절히 빈칸 줄바꿈(엔터)을 넣어 문단을 짧고 깔끔하게 쪼개어 가독성을 극대화해 주십시오.
5. [포스팅 하단 태그 삽입] 모든 버전의 본문 가장 최하단(본문 내용이 완전히 끝난 후)에는 해당 요리 레시피와 관련이 깊은 핵심 단어들을 해시태그 형식(예: #요리레시피 #집밥반찬 등)으로 5~10개 반드시 첨부하십시오.

[요청 주제/키워드]
{content}

[온라인 검색 참고 자료]
{online_context if online_context else "자체 지식을 활용해 상세히 작성하세요"}

[출력 요구사항 및 포맷]
반드시 다음 구분자(Delimiter)를 정확히 사용하여 각각 다른 스타일로 작성하세요.

========== WORDPRESS VERSION ==========
# [워드프레스용 제목]
(본문은 이웃집 다정한 이웃이 본인의 일상 이야기나 가족과의 추억, 요리하는 과정에서 느낀 소소한 감정을 털어놓는 듯한 '친근하고 따뜻한 스토리텔링 어조'로 작성해 주세요. 요리에 담긴 사연이나 요리할 때 집안에 풍기는 냄새, 맛에 대한 묘사 등 풍성한 이야기 중심의 글이어야 합니다. 요리 순서도 딱딱한 개조식이 아니라 자연스럽게 이야기하듯 풀어내어 정겨움을 주도록 작성하세요. 마지막에 해시태그를 추가해 주세요.)

========== BLOGGER VERSION ==========
# [블로거용 제목]
(본문은 깔끔하고 명확하며 군더더기 없는 '구조적이고 전문적인 레시피 카드 어조'로 작성해 주세요. 불필요한 일상 이야기나 감정 묘사는 일체 배제하고, 필요한 재료 목록(정량 표기 포함)을 표(Table) 또는 명확한 리스트 형식으로 정리해 제시하십시오. 조리 단계(Step-by-step)를 시간순으로 명확하고 간결하게 기입하고, 불을 다룰 때의 주의점이나 맛을 더하는 비법 팁을 객관적인 어조로 정리해 주십시오. 마크다운 기호 # 나 ** 는 제거하여 가독성을 높여 주시고 마지막에 해시태그를 추가해 주세요.)
"""
        else:
            prompt = content

        # Load Config
        cfg = load_config()
        ollama_url = cfg.get("OLLAMA_URL", "http://127.0.0.1:11434")
        model = cfg.get("MODEL", "llama3.2:1b")
        
        # Call LLM
        gemini_api_key = ""
        ac_path = os.path.join(HERE, "blog_account.json")
        if os.path.exists(ac_path):
            try:
                with open(ac_path, "r", encoding="utf-8") as ac_f:
                    ac_cfg = json.load(ac_f)
                    gemini_api_key = ac_cfg.get("GEMINI_API_KEY", "").strip()
            except Exception:
                pass
        result = ask_llm(ollama_url, model, prompt, gemini_api_key)
        if not result:
            print("[ERROR] Failed to generate content from LLM.")
            sys.exit(1)
            
        # Save draft
        category_dir = os.path.join(DRAFTS_ROOT, category)
        os.makedirs(category_dir, exist_ok=True)
        
        timestamp = int(time.time())
        filename = f"blog_draft_{timestamp}.md"
        filepath = os.path.join(category_dir, filename)
        
        try:
            with open(filepath, "w", encoding="utf-8") as f:
                f.write(f"# 📝 블로그 포스팅 초안 ({category.upper()})\n\n")
                f.write(result)
            print(f"[SUCCESS] Blog post draft written to: {filepath}")
        except Exception as e:
            print(f"[ERROR] Failed to save draft file: {e}")
            sys.exit(1)

        # Save queue progress if auto mode
        if auto_mode:
            print("[INFO] Draft created. Auto-publishing now...")
            urls = auto_publish_post(result, category, current_subject, target_file_name)
            wp_url = urls.get("wp_url", "")
            blogger_url = urls.get("blogger_url", "")
            today_str = time.strftime("%Y-%m-%d")
            completed_entry = {
                "subject": current_subject,
                "lesson": target_file_name,
                "date": today_str,
                "draft_path": os.path.abspath(filepath),
                "status": "published" if (wp_url or blogger_url) else "draft",
                "url": wp_url or blogger_url,
                "wp_url": wp_url,
                "blogger_url": blogger_url
            }
            if "completed_lessons" not in queue_data:
                queue_data["completed_lessons"] = []
            queue_data["completed_lessons"].append(completed_entry)

            # Update memory.md
            memory_path = os.path.join(HERE, "..", "memory.md")
            if os.path.exists(memory_path):
                try:
                    with open(memory_path, "r", encoding="utf-8") as mem_f:
                        mem_lines = mem_f.read().splitlines()
                    insert_idx = -1
                    for idx_l, line in enumerate(mem_lines):
                        if "## 최근 소식 & 히스토리" in line:
                            insert_idx = idx_l + 1
                            break
                    status_text = "발행 완료" if (wp_url or blogger_url) else "초안 작성"
                    log_line = f"- [{today_str}] {current_subject} - {target_file_name} {status_text} (WordPress: {wp_url or '실패'}, Blogger: {blogger_url or '실패'})"
                    if insert_idx != -1:
                        mem_lines.insert(insert_idx, log_line)
                    else:
                        mem_lines.append(log_line)
                    with open(memory_path, "w", encoding="utf-8") as mem_f:
                        mem_f.write("\n".join(mem_lines) + "\n")
                    print(f"[SUCCESS] Updated blog memory.md with publishing status.")
                except Exception as mem_err:
                    print(f"[WARN] Failed to update memory.md: {mem_err}")

            next_idx = current_idx + 1
            if next_idx >= len(files):
                # Completed this subject!
                completed_history.append(current_subject)
                if subj_queue:
                    next_subject = subj_queue.pop(0)
                    queue_data["current_subject"] = next_subject
                    queue_data["current_lesson_index"] = 0
                    queue_data["queue"] = subj_queue
                    queue_data["completed_history"] = completed_history
                    print(f"\n🎉 [과목 완료] '{current_subject}' 과목의 모든 회차가 완료되었습니다!")
                    print(f"👉 다음 과목 '{next_subject}' 발행을 대기열에서 꺼내어 준비합니다.")
                else:
                    queue_data["current_subject"] = ""
                    queue_data["current_lesson_index"] = 0
                    queue_data["queue"] = []
                    queue_data["completed_history"] = completed_history
                    print(f"\n🎉 [대기열 최종 완료] 모든 대기열 과목('{current_subject}')의 발행이 최종 완료되었습니다!")
                    print("👉 다음 과목을 대기열에 추가해 주세요.")
            else:
                queue_data["current_lesson_index"] = next_idx
                next_file = files[next_idx]
                print(f"\n📆 [초안 작성 완료] '{current_subject}' 과목의 {current_idx + 1}번째 차시 초안 생성이 완료되었습니다. (다음 예정: {next_file})")
                
            with open(queue_path, "w", encoding="utf-8") as f:
                json.dump(queue_data, f, indent=2, ensure_ascii=False)
    else:
        # Standard mode fallback
        current_subject = category
        target_file_name = os.path.basename(input_arg)
        if os.path.exists(input_arg):
            with open(input_arg, "r", encoding="utf-8") as f:
                content = f.read()
        else:
            content = input_arg
            
        # Standardize content
        circle_map = {
            '\u2460': '1.', '\u2461': '2.', '\u2462': '3.', '\u2463': '4.', '\u2464': '5.',
            '\u2465': '6.', '\u2466': '7.', '\u2467': '8.', '\u2468': '9.', '\u2469': '10.'
        }
        for circ, rep in circle_map.items():
            content = content.replace(circ, rep)
        content = re.sub(r'#+', ' ', content)

        # Search online context and run LLM
        online_context = fetch_online_context(category)
        
        prompt = ""
        if category == "study":
            prompt = f"""당신은 자격증 시험 전문 교육 블로거입니다.
아래 제공된 '청소년지도사' 관련 학습 텍스트 및 온라인 검색 참고자료를 바탕으로 워드프레스와 구글 블로거에 각각 업로드할 두 가지 버전의 글을 작성하세요.

[중요 지시사항]
- 반드시 처음부터 끝까지 완전하고 완벽한 '한국어'로만 작성하십시오.
- 영어(sớm, also, juga 등), 베트남어, 태국어 등 외래어 토큰이나 타국어 단어가 단 한 단어도 섞여서는 안 됩니다. 
- 한자(漢字) 역시 가급적 한글로 순화하고 한글로만 작성하십시오.
- AI 임의의 다국어 번역 혼동이나 깨진 토큰 사용을 철저히 금지합니다.
- [가독성 극대화 지시사항] 모든 본문 문장은 가로로 너무 길게 이어지지 않도록 하십시오. 의미 단위 또는 약 1~2개 문장마다 적절히 빈칸 줄바꿈(엔터)을 넣어 문단을 짧고 깔끔하게 쪼개어 가독성을 극대화해 주십시오.
- [포스팅 하단 태그 삽입] 모든 버전의 본문 가장 최하단(본문 및 퀴즈 내용이 완전히 끝난 후)에는 해당 포스팅 내용과 관련이 깊은 핵심 단어들을 해시태그 형식(예: #청소년지도사 #청소년복지론 등)으로 5~10개 반드시 첨부하십시오.

[요청 주제/키워드]
{content}

[온라인 검색 참고 자료]
{online_context if online_context else "자체 지식을 활용해 상세히 작성하세요"}

[출력 요구사항 및 포맷]
반드시 다음 구분자(Delimiter)를 정확히 사용하여 각각 다른 스타일로 작성하세요.

========== WORDPRESS VERSION ==========
# [워드프레스용 제목]
(본문은 아주 따뜻하고 친근하며 다정한 어조로 작성해 주세요. 불릿 포인트나 정리 표 등을 통해 상세히 설명해 주세요. 마크다운 예시 기호 # 나 bold 기호 ** 는 제거하고 줄바꿈과 텍스트 위주로 작성하세요. 본문과 퀴즈 사이에 빈칸 줄바꿈(엔터)을 2회 이상 넣고, "[이곳에 학습 퀴즈 관련 이미지가 들어갈 자리입니다]" 라는 안내 문구를 가독성 있게 표기하여 확실하게 물리적인 간격을 넓혀 주세요. 그 후 공부한 내용을 점검할 수 있도록 4지선다형 객관식 퀴즈 1문항과 정답 및 해설을 추가해 주세요. 마지막에 독자들을 응원하는 다정한 멘트와 해시태그를 작성해 주세요.)

========== BLOGGER VERSION ==========
# [블로거용 제목]
(본문은 담담하고 핵심 중심의 간결하며 정돈된 전문적인 어조로 작성해 주세요. 핵심 본문은 표(Table) 또는 구조화된 도표 형식을 적극 활용하여 한눈에 정리되게 작성해 주시고, 마크다운 기호 # 나 ** 는 제거하고 핵심만 빠르게 읽을 수 있도록 요약해 주세요. 본문과 퀴즈 사이에 빈칸 줄바꿈(엔터)을 2회 이상 넣고, "[이곳에 학습 퀴즈 관련 이미지가 들어갈 자리입니다]" 라는 안내 문구를 가독성 있게 표기하여 확실하게 물리적인 간격을 넓혀 주세요. 그 후 공부한 내용을 직관적으로 점검할 수 있도록 O/X 퀴즈 2문항과 각각의 정답 및 해설을 추가해 주세요. 마지막에 해시태그를 추가해 주세요.)
"""
        elif category == "mindset":
            prompt = f"""당신은 마음 치유 및 심리 전문 블로거입니다.
아래 키워드와 참고자료를 바탕으로 워드프레스와 구글 블로거에 각각 업로드할 두 가지 버전의 글을 작성하세요.

[중요 지시사항]
- [가독성 극대화 지시사항] 모든 본문 문장은 가로로 너무 길게 이어지지 않도록 하십시오. 의미 단위 또는 약 1~2개 문장마다 적절히 빈칸 줄바꿈(엔터)을 넣어 문단을 짧고 깔끔하게 쪼개어 가독성을 극대화해 주십시오.
- [포스팅 하단 태그 삽입] 모든 버전의 본문 가장 최하단(응원 멘트나 본문 내용이 완전히 끝난 후)에는 해당 포스팅 내용과 관련이 깊은 핵심 단어들을 해시태그 형식(예: #마인드셋 #심리테라피 등)으로 5~10개 반드시 첨부하십시오.

[요청 주제/키워드]
{content}

[온라인 검색 참고 자료]
{online_context if online_context else "자체 지식을 활용해 상세히 작성하세요"}

[출력 요구사항 및 포맷]
반드시 다음 구분자(Delimiter)를 정확히 사용하여 각각 다른 스타일로 작성하세요.

========== WORDPRESS VERSION ==========
# [워드프레스용 제목]
(본문은 따뜻하고 위로가 되는 친근한 어조로 작성해 주세요. 마지막에 해시태그를 추가해 주세요.)

========== BLOGGER VERSION ==========
# [블로거용 제목]
(본문은 정돈되고 전문적인 에세이 톤으로 작성해 주세요. 마지막에 해시태그를 추가해 주세요.)
"""
        elif category == "recipe":
            prompt = f"""당신은 요리 및 집밥 전문 파워 블로거입니다.
아래 제공된 정보 및 레시피 키워드를 바탕으로 워드프레스(WordPress)와 구글 블로거(Blogger)에 각각 업로드할 두 가지 버전의 글을 작성하세요.

[중요 지시사항]
1. 두 블로그는 완전히 다른 독자층을 대상으로 독립적으로 운영되므로, 두 버전의 문체와 내용 구성이 완전히 다르게(차별화되게) 작성되어야 합니다. 동일한 내용을 단순히 다듬기만 한 형태여서는 안 됩니다.
2. 한 블로그 내용에 여러 요리를 함께 나열하지 마십시오. 반드시 제시된 주제/키워드 중 단 '하나'의 요리(단일 요리)만을 선정하여 그 요리 하나만 깊고 상세하게 설명해야 합니다. (여러 요리나 다른 반찬 정보가 입력값에 섞여 있더라도, 단 하나의 핵심 요리만 집중적으로 파고드십시오.)
3. 본문 내에 절대로 '자가진단', '퀴즈', '자가진단 QUIZ' 또는 학습용 질문/평가 문제를 포함하지 마십시오.
4. [가독성 극대화 지시사항] 모든 본문 문장은 가로로 너무 길게 이어지지 않도록 하십시오. 의미 단위 또는 약 1~2개 문장마다 적절히 빈칸 줄바꿈(엔터)을 넣어 문단을 짧고 깔끔하게 쪼개어 가독성을 극대화해 주십시오.
5. [포스팅 하단 태그 삽입] 모든 버전의 본문 가장 최하단(본문 내용이 완전히 끝난 후)에는 해당 요리 레시피와 관련이 깊은 핵심 단어들을 해시태그 형식(예: #요리레시피 #집밥반찬 등)으로 5~10개 반드시 첨부하십시오.

[요청 주제/키워드]
{content}

[온라인 검색 참고 자료]
{online_context if online_context else "자체 지식을 활용해 상세히 작성하세요"}

[출력 요구사항 및 포맷]
반드시 다음 구분자(Delimiter)를 정확히 사용하여 각각 다른 스타일로 작성하세요.

========== WORDPRESS VERSION ==========
# [워드프레스용 제목]
(본문은 이웃집 다정한 이웃이 본인의 일상 이야기나 가족과의 추억, 요리하는 과정에서 느낀 소소한 감정을 털어놓는 듯한 '친근하고 따뜻한 스토리텔링 어조'로 작성해 주세요. 요리에 담긴 사연이나 요리할 때 집안에 풍기는 냄새, 맛에 대한 묘사 등 풍성한 이야기 중심의 글이어야 합니다. 요리 순서도 딱딱한 개조식이 아니라 자연스럽게 이야기하듯 풀어내어 정겨움을 주도록 작성하세요. 마지막에 해시태그를 추가해 주세요.)

========== BLOGGER VERSION ==========
# [블로거용 제목]
(본문은 깔끔하고 명확하며 군더더기 없는 '구조적이고 전문적인 레시피 카드 어조'로 작성해 주세요. 불필요한 일상 이야기나 감정 묘사는 일체 배제하고, 필요한 재료 목록(정량 표기 포함)을 표(Table) 또는 명확한 리스트 형식으로 정리해 제시하십시오. 조리 단계(Step-by-step)를 시간순으로 명확하고 간결하게 기입하고, 불을 다룰 때의 주의점이나 맛을 더하는 비법 팁을 객관적인 어조로 정리해 주십시오. 마크다운 기호 # 나 ** 는 제거하여 가독성을 높여 주시고 마지막에 해시태그를 추가해 주세요.)
"""
        else:
            prompt = content

        # Load Config
        cfg = load_config()
        ollama_url = cfg.get("OLLAMA_URL", "http://127.0.0.1:11434")
        model = cfg.get("MODEL", "llama3.2:1b")
        
        # Call LLM
        gemini_api_key = ""
        ac_path = os.path.join(HERE, "blog_account.json")
        if os.path.exists(ac_path):
            try:
                with open(ac_path, "r", encoding="utf-8") as ac_f:
                    ac_cfg = json.load(ac_f)
                    gemini_api_key = ac_cfg.get("GEMINI_API_KEY", "").strip()
            except Exception:
                pass
        result = ask_llm(ollama_url, model, prompt, gemini_api_key)
        if not result:
            print("[ERROR] Failed to generate content from LLM.")
            sys.exit(1)
            
        # Save draft
        category_dir = os.path.join(DRAFTS_ROOT, category)
        os.makedirs(category_dir, exist_ok=True)
        
        timestamp = int(time.time())
        filename = f"blog_draft_{timestamp}.md"
        filepath = os.path.join(category_dir, filename)
        
        try:
            with open(filepath, "w", encoding="utf-8") as f:
                f.write(f"# 📝 블로그 포스팅 초안 ({category.upper()})\n\n")
                f.write(result)
            print(f"[SUCCESS] Blog post draft written to: {filepath}")

            # Update memory.md
            memory_path = os.path.join(HERE, "..", "memory.md")
            if os.path.exists(memory_path):
                try:
                    with open(memory_path, "r", encoding="utf-8") as mem_f:
                        mem_lines = mem_f.read().splitlines()
                    insert_idx = -1
                    for idx_l, line in enumerate(mem_lines):
                        if "## 최근 소식 & 히스토리" in line:
                            insert_idx = idx_l + 1
                            break
                    today_str = time.strftime("%Y-%m-%d")
                    log_line = f"- [{today_str}] 수동 블로그 초안 생성 완료 ({category.upper()} - {target_file_name})"
                    if insert_idx != -1:
                        mem_lines.insert(insert_idx, log_line)
                    else:
                        mem_lines.append(log_line)
                    with open(memory_path, "w", encoding="utf-8") as mem_f:
                        mem_f.write("\n".join(mem_lines) + "\n")
                    print(f"[SUCCESS] Updated blog memory.md with manual draft status.")
                except Exception as mem_err:
                    print(f"[WARN] Failed to update memory.md: {mem_err}")
        except Exception as e:
            print(f"[ERROR] Failed to save draft file: {e}")
            sys.exit(1)


if __name__ == "__main__":
    main()
