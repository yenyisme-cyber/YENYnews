#!/usr/bin/env python3
"""예니뉴스 사이트 생성기.

기사 원고(content/articles/*.md)와 안내 페이지(content/pages/*.md)를 읽어
index.html, articles/*.html, category/*.html, pages/*.html 을 만듭니다.

사용법:  python3 build.py
기사 추가: content/articles/ 에 원고 파일 하나를 넣고 다시 실행하면
           첫 화면·분야별 목록·전체기사 목록이 함께 바뀝니다.
"""
import html
import re
import sys
from datetime import date
from pathlib import Path

import markdown

ROOT = Path(__file__).resolve().parent

# ---------------------------------------------------------------------------
# 신문 등록사항 — 등록증을 받으면 여기만 고치면 모든 페이지 하단이 바뀝니다.
# 비어 있는 값("")은 화면에 [기재 예정] 으로 표시됩니다.
# ---------------------------------------------------------------------------
SITE = {
    "name": "예니뉴스",
    "tagline": "배움과 사람을 잇는 인터넷신문",
    "reg_no": "",          # 등록번호 (예: 서울 아00000)
    "reg_date": "",        # 등록연월일
    "pub_date": "",        # 최초 발행연월일
    "publisher": "",       # 발행인
    "editor": "",          # 편집인
    "youth_officer": "",   # 청소년보호책임자
    "address": "",         # 주사무소 주소
    "phone": "",           # 대표 전화
    "email": "",           # 대표 이메일 (기사제보 받을 주소)
    "biz_no": "",          # 사업자등록번호
}

CATEGORIES = [  # (주소용 이름, 화면 이름)
    ("edu", "교육"),
    ("society", "사회"),
    ("economy", "경제"),
    ("culture", "문화"),
    ("life", "라이프"),
    ("opinion", "오피니언"),
    ("interview", "인터뷰"),
]
CAT_SLUG = {name: slug for slug, name in CATEGORIES}

FOOTER_PAGES = [  # (파일 이름, 화면 이름, 강조 여부)
    ("about", "회사소개", False),
    ("ethics", "윤리강령", False),
    ("privacy", "개인정보처리방침", True),
    ("youth", "청소년보호정책", True),
    ("no-email", "이메일무단수집거부", False),
    ("report", "기사제보", False),
    ("ads", "광고문의", False),
]

PH_STYLES = ["", " c", " b"]  # 사진 없는 기사의 썸네일 색 순환


# ---------------------------------------------------------------------------
# 원고 읽기
# ---------------------------------------------------------------------------
def parse_doc(path):
    """--- 로 감싼 머리말(key: value)과 본문(마크다운)을 나눕니다."""
    text = path.read_text(encoding="utf-8")
    meta, body = {}, text
    m = re.match(r"^---\s*\n(.*?)\n---\s*\n(.*)$", text, re.S)
    if m:
        body = m.group(2)
        key = None
        for line in m.group(1).splitlines():
            if re.match(r"^\s+-\s+", line) and key:  # 목록 값 (출처 등)
                meta.setdefault(key, [])
                if isinstance(meta[key], str):
                    meta[key] = [meta[key]] if meta[key] else []
                meta[key].append(re.sub(r"^\s+-\s+", "", line).strip())
            elif ":" in line:
                key, val = line.split(":", 1)
                key = key.strip()
                meta[key] = val.strip()
    return meta, body.strip()


def load_articles():
    arts = []
    for p in sorted((ROOT / "content" / "articles").glob("*.md")):
        if p.name.startswith("_"):  # _로 시작하는 파일은 견본이라 건너뜀
            continue
        meta, body = parse_doc(p)
        if meta.get("status", "publish") != "publish":
            continue
        missing = [k for k in ("title", "category", "author", "date") if not meta.get(k)]
        if missing:
            sys.exit(f"[중단] {p.name}: 머리말에 {', '.join(missing)} 이(가) 없습니다.")
        if meta["category"] not in CAT_SLUG:
            sys.exit(f"[중단] {p.name}: 분야 '{meta['category']}' 는 없는 분야입니다. "
                     f"가능한 값: {', '.join(CAT_SLUG)}")
        meta["slug"] = p.stem
        meta["body_html"] = markdown.markdown(body, extensions=["extra", "sane_lists"])
        meta["summary"] = meta.get("deck") or re.sub(r"\s+", " ", re.sub(r"[#>*_\[\]()`-]", "", body))[:120]
        sources = meta.get("sources", [])
        meta["sources"] = sources if isinstance(sources, list) else ([sources] if sources else [])
        arts.append(meta)
    arts.sort(key=lambda a: (a["date"], a["slug"]), reverse=True)
    for i, a in enumerate(arts):
        a["ph"] = PH_STYLES[i % 3]
    return arts


