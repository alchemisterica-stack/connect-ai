#!/usr/bin/env python3
"""
generate_single_card.py — v2 리빌드
- 텍스트 진짜 화면 수직/수평 중앙 배치
- 박스 없음, 텍스트 스크림만
- 부제 흰색 반투명
- Unsplash 배경 (실사), 실패 시 고급 그라디언트 폴백
- 레이아웃 고정 (랜덤 제거)
"""
import os, sys, io, time, json, random, urllib.parse, requests
from PIL import Image, ImageDraw, ImageFont, ImageFilter

HERE = os.path.dirname(os.path.abspath(__file__))
FONTS_DIR = r"C:\Users\User\my-ai-office\assets\fonts"
OUTPUT_DIR = r"C:\Users\User\my-ai-office\temp_slides"

FONT_BOLD = os.path.join(FONTS_DIR, "Pretendard-Bold.otf")
FONT_SEMI = os.path.join(FONTS_DIR, "Pretendard-SemiBold.otf")
FONT_REG  = os.path.join(FONTS_DIR, "Pretendard-Regular.otf")

# ── Pollinations 프롬프트 (실사 사진 느낌) ──────────────────────────────
POLL_PROMPTS = {
    "burnout":    "cinematic photo of a person resting on a cozy couch, soft dim lamp light, warm brown tones, shallow depth of field, photorealistic, no text",
    "self_esteem":"beautiful sunlight through window onto wooden table with small plant, warm morning tones, photorealistic photography, no text",
    "relationship":"empty bench in quiet rainy park, bokeh lights, moody atmosphere, film photography style, no text",
    "anxiety":    "calm misty ocean horizon at dawn, soft blue and gray tones, minimal, photorealistic, no text",
    "consolation":"cozy candlelight on soft blanket at night, warm bokeh lights, intimate atmosphere, photorealistic, no text",
    "warm":       "golden hour sunlight on coffee and book, warm tones, cozy morning, photorealistic, no text",
    "dark":       "starry night sky over still lake, dark blue reflections, serene, photorealistic, no text",
    "nature":     "soft morning light through green leaves, botanical, fresh, photorealistic, no text",
    "sunset":     "dramatic orange sunset clouds over sea horizon, warm golden light, photorealistic, no text",
}

# ── Unsplash 쿼리 (폴백) ───────────────────────────────────────────────
UNSPLASH_QUERIES = {
    "burnout":    ["tired rest calm nature", "peaceful quiet morning light"],
    "self_esteem":["gentle sunrise soft", "blooming flower pastel"],
    "relationship":["empty bench park", "rainy window bokeh"],
    "anxiety":    ["calm sea horizon", "foggy morning quiet"],
    "consolation":["cozy lamp night", "candle warm dark"],
    "warm":       ["warm sunlight morning coffee"],
    "dark":       ["night sky stars calm"],
    "nature":     ["green leaves morning light"],
    "sunset":     ["sunset orange clouds"],
}

# ── 그라디언트 폴백 팔레트 (테마별) ───────────────────────────────────────
GRADIENTS = {
    "burnout":    [(40, 44, 52),   (70, 78, 95)],
    "self_esteem":[(245, 220, 210),(210, 180, 160)],
    "relationship":[(30, 30, 50),  (60, 50, 80)],
    "anxiety":    [(35, 45, 65),   (55, 70, 95)],
    "consolation":[(20, 20, 35),   (50, 45, 65)],
    "warm":       [(240, 220, 195),(200, 175, 150)],
    "dark":       [(18, 24, 42),   (35, 45, 70)],
    "nature":     [(190, 220, 195),(150, 185, 160)],
    "sunset":     [(255, 160, 80), (200, 100, 60)],
}

def fetch_pollinations_bg(theme_key, size=(1080, 1080)):
    """Pollinations AI — 실사 사진 느낌 프롬프트로 배경 생성"""
    import random
    prompt = POLL_PROMPTS.get(theme_key, "calm peaceful nature photography, no text")
    seed = random.randint(0, 99999999)
    encoded = urllib.parse.quote(prompt)
    url = f"https://image.pollinations.ai/prompt/{encoded}?width={size[0]}&height={size[1]}&nologo=true&seed={seed}"
    for attempt in range(2):
        try:
            print(f"  [BG] Pollinations attempt {attempt+1}: {theme_key}...")
            r = requests.get(url, timeout=55)
            if r.status_code == 200 and len(r.content) > 10000:
                img = Image.open(io.BytesIO(r.content)).convert("RGB")
                print(f"  [BG] Pollinations OK ({len(r.content)//1024}KB)")
                return img.resize(size, Image.Resampling.LANCZOS)
        except Exception as e:
            print(f"  [BG] Pollinations failed: {e}")
        time.sleep(2)
    return None

    """Unsplash Source에서 고품질 실사 배경 가져오기 (API 키 불필요)"""
    queries = UNSPLASH_QUERIES.get(theme_key, ["calm peaceful nature"])
    query = random.choice(queries)
    encoded = urllib.parse.quote(query)
    url = f"https://source.unsplash.com/{size[0]}x{size[1]}/?{encoded}"
    try:
        print(f"  [BG] Unsplash: '{query}'...")
        r = requests.get(url, timeout=20, allow_redirects=True)
        if r.status_code == 200 and len(r.content) > 10000:
            img = Image.open(io.BytesIO(r.content)).convert("RGB")
            img = img.resize(size, Image.Resampling.LANCZOS)
            print(f"  [BG] Unsplash OK ({len(r.content)//1024}KB)")
            return img
    except Exception as e:
        print(f"  [BG] Unsplash failed: {e}")
    return None

