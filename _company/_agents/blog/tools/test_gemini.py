import requests
import os
import json

key = ""
url = f"https://generativelanguage.googleapis.com/v1beta/models/gemini-3.1-flash-lite:generateContent?key={key}"

HERE = os.path.dirname(os.path.abspath(__file__))
txt_path = r"C:\Users\User\.connect-ai-brain\_company\00_Raw\청소년복지론\3주차_1교시.txt"

print("Reading 3주차_1교시.txt...")
with open(txt_path, "r", encoding="utf-8") as f:
    content = f.read()

prompt = f"""당신은 자격증 시험 전문 교육 블로거입니다.
아래 제공된 '청소년지도사' 관련 학습 텍스트 및 온라인 검색 참고자료를 바탕으로 워드프레스와 구글 블로거에 각각 업로드할 두 가지 버전의 글을 작성하세요.

[요청 주제/키워드]
{content}

[출력 요구사항 및 포맷]
========== WORDPRESS VERSION ==========
# [워드프레스용 제목]
(본문은 아주 따뜻하고 친근하며 다정한 어조로 작성해 주세요. 불릿 포인트나 정리 표 등을 통해 상세히 설명해 주세요. 마크다운 예시 기호 # 나 bold 기호 ** 는 제거하고 줄바꿈과 텍스트 위주로 작성하세요. 마지막에 독자들을 응원하는 다정한 멘트를 추가하세요.)

========== BLOGGER VERSION ==========
# [블로거용 제목]
(본문은 담담하고 핵심 중심의 간결하며 정돈된 전문적인 어조로 작성해 주세요. 핵심 본문은 표(Table) 또는 구조화된 도표 형식을 적극 활용하여 한눈에 정리되게 작성해 주시고, 마크다운 기호 # 나 ** 는 제거하고 핵심만 빠르게 읽을 수 있도록 요약해 주세요. 본문 마지막에는 공부한 내용을 직관적으로 점검할 수 있도록 O/X 퀴즈 2문항과 각각의 정답 및 해설을 추가해 주세요.)
"""

print("Sending actual prompt to Google Gemini API (gemini-3.1-flash-lite)...")
try:
    r = requests.post(
        url, 
        headers={"Content-Type": "application/json"},
        json={"contents": [{"parts": [{"text": prompt}]}]},
        timeout=30
    )
    print(f"Status Code: {r.status_code}")
    if r.status_code == 200:
        print("SUCCESS!")
        print(r.json()["candidates"][0]["content"]["parts"][0]["text"][:1000])
    else:
        print("FAILED!")
        print(r.text)
except Exception as e:
    print("Error:", e)