# ---------------------------------------------------------------------------
# 공통 틀
# ---------------------------------------------------------------------------
e = html.escape


def reg(v, label="기재 예정"):
    return e(v) if v else f'<span class="fill">[{label}]</span>'


def head(title, root, desc=""):
    full = f"{title} - {SITE['name']}" if title != SITE["name"] else title
    return f"""<!DOCTYPE html>
<html lang="ko">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>{e(full)}</title>
<meta name="description" content="{e(desc or SITE['tagline'])}">
<link rel="stylesheet" href="https://cdn.jsdelivr.net/gh/orioncactus/pretendard@v1.3.9/dist/web/static/pretendard.min.css">
<link rel="stylesheet" href="{root}assets/style.css">
</head>
<body>
"""


def header(root, active=""):
    nav = "".join(
        f'<a href="{root}category/{slug}.html"{" class=\"on\"" if active == slug else ""}>{name}</a>'
        for slug, name in CATEGORIES
    )
    all_on = ' class="on"' if active == "all" else ""
    return f"""<div class="topbar">
  <div class="wrap">
    <span id="today"></span>
    <nav>
      <a href="{root}pages/report.html">기사제보</a>
      <a href="{root}pages/ads.html">광고문의</a>
    </nav>
  </div>
</div>
<header class="masthead">
  <div class="wrap">
    <a href="{root}index.html" class="logo" aria-label="{SITE['name']} 홈">
      <b>예니<span>뉴스</span></b>
      <small>{e(SITE['tagline'])}</small>
    </a>
  </div>
</header>
<nav class="gnb" aria-label="주요 메뉴">
  <div class="wrap">
    <a href="{root}articles/index.html"{all_on}>전체기사</a>
    {nav}
  </div>
</nav>
"""


def footer(root):
    links = "".join(
        f'<a href="{root}pages/{slug}.html"{" class=\"strong\"" if strong else ""}>{name}</a>'
        for slug, name, strong in FOOTER_PAGES
    )
    s = SITE
    return f"""<footer>
  <div class="wrap">
    <div class="f-links">{links}</div>
    <div class="f-logo">예니<span>뉴스</span></div>
    <!-- 신문법 제19조 필요적 게재사항 + 청소년보호책임자 (build.py 의 SITE 에서 수정) -->
    <div class="reg">
      <span><b>제호</b>{e(s['name'])}</span>
      <span><b>등록번호</b>{reg(s['reg_no'], '등록 후 기재')}</span>
      <span><b>등록일</b>{reg(s['reg_date'], '등록 후 기재')}</span>
      <span><b>발행일</b>{reg(s['pub_date'])}</span>
      <span><b>발행인</b>{reg(s['publisher'])}</span>
      <span><b>편집인</b>{reg(s['editor'])}</span>
      <span><b>청소년보호책임자</b>{reg(s['youth_officer'])}</span>
    </div>
    <div class="reg">
      <span><b>주소</b>{reg(s['address'])}</span>
      <span><b>전화</b>{reg(s['phone'])}</span>
      <span><b>이메일</b>{reg(s['email'])}</span>
      <span><b>사업자등록번호</b>{reg(s['biz_no'])}</span>
    </div>
    <p class="copy">{e(s['name'])}의 모든 콘텐츠는 저작권법의 보호를 받으며, 무단 전재·복사·배포를 금합니다. © {e(s['name'])}</p>
  </div>
</footer>
<script>
  (function(){{
    var d=new Date(),w=['일','월','화','수','목','금','토'];
    document.getElementById('today').textContent=d.getFullYear()+'년 '+(d.getMonth()+1)+'월 '+d.getDate()+'일 ('+w[d.getDay()]+')';
  }})();
</script>
</body>
</html>
"""


def fmt_date(d):
    return d.replace("-", ".")


def thumb(a, root, label=""):
    if a.get("image"):
        return f'<img class="ph" src="{root}{e(a["image"])}" alt="" style="object-fit:cover;padding:0">'
    return f'<div class="ph{a["ph"]}">{label or "예니뉴스"}</div>'


def link(a, root):
    return f"{root}articles/{a['slug']}.html"


# ---------------------------------------------------------------------------
# 견본 기사 (실제 기사가 부족한 자리를 채움, 모두 "예시" 표시)
# ---------------------------------------------------------------------------
def sample(n, cat="교육"):
    return {
        "sample": True, "title": f"기사 제목 자리 {n}", "category": cat,
        "summary": "기사가 올라오면 이 자리가 자동으로 바뀝니다.",
        "author": "기자명", "date": "2026-00-00", "ph": PH_STYLES[n % 3],
    }


