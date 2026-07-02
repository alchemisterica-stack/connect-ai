#!/usr/bin/env python3
import os
import json
import sys
import time
import socket
socket.setdefaulttimeout(30) # 전역 네트워크 타임아웃을 30초로 제한하여 무한 대기 방지

if sys.platform.startswith('win'):
    import io
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')
    sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding='utf-8', errors='replace')


sys.path.append(r"C:\Users\User\my-ai-office\scripts")
try:
    import automation_utils
except ImportError:
    automation_utils = None

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

def load_trending_study_keywords():
    report_path = r"C:\Users\User\my-ai-office\_company\sessions\latest_trend_report.md"
    keywords = ["청소년지도사", "사회복지사", "독학합격", "공부계획", "학습팁"]
    if os.path.exists(report_path):
        try:
            with open(report_path, "r", encoding="utf-8") as f:
                content = f.read()
            study_sec = re.search(r'### 1\. \[학습/자격증\](.*?)###', content, re.DOTALL)
            if not study_sec:
                study_sec = re.search(r'### 1\. \[학습/자격증\](.*?)##', content, re.DOTALL)
            if study_sec:
                found_kws = re.findall(r'-\s+\*\*([^*]+?)\*\*:\s*(.*)', study_sec.group(1))
                if found_kws:
                    kws = [fk[1].strip() for fk in found_kws]
                    kws = [k for k in kws if k]
                    processed = []
                    for kw in kws:
                        clean_kw = re.sub(r'[^\uac00-\ud7a3\w]', '', kw)
                        if clean_kw:
                            processed.append(clean_kw)
                    if processed:
                        keywords.extend(processed)
        except Exception as e:
            print(f"[WARN] Failed to load trending study keywords: {e}")
    seen = set()
    return [x for x in keywords if not (x in seen or seen.add(x))][:8]

