#!/usr/bin/env python3
"""
analyze_my_account.py
rolling.s.cong01 인스타그램 계정의 실제 게시물 성과를 분석합니다.
- 게시물별 좋아요, 댓글, 저장수, 도달수 수집
- 상위/하위 게시물 비교
- 리서처용 분석 보고서 생성
"""

import os
import sys
import json
import requests
from datetime import datetime

HERE = os.path.dirname(os.path.abspath(__file__))
CONFIG_PATH = os.path.abspath(os.path.join(HERE, "..", "config.md"))
REPORT_PATH = os.path.abspath(os.path.join(HERE, "..", "my_account_analysis.md"))

def load_config():
    tokens = {}
    if os.path.exists(CONFIG_PATH):
        with open(CONFIG_PATH, "r", encoding="utf-8") as f:
            for line in f:
                if line.strip().startswith("- "):
                    parts = line.strip()[2:].split(":", 1)
                    if len(parts) == 2:
                        tokens[parts[0].strip()] = parts[1].strip()
    return tokens

def get_media_list(biz_id, token, limit=30):
    """최근 게시물 목록 가져오기"""
    url = f"https://graph.facebook.com/v20.0/{biz_id}/media"
    params = {
        "fields": "id,caption,media_type,timestamp,like_count,comments_count,thumbnail_url,media_url",
        "limit": limit,
        "access_token": token
    }
    r = requests.get(url, params=params, timeout=15)
    r.raise_for_status()
    return r.json().get("data", [])

def get_media_insights(media_id, media_type, token):
    """개별 게시물 인사이트 (저장수, 도달수, 노출수)"""
    url = f"https://graph.facebook.com/v20.0/{media_id}/insights"
    
    if media_type == "VIDEO" or media_type == "REELS":
        metrics = "reach,saved,video_views,shares"
    else:
        metrics = "reach,saved,impressions,shares"
    
    params = {
        "metric": metrics,
        "access_token": token
    }
    try:
        r = requests.get(url, params=params, timeout=15)
        r.raise_for_status()
        data = r.json().get("data", [])
        result = {}
        for item in data:
            result[item["name"]] = item["values"][0]["value"] if item.get("values") else 0
        return result
    except Exception as e:
        return {}

def analyze_caption(caption):
    """캡션 특성 분석"""
    if not caption:
        return {"length": 0, "has_hashtags": False, "hashtag_count": 0, "first_line": ""}
    
    lines = caption.strip().split("\n")
    first_line = lines[0][:50] if lines else ""
    hashtags = [w for w in caption.split() if w.startswith("#")]
    
    return {
        "length": len(caption),
        "has_hashtags": len(hashtags) > 0,
        "hashtag_count": len(hashtags),
        "first_line": first_line,
        "line_count": len(lines)
    }