def fill(arts, k):
    out = list(arts[:k])
    cats = [c for _, c in CATEGORIES]
    while len(out) < k:
        out.append(sample(len(out) + 1, cats[len(out) % len(cats)]))
    return out


def tag(a):
    return '<span class="sample">예시</span>' if a.get("sample") else ""


def href(a, root):
    return "#" if a.get("sample") else link(a, root)


# ---------------------------------------------------------------------------
# 페이지 만들기
# ---------------------------------------------------------------------------
def feed_items(items, root):
    return "".join(
        f'<a href="{href(a, root)}">{thumb(a, root)}<div><div class="cat">{e(a["category"])}</div>'
        f'<h3 class="t">{tag(a)}{e(a["title"])}</h3><p>{e(a["summary"])}</p>'
        f'<div class="meta">{e(a["author"])} · {fmt_date(a["date"])}</div></div></a>'
        for a in items
    )


def build_index(arts):
    """첫 화면. 실제 기사만 보여 주고, 기사가 모자란 칸은 숨깁니다."""
    root = ""
    lead, side, latest = (arts[0] if arts else None), arts[1:5], arts[5:10]
    rank = arts[:5]
    opinion = [a for a in arts if a["category"] == "오피니언"][:3]

    if lead:
        side_html = "".join(
            f'<a href="{link(a, root)}"><div><div class="cat">{e(a["category"])}</div>'
            f'<h3 class="t">{e(a["title"])}</h3></div>{thumb(a, root)}</a>'
            for a in side
        )
        top = f"""<section class="top{' solo' if not side else ''}" style="margin-top:22px">
    <a href="{link(lead, root)}" class="lead">
      {thumb(lead, root, "")}
      <div class="cat">{e(lead["category"])}</div>
      <h1 class="t">{e(lead["title"])}</h1>
      <p>{e(lead["summary"])}</p>
      <div class="meta">{e(lead["author"])} · 입력 {fmt_date(lead["date"])}</div>
    </a>
    {f'<div class="side-list">{side_html}</div>' if side else ''}
  </section>"""
    else:
        top = '<p style="padding:80px 0;text-align:center;color:#8a929e">첫 기사를 준비하고 있습니다.</p>'

    latest_block = ""
    if latest:
        latest_block = f"""<div class="sec-h"><h2>최신 기사</h2><a href="articles/index.html">전체보기 ›</a></div>
      <div class="feed">{feed_items(latest, root)}</div>"""
    elif arts:
        latest_block = f"""<div class="sec-h"><h2>전체 기사</h2><a href="articles/index.html">전체보기 ›</a></div>
      <div class="feed">{feed_items(arts, root)}</div>"""
    rank_html = "".join(f'<li><a href="{link(a, root)}">{e(a["title"])}</a></li>' for a in rank)
    rank_block = f"""<div class="rank"><div class="sec-h"><h2>주요 기사</h2></div><ol>{rank_html}</ol></div>""" if len(rank) >= 3 else ""
    op_block = ""
    if opinion:
        op_html = "".join(
            f'<a href="{link(a, root)}"><b>{e(a.get("column", "칼럼"))}</b><span>{e(a["title"])}</span></a>'
            for a in opinion)
        op_block = f'<div class="opinion"><div class="sec-h"><h2>오피니언</h2></div>{op_html}</div>'

    page = head(SITE["name"], root) + header(root) + f"""
<main class="wrap">
  {top}
  <div class="body">
    <section>
      {latest_block}
      <a href="articles/index.html" class="more">전체 기사 보기</a>
    </section>
    <aside>
      {rank_block}
      <div class="edu-box">
        <small>예니뉴스 부설 평생교육원</small>
        <h3>배움을 다시 시작하는<br>어른을 위한 온라인 강좌</h3>
        <p>예니뉴스가 운영하는 평생교육원입니다. 교육과정은 준비 중입니다.</p>
      </div>
      {op_block}
    </aside>
  </div>
</main>
""" + footer(root)
    (ROOT / "index.html").write_text(page, encoding="utf-8")