def markdown_to_html_for_blogger(md_text, is_blogger=True):
    import re
    
    html = md_text
    
    # 1. Parse Blockquotes
    lines = html.split('\n')
    in_blockquote = False
    new_lines = []
    blockquote_lines = []
    
    for line in lines:
        if line.strip().startswith('>'):
            in_blockquote = True
            content = line.strip()[1:].strip()
            blockquote_lines.append(content)
        else:
            if in_blockquote:
                bq_content = '<br>'.join(blockquote_lines)
                if is_blogger:
                    bq_html = (
                        f'<blockquote style="border-left: 4px solid #f59e0b; '
                        f'padding: 16px 20px; margin: 24px 0; background-color: #fffbeb; '
                        f'color: #7c2d12; border-radius: 8px; font-size: 0.95em; line-height: 1.7; '
                        f'font-family: \'Apple SD Gothic Neo\', \'Malgun Gothic\', sans-serif;">'
                        f'{bq_content}</blockquote>'
                    )
                else:
                    bq_html = (
                        f'<blockquote style="border-left: 4px solid #3b82f6; '
                        f'padding: 16px 20px; margin: 24px 0; background-color: #eff6ff; '
                        f'color: #1e3a8a; border-radius: 6px; font-size: 0.98em; line-height: 1.7; '
                        f'font-family: Batang, Georgia, serif;">'
                        f'{bq_content}</blockquote>'
                    )
                new_lines.append(bq_html)
                blockquote_lines = []
                in_blockquote = False
            new_lines.append(line)
            
    if in_blockquote:
        bq_content = '<br>'.join(blockquote_lines)
        if is_blogger:
            bq_html = (
                f'<blockquote style="border-left: 4px solid #f59e0b; '
                f'padding: 16px 20px; margin: 24px 0; background-color: #fffbeb; '
                f'color: #7c2d12; border-radius: 8px; font-size: 0.95em; line-height: 1.7; '
                f'font-family: \'Apple SD Gothic Neo\', \'Malgun Gothic\', sans-serif;">'
                f'{bq_content}</blockquote>'
            )
        else:
            bq_html = (
                f'<blockquote style="border-left: 4px solid #3b82f6; '
                f'padding: 16px 20px; margin: 24px 0; background-color: #eff6ff; '
                f'color: #1e3a8a; border-radius: 6px; font-size: 0.98em; line-height: 1.7; '
                f'font-family: Batang, Georgia, serif;">'
                f'{bq_content}</blockquote>'
            )
        new_lines.append(bq_html)
        
    html = '\n'.join(new_lines)
    
    # 2. Headings
    if is_blogger:
        def replace_h3_blogger(match):
            title = match.group(1).strip()
            return (
                f'<h3 style="font-size: 1.25em; color: #7c2d12; margin-top: 28px; '
                f'margin-bottom: 14px; font-weight: bold; border-left: 4px solid #b45309; '
                f'padding-left: 12px; line-height: 1.4; font-family: \'Apple SD Gothic Neo\', \'Malgun Gothic\', sans-serif;">{title}</h3>'
            )
        html = re.sub(r'^###\s+(.*)$', replace_h3_blogger, html, flags=re.MULTILINE)
        
        def replace_h2_blogger(match):
            title = match.group(1).strip()
            return (
                f'<h2 style="font-size: 1.45em; color: #431407; margin-top: 36px; '
                f'margin-bottom: 18px; font-weight: bold; border-bottom: 2px solid #fed7aa; '
                f'padding-bottom: 8px; line-height: 1.4; font-family: \'Apple SD Gothic Neo\', \'Malgun Gothic\', sans-serif;">{title}</h2>'
            )
        html = re.sub(r'^##\s+(.*)$', replace_h2_blogger, html, flags=re.MULTILINE)
        
        def replace_h1_blogger(match):
            title = match.group(1).strip()
            return (
                f'<h1 style="font-size: 1.8em; color: #431407; margin-top: 40px; '
                f'margin-bottom: 22px; font-weight: bold; line-height: 1.3; font-family: \'Apple SD Gothic Neo\', \'Malgun Gothic\', sans-serif;">{title}</h1>'
            )
        html = re.sub(r'^#\s+(.*)$', replace_h1_blogger, html, flags=re.MULTILINE)
    else:
        # WordPress - Blue-gray elegant editorial look
        def replace_h3_wp(match):
            title = match.group(1).strip()
            return (
                f'<h3 style="font-size: 1.25em; color: #1e3a8a; margin-top: 28px; '
                f'margin-bottom: 14px; font-weight: bold; border-left: 4px solid #3b82f6; '
                f'padding-left: 12px; line-height: 1.4; font-family: Batang, Georgia, serif;">{title}</h3>'
            )
        html = re.sub(r'^###\s+(.*)$', replace_h3_wp, html, flags=re.MULTILINE)
        
        def replace_h2_wp(match):
            title = match.group(1).strip()
            return (
                f'<h2 style="font-size: 1.45em; color: #0f172a; margin-top: 36px; '
                f'margin-bottom: 18px; font-weight: bold; border-bottom: 2px solid #bfdbfe; '
                f'padding-bottom: 8px; line-height: 1.4; font-family: Batang, Georgia, serif;">{title}</h2>'
            )
        html = re.sub(r'^##\s+(.*)$', replace_h2_wp, html, flags=re.MULTILINE)
        
        def replace_h1_wp(match):
            title = match.group(1).strip()
            return (
                f'<h1 style="font-size: 1.8em; color: #0f172a; margin-top: 40px; '
                f'margin-bottom: 22px; font-weight: bold; line-height: 1.3; font-family: Batang, Georgia, serif;">{title}</h1>'
            )
        html = re.sub(r'^#\s+(.*)$', replace_h1_wp, html, flags=re.MULTILINE)

    # 3. Links and Horizontal Rules
    if is_blogger:
        html = re.sub(r'\[(.*?)\]\((.*?)\)', r'<a href="\2" style="color: #b45309; text-decoration: underline;">\1</a>', html)
        html = re.sub(r'^---$', r'<hr style="border: 0; border-top: 1px solid #fed7aa; margin: 28px 0;" />', html, flags=re.MULTILINE)
    else:
        html = re.sub(r'\[(.*?)\]\((.*?)\)', r'<a href="\2" style="color: #2563eb; text-decoration: underline; font-family: Batang, Georgia, serif;">\1</a>', html)
        html = re.sub(r'^---$', r'<hr style="border: 0; border-top: 1px solid #bfdbfe; margin: 28px 0;" />', html, flags=re.MULTILINE)

    # 4. Bold / Strong
    if is_blogger:
        html = re.sub(r'\*\*(.*?)\*\*', r'<strong style="color: #7c2d12; font-weight: bold;">\1</strong>', html)
    else:
        html = re.sub(r'\*\*(.*?)\*\*', r'<strong style="color: #1e3a8a; font-weight: bold; font-family: Batang, Georgia, serif;">\1</strong>', html)
    
    # 5. Lists (Unordered & Ordered)
    lines = html.split('\n')
    in_ul = False
    in_ol = False
    new_lines = []
    
    for line in lines:
        strip_line = line.strip()
        is_ul_item = False
        is_ol_item = False
        
        m_ul = re.match(r'^[\-\*•]\s+(.*)$', strip_line)
        m_ol = re.match(r'^(\d+)\.\s+(.*)$', strip_line)
        
        if m_ul:
            is_ul_item = True
            content = m_ul.group(1).strip()
        elif m_ol:
            is_ol_item = True
            content = m_ol.group(2).strip()
            
        if is_ul_item:
            if in_ol:
                new_lines.append('</ol>')
                in_ol = False
            if not in_ul:
                new_lines.append('<ul style="margin: 12px 0; padding-left: 20px; list-style-type: disc; line-height: 1.7;">')
                in_ul = True
            new_lines.append(f'<li style="margin-bottom: 6px; color: #27272a;">{content}</li>')
        elif is_ol_item:
            if in_ul:
                new_lines.append('</ul>')
                in_ul = False
            if not in_ol:
                new_lines.append('<ol style="margin: 12px 0; padding-left: 20px; list-style-type: decimal; line-height: 1.7;">')
                in_ol = True
            new_lines.append(f'<li style="margin-bottom: 6px; color: #27272a;">{content}</li>')
        else:
            if in_ul:
                new_lines.append('</ul>')
                in_ul = False
            if in_ol:
                new_lines.append('</ol>')
                in_ol = False
            new_lines.append(line)
            
    if in_ul:
        new_lines.append('</ul>')
    if in_ol:
        new_lines.append('</ol>')
        
    html = '\n'.join(new_lines)
    
    # 5. Tables
    lines = html.split('\n')
    in_table = False
    table_lines = []
    new_lines = []
    
    for line in lines:
        strip_line = line.strip()
        if '|' in strip_line:
            if re.match(r'^[\s\|:\-\u2014]+$', strip_line):
                continue
            in_table = True
            table_lines.append(strip_line)
        else:
            if in_table:
                if is_blogger:
                    # Blogger: Modern Card-style Grid Table (With vertical lines, rounded corners, warm borders)
                    table_html = (
                        '<table style="width: 100%; border-collapse: collapse; margin: 24px 0; '
                        'font-size: 0.95em; text-align: left; line-height: 1.6; border: 1px solid #fed7aa; '
                        'font-family: \'Apple SD Gothic Neo\', \'Malgun Gothic\', sans-serif;">'
                    )
                else:
                    # WordPress: Editorial Slate-Blue Grid Table (No vertical lines, clean borders, minimal zebra-striping)
                    table_html = (
                        '<table style="width: 100%; border-collapse: collapse; margin: 24px 0; '
                        'font-size: 0.95em; text-align: left; line-height: 1.6; '
                        'font-family: Batang, Georgia, serif;">'
                    )
                for idx, tline in enumerate(table_lines):
                    cells = [c.strip() for c in tline.split('|') if c.strip() or tline.startswith('|') or tline.endswith('|')]
                    if len(cells) > 0:
                        if is_blogger:
                            tr_style = "border-bottom: 1px solid #fed7aa;"
                            if idx == 0:
                                tr_html = f'<tr style="background-color: #ffedd5; color: #7c2d12; font-weight: bold; {tr_style}">'
                                for cell in cells:
                                    tr_html += f'<th style="padding: 12px 14px; border: 1px solid #fed7aa; text-align: center;">{cell}</th>'
                                tr_html += '</tr>'
                            else:
                                bg_color = "#fffdfa" if idx % 2 == 1 else "#ffffff"
                                tr_html = f'<tr style="background-color: {bg_color}; {tr_style}">'
                                for cell in cells:
                                    tr_html += f'<td style="padding: 11px 13px; border: 1px solid #fed7aa; color: #27272a;">{cell}</td>'
                                tr_html += '</tr>'
                        else:
                            # WordPress: Clean blue-gray editorial table with Batang font, no vertical borders
                            if idx == 0:
                                tr_html = f'<tr style="background-color: #eff6ff; color: #1e3a8a; font-weight: bold; border-top: 2px solid #3b82f6; border-bottom: 2px solid #3b82f6;">'
                                for cell in cells:
                                    tr_html += f'<th style="padding: 12px 14px; font-family: Batang, Georgia, serif; text-align: center;">{cell}</th>'
                                tr_html += '</tr>'
                            else:
                                bg_color = "#f8fafc" if idx % 2 == 1 else "#ffffff"
                                tr_html = f'<tr style="background-color: {bg_color}; border-bottom: 1px solid #e2e8f0;">'
                                for cell in cells:
                                    tr_html += f'<td style="padding: 10px 12px; color: #334155; font-family: Batang, Georgia, serif;">{cell}</td>'
                                tr_html += '</tr>'
                        table_html += tr_html
                table_html += '</table>'
                new_lines.append(table_html)
                table_lines = []
                in_table = False
            new_lines.append(line)
            
    if in_table:
        if is_blogger:
            table_html = (
                '<table style="width: 100%; border-collapse: collapse; margin: 24px 0; '
                'font-size: 0.95em; text-align: left; line-height: 1.6; border: 1px solid #fed7aa; '
                'font-family: \'Apple SD Gothic Neo\', \'Malgun Gothic\', sans-serif;">'
            )
        else:
            table_html = (
                '<table style="width: 100%; border-collapse: collapse; margin: 24px 0; '
                'font-size: 0.95em; text-align: left; line-height: 1.6; '
                'font-family: Batang, Georgia, serif;">'
            )
        for idx, tline in enumerate(table_lines):
            cells = [c.strip() for c in tline.split('|') if c.strip() or tline.startswith('|') or tline.endswith('|')]
            if len(cells) > 0:
                if is_blogger:
                    tr_style = "border-bottom: 1px solid #fed7aa;"
                    if idx == 0:
                        tr_html = f'<tr style="background-color: #ffedd5; color: #7c2d12; font-weight: bold; {tr_style}">'
                        for cell in cells:
                            tr_html += f'<th style="padding: 12px 14px; border: 1px solid #fed7aa; text-align: center;">{cell}</th>'
                        tr_html += '</tr>'
                    else:
                        bg_color = "#fffdfa" if idx % 2 == 1 else "#ffffff"
                        tr_html = f'<tr style="background-color: {bg_color}; {tr_style}">'
                        for cell in cells:
                            tr_html += f'<td style="padding: 11px 13px; border: 1px solid #fed7aa; color: #27272a;">{cell}</td>'
                        tr_html += '</tr>'
                else:
                    if idx == 0:
                        tr_html = f'<tr style="background-color: #eff6ff; color: #1e3a8a; font-weight: bold; border-top: 2px solid #3b82f6; border-bottom: 2px solid #3b82f6;">'
                        for cell in cells:
                            tr_html += f'<th style="padding: 12px 14px; font-family: Batang, Georgia, serif; text-align: center;">{cell}</th>'
                        tr_html += '</tr>'
                    else:
                        bg_color = "#f8fafc" if idx % 2 == 1 else "#ffffff"
                        tr_html = f'<tr style="background-color: {bg_color}; border-bottom: 1px solid #e2e8f0;">'
                        for cell in cells:
                            tr_html += f'<td style="padding: 10px 12px; color: #334155; font-family: Batang, Georgia, serif;">{cell}</td>'
                        tr_html += '</tr>'
                table_html += tr_html
        table_html += '</table>'
        new_lines.append(table_html)
        
    html = '\n'.join(new_lines)
    
    # 6. Convert newlines to <br> safely (only in non-HTML parts)
    parts = re.split(r'(<[^>]+>)', html)
    for idx in range(len(parts)):
        if idx % 2 == 0:
            parts[idx] = parts[idx].replace('\n', '<br>')
            
    html = ''.join(parts)
    html = re.sub(r'(<br>\s*){3,}', '<br><br>', html)
    
    # Wrap in container with modern fonts, line-height, and slate-gray text color
    if is_blogger:
        return f'<div style="font-family: \'Apple SD Gothic Neo\', \'Malgun Gothic\', sans-serif; font-size: 16px; line-height: 1.8; color: #27272a;">{html}</div>'
    else:
        return f'<div style="font-family: Batang, Georgia, serif; font-size: 16.5px; line-height: 1.85; color: #334155;">{html}</div>'

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
                snow_rng = random.Random(42)
                for _ in range(50):
                    sx = snow_rng.randint(0, width)
                    sy = snow_rng.randint(0, height - 200)
                    sr = snow_rng.randint(2, 5)
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
    import hashlib
    img = None
    try:
        # Select background strictly based on the current day of the week (Monday=0, Tuesday=1, ..., Sunday=6)
        idx = datetime.datetime.now().weekday()
        
        # WordPress gets the realistic photo background, Blogger gets the illustration
        if not is_blogger:
            bg_path = os.path.join(HERE, "assets", f"study_bg_wp_{idx}.png")
        else:
            bg_path = os.path.join(HERE, "assets", f"study_bg_{idx}.png")
            
        if os.path.exists(bg_path):
            orig_img = Image.open(bg_path).convert("RGBA")
            orig_w, orig_h = orig_img.size
            if not is_blogger:
                # --- WordPress Polaroid Editorial Style ---
                img = Image.new("RGBA", (width, height), (250, 249, 246, 255)) # Cream background
                photo_h = 470
                photo_y = 110
                scale = max(width / orig_w, photo_h / orig_h)
                new_w = int(orig_w * scale)
                new_h = int(orig_h * scale)
                photo_img = orig_img.resize((new_w, new_h), Image.Resampling.LANCZOS)
                left = (new_w - width) // 2
                # Custom crop factors for WordPress Study Background illustrations to ensure Y Y-offset is correct
                crop_factors = {
                    0: 0.1,  # Keep top hair Y-offset
                    1: 0.05, # High top-bias to avoid cutting counselor hair
                    2: 0.5,  # Center Y-offset for books
                    3: 0.35, # Centered students at table
                    4: 0.5,  # Center Y-offset for books
                    5: 0.5,  # Center Y-offset for desk/lamp
                    6: 0.2   # Focus on seminar people
                }
                factor = crop_factors.get(idx, 0.5)
                top = int((new_h - photo_h) * factor)
                photo_img = photo_img.crop((left, top, left + width, top + photo_h))
                img.paste(photo_img, (0, photo_y))
            else:
                scale = max(width / orig_w, height / orig_h)
                new_w = int(orig_w * scale)
                new_h = int(orig_h * scale)
                img = orig_img.resize((new_w, new_h), Image.Resampling.LANCZOS)
                left = (new_w - width) // 2
                top = (new_h - height) // 2
                img = img.crop((left, top, left + width, top + height))
            print(f"[SUCCESS] Loaded and aspect-cropped local illustration background: {bg_path}")
        else:
            print(f"[WARN] Local background not found at {bg_path}. Falling back to gradient.")
    except Exception as e:
        print(f"[WARN] Failed to load local background illustration: {e}")
        
    if img is None:
        # Fallback to gradient & shape drawing if local image loading fails
        img = Image.new("RGBA", (width, height), (0, 0, 0, 0))
        if is_blogger:
            PALETTES = [
                ((15, 32, 67), (6, 182, 212)),      # Dark Blue to Cyan
                ((76, 29, 149), (217, 70, 239)),    # Deep Violet to Fuchsia
                ((6, 78, 59), (13, 148, 136)),      # Emerald to Teal
                ((136, 19, 55), (225, 29, 72)),     # Rose to Red
                ((120, 53, 4), (249, 115, 22)),      # Amber to Orange
                ((49, 46, 129), (124, 58, 237)),    # Indigo to Violet
                ((15, 23, 42), (71, 85, 105)),      # Slate to Charcoal
                ((20, 83, 45), (132, 204, 22)),     # Forest Green to Lime
                ((153, 27, 27), (244, 63, 94)),     # Crimson to Coral
                ((8, 47, 73), (134, 25, 143))       # Midnight Blue to Plum
            ]
            h_idx = int(hashlib.md5(title.encode('utf-8')).hexdigest(), 16) % len(PALETTES)
            selected_palette = PALETTES[h_idx]
            
            c1_offset = (random.randint(-15, 15), random.randint(-15, 15), random.randint(-15, 15))
            c2_offset = (random.randint(-15, 15), random.randint(-15, 15), random.randint(-15, 15))
            
            color1 = (max(0, min(255, selected_palette[0][0] + c1_offset[0])),
                      max(0, min(255, selected_palette[0][1] + c1_offset[1])),
                      max(0, min(255, selected_palette[0][2] + c1_offset[2])), 255)
            color2 = (max(0, min(255, selected_palette[1][0] + c2_offset[0])),
                      max(0, min(255, selected_palette[1][1] + c2_offset[1])),
                      max(0, min(255, selected_palette[1][2] + c2_offset[2])), 255)
                
            for y in range(height):
                for x in range(width):
                    factor = (x / width + y / height) / 2
                    r = int(color1[0] + (color2[0] - color1[0]) * factor)
                    g = int(color1[1] + (color2[1] - color1[1]) * factor)
                    b = int(color1[2] + (color2[2] - color1[2]) * factor)
                    img.putpixel((x, y), (r, g, b, 255))
        else:
            img = Image.new("RGBA", (width, height), (250, 249, 246, 255))

    # 3. Load font (Batang Serif for WordPress, Malgun Gothic for Blogger)
    font_path = "C:\\Windows\\Fonts\\batang.ttc" if not is_blogger else "C:\\Windows\\Fonts\\malgun.ttf"
    if not os.path.exists(font_path):
        font_path = "C:\\Windows\\Fonts\\malgun.ttf"
    if not os.path.exists(font_path):
        font_path = "C:\\Windows\\Fonts\\arial.ttf"
        
    try:
        if not is_blogger:
            font_title = ImageFont.truetype(font_path, 34)
            font_subtitle = ImageFont.truetype(font_path, 22)
            font_tag = ImageFont.truetype(font_path, 18)
        else:
            font_title = ImageFont.truetype(font_path, 48)
            font_subtitle = ImageFont.truetype(font_path, 32)
            font_tag = ImageFont.truetype(font_path, 22)
    except Exception:
        font_title = ImageFont.load_default()
        font_subtitle = ImageFont.load_default()
        font_tag = ImageFont.load_default()

    # Clean up subject from forbidden keywords
    clean_subj = subject
    for word in ["청소년지도사 자격증 대비:", "청소년지도사 자격증 대비 :", "청소년지도사자격증대비:", "청소년지도사 자격증 대비", "청소년지도사자격증대비", "청소년지도사", "핵심 요약", "핵심요약"]:
        clean_subj = clean_subj.replace(word, "")
    clean_subj = clean_subj.strip()

    tag_text = f"{clean_subj}"
    footer_text = "congcandy.wordpress.com" if not is_blogger else "congcandy.blogspot.com"
    
    # Split title text
    import re
    title_text = title
    for word in ["청소년지도사 자격증 대비:", "청소년지도사 자격증 대비 :", "청소년지도사자격증대비:", "청소년지도사 자격증 대비", "청소년지도사자격증대비", "청소년지도사", "핵심 요약", "핵심요약"]:
        title_text = title_text.replace(word, "")
    # Remove leading/trailing dashes, colons, spaces
    title_text = re.sub(r'^[\s\-:\s]+', '', title_text)
    title_text = re.sub(r'[\s\-:\s]+$', '', title_text)
    title_text = title_text.strip()
    
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

    if is_blogger:
        # --- Blogger Card Layout Style ---
        card_margin = 60
        card_overlay = Image.new("RGBA", (width, height), (0, 0, 0, 0))
        card_draw = ImageDraw.Draw(card_overlay)
        card_draw.rounded_rectangle(
            [card_margin, card_margin, width - card_margin, height - card_margin],
            radius=24,
            fill=(45, 15, 8, 185),  # Blogger warm dark orange/plum card overlay
            outline=(255, 255, 255, 60),
            width=2
        )
        img = Image.alpha_composite(img, card_overlay)
        draw = ImageDraw.Draw(img)

        # Draw Title text (Centered)
        title_y = height // 2 - 20
        if len(lines) == 1:
            draw.text((width // 2, title_y), lines[0], fill=(255, 255, 255, 255), font=font_title, anchor="mm")
        else:
            draw.text((width // 2, title_y - 35), lines[0], fill=(255, 255, 255, 255), font=font_title, anchor="mm")
            draw.text((width // 2, title_y + 35), lines[1], fill=(255, 255, 255, 255), font=font_title, anchor="mm")

        # Draw footer logo
        draw.text((width // 2, height - card_margin - 60), footer_text, fill=(255, 255, 255, 180), font=font_subtitle, anchor="mm")

    else:
        # --- WordPress Elegant Polaroid Editorial Style ---
        draw = ImageDraw.Draw(img)
        
        # Left aligned margins
        text_x = 60
        text_y_start = 30
        
        # Draw Title text on a single line with left vertical Navy accent bar
        title_y_start = text_y_start + 10
        title_display = title_text
        if len(title_display) > 34:
            title_display = title_display[:34] + "..."
            
        # Draw left vertical accent line (Navy)
        draw.rounded_rectangle(
            [text_x - 15, title_y_start + 2, text_x - 10, title_y_start + 36],
            radius=2,
            fill=(30, 58, 138, 255) # Navy
        )
        
        draw.text(
            (text_x, title_y_start), title_display, 
            fill=(15, 23, 42, 255), font=font_title, anchor="lt"
        )
            
        # Draw footer logo at the bottom right
        draw.text(
            (width - 60, height - 15), footer_text, 
            fill=(71, 85, 105, 255), font=font_subtitle, anchor="rb"
        )
    
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
    import hashlib
    import datetime
    img = None
    try:
        # Select background strictly based on the current day of the week (Monday=0, Tuesday=1, ..., Sunday=6)
        idx = datetime.date.today().weekday()
        if not is_blogger:
            bg_path = os.path.join(HERE, "assets", f"quiz_bg_wp_{idx}.png")
        else:
            bg_path = os.path.join(HERE, "assets", f"quiz_bg_{idx}.png")
        if os.path.exists(bg_path):
            orig_img = Image.open(bg_path).convert("RGBA")
            orig_w, orig_h = orig_img.size
            if not is_blogger:
                # --- WordPress Polaroid Editorial Style ---
                img = Image.new("RGBA", (width, height), (250, 249, 246, 255)) # Cream background
                photo_h = 265
                photo_y = 80
                scale = max(width / orig_w, photo_h / orig_h)
                new_w = int(orig_w * scale)
                new_h = int(orig_h * scale)
                photo_img = orig_img.resize((new_w, new_h), Image.Resampling.LANCZOS)
                left = (new_w - width) // 2
                top = (new_h - photo_h) // 2
                photo_img = photo_img.crop((left, top, left + width, top + photo_h))
                img.paste(photo_img, (0, photo_y))
            else:
                scale = max(width / orig_w, height / orig_h)
                new_w = int(orig_w * scale)
                new_h = int(orig_h * scale)
                img = orig_img.resize((new_w, new_h), Image.Resampling.LANCZOS)
                left = (new_w - width) // 2
                top = (new_h - height) // 2
                img = img.crop((left, top, left + width, top + height))
            print(f"[SUCCESS] Loaded and aspect-cropped local quiz background: {bg_path}")
        else:
            print(f"[WARN] Local quiz background not found at {bg_path}. Falling back to gradient.")
    except Exception as e:
        print(f"[WARN] Failed to load local quiz background: {e}")
        
    if img is None:
        # Fallback to gradient & shape drawing if local image loading fails
        img = Image.new("RGBA", (width, height), (0, 0, 0, 0))
        if is_blogger:
            color1 = (76, 5, 25, 255)     # #4c0519
            color2 = (244, 63, 94, 255)   # #f43f5e
            
            for y in range(height):
                for x in range(width):
                    factor = (x / width + y / height) / 2
                    r = int(color1[0] + (color2[0] - color1[0]) * factor)
                    g = int(color1[1] + (color2[1] - color1[1]) * factor)
                    b = int(color1[2] + (color2[2] - color1[2]) * factor)
                    img.putpixel((x, y), (r, g, b, 255))
        else:
            img = Image.new("RGBA", (width, height), (250, 249, 246, 255))
                
    # Fonts
    font_path = "C:\\Windows\\Fonts\\batang.ttc" if not is_blogger else "C:\\Windows\\Fonts\\malgun.ttf"
    if not os.path.exists(font_path):
        font_path = "C:\\Windows\\Fonts\\malgun.ttf"
    if not os.path.exists(font_path):
        font_path = "C:\\Windows\\Fonts\\arial.ttf"
        
    try:
        if not is_blogger:
            font_title = ImageFont.truetype(font_path, 32)
            font_subtitle = ImageFont.truetype(font_path, 20)
            font_tag = ImageFont.truetype(font_path, 16)
        else:
            font_title = ImageFont.truetype(font_path, 42)
            font_subtitle = ImageFont.truetype(font_path, 22)
            font_tag = ImageFont.truetype(font_path, 18)
    except Exception:
        font_title = ImageFont.load_default()
        font_subtitle = ImageFont.load_default()
        font_tag = ImageFont.load_default()
        
    # Clean up subject from forbidden keywords in quiz banner
    clean_subj = subject
    for word in ["청소년지도사 자격증 대비:", "청소년지도사 자격증 대비 :", "청소년지도사자격증대비:", "청소년지도사 자격증 대비", "청소년지도사자격증대비", "청소년지도사", "핵심 요약", "핵심요약"]:
        clean_subj = clean_subj.replace(word, "")
    clean_subj = clean_subj.strip()
    
    tag_text = f"{clean_subj}"
    footer_text = "congcandy.wordpress.com" if not is_blogger else "congcandy.blogspot.com"

    if is_blogger:
        # --- Blogger Card Layout Style ---
        card_margin = 35
        card_overlay = Image.new("RGBA", (width, height), (0, 0, 0, 0))
        card_draw = ImageDraw.Draw(card_overlay)
        card_draw.rounded_rectangle(
            [card_margin, card_margin, width - card_margin, height - card_margin],
            radius=20,
            fill=(54, 5, 18, 195),  # Blogger warm dark plum card overlay
            outline=(255, 255, 255, 50),
            width=1
        )
        img = Image.alpha_composite(img, card_overlay)
        draw = ImageDraw.Draw(img)

        # Draw Quiz Title and Subtitle (Centered)
        draw.text((width // 2, height // 2), "자가진단 QUIZ", fill=(255, 255, 255, 255), font=font_title, anchor="mm")
        draw.text((width // 2, height // 2 + 50), "문제를 풀며 오늘 배운 핵심 내용을 최종 점검해 보세요!", fill=(255, 255, 255, 200), font=font_subtitle, anchor="mm")
        
        # Draw footer logo
        draw.text((width // 2, height - card_margin - 30), footer_text, fill=(255, 255, 255, 150), font=font_subtitle, anchor="mm")

    else:
        # --- WordPress Elegant Polaroid Style ---
        draw = ImageDraw.Draw(img)
        
        # Left aligned margins
        text_x = 50
        
        # Draw Quiz Title on the right side in Navy color
        draw.text(
            (width - 50, 18), "자가진단 QUIZ", 
            fill=(30, 58, 138, 255), font=font_title, anchor="rt" # Navy
        )
        
        # Draw a separator horizontal line in blue matching H2 bottom border style
        draw.line([(50, 60), (width - 50, 60)], fill=(191, 219, 254, 255), width=2)
        
        # Draw Subtitle on the left
        draw.text(
            (text_x, height - 10), "문제를 풀며 핵심 내용을 점검해 보세요!", 
            fill=(71, 85, 105, 255), font=font_subtitle, anchor="lb"
        )
        
        # Draw footer logo at the bottom right
        draw.text(
            (width - 50, height - 10), footer_text, 
            fill=(71, 85, 105, 255), font=font_subtitle, anchor="rb"
        )

    img.convert("RGB").save(output_path, "PNG")
    print(f"[DYNAMIC QUIZ BANNER] Created quiz banner at: {output_path}")

def embed_images_in_content(content, image_urls, exclude_fin=False):
    if not image_urls:
        return content
    import re
    paragraphs = content.split('\n\n\n')
    new_paragraphs = []
    used_images = set()
    if exclude_fin:
        used_images.add("fin")
    ing_inserted = False
    
    for idx, para in enumerate(paragraphs):
        new_paragraphs.append(para)
        # 1. Embed Ingredient Image: Find list of ingredients or "재료" header
        if not ing_inserted and ("재료" in para or "분량" in para or "| 재료 |" in para or "INGREDIENTS" in para.upper()):
            if "ing" in image_urls:
                img_tag = f'<img src="{image_urls["ing"]}" style="width: 100%; max-width: 600px; height: auto; display: block; margin: 24px auto; border-radius: 8px; box-shadow: 0 4px 6px -1px rgba(0,0,0,0.1), 0 2px 4px -1px rgba(0,0,0,0.06);" alt="재료 준비" />'
                new_paragraphs.append(img_tag)
                ing_inserted = True
                used_images.add("ing")
                
        # 2. Embed Step Images: Look for step indicators in headers or lines
        m_step = re.search(r'(?:\*\*|\b)(?:[sS]tep\s*|조리\s*단계\s*|단계\s*|)?(\d+)(?:\.|\b)', para)
        if m_step:
            step_num = m_step.group(1)
            step_key = f"step{step_num}"
            if step_key in image_urls and step_key not in used_images:
                img_tag = f'<img src="{image_urls[step_key]}" style="width: 100%; max-width: 600px; height: auto; display: block; margin: 20px auto; border-radius: 8px; box-shadow: 0 4px 6px -1px rgba(0,0,0,0.1), 0 2px 4px -1px rgba(0,0,0,0.06);" alt="조리 단계 {step_num}" />'
                new_paragraphs.append(img_tag)
                used_images.add(step_key)
                
    # 3. Embed Finished Image: Place at the very end or right before hashtags
    if "fin" in image_urls and "fin" not in used_images:
        fin_tag = f'<img src="{image_urls["fin"]}" style="width: 100%; max-width: 650px; height: auto; display: block; margin: 28px auto; border-radius: 8px; box-shadow: 0 10px 15px -3px rgba(0,0,0,0.1), 0 4px 6px -2px rgba(0,0,0,0.05);" alt="완성 요리" />'
        if len(new_paragraphs) > 0 and "#" in new_paragraphs[-1]:
            new_paragraphs.insert(len(new_paragraphs) - 1, fin_tag)
        else:
            new_paragraphs.append(fin_tag)
            
    return '\n\n\n'.join(new_paragraphs)


def get_authentic_korean_food_styling_guide(dish_name, is_ingredients, gemini_api_key):
    if not gemini_api_key:
        return ""
    import requests
    url = f"https://generativelanguage.googleapis.com/v1beta/models/gemini-3.1-flash-lite:generateContent?key={gemini_api_key}"
    headers = {"Content-Type": "application/json"}
    
    if is_ingredients:
        prompt = f"""당신은 한식 요리 전문가이자 비주얼 스타일리스트입니다. 네이버 이미지 검색(Naver Image Search)에서 '{dish_name} 재료'를 검색했을 때 나오는 가장 대중적인 한식 식재료의 손질 및 깔끔한 배치 스타일을 분석해 주세요.
이탈리안 파스타나 다른 서양 요리 재료 형태가 아닌, 한국 가정식 및 전문점 조리 전 날것의 재료 배치 형태를 영어 묘사 가이드(약 2~3개 단어구 및 상세 디테일)로 제공해 주세요.
반드시 영어로만 출력하고, 배경이 아닌 오직 '식재료(ingredients)' 자체의 비주얼 표준에 집중하십시오. (예: "raw soybean in a small ceramic bowl, fresh wheat noodles bundled neatly, sliced cucumber on a modern cutting board")"""
    else:
        prompt = f"""당신은 한식 요리 전문가이자 비주얼 스타일리스트입니다. 네이버 이미지 검색(Naver Image Search)에서 '{dish_name} 요리하는법' 및 레시피 결과물 이미지를 검색했을 때 나오는 가장 대중적이고 깔끔한 한국 요리의 플레이팅 형태와 고명 특징을 분석해 주세요.
양식 파스타나 일본식 라멘, 쌀국수 비주얼이 아닌, 정갈한 한국 가정식/전문점 완성본의 고명(고추, 파, 깨, 오이 등), 면발, 국물 색깔/농도를 영어 묘사 가이드(약 2~3개 단어구 및 상세 디테일)로 제공해 주세요.
반드시 영어로만 출력하고, 배경이 아닌 오직 '완성된 음식(finished food)' 자체의 비주얼 표준에 집중하십시오. (예: "Korean cold noodle soup with rich creamy white broth, yellow noodles, topped with a mountain of julienned cucumber, half boiled egg, and toasted sesame seeds, with ice cubes")"""

    payload = {
        "contents": [{"parts": [{"text": prompt}]}]
    }
    try:
        r = requests.post(url, json=payload, headers=headers, timeout=15)
        if r.status_code == 200:
            res = r.json()
            return res["candidates"][0]["content"]["parts"][0]["text"].strip()
    except Exception:
        pass
    return ""


def auto_publish_post(result, category, current_subject, target_file_name, metadata=None):

    import re
    import os
    
    # Clean up previous session's temporary images to prevent reuse bugs
    for temp_img in [
        "temp_wp_banner.png", "temp_blogger_banner.png", 
        "temp_wp_quiz.png", "temp_blogger_quiz.png",
        "temp_wp_ing.png", "temp_wp_fin.png", 
        "temp_blogger_ing.png", "temp_blogger_fin.png"
    ]:
        temp_path = os.path.join(HERE, temp_img)
        if os.path.exists(temp_path):
            try:
                os.remove(temp_path)
                print(f"[INFO] Cleaned up old temporary image: {temp_img}")
            except Exception as clean_err:
                print(f"[WARN] Failed to clean up {temp_img}: {clean_err}")

    # Clean up title: e.g. "1주차_2교시.pdf" or "recipe_메밀국수_timestamp.md" -> clean name
    cleaned_lesson = target_file_name.replace('.pdf','').replace('.txt','').replace('.hwp','').replace('.md','')
    if cleaned_lesson.startswith('recipe_'):
        cleaned_lesson = cleaned_lesson.replace('recipe_', '')
        cleaned_lesson = re.sub(r'_\d+$', '', cleaned_lesson)
        cleaned_lesson = cleaned_lesson.replace('_', ' ')
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
            
        # Enforce extra spacing between paragraphs (double newline -> triple newline)
        import re
        text = re.sub(r'\n{3,}', '\n\n', text)
        text = text.replace('\n\n', '\n\n\n')
            
        return text


    # Load gemini api key for QC validation
    gemini_api_key = ""
    try:
        config_path = os.path.join(HERE, "blog_account.json")
        if os.path.exists(config_path):
            with open(config_path, "r", encoding="utf-8") as f:
                config = json.load(f)
                gemini_api_key = config.get("GEMINI_API_KEY", "").strip()
    except Exception:
        pass

    wp_content = clean_remnants(wp_content, strip_markdown=False)
    blogger_content = clean_remnants(blogger_content)

    # 자체 텍스트 품질 검수(QC) 가동
    blogger_qc_passed = True
    blogger_qc_reason = ""
    if automation_utils:
        is_passed, reason = automation_utils.run_text_self_qc(wp_content, category, gemini_api_key)
        if not is_passed:
            raise ValueError(f"WordPress 본문 자체 검수(QC) 실패: {reason}")
        is_passed, reason = automation_utils.run_text_self_qc(blogger_content, category, gemini_api_key)
        if not is_passed:
            print(f"[WARN] Blogger 본문 자체 검수(QC) 실패: {reason}")
            blogger_qc_passed = False
            blogger_qc_reason = reason
    
    # Automatically append hashtags for recipe posts if none exist in the draft
    if category == "recipe" and cleaned_lesson:
        if "#" not in wp_content:
            tags = [
                "#요리레시피", "#집밥반찬", "#간단요리", "#홈쿡", 
                "#맛있는레시피", "#집밥레시피", "#요리추천", f"#{cleaned_lesson.replace(' ', '')}"
            ]
            wp_content = wp_content + "\n\n\n" + " ".join(tags)
        if "#" not in blogger_content:
            tags = [
                "#요리레시피", "#집밥반찬", "#간단요리", "#홈쿡", 
                "#맛있는레시피", "#집밥레시피", "#요리추천", f"#{cleaned_lesson.replace(' ', '')}"
            ]
            blogger_content = blogger_content + "\n\n\n" + " ".join(tags)
    
    if category == "study":
        lesson_part = target_file_name.replace('.pdf','').replace('.txt','').replace('.hwp','').replace('.md','').replace('_', ' ').strip()
        wp_title = f"{current_subject} - {lesson_part}"
        blogger_title = f"{current_subject} - {lesson_part}"

    # Also clean up the titles if they somehow still contain brackets/weeks/instructions/forbidden phrases
    for word in ["청소년지도사 자격증 대비:", "청소년지도사 자격증 대비 :", "청소년지도사자격증대비:", "청소년지도사 자격증 대비", "청소년지도사자격증대비", "청소년지도사", "핵심 요약", "핵심요약"]:
        wp_title = wp_title.replace(word, "")
        blogger_title = blogger_title.replace(word, "")

    wp_title = re.sub(r'^\[워드프레스용\s*제목\]\s*', '', wp_title)
    wp_title = re.sub(r'^\[워드프레스용\]\s*', '', wp_title)
    wp_title = wp_title.replace('[', '').replace(']', '').strip()
    wp_title = re.sub(r'^[\s\-:\s]+', '', wp_title)
    wp_title = re.sub(r'[\s\-:\s]+$', '', wp_title)
    wp_title = wp_title.strip()
    
    blogger_title = re.sub(r'^\[블로거용\s*제목\]\s*', '', blogger_title)
    blogger_title = re.sub(r'^\[블로거용\]\s*', '', blogger_title)
    blogger_title = blogger_title.replace('[', '').replace(']', '').strip()
    blogger_title = re.sub(r'^[\s\-:\s]+', '', blogger_title)
    blogger_title = re.sub(r'[\s\-:\s]+$', '', blogger_title)
    blogger_title = blogger_title.strip()

    # Re-enforce standard [과목명] - [차시명] format if it got too cleaned up
    if category == "study" and "-" not in wp_title:
        wp_title = f"{current_subject} - {wp_title}"
    if category == "study" and "-" not in blogger_title:
        blogger_title = f"{current_subject} - {blogger_title}"
    
    wp_url = ""
    wp_banner_url = ""
    blogger_banner_url = ""

    # Helper function to download AI image
    def download_image_helper(prompt, path):
        import os
        import random
        import time
        import requests
        import urllib.parse
        
        def preprocess_custom_image(src_path, dst_path, target_width=1080):
            try:
                from PIL import Image, ImageOps
                img = Image.open(src_path)
                img = ImageOps.exif_transpose(img)
                w, h = img.size
                if w > target_width:
                    ratio = target_width / float(w)
                    new_h = int(float(h) * ratio)
                    img = img.resize((target_width, new_h), Image.Resampling.LANCZOS)
                    print(f"[IMAGE_PROCESS] Resized custom image: {w}x{h} -> {target_width}x{new_h}")
                else:
                    print(f"[IMAGE_PROCESS] Keeping original dimensions: {w}x{h}")
                
                # Save as JPEG web-optimized
                img.convert("RGB").save(dst_path, "JPEG", quality=85)
                print(f"[SUCCESS] Preprocessed and saved custom image to: {dst_path}")
                return True
            except Exception as e:
                print(f"[WARN] Image preprocessing failed: {e}. Falling back to standard copy.")
                try:
                    import shutil
                    shutil.copy(src_path, dst_path)
                    return True
                except Exception as copy_err:
                    print(f"[ERROR] Failed fallback copy: {copy_err}")
                    return False

        if os.path.exists(path) and os.path.getsize(path) > 1000:
            print(f"[INFO] Using pre-existing local image at: {path}")
            return True
        encoded = urllib.parse.quote(prompt)
        headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
        }
        for attempt in range(4):
            seed = random.randint(1, 100000)
            url = f"https://image.pollinations.ai/prompt/{encoded}?width=800&height=600&nologo=true&seed={seed}"
            try:
                print(f"[INFO] Fetching AI image (attempt {attempt+1}): {url}")
                res = requests.get(url, headers=headers, timeout=25, verify=False)
                if res.status_code == 200 and len(res.content) > 1000:
                    with open(path, "wb") as f:
                        f.write(res.content)
                    print(f"[SUCCESS] Downloaded AI image to: {path}")
                    return True
                elif res.status_code == 402:
                    print(f"[WARN] Queue busy (402). Retrying in 3s...")
                    time.sleep(3)
                elif res.status_code == 429:
                    print(f"[WARN] Rate limited (429). Waiting 5s before retrying...")
                    time.sleep(5)
                else:
                    print(f"[WARN] Failed with status {res.status_code}. Retrying...")
                    time.sleep(2)
            except Exception as e:
                print(f"[WARN] Error fetching: {e}. Retrying...")
                time.sleep(2)
        return False

    def preprocess_custom_image(src_path, dst_path, target_width=1080):
        try:
            from PIL import Image, ImageOps
            img = Image.open(src_path)
            img = ImageOps.exif_transpose(img)
            w, h = img.size
            if w > target_width:
                ratio = target_width / float(w)
                new_h = int(float(h) * ratio)
                img = img.resize((target_width, new_h), Image.Resampling.LANCZOS)
                print(f"[IMAGE_PROCESS] Resized custom image: {w}x{h} -> {target_width}x{new_h}")
            else:
                print(f"[IMAGE_PROCESS] Keeping original dimensions: {w}x{h}")
            
            # Save as JPEG web-optimized
            img.convert("RGB").save(dst_path, "JPEG", quality=85)
            print(f"[SUCCESS] Preprocessed and saved custom image to: {dst_path}")
            return True
        except Exception as e:
            print(f"[WARN] Image preprocessing failed: {e}. Falling back to standard copy.")
            try:
                import shutil
                shutil.copy(src_path, dst_path)
                return True
            except Exception as copy_err:
                print(f"[ERROR] Failed fallback copy: {copy_err}")
                return False

    # Map category to specific blog folder/category
    if category == "recipe":
        cat_name = "요리/반찬"
    elif category == "study":
        cat_name = current_subject if current_subject else "청소년지도사"
        if "_" in cat_name:
            cat_name = cat_name.split("_")[0]
    elif category == "mindset":
        cat_name = "자기계발"
    else:
        cat_name = current_subject or "기타"
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
                
                # --- START: Cooking Recipe Images Pipeline ---
                recipe_images = {}
                banner_path = None
                blogger_banner_path = None
                if category == "recipe" and cleaned_lesson:
                    dish_name = cleaned_lesson
                    clean_dish = dish_name.replace(" ", "").lower()
                    user_home = os.path.expanduser("~")
                    custom_dirs = [
                        os.path.join(user_home, "my-ai-office", "assets", "custom_recipe_photos"),
                        os.path.join(user_home, "my-ai-office", "_company", "자료")
                    ]
                    
                    local_files = {}
                    for custom_dir in custom_dirs:
                        if not os.path.exists(custom_dir):
                            continue
                        try:
                            for f in os.listdir(custom_dir):
                                if not f.lower().endswith(('.png', '.jpg', '.jpeg')):
                                    continue
                                f_lower = f.replace(" ", "").lower()
                                if f_lower.startswith(clean_dish):
                                    suffix = f_lower.replace(clean_dish, "").strip("_")
                                    photo_type = None
                                    if "ing" in suffix:
                                        photo_type = "ing"
                                    elif "wp_fin" in suffix:
                                        photo_type = "wp_fin"
                                    elif "blogger_fin" in suffix:
                                        photo_type = "blogger_fin"
                                    elif "fin" in suffix or "finished" in suffix or "cozy" in suffix or "modern" in suffix:
                                        photo_type = "fin"
                                    elif "step" in suffix:
                                        m_step = re.search(r'step(\d+)', suffix)
                                        if m_step:
                                            photo_type = f"step{m_step.group(1)}"
                                    
                                    if photo_type and photo_type not in local_files:
                                        temp_name = f"temp_optimized_{photo_type}.png"
                                        temp_path = os.path.join(HERE, temp_name)
                                        if preprocess_custom_image(os.path.join(custom_dir, f), temp_path):
                                            local_files[photo_type] = temp_path
                                            print(f"[INFO] Found local custom photo: {photo_type} -> {f}")
                        except Exception as scan_err:
                            print(f"[WARN] Flexible image scanning failed in {custom_dir}: {scan_err}")
                    
                    # Resolve general finished photo to channel-specific if not explicitly present
                    if "fin" in local_files:
                        if "wp_fin" not in local_files:
                            local_files["wp_fin"] = local_files["fin"]
                            print("[INFO] Reusing custom general finished photo as wp_fin")
                        if "blogger_fin" not in local_files:
                            local_files["blogger_fin"] = local_files["fin"]
                            print("[INFO] Reusing custom general finished photo as blogger_fin")
                            
                    # Extract variables from metadata
                    dish_val = metadata.get('Dish', dish_name) if metadata else dish_name
                    ing_val = metadata.get('Ingredients', '') if metadata else ''

                    # 7, 8단계: 병렬 이미지 다운로드 + Gemini 멀티모달 QC 검수 + 실패 시 예외 차단
                    def get_and_qc_image(photo_type, prompt_template, path, is_ing):
                        if photo_type in local_files:
                            return True
                        for attempt in range(1, 4):
                            prompt = prompt_template
                            if attempt > 1:
                                prompt += f", alternative composition variation {attempt}"
                            if download_image_helper(prompt, path):
                                if automation_utils:
                                    is_passed, reason = automation_utils.run_gemini_multimodal_image_qc(
                                        path, dish_val, is_ingredients=is_ing, gemini_api_key=gemini_api_key
                                    )
                                    if is_passed:
                                        # 비주얼 중복 검수(기존 해시 기반)
                                        dup_passed, dup_reason = automation_utils.run_self_qc_image(path)
                                        if dup_passed:
                                            local_files[photo_type] = path
                                            print(f"[QC-PASSED] {photo_type} Multimodal & Duplicate QC passed on attempt {attempt}.")
                                            return True
                                        else:
                                            print(f"[QC-FAILED] {photo_type} Duplicate QC failed on attempt {attempt}: {dup_reason}")
                                    else:
                                        print(f"[QC-FAILED] {photo_type} Multimodal QC failed on attempt {attempt}: {reason}")
                                else:
                                    local_files[photo_type] = path
                            time.sleep(2.5)
                        return False

                    # 네이버 이미지 검색 기준 요리/식재료 스타일 분석 가이드 획득
                    ing_styling_guide = get_authentic_korean_food_styling_guide(dish_val, is_ingredients=True, gemini_api_key=gemini_api_key)
                    fin_styling_guide = get_authentic_korean_food_styling_guide(dish_val, is_ingredients=False, gemini_api_key=gemini_api_key)

                    tasks = []
                    # Build prompts
                    if "ing" not in local_files:
                        if ing_val:
                            ing_prompt = f"gourmet food photography of fresh raw ingredients for cooking Korean {dish_val}: {ing_styling_guide or ing_val}, raw materials, neatly arranged on a clean wooden plate, bright modern kitchen background, warm natural light, authentic Korean ingredients styling, realistic photo, hyper-realistic food photography, natural realistic food texture, no plastic sheen, highly detailed"
                        else:
                            ing_prompt = f"gourmet food photography of fresh raw ingredients for cooking Korean {dish_val}: {ing_styling_guide or 'raw materials'}, raw materials, neatly arranged on a clean wooden plate, bright modern kitchen background, warm natural light, authentic Korean ingredients styling, realistic photo, hyper-realistic food photography, natural realistic food texture, no plastic sheen, highly detailed"
                        tasks.append(("ing", ing_prompt, os.path.join(HERE, "temp_wp_ing.png"), True))
                        
                    if "wp_fin" not in local_files:
                        wp_fin_prompt = f"professional food photography of a delicious finished bowl of authentic Korean {dish_val}: {fin_styling_guide or 'finished dish'}, styled neatly in a clean modern ceramic bowl, cozy modern dining room background, light mint green placemat, warm natural side light, 8k resolution, realistic food texture, hyper-realistic food photography, no plastic sheen, highly detailed, realistic photo"
                        tasks.append(("wp_fin", wp_fin_prompt, os.path.join(HERE, "temp_wp_fin.png"), False))
                        
                    if "blogger_fin" not in local_files:
                        blogger_fin_prompt = f"professional food photography of a delicious finished bowl of authentic Korean {dish_val}: {fin_styling_guide or 'finished dish'}, styled neatly in a clean white porcelain bowl, elegant modern kitchen background, placed on a white linen mat over a light marble countertop, styled food shot, natural daylight, 8k resolution, realistic food texture, hyper-realistic food photography, no plastic sheen, highly detailed, realistic photo"
                        tasks.append(("blogger_fin", blogger_fin_prompt, os.path.join(HERE, "temp_blogger_fin.png"), False))

                    if tasks:
                        import concurrent.futures
                        with concurrent.futures.ThreadPoolExecutor(max_workers=len(tasks)) as executor:
                            futures = {executor.submit(get_and_qc_image, t[0], t[1], t[2], t[3]): t[0] for t in tasks}
                            concurrent.futures.wait(futures)

                    # 필수 요리 완성 이미지 누락 검출 시 에러 강제 전파 (발행 차단)
                    if "wp_fin" not in local_files:
                        raise ValueError(f"요리 완성 이미지(wp_fin) 다운로드 및 멀티모달 검수 실패로 포스팅 발행을 차단합니다. (요리명: {dish_val})")

                    # Upload all to WP media library
                    for p_type, local_path in local_files.items():
                        if p_type == "fin":
                            continue  # resolved to channel-specific fins
                        try:
                            with open(local_path, "rb") as im_f:
                                im_data = im_f.read()
                            res = client.wp.uploadFile(0, wp_user, wp_pass, {
                                "name": f"recipe_{p_type}_{int(time.time())}.png",
                                "type": "image/png",
                                "bits": xmlrpc.client.Binary(im_data),
                                "overwrite": True
                            })
                            uploaded_url = res.get("url")
                            if uploaded_url:
                                recipe_images[p_type] = uploaded_url
                                print(f"[SUCCESS] Uploaded {p_type} image: {uploaded_url}")
                        except Exception as upload_err:
                            print(f"[WARN] Failed to upload {p_type} image to WP: {upload_err}")
                # --- END: Cooking Recipe Images Pipeline ---

                # Check for custom media uploaded by user (only for study/mindset, skip recipe banner generation)
                wp_banner_url = ""
                blogger_banner_url = ""
                
                if category == "recipe":
                    # Representative Banner is the cooked finished photo (or ingredients photo if fin is missing)
                    wp_banner_url = recipe_images.get("wp_fin") or recipe_images.get("fin") or recipe_images.get("ing") or ""
                    blogger_banner_url = recipe_images.get("blogger_fin") or recipe_images.get("fin") or recipe_images.get("ing") or ""
                    print(f"[INFO] Using cooking photo as top banner - WP: {wp_banner_url}, Blogger: {blogger_banner_url}")
                else:
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
                                
                    # Determine paths to upload with Visual QC self-healing retry (up to 3 attempts)
                    banner_path = None
                    blogger_banner_path = None
                    
                    max_attempts = 3
                    qc_passed = False
                    
                    for attempt in range(1, max_attempts + 1):
                        if custom_banner_path and os.path.exists(custom_banner_path):
                            banner_path = custom_banner_path
                            blogger_banner_path = custom_banner_path
                        else:
                            # Generate dynamic banner using Pillow
                            banner_path = os.path.join(HERE, "temp_wp_banner.png")
                            blogger_banner_path = os.path.join(HERE, "temp_blogger_banner.png")
                            try:
                                # Clean up previous dynamic banner drafts to avoid cache issues
                                for tp in [banner_path, blogger_banner_path]:
                                    if os.path.exists(tp):
                                        try:
                                            os.remove(tp)
                                        except Exception:
                                            pass
                                create_dynamic_banner(wp_title, category, current_subject, banner_path, is_blogger=False)
                                create_dynamic_banner(blogger_title, category, current_subject, blogger_banner_path, is_blogger=True)
                            except Exception as gen_err:
                                print(f"[WARN] Dynamic banner generation failed: {gen_err}")
                                banner_path = os.path.join(HERE, "youth_instructor_banner.png")
                                blogger_banner_path = os.path.join(HERE, "youth_instructor_banner_blogger.png")
                        
                        # 비주얼 중복 검수 가동 (study / mindset)
                        qc_passed = True
                        if automation_utils:
                            for p_path in [banner_path, blogger_banner_path]:
                                if p_path and os.path.exists(p_path):
                                    is_passed, reason = automation_utils.run_self_qc_image(p_path)
                                    if not is_passed:
                                        print(f"[QC-FAILED] Banner Visual QC failed on attempt {attempt}: {reason}")
                                        qc_passed = False
                                        break
                                        
                        if qc_passed:
                            print(f"[QC-PASSED] Banner Visual QC passed on attempt {attempt}.")
                            break
                        else:
                            if attempt == max_attempts:
                                print(f"[WARN] Banner Visual QC failed on final attempt: {reason}. Falling back to default banners.")
                                banner_path = os.path.join(HERE, "youth_instructor_banner.png")
                                blogger_banner_path = os.path.join(HERE, "youth_instructor_banner_blogger.png")
                                break
                            else:
                                print(f"[QC-RETRY] Retrying banner generation...")

                    # Upload WordPress Banner
                    if banner_path and os.path.exists(banner_path):
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
                    if blogger_banner_path and os.path.exists(blogger_banner_path):
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

                wp_body = markdown_to_html_for_blogger(wp_content, is_blogger=False)

                # Embed WordPress recipe images dynamically
                if category == "recipe" and recipe_images:
                    wp_recipe_images = {}
                    if "ing" in recipe_images: wp_recipe_images["ing"] = recipe_images["ing"]
                    if "wp_fin" in recipe_images: wp_recipe_images["fin"] = recipe_images["wp_fin"]
                    elif "fin" in recipe_images: wp_recipe_images["fin"] = recipe_images["fin"]
                    for k, v in recipe_images.items():
                        if k.startswith("step"):
                            wp_recipe_images[k] = v
                    wp_body = embed_images_in_content(wp_body, wp_recipe_images, exclude_fin=False)
                
                # Generate and Upload WordPress Quiz Banner (ONLY for study summaries category)
                wp_quiz_url = ""
                if category == "study":
                    wp_quiz_path = os.path.join(HERE, "temp_wp_quiz.png")
                    try:
                        create_quiz_banner(current_subject, wp_quiz_path, is_blogger=False)
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
                        img_tag = f'\n<br><br>\n<img src="{wp_quiz_url}" style="width: 100%; max-width: 850px; height: auto; display: block; margin: 40px auto;" alt="Quiz Banner" />\n<br><br>\n'
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
                    if category == "recipe":
                        wp_body = f'<img src="{wp_banner_url}" style="width: 100%; max-width: 650px; height: auto; display: block; margin: 24px auto; border-radius: 8px; box-shadow: 0 10px 15px -3px rgba(0,0,0,0.1), 0 4px 6px -2px rgba(0,0,0,0.05);" alt="대표 완성 요리" />\n\n' + wp_body
                    else:
                        wp_body = f'<img src="{wp_banner_url}" style="width: 100%; max-width: 850px; height: auto; display: block; margin: 30px auto;" alt="Banner" />\n\n' + wp_body

                # Check and dynamically create WordPress category if not exists
                wp_categories = []
                try:
                    cats = client.wp.getCategories(0, wp_user, wp_pass)
                    wp_categories = [c.get('categoryName') for c in cats]
                except Exception as cat_err:
                    print(f"[WARN] Failed to fetch WordPress categories: {cat_err}")

                if cat_name not in wp_categories:
                    try:
                        client.wp.newTerm(0, wp_user, wp_pass, {
                            "name": cat_name,
                            "taxonomy": "category"
                        })
                        print(f"[SUCCESS] Created WordPress category dynamically: {cat_name}")
                    except Exception as create_err:
                        print(f"[WARN] Failed to create WordPress category '{cat_name}': {create_err}")

                post_data = {
                    "title": wp_title,
                    "description": wp_body,
                    "post_status": "publish",
                    "categories": [cat_name]
                }
                post_id = client.metaWeblog.newPost("default", wp_user, wp_pass, post_data, True)
                wp_url = f"{wp_domain}/?p={post_id}"
                print(f"[SUCCESS] WordPress auto-published! URL: {wp_url}")
                
                # 비주얼 QC 히스토리에 이미지 해시 등록
                if automation_utils:
                    if category == "recipe" and "wp_fin" in local_files:
                        automation_utils.add_image_to_history(local_files["wp_fin"])
                    elif banner_path and os.path.exists(banner_path):
                        automation_utils.add_image_to_history(banner_path)
    except Exception as e:
        print(f"[ERROR] WordPress auto-publishing failed: {e}")
        raise e

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
                    
                    if not blogger_qc_passed:
                        raise ValueError(f"Blogger 본문 품질 검수(QC) 통과 실패: {blogger_qc_reason}")
                        
                    blogger_body = blogger_content

                    # Embed Blogger recipe images dynamically
                    if category == "recipe" and recipe_images:
                        blogger_recipe_images = {}
                        if "ing" in recipe_images: blogger_recipe_images["ing"] = recipe_images["ing"]
                        if "blogger_fin" in recipe_images: blogger_recipe_images["fin"] = recipe_images["blogger_fin"]
                        elif "fin" in recipe_images: blogger_recipe_images["fin"] = recipe_images["fin"]
                        for k, v in recipe_images.items():
                            if k.startswith("step"):
                                blogger_recipe_images[k] = v
                        blogger_body = embed_images_in_content(blogger_body, blogger_recipe_images, exclude_fin=False)
                    
                    # Generate and Upload Blogger Quiz Banner (ONLY for study summaries category)
                    blogger_quiz_url = ""
                    if category == "study":
                        blogger_quiz_path = os.path.join(HERE, "temp_blogger_quiz.png")
                        try:
                            create_quiz_banner(current_subject, blogger_quiz_path, is_blogger=True)
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
                            img_tag = f'\n<br><br>\n<img src="{blogger_quiz_url}" style="width: 100%; max-width: 850px; height: auto; display: block; margin: 40px auto;" alt="Quiz Banner" />\n<br><br>\n'
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
                        if category == "recipe":
                            blogger_body = f'<img src="{blogger_banner_url}" style="width: 100%; max-width: 650px; height: auto; display: block; margin: 24px auto; border-radius: 8px; box-shadow: 0 10px 15px -3px rgba(0,0,0,0.1), 0 4px 6px -2px rgba(0,0,0,0.05);" alt="대표 완성 요리" />\n\n' + blogger_body
                        else:
                            blogger_body = f'<img src="{blogger_banner_url}" style="width: 100%; max-width: 850px; height: auto; display: block; margin: 30px auto;" alt="Banner" />\n\n' + blogger_body
                    elif wp_banner_url:
                        if category == "recipe":
                            blogger_body = f'<img src="{wp_banner_url}" style="width: 100%; max-width: 650px; height: auto; display: block; margin: 24px auto; border-radius: 8px; box-shadow: 0 10px 15px -3px rgba(0,0,0,0.1), 0 4px 6px -2px rgba(0,0,0,0.05);" alt="대표 완성 요리" />\n\n' + blogger_body
                        else:
                            blogger_body = f'<img src="{wp_banner_url}" style="width: 100%; max-width: 850px; height: auto; display: block; margin: 30px auto;" alt="Banner" />\n\n' + blogger_body
                        
                    html_content = markdown_to_html_for_blogger(blogger_body, is_blogger=True)
                    payload = {
                        "kind": "blogger#post",
                        "blog": {"id": blogger_id},
                        "title": blogger_title,
                        "content": html_content,
                        "labels": [cat_name]
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
                        
                        # 비주얼 QC 히스토리에 이미지 해시 등록
                        if automation_utils:
                            if category == "recipe" and "blogger_fin" in local_files:
                                automation_utils.add_image_to_history(local_files["blogger_fin"])
                            elif blogger_banner_path and os.path.exists(blogger_banner_path):
                                automation_utils.add_image_to_history(blogger_banner_path)
                    else:
                        raise ValueError(f"Blogger API returned status {response.status_code}: {response.text}")
    except Exception as e:
        print(f"[ERROR] Blogger auto-publishing failed: {e}")
        if wp_url:
            print("[INFO] WordPress succeeded, so we will bypass raising Blogger error and mark Blogger as pending.")
            if automation_utils:
                try:
                    automation_utils.log_automation_failure(
                        task_id=f"blogger_{category}_pending",
                        task_name=f"Blogger 블로그 연동 대기 ({current_subject})",
                        stage="Blogger API 글 작성 단계",
                        error_msg=f"Blogger API 실패 (구글 로그인 권한 필요): {e}\n(워드프레스는 정상 발행됨: {wp_url})"
                    )
                except Exception as log_err:
                    print(f"[WARN] Failed to log Blogger pending warning to dashboard: {log_err}")
        else:
            raise e

    return {
        "wp_url": wp_url,
        "blogger_url": blogger_url
    }

def main():
    try:
        _main_impl()
    except Exception as err:
        import traceback
        err_msg = f"{err}\n{traceback.format_exc()}"
        print(f"[ERROR] Critical failure in blog_post_generator: {err_msg}")
        
        if automation_utils:
            try:
                is_auto = "auto" in [a.lower() for a in sys.argv]
                task_name = "청소년지도사 블로그 자동 발행" if is_auto else "블로그 수동 발행"
                automation_utils.log_automation_failure(
                    task_id="youth_blog_publish",
                    task_name=task_name,
                    stage="초안 작성 및 API 전송 발행 단계",
                    error_msg=str(err)
                )
            except Exception as log_err:
                print(f"[WARN] Failed to write failure task: {log_err}")
        sys.exit(1)

def _main_impl():
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
            
        # 1일 1회 초과 발행 방지 안전 제어 장치 (study 카테고리 한정)
        today_str = time.strftime("%Y-%m-%d")
        today_study_posts = [
            p for p in queue_data.get("completed_lessons", [])
            if p.get("date") == today_str and p.get("status") == "published" and p.get("subject") not in ["요리/반찬", "인스타그램"]
        ]
        if len(today_study_posts) >= 1:
            print(f"\n[INFO] Daily limit reached. Today ({today_str}) already published: {[p['lesson'] for p in today_study_posts]}")
            print("Execution skipped to protect SEO rating from search engines.")
            sys.exit(0)
            
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
        
        # Get dynamic hashtags
        trending_study_kws = load_trending_study_keywords()
        subject_tag = current_subject.replace(" ", "")
        if subject_tag not in trending_study_kws:
            trending_study_kws.insert(0, subject_tag)
        for def_tag in ["청소년지도사", "사회복지사", "독학합격", "공부계획", "학습팁"]:
            if def_tag not in trending_study_kws:
                trending_study_kws.append(def_tag)
        hashtag_str = " ".join([f"#{kw}" for kw in trending_study_kws[:10]])
        
        prompt = ""
        is_study_category = (category == "study")
        if is_study_category:
            wp_prompt = f"""당신은 자격증 시험 전문 교육 블로거입니다.
아래 제공된 '청소년지도사' 관련 학습 텍스트 및 온라인 검색 참고자료를 바탕으로 워드프레스(WordPress)에 업로드할 학습 요약 글을 작성하세요.

[중요 지시사항]
- 반드시 처음부터 끝까지 완전하고 완벽한 '한국어'로만 작성하십시오.
- 영어(sớm, also, juga 등), 베트남어, 태국어 등 외래어 토큰이나 타국어 단어가 단 한 단어도 섞여서는 안 됩니다. 
- 한자(漢字) 역시 가급적 한글로 순화하고 한글로만 작성하십시오.
- AI 임의의 다국어 번역 혼동이나 깨진 토큰 사용을 철저히 금지합니다.

[가독성 극대화 및 레이아웃 지시사항 (네이버 블로그 스타일 가독성)]
1. [핵심 요약 3가지 우선 배치]: 본문 도입부(서론) 직후에, 오늘 공부할 내용에서 가장 중요한 핵심 요점 3가지를 글머리 기호(•) 또는 순서 있는 번호(1., 2., 3.)를 활용하여 한눈에 들어오도록 3줄 요약 리스트로 먼저 제시한 후 본론을 시작하십시오.
2. [시각적 강약 조절 (강조)]: 단조로운 줄글 구성을 배제하고, 핵심 용어나 중요한 문장은 반드시 마크다운 굵게(**텍스트**) 기호로 감싸 시각적 포인트를 주어 독자가 중요한 내용을 한눈에 파악할 수 있도록 '강약'을 확실하게 구현하십시오.
3. [인용구 및 정리 블록 활용]: 주요 개념의 정의나 핵심 요약은 마크다운 인용구(> ) 형식을 적극 활용하여 본문과 시각적으로 구분하여 정리해 주십시오.
4. [구조화된 정보 제공]: 주요 개념 비교나 분류가 필요한 경우, 적극적으로 표(Table) 형식을 사용하여 깔끔하게 정보를 전달하십시오. 이때 워드프레스용 표는 전문적이고 상세한 분류 기준을 다룰 수 있도록 3~4개 열(Column)로 구성된 깊이 있는 상세 정보 표(Table) 형태로 작성하십시오.
5. [마이크로 문단 및 충분한 여백]: 글을 쓸 때 1~2개 문장 단위로 매우 짧게 단락을 나누고, 문단과 문단 사이에는 빈 줄을 2줄 이상(엔터 3번) 넣어 모바일 화면에서 읽기 편리하도록 충분한 여백(가독성 높은 숨구멍)을 확보하십시오.
6. [마크다운 문법 적용]: 대제목은 `#`, 중제목은 `##`, 소제목은 `###`을 명확하게 붙여서 구조적인 문서를 만드십시오. (이 기호들은 자동 변환되므로 반드시 작성해 주셔야 합니다.)
7. [포스팅 하단 태그 삽입]: 모든 버전의 본문 가장 최하단(본문 및 퀴즈 내용이 완전히 끝난 후)에는 다음 해시태그를 공백 문자로 구분하여 반드시 그대로 첨부하십시오. 추가로 본문 주제와 관련된 개별 핵심 태그를 2~3개 더 추가해 주십시오.
{hashtag_str}

[요청 주제/키워드]
{content}

[온라인 검색 참고 자료]
{online_context if online_context else "자체 지식을 활용해 상세히 작성하세요"}

[출력 요구사항 및 포맷]
# [워드프레스용 제목]
(본문은 아주 따뜻하고 친근하며 다정한 어조로 작성해 주세요. 요약 리스트(•)와 단락 구분, 깔끔한 소제목을 적극적으로 활용하여 가독성 있게 정리해 주세요. 본문과 퀴즈 사이에 빈칸 줄바꿈(엔터)을 2회 이상 넣고, "[이곳에 학습 퀴즈 관련 이미지가 들어갈 자리입니다]" 라는 안내 문구를 가독성 있게 표기하여 확실하게 물리적인 간격을 넓혀 주세요. 그 후 공부한 내용을 점검할 수 있도록 4지선다형 객관식 퀴즈 1문항과 정답 및 해설을 추가해 주세요. 마지막에 독자들을 응원하는 다정한 멘트와 해시태그를 작성해 주세요.)
"""

            blogger_prompt = f"""당신은 자격증 시험 전문 교육 블로거입니다.
아래 제공된 '청소년지도사' 관련 학습 텍스트 및 온라인 검색 참고자료를 바탕으로 구글 블로거(Blogger)에 업로드할 학습 요약 글을 작성하세요.

[중요 지시사항]
- 반드시 처음부터 끝까지 완전하고 완벽한 '한국어'로만 작성하십시오.
- 영어(sớm, also, juga 등), 베트남어, 태국어 등 외래어 토큰이나 타국어 단어가 단 한 단어도 섞여서는 안 됩니다. 
- 한자(漢字) 역시 가급적 한글로 순화하고 한글로만 작성하십시오.
- AI 임의의 다국어 번역 혼동이나 깨진 토큰 사용을 철저히 금지합니다.

[가독성 극대화 및 레이아웃 지시사항 (네이버 블로그 스타일 가독성)]
1. [핵심 요약 3가지 우선 배치]: 본문 도입부(서론) 직후에, 오늘 공부할 내용에서 가장 중요한 핵심 요점 3가지를 글머리 기호(•) 또는 순서 있는 번호(1., 2., 3.)를 활용하여 한눈에 들어오도록 3줄 요약 리스트로 먼저 제시한 후 본론을 시작하십시오.
2. [시각적 강약 조절 (강조)]: 단조로운 줄글 구성을 배제하고, 핵심 용어나 중요한 문장은 반드시 마크다운 굵게(**텍스트**) 기호로 감싸 시각적 포인트를 주어 독자가 중요한 내용을 한눈에 파악할 수 있도록 '강약'을 확실하게 구현하십시오.
3. [인용구 및 정리 블록 활용]: 주요 개념의 정의나 핵심 요약은 마크다운 인용구(> ) 형식을 적극 활용하여 본문과 시각적으로 구분하여 정리해 주십시오.
4. [구조화된 정보 제공]: 주요 개념 비교나 분류가 필요한 경우, 적극적으로 표(Table) 형식을 사용하여 깔끔하게 정보를 전달하십시오. 이때 구글 블로거용 표는 모바일 가독성을 극대화하기 위해 핵심 요약 위주의 간결한 2개 열(Column)로 구성된 직관적인 비교 표 형태로 작성하십시오.
5. [마이크로 문단 및 충분한 여백]: 글을 쓸 때 1~2개 문장 단위로 매우 짧게 단락을 나누고, 문단과 문단 사이에는 빈 줄을 2줄 이상(엔터 3번) 넣어 모바일 화면에서 읽기 편리하도록 충분한 여백(가독성 높은 숨구멍)을 확보하십시오.
6. [마크다운 문법 적용]: 대제목은 `#`, 중제목은 `##`, 소제목은 `###`을 명확하게 붙여서 구조적인 문서를 만드십시오. (이 기호들은 자동 변환되므로 반드시 작성해 주셔야 합니다.)
7. [포스팅 하단 태그 삽입]: 모든 버전의 본문 가장 최하단(본문 및 퀴즈 내용이 완전히 끝난 후)에는 다음 해시태그를 공백 문자로 구분하여 반드시 그대로 첨부하십시오. 추가로 본문 주제와 관련된 개별 핵심 태그를 2~3개 더 추가해 주십시오.
{hashtag_str}

[요청 주제/키워드]
{content}

[온라인 검색 참고 자료]
{online_context if online_context else "자체 지식을 활용해 상세히 작성하세요"}

[출력 요구사항 및 포맷]
# [블로거용 제목]
(본문은 담담하고 핵심 중심의 간결하며 정돈된 전문적인 어조로 작성해 주세요. 핵심 개념 설명은 표(Table) 또는 구조화된 도표 형식을 적극 활용하여 한눈에 정리되게 작성해 주시고, 요약 리스트(•)를 풍부하게 배치하여 핵심만 빠르게 읽을 수 있도록 해 주세요. 본문과 퀴즈 사이에 빈칸 줄바꿈(엔터)을 2회 이상 넣고, "[이곳에 학습 퀴즈 관련 이미지가 들어갈 자리입니다]" 라는 안내 문구를 가독성 있게 표기하여 확실하게 물리적인 간격을 넓혀 주세요. 그 후 공부한 내용을 직관적으로 점검할 수 있도록 O/X 퀴즈 2문항을 작성해 주세요. 단, O/X 퀴즈의 정답과 해설은 개별 문제 바로 옆에 작성하여 미리 노출하지 말고, 반드시 문제 전체가 끝난 후 본문 최하단(해시태그 바로 위)에 '[정답 및 해설]' 영역을 별도로 만들어 분리 기입하십시오. 마지막에 해시태그를 추가해 주세요.)
"""
        elif category == "mindset":
            prompt = f"""당신은 마음 치유 및 심리 전문 블로거입니다.
아래 키워드와 참고자료를 바탕으로 워드프레스와 구글 블로거에 각각 업로드할 두 가지 버전의 글을 작성하세요.

[중요 지시사항]
1. [마이크로 문단 및 충분한 여백 (네이버 블로그 스타일)]: 문장은 1~2개 문장 단위로 매우 짧게 단락을 나누어 작성하고, 문단과 문단 사이에는 반드시 빈 줄을 2줄 이상(엔터 3번) 띄워서 모바일 가독성을 극대화하십시오.
2. [시각적 강약 조절 (강조)]: 글 전체에 어조의 강약이 느껴지도록, 가벼운 설명과 강조해야 할 핵심 인사이트 및 마음에 와닿는 구절을 명확히 구분하십시오. 특히 핵심 단어나 핵심이 되는 한 줄 문장은 마크다운 굵게(**텍스트**)로 감싸 포인트를 주십시오.
3. [인용구 및 마크다운 헤더 활용]: 에세이 중간에 깊은 통찰을 주는 문장이나 마음을 치유하는 한마디는 마크다운 인용구(> ) 형식을 활용해 독자의 시선을 사로잡고, 각 단락의 주제는 `##` 또는 `###` 마크다운 헤더로 명확히 표시하여 글에 뼈대와 깊이를 주십시오.
4. [포스팅 하단 태그 삽입] 모든 버전의 본문 가장 최하단(응원 멘트나 본문 내용이 완전히 끝난 후)에는 해당 포스팅 내용과 관련이 깊은 핵심 단어들을 해시태그 형식(예: #마인드셋 #심리테라피 등)으로 5~10개 반드시 첨부하십시오.

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
(본문은 정돈되고 전문적인 에세이 톤으로 작성해 주세요. 밋밋하고 평평한 문장이 되지 않도록 깊은 울림을 주는 통찰 문장이나 핵심 메시지는 마크다운 굵게 기호(**강조**)를 사용해 강약을 주고, 주요 생각이나 질문은 인용구 기호(> )를 사용해 시각적으로 도드라지게 하십시오. 본문 단락에는 소제목(##, ###)을 붙여 구조화하고, 마지막에 해시태그를 추가해 주세요.)
"""
        elif category == "recipe":
            prompt = f"""당신은 요리 및 집밥 전문 파워 블로거입니다.
아래 제공된 정보 및 레시피 키워드를 바탕으로 워드프레스(WordPress)와 구글 블로거(Blogger)에 각각 업로드할 두 가지 버전의 글을 작성하세요.

[중요 지시사항]
1. 두 블로그는 완전히 다른 독자층을 대상으로 독립적으로 운영되므로, 두 버전의 문체와 내용 구성이 완전히 다르게(차별화되게) 작성되어야 합니다. 동일한 내용을 단순히 다듬기만 한 형태여서는 안 됩니다.
2. 한 블로그 내용에 여러 요리를 함께 나열하지 마십시오. 반드시 제시된 주제/키워드 중 단 '하나'의 요리(단일 요리)만을 선정하여 그 요리 하나만 깊고 상세하게 설명해야 합니다. (여러 요리나 다른 반찬 정보가 입력값에 섞여 있더라도, 단 하나의 핵심 요리만 집중적으로 파고드십시오.)
3. 본문 내에 절대로 '자가진단', '퀴즈', '자가진단 QUIZ' 또는 학습용 질문/평가 문제를 포함하지 마십시오.
4. [마이크로 문단 및 충분한 여백 (네이버 블로그 스타일)]: 글을 쓸 때 1~2개 문장 단위로 매우 짧게 단락을 나누고, 문단과 문단 사이에는 반드시 빈 줄을 2줄 이상(엔터 3번) 띄워서 모바일 화면에서 쾌적하게 보이도록 충분한 숨구멍 여백을 확보하십시오.
5. [시각적 강약 조절 (강조와 구조화)]:
   - 각 요리 과정의 핵심 비법이나 주요 팁은 마크다운 굵게(**텍스트**)와 인용구(> ) 기호를 적극적으로 사용하여 시각적 강약을 뚜렷하게 구분해 주십시오.
   - 대제목은 `#`, 중제목은 `##`, 소제목은 `###`을 명확하게 표시하십시오.
   - 필요한 재료 목록은 반드시 표(Table) 또는 명확한 글머리 기호 리스트 형식으로 깔끔하게 정리해 한눈에 들어오게 제시하십시오.
6. [포스팅 하단 태그 삽입] 모든 버전의 본문 가장 최하단(본문 내용이 완전히 끝난 후)에는 해당 요리 레시피와 관련이 깊은 핵심 단어들을 해시태그 형식(예: #요리레시피 #집밥반찬 등)으로 5~10개 반드시 첨부하십시오.

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
(본문은 깔끔하고 명확하며 군더더기 없는 '구조적이고 전문적인 레시피 카드 어조'로 작성해 주세요. 불필요한 일상 이야기나 감정 묘사는 일체 배제하고, 필요한 재료 목록(정량 표기 포함)을 표(Table) 또는 명확한 리스트 형식으로 정리해 제시하십시오. 조리 단계(Step-by-step)를 시간순으로 명확하고 간결하게 기입하되, 각 단계와 핵심 팁에는 적절히 마크다운 소제목(##, ###)과 강조 기호(**강조**) 및 인용구 기호(> )를 꼭 사용하여 시각적인 강약과 가독성을 확실하게 확보하십시오. 마지막에 해시태그를 추가해 주세요.)
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
        if is_study_category:
            print("[INFO] Generating WordPress version content...")
            wp_res = ask_llm(ollama_url, model, wp_prompt, gemini_api_key)
            if not wp_res:
                print("[ERROR] Failed to generate WordPress content from LLM.")
                sys.exit(1)
                
            print("[INFO] Generating Blogger version content...")
            blogger_res = ask_llm(ollama_url, model, blogger_prompt, gemini_api_key)
            if not blogger_res:
                print("[ERROR] Failed to generate Blogger content from LLM.")
                sys.exit(1)
                
            result = f"========== WORDPRESS VERSION ==========\n\n{wp_res}\n\n========== BLOGGER VERSION ==========\n\n{blogger_res}"
        else:
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
        
        # Get dynamic hashtags
        trending_study_kws = load_trending_study_keywords()
        subject_tag = category.replace(" ", "")
        if subject_tag not in trending_study_kws:
            trending_study_kws.insert(0, subject_tag)
        for def_tag in ["청소년지도사", "사회복지사", "독학합격", "공부계획", "학습팁"]:
            if def_tag not in trending_study_kws:
                trending_study_kws.append(def_tag)
        hashtag_str = " ".join([f"#{kw}" for kw in trending_study_kws[:10]])
        
        prompt = ""
        is_study_category = (category == "study")
        if is_study_category:
            wp_prompt = f"""당신은 자격증 시험 전문 교육 블로거입니다.
아래 제공된 '청소년지도사' 관련 학습 텍스트 및 온라인 검색 참고자료를 바탕으로 워드프레스(WordPress)에 업로드할 학습 요약 글을 작성하세요.

[중요 지시사항]
- 반드시 처음부터 끝까지 완전하고 완벽한 '한국어'로만 작성하십시오.
- 영어(sớm, also, juga 등), 베트남어, 태국어 등 외래어 토큰이나 타국어 단어가 단 한 단어도 섞여서는 안 됩니다. 
- 한자(漢字) 역시 가급적 한글로 순화하고 한글로만 작성하십시오.
- AI 임의의 다국어 번역 혼동이나 깨진 토큰 사용을 철저히 금지합니다.

[가독성 극대화 및 레이아웃 지시사항 (네이버 블로그 스타일 가독성)]
1. [핵심 요약 3가지 우선 배치]: 본문 도입부(서론) 직후에, 오늘 공부할 내용에서 가장 중요한 핵심 요점 3가지를 글머리 기호(•) 또는 순서 있는 번호(1., 2., 3.)를 활용하여 한눈에 들어오도록 3줄 요약 리스트로 먼저 제시한 후 본론을 시작하십시오.
2. [시각적 강약 조절 (강조)]: 단조로운 줄글 구성을 배제하고, 핵심 용어나 중요한 문장은 반드시 마크다운 굵게(**텍스트**) 기호로 감싸 시각적 포인트를 주어 독자가 중요한 내용을 한눈에 파악할 수 있도록 '강약'을 확실하게 구현하십시오.
3. [인용구 및 정리 블록 활용]: 주요 개념의 정의나 핵심 요약은 마크다운 인용구(> ) 형식을 적극 활용하여 본문과 시각적으로 구분하여 정리해 주십시오.
4. [구조화된 정보 제공]: 주요 개념 비교나 분류가 필요한 경우, 적극적으로 표(Table) 형식을 사용하여 깔끔하게 정보를 전달하십시오. 이때 워드프레스용 표는 전문적이고 상세한 분류 기준을 다룰 수 있도록 3~4개 열(Column)로 구성된 깊이 있는 상세 정보 표(Table) 형태로 작성하십시오.
5. [마이크로 문단 및 충분한 여백]: 글을 쓸 때 1~2개 문장 단위로 매우 짧게 단락을 나누고, 문단과 문단 사이에는 빈 줄을 2줄 이상(엔터 3번) 넣어 모바일 화면에서 읽기 편리하도록 충분한 여백(가독성 높은 숨구멍)을 확보하십시오.
6. [마크다운 문법 적용]: 대제목은 `#`, 중제목은 `##`, 소제목은 `###`을 명확하게 붙여서 구조적인 문서를 만드십시오. (이 기호들은 자동 변환되므로 반드시 작성해 주셔야 합니다.)
7. [포스팅 하단 태그 삽입]: 모든 버전의 본문 가장 최하단(본문 및 퀴즈 내용이 완전히 끝난 후)에는 다음 해시태그를 공백 문자로 구분하여 반드시 그대로 첨부하십시오. 추가로 본문 주제와 관련된 개별 핵심 태그를 2~3개 더 추가해 주십시오.
{hashtag_str}

[요청 주제/키워드]
{content}

[온라인 검색 참고 자료]
{online_context if online_context else "자체 지식을 활용해 상세히 작성하세요"}

[출력 요구사항 및 포맷]
# [워드프레스용 제목]
(본문은 아주 따뜻하고 친근하며 다정한 어조로 작성해 주세요. 요약 리스트(•)와 단락 구분, 깔끔한 소제목을 적극적으로 활용하여 가독성 있게 정리해 주세요. 본문과 퀴즈 사이에 빈칸 줄바꿈(엔터)을 2회 이상 넣고, "[이곳에 학습 퀴즈 관련 이미지가 들어갈 자리입니다]" 라는 안내 문구를 가독성 있게 표기하여 확실하게 물리적인 간격을 넓혀 주세요. 그 후 공부한 내용을 점검할 수 있도록 4지선다형 객관식 퀴즈 1문항과 정답 및 해설을 추가해 주세요. 마지막에 독자들을 응원하는 다정한 멘트와 해시태그를 작성해 주세요.)
"""

            blogger_prompt = f"""당신은 자격증 시험 전문 교육 블로거입니다.
아래 제공된 '청소년지도사' 관련 학습 텍스트 및 온라인 검색 참고자료를 바탕으로 구글 블로거(Blogger)에 업로드할 학습 요약 글을 작성하세요.

[중요 지시사항]
- 반드시 처음부터 끝까지 완전하고 완벽한 '한국어'로만 작성하십시오.
- 영어(sớm, also, juga 등), 베트남어, 태국어 등 외래어 토큰이나 타국어 단어가 단 한 단어도 섞여서는 안 됩니다. 
- 한자(漢字) 역시 가급적 한글로 순화하고 한글로만 작성하십시오.
- AI 임의의 다국어 번역 혼동이나 깨진 토큰 사용을 철저히 금지합니다.

[가독성 극대화 및 레이아웃 지시사항 (네이버 블로그 스타일 가독성)]
1. [핵심 요약 3가지 우선 배치]: 본문 도입부(서론) 직후에, 오늘 공부할 내용에서 가장 중요한 핵심 요점 3가지를 글머리 기호(•) 또는 순서 있는 번호(1., 2., 3.)를 활용하여 한눈에 들어오도록 3줄 요약 리스트로 먼저 제시한 후 본론을 시작하십시오.
2. [시각적 강약 조절 (강조)]: 단조로운 줄글 구성을 배제하고, 핵심 용어나 중요한 문장은 반드시 마크다운 굵게(**텍스트**) 기호로 감싸 시각적 포인트를 주어 독자가 중요한 내용을 한눈에 파악할 수 있도록 '강약'을 확실하게 구현하십시오.
3. [인용구 및 정리 블록 활용]: 주요 개념의 정의나 핵심 요약은 마크다운 인용구(> ) 형식을 적극 활용하여 본문과 시각적으로 구분하여 정리해 주십시오.
4. [구조화된 정보 제공]: 주요 개념 비교나 분류가 필요한 경우, 적극적으로 표(Table) 형식을 사용하여 깔끔하게 정보를 전달하십시오. 이때 구글 블로거용 표는 모바일 가독성을 극대화하기 위해 핵심 요약 위주의 간결한 2개 열(Column)로 구성된 직관적인 비교 표 형태로 작성하십시오.
5. [마이크로 문단 및 충분한 여백]: 글을 쓸 때 1~2개 문장 단위로 매우 짧게 단락을 나누고, 문단과 문단 사이에는 빈 줄을 2줄 이상(엔터 3번) 넣어 모바일 화면에서 읽기 편리하도록 충분한 여백(가독성 높은 숨구멍)을 확보하십시오.
6. [마크다운 문법 적용]: 대제목은 `#`, 중제목은 `##`, 소제목은 `###`을 명확하게 붙여서 구조적인 문서를 만드십시오. (이 기호들은 자동 변환되므로 반드시 작성해 주셔야 합니다.)
7. [포스팅 하단 태그 삽입]: 모든 버전의 본문 가장 최하단(본문 및 퀴즈 내용이 완전히 끝난 후)에는 다음 해시태그를 공백 문자로 구분하여 반드시 그대로 첨부하십시오. 추가로 본문 주제와 관련된 개별 핵심 태그를 2~3개 더 추가해 주십시오.
{hashtag_str}

[요청 주제/키워드]
{content}

[온라인 검색 참고 자료]
{online_context if online_context else "자체 지식을 활용해 상세히 작성하세요"}

[출력 요구사항 및 포맷]
# [블로거용 제목]
(본문은 담담하고 핵심 중심의 간결하며 정돈된 전문적인 어조로 작성해 주세요. 핵심 개념 설명은 표(Table) 또는 구조화된 도표 형식을 적극 활용하여 한눈에 정리되게 작성해 주시고, 요약 리스트(•)를 풍부하게 배치하여 핵심만 빠르게 읽을 수 있도록 해 주세요. 본문과 퀴즈 사이에 빈칸 줄바꿈(엔터)을 2회 이상 넣고, "[이곳에 학습 퀴즈 관련 이미지가 들어갈 자리입니다]" 라는 안내 문구를 가독성 있게 표기하여 확실하게 물리적인 간격을 넓혀 주세요. 그 후 공부한 내용을 직관적으로 점검할 수 있도록 O/X 퀴즈 2문항을 작성해 주세요. 단, O/X 퀴즈의 정답과 해설은 개별 문제 바로 옆에 작성하여 미리 노출하지 말고, 반드시 문제 전체가 끝난 후 본문 최하단(해시태그 바로 위)에 '[정답 및 해설]' 영역을 별도로 만들어 분리 기입하십시오. 마지막에 해시태그를 추가해 주세요.)
"""
        elif category == "mindset":
            prompt = f"""당신은 마음 치유 및 심리 전문 블로거입니다.
아래 키워드와 참고자료를 바탕으로 워드프레스와 구글 블로거에 각각 업로드할 두 가지 버전의 글을 작성하세요.

[중요 지시사항]
1. [마이크로 문단 및 충분한 여백 (네이버 블로그 스타일)]: 문장은 1~2개 문장 단위로 매우 짧게 단락을 나누어 작성하고, 문단과 문단 사이에는 반드시 빈 줄을 2줄 이상(엔터 3번) 띄워서 모바일 가독성을 극대화하십시오.
2. [시각적 강약 조절 (강조)]: 글 전체에 어조의 강약이 느껴지도록, 가벼운 설명과 강조해야 할 핵심 인사이트 및 마음에 와닿는 구절을 명확히 구분하십시오. 특히 핵심 단어나 핵심이 되는 한 줄 문장은 마크다운 굵게(**텍스트**)로 감싸 포인트를 주십시오.
3. [인용구 및 마크다운 헤더 활용]: 에세이 중간에 깊은 통찰을 주는 문장이나 마음을 치유하는 한마디는 마크다운 인용구(> ) 형식을 활용해 독자의 시선을 사로잡고, 각 단락의 주제는 `##` 또는 `###` 마크다운 헤더로 명확히 표시하여 글에 뼈대와 깊이를 주십시오.
4. [포스팅 하단 태그 삽입] 모든 버전의 본문 가장 최하단(응원 멘트나 본문 내용이 완전히 끝난 후)에는 해당 포스팅 내용과 관련이 깊은 핵심 단어들을 해시태그 형식(예: #마인드셋 #심리테라피 등)으로 5~10개 반드시 첨부하십시오.

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
(본문은 정돈되고 전문적인 에세이 톤으로 작성해 주세요. 밋밋하고 평평한 문장이 되지 않도록 깊은 울림을 주는 통찰 문장이나 핵심 메시지는 마크다운 굵게 기호(**강조**)를 사용해 강약을 주고, 주요 생각이나 질문은 인용구 기호(> )를 사용해 시각적으로 도드라지게 하십시오. 본문 단락에는 소제목(##, ###)을 붙여 구조화하고, 마지막에 해시태그를 추가해 주세요.)
"""
        elif category == "recipe":
            prompt = f"""당신은 요리 및 집밥 전문 파워 블로거입니다.
아래 제공된 정보 및 레시피 키워드를 바탕으로 워드프레스(WordPress)와 구글 블로거(Blogger)에 각각 업로드할 두 가지 버전의 글을 작성하세요.

[중요 지시사항]
1. 두 블로그는 완전히 다른 독자층을 대상으로 독립적으로 운영되므로, 두 버전의 문체와 내용 구성이 완전히 다르게(차별화되게) 작성되어야 합니다. 동일한 내용을 단순히 다듬기만 한 형태여서는 안 됩니다.
2. 한 블로그 내용에 여러 요리를 함께 나열하지 마십시오. 반드시 제시된 주제/키워드 중 단 '하나'의 요리(단일 요리)만을 선정하여 그 요리 하나만 깊고 상세하게 설명해야 합니다. (여러 요리나 다른 반찬 정보가 입력값에 섞여 있더라도, 단 하나의 핵심 요리만 집중적으로 파고드십시오.)
3. 본문 내에 절대로 '자가진단', '퀴즈', '자가진단 QUIZ' 또는 학습용 질문/평가 문제를 포함하지 마십시오.
4. [마이크로 문단 및 충분한 여백 (네이버 블로그 스타일)]: 글을 쓸 때 1~2개 문장 단위로 매우 짧게 단락을 나누고, 문단과 문단 사이에는 반드시 빈 줄을 2줄 이상(엔터 3번) 띄워서 모바일 화면에서 쾌적하게 보이도록 충분한 숨구멍 여백을 확보하십시오.
5. [시각적 강약 조절 (강조와 구조화)]:
   - 각 요리 과정의 핵심 비법이나 주요 팁은 마크다운 굵게(**텍스트**)와 인용구(> ) 기호를 적극적으로 사용하여 시각적 강약을 뚜렷하게 구분해 주십시오.
   - 대제목은 `#`, 중제목은 `##`, 소제목은 `###`을 명확하게 표시하십시오.
   - 필요한 재료 목록은 반드시 표(Table) 또는 명확한 글머리 기호 리스트 형식으로 깔끔하게 정리해 한눈에 들어오게 제시하십시오.
6. [포스팅 하단 태그 삽입] 모든 버전의 본문 가장 최하단(본문 내용이 완전히 끝난 후)에는 해당 요리 레시피와 관련이 깊은 핵심 단어들을 해시태그 형식(예: #요리레시피 #집밥반찬 등)으로 5~10개 반드시 첨부하십시오.

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
(본문은 깔끔하고 명확하며 군더더기 없는 '구조적이고 전문적인 레시피 카드 어조'로 작성해 주세요. 불필요한 일상 이야기나 감정 묘사는 일체 배제하고, 필요한 재료 목록(정량 표기 포함)을 표(Table) 또는 명확한 리스트 형식으로 정리해 제시하십시오. 조리 단계(Step-by-step)를 시간순으로 명확하고 간결하게 기입하되, 각 단계와 핵심 팁에는 적절히 마크다운 소제목(##, ###)과 강조 기호(**강조**) 및 인용구 기호(> )를 꼭 사용하여 시각적인 강약과 가독성을 확실하게 확보하십시오. 마지막에 해시태그를 추가해 주세요.)
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
        if is_study_category:
            print("[INFO] Generating WordPress version content (fallback)...")
            wp_res = ask_llm(ollama_url, model, wp_prompt, gemini_api_key)
            if not wp_res:
                print("[ERROR] Failed to generate WordPress content from LLM.")
                sys.exit(1)
                
            print("[INFO] Generating Blogger version content (fallback)...")
            blogger_res = ask_llm(ollama_url, model, blogger_prompt, gemini_api_key)
            if not blogger_res:
                print("[ERROR] Failed to generate Blogger content from LLM.")
                sys.exit(1)
                
            result = f"========== WORDPRESS VERSION ==========\n\n{wp_res}\n\n========== BLOGGER VERSION ==========\n\n{blogger_res}"
        else:
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
