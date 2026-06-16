# 📷 Instagram — 도구 매니페스트

_Instagram 에이전트가 어떤 도구를 어디까지 자율적으로 쓸 수 있는지 정의합니다._
_매번 시스템 프롬프트로 주입되며, 텔레그램에서 `/tools`로 현재 상태 확인 가능._

---

## 자율도 레벨

AUTONOMY_LEVEL: 2

| 값 | 의미 |
|---|---|
| 0 | Off — 도구 전체 비활성 (이 에이전트는 채팅만) |
| 1 | Read-only — 읽기·분석·보고만, 외부에 쓰기 X |
| 2 | Draft — 초안 작성 후 사용자 승인 게이트 통과해야 실행 ⭐ 권장 기본값 |
| 3 | Auto — 화이트리스트 안에서 사용자 승인 없이 실행 |

> 위 `AUTONOMY_LEVEL` 줄의 숫자(0~3)를 직접 바꾸면 다음 호출부터 적용됩니다.

---

## 사용 가능한 도구

### `instagram_trend_sniper.py`
웹 검색을 통해 대표님이 지정하신 키워드들의 최근 인스타그램 콘텐츠 트렌드, 태그 노출 방식을 분석하여 트렌드 분석 보고서를 작성합니다.

- 실행: `python instagram_trend_sniper.py`
- 결과 파일: `_agents/instagram/instagram_trend_report.md`

### `instagram_feed_drafter.py`
지정된 테마(주제)를 기반으로 즉시 업로드 가능한 5슬라이드 카드뉴스 기획안, 캡션, 해시태그 목록 및 Reels 대본을 마크다운 초안으로 작성합니다.

- 실행: `python instagram_feed_drafter.py`
- 결과 파일: `_agents/instagram/drafts/instagram_post_draft.md`

### `publish_instagram.py`
발급된 Meta Graph API 토큰을 사용하여 인스타그램 계정 연결을 검증하거나, 로컬 이미지 또는 이미지 URL을 지정된 캡션과 함께 인스타그램 피드에 자동으로 게시합니다. (로컬 이미지의 경우 연동된 워드프레스를 이미지 CDN으로 활용해 임시 업로드 후 발행합니다.)

- 검증 실행: `python publish_instagram.py verify`
- 발행 실행: `python publish_instagram.py publish <image_path_or_url> <caption_text>`


---

## 안전 규칙 (모든 레벨 공통, 절대 우회 X)

- **삭제·배포·발송**(rm, deploy --prod, send, publish) 류는 자율도와 무관하게 **항상 승인 게이트**.
- 외부 API 호출 전 `config.md`의 토큰 존재 여부 확인.
- 모든 외부 행동은 `_agents/instagram/activity.log`에 한 줄 기록 (감사용).
- 승인 대기 액션은 `approvals/pending/` 에 저장 → 텔레그램 `/approvals` 로 조회.

---

_레벨을 어떻게 골라야 할지 모르겠다면 `2 (Draft)`가 안전한 시작점입니다._
