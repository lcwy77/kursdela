#!/usr/bin/env python3
"""Сборка сайта «Курс дела».

Запуск:  python3 build.py
Материалы лежат в content/*.md, готовый сайт собирается в docs/ (эту папку раздаёт GitHub Pages).
Перед выкладкой поменяй SITE_URL и CONTACT ниже.
"""
import html, json, re, shutil, datetime as dt
from pathlib import Path

# ---------- настройки ----------
SITE_URL = "https://kursmedia.com"   # свой домен, без косой черты в конце
SITE_NAME = "Курс дела Медиа"
BRAND = "Курс дела"                   # короткое имя для логотипа и шапки
MOTTO = "Конфликты, деньги, власть"
TAGLINE = "Конфликты, деньги, власть: что произошло, сколько это стоит и кому выгодно."
AUTHOR = "Редакция «Курс дела Медиа»"
CHANNEL = "https://t.me/economskepticism"
EMAIL = "press@kursmedia.com"           # почта редакции
CONTACT = "@mishaasublime"                # контакт для рекламы и консультаций
# -------------------------------

ROOT = Path(__file__).parent
SRC, STATIC, OUT = ROOT / "content", ROOT / "static", ROOT / "docs"

RUBRICS = {  # ключ: (название, файл, описание для поиска)
    "konflikty": ("Конфликты", "konflikty.html", "Корпоративные споры: стороны, их позиции и решения судов."),
    "ekonomika": ("Экономика", "ekonomika.html", "Экономика, финансы и бизнес России: бюджет, банки, рынки, компании."),
    "politika": ("Политика", "politika.html", "Российская политика и международные контакты."),
    "mir": ("Мир", "mir.html", "Политики и события Запада, Европы и Китая."),
    "ukraina": ("Украина", "ukraina.html", "Что происходит на Украине и вокруг неё."),
}
# английская версия: content_en/*.md, поле `ru:` — слаг русского оригинала (для hreflang и переключателя языка)
SRC_EN = ROOT / "content_en"
EN_NAME = "Kurs Media"
EN_MOTTO = "Conflicts, money, power"
EN_TAGLINE = "Russian business conflicts, money and power: what happened, what it costs and who benefits."
RUBRICS_EN = {
    "konflikty": ("Conflicts", "conflicts.html", "Russian corporate disputes: the parties, their positions and court rulings."),
    "ekonomika": ("Economy", "economy.html", "Russia's economy, finance and business: budget, banks, markets, companies."),
    "politika": ("Politics", "politics.html", "Russian politics and foreign relations."),
    "mir": ("World", "world.html", "The West, Europe and China as seen from Moscow."),
    "ukraina": ("Ukraine", "ukraine.html", "Ukraine and the war."),
}
NOW_MSK = (dt.datetime.now(dt.timezone.utc) + dt.timedelta(hours=3)).replace(tzinfo=None)   # даты в материалах московские
MONTHS = "января февраля марта апреля мая июня июля августа сентября октября ноября декабря".split()
MONTHS_EN = "January February March April May June July August September October November December".split()


def esc(s):
    return html.escape(str(s), quote=True)


def ru_date(d, lang="ru"):
    return f"{d.day} {(MONTHS_EN if lang == 'en' else MONTHS)[d.month - 1]} {d.year}"


def inline(s):
    s = esc(s)
    s = re.sub(r"\[([^\]]+)\]\((https?://[^)\s]+)\)", r'<a href="\2" rel="noopener">\1</a>', s)
    return re.sub(r"\*\*(.+?)\*\*", r"<strong>\1</strong>", s)


def md(body):
    return "\n".join(f"<p>{inline(' '.join(b.split()))}</p>" for b in re.split(r"\n\s*\n", body.strip()) if b.strip())


def load(src=SRC):
    posts = []
    for f in sorted(src.glob("*.md")):
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
        if meta["date"] > NOW_MSK:   # отложенный материал: выйдет при первой сборке после этой даты (время московское)
            print(f"  отложено до {meta['date']:%d.%m %H:%M}: {f.stem}")
            continue
        meta["updated"] = dt.datetime.strptime(meta["updated"], "%Y-%m-%d %H:%M") if "updated" in meta else meta["date"]
        meta.update(slug=f.stem, sources=sources, body=md(body), plain=" ".join(body.split()))
        meta.setdefault("seo_title", meta["title"])
        posts.append(meta)
    return sorted(posts, key=lambda p: p["date"], reverse=True)


