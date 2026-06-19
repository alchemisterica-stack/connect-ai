# 요리 블로그 자동 발행 시스템 업무 인계 브리핑

이 문서는 새로운 대화방(방)에서 요리 블로그 자동 발행 및 관리를 계속 진행할 때, 새 AI 비서에게 그대로 복사하여 전달할 수 있는 컨텍스트 정리 파일입니다.

---

## 1. 프로젝트 개요 & 역할
- **목표**: 사용자 요리 메모 및 실사 사진을 스캔하거나 트렌드 리포트를 분석하여, WordPress와 Google Blogger에 최적화된 포스팅을 자동 발행합니다.
- **핵심 역할**: 요리 반찬 카테고리 레시피 블로그 포스팅 생성 및 업로드 자동화 관리.

---

## 2. 관련 핵심 파일 경로
- **주요 실행 스크립트**:
  - [blog_post_generator.py](file:///C:/Users/User/.connect-ai-brain/_company/_agents/blog/tools/blog_post_generator.py): 마크다운 텍스트를 HTML로 파싱하는 코어 파서(`markdown_to_html_for_blogger`) 및 업로드 로직 내장.
  - [publish_recipe_auto.py](file:///C:/Users/User/.connect-ai-brain/_company/_agents/blog/tools/publish_recipe_auto.py): 트렌드 리포트를 분석하여 미발행 요리를 자동 발행하는 스크립트.
  - [publish_recipe_monday_scan.py](file:///C:/Users/User/.connect-ai-brain/_company/_agents/blog/tools/publish_recipe_monday_scan.py): 로컬 폴더를 스캔하여 직접 준비한 실사 이미지와 요리 메모(`{요리명}_memo.txt`)를 기반으로 레시피를 발행하는 스크립트.
- **설정 및 데이터 파일**:
  - [blog_account.json](file:///C:/Users/User/.connect-ai-brain/_company/_agents/blog/tools/blog_account.json): 블로그 API 계정 정보 및 API Key 설정 파일.
  - [blog_queue.json](file:///C:/Users/User/.connect-ai-brain/_company/_agents/blog/tools/blog_queue.json): 발행 완료 이력 및 대기열 정보 파일.
- **실사 사진 및 사용자 메모 저장 위치**:
  - [assets/custom_recipe_photos/](file:///C:/Users/User/my-ai-office/assets/custom_recipe_photos)
  - [_company/자료/](file:///C:/Users/User/my-ai-office/_company/자료)

---

## 3. 요리 포스팅 발행 필수 규칙 (체크리스트)
새 AI 비서는 글을 생성하거나 프롬프트를 수정할 때 반드시 아래 규칙들을 엄격히 지켜야 합니다.

- [ ] **1블로그 1요리 원칙**: 한 포스팅에 여러 요리를 나열하지 않고, 지정된 단 **하나의 핵심 요리**만 집중적으로 다룹니다.
- [ ] **퀴즈 포함 금지**: 요리 포스팅에는 절대로 자가진단이나 퀴즈(Q&A)를 포함하지 않습니다.
- [ ] **네이버 블로그 스타일 가독성**:
  - **마이크로 문단**: 스마트폰 화면을 고려해 문장은 1~2개 단위로 매우 짧게 단락을 나눕니다.
  - **여백 확보**: 문단과 문단 사이에는 반드시 빈 줄을 2줄 이상(엔터 3번) 띄웁니다.
- [ ] **구글 블로거 시각적 강약 조절 (HTML 변환 보장)**:
  - 밋밋한 글이 되지 않도록 마크다운 소제목 기호(`##`, `###`), 강조 기호(`**강조**`), 인용구 기호(`&gt; `)를 반드시 적절히 사용하여 글의 구조와 포인트를 줍니다.
  - 재료 목록은 표(Table) 또는 명확한 글머리 기호 리스트 형식으로 한눈에 정리합니다.
  - 번호 매기기 목록(`1.`, `2.`)은 파서가 인식할 수 있도록 줄 첫머리에 명확하게 작성합니다.
- [ ] **채널별 톤앤매너 분리**:
  - **Wordpress**: 다정하고 따뜻한 이웃집 스토리텔링 말투.
  - **Blogger**: 전문적이고 깔끔한 레시피 카드 중심 말투.

---

## 4. 새 대화방 사용 예시
새로운 대화방을 열고 대화창에 아래 텍스트를 그대로 복사해서 붙여넣으시면 됩니다.

> **[새 대화방 시작 시 붙여넣을 프롬프트]**
> ```text
> 안녕하세요. 이 대화방에서는 "요리/반찬 레시피 블로그 포스팅 발행 및 관리" 작업만 단독으로 수행하겠습니다.
> C:/Users/User/.gemini/antigravity/brain/cd3b9191-ef13-4ae5-9c5c-cb4854cbbb82/cooking_blog_briefing.md 파일을 열어 관련 파일 경로와 핵심 발행 규칙(1블로그 1요리, 퀴즈 배제, 네이버식 1-2문장 단락 구분, 구글 블로거 시각적 강약 조절 등)을 파악해 주세요.
> 파악이 완료되면, 현재 요리 발행 시스템 구조를 이해했다고 짧게 답변해 주세요.
> ```
