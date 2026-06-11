#!/usr/bin/env python3
"""Blog Account (Naver / Tistory) — shared configuration for blog tools.

This script doesn't perform tasks on its own. It holds blog types,
API keys, credentials, and competitive target blog URLs.
"""
import os, json, sys

HERE = os.path.dirname(os.path.abspath(__file__))
CONFIG_PATH = os.path.join(HERE, "blog_account.json")

def load():
    with open(CONFIG_PATH, "r", encoding="utf-8") as f:
        return json.load(f)

def main():
    cfg = load()
    blog_type = (cfg.get("BLOG_TYPE") or "naver").lower()
    api_key = (cfg.get("BLOG_API_KEY") or "").strip()
    blog_id = (cfg.get("BLOG_ID") or "").strip()
    
    masked = (api_key[:4] + "…" + api_key[-3:]) if len(api_key) >= 8 else ("(빈 값)" if not api_key else "(짧음)")
    
    print("─── 블로그 계정 및 공유 설정 ───")
    print(f"  블로그 종류       : {blog_type.upper()}")
    print(f"  블로그 ID / 주소   : {blog_id or '(없음)'}")
    print(f"  API 키 / 토큰      : {masked}")
    
    competitors = cfg.get("COMPETITOR_BLOGS") or []
    print(f"  경쟁 블로그 ({len(competitors)}개): {', '.join(competitors) if competitors else '(없음)'}")
    
    print(f"  Ollama URL        : {cfg.get('OLLAMA_URL') or 'http://127.0.0.1:11434'}")
    print(f"  분석 모델          : {cfg.get('MODEL') or '(자동 선택)'}")
    
    if not api_key or not blog_id:
        print("\n⚠️  계정 ID와 API 키가 설정되지 않았습니다. 분석 기능이 제한될 수 있습니다.")
        sys.exit(1)
    
    print("\n✅ 블로그 설정 로드 완료! 분석 및 채널 포스팅 기능이 이 계정에 연결됩니다.")

if __name__ == "__main__":
    main()
