#!/usr/bin/env python3
import os
import json
import sys
import argparse

try:
    import requests
except ImportError:
    print("[ERROR] requests library is required. Run 'pip install requests'.")
    sys.exit(1)

# Paths
HERE = os.path.dirname(os.path.abspath(__file__))
DRAFT_DIR = os.path.join(HERE, "..", "drafts")
CONFIG_PATH = os.path.join(HERE, "instagram_feed_drafter.json")

# Default Config
DEFAULT_CONFIG = {
    "DRAFT_THEME": "자존감을 지키며 타인과 적절한 거리를 두는 법",
    "OLLAMA_URL": "http://127.0.0.1:11434",
    "MODEL": "llama3.2:1b"
}

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

def ask_llm(ollama_url, model, prompt):
    print(f"[LLM] Starting local LLM ({model}) analysis...")
    try:
        r = requests.post(
            f"{ollama_url.rstrip('/')}/api/generate",
            json={"model": model, "prompt": prompt, "stream": False},
            timeout=180
        )
        r.raise_for_status()
        return r.json().get("response", "").strip()
    except Exception as e:
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
                    timeout=180
                )
                r.raise_for_status()
                return r.json().get("choices", [{}])[0].get("message", {}).get("content", "").strip()
            except Exception as e2:
                print(f"[ERROR] LLM call failed: {e2}")
        return ""

