#!/usr/bin/env python3
"""
generate_single_card.py — v3
[유지] 실사 배경(Pollinations), 텍스트 정중앙, 흰색 부제, 스크림 방식
[복원] 아침(bold)=밝은 톤 / 저녁(normal)=어두운 톤 완전 분리
[복원] 색상 다양성 — 슬롯별 5가지 팔레트, 3일 중복 방지
"""
import os, sys, io, time, json, random, urllib.parse, requests
from PIL import Image, ImageDraw, ImageFont

HERE       = os.path.dirname(os.path.abspath(__file__))
FONTS_DIR  = r"C:\Users\User\my-ai-office\assets\fonts"
OUTPUT_DIR = r"C:\Users\User\my-ai-office\temp_slides"
FONT_BOLD  = os.path.join(FONTS_DIR, "Pretendard-Bold.otf")
FONT_SEMI  = os.path.join(FONTS_DIR, "Pretendard-SemiBold.otf")
FONT_REG   = os.path.join(FONTS_DIR, "Pretendard-Regular.otf")

# ══════════════════════════════════════════════════════════════════════
# 배경 팔레트 — 아침(bold) vs 저녁(normal) 완전 분리
# ══════════════════════════════════════════════════════════════════════

# 🌅 아침(bold): 밝고 따뜻한 색감 — 5가지 팔레트
MORNING_PALETTES = {
    "golden_morning": {
        "prompt": "soft golden sunlight streaming through sheer white curtains onto wooden floor, warm amber glow, bright hopeful morning, photorealistic photography, no text no words",
        "gradient": [(255, 220, 160), (230, 190, 120)],
    },
    "fresh_coffee": {
        "prompt": "steaming coffee cup on bright wooden table by window, morning light and soft shadows, clean warm tones, photorealistic, no text no words",
        "gradient": [(245, 230, 200), (210, 185, 150)],
    },
    "spring_bloom": {
        "prompt": "soft pink cherry blossoms in bright gentle morning light, pastel pink and white tones, fresh spring atmosphere, photorealistic, no text no words",
        "gradient": [(255, 220, 220), (240, 190, 190)],
    },
    "sunrise_sky": {
        "prompt": "beautiful sunrise over calm water, soft orange and gold clouds reflected, hopeful warm tones, photorealistic, no text no words",
        "gradient": [(255, 180, 100), (220, 140, 80)],
    },
    "morning_green": {
        "prompt": "sunlight through fresh green leaves, bright botanical morning, clear light tones, dewdrops on leaves, photorealistic, no text no words",
        "gradient": [(200, 235, 200), (160, 205, 165)],
    },
}

# 🌆 저녁(normal): 어둡고 감성적인 색감 — 5가지 팔레트
EVENING_PALETTES = {
    "candle_night": {
        "prompt": "cozy candlelight glowing on soft blanket at night, warm golden bokeh lights, intimate quiet atmosphere, photorealistic photography, no text no words",
        "gradient": [(30, 20, 15), (60, 40, 25)],
    },
    "starry_lake": {
        "prompt": "starry night sky perfectly reflected in still calm lake, deep midnight blue, peaceful serene, photorealistic, no text no words",
        "gradient": [(15, 20, 45), (30, 40, 80)],
    },
    "rainy_window": {
        "prompt": "raindrops on window at night, blurred city lights bokeh in background, moody blue and gray, melancholic peaceful, photorealistic, no text no words",
        "gradient": [(25, 35, 55), (45, 60, 85)],
    },
    "lamp_room": {
        "prompt": "warm desk lamp casting soft amber glow in dark cozy room, open book nearby, quiet evening atmosphere, photorealistic, no text no words",
        "gradient": [(35, 25, 15), (70, 50, 30)],
    },
    "dusk_purple": {
        "prompt": "twilight dusk sky in deep purple and navy, last light of day over silhouetted trees, calm contemplative, photorealistic, no text no words",
        "gradient": [(40, 25, 55), (70, 45, 90)],
    },
}

