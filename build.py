#!/usr/bin/env python3
"""Сборка сайта «Курс дела».

Запуск:  python3 build.py
Материалы лежат в content/*.md, готовый сайт собирается в docs/ (эту папку раздаёт GitHub Pages).
Перед выкладкой поменяй SITE_URL и CONTACT ниже.
"""
import html, json, re, shutil, datetime as dt
from pathlib import Path

# ---------- настройки ----------
SITE_URL = "https://lcwy77.github.io/kursdela"   # после покупки домена заменить на него, без косой черты в конце
SITE_NAME = "Курс дела"
TAGLINE = "Политика и экономика: что произошло, сколько это стоит и кому выгодно."
AUTHOR = "Алексей Лисовский"
CHANNEL = "https://t.me/economskepticism"
CONTACT = "@mishaasublime"                # контакт для рекламы и консультаций
# -------------------------------

ROOT = Path(__file__).parent
SRC, STATIC, OUT = ROOT / "content", ROOT / "static", ROOT / "docs"

RUBRICS = {  # ключ: (название, файл, описание для поиска)
    "konflikty": ("Конфликты", "konflikty.html", "Корпоративные споры: кто с кем судится, позиции сторон, решения судов и то, как компании ведут себя публично."),
    "ekonomika": ("Экономика", "ekonomika.html", "Экономика, финансы и бизнес России: бюджет, банки, рынки, компании."),
    "politika": ("Политика", "politika.html", "Российская политика и международные контакты."),
    "mir": ("Мир", "mir.html", "Политики и события Запада, Европы и Китая."),
    "ukraina": ("Украина", "ukraina.html", "Что происходит на Украине и вокруг неё."),
}
MONTHS = "января февраля марта апреля мая июня июля августа сентября октября ноября декабря".split()


def esc(s):
    return html.escape(str(s), quote=True)


def ru_date(d):
    return f"{d.day} {MONTHS[d.month - 1]} {d.year}"


def inline(s):
    s = esc(s)
    s = re.sub(r"\[([^\]]+)\]\((https?://[^)\s]+)\)", r'<a href="\2" rel="noopener">\1</a>', s)
    return re.sub(r"\*\*(.+?)\*\*", r"<strong>\1</strong>", s)


def md(body):
    return "\n".join(f"<p>{inline(' '.join(b.split()))}</p>" for b in re.split(r"\n\s*\n", body.strip()) if b.strip())


def load():
    posts = []
    for f in sorted(SRC.glob("*.md")):
        head, body = f.read_text(encoding="utf-8").split("\n---\n", 1)
        meta, sources = {}, []
        for line in head.splitlines():
            if not line.strip() or line.strip() == "---":
                continue
            k, v = line.split(":", 1)
            k, v = k.strip(), v.strip()
            if k == "src":
                t, u = v.rsplit("|", 1)
                sources.append((t.strip(), u.strip()))
            else:
                meta[k] = v
        meta["date"] = dt.datetime.strptime(meta["date"], "%Y-%m-%d %H:%M")
        meta["updated"] = dt.datetime.strptime(meta["updated"], "%Y-%m-%d %H:%M") if "updated" in meta else meta["date"]
        meta.update(slug=f.stem, sources=sources, body=md(body), plain=" ".join(body.split()))
        meta.setdefault("seo_title", meta["title"])
        posts.append(meta)
    return sorted(posts, key=lambda p: p["date"], reverse=True)