CSS = """
/* Курс дела: строгая деловая вёрстка. Бумага и графит, лайм только в знаке и в отметках статуса.
   Заголовки — Literata (серьёзная газетная антиква), интерфейс и стороны споров — Golos Text. */
:root{--paper:#FBFBF8;--ink:#171B24;--muted:#5C6370;--rule:#DCDFE3;--panel:#F0F2EC;--lime:#CCFF33;--on-lime:#171B24;
 --serif:"Literata",Georgia,"Times New Roman",serif;--sans:"Golos Text","Helvetica Neue",Arial,sans-serif;color-scheme:light}
@media (prefers-color-scheme:dark){:root:not([data-theme="light"]){--paper:#11141A;--ink:#E9ECF1;--muted:#9AA1AD;--rule:#2A2F39;--panel:#1A1F28;color-scheme:dark}}
:root[data-theme="dark"]{--paper:#11141A;--ink:#E9ECF1;--muted:#9AA1AD;--rule:#2A2F39;--panel:#1A1F28;color-scheme:dark}
*{box-sizing:border-box}
html{-webkit-text-size-adjust:100%}
body{margin:0;background:var(--paper);color:var(--ink);font:400 1.0625rem/1.65 var(--serif);border-top:5px solid var(--lime)}
a{color:inherit;text-decoration-color:var(--rule);text-decoration-thickness:1px;text-underline-offset:.2em}
a:hover{text-decoration-color:currentColor}
a:focus-visible{outline:2px solid var(--ink);outline-offset:3px;border-radius:2px}
.wrap{max-width:74rem;margin-inline:auto;padding-inline:clamp(1rem,4vw,2.5rem)}
/* шапка */
.mast{border-bottom:1px solid var(--ink)}
.strip{display:flex;justify-content:space-between;gap:1rem;padding-block:.55rem;border-bottom:1px solid var(--rule);font:500 .8rem/1.4 var(--sans);color:var(--muted)}
.strip a{text-decoration:none}.strip a:hover{color:var(--ink)}
.strip .r{display:flex;gap:1.1rem}
.brand{display:flex;flex-wrap:wrap;align-items:center;justify-content:space-between;gap:.75rem 2rem;padding-block:1.4rem 1.1rem}
.logo{display:inline-flex;align-items:center;gap:.8rem;text-decoration:none}
.mark{display:inline-grid;grid-template-columns:1fr 1fr;width:2.9rem;height:2.9rem;border-radius:.45rem;overflow:hidden;font:700 1.15rem/1 var(--sans);flex:none}
.mark span{display:grid;place-items:center}
.mark span:first-child{background:var(--ink);color:var(--paper)}
.mark span:last-child{background:var(--lime);color:var(--on-lime)}
.wm{display:flex;flex-direction:column;gap:.15rem}
.wm b{font:700 clamp(1.6rem,3.6vw,2.15rem)/1 var(--serif);letter-spacing:-.02em}
.wm small{font:500 .82rem/1 var(--sans);color:var(--muted);letter-spacing:.01em}
.motto{margin:0;font:500 .95rem/1.4 var(--sans);color:var(--muted);max-width:34ch;text-align:right}
nav{display:flex;flex-wrap:wrap;gap:.2rem 1.6rem;padding-block:.15rem .7rem;font:600 .95rem/1.4 var(--sans)}
nav a{text-decoration:none;padding-block:.35rem;border-bottom:3px solid transparent}
nav a:hover{border-bottom-color:var(--rule)}
nav a[aria-current="page"]{border-bottom-color:var(--lime)}
nav .lang{margin-left:auto;color:var(--muted)}
@media (max-width:40rem){.motto{text-align:left}nav .lang{margin-left:0}}
/* заголовки страниц */
.pagehead{padding-block:clamp(.5rem,2vw,1.25rem) clamp(1.5rem,3vw,2.25rem)}
.pagehead h1{margin:0;font:700 clamp(2rem,5vw,3.3rem)/1.08 var(--serif);letter-spacing:-.025em;max-width:24ch;text-wrap:balance}
.pagehead p{margin:.8rem 0 0;max-width:60ch;font:400 1.1rem/1.5 var(--sans);color:var(--muted)}
main{padding-block:clamp(1.5rem,3.5vw,2.5rem) 4rem}
.sh{margin:0 0 1rem;padding-bottom:.55rem;border-bottom:1px solid var(--ink);font:700 1.05rem/1.2 var(--sans)}
.block+.block{margin-top:clamp(2.5rem,5vw,3.5rem)}
.note{font:400 1rem/1.5 var(--sans);color:var(--muted);max-width:60ch}
.rub{display:inline-block;font:600 .78rem/1 var(--sans);padding:.32rem .5rem .34rem;border-radius:.3rem;background:var(--ink);color:var(--paper);text-decoration:none}
.rub.c{background:var(--lime);color:var(--on-lime)}
time,.when{font:500 .85rem/1.4 var(--sans);color:var(--muted);font-variant-numeric:tabular-nums}
/* первый экран главной: главный материал и колонка споров */
.front{display:grid;grid-template-columns:minmax(0,1.7fr) minmax(0,1fr);gap:clamp(1.5rem,4vw,3.5rem);padding-bottom:clamp(1.5rem,3vw,2rem)}
.lead .cm{display:flex;align-items:center;gap:.75rem;margin-bottom:.9rem}
.lead h2{margin:0;font:700 clamp(1.9rem,4.4vw,3.1rem)/1.08 var(--serif);letter-spacing:-.025em;text-wrap:balance}
.lead h2 a{text-decoration:none}.lead h2 a:hover{text-decoration:underline;text-decoration-thickness:2px}
.lead p{margin:1rem 0 0;font-size:1.15rem;line-height:1.6;color:var(--muted);max-width:58ch}
.side{border-left:1px solid var(--rule);padding-left:clamp(1rem,2.5vw,2rem)}
.mini{list-style:none;margin:0;padding:0}
.mini li{padding-block:.85rem;border-bottom:1px solid var(--rule)}
.mini li:first-child{padding-top:.2rem}
.mini a{display:block;text-decoration:none;font:700 1.12rem/1.25 var(--sans);letter-spacing:-.01em}
.mini a:hover .pt{text-decoration:underline}
.vs{font-weight:400;color:var(--muted)}
.mini .st{display:block;margin-top:.35rem;font:400 .88rem/1.45 var(--sans);color:var(--muted)}
.more{display:inline-block;margin-top:.9rem;font:600 .9rem/1.4 var(--sans)}
@media (max-width:52rem){.front{grid-template-columns:1fr}.side{border-left:0;padding-left:0}}
/* лента: колонки без карточек, только линейки */
.grid{list-style:none;margin:0;padding:0;display:grid;grid-template-columns:repeat(auto-fill,minmax(17rem,1fr));gap:0 clamp(1.25rem,3vw,2.25rem)}
.grid li{padding-block:1.1rem 1.5rem;border-bottom:1px solid var(--rule)}
.grid .cm{display:flex;align-items:center;gap:.6rem;margin-bottom:.6rem}
.grid h3{margin:0 0 .45rem;font:700 1.22rem/1.25 var(--serif);letter-spacing:-.01em;text-wrap:balance}
.grid h3 a{text-decoration:none}.grid h3 a:hover{text-decoration:underline}
.grid p{margin:0;font:400 .95rem/1.5 var(--sans);color:var(--muted);display:-webkit-box;-webkit-line-clamp:3;-webkit-box-orient:vertical;overflow:hidden}
/* споры: стороны крупно, карточка дела как выписка */
.cases{display:grid;gap:0;border-top:1px solid var(--ink)}
.case{padding-block:1.6rem;border-bottom:1px solid var(--rule);display:grid;gap:1rem;min-width:0}
.case h3{margin:0;font:700 clamp(1.45rem,3.6vw,2.2rem)/1.1 var(--sans);letter-spacing:-.025em;text-wrap:balance}
.case h3 a{text-decoration:none}.case h3 a:hover .pt{text-decoration:underline;text-decoration-thickness:2px}
.docket{display:grid;grid-template-columns:repeat(auto-fit,minmax(13rem,1fr));gap:.8rem 1.75rem;margin:0;font:400 .92rem/1.45 var(--sans)}
.docket div{min-width:0;padding-left:.75rem;border-left:2px solid var(--rule)}
.docket dt{color:var(--muted);font-size:.82rem}
.docket dd{margin:.15rem 0 0;font-weight:600}
.lead-c{margin:0;max-width:64ch;color:var(--muted)}
/* материал */
.meta{display:flex;flex-wrap:wrap;align-items:center;gap:.5rem 1rem;margin-bottom:1rem}
article{max-width:44rem}
article>p{margin:0 0 1.15em;font-size:1.125rem;line-height:1.72}
article>p:first-of-type{font-size:1.28rem;line-height:1.6}
article strong{font-family:var(--sans);font-weight:700;font-size:.95em}
figure{margin:0 0 1.75rem}
figure img{display:block;width:100%;height:auto;border-radius:.4rem}
.box{background:var(--panel);border-radius:.5rem;padding:1.25rem 1.4rem;margin:0 0 2rem;border-top:4px solid var(--lime)}
.box h2{font:700 1rem/1.2 var(--sans);margin:0 0 .9rem}
.box .docket div{border-left-color:var(--rule)}
.sources{margin-top:2.5rem;padding-top:1rem;border-top:1px solid var(--ink);font:400 .95rem/1.5 var(--sans)}
.sources h2{font:700 1rem/1.2 var(--sans);margin:0 0 .6rem}
.sources ul{margin:0;padding-left:1.1rem}
.sources li+li{margin-top:.35rem}
.sign{margin-top:2rem;font:400 .98rem/1.55 var(--sans);color:var(--muted);max-width:44rem}
.sign strong{color:var(--ink)}
.prose{max-width:44rem}
.prose h2{margin:2.2rem 0 .8rem;font:700 1.45rem/1.2 var(--serif)}
.prose p{margin:0 0 1.1em;font-size:1.1rem}
.contact{font:700 1.3rem/1.2 var(--sans)}
footer{border-top:1px solid var(--ink);padding-block:1.75rem 3rem;font:400 .88rem/1.55 var(--sans);color:var(--muted)}
footer .wrap{display:flex;flex-wrap:wrap;gap:1rem 3rem;justify-content:space-between;align-items:flex-start}
footer .logo{gap:.6rem}footer .mark{width:2.1rem;height:2.1rem;font-size:.85rem}
footer p{margin:.6rem 0 0;max-width:52ch}
.fl{display:flex;flex-wrap:wrap;gap:.4rem 1.5rem;margin:0!important}
@media (prefers-reduced-motion:reduce){*{scroll-behavior:auto!important}}
"""