# ══════════════════════════════════════════════════════════════════════
# 색상 다양성 — 3일 중복 방지
# ══════════════════════════════════════════════════════════════════════
USED_COLOR_FILE = os.path.join(OUTPUT_DIR, "used_color.txt")

def load_recent_used_colors():
    """최근 사용된 색상 키 목록 읽기"""
    try:
        if os.path.exists(USED_COLOR_FILE):
            with open(USED_COLOR_FILE, "r", encoding="utf-8") as f:
                return [line.strip() for line in f.readlines() if line.strip()]
    except Exception:
        pass
    return []

def save_used_color(color_key):
    """사용된 색상 기록 (최근 10개 유지)"""
    try:
        recent = load_recent_used_colors()
        recent.append(color_key)
        recent = recent[-10:]  # 최근 10개만 유지
        with open(USED_COLOR_FILE, "w", encoding="utf-8") as f:
            f.write("\n".join(recent))
    except Exception as e:
        print(f"  [WARN] 색상 기록 실패: {e}")

def pick_palette(palettes, used_colors):
    """최근 사용 안 한 팔레트 우선 선택"""
    unused = [k for k in palettes if k not in used_colors]
    if unused:
        chosen = random.choice(unused)
        print(f"  [COLOR] 미사용 팔레트 선택: '{chosen}'")
    else:
        # 전부 썼으면 가장 오래된 것 제외하고 선택
        chosen = random.choice(list(palettes.keys()))
        print(f"  [COLOR] 팔레트 풀 순환: '{chosen}'")
    return chosen, palettes[chosen]

# ══════════════════════════════════════════════════════════════════════
# 배경 생성
# ══════════════════════════════════════════════════════════════════════
def fetch_pollinations(prompt, size=(1080, 1080)):
    seed = random.randint(0, 99999999)
    encoded = urllib.parse.quote(prompt)
    url = f"https://image.pollinations.ai/prompt/{encoded}?width={size[0]}&height={size[1]}&nologo=true&seed={seed}"
    for attempt in range(2):
        try:
            print(f"  [BG] Pollinations 시도 {attempt+1}...")
            r = requests.get(url, timeout=8)
            if r.status_code == 200 and len(r.content) > 10000:
                img = Image.open(io.BytesIO(r.content)).convert("RGB")
                print(f"  [BG] 성공 ({len(r.content)//1024}KB)")
                return img.resize(size, Image.Resampling.LANCZOS)
        except Exception as e:
            print(f"  [BG] 실패: {e}")
        time.sleep(1)
    return None

def make_gradient(colors, size=(1080, 1080)):
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

def add_scrim(bg, strength=0.50):
    scrim = Image.new("RGBA", bg.size, (0, 0, 0, int(255 * strength)))
    return Image.alpha_composite(bg.convert("RGBA"), scrim)

# ══════════════════════════════════════════════════════════════════════
# 폰트 & 텍스트
# ══════════════════════════════════════════════════════════════════════
def get_serif_font(size):
    candidates = [
        os.path.join(FONTS_DIR, "MaruBuri-Regular.ttf"),
        os.path.join(FONTS_DIR, "NanumMyeongjo-Regular.ttf"),
        os.path.join(FONTS_DIR, "SongMyung-Regular.ttf"),
        r"C:\Windows\Fonts\batang.ttc",
    ]
    for p in candidates:
        if os.path.exists(p) and os.path.getsize(p) > 10000:
            try:
                return ImageFont.truetype(p, size)
            except Exception:
                pass
    return ImageFont.truetype(FONT_BOLD, size)

def wrap_text(text, font, max_width, draw):
    lines = []
    for para in text.split("\n"):
        if not para.strip():
            lines.append(""); continue
        current = ""
        for ch in para:
            test = current + ch
            if draw.textbbox((0,0), test, font=font)[2] > max_width and current:
                lines.append(current); current = ch
            else:
                current = test
        if current:
            lines.append(current)
    return lines