def make_gradient_bg(theme_key, size=(1080, 1080)):
    """고급 그라디언트 배경 (폴백)"""
    colors = GRADIENTS.get(theme_key, [(30, 30, 50), (60, 55, 80)])
    c1, c2 = colors[0], colors[1]
    img = Image.new("RGB", size)
    draw = ImageDraw.Draw(img)
    for y in range(size[1]):
        t = y / size[1]
        r = int(c1[0] + (c2[0] - c1[0]) * t)
        g = int(c1[1] + (c2[1] - c1[1]) * t)
        b = int(c1[2] + (c2[2] - c1[2]) * t)
        draw.line([(0, y), (size[0], y)], fill=(r, g, b))
    return img

def get_bg(theme_key, size=(1080, 1080)):
    # 1순위: Pollinations (실사 느낌 프롬프트)
    bg = fetch_pollinations_bg(theme_key, size)
    if bg is None:
        # 2순위: Unsplash
        bg = fetch_unsplash_bg(theme_key, size)
    if bg is None:
        # 3순위: 그라디언트
        print("  [BG] Using gradient fallback")
        bg = make_gradient_bg(theme_key, size)
    return bg

def add_scrim(bg, strength=0.52):
    """텍스트 가독성을 위한 전체 어두운 스크림 레이어"""
    scrim = Image.new("RGBA", bg.size, (0, 0, 0, int(255 * strength)))
    base = bg.convert("RGBA")
    return Image.alpha_composite(base, scrim)

def load_fonts(size_title=72, size_sub=36, size_brand=20):
    serif_candidates = [
        os.path.join(FONTS_DIR, "MaruBuri-Regular.ttf"),
        os.path.join(FONTS_DIR, "NanumMyeongjo-Regular.ttf"),
        os.path.join(FONTS_DIR, "SongMyung-Regular.ttf"),
        r"C:\Windows\Fonts\batang.ttc",
    ]
    title_path = FONT_BOLD
    serif_path = None
    for p in serif_candidates:
        if os.path.exists(p) and os.path.getsize(p) > 10000:
            serif_path = p
            break

    chosen_path = serif_path if serif_path else title_path
    try:
        tf = ImageFont.truetype(chosen_path, size_title)
    except Exception:
        tf = ImageFont.truetype(title_path, size_title)
    try:
        sf = ImageFont.truetype(FONT_SEMI, size_sub)
    except Exception:
        sf = ImageFont.load_default()
    try:
        bf = ImageFont.truetype(FONT_REG, size_brand)
    except Exception:
        bf = ImageFont.load_default()
    return tf, sf, bf

def wrap_text(text, font, max_width, draw):
    lines = []
    for para in text.split("\n"):
        if not para.strip():
            lines.append("")
            continue
        current = ""
        for ch in para:
            test = current + ch
            w = draw.textbbox((0,0), test, font=font)[2]
            if w > max_width and current:
                lines.append(current)
                current = ch
            else:
                current = test
        if current:
            lines.append(current)
    return lines

def measure_block(lines, font, sub_lines, sub_font, draw, line_gap=1.55, sub_gap=1.45):
    """텍스트 블록 전체 높이 계산"""
    total = 0
    for line in lines:
        if not line:
            h = int(font.size * 0.6)
        else:
            h = draw.textbbox((0,0), line, font=font)[3]
        total += int(h * line_gap)
    if sub_lines:
        total += 36  # 제목-부제 사이 여백
        for line in sub_lines:
            h = draw.textbbox((0,0), line, font=sub_font)[3]
            total += int(h * sub_gap)
    return total

