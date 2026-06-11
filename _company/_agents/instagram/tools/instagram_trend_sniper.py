#!/usr/bin/env python3
import os
import json
import sys
import urllib.parse
import re

try:
    import requests
except ImportError:
    print("[ERROR] requests library is required. Run 'pip install requests'.")
    sys.exit(1)

# Paths
HERE = os.path.dirname(os.path.abspath(__file__))
REPORT_PATH = os.path.join(HERE, "..", "instagram_trend_report.md")
CONFIG_PATH = os.path.join(HERE, "instagram_trend_sniper.json")

# Default Config
DEFAULT_CONFIG = {
    "TARGET_KEYWORDS": ["동기부여", "관계 심리", "자존감"],
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

def search_instagram_trends(keyword):
    print(f"[SEARCH] Searching trends for '{keyword}'...")
    query = f"site:instagram.com {keyword} 릴스 카드뉴스"
    encoded_query = urllib.parse.quote(query)
    url = f"https://html.duckduckgo.com/html/?q={encoded_query}"
    
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36"
    }
    
    try:
        r = requests.get(url, headers=headers, timeout=15)
        r.raise_for_status()
        html = r.text
        
        results = []
        matches = re.findall(r'<a class="result__url"[^>]*>([\s\S]*?)</a>[\s\S]*?<a class="result__snippet"[^>]*>([\s\S]*?)</a>', html)
        for m in matches[:6]:
            title = re.sub(r'<[^>]+>', '', m[0]).strip().replace('\n', ' ')
            snippet = re.sub(r'<[^>]+>', '', m[1]).strip().replace('\n', ' ')
            results.append(f"- 제목/링크: {title}\n  내용 요약: {snippet}")
        return "\n".join(results)
    except Exception as e:
        print(f"[WARN] Search failed ({keyword}): {e}")
        return ""

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
    keywords = cfg.get("TARGET_KEYWORDS", DEFAULT_CONFIG["TARGET_KEYWORDS"])
    ollama_url = cfg.get("OLLAMA_URL", DEFAULT_CONFIG["OLLAMA_URL"])
    model = cfg.get("MODEL", DEFAULT_CONFIG["MODEL"])
    
    collected_data = []
    for kw in keywords[:3]:
        data = search_instagram_trends(kw)
        if data:
            collected_data.append(f"### 키워드: {kw}\n{data}")
            
    if not collected_data:
        print("[WARN] No trend data retrieved. Check internet connection.")
        sys.exit(1)
        
    all_data = "\n\n".join(collected_data)
    
    prompt = f"""당신은 인스타그램 알고리즘 및 트렌드 전문가입니다.
아래 수집된 검색 데이터(인스타그램 관련 게시글 패턴 및 키워드)를 바탕으로 현재 인스타에서 반응이 좋은 트렌드 요약 보고서를 한국어로 작성하세요.

[수집 데이터]
{all_data}

[작성 요구사항]
1. 📈 인스타 급상승 트렌드 분석: 최근 사용자들이 가장 열광하는 심리/동기부여 키워드와 톤앤매너
2. 🎯 잘 먹히는 해시태그 목록: 검색 노출을 극대화할 수 있는 필수 해시태그 15개 추천
3. 💡 즉시 적용 가능한 킬러 콘텐츠 아이디어 2가지: 카드뉴스 제목, 후킹 문구, 슬라이드 구성안 포함

반드시 마크다운 형식으로 보기 좋게 작성하세요.
"""
    
    report = ask_llm(ollama_url, model, prompt)
    if not report:
        print("[ERROR] Failed to generate report")
        sys.exit(1)
        
    try:
        os.makedirs(os.path.dirname(REPORT_PATH), exist_ok=True)
        with open(REPORT_PATH, "w", encoding="utf-8") as f:
            f.write(f"# 📊 인스타그램 트렌드 분석 보고서\n\n")
            f.write(f"> **분석 대상 키워드:** {', '.join(keywords)}\n\n")
            f.write(report)
        print(f"[SUCCESS] Trend report written to: {REPORT_PATH}")
    except Exception as e:
        print(f"[ERROR] Failed to write report file: {e}")

if __name__ == "__main__":
    main()
