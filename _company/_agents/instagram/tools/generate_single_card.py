#!/usr/bin/env python3
"""
generate_single_card.py — 1장짜리 명상 카드 이미지 생성기

콩콩캔디 브랜드 가이드라인에 맞춰 프리미엄 감성 카드를 생성합니다.
- 1080x1080 (피드용 정사각)
- 1080x1920 (릴스용 세로)  두 가지를 동시에 출력합니다.

Usage:
    python generate_single_card.py
    python generate_single_card.py --title "완벽하지 않아도, 괜찮아." --subtitle "오늘 하루도 버텨준 네가 대견해"
    python generate_single_card.py --theme dark
"""
import os
import sys
import io
import time
import json
import argparse
import urllib.parse
import requests
from PIL import Image, ImageDraw, ImageFont, ImageFilter, ImageColor

# ─── Paths ───────────────────────────────────────────────────────────
HERE = os.path.dirname(os.path.abspath(__file__))
FONTS_DIR = r"C:\Users\User\my-ai-office\assets\fonts"
OUTPUT_DIR = r"C:\Users\User\my-ai-office\temp_slides"

FONT_BOLD = os.path.join(FONTS_DIR, "Pretendard-Bold.otf")
FONT_SEMI = os.path.join(FONTS_DIR, "Pretendard-SemiBold.otf")
FONT_REG = os.path.join(FONTS_DIR, "Pretendard-Regular.otf")

# ─── Brand Colors ────────────────────────────────────────────────────
BRAND = {
    "teal":   "#00BFA5",
    "blue":   "#007ACC",
    "peach":  "#FFCC99",
    "orange": "#FF8C00",
    "gray":   "#E0E0E0",
    "dark":   "#333333",
    "white":  "#FFFFFF",
}

# ─── Theme Presets ───────────────────────────────────────────────────
THEMES = {
    "warm": {
        "bg_prompt": "Beautiful soft watercolor painting of a cozy morning scene with warm golden sunlight streaming through sheer curtains, a steaming cup of coffee on a wooden windowsill, soft pastel cream and beige tones, dreamy peaceful atmosphere, highly detailed, absolutely no text no letters no words",
        "bg_fallback": (245, 240, 230),
        "card_bg": (255, 255, 255, 195),
        "text_color": (51, 51, 51),
        "accent_color": (0, 122, 204),  # Deep Sky Blue
        "border_color": (255, 255, 255, 120),
    },
    "dark": {
        "bg_prompt": "Stunning atmospheric digital art of a calm deep blue night sky with soft glowing stars and a crescent moon over a peaceful quiet lake reflection, dark navy and indigo tones, serene contemplative mood, highly detailed, absolutely no text no letters no words",
        "bg_fallback": (25, 32, 48),
        "card_bg": (15, 20, 35, 185),
        "text_color": (240, 240, 245),
        "accent_color": (0, 191, 165),  # Bright Teal
        "border_color": (255, 255, 255, 60),
    },
    "nature": {
        "bg_prompt": "Whimsical watercolor illustration of lush green potted plants on a bright sunlit windowsill, soft morning light casting beautiful leaf shadows, fresh mint green and sage tones, uplifting serene botanical atmosphere, highly detailed, absolutely no text no letters no words",
        "bg_fallback": (220, 238, 225),
        "card_bg": (255, 255, 255, 195),
        "text_color": (44, 62, 44),
        "accent_color": (0, 191, 165),  # Bright Teal
        "border_color": (255, 255, 255, 100),
    },
    "sunset": {
        "bg_prompt": "Magical dreamlike digital painting of soft golden orange clouds at sunset with sparkling warm stardust, peaceful comforting fantasy sky in coral and amber tones, highly detailed, absolutely no text no letters no words",
        "bg_fallback": (255, 235, 210),
        "card_bg": (255, 255, 255, 195),
        "text_color": (70, 45, 20),
        "accent_color": (255, 140, 0),  # Vibrant Orange
        "border_color": (255, 255, 255, 110),
    },
}

# ─── Default Content ─────────────────────────────────────────────────
DEFAULT_TITLE = "완벽하지 않아도,\n괜찮아."
DEFAULT_SUBTITLE = "오늘 하루도 버텨준 네가 대견해"

# ─── AI Background Generation ───────────────────────────────────────
def generate_background(prompt, size=(1080, 1080), fallback_color=(240, 240, 240)):
    """Pollinations AI로 배경 이미지를 생성합니다. 실패 시 단색 폴백."""
    encoded = urllib.parse.quote(prompt)
    url = f"https://image.pollinations.ai/prompt/{encoded}?width={size[0]}&height={size[1]}&nologo=true"

    for attempt in range(3):
        try:
            print(f"  [BG] Attempt {attempt+1}/3: Generating background...")
            r = requests.get(url, timeout=60)
            if r.status_code == 200 and len(r.content) > 5000:
                img = Image.open(io.BytesIO(r.content))
                print(f"  [BG] Success! ({len(r.content) // 1024} KB)")
                return img.resize(size, Image.Resampling.LANCZOS)
        except Exception as e:
            print(f"  [BG] Attempt {attempt+1} failed: {e}")
        time.sleep(3)

    print(f"  [BG] All attempts failed. Using solid color fallback.")
    return Image.new("RGB", size, fallback_color)


