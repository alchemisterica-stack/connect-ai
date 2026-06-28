#!/usr/bin/env python3
"""
generate_single_card.py — 1장짜리 명상 카드 이미지 생성기
- Pretendard + Emotional Font Mix (MaruBuri, NanumMyeongjo, SongMyung, System Batang)
- Automatic background brightness detection for dynamic contrast card transparency
- Dynamic font size adjustment based on character length
- Discrete branding footprint (18px)
- Layout variations & High-readability bold style support
"""
import os
import sys
import io
import time
import json
import argparse
import random
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

# ─── AI Background Brightness Detection ──────────────────────────────
def calculate_background_brightness(bg_img):
    """배경 이미지의 평균 밝기 (0~255)를 PIL 분석을 통해 획득합니다."""
    try:
        gray = bg_img.convert("L")
        data = list(gray.getdata())
        if not data:
            return 128
        return sum(data) / len(data)
    except Exception:
        return 128

# ─── AI Background Generation ───────────────────────────────────────
def generate_background(prompt, size=(1080, 1080), fallback_color=(240, 240, 240)):
    """Pollinations AI로 배경 이미지를 생성합니다. 실패 시 단색 폴백."""
    import random
    seed = random.randint(0, 99999999)
    encoded = urllib.parse.quote(prompt)
    url = f"https://image.pollinations.ai/prompt/{encoded}?width={size[0]}&height={size[1]}&nologo=true&seed={seed}"

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
        words = list(paragraph)
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
    draw.text((x + offset, y + offset), text, font=font, fill=shadow_color)
    draw.text(pos, text, font=font, fill=fill)


def draw_centered_text_block(draw, lines, font, start_y, usable_box, fill, line_spacing_factor=1.5, shadow=True, text_align="center"):
    """여러 줄의 텍스트를 레이아웃 정렬 방식에 맞춰 그립니다."""
    y = start_y
    for line in lines:
        if not line:
            y += int(font.size * 0.8)
            continue
        bbox = draw.textbbox((0, 0), line, font=font)
        w = bbox[2] - bbox[0]
        h = bbox[3] - bbox[1]
        
        if text_align == "left":
            x = usable_box[0]
        elif text_align == "right":
            x = usable_box[2] - w
        else:
            x = usable_box[0] + (usable_box[2] - usable_box[0] - w) // 2
            
        if shadow:
            draw_text_with_shadow(draw, (x, y), line, font, fill)
        else:
            draw.text((x, y), line, font=font, fill=fill)
        y += int(h * line_spacing_factor)
    return y


# ─── Font Loading & Random Mixing ────────────────────────────────────
def load_fonts():
    """Pretendard 및 동적 믹스매치 명조 서체 풀을 구축하여 무작위 로드합니다."""
    fonts_pool = []
    
    # 윈도우 시스템 바탕체
    try:
        fonts_pool.append(("C:\\Windows\\Fonts\\batang.ttc", "SystemBatang"))
    except Exception:
        pass
        
    # 다운로드된 프리미엄 서체들 추가
    candidate_files = [
        "MaruBuri-Regular.ttf",
        "NanumMyeongjo-Regular.ttf",
        "SongMyung-Regular.ttf"
    ]
    for fname in candidate_files:
        p = os.path.join(FONTS_DIR, fname)
        if os.path.exists(p) and os.path.getsize(p) > 10000:
            fonts_pool.append((p, fname.split(".")[0]))
            
    # 만약 풀이 아예 비어있다면 고딕으로 대체
    if not fonts_pool:
        fonts_pool.append((FONT_BOLD, "PretendardFallback"))
        
    # 무작위 서체 선택
    chosen_path, font_name = random.choice(fonts_pool)
    print(f"[FONT-MIXER] Randomly selected emotional font: '{font_name}' ({chosen_path})")

    # 1. 로드할 타겟 폰트 빌드
    try:
        serif_font = ImageFont.truetype(chosen_path, 58)
    except Exception:
        serif_font = ImageFont.load_default()

    try:
        title_font = ImageFont.truetype(FONT_BOLD, 58)
        title_font_bold_lg = ImageFont.truetype(FONT_BOLD, 68) # 68px Cover/Single Bold Title
        sub_font = ImageFont.truetype(FONT_SEMI, 34)
        brand_font = ImageFont.truetype(FONT_REG, 18)
        return title_font, sub_font, brand_font, serif_font, title_font_bold_lg, chosen_path
    except Exception as e:
        print(f"[FONT] Pretendard load failed ({e}), falling back to default")
        return (
            ImageFont.load_default(),
            ImageFont.load_default(),
            ImageFont.load_default(),
            serif_font,
            ImageFont.load_default(),
            chosen_path
        )


