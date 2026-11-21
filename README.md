# 예니뉴스

인터넷신문 예니뉴스 사이트 (GitHub Pages, 정적 사이트).

## 구조
- `content/articles/` — 기사 원고 (기사 1건 = `.md` 파일 1개). 형식은 `_sample.md` 참고
- `content/pages/` — 회사소개·윤리강령·개인정보처리방침·청소년보호정책 등 안내 페이지 원고
- `build.py` — 원고를 읽어 `index.html`, `articles/`, `category/`, `pages/` 를 만듭니다
- `assets/style.css` — 공통 디자인

## 기사 발행
1. `content/articles/_sample.md` 를 복사해 `2026-11-22-주제.md` 처럼 이름을 붙입니다
2. 머리말(제목·분야·기자·날짜)과 본문을 쓰고 `status: publish` 로 바꿉니다
3. `python3 build.py` 를 실행한 뒤 커밋·푸시하면 1~2분 안에 사이트에 반영됩니다

## 등록사항
신문 등록증을 받으면 `build.py` 맨 위 `SITE` 의 빈칸만 채우고 다시 빌드하면 모든 페이지 하단이 바뀝니다.