CSS = """
/* Раскладка: лаймовая плашка-шапка с логотипом, под ней одна читаемая колонка; всё выровнено влево. */
:root{--paper:#F6F7EE;--ink:#121110;--muted:#565A4C;--rule:#D5D9C4;--lime:#CCFF33;--on-lime:#121110;--mark:#E9F7A8;
 --display:"Inter","Helvetica Neue",Arial,sans-serif;--text:"PT Serif",Georgia,"Times New Roman",serif}
@media (prefers-color-scheme:dark){:root:not([data-theme="light"]){--paper:#121110;--ink:#F1F3E6;--muted:#A5A996;--rule:#34362E;--mark:#39451A;color-scheme:dark}}
:root[data-theme="dark"]{--paper:#121110;--ink:#F1F3E6;--muted:#A5A996;--rule:#34362E;--mark:#39451A;color-scheme:dark}
*{box-sizing:border-box}
body{margin:0;background:var(--paper);color:var(--ink);font:400 1.125rem/1.6 var(--text);-webkit-text-size-adjust:100%}
a{color:inherit;text-decoration-color:var(--muted);text-underline-offset:.18em}
a:hover{text-decoration-color:currentColor}
a:focus-visible,summary:focus-visible{outline:3px solid var(--ink);outline-offset:3px;border-radius:2px}
.wrap{max-width:70rem;margin-inline:auto;padding-inline:clamp(1rem,4vw,2.5rem)}
.slab{background:var(--lime);color:var(--on-lime)}
.slab a:focus-visible{outline-color:var(--on-lime)}
.top{display:flex;flex-wrap:wrap;align-items:baseline;justify-content:space-between;gap:.5rem 2rem;padding-block:1.1rem}
.logo{font:900 1.5rem/1 var(--display);letter-spacing:-.03em;text-decoration:none;text-transform:uppercase}
nav{display:flex;flex-wrap:wrap;gap:.35rem 1.25rem;font:600 .95rem/1.3 var(--display)}
nav a{text-decoration:none;padding-block:.2rem;border-bottom:2px solid transparent}
nav a:hover,nav a[aria-current="page"]{border-bottom-color:currentColor}
.hero{padding-block:clamp(1.5rem,5vw,3.5rem) clamp(1.75rem,5vw,3.25rem)}
.hero h1{margin:0;font:900 clamp(3.25rem,15vw,11rem)/.86 var(--display);letter-spacing:-.055em;text-transform:uppercase}
.hero p{margin:1.25rem 0 0;max-width:34ch;font:600 clamp(1.1rem,2.3vw,1.45rem)/1.3 var(--display)}
.pagehead{padding-block:clamp(1.5rem,4vw,2.75rem)}
.pagehead h1{margin:0;font:900 clamp(2.25rem,7vw,4.5rem)/.95 var(--display);letter-spacing:-.045em;text-wrap:balance}
.pagehead p{margin:.9rem 0 0;max-width:52ch;font:500 1.1rem/1.4 var(--display)}
main{padding-block:clamp(1.75rem,4vw,3rem) 4rem}
h2{font:900 clamp(1.6rem,3.6vw,2.35rem)/1.05 var(--display);letter-spacing:-.035em;margin:0 0 1.25rem;text-wrap:balance}
.note{font:500 1rem/1.45 var(--display);color:var(--muted);max-width:60ch;margin:-.5rem 0 1.5rem}
.block+.block{margin-top:clamp(2.5rem,6vw,4.5rem)}
/* дела: стороны крупно, ниже карточка дела */
.cases{display:grid;gap:0;border-top:3px solid var(--ink)}
.case{padding-block:1.5rem;border-bottom:1px solid var(--rule);display:grid;gap:.9rem;min-width:0}
.case h3{margin:0;font:900 clamp(1.5rem,4.2vw,2.6rem)/1.02 var(--display);letter-spacing:-.04em;text-wrap:balance}
.case h3 a{text-decoration:none}
.case h3 a:hover{text-decoration:underline;text-decoration-thickness:.08em}
.vs{font-weight:500;letter-spacing:-.02em;color:var(--muted)}
.docket{display:grid;grid-template-columns:repeat(auto-fit,minmax(11rem,1fr));gap:.75rem 1.5rem;margin:0;font:500 .95rem/1.35 var(--display)}
.docket div{min-width:0}
.docket dt{color:var(--muted)}
.docket dd{margin:.1rem 0 0;font-weight:700}
.lead{margin:0;max-width:62ch}
/* лента */
.feed{list-style:none;margin:0;padding:0;border-top:3px solid var(--ink)}
.feed li{display:grid;grid-template-columns:8.5rem minmax(0,1fr);gap:.25rem 1.5rem;padding-block:1.15rem;border-bottom:1px solid var(--rule)}
.when{font:500 .9rem/1.5 var(--display);color:var(--muted);font-variant-numeric:tabular-nums}
.rub{display:inline-block;font:700 .8rem/1 var(--display);padding:.3rem .5rem;border-radius:.35rem;background:var(--ink);color:var(--paper);text-decoration:none}
.feed h3{margin:.45rem 0 .3rem;font:800 clamp(1.2rem,2.6vw,1.5rem)/1.15 var(--display);letter-spacing:-.025em;text-wrap:balance}
.feed h3 a{text-decoration:none}
.feed h3 a:hover{text-decoration:underline}
.feed p{margin:0;color:var(--muted);font-size:1rem;line-height:1.5;max-width:62ch}
@media (max-width:40rem){.feed li{grid-template-columns:1fr}}
/* материал */
article{max-width:42rem}
.meta{display:flex;flex-wrap:wrap;align-items:center;gap:.5rem 1rem;font:500 .95rem/1.4 var(--display);margin-bottom:1rem}
.slab .rub{background:var(--on-lime);color:var(--lime)}
article p{margin:0 0 1.15em}
article p:first-of-type{font-size:1.25rem;line-height:1.5}
article strong{font-weight:700}
figure{margin:0 0 1.75rem}
figure img{display:block;width:100%;height:auto;border-radius:.5rem}
.box{background:var(--mark);border-radius:.6rem;padding:1.25rem 1.4rem;margin:0 0 2rem}
.box h2{font-size:1.05rem;letter-spacing:-.01em;margin-bottom:.9rem}
.sources{margin-top:2.5rem;padding-top:1.25rem;border-top:3px solid var(--ink);font:500 .98rem/1.45 var(--display)}
.sources h2{font-size:1.05rem;letter-spacing:-.01em;margin-bottom:.6rem}
.sources ul{margin:0;padding-left:1.1rem}
.sources li+li{margin-top:.35rem}
.sign{margin-top:2.5rem;font:500 1rem/1.5 var(--display);max-width:42rem}
.sign strong{font-weight:800}
.prose{max-width:42rem}
.prose h2{margin-top:2.25rem}
.prose p{margin:0 0 1.1em}
.contact{font:800 1.35rem/1.2 var(--display);user-select:all}
footer{border-top:1px solid var(--rule);padding-block:2rem 3rem;font:500 .9rem/1.5 var(--display);color:var(--muted)}
footer .wrap{display:flex;flex-wrap:wrap;gap:.75rem 2.5rem;justify-content:space-between}
footer p{margin:0;max-width:52ch}
.fl{display:flex;flex-wrap:wrap;gap:.4rem 1.5rem}
"""