def build_article(a, arts):
    root = "../"
    srcs = ""
    if a["sources"]:
        items = []
        for s in a["sources"]:
            if "|" in s:
                t, u = [x.strip() for x in s.split("|", 1)]
                items.append(f'<li>{e(t)} — <a href="{e(u)}" rel="noopener">{e(u)}</a></li>')
            else:
                items.append(f"<li>{e(s)}</li>")
        srcs = f'<div class="sources"><b>참고 자료</b><ul>{"".join(items)}</ul></div>'
    updated = f'<span>수정 {fmt_date(a["updated"])}</span>' if a.get("updated") else ""
    email = f'<span>{e(a["email"])}</span>' if a.get("email") else ""
    related = [x for x in arts if x["slug"] != a["slug"] and x["category"] == a["category"]][:3]
    rel_html = ""
    if related:
        rel_html = f"""<section class="related wrap"><div class="sec-h"><h2>{e(a["category"])} 다른 기사</h2></div>
<div class="feed">{feed_items(related, root)}</div></section>"""
    page = head(a["title"], root, a["summary"]) + header(root, CAT_SLUG[a["category"]]) + f"""
<main class="wrap">
  <article class="article">
    <a class="cat" href="{root}category/{CAT_SLUG[a["category"]]}.html">{e(a["category"])}</a>
    <h1>{e(a["title"])}</h1>
    {f'<p class="deck">{e(a["deck"])}</p>' if a.get("deck") else ""}
    <div class="byline"><b>{e(a["author"]) + ("" if "편집국" in a["author"] else " 기자")}</b>{email}<span>입력 {fmt_date(a["date"])}</span>{updated}</div>
    {f'<img src="{root}{e(a["image"])}" alt="{e(a.get("image_caption", ""))}" style="margin-top:24px;border-radius:4px">' if a.get("image") else ""}
    <div class="article-body">{a["body_html"]}</div>
    {srcs}
    <p class="endnote">{e(SITE["name"])} 기사 무단 전재·재배포 금지</p>
  </article>
</main>
{rel_html}
""" + footer(root)
    out = ROOT / "articles" / f"{a['slug']}.html"
    out.write_text(page, encoding="utf-8")


def build_list(title, items, out_path, root, active):
    body = feed_items(items, root) if items else '<p style="padding:40px 0;color:#8a929e">아직 기사가 없습니다.</p>'
    page = head(title, root) + header(root, active) + f"""
<main class="wrap" style="max-width:900px">
  <div class="sec-h" style="margin-top:30px"><h2>{e(title)}</h2><span style="font-size:13px;color:#8a929e">{len(items)}건</span></div>
  <div class="feed">{body}</div>
</main>
""" + footer(root)
    out_path.parent.mkdir(parents=True, exist_ok=True)
    out_path.write_text(page, encoding="utf-8")


def fill_tokens(text):
    """안내 페이지 원고 속 {{발행인}} 같은 자리를 SITE 값으로 바꿉니다."""
    keys = {"제호": "name", "발행인": "publisher", "편집인": "editor",
            "청소년보호책임자": "youth_officer", "주소": "address",
            "전화": "phone", "이메일": "email", "사업자등록번호": "biz_no"}
    def rep(m):
        v = SITE.get(keys.get(m.group(1), ""), "")
        return v if v else f"[{m.group(1)} 기재 예정]"
    return re.sub(r"\{\{(.+?)\}\}", rep, text)


def build_pages():
    root = "../"
    for p in sorted((ROOT / "content" / "pages").glob("*.md")):
        meta, body = parse_doc(p)
        body_html = markdown.markdown(fill_tokens(body), extensions=["extra", "sane_lists"])
        title = meta.get("title", p.stem)
        page = head(title, root) + header(root) + f"""
<main class="wrap"><div class="page"><h1>{e(title)}</h1>{body_html}</div></main>
""" + footer(root)
        out = ROOT / "pages" / f"{p.stem}.html"
        out.parent.mkdir(exist_ok=True)
        out.write_text(page, encoding="utf-8")


def main():
    arts = load_articles()
    (ROOT / "articles").mkdir(exist_ok=True)
    # 원고가 사라진 기사 페이지는 정리 (견본·목록 페이지 제외)
    keep = {f"{a['slug']}.html" for a in arts} | {"index.html"}
    for old in (ROOT / "articles").glob("*.html"):
        if old.name not in keep:
            old.unlink()
    build_index(arts)
    for a in arts:
        build_article(a, arts)
    build_list("전체기사", arts, ROOT / "articles" / "index.html", "../", "all")
    for slug, name in CATEGORIES:
        build_list(name, [a for a in arts if a["category"] == name],
                   ROOT / "category" / f"{slug}.html", "../", slug)
    build_pages()
    print(f"완료: 기사 {len(arts)}건, 안내 페이지 {len(list((ROOT / 'content' / 'pages').glob('*.md')))}개")


if __name__ == "__main__":
    main()
