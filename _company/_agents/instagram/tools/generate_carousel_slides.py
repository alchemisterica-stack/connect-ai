#!/usr/bin/env python3
"""
Instagram Carousel Card News Generator
========================================
Generates 5 premium 1080×1080 slides following the emotion curve:
  Hook → Empathy → Shift → Core Message → CTA

Uses:
  - Pretendard fonts (Bold / SemiBold / Regular)
  - Pollinations AI for background image generation
  - Glassmorphism card overlay with rounded corners
  - Auto-wrapped Korean text with text shadows
"""

import os
import sys
import io
import time
import json
import urllib.parse
import requests
from PIL import Image, ImageDraw, ImageFont, ImageFilter

# ---------------------------------------------------------------------------
# Paths
# ---------------------------------------------------------------------------
OUTPUT_DIR = r"C:\Users\User\my-ai-office\temp_slides"
FONT_DIR = r"C:\Users\User\my-ai-office\assets\fonts"
FONT_BOLD = os.path.join(FONT_DIR, "Pretendard-Bold.otf")
FONT_SEMI = os.path.join(FONT_DIR, "Pretendard-SemiBold.otf")
FONT_REGULAR = os.path.join(FONT_DIR, "Pretendard-Regular.otf")

# ---------------------------------------------------------------------------
# Brand colours
# ---------------------------------------------------------------------------
BRIGHT_TEAL = (0, 191, 165)       # #00BFA5
DEEP_SKY_BLUE = (0, 122, 204)     # #007ACC
SOFT_PEACH = (255, 204, 153)       # #FFCC99
VIBRANT_ORANGE = (255, 140, 0)     # #FF8C00

# ---------------------------------------------------------------------------
# Slide contents & style (5-slide emotion curve)
# ---------------------------------------------------------------------------
SLIDES_INFO = [
    {   # Slide 1 – Hook
        "prompt": (
            "Beautiful vibrant watercolor digital illustration of a glowing candle, "
            "soft warm cozy lighting, pastel cream and beige wash background, "
            "dreamlike cozy room atmosphere, highly detailed, "
            "absolutely no text, no letters"
        ),
        "title": "남들의 기준에 너를 끼워 맞추지 마.",
        "subtitle": "마음이 지친 당신을 위한 자존감 처방전",
        "bg_color": (245, 242, 235),
        "text_color": (44, 44, 44),
        "card_bg": (255, 255, 255, 200),
    },
    {   # Slide 2 – Empathy
        "prompt": (
            "Stunning cozy 3D clay rendering of a calm room, deep blue starry "
            "night sky outside a big window, warm glowing lamp light inside, "
            "dreamlike psychological mindset theme, highly detailed, no text"
        ),
        "title": "오늘도 다른 사람 눈치 보느라 정작 '나'의 목소리는 외면하지 않았나요?",
        "subtitle": "",
        "bg_color": (34, 43, 54),
        "text_color": (255, 255, 255),
        "card_bg": (20, 30, 40, 180),
    },
    {   # Slide 3 – Shift
        "prompt": (
            "Whimsical watercolor painting of a sunlit cozy window sill, "
            "vibrant green potted plants, casting beautiful warm soft leaf "
            "shadows on the wall, mint green tones, sunny uplifting morning "
            "vibe, highly detailed, no text"
        ),
        "title": "하루 한 번, 거울을 보고 나에게 건네는 말 한마디면 충분합니다.",
        "subtitle": "\"오늘도 버텨줘서 고마워, 넌 이미 잘하고 있어.\"",
        "bg_color": (224, 240, 230),
        "text_color": (44, 53, 44),
        "card_bg": (255, 255, 255, 200),
    },
    {   # Slide 4 – Core Message
        "prompt": (
            "Magical dreamlike digital art of soft golden-orange clouds, "
            "sparkling stardust sky, comforting glowing warm aura, peaceful "
            "comforting fantasy background, highly detailed, no text"
        ),
        "title": "실수해도 괜찮아. 완벽하지 않아도 너는 그 자체로 가장 빛나는 존재야.",
        "subtitle": "",
        "bg_color": (255, 242, 215),
        "text_color": (60, 44, 20),
        "card_bg": (255, 255, 255, 200),
    },
    {   # Slide 5 – CTA
        "prompt": (
            "Cute 3D pastel clay art illustration of an instagram bookmark "
            "and heart floating in a warm cozy bedroom space, soft volumetric "
            "lighting, vibrant pink and peach tones, cheerful aesthetic, "
            "highly detailed, no text"
        ),
        "title": "나를 더 사랑하고 싶다면? 지금 이 글을 [저장]하고, 나를 아끼는 하루를 시작해 보세요!",
        "subtitle": "👉 @rolling.s.cong01 팔로우하고 매일 위로받기",
        "bg_color": (245, 242, 235),
        "text_color": (44, 44, 44),
        "card_bg": (255, 255, 255, 200),
    },
]

# ---------------------------------------------------------------------------
# Font helpers
# ---------------------------------------------------------------------------