FONTS = '<link rel="preconnect" href="https://fonts.googleapis.com"><link rel="preconnect" href="https://fonts.gstatic.com" crossorigin><link rel="stylesheet" href="https://fonts.googleapis.com/css2?family=Golos+Text:wght@400;500;600;700&family=Literata:ital,opsz,wght@0,7..72,400;0,7..72,700;1,7..72,400&display=swap">'


def url_of(path):
    return f"{SITE_URL}/" + (path[:-len("index.html")] if path.endswith("index.html") else path)


def page(path, title, desc, slab, main, up="", current="", extra_head="", og_image="img/og.png", og_type="website",
         lang="ru", alts=None, switch=None):
    """Возвращает (head, body). up — префикс до корня сайта ('', '../', '../../').
    alts — список (hreflang, url) для парных страниц; switch — ссылка переключателя языка."""
    url = url_of(path)
    cur = lambda k: ' aria-current="page"' if current == k else ""
    if lang == "en":
        base = f"{up}en/"
        nav = "".join(f'<a href="{base}{f}"{cur(k)}>{n}</a>' for k, (n, f, _) in RUBRICS_EN.items()) + f'<a href="{base}about.html"{cur("about")}>About</a>'
        nav += f'<a class="lang" href="{switch or up + "index.html"}" lang="ru" hreflang="ru">Русский</a>'
        name, home = EN_NAME, f"{base}index.html"
        wm, motto, sub = "Kurs Media", "Russian business conflicts, money and power", "Kurs Media"
        foot = f"© {dt.date.today().year} {EN_NAME}. Based on public sources, linked in every article. Opinions are those of the editors."
        fl = f'<a href="{base}rss.xml">RSS</a><a href="{base}about.html">Contact</a><a href="{up}index.html" lang="ru">Русская версия</a>'
        rss, locale, navlabel = f"{SITE_URL}/en/rss.xml", "en_US", "Sections"
    else:
        nav = "".join(f'<a href="{up}{f}"{cur(k)}>{n}</a>' for k, (n, f, _) in RUBRICS.items()) + f'<a href="{up}o-proekte.html"{cur("about")}>О проекте</a>'
        nav += f'<a class="lang" href="{switch or up + "en/index.html"}" lang="en" hreflang="en">English</a>'
        name, home = SITE_NAME, f"{up}index.html"
        wm, motto, sub = BRAND, "Конфликты, деньги, власть: что произошло, сколько это стоит и кому выгодно", "медиа"
        foot = f"© {dt.date.today().year} «{SITE_NAME}». Материалы подготовлены по открытым источникам, ссылки на них даны в каждом тексте. Оценки отражают мнение редакции."
        fl = f'<a href="{CHANNEL}" rel="noopener">Телеграм-канал</a><a href="{up}rss.xml">RSS</a><a href="{up}o-proekte.html">Связаться</a><a href="{up}en/index.html" lang="en">English</a>'
        rss, locale, navlabel = f"{SITE_URL}/rss.xml", "ru_RU", "Рубрики"
    hl = "".join(f'\n<link rel="alternate" hreflang="{h}" href="{u}">' for h, u in (alts or []))
    head = f"""<title>{esc(title)}</title>
<meta name="description" content="{esc(desc)}">
<link rel="canonical" href="{url}">{hl}
<meta property="og:site_name" content="{name}"><meta property="og:type" content="{og_type}"><meta property="og:locale" content="{locale}">
<meta property="og:title" content="{esc(title)}"><meta property="og:description" content="{esc(desc)}">
<meta property="og:url" content="{url}"><meta property="og:image" content="{SITE_URL}/{og_image}">
<meta name="twitter:card" content="summary_large_image">
<link rel="icon" href="{up}favicon.ico" sizes="48x48">
<link rel="icon" href="{up}favicon-96.png" type="image/png" sizes="96x96">
<link rel="icon" href="{up}favicon-192.png" type="image/png" sizes="192x192">
<link rel="icon" href="{up}favicon.svg" type="image/svg+xml">
<link rel="apple-touch-icon" href="{up}apple-touch-icon.png">
<link rel="alternate" type="application/rss+xml" title="{name}" href="{rss}">
{FONTS}
<style>{CSS}</style>{extra_head}"""
    mark = '<span class="mark" aria-hidden="true"><span>К</span><span>Д</span></span>'
    today = ru_date(NOW_MSK, lang)
    upd = "Updated" if lang == "en" else "Обновлено"
    body = f"""<header class="mast"><div class="wrap">
<div class="strip"><span>{upd} {today}</span><span class="r"><a href="{CHANNEL}" rel="noopener">Telegram</a><a href="{home.rsplit('index.html',1)[0]}{'rss.xml'}">RSS</a></span></div>
<div class="brand"><a class="logo" href="{home}">{mark}<span class="wm"><b>{wm}</b><small>{sub}</small></span></a><p class="motto">{motto}</p></div>
<nav aria-label="{navlabel}">{nav}</nav>
</div></header>
<main><div class="wrap">
{slab}
{main}
</div></main>
<footer><div class="wrap">
<div><a class="logo" href="{home}">{mark}<span class="wm"><b style="font-size:1.25rem">{wm}</b></span></a><p>{foot}</p></div>
<p class="fl">{fl}</p>
</div></footer>"""
    return head, body