FONTS = '<link rel="preconnect" href="https://fonts.googleapis.com"><link rel="preconnect" href="https://fonts.gstatic.com" crossorigin><link rel="stylesheet" href="https://fonts.googleapis.com/css2?family=Inter:wght@500;600;700;800;900&family=PT+Serif:ital,wght@0,400;0,700;1,400&display=swap">'


def page(path, title, desc, slab, main, up="", current="", extra_head="", og_image="img/og.png", og_type="website"):
    """Возвращает (head, body). up — префикс до корня ('' или '../')."""
    url = f"{SITE_URL}/{path}" if path != "index.html" else f"{SITE_URL}/"
    nav = "".join(
        f'<a href="{up}{f}"{" aria-current=\"page\"" if current == k else ""}>{n}</a>' for k, (n, f, _) in RUBRICS.items()
    ) + f'<a href="{up}o-proekte.html"{" aria-current=\"page\"" if current == "about" else ""}>О проекте</a>'
    head = f"""<title>{esc(title)}</title>
<meta name="description" content="{esc(desc)}">
<link rel="canonical" href="{url}">
<meta property="og:site_name" content="{SITE_NAME}"><meta property="og:type" content="{og_type}">
<meta property="og:title" content="{esc(title)}"><meta property="og:description" content="{esc(desc)}">
<meta property="og:url" content="{url}"><meta property="og:image" content="{SITE_URL}/{og_image}">
<meta name="twitter:card" content="summary_large_image">
<link rel="icon" href="{up}favicon.svg" type="image/svg+xml">
<link rel="alternate" type="application/rss+xml" title="{SITE_NAME}" href="{SITE_URL}/rss.xml">
{FONTS}
<style>{CSS}</style>{extra_head}"""
    body = f"""<header class="slab"><div class="wrap">
<div class="top"><a class="logo" href="{up}index.html">{SITE_NAME}</a><nav aria-label="Рубрики">{nav}</nav></div>
{slab}
</div></header>
<main><div class="wrap">
{main}
</div></main>
<footer><div class="wrap">
<p>© {dt.date.today().year} «{SITE_NAME}». Материалы подготовлены по открытым источникам, ссылки на них даны в каждом тексте. Оценки отражают мнение автора.</p>
<p class="fl"><a href="{CHANNEL}" rel="noopener">Телеграм-канал</a><a href="{up}rss.xml">RSS</a><a href="{up}o-proekte.html">Связаться</a></p>
</div></footer>"""
    return head, body