# ─── Text Utilities ──────────────────────────────────────────────────
def wrap_text(text, font, max_width, draw):
    """텍스트를 max_width에 맞게 자동 줄바꿈합니다."""
    lines = []
    for paragraph in text.split("\n"):
        if not paragraph.strip():
            lines.append("")
            continue
        words = list(paragraph)  # 한글은 글자 단위로 잘라야 함
        current = ""
        for ch in words:
            test = current + ch
            bbox = draw.textbbox((0, 0), test, font=font)
            if bbox[2] - bbox[0] > max_width and current:
                lines.append(current)
                current = ch
            else:
                current = test
        if current:
            lines.append(current)
    return lines


def draw_text_with_shadow(draw, pos, text, font, fill, shadow_color=(0, 0, 0, 60), offset=2):
    """텍스트에 그림자를 넣어 가독성을 높입니다."""
    x, y = pos
    # Shadow
    draw.text((x + offset, y + offset), text, font=font, fill=shadow_color)
    # Main text
    draw.text((x, y), text, font=font, fill=fill)


def draw_centered_text_block(draw, lines, font, start_y, canvas_width, fill, line_spacing_factor=1.5, shadow=True):
    """여러 줄의 텍스트를 중앙 정렬로 그립니다."""
    y = start_y
    for line in lines:
        if not line:
            y += int(font.size * 0.8)
            continue
        bbox = draw.textbbox((0, 0), line, font=font)
        w = bbox[2] - bbox[0]
        h = bbox[3] - bbox[1]
        x = (canvas_width - w) // 2
        if shadow:
            draw_text_with_shadow(draw, (x, y), line, font, fill)
        else:
            draw.text((x, y), line, font=font, fill=fill)
        y += int(h * line_spacing_factor)
    return y


# ─── Card Generation ─────────────────────────────────────────────────
def load_fonts():
    """Pretendard 폰트를 로드합니다. 실패 시 맑은 고딕 폴백."""
    try:
        title_font = ImageFont.truetype(FONT_BOLD, 58)
        sub_font = ImageFont.truetype(FONT_SEMI, 34)
        brand_font = ImageFont.truetype(FONT_REG, 26)
        print("[FONT] Pretendard loaded successfully.")
        return title_font, sub_font, brand_font
    except Exception as e:
        print(f"[FONT] Pretendard load failed ({e}), falling back to malgun.ttf")
        fallback = r"C:\Windows\Fonts\malgun.ttf"
        return (
            ImageFont.truetype(fallback, 58),
            ImageFont.truetype(fallback, 34),
            ImageFont.truetype(fallback, 26),
        )