def draw_block_centered(img_w, img_h, draw, lines, font, sub_lines, sub_font,
                         title_color, sub_color, line_gap=1.55, sub_gap=1.45,
                         pad_x=120):
    """텍스트 블록을 이미지 정확한 중앙에 배치"""
    max_w = img_w - pad_x * 2
    total_h = measure_block(lines, font, sub_lines, sub_font, draw, line_gap, sub_gap)

    # 수직 중앙
    start_y = (img_h - total_h) // 2

    y = start_y - 20  # 시각적 중심 미세 보정 (폰트 baseline 오프셋)
    for line in lines:
        if not line:
            y += int(font.size * 0.6)
            continue
        bbox = draw.textbbox((0,0), line, font=font)
        lw = bbox[2] - bbox[0]
        lh = bbox[3] - bbox[1]
        x = (img_w - lw) // 2  # 수평 중앙
        # 부드러운 그림자
        draw.text((x+2, y+2), line, font=font, fill=(0,0,0,100))
        draw.text((x, y), line, font=font, fill=title_color)
        y += int(lh * line_gap)

    if sub_lines:
        y += 36
        for line in sub_lines:
            bbox = draw.textbbox((0,0), line, font=sub_font)
            lw = bbox[2] - bbox[0]
            lh = bbox[3] - bbox[1]
            x = (img_w - lw) // 2
            draw.text((x, y), line, font=sub_font, fill=sub_color)
            y += int(lh * sub_gap)

    return y

def create_single_card(title, subtitle, theme_name="warm", layout_type=None, style="normal", exclude_colors=""):
    """단일 카드 생성 — 피드(1080×1080) + 릴스(1080×1920)"""
    W, H = 1080, 1080
    W2, H2 = 1080, 1920

    print(f"\n[CARD] theme='{theme_name}' | title: {title[:30].replace(chr(10),' / ')}")

    # ── 1. 배경 ──────────────────────────────────────────────────────────
    bg_feed = get_bg(theme_name, (W, H))
    bg_reel = bg_feed.resize((W2, H2), Image.Resampling.LANCZOS)

    # ── 2. 스크림 ─────────────────────────────────────────────────────────
    feed = add_scrim(bg_feed, strength=0.50)
    reel = add_scrim(bg_reel, strength=0.50)

    # ── 3. 폰트 ──────────────────────────────────────────────────────────
    char_count = len(title.replace("\n", ""))
    if char_count > 28:
        ts = 58
    elif char_count > 18:
        ts = 66
    else:
        ts = 76

    tf, sf, bf = load_fonts(size_title=ts, size_sub=34, size_brand=20)

    # ── 4. 색상 ──────────────────────────────────────────────────────────
    title_color = (255, 255, 255, 255)
    sub_color   = (220, 220, 220, 200)  # 흰색 반투명 — accent 색 제거
    brand_color = (180, 180, 180, 160)

    # ── 5. 피드 카드 렌더 ─────────────────────────────────────────────────
    draw_f = ImageDraw.Draw(feed)
    t_lines = wrap_text(title, tf, W - 240, draw_f)
    s_lines = wrap_text(subtitle, sf, W - 280, draw_f) if subtitle else []

    # 제목과 부제 사이 구분선 (얇은 흰선)
    draw_block_centered(W, H, draw_f, t_lines, tf, s_lines, sf,
                         title_color, sub_color, pad_x=120)

    # 브랜드
    brand = "@rolling.s.cong01"
    bw = draw_f.textbbox((0,0), brand, font=bf)[2]
    draw_f.text(((W - bw)//2, H - 52), brand, font=bf, fill=brand_color)

    # ── 6. 릴스 카드 렌더 ─────────────────────────────────────────────────
    draw_r = ImageDraw.Draw(reel)
    draw_block_centered(W2, H2, draw_r, t_lines, tf, s_lines, sf,
                         title_color, sub_color, pad_x=120)
    bw2 = draw_r.textbbox((0,0), brand, font=bf)[2]
    draw_r.text(((W2 - bw2)//2, H2 - 52), brand, font=bf, fill=brand_color)

    # ── 7. 저장 ──────────────────────────────────────────────────────────
    os.makedirs(OUTPUT_DIR, exist_ok=True)
    feed_path = os.path.join(OUTPUT_DIR, "single_card_feed.png")
    reel_path = os.path.join(OUTPUT_DIR, "single_card_reels.png")
    feed.convert("RGB").save(feed_path, "PNG")
    reel.convert("RGB").save(reel_path, "PNG")
    print(f"[SAVED] Feed  : {feed_path}")
    print(f"[SAVED] Reels : {reel_path}")
    return feed_path, reel_path


if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser()
    parser.add_argument("--title",    default="아무것도 하기 싫은\n날이 있어요.")
    parser.add_argument("--subtitle", default="그냥 쉬어도 괜찮아요")
    parser.add_argument("--theme",    default="consolation")
    parser.add_argument("--style",    default="normal")
    args = parser.parse_args()
    create_single_card(args.title, args.subtitle, args.theme, style=args.style)