def measure_block(lines, font, sub_lines, sub_font, draw, lg, sg):
    total = 0
    for line in lines:
        h = int(font.size * 0.6) if not line else draw.textbbox((0,0), line, font=font)[3]
        total += int(h * lg)
    if sub_lines:
        total += 40
        for line in sub_lines:
            h = draw.textbbox((0,0), line, font=sub_font)[3]
            total += int(h * sg)
    return total

def draw_centered(W, H, draw, t_lines, tf, s_lines, sf,
                   tc, sc, lg=1.55, sg=1.45, pad_x=110):
    total_h = measure_block(t_lines, tf, s_lines, sf, draw, lg, sg)
    y = (H - total_h) // 2 - 15  # 시각적 중심 미세 보정

    for line in t_lines:
        if not line:
            y += int(tf.size * 0.6); continue
        bbox = draw.textbbox((0,0), line, font=tf)
        lw, lh = bbox[2]-bbox[0], bbox[3]-bbox[1]
        x = (W - lw) // 2
        draw.text((x+2, y+2), line, font=tf, fill=(0,0,0,120))  # 그림자
        draw.text((x, y),     line, font=tf, fill=tc)
        y += int(lh * lg)

    if s_lines:
        y += 40
        for line in s_lines:
            bbox = draw.textbbox((0,0), line, font=sf)
            lw, lh = bbox[2]-bbox[0], bbox[3]-bbox[1]
            x = (W - lw) // 2
            draw.text((x, y), line, font=sf, fill=sc)
            y += int(lh * sg)