# ─── Card Generation ─────────────────────────────────────────────────
def create_single_card(title, subtitle, theme_name="warm", layout_type=None, style="normal"):
    """1장짜리 명상 카드를 생성합니다. 피드용(1080x1080) + 릴스용(1080x1920) 동시 출력."""
    theme = THEMES.get(theme_name, THEMES["warm"])
    title_font, sub_font, brand_font, serif_font, title_font_bold_lg, chosen_path = load_fonts()

    # 가독성 강화 스타일이면 레이아웃을 rect_center로 고정
    is_bold = (style == "bold")
    if is_bold:
        layout_type = "rect_center"

    if not layout_type:
        layout_choices = ["rect_center", "ellipse_center", "circle_left", "rect_right"]
        layout_type = random.choice(layout_choices)

    print(f"\n[CARD] Generating '{theme_name}' theme single card with layout '{layout_type}' [Style: {style}]...")
    print(f"  Title: {title.replace(chr(10), ' / ')}")
    print(f"  Subtitle: {subtitle}")

    # ── 1) Generate background ──
    # AI 9:16 비율 직접 생성 파라미터 연동을 위한 규격 확장 (비주얼 깨짐 원천 차단)
    bg = generate_background(theme["bg_prompt"], (1080, 1080), theme["bg_fallback"])

    # ── 2) Calculate background brightness for contrast matching ──
    brightness = calculate_background_brightness(bg)
    print(f"  [CONTRAST] Background brightness computed: {brightness:.1f}")

    # ── 3) Create glassmorphism overlay ──
    overlay = Image.new("RGBA", (1080, 1080), (0, 0, 0, 0))
    draw_overlay = ImageDraw.Draw(overlay)

    # 대비 지능형 로직: 배경이 밝으면(140 이상) 글상자 불투명도(alpha)를 245로 아주 진하게 어둡게 조절,
    # 배경이 어두우면(140 미만) 글상자 불투명도를 140~160으로 조절하여 자연스럽게 투명하게 만듦
    card_bg = theme["card_bg"]
    if brightness > 140:
        alpha_val = 245 if is_bold else 225
    else:
        alpha_val = 180 if is_bold else 150
        
    card_bg_color = (card_bg[0], card_bg[1], card_bg[2], alpha_val)
    print(f"  [CONTRAST] Auto card opacity set to alpha={alpha_val}")

    # Layout geometries
    if layout_type == "ellipse_center":
        card_box = [100, 150, 980, 930]
        draw_overlay.ellipse(card_box, fill=card_bg_color, outline=theme["border_color"], width=2)
        usable_box = [150, 200, 930, 880]
        text_align = "center"
    elif layout_type == "circle_left":
        card_box = [80, 420, 720, 1060]
        draw_overlay.ellipse(card_box, fill=card_bg_color, outline=theme["border_color"], width=2)
        usable_box = [130, 460, 670, 1020]
        text_align = "left"
    elif layout_type == "rect_right":
        card_box = [450, 400, 1020, 1020]
        draw_overlay.rounded_rectangle(card_box, radius=20, fill=card_bg_color, outline=theme["border_color"], width=2)
        usable_box = [490, 440, 980, 980]
        text_align = "right"
    else:
        # rect_center
        card_box = [80, 80, 1000, 1000]
        draw_overlay.rounded_rectangle(card_box, radius=30, fill=card_bg_color, outline=theme["border_color"], width=2)
        usable_box = [120, 120, 960, 960]
        text_align = "center"

    # ── 4) Compose background + card ──
    img = Image.alpha_composite(bg.convert("RGBA"), overlay)
    draw = ImageDraw.Draw(img)

    # ── 5) Dynamic Font Size & Sizing ──
    max_text_width = (usable_box[2] - usable_box[0]) - 40
    
    # 텍스트 길이에 따라 자동으로 폰트 크기 계산 (동적 폰트 크기 계산기)
    base_font_size = 68 if is_bold else 58
    char_count = len(title.replace("\n", ""))
    
    if char_count > 30:
        base_font_size = int(base_font_size * 0.72)  # 많은 글자 수: 대폭 감소
    elif char_count > 18:
        base_font_size = int(base_font_size * 0.85)  # 중간 글자 수: 약간 감소
        
    print(f"  [DYNAMIC-SIZE] Base font size calculated: {base_font_size}px based on {char_count} chars")
    
    # 동적 크기가 적용된 폰트 획득
    try:
        active_font = ImageFont.truetype(chosen_path if not is_bold else FONT_BOLD, base_font_size)
    except Exception:
        active_font = ImageFont.load_default()

    title_lines = wrap_text(title, active_font, max_text_width, draw)

    title_line_h = int(base_font_size * 1.4)
    sub_line_h = int(34 * 1.5)
    brand_line_h = int(18 * 1.5)
    
    total_title_h = len(title_lines) * title_line_h
    total_sub_h = sub_line_h if subtitle else 0
    gap = 40 if subtitle else 0
    total_h = total_title_h + gap + total_sub_h
    
    usable_h = (usable_box[3] - usable_box[1]) - brand_line_h - 20
    start_y = usable_box[1] + max(0, (usable_h - total_h) // 2)

    y = draw_centered_text_block(
        draw, title_lines, active_font, start_y, usable_box,
        fill=theme["text_color"], line_spacing_factor=1.4, text_align=text_align
    )

    # ── 6) Render subtitle ──
    if subtitle:
        y += 20
        sub_lines = wrap_text(subtitle, sub_font, max_text_width, draw)
        draw_centered_text_block(
            draw, sub_lines, sub_font, y, usable_box,
            fill=theme["accent_color"], line_spacing_factor=1.4, text_align=text_align
        )

    # ── 7) Branding (Tiny & Semi-Transparent) ──
    brand_text = "@rolling.s.cong01"
    bbox = draw.textbbox((0, 0), brand_text, font=brand_font)
    bw = bbox[2] - bbox[0]
    
    brand_y = usable_box[3] - brand_line_h - 10
    if text_align == "left":
        brand_x = usable_box[0]
    elif text_align == "right":
        brand_x = usable_box[2] - bw
    else:
        brand_x = usable_box[0] + (usable_box[2] - usable_box[0] - bw) // 2
        
    brand_color = tuple(list(theme["text_color"][:3]) + [120]) if len(theme["text_color"]) < 4 else theme["text_color"]
    draw.text((brand_x, brand_y), brand_text, font=brand_font, fill=brand_color[:3])

    # ── 8) Save feed version (1080x1080) ──
    os.makedirs(OUTPUT_DIR, exist_ok=True)
    feed_path = os.path.join(OUTPUT_DIR, "single_card_feed.png")
    img.convert("RGB").save(feed_path, "PNG", quality=95)
    print(f"[SAVED] Feed card (1080x1080): {feed_path}")

    # ── 9) Create & save reels version (1080x1920) ──
    reels_img = create_reels_version(img, bg, theme)
    reels_path = os.path.join(OUTPUT_DIR, "single_card_reels.png")
    reels_img.convert("RGB").save(reels_path, "PNG", quality=95)
    print(f"[SAVED] Reels card (1080x1920): {reels_path}")

    return feed_path, reels_path


def create_reels_version(card_img, bg_img, theme):
    """1080x1080 카드를 1080x1920 세로 릴스용으로 확장합니다."""
    canvas = Image.new("RGB", (1080, 1920), theme["bg_fallback"])
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

    top_fill = Image.new("RGB", (1080, 420), top_color)
    canvas.paste(top_fill, (0, 0))

    bot_fill = Image.new("RGB", (1080, 420), bot_color)
    canvas.paste(bot_fill, (0, 1500))

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
    parser.add_argument("--style", default="normal", choices=["normal", "bold"],
                        help="스타일: normal (명조) 또는 bold (가독성 강화 68px 고딕)")
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

    # Enforce layout variation
    layout_choices = ["rect_center", "ellipse_center", "circle_left", "rect_right"]
    layout_type = random.choice(layout_choices)

    feed_path, reels_path = create_single_card(title, subtitle, args.theme, layout_type=layout_type, style=args.style)

    print(f"\n{'='*50}")
    print(f"[SUCCESS] Single card generated with layout '{layout_type}' [Style: {args.style}]!")
    print(f"  Feed:  {feed_path}")
    print(f"  Reels: {reels_path}")
    print(f"{'='*50}")


if __name__ == "__main__":
    main()