def load_fonts():
    """Load Pretendard fonts; fall back to default if missing."""
    try:
        title_font = ImageFont.truetype(FONT_BOLD, 54)
        sub_font = ImageFont.truetype(FONT_SEMI, 36)
        brand_font = ImageFont.truetype(FONT_REGULAR, 28)
        print("[INFO] Pretendard fonts loaded successfully.")
    except Exception as exc:
        print(f"[WARN] Could not load Pretendard fonts ({exc}). Using defaults.")
        title_font = ImageFont.load_default()
        sub_font = ImageFont.load_default()
        brand_font = ImageFont.load_default()
    return title_font, sub_font, brand_font

# ---------------------------------------------------------------------------
# Text auto-wrap
# ---------------------------------------------------------------------------

def auto_wrap(text, chars_per_line=16):
    """
    Break *text* into lines of roughly *chars_per_line* Korean characters.

    Rules:
    - Explicit newlines (``\\n``) are always honoured.
    - Empty lines are preserved (to keep intentional paragraph spacing).
    - For each logical paragraph the text is split on spaces first; if any
      single token is longer than *chars_per_line* it is hard-wrapped at
      that width.
    """
    result_lines = []
    for paragraph in text.split("\n"):
        if not paragraph.strip():
            result_lines.append("")
            continue

        tokens = paragraph.split(" ")
        current_line = ""

        for token in tokens:
            # If the token itself is wider than one line, hard-wrap it
            while len(token) > chars_per_line:
                piece = token[:chars_per_line]
                token = token[chars_per_line:]
                if current_line:
                    result_lines.append(current_line)
                    current_line = ""
                result_lines.append(piece)

            candidate = f"{current_line} {token}".strip() if current_line else token
            if len(candidate) <= chars_per_line:
                current_line = candidate
            else:
                result_lines.append(current_line)
                current_line = token

        if current_line:
            result_lines.append(current_line)

    return result_lines

# ---------------------------------------------------------------------------
# Background generation via Pollinations AI
# ---------------------------------------------------------------------------

def fetch_pollinations_background(prompt, retries=3, wait=3):
    """
    Download an AI-generated 1080×1080 background from Pollinations.
    Retries up to *retries* times with *wait*-second pauses.
    Returns a PIL Image or None on total failure.
    """
    seed = random.randint(0, 99999999)
    encoded = urllib.parse.quote(prompt)
    url = (
        f"https://image.pollinations.ai/prompt/{encoded}"
        f"?width=1080&height=1080&nologo=true&seed={seed}"
    )

    for attempt in range(1, retries + 1):
        try:
            print(f"  [AI-BG] Attempt {attempt}/{retries} — requesting image…")
            resp = requests.get(url, timeout=60)
            if resp.status_code == 200 and len(resp.content) > 1000:
                img = Image.open(io.BytesIO(resp.content))
                print(f"  [AI-BG] Success on attempt {attempt}.")
                return img.convert("RGBA")
            else:
                print(
                    f"  [AI-BG] Unexpected response "
                    f"(status={resp.status_code}, bytes={len(resp.content)})"
                )
        except Exception as exc:
            print(f"  [AI-BG] Error: {exc}")

        if attempt < retries:
            print(f"  [AI-BG] Waiting {wait}s before retry…")
            time.sleep(wait)

    print("  [AI-BG] All retries exhausted — returning None.")
    return None

# ---------------------------------------------------------------------------
# Drawing helpers
# ---------------------------------------------------------------------------

def draw_text_shadow(draw, position, text, font, fill, shadow_color=(0, 0, 0, 90),
                     offset=(2, 2)):
    """Draw text with a shadow for readability on varied backgrounds."""
    sx, sy = position[0] + offset[0], position[1] + offset[1]
    draw.text((sx, sy), text, font=font, fill=shadow_color)
    draw.text(position, text, font=font, fill=fill)


def draw_rounded_rect(draw, box, radius, fill, outline=None, outline_width=1):
    """Draw a rounded rectangle with optional outline."""
    draw.rounded_rectangle(box, radius=radius, fill=fill,
                           outline=outline, width=outline_width)

# ---------------------------------------------------------------------------
# Main slide creation
# ---------------------------------------------------------------------------

