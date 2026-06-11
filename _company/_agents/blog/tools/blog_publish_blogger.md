# 📈 구글 블로거 자동 발행

이 도구는 작성된 최신 글 또는 지정한 마크다운 파일의 내용을 대표님의 구글 블로거(Blogger / Blogspot)에 Blogger API v3를 통해 자동으로 발행합니다.

## 입력 값 및 사용 방법
도구가 실행되면 `blog_account.json`에 정의된 `BLOG_ID`, `BLOGGER_API_KEY`를 로드하여 인증한 후, 가장 최근에 작성된 드래프트 포스팅을 로드해 원격 전송합니다.

*   만약 특정 포스팅 파일을 발행하고 싶다면 스크립트 실행 인자로 파일 경로를 전달할 수 있습니다:
    `python blog_publish_blogger.py [파일 경로]`