def write(path, head, body):
    f = OUT / path
    f.parent.mkdir(parents=True, exist_ok=True)
    f.write_text(f'<!doctype html>\n<html lang="ru">\n<head>\n<meta charset="utf-8">\n<meta name="viewport" content="width=device-width,initial-scale=1">\n{head}\n</head>\n<body>\n{body}\n</body>\n</html>\n', encoding="utf-8")


def rub_link(p, up=""):
    n, f, _ = RUBRICS[p["rubric"]]
    return f'<a class="rub" href="{up}{f}">{n}</a>'


def docket(p):
    rows = [("Суд", p.get("sud")), ("Номер дела", p.get("delo")), ("Цена вопроса", p.get("cena")), ("Стадия", p.get("stadiya"))]
    return '<dl class="docket">' + "".join(f"<div><dt>{k}</dt><dd>{esc(v)}</dd></div>" for k, v in rows if v) + "</dl>"


def case_card(p, up=""):
    return f"""<div class="case">
<h3><a href="{up}materialy/{p['slug']}.html">{esc(p['a'])} <span class="vs">против</span> {esc(p.get('b_rod', p['b']))}</a></h3>
{docket(p)}
<p class="lead">{esc(p['description'])}</p>
</div>"""


def feed_item(p, up=""):
    return f"""<li><div class="when"><time datetime="{p['date'].isoformat()}">{ru_date(p['date'])}</time></div>
<div>{rub_link(p, up)}<h3><a href="{up}materialy/{p['slug']}.html">{esc(p['title'])}</a></h3><p>{esc(p['description'])}</p></div></li>"""