def create_card_slide(slide_idx, info, title_font, sub_font, brand_font):
    """Create one 1080×1080 slide and return its file path."""
    print(f"\n[SLIDE {slide_idx + 1}] Generating…")

    # ---- Background ---------------------------------------------------
    bg_img = fetch_pollinations_background(info["prompt"])
    if bg_img is None:
        print(f"  [FALLBACK] Using solid colour {info['bg_color']}")
        bg_img = Image.new("RGBA", (1080, 1080), info["bg_color"] + (255,))
    bg_img = bg_img.resize((1080, 1080), Image.Resampling.LANCZOS)

    # Slight Gaussian blur so the text pops
    bg_rgb = bg_img.convert("RGB").filter(ImageFilter.GaussianBlur(radius=6))
    bg_img = bg_rgb.convert("RGBA")

    # ---- Glassmorphism card overlay -----------------------------------
    overlay = Image.new("RGBA", (1080, 1080), (0, 0, 0, 0))
    ov_draw = ImageDraw.Draw(overlay)

    card_margin = 80
    card_box = [card_margin, card_margin, 1080 - card_margin, 1080 - card_margin]
    card_bg = info["card_bg"]  # RGBA tuple with alpha ~180-200
    border_color = (255, 255, 255, 100)

    draw_rounded_rect(ov_draw, card_box, radius=30, fill=card_bg,
                      outline=border_color, outline_width=2)

    # Composite card onto background
    img = Image.alpha_composite(bg_img, overlay)
    draw = ImageDraw.Draw(img)

    # ---- Prepare text -------------------------------------------------
    title_lines = auto_wrap(info["title"], chars_per_line=16)
    sub_lines = auto_wrap(info["subtitle"], chars_per_line=22) if info["subtitle"] else []

    title_line_h = int(54 * 1.5)  # font_size * 1.5 spacing
    sub_line_h = int(36 * 1.5)
    gap_between = 40  # gap between title block and subtitle block
    brand_line_h = int(28 * 1.5)

    # Total height of the text block (title + gap + subtitle)
    total_text_h = len(title_lines) * title_line_h
    if sub_lines:
        total_text_h += gap_between + len(sub_lines) * sub_line_h

    # Vertical centering inside card area (leave room for brand at bottom)
    card_top = card_margin
    card_bottom = 1080 - card_margin
    usable_h = card_bottom - card_top - brand_line_h - 30  # reserve space for brand
    y_start = card_top + max(0, (usable_h - total_text_h) // 2)

    text_color = info["text_color"]
    shadow_color = (0, 0, 0, 90) if sum(text_color[:3]) > 380 else (0, 0, 0, 120)

    # ---- Draw title ---------------------------------------------------
    y = y_start
    for line in title_lines:
        bbox = draw.textbbox((0, 0), line, font=title_font)
        tw = bbox[2] - bbox[0]
        x = (1080 - tw) // 2
        draw_text_shadow(draw, (x, y), line, title_font, fill=text_color,
                         shadow_color=shadow_color)
        y += title_line_h

    # ---- Draw subtitle -----------------------------------------------
    if sub_lines:
        y += gap_between
        for line in sub_lines:
            bbox = draw.textbbox((0, 0), line, font=sub_font)
            sw = bbox[2] - bbox[0]
            x = (1080 - sw) // 2

            # Use rose/gold colour for quotation lines
            if line.startswith('"') or line.startswith('\u201c'):
                line_color = (255, 100, 120)
            elif slide_idx == 4:
                # CTA slide: orange accent for subtitle
                line_color = VIBRANT_ORANGE
            else:
                line_color = text_color

            draw_text_shadow(draw, (x, y), line, sub_font, fill=line_color,
                             shadow_color=shadow_color)
            y += sub_line_h

    # ---- Branding at bottom -------------------------------------------
    brand_text = "@rolling.s.cong01"
    bbox = draw.textbbox((0, 0), brand_text, font=brand_font)
    bw = bbox[2] - bbox[0]
    brand_y = card_bottom - brand_line_h - 16
    brand_x = (1080 - bw) // 2
    draw_text_shadow(draw, (brand_x, brand_y), brand_text, brand_font,
                     fill=text_color, shadow_color=(0, 0, 0, 60), offset=(1, 1))

    # ---- Save ---------------------------------------------------------
    os.makedirs(OUTPUT_DIR, exist_ok=True)
    slide_path = os.path.join(OUTPUT_DIR, f"slide_{slide_idx + 1}.png")
    img.convert("RGB").save(slide_path, "PNG")
    print(f"[SUCCESS] Saved slide {slide_idx + 1} → {slide_path}")
    return slide_path


def main():
    print("=" * 60)
    print(" Instagram Carousel Card News — Slide Generator")
    print("=" * 60)

    # Load content draft if exists
    draft_path = os.path.join(OUTPUT_DIR, "current_draft.json")
    global SLIDES_INFO
    if os.path.exists(draft_path):
        try:
            with open(draft_path, "r", encoding="utf-8") as f:
                draft_data = json.load(f)
            slides_draft = draft_data.get("slideshow", [])
            for idx, slide_item in enumerate(slides_draft):
                if idx < len(SLIDES_INFO):
                    SLIDES_INFO[idx]["title"] = slide_item["title"]
                    SLIDES_INFO[idx]["subtitle"] = slide_item["subtitle"]
            print(f"[INFO] Loaded draft content. Theme: {draft_data.get('theme_name')}")
        except Exception as e:
            print(f"[WARN] Failed to load content draft: {e}")

    title_font, sub_font, brand_font = load_fonts()

    paths = []
    for idx, info in enumerate(SLIDES_INFO):
        p = create_card_slide(idx, info, title_font, sub_font, brand_font)
        paths.append(p)

    print("\n" + "=" * 60)
    print("[DONE] All 5 slides generated successfully!")
    print(f"Output directory: {OUTPUT_DIR}")
    for p in paths:
        print(f"  • {os.path.basename(p)}")
    print("=" * 60)


if __name__ == "__main__":
    main()