def main():
    cfg = load_config()
    token = cfg.get("META_ACCESS_TOKEN", "").strip()
    biz_id = cfg.get("INSTAGRAM_BUSINESS_ID", "").strip()
    
    if not token or not biz_id:
        print("[ERROR] META_ACCESS_TOKEN 또는 INSTAGRAM_BUSINESS_ID 누락")
        sys.exit(1)
    
    print(f"[INFO] 계정 {biz_id} 분석 시작...")
    
    # 계정 기본 정보
    acc_url = f"https://graph.facebook.com/v20.0/{biz_id}"
    acc_params = {
        "fields": "username,name,biography,followers_count,media_count",
        "access_token": token
    }
    acc_r = requests.get(acc_url, params=acc_params, timeout=15)
    acc_r.raise_for_status()
    acc = acc_r.json()
    
    print(f"[INFO] @{acc.get('username')} | 팔로워 {acc.get('followers_count')} | 게시물 {acc.get('media_count')}")
    
    # 게시물 목록
    print("[INFO] 최근 30개 게시물 수집 중...")
    media_list = get_media_list(biz_id, token, limit=30)
    
    posts = []
    for i, m in enumerate(media_list):
        mid = m["id"]
        mtype = m.get("media_type", "IMAGE")
        caption = m.get("caption", "")
        ts = m.get("timestamp", "")
        likes = m.get("like_count", 0)
        comments = m.get("comments_count", 0)
        
        print(f"[{i+1}/{len(media_list)}] 인사이트 수집: {mid}")
        insights = get_media_insights(mid, mtype, token)
        
        reach = insights.get("reach", 0)
        saved = insights.get("saved", 0)
        shares = insights.get("shares", 0)
        views = insights.get("video_views", 0)
        
        # 종합 점수 (저장 3점, 공유 3점, 좋아요 1점, 댓글 2점)
        score = (saved * 3) + (shares * 3) + (likes * 1) + (comments * 2)
        
        cap_info = analyze_caption(caption)
        
        posts.append({
            "id": mid,
            "type": mtype,
            "timestamp": ts[:10] if ts else "",
            "likes": likes,
            "comments": comments,
            "reach": reach,
            "saved": saved,
            "shares": shares,
            "views": views,
            "score": score,
            "caption_length": cap_info["length"],
            "hashtag_count": cap_info["hashtag_count"],
            "first_line": cap_info["first_line"],
        })
    
    if not posts:
        print("[ERROR] 게시물 데이터를 가져오지 못했습니다.")
        sys.exit(1)
    
    # 정렬
    top_posts = sorted(posts, key=lambda x: x["score"], reverse=True)[:5]
    bottom_posts = sorted(posts, key=lambda x: x["score"])[:5]
    
    avg_likes = sum(p["likes"] for p in posts) / len(posts)
    avg_saves = sum(p["saved"] for p in posts) / len(posts)
    avg_reach = sum(p["reach"] for p in posts) / len(posts)
    avg_score = sum(p["score"] for p in posts) / len(posts)
    
    # 타입별 성과
    reels = [p for p in posts if p["type"] in ("VIDEO", "REELS")]
    images = [p for p in posts if p["type"] == "IMAGE"]
    carousels = [p for p in posts if p["type"] == "CAROUSEL_ALBUM"]
    
    def avg(lst, key):
        return round(sum(p[key] for p in lst) / len(lst), 1) if lst else 0
    
    now = datetime.now().strftime("%Y-%m-%d %H:%M")
    
    report = f"""# 📊 @rolling.s.cong01 계정 분석 보고서
> 생성: {now} | 분석 게시물: {len(posts)}개

## 계정 현황
| 항목 | 수치 |
|---|---|
| 팔로워 | **{acc.get('followers_count')}명** |
| 전체 게시물 | {acc.get('media_count')}개 |
| 바이오 | {acc.get('biography', '').replace(chr(10), ' / ')} |

## 평균 성과 (최근 {len(posts)}개 기준)
| 지표 | 평균 |
|---|---|
| 좋아요 | {avg_likes:.1f} |
| 저장수 | {avg_saves:.1f} |
| 도달수 | {avg_reach:.1f} |
| 종합점수 | {avg_score:.1f} |

## 포맷별 성과 비교
| 형식 | 게시물수 | 평균 좋아요 | 평균 저장 | 평균 도달 |
|---|---|---|---|---|
| 릴스/영상 | {len(reels)} | {avg(reels,'likes')} | {avg(reels,'saved')} | {avg(reels,'reach')} |
| 이미지 | {len(images)} | {avg(images,'likes')} | {avg(images,'saved')} | {avg(images,'reach')} |
| 카드뉴스 | {len(carousels)} | {avg(carousels,'likes')} | {avg(carousels,'saved')} | {avg(carousels,'reach')} |

## 🏆 TOP 5 — 가장 반응 좋은 게시물
_(저장×3 + 공유×3 + 좋아요×1 + 댓글×2 기준)_

"""
    for i, p in enumerate(top_posts, 1):
        report += f"""### {i}위 | {p['timestamp']} | {p['type']}
- **첫줄:** {p['first_line'] or '(캡션 없음)'}
- 좋아요 {p['likes']} | 저장 {p['saved']} | 공유 {p['shares']} | 도달 {p['reach']} | 댓글 {p['comments']}
- 해시태그: {p['hashtag_count']}개 | 캡션 길이: {p['caption_length']}자

"""
    
    report += """## 📉 하위 5 — 가장 반응 낮은 게시물

"""
    for i, p in enumerate(bottom_posts, 1):
        report += f"""### {i}위 | {p['timestamp']} | {p['type']}
- **첫줄:** {p['first_line'] or '(캡션 없음)'}
- 좋아요 {p['likes']} | 저장 {p['saved']} | 공유 {p['shares']} | 도달 {p['reach']}

"""
    
    # 패턴 인사이트
    top_avg_hashtags = sum(p["hashtag_count"] for p in top_posts) / len(top_posts) if top_posts else 0
    bot_avg_hashtags = sum(p["hashtag_count"] for p in bottom_posts) / len(bottom_posts) if bottom_posts else 0
    top_avg_caption = sum(p["caption_length"] for p in top_posts) / len(top_posts) if top_posts else 0
    bot_avg_caption = sum(p["caption_length"] for p in bottom_posts) / len(bottom_posts) if bottom_posts else 0
    
    report += f"""## 🔍 패턴 분석

| 비교 항목 | 상위 5개 평균 | 하위 5개 평균 |
|---|---|---|
| 해시태그 수 | {top_avg_hashtags:.1f}개 | {bot_avg_hashtags:.1f}개 |
| 캡션 길이 | {top_avg_caption:.0f}자 | {bot_avg_caption:.0f}자 |

## 💡 리서처 액션 아이템
1. 상위 게시물의 공통 주제·첫줄 패턴을 라이터에게 전달
2. 저장수가 높은 게시물 형식(릴스 vs 카드뉴스) 우선 확대
3. 해시태그 효과 검증: 상위 vs 하위 차이 기반으로 최적 개수 추천
4. 도달수 대비 저장율 = 진성 콘텐츠 지표 — 이 비율 높은 게시물 분석 우선

_이 보고서는 Instagram Graph API 실제 데이터 기반입니다._
"""
    
    with open(REPORT_PATH, "w", encoding="utf-8") as f:
        f.write(report)
    
    print(f"\n[SUCCESS] 분석 완료 → {REPORT_PATH}")
    print(f"[결과] 팔로워 {acc.get('followers_count')} | 분석 {len(posts)}개 | TOP 저장수 {top_posts[0]['saved'] if top_posts else 0}")

if __name__ == "__main__":
    main()
