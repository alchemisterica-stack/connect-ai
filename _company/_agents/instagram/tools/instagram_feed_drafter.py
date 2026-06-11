#!/usr/bin/env python3
import os
import json
import sys

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
    cfg = load_config()
    theme = cfg.get("DRAFT_THEME", DEFAULT_CONFIG["DRAFT_THEME"])
    ollama_url = cfg.get("OLLAMA_URL", DEFAULT_CONFIG["OLLAMA_URL"])
    model = cfg.get("MODEL", DEFAULT_CONFIG["MODEL"])
    
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
    filename = "instagram_post_draft.md"
    draft_path = os.path.join(DRAFT_DIR, filename)
    
    try:
        with open(draft_path, "w", encoding="utf-8") as f:
            f.write(f"# ✍️ 인스타그램 포스트 기획 초안\n\n")
            f.write(f"> **기획 주제:** {theme}\n\n")
            f.write(draft)
        print(f"[SUCCESS] Instagram post draft written to: {draft_path}")
    except Exception as e:
        print(f"[ERROR] Failed to write draft file: {e}")

if __name__ == "__main__":
    main()