def main():
    parser = argparse.ArgumentParser(description="Instagram Feed Drafter")
    parser.add_argument("--theme", type=str, default=None, help="Theme for the post draft")
    parser.add_argument("--category", type=str, default="general", choices=["general", "social_worker", "cooking_tip"], help="Category for custom prompt guidelines")
    args = parser.parse_args()

    cfg = load_config()
    theme = args.theme if args.theme else cfg.get("DRAFT_THEME", DEFAULT_CONFIG["DRAFT_THEME"])
    ollama_url = cfg.get("OLLAMA_URL", DEFAULT_CONFIG["OLLAMA_URL"])
    model = cfg.get("MODEL", DEFAULT_CONFIG["MODEL"])
    category = args.category
    
    if category == "social_worker":
        prompt = f"""당신은 자격증 시험 및 교육 콘텐츠 전문 인스타그램 크리에이터입니다.
아래의 사회복지사 1급 공부/학습 관련 주제(테마)를 기반으로 인스타그램에 즉시 올릴 수 있는 최고의 카드뉴스 5슬라이드 기획안과 캡션, 그리고 Reels 대본을 한국어로 작성하세요.

[주제] {theme}

[작성 가이드라인]
- 가독성이 극대화된 텍스트 디자인 위주의 카드뉴스를 설계해야 합니다.
- 수험생들이 한 눈에 핵심 요약을 이해할 수 있도록 명료하고 직관적인 어조를 사용하세요.
- 시각 피드백: 비주얼 컨셉 가이드에는 깔끔하고 정돈된 색상 조합(예: 파스텔톤, 네이비 등 신뢰감을 주는 톤), 굵고 가독성 높은 폰트 배치 및 핵심 단어 강조 방식을 서술하세요.

[작성 포맷 요구사항]
1. 🎨 5슬라이드 카드뉴스 기획안
   - 각 슬라이드(1~5)별로 다음 내용을 명확히 적으세요:
     * [슬라이드 제목 및 핵심 텍스트] (짧고 직관적인 공부 꿀팁/핵심 내용 요약)
     * [비주얼 이미지 컨셉 가이드] (수험생 집중력을 높일 수 있는 텍스트 정렬 및 배색 가이드)
2. 📝 본문 캡션 (Caption)
   - 줄바꿈과 이모지를 적절히 섞어 학습 동기를 부여하고 가독성 좋게 적으세요.
   - 마지막에 수험생들의 댓글 참여 유도 및 공부 꿀팁 무료 자료집 신청 등을 유도하는 멘트를 넣으세요.
3. 🏷️ 해시태그 (Hashtags)
   - 사회복지사1급, 공부자극, 자격증공부 등 주제와 공부에 어울리는 핵심 해시태그 15개
4. 🎬 7초 Reels 숏폼 대본
   - 짧고 강력한 공부 요약 텍스트와 집중력 향상에 어울리는 차분한 분위기의 오디오 추천 구성안

반드시 마크다운으로 깔끔하게 정리해 작성하세요.
"""
    elif category == "cooking_tip":
        prompt = f"""당신은 일상 요리 꿀팁과 실용적인 주방 팁을 전문으로 다루는 인기 요리 크리에이터입니다.
무거운 요리 레시피가 아닌, 실용적인 정보성 '요리 꿀팁'을 주제로 인스타그램에 즉시 올릴 수 있는 최고의 카드뉴스 5슬라이드 기획안과 캡션, 그리고 Reels 대본을 한국어로 작성하세요.

[주제] {theme}

[작성 가이드라인]
- 가짜 요리 완성 사진을 사용하는 대신, 식재료 단품의 깔끔한 누끼 이미지와 텍스트를 위주로 심플하고 시각적으로 돋보이는 카드뉴스를 기획합니다.
- 주부, 1인 가구, 요리 초보자 등이 일상에서 바로 써먹을 수 있는 유용한 주방/요리 꿀팁 위주로 명확하게 서술하세요.
- 시각 피드백: 비주얼 컨셉 가이드에는 깔끔한 식재료 단품 누끼(예: 양파, 대파 등 단품 누끼 1순위 활용) 및 명확한 포인트 컬러를 조합하는 가이드라인을 적으세요.

[작성 포맷 요구사항]
1. 🎨 5슬라이드 카드뉴스 기획안
   - 각 슬라이드(1~5)별로 다음 내용을 명확히 적으세요:
     * [슬라이드 제목 및 핵심 텍스트] (한눈에 들어오는 요리 꿀팁 핵심 요약)
     * [비주얼 이미지 컨셉 가이드] (식재료 단품 누끼 이미지 활용 가이드 및 직관적인 텍스트 강조 안내)
2. 📝 본문 캡션 (Caption)
   - 일상 어조로 친근하고 가독성 높게 이모지를 섞어 작성하세요.
   - 마지막에 질문을 던져 유저들의 댓글 답변과 꿀팁 저장을 유도하는 멘트를 반드시 넣으세요.
3. 🏷️ 해시태그 (Hashtags)
   - 요리꿀팁, 주방꿀팁, 살림팁 등 실생활 정보 중심 해시태그 15개
4. 🎬 7초 Reels 숏폼 대본
   - 7초 이내에 시선을 끌 수 있는 비포/애프터 꿀팁 비교 연출 및 톡톡 튀는 분위기의 오디오 구성안

반드시 마크다운으로 깔끔하게 정리해 작성하세요.
"""
    else:
        prompt = f"""당신은 인스타그램 최고 인기 크리에이터이자 감성 마케터입니다.
아래의 주제(테마)를 기반으로 인스타그램에 즉시 올릴 수 있는 최고의 카드뉴스 5슬라이드 기획안과 캡션, 그리고 Reels 대본을 한국어로 작성하세요.

[주제] {theme}

[작성 포맷 요구사항]
1. 🎨 5슬라이드 카드뉴스 기획안
   - 각 슬라이드(1~5)별로 다음 내용을 명확히 적으세요:
     * [슬라이드 제목 및 핵심 텍스트] (짧고 강하게 마음을 울리는 문구)
     * [비주얼 이미지 컨셉 가이드] (디자이너에게 전달할 시각적 요구사항이나 이미지 생성 툴용 프롬프트)
2. 📝 본문 캡션 (Caption)
   - 줄바꿈과 이모지를 적절히 섞어 따뜻하고 가독성 좋게 적으세요.
   - 마지막에 댓글 참여 및 무료 다운로드를 유도하는 멘트를 반드시 넣으세요.
3. 🏷️ 해시태그 (Hashtags)
   - 주제와 어울리는 핵심 해시태그 15개
4. 🎬 7초 Reels 숏폼 대본
   - 짧은 시간 안에 멈춰 세울 수 있는 텍스트와 추천 오디오/분위기 구성안

반드시 마크다운으로 깔끔하게 정리해 작성하세요.
"""
    
    draft = ask_llm(ollama_url, model, prompt)
    if not draft:
        print("[ERROR] Failed to generate draft")
        sys.exit(1)
        
    os.makedirs(DRAFT_DIR, exist_ok=True)
    filename = f"instagram_post_draft_{category}.md"
    draft_path = os.path.join(DRAFT_DIR, filename)
    
    try:
        with open(draft_path, "w", encoding="utf-8") as f:
            f.write(f"# ✍️ 인스타그램 포스트 기획 초안\n\n")
            f.write(f"> **기획 카테고리:** {category}\n")
            f.write(f"> **기획 주제:** {theme}\n\n")
            f.write(draft)
        print(f"[SUCCESS] Instagram post draft written to: {draft_path}")
    except Exception as e:
        print(f"[ERROR] Failed to write draft file: {e}")

if __name__ == "__main__":
    main()