def write(path, head, body, lang="ru"):
    f = OUT / path
    f.parent.mkdir(parents=True, exist_ok=True)
    f.write_text(f'<!doctype html>\n<html lang="{lang}">\n<head>\n<meta charset="utf-8">\n<meta name="viewport" content="width=device-width,initial-scale=1">\n{head}\n</head>\n<body>\n{body}\n</body>\n</html>\n', encoding="utf-8")


# up в хелперах ниже — префикс до раздела языка: для русских страниц до корня, для английских до /en/
def art_path(p, lang="ru"):
    return f"articles/{p['slug']}.html" if lang == "en" else f"materialy/{p['slug']}.html"


def rub_link(p, up="", lang="ru"):
    n, f, _ = (RUBRICS_EN if lang == "en" else RUBRICS)[p["rubric"]]
    c = " c" if p["rubric"] == "konflikty" else ""
    return f'<a class="rub{c}" href="{up}{f}">{n}</a>'


def docket(p, lang="ru"):
    labels = ("Court", "Case No.", "At stake", "Status") if lang == "en" else ("Суд", "Номер дела", "Цена вопроса", "Стадия")
    rows = zip(labels, (p.get("sud"), p.get("delo"), p.get("cena"), p.get("stadiya")))
    return '<dl class="docket">' + "".join(f"<div><dt>{k}</dt><dd>{esc(v)}</dd></div>" for k, v in rows if v) + "</dl>"