# ══════════════════════════════════════════════════════════════════════
# 메인 카드 생성
# ══════════════════════════════════════════════════════════════════════
def create_single_card(title, subtitle, theme_name="warm", layout_type=None,
                        style="normal", exclude_colors="", target_type="all"):
    """
    style='bold'   → 🌅 아침 08:30: 밝은 톤, Pretendard Bold, 강한 스크림
    style='normal' → 🌆 저녁 20:30: 어두운 톤, 명조체, 부드러운 스크림
    """
    W, H   = 1080, 1080
    W2, H2 = 1080, 1920
    is_bold = (style == "bold")

    slot_label = "[MORNING BOLD]" if is_bold else "[EVENING NORMAL]"
    print(f"\n[CARD] {slot_label} | theme='{theme_name}'")

    # ── 1. 팔레트 선택 (3일 중복 방지 / 복구 시에는 기존 톤 복원) ──
    color_key = None
    if target_type != "all":
        try:
            preset_file = os.path.join(OUTPUT_DIR, "used_color.txt")
            if os.path.exists(preset_file):
                with open(preset_file, "r", encoding="utf-8") as pf:
                    color_key = pf.read().strip()
        except Exception as e:
            print(f"[WARN] Failed to load previous color for single card retry: {e}")

    palettes = MORNING_PALETTES if is_bold else EVENING_PALETTES
    if color_key and color_key in palettes:
        palette = palettes[color_key]
    else:
        used_colors = load_recent_used_colors()
        if exclude_colors:
            used_colors += [c.strip() for c in exclude_colors.split(",") if c.strip()]
        color_key, palette = pick_palette(palettes, used_colors)

    # ── 2. 배경 생성 ───────────────────────────────────────────────────
    bg_feed = fetch_pollinations(palette["prompt"], (W, H))
    if bg_feed is None:
        print("  [BG] 그라디언트 폴백 사용")
        bg_feed = make_gradient(palette["gradient"], (W, H))

    # 순수 원본 배경 저장 (텍스트 얹기 전)
    raw_bg_feed_path = os.path.join(OUTPUT_DIR, "bg_single_card_feed.png")
    bg_feed.convert("RGB").save(raw_bg_feed_path, "PNG")
    print(f"  [RAW-BG] Saved raw background -> {raw_bg_feed_path}")

    bg_reel = bg_feed.resize((W2, H2), Image.Resampling.LANCZOS)

    # ── 3. 스크림 (아침=진하게, 저녁=부드럽게) ─────────────────────────
    scrim = 0.58 if is_bold else 0.46
    feed = add_scrim(bg_feed, scrim)
    reel = add_scrim(bg_reel, scrim)

    # ── 4. 폰트 (아침=Bold 굵게, 저녁=명조 감성) ────────────────────────
    char_count = len(title.replace("\n", ""))
    if is_bold:
        ts = 84 if char_count <= 18 else (74 if char_count <= 28 else 64)
        tf = ImageFont.truetype(FONT_BOLD, ts)
    else:
        ts = 76 if char_count <= 18 else (66 if char_count <= 28 else 58)
        tf = get_serif_font(ts)

    try:
        sf = ImageFont.truetype(FONT_SEMI, 34 if is_bold else 32)
    except Exception:
        sf = ImageFont.load_default()
    try:
        bf = ImageFont.truetype(FONT_REG, 20)
    except Exception:
        bf = ImageFont.load_default()

    # ── 5. 색상 & 줄간격 ────────────────────────────────────────────────
    tc = (255, 255, 255, 255)
    sc = (235, 230, 225, 215) if is_bold else (218, 215, 212, 190)
    bc = (175, 175, 175, 150)
    lg = 1.45 if is_bold else 1.62  # 아침=타이트, 저녁=여유
    sg = 1.35 if is_bold else 1.45

    print(f"  [FONT] {ts}px | scrim={scrim} | palette='{color_key}'")

    # ── 6. 렌더 & 7. 저장 ──────────────────────────────────────────────
    os.makedirs(OUTPUT_DIR, exist_ok=True)
    feed_path = os.path.join(OUTPUT_DIR, "single_card_feed.png")
    reel_path = os.path.join(OUTPUT_DIR, "single_card_reels.png")

    targets = []
    if target_type == "all" or target_type == "feed":
        targets.append((feed, W, H, feed_path))
    if target_type == "all" or target_type == "reels":
        targets.append((reel, W2, H2, reel_path))

    for (img, IW, IH, path) in targets:
        d = ImageDraw.Draw(img)
        t_lines = wrap_text(title, tf, IW - 240, d)
        s_lines = wrap_text(subtitle, sf, IW - 280, d) if subtitle else []
        draw_centered(IW, IH, d, t_lines, tf, s_lines, sf, tc, sc, lg, sg)
        brand = "@rolling.s.cong01"
        bw = d.textbbox((0,0), brand, font=bf)[2]
        d.text(((IW - bw)//2, IH - 52), brand, font=bf, fill=bc)
        img.convert("RGB").save(path)
        print(f"[SAVED] {path}")

    if target_type == "all":
        save_used_color(color_key)

    return feed_path, reel_path


if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser()
    parser.add_argument("--title",          default=None)
    parser.add_argument("--subtitle",       default=None)
    parser.add_argument("--theme",          default=None)
    parser.add_argument("--style",          default="normal",
                        choices=["normal","bold"])
    parser.add_argument("--exclude-colors", default="")
    parser.add_argument("--target-type",    default="all",
                        choices=["all", "feed", "reels"])
    args = parser.parse_args()

    title = args.title
    subtitle = args.subtitle
    theme = args.theme

    if not title or not subtitle:
        draft_path = os.path.join(OUTPUT_DIR, "current_draft.json")
        if os.path.exists(draft_path):
            try:
                with open(draft_path, "r", encoding="utf-8") as f:
                    draft_data = json.load(f)
                    single_info = draft_data.get("single", {})
                    if single_info:
                        title = single_info.get("title", title)
                        subtitle = single_info.get("subtitle", subtitle)
                    theme = draft_data.get("theme", theme)
            except Exception as e:
                print(f"[WARN] Failed to auto-load draft in single card: {e}")

    if not title:
        title = "오늘 하루도 참\n고생 많았어."
    if not subtitle:
        subtitle = "그저 존재만으로도 충분해요."
    if not theme:
        theme = "consolation"

    create_single_card(title, subtitle, theme,
                       style=args.style,
                       exclude_colors=getattr(args,"exclude_colors",""),
                       target_type=args.target_type)
