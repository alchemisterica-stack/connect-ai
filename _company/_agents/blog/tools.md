# 📝 블로그 에이전트 도구 매니페스트 (Tools Manifest)

_블로그 에이전트가 어떤 도구를 사용하여 포스팅 기획서 및 서머리 초안을 자동 생성하는지 기술합니다._

---

## 자율도 레벨

AUTONOMY_LEVEL: 2

---

## 사용 가능한 도구

### `blog_post_generator.py`
대표님이 입력하신 학습 교재 텍스트(또는 PDF 파일 내용)나 인스타 감성 글귀, 집 반찬 메뉴 정보를 분석하여 완성도 높은 블로그 포스팅 원고를 자동 생성하고 카테고리별 마크다운 파일로 영구 저장합니다.

- 실행: `python blog_post_generator.py`
- 결과 파일: 
  * 학습 서머리: `_agents/blog/drafts/study/` 폴더 내에 저장
  * 심리 칼럼: `_agents/blog/drafts/mindset/` 폴더 내에 저장
  * 집 반찬: `_agents/blog/drafts/recipe/` 폴더 내에 저장