def build():
    posts = load()
    if OUT.exists():
        shutil.rmtree(OUT)
    shutil.copytree(STATIC, OUT)
    cases = [p for p in posts if p["rubric"] == "konflikty"]

    # главная
    slab = f'<div class="hero"><h1>{SITE_NAME}</h1><p>{TAGLINE}</p></div>'
    main = f"""<section class="block"><h2>Конфликты</h2>
<p class="note">Кто с кем спорит, что сказала каждая сторона и что решил суд. Страницы обновляются, когда в деле появляется новое решение.</p>
<div class="cases">{''.join(case_card(p) for p in cases[:4])}</div></section>
<section class="block"><h2>Все материалы</h2><ul class="feed">{''.join(feed_item(p) for p in posts)}</ul></section>"""
    ld = {"@context": "https://schema.org", "@type": "WebSite", "name": SITE_NAME, "url": SITE_URL + "/", "description": TAGLINE, "inLanguage": "ru"}
    head, body = page("index.html", f"{SITE_NAME}: политика, экономика и корпоративные конфликты", TAGLINE, slab, main,
                      extra_head=f'\n<script type="application/ld+json">{json.dumps(ld, ensure_ascii=False)}</script>')
    write("index.html", head, body)
    index_parts = (head, body)

    # рубрики
    for key, (name, fname, rdesc) in RUBRICS.items():
        items = [p for p in posts if p["rubric"] == key]
        slab = f'<div class="pagehead"><h1>{name}</h1><p>{rdesc}</p></div>'
        if key == "konflikty":
            main = f'<div class="cases">{"".join(case_card(p) for p in items)}</div>'
        else:
            main = f'<ul class="feed">{"".join(feed_item(p) for p in items)}</ul>' if items else '<p class="note">Материалы в этой рубрике появятся скоро.</p>'
        write(fname, *page(fname, f"{name} — {SITE_NAME}", rdesc, slab, main, current=key))

    # материалы
    for p in posts:
        path = f"materialy/{p['slug']}.html"
        upd = f'<span>обновлено <time datetime="{p["updated"].isoformat()}">{ru_date(p["updated"])}</time></span>' if p["updated"] != p["date"] else ""
        slab = f"""<div class="pagehead"><div class="meta">{rub_link(p, '../')}<time datetime="{p['date'].isoformat()}">{ru_date(p['date'])}</time>{upd}</div>
<h1>{esc(p['title'])}</h1></div>"""
        fig = f'<figure><img src="../img/{p["image"]}" alt="{esc(p.get("image_alt", p["title"]))}" width="1280" height="800" loading="lazy"></figure>' if p.get("image") else ""
        box = f'<div class="box"><h2>Карточка дела</h2>{docket(p)}</div>' if p["rubric"] == "konflikty" else ""
        src = "".join(f'<li><a href="{esc(u)}" rel="noopener">{esc(t)}</a></li>' for t, u in p["sources"])
        main = f"""<article>{box}{fig}
{p['body']}
<section class="sources"><h2>Источники</h2><ul>{src}</ul></section>
<p class="sign"><strong>{AUTHOR}</strong>, автор «{SITE_NAME}». Канал в телеграме: <a href="{CHANNEL}" rel="noopener">t.me/economskepticism</a>. По вопросам коммуникаций в корпоративных спорах: <a href="../o-proekte.html">как связаться</a>.</p>
</article>"""
        ld = {"@context": "https://schema.org", "@type": "NewsArticle", "headline": p["title"], "description": p["description"],
              "datePublished": p["date"].isoformat() + "+03:00", "dateModified": p["updated"].isoformat() + "+03:00", "inLanguage": "ru",
              "author": {"@type": "Person", "name": AUTHOR}, "publisher": {"@type": "Organization", "name": SITE_NAME, "url": SITE_URL + "/"},
              "mainEntityOfPage": f"{SITE_URL}/{path}", "image": f"{SITE_URL}/img/{p.get('image', 'og.png')}"}
        write(path, *page(path, f"{p['seo_title']} — {SITE_NAME}", p["description"], slab, main, up="../", current=p["rubric"],
                          og_image=f"img/{p.get('image', 'og.png')}", og_type="article",
                          extra_head=f'\n<script type="application/ld+json">{json.dumps(ld, ensure_ascii=False)}</script>'))

    # о проекте
    slab = '<div class="pagehead"><h1>О проекте</h1><p>Кто это пишет, по каким правилам и как связаться.</p></div>'
    main = f"""<div class="prose">
<p>«{SITE_NAME}» — авторское издание о политике и экономике. Мы пишем о том, что произошло, сколько это стоит и кому выгодно. Автор — журналист {AUTHOR}, 15 лет в медиа. У проекта есть <a href="{CHANNEL}" rel="noopener">телеграм-канал</a>, он зарегистрирован в реестре Роскомнадзора.</p>
<h2>Как мы пишем о конфликтах</h2>
<p>В рубрике «Конфликты» разбираются публичные корпоративные споры: иски, арбитражи, столкновения компаний с регуляторами и друг с другом. У каждого разбора одни и те же правила.</p>
<p>Позиции обеих сторон излагаются одинаково подробно и по их собственным заявлениям. Решения судов приводятся с инстанцией и статусом: вступило ли решение в силу и обжалуется ли оно. Пока спор не завершён, мы никого не называем виновным. Мы оцениваем то, как стороны ведут себя публично, а не то, кто прав по существу.</p>
<p>Страницы разборов обновляются, когда в деле появляется новое решение или заявление. Если вы участник спора и считаете, что ваша позиция изложена неточно, напишите: мы поправим текст и укажем дату изменения.</p>
<h2>Консультации</h2>
<p>Автор консультирует компании и собственников по коммуникациям в корпоративных спорах и по защите репутации: как объяснять свою позицию во время разбирательства, что говорить и чего не говорить публично, как отвечать на информационные кампании.</p>
<h2>Связаться</h2>
<p>Реклама в канале и вопросы по консультациям, телеграм:</p>
<p class="contact">{CONTACT}</p>
</div>"""
    write("o-proekte.html", *page("o-proekte.html", f"О проекте — {SITE_NAME}", "Кто пишет «Курс дела», правила рубрики о корпоративных конфликтах и контакты.", slab, main, current="about"))

    # 404
    write("404.html", *page("404.html", f"Страница не найдена — {SITE_NAME}", "Такой страницы нет.", '<div class="pagehead"><h1>Такой страницы нет</h1><p>Возможно, адрес изменился.</p></div>',
                            '<p class="note"><a href="index.html">Перейти на главную</a></p>'))

    # служебные файлы
    urls = ["", *[f for _, f, _ in RUBRICS.values()], "o-proekte.html", *[f"materialy/{p['slug']}.html" for p in posts]]
    last = {f"materialy/{p['slug']}.html": p["updated"].date().isoformat() for p in posts}
    today = max(p["updated"] for p in posts).date().isoformat()
    (OUT / "sitemap.xml").write_text('<?xml version="1.0" encoding="UTF-8"?>\n<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">\n' +
        "".join(f"<url><loc>{SITE_URL}/{u}</loc><lastmod>{last.get(u, today)}</lastmod></url>\n" for u in urls) + "</urlset>\n", encoding="utf-8")
    (OUT / "robots.txt").write_text(f"User-agent: *\nAllow: /\n\nSitemap: {SITE_URL}/sitemap.xml\n", encoding="utf-8")
    items = "".join(f"<item><title>{esc(p['title'])}</title><link>{SITE_URL}/materialy/{p['slug']}.html</link><guid>{SITE_URL}/materialy/{p['slug']}.html</guid>"
                    f"<pubDate>{p['date'].strftime('%a, %d %b %Y %H:%M:%S')} +0300</pubDate><description>{esc(p['description'])}</description></item>\n" for p in posts[:30])
    (OUT / "rss.xml").write_text(f'<?xml version="1.0" encoding="UTF-8"?>\n<rss version="2.0"><channel><title>{SITE_NAME}</title><link>{SITE_URL}/</link>'
                                 f"<description>{esc(TAGLINE)}</description><language>ru</language>\n{items}</channel></rss>\n", encoding="utf-8")
    llms = [f"# {SITE_NAME}", "", f"> {TAGLINE} Авторское издание, автор — {AUTHOR}. Отдельная рубрика посвящена публичным корпоративным конфликтам: стороны, позиции, решения судов.", "",
            "## Конфликты", *[f"- [{p['a']} против {p.get('b_rod', p['b'])}]({SITE_URL}/materialy/{p['slug']}.html): {p['description']}" for p in cases], "",
            "## Материалы", *[f"- [{p['title']}]({SITE_URL}/materialy/{p['slug']}.html): {p['description']}" for p in posts if p['rubric'] != 'konflikty'], "",
            "## О проекте", f"- [Правила и контакты]({SITE_URL}/o-proekte.html)", ""]
    (OUT / "llms.txt").write_text("\n".join(llms), encoding="utf-8")
    (OUT / ".nojekyll").write_text("", encoding="utf-8")
    (OUT / "favicon.svg").write_text('<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 64 64"><rect width="64" height="64" rx="12" fill="#CCFF33"/><text x="32" y="43" text-anchor="middle" font-family="Inter,Arial,sans-serif" font-weight="900" font-size="30" letter-spacing="-1.5" fill="#121110">КД</text></svg>', encoding="utf-8")

    # главная без обёртки документа: для предпросмотра
    pv = re.sub(r"<title>.*?</title>", f"<title>{SITE_NAME}</title>", index_parts[0], count=1)
    (ROOT / "preview_index.html").write_text(pv + "\n" + index_parts[1] + "\n", encoding="utf-8")
    print(f"Собрано: {len(posts)} материалов, {len(list(OUT.rglob('*.html')))} страниц → {OUT}")


if __name__ == "__main__":
    build()