def create_single_card(title, subtitle, theme_name="warm"):
    """1장짜리 명상 카드를 생성합니다. 피드용(1080x1080) + 릴스용(1080x1920) 동시 출력."""

    theme = THEMES.get(theme_name, THEMES["warm"])
    title_font, sub_font, brand_font = load_fonts()

    print(f"\n[CARD] Generating '{theme_name}' theme single card...")
    print(f"  Title: {title.replace(chr(10), ' / ')}")
    print(f"  Subtitle: {subtitle}")

    # ── 1) Generate background ──
    bg = generate_background(theme["bg_prompt"], (1080, 1080), theme["bg_fallback"])

    # ── 2) Create glassmorphism overlay ──
    overlay = Image.new("RGBA", (1080, 1080), (0, 0, 0, 0))
    draw_overlay = ImageDraw.Draw(overlay)

    margin = 80
    card_box = [margin, margin, 1080 - margin, 1080 - margin]
    draw_overlay.rounded_rectangle(
        card_box,
        radius=30,
        fill=theme["card_bg"],
        outline=theme["border_color"],
        width=2,
    )

    # ── 3) Compose background + card ──
    img = Image.alpha_composite(bg.convert("RGBA"), overlay)
    draw = ImageDraw.Draw(img)

    # ── 4) Render title text ──
    max_text_width = 1080 - margin * 2 - 80  # card내부 여백 추가
    title_lines = wrap_text(title, title_font, max_text_width, draw)

    # 텍스트 전체 높이 계산 → 수직 중앙 배치
    title_line_h = int(58 * 1.5)
    sub_line_h = int(34 * 1.5)
    total_title_h = len(title_lines) * title_line_h
    total_sub_h = sub_line_h if subtitle else 0
    gap = 40 if subtitle else 0
    total_h = total_title_h + gap + total_sub_h
    start_y = (1080 - total_h) // 2 - 30  # 약간 위로 올림 (브랜딩 공간 확보)

    y = draw_centered_text_block(
        draw, title_lines, title_font, start_y, 1080,
        fill=theme["text_color"], line_spacing_factor=1.5
    )

    # ── 5) Render subtitle ──
    if subtitle:
        y += 30
        sub_lines = wrap_text(subtitle, sub_font, max_text_width, draw)
        draw_centered_text_block(
            draw, sub_lines, sub_font, y, 1080,
            fill=theme["accent_color"], line_spacing_factor=1.4
        )

    # ── 6) Branding ──
    brand_text = "@rolling.s.cong01"
    bbox = draw.textbbox((0, 0), brand_text, font=brand_font)
    bw = bbox[2] - bbox[0]
    # 살짝 투명하게
    brand_color = tuple(list(theme["text_color"][:3]) + [180]) if len(theme["text_color"]) < 4 else theme["text_color"]
    draw.text(((1080 - bw) // 2, 940), brand_text, font=brand_font, fill=brand_color[:3])

    # ── 7) Save feed version (1080x1080) ──
    os.makedirs(OUTPUT_DIR, exist_ok=True)
    feed_path = os.path.join(OUTPUT_DIR, "single_card_feed.png")
    img.convert("RGB").save(feed_path, "PNG", quality=95)
    print(f"[SAVED] Feed card (1080x1080): {feed_path}")

    # ── 8) Create & save reels version (1080x1920) ──
    reels_img = create_reels_version(img, bg, theme)
    reels_path = os.path.join(OUTPUT_DIR, "single_card_reels.png")
    reels_img.convert("RGB").save(reels_path, "PNG", quality=95)
    print(f"[SAVED] Reels card (1080x1920): {reels_path}")

    return feed_path, reels_path


def create_reels_version(card_img, bg_img, theme):
    """1080x1080 카드를 1080x1920 세로 릴스용으로 확장합니다.
    상하 여백은 배경 폴백 색으로 채우고 카드를 중앙에 배치."""

    canvas = Image.new("RGB", (1080, 1920), theme["bg_fallback"])

    # 배경의 상단/하단 평균 색상 추출 (numpy 없이)
    bg_rgb = bg_img.convert("RGB")

    def avg_color(img, box):
        region = img.crop(box)
        pixels = list(region.getdata())
        n = len(pixels)
        if n == 0:
            return theme["bg_fallback"]
        r = sum(p[0] for p in pixels) // n
        g = sum(p[1] for p in pixels) // n
        b = sum(p[2] for p in pixels) // n
        return (r, g, b)

    top_color = avg_color(bg_rgb, (0, 0, 1080, 10))
    bot_color = avg_color(bg_rgb, (0, 1070, 1080, 1080))

    # 상단 영역을 단색으로 채움
    top_fill = Image.new("RGB", (1080, 420), top_color)
    canvas.paste(top_fill, (0, 0))

    # 하단 영역을 단색으로 채움
    bot_fill = Image.new("RGB", (1080, 420), bot_color)
    canvas.paste(bot_fill, (0, 1500))

    # 중앙에 카드 배치
    card_rgb = card_img.convert("RGB")
    canvas.paste(card_rgb, (0, 420))

    return canvas


def create_reels_version_fast(card_img, bg_img, theme):
    """빠른 버전: putpixel 대신 Pillow draw로 상/하단 채움."""
    canvas = Image.new("RGB", (1080, 1920), theme["bg_fallback"])
    draw = ImageDraw.Draw(canvas)

    # 상단/하단을 배경 폴백 색으로 간단히 채움
    card_rgb = card_img.convert("RGB")
    canvas.paste(card_rgb, (0, 420))

    return canvas


# ─── Main ─────────────────────────────────────────────────────────────
def main():
    parser = argparse.ArgumentParser(description="1장짜리 명상 카드 생성기")
    parser.add_argument("--title", default=DEFAULT_TITLE, help="카드 제목 (줄바꿈: \n)")
    parser.add_argument("--subtitle", default=DEFAULT_SUBTITLE, help="카드 부제")
    parser.add_argument("--theme", default="warm", choices=list(THEMES.keys()),
                        help="테마: warm, dark, nature, sunset")
    args = parser.parse_args()

    title = args.title
    subtitle = args.subtitle

    # Load draft if exists
    draft_path = os.path.join(OUTPUT_DIR, "current_draft.json")
    if os.path.exists(draft_path):
        try:
            with open(draft_path, "r", encoding="utf-8") as f:
                draft_data = json.load(f)
            title = draft_data.get("single", {}).get("title", title)
            subtitle = draft_data.get("single", {}).get("subtitle", subtitle)
            print(f"[INFO] Loaded draft content for single card. Theme: {draft_data.get('theme_name')}")
        except Exception as e:
            print(f"[WARN] Failed to load content draft: {e}")

    # 명령줄에서 \n을 실제 줄바꿈으로 변환
    title = title.replace("\\n", "\n")
    subtitle = subtitle.replace("\\n", "\n")

    feed_path, reels_path = create_single_card(title, subtitle, args.theme)

    print(f"\n{'='*50}")
    print(f"[SUCCESS] Single card generated!")
    print(f"  Feed:  {feed_path}")
    print(f"  Reels: {reels_path}")
    print(f"{'='*50}")


if __name__ == "__main__":
    main()