def parties(p, lang="ru"):
    vs, b = ("v.", p["b"]) if lang == "en" else ("против", p.get("b_rod", p["b"]))
    return f'<span class="pt">{esc(p["a"])}</span> <span class="vs">{vs}</span> <span class="pt">{esc(b)}</span>'


def short(t, n=120):
    t = re.split(r"(?<=[.;])\s", t or "", maxsplit=1)[0].rstrip(";.")
    return t if len(t) <= n else t[:n].rsplit(" ", 1)[0] + "…"


def case_card(p, up="", lang="ru"):
    return f"""<div class="case">
<h3><a href="{up}{art_path(p, lang)}">{parties(p, lang)}</a></h3>
{docket(p, lang)}
<p class="lead-c">{esc(p['description'])}</p>
</div>"""


def feed_item(p, up="", lang="ru"):
    return f"""<li><div class="cm">{rub_link(p, up, lang)}<time datetime="{p['date'].isoformat()}">{ru_date(p['date'], lang)}</time></div>
<h3><a href="{up}{art_path(p, lang)}">{esc(p['title'])}</a></h3><p>{esc(p['description'])}</p></li>"""


def front(posts, cases, lang="ru"):
    """Первый экран главной: свежий материал крупно и колонка споров."""
    L = posts[0]
    h_c, more = ("Conflicts", ("All case files", "conflicts.html")) if lang == "en" else ("Конфликты", ("Все разборы", "konflikty.html"))
    h_l = "Latest" if lang == "en" else "Последние материалы"
    mini = "".join(f'<li><a href="{art_path(c, lang)}">{parties(c, lang)}</a><span class="st">{esc(short(c.get("stadiya", "")))}</span></li>' for c in cases[:5])
    side = f'<aside class="side"><h2 class="sh">{h_c}</h2><ul class="mini">{mini}</ul><a class="more" href="{more[1]}">{more[0]}</a></aside>' if cases else ""
    return f"""<section class="front">
<article class="lead"><div class="cm">{rub_link(L, '', lang)}<time datetime="{L['date'].isoformat()}">{ru_date(L['date'], lang)}</time></div>
<h2><a href="{art_path(L, lang)}">{esc(L['title'])}</a></h2><p>{esc(L['description'])}</p></article>
{side}
</section>
<section class="block"><h2 class="sh">{h_l}</h2><ul class="grid">{''.join(feed_item(p, '', lang) for p in posts[1:])}</ul></section>"""


def build():
    posts = load()
    posts_en = load(SRC_EN) if SRC_EN.exists() else []
    en_of = {p["ru"]: p for p in posts_en if p.get("ru")}   # русский слаг → английский материал
    if OUT.exists():
        shutil.rmtree(OUT)
    shutil.copytree(STATIC, OUT)
    cases = [p for p in posts if p["rubric"] == "konflikty"]
    pair = lambda ru, en: [("ru", url_of(ru)), ("en", url_of(en)), ("x-default", url_of(ru))]

    # главная
    slab = ''
    main = front(posts, cases)
    ld = {"@context": "https://schema.org", "@type": "WebSite", "name": SITE_NAME, "url": SITE_URL + "/", "description": TAGLINE, "inLanguage": "ru"}
    head, body = page("index.html", f"{SITE_NAME} — {MOTTO.lower()}: корпоративные споры, экономика и политика", TAGLINE, slab, main,
                      alts=pair("index.html", "en/index.html"),
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
            main = f'<ul class="grid">{"".join(feed_item(p) for p in items)}</ul>' if items else '<p class="note">Материалы в этой рубрике появятся скоро.</p>'
        en_f = "en/" + RUBRICS_EN[key][1]
        write(fname, *page(fname, f"{name} — {SITE_NAME}", rdesc, slab, main, current=key, alts=pair(fname, en_f), switch=en_f))

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
<p class="sign"><strong>Редакция «{SITE_NAME}»</strong>. Канал в телеграме: <a href="{CHANNEL}" rel="noopener">t.me/economskepticism</a>. По вопросам коммуникаций в корпоративных спорах: <a href="../o-proekte.html">как связаться</a>.</p>
</article>"""
        ld = {"@context": "https://schema.org", "@type": "NewsArticle", "headline": p["title"], "description": p["description"],
              "datePublished": p["date"].isoformat() + "+03:00", "dateModified": p["updated"].isoformat() + "+03:00", "inLanguage": "ru",
              "author": {"@type": "Organization", "name": SITE_NAME, "url": SITE_URL + "/"}, "publisher": {"@type": "Organization", "name": SITE_NAME, "url": SITE_URL + "/"},
              "mainEntityOfPage": f"{SITE_URL}/{path}", "image": f"{SITE_URL}/img/{p.get('image', 'og.png')}"}
        en = en_of.get(p["slug"])
        en_path = f"en/{art_path(en, 'en')}" if en else None
        write(path, *page(path, f"{p['seo_title']} — {SITE_NAME}", p["description"], slab, main, up="../", current=p["rubric"],
                          og_image=f"img/{p.get('image', 'og.png')}", og_type="article",
                          alts=pair(path, en_path) if en else None, switch=f"../{en_path}" if en else None,
                          extra_head=f'\n<script type="application/ld+json">{json.dumps(ld, ensure_ascii=False)}</script>'))

    # о проекте
    slab = '<div class="pagehead"><h1>О проекте</h1><p>Редакция, правила и контакты.</p></div>'
    main = f"""<div class="prose">
<p>«{SITE_NAME}» — издание о политике, экономике и корпоративных спорах. У издания есть <a href="{CHANNEL}" rel="noopener">телеграм-канал</a>, он внесён в реестр Роскомнадзора.</p>
<h2>Как мы пишем о конфликтах</h2>
<p>В рубрике «Конфликты» разбираются публичные корпоративные споры: иски, арбитражи, разбирательства компаний с регуляторами и друг с другом. Правила для всех разборов одни.</p>
<p>Позиции сторон излагаются одинаково подробно и по их собственным заявлениям. Решения судов приводятся с номером дела, инстанцией и статусом: вступило ли решение в силу, обжалуется ли оно. О том, кто прав по существу, мы не судим: это дело суда. Мы описываем публичные действия сторон: иски, заявления, раскрытия.</p>
<p>Разборы обновляются, когда в деле появляется новое решение или заявление. Если ваша компания участвует в споре и её позиция изложена неточно, напишите на {EMAIL}. Мы сверим текст с документами, исправим и укажем дату правки.</p>
<p>Разборы не публикуются, не правятся и не снимаются за плату.</p>
<h2>Консультации</h2>
<p>Редакция консультирует компании и акционеров по публичной коммуникации в корпоративных спорах и по защите репутации: позиция на время разбирательства, работа с прессой, ответ на информационные кампании.</p>
<h2>Связаться</h2>
<p>Редакция, запросы и позиции сторон, исправления:</p>
<p class="contact"><a href="mailto:{EMAIL}">{EMAIL}</a></p>
<p>Консультации и реклама в канале, телеграм:</p>
<p class="contact">{CONTACT}</p>
</div>"""
    write("o-proekte.html", *page("o-proekte.html", f"О проекте — {SITE_NAME}", "Кто пишет «Курс дела Медиа», правила рубрики о корпоративных конфликтах и контакты.", slab, main, current="about",
                                  alts=pair("o-proekte.html", "en/about.html"), switch="en/about.html"))

    en_urls = build_en(posts_en, {p["slug"]: p for p in posts}, pair)

    # 404
    write("404.html", *page("404.html", f"Страница не найдена — {SITE_NAME}", "Такой страницы нет.", '<div class="pagehead"><h1>Такой страницы нет</h1><p>Возможно, адрес изменился.</p></div>',
                            '<p class="note"><a href="index.html">Перейти на главную</a></p>'))

    # служебные файлы
    urls = ["", *[f for _, f, _ in RUBRICS.values()], "o-proekte.html", *[f"materialy/{p['slug']}.html" for p in posts], *en_urls]
    last = {f"materialy/{p['slug']}.html": p["updated"].date().isoformat() for p in posts}
    last.update({f"en/articles/{p['slug']}.html": p["updated"].date().isoformat() for p in posts_en})
    today = max(p["updated"] for p in posts).date().isoformat()
    (OUT / "sitemap.xml").write_text('<?xml version="1.0" encoding="UTF-8"?>\n<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">\n' +
        "".join(f"<url><loc>{SITE_URL}/{u}</loc><lastmod>{last.get(u, today)}</lastmod></url>\n" for u in urls) + "</urlset>\n", encoding="utf-8")
    (OUT / "robots.txt").write_text(f"User-agent: *\nAllow: /\n\nSitemap: {SITE_URL}/sitemap.xml\n", encoding="utf-8")
    items = "".join(f"<item><title>{esc(p['title'])}</title><link>{SITE_URL}/materialy/{p['slug']}.html</link><guid>{SITE_URL}/materialy/{p['slug']}.html</guid>"
                    f"<pubDate>{p['date'].strftime('%a, %d %b %Y %H:%M:%S')} +0300</pubDate><description>{esc(p['description'])}</description></item>\n" for p in posts[:30])
    (OUT / "rss.xml").write_text(f'<?xml version="1.0" encoding="UTF-8"?>\n<rss version="2.0"><channel><title>{SITE_NAME}</title><link>{SITE_URL}/</link>'
                                 f"<description>{esc(TAGLINE)}</description><language>ru</language>\n{items}</channel></rss>\n", encoding="utf-8")
    llms = [f"# {SITE_NAME}", "", f"> {TAGLINE} Отдельная рубрика посвящена публичным корпоративным конфликтам: стороны, позиции, решения судов.", "",
            "## Конфликты", *[f"- [{p['a']} против {p.get('b_rod', p['b'])}]({SITE_URL}/materialy/{p['slug']}.html): {p['description']}" for p in cases], "",
            "## Материалы", *[f"- [{p['title']}]({SITE_URL}/materialy/{p['slug']}.html): {p['description']}" for p in posts if p['rubric'] != 'konflikty'], "",
            "## О проекте", f"- [Правила и контакты]({SITE_URL}/o-proekte.html)", ""]
    (OUT / "llms.txt").write_text("\n".join(llms), encoding="utf-8")
    (OUT / ".nojekyll").write_text("", encoding="utf-8")
    (OUT / "CNAME").write_text(SITE_URL.split("//", 1)[1] + "\n", encoding="utf-8")   # домен для GitHub Pages
    (OUT / "favicon.svg").write_text('<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 64 64"><clipPath id="r"><rect width="64" height="64" rx="10"/></clipPath><g clip-path="url(#r)"><rect width="32" height="64" fill="#171B24"/><rect x="32" width="32" height="64" fill="#CCFF33"/></g><g font-family="Arial,sans-serif" font-weight="700" font-size="30" text-anchor="middle"><text x="16" y="42" fill="#FBFBF8">К</text><text x="48" y="42" fill="#171B24">Д</text></g></svg>', encoding="utf-8")

    # главная без обёртки документа: для предпросмотра
    pv = re.sub(r"<title>.*?</title>", f"<title>{SITE_NAME}</title>", index_parts[0], count=1)
    (ROOT / "preview_index.html").write_text(pv + "\n" + index_parts[1] + "\n", encoding="utf-8")
    print(f"Собрано: {len(posts)} материалов, {len(posts_en)} на английском, {len(list(OUT.rglob('*.html')))} страниц → {OUT}")


def build_en(posts, ru_by_slug, pair):
    """Английский раздел /en/. Возвращает список путей для sitemap."""
    urls = []
    cases = [p for p in posts if p["rubric"] == "konflikty"]

    def put(path, title, desc, slab, main, up, alts=None, switch=None, **kw):
        write(path, *page(path, title, desc, slab, main, up=up, lang="en", alts=alts, switch=switch, **kw), lang="en")
        urls.append(path[:-len("index.html")] if path.endswith("index.html") else path)

    # главная
    slab = ''
    blocks = [front(posts, cases, 'en') if posts else '<p class="note">English coverage starts soon.</p>']
    ld = {"@context": "https://schema.org", "@type": "WebSite", "name": EN_NAME, "url": SITE_URL + "/en/", "description": EN_TAGLINE, "inLanguage": "en"}
    put("en/index.html", f"{EN_NAME} — Russian business conflicts, money and power", EN_TAGLINE, slab, "\n".join(blocks), "../",
        alts=pair("index.html", "en/index.html"), switch="../index.html",
        extra_head=f'\n<script type="application/ld+json">{json.dumps(ld)}</script>')

    # рубрики
    for key, (name, fname, rdesc) in RUBRICS_EN.items():
        items = [p for p in posts if p["rubric"] == key]
        slab = f'<div class="pagehead"><h1>{name}</h1><p>{rdesc}</p></div>'
        if not items:
            main = '<p class="note">English coverage in this section is coming soon.</p>'
        elif key == "konflikty":
            main = f'<div class="cases">{"".join(case_card(p, "", "en") for p in items)}</div>'
        else:
            main = f'<ul class="grid">{"".join(feed_item(p, "", "en") for p in items)}</ul>'
        ru_f = RUBRICS[key][1]
        put(f"en/{fname}", f"{name} — {EN_NAME}", rdesc, slab, main, "../", current=key, alts=pair(ru_f, f"en/{fname}"), switch=f"../{ru_f}")

    # материалы
    for p in posts:
        path = f"en/{art_path(p, 'en')}"
        upd = f'<span>updated <time datetime="{p["updated"].isoformat()}">{ru_date(p["updated"], "en")}</time></span>' if p["updated"] != p["date"] else ""
        slab = f"""<div class="pagehead"><div class="meta">{rub_link(p, '../', 'en')}<time datetime="{p['date'].isoformat()}">{ru_date(p['date'], 'en')}</time>{upd}</div>
<h1>{esc(p['title'])}</h1></div>"""
        box = f'<div class="box"><h2>Case file</h2>{docket(p, "en")}</div>' if p["rubric"] == "konflikty" else ""
        src = "".join(f'<li><a href="{esc(u)}" rel="noopener">{esc(t)}</a></li>' for t, u in p["sources"])
        ru = ru_by_slug.get(p.get("ru"))
        ru_link = f' <a href="../../materialy/{ru["slug"]}.html" lang="ru">Read in Russian</a>.' if ru else ""
        main = f"""<article>{box}
{p['body']}
<section class="sources"><h2>Sources</h2><p class="note" style="margin:0 0 .6rem">Most sources are in Russian.</p><ul>{src}</ul></section>
<p class="sign"><strong>Kurs Media editorial team.</strong> Corrections and statements from the parties: <a href="mailto:{EMAIL}">{EMAIL}</a>.{ru_link}</p>
</article>"""
        ld = {"@context": "https://schema.org", "@type": "NewsArticle", "headline": p["title"], "description": p["description"],
              "datePublished": p["date"].isoformat() + "+03:00", "dateModified": p["updated"].isoformat() + "+03:00", "inLanguage": "en",
              "author": {"@type": "Organization", "name": EN_NAME, "url": SITE_URL + "/en/"}, "publisher": {"@type": "Organization", "name": EN_NAME, "url": SITE_URL + "/"},
              "mainEntityOfPage": url_of(path), "image": f"{SITE_URL}/img/og.png"}
        ru_path = f"materialy/{ru['slug']}.html" if ru else None
        put(path, f"{p['seo_title']} — {EN_NAME}", p["description"], slab, main, "../../", current=p["rubric"], og_type="article",
            alts=pair(ru_path, path) if ru else None, switch=f"../../{ru_path}" if ru else None,
            extra_head=f'\n<script type="application/ld+json">{json.dumps(ld)}</script>')

    # о проекте
    slab = '<div class="pagehead"><h1>About</h1><p>Who we are, how we cover disputes, how to reach us.</p></div>'
    main = f"""<div class="prose">
<p>Kurs Media is an independent Russian outlet covering business, money and power in Russia. The English edition focuses on corporate conflicts: lawsuits, arbitration and disputes between companies, shareholders and regulators. The Russian edition is at <a href="../index.html" lang="ru">kursmedia.com</a>; its Telegram channel <a href="{CHANNEL}" rel="noopener">«Курс дела»</a> is registered with Russia's media regulator.</p>
<h2>How we cover disputes</h2>
<p>We set out each party's position in equal detail, based on their own statements and filings. Court rulings are cited with the court, case number and status — whether a ruling is final or under appeal. We do not judge who is right on the merits; that is for the courts. Russian legal terms are explained for international readers, and ruble amounts are given alongside approximate dollar figures where useful.</p>
<p>Case files are updated when a new ruling or statement appears. If your company is a party to a dispute and its position is stated inaccurately, write to {EMAIL}. We will check the text against the documents, correct it and note the date of the correction.</p>
<p>Coverage is never published, edited or removed for payment.</p>
<h2>Contact</h2>
<p>Editorial, statements from the parties, corrections:</p>
<p class="contact"><a href="mailto:{EMAIL}">{EMAIL}</a></p>
</div>"""
    put("en/about.html", f"About — {EN_NAME}", "Who writes Kurs Media, how we cover Russian corporate disputes, and how to contact the editors.", slab, main, "../",
        current="about", alts=pair("o-proekte.html", "en/about.html"), switch="../o-proekte.html")

    items = "".join(f"<item><title>{esc(p['title'])}</title><link>{url_of('en/' + art_path(p, 'en'))}</link><guid>{url_of('en/' + art_path(p, 'en'))}</guid>"
                    f"<pubDate>{p['date'].strftime('%a, %d %b %Y %H:%M:%S')} +0300</pubDate><description>{esc(p['description'])}</description></item>\n" for p in posts[:30])
    (OUT / "en" / "rss.xml").write_text(f'<?xml version="1.0" encoding="UTF-8"?>\n<rss version="2.0"><channel><title>{EN_NAME}</title><link>{SITE_URL}/en/</link>'
                                        f"<description>{esc(EN_TAGLINE)}</description><language>en</language>\n{items}</channel></rss>\n", encoding="utf-8")
    return urls


if __name__ == "__main__":
    build()
