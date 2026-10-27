#!/usr/bin/env python3
"""Сборка сайта «Курс дела».

Запуск:  python3 build.py
Материалы лежат в content/*.md (английские — в content_en/*.md), готовый сайт собирается в docs/ (эту папку раздаёт GitHub Pages).

Поля материала (до строки ---):
  title, seo_title, date (ГГГГ-ММ-ДД ЧЧ:ММ, Москва), updated, rubric, description, src: Название | URL (сколько угодно)
  фото:      image (файл в static/img, готовится через tools/photo.py), image_caption, image_credit, image_license, image_src
  инфографика внутри текста: graphic, graphic_alt
  споры:     a, b, b_rod, sud, delo, cena, stadiya
  календарь: next: ГГГГ-ММ-ДД | что произойдёт (сколько угодно)
Одно фото — один материал: повтор снимка остановит сборку.
"""
import html, json, re, shutil, datetime as dt
from pathlib import Path
from urllib.parse import quote

# ---------- настройки ----------
SITE_URL = "https://kursmedia.com"   # свой домен, без косой черты в конце
SITE_NAME = "Курс дела Медиа"
BRAND = "Курс дела"                   # название в шапке
MOTTO = "Конфликты, деньги, власть"
TAGLINE = "Конфликты, деньги, власть: что произошло, сколько это стоит и кому выгодно."
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
WEEKDAYS = "понедельник вторник среда четверг пятница суббота воскресенье".split()
WEEKDAYS_EN = "Monday Tuesday Wednesday Thursday Friday Saturday Sunday".split()
LICENSES = {  # лицензия фото: адрес текста лицензии без языкового суффикса
    "CC0": "https://creativecommons.org/publicdomain/zero/1.0/deed.",
    "CC BY 2.0": "https://creativecommons.org/licenses/by/2.0/deed.",
    "CC BY 3.0": "https://creativecommons.org/licenses/by/3.0/deed.",
    "CC BY 4.0": "https://creativecommons.org/licenses/by/4.0/deed.",
    "CC BY-SA 2.0": "https://creativecommons.org/licenses/by-sa/2.0/deed.",
    "CC BY-SA 3.0": "https://creativecommons.org/licenses/by-sa/3.0/deed.",
    "CC BY-SA 3.0 DE": "https://creativecommons.org/licenses/by-sa/3.0/de/deed.",
    "CC BY-SA 4.0": "https://creativecommons.org/licenses/by-sa/4.0/deed.",
}


def esc(s):
    return html.escape(str(s), quote=True)


def ru_date(d, lang="ru", year=True):
    m = (MONTHS_EN if lang == "en" else MONTHS)[d.month - 1]
    return f"{d.day} {m}" + (f" {d.year}" if year else "")


def card_date(d, lang="ru"):
    return ru_date(d, lang, year=d.year != NOW_MSK.year)


def inline(s):
    s = esc(s)
    s = re.sub(r"\[([^\]]+)\]\((https?://[^)\s]+)\)", r'<a href="\2" rel="noopener">\1</a>', s)
    return re.sub(r"\*\*(.+?)\*\*", r"<strong>\1</strong>", s)


def md(body):
    return [f"<p>{inline(' '.join(b.split()))}</p>" for b in re.split(r"\n\s*\n", body.strip()) if b.strip()]


def load(src=SRC):
    posts = []
    for f in sorted(src.glob("*.md")):
        head, body = f.read_text(encoding="utf-8").split("\n---\n", 1)
        meta, sources, nxt = {}, [], []
        for line in head.splitlines():
            if not line.strip() or line.strip() == "---":
                continue
            k, v = line.split(":", 1)
            k, v = k.strip(), v.strip()
            if k == "src":
                t, u = v.rsplit("|", 1)
                sources.append((t.strip(), u.strip()))
            elif k == "next":
                d, t = v.split("|", 1)
                nxt.append((dt.date.fromisoformat(d.strip()), t.strip()))
            else:
                meta[k] = v
        meta["date"] = dt.datetime.strptime(meta["date"], "%Y-%m-%d %H:%M")
        if meta["date"] > NOW_MSK:   # отложенный материал: выйдет при первой сборке после этой даты (время московское)
            print(f"  отложено до {meta['date']:%d.%m %H:%M}: {f.stem}")
            continue
        meta["updated"] = dt.datetime.strptime(meta["updated"], "%Y-%m-%d %H:%M") if "updated" in meta else meta["date"]
        meta.update(slug=f.stem, sources=sources, next=nxt, paras=md(body), plain=" ".join(body.split()))
        meta.setdefault("seo_title", meta["title"])
        posts.append(meta)
    return sorted(posts, key=lambda p: p["date"], reverse=True)


def check_photos(posts, posts_en):
    """Каждый снимок — только к одному материалу. Английский перевод может повторять фото своего русского оригинала."""
    seen = {}
    for p in posts:
        if p.get("image"):
            if p["image"] in seen:
                raise SystemExit(f"Фото {p['image']} уже стоит в материале {seen[p['image']]} — нужен другой снимок для {p['slug']}")
            seen[p["image"]] = p["slug"]
            if not (STATIC / "img" / p["image"]).exists():
                raise SystemExit(f"Нет файла static/img/{p['image']} для {p['slug']}")
    for p in posts_en:
        if p.get("image") and p["image"] in seen and seen[p["image"]] != p.get("ru"):
            raise SystemExit(f"Фото {p['image']} принадлежит материалу {seen[p['image']]}, а стоит в английском {p['slug']}")


CYR = "U+0301,U+0400-045F,U+0490-0491,U+04B0-04B1,U+2116"
LAT = "U+0000-00FF,U+0131,U+0152-0153,U+02BB-02BC,U+02C6,U+02DA,U+02DC,U+0304,U+0308,U+0329,U+2000-206F,U+20AC,U+2122,U+2191,U+2193,U+2212,U+2215,U+FEFF,U+FFFD"
FACES = [  # семейство, файл без набора символов, насыщенность, начертание
    ("Old Standard TT", "old-standard-tt-{}-700-normal", "700", "normal"),
    ("Old Standard TT", "old-standard-tt-{}-400-italic", "400", "italic"),
    ("Literata", "literata-{}-standard-normal", "200 900", "normal"),
    ("Literata", "literata-{}-standard-italic", "200 900", "italic"),
    ("Golos Text", "golos-text-{}-wght-normal", "400 900", "normal"),
]
FONTFACE = "".join(f"@font-face{{font-family:'{fam}';src:url(/fonts/{f.format(sub)}.woff2) format('woff2');font-weight:{w};font-style:{s};font-display:swap;unicode-range:{rng}}}\n"
                   for fam, f, w, s in FACES for sub, rng in (("cyrillic", CYR), ("latin", LAT)))

CSS = FONTFACE + """
/* Курс дела. Ориентир — деловые газеты: белая бумага, название по центру, тёмная полоса рубрик.
   Название набрано Old Standard — шрифтом русских газет начала XX века. Заголовки и текст — Literata, интерфейс — Golos Text.
   Лайм — фирменный цвет канала — только на тёмном; на белом его заменяет оливковый. */
:root{--paper:#FFFFFF;--ink:#141922;--ink-2:#394049;--muted:#646B77;--rule:#DCDFE3;--panel:#F3F4F0;
 --band:#141922;--band-ink:#F3F4EF;--band-muted:#9AA2AF;--band-rule:#2B313C;--lime:#CCFF33;--olive:#4C6B00;
 --plate:"Old Standard TT",Georgia,serif;--serif:"Literata",Georgia,"Times New Roman",serif;--sans:"Golos Text","Helvetica Neue",Arial,sans-serif;color-scheme:light}
@media (prefers-color-scheme:dark){:root:not([data-theme="light"]){--paper:#0F1218;--ink:#E8EAEE;--ink-2:#C4C9D1;--muted:#9AA1AD;--rule:#282D37;--panel:#181C24;--band:#080A0E;--band-rule:#232833;--olive:#C2EB4A;color-scheme:dark}}
:root[data-theme="dark"]{--paper:#0F1218;--ink:#E8EAEE;--ink-2:#C4C9D1;--muted:#9AA1AD;--rule:#282D37;--panel:#181C24;--band:#080A0E;--band-rule:#232833;--olive:#C2EB4A;color-scheme:dark}
*{box-sizing:border-box}
html{-webkit-text-size-adjust:100%}
body{margin:0;background:var(--paper);color:var(--ink);font:400 1rem/1.5 var(--serif);font-optical-sizing:auto;-webkit-font-smoothing:antialiased;text-rendering:optimizeLegibility}
img{display:block;max-width:100%;height:auto}
a{color:inherit;text-decoration:none}
a:hover{text-decoration:underline;text-decoration-thickness:1px;text-underline-offset:.16em}
:focus-visible{outline:2px solid var(--olive);outline-offset:2px}
.wrap{max-width:78rem;margin-inline:auto;padding-inline:clamp(1rem,3vw,2rem)}
.skip{position:absolute;left:-999px;top:0;background:var(--ink);color:var(--paper);padding:.6rem 1rem;font:600 .9rem var(--sans);z-index:9}.skip:focus{left:1rem}
/* шапка */
.np-row{display:grid;grid-template-columns:minmax(0,1fr) auto minmax(0,1fr);align-items:center;gap:1.5rem;padding-block:1.15rem 1.05rem}
.np-c{text-align:center}
.np{display:inline-block;font:700 clamp(2.75rem,6.6vw,5.4rem)/1 var(--plate);letter-spacing:-.005em;white-space:nowrap;padding-bottom:.06em}
.np:hover{text-decoration:none}
.ear{min-width:0}.ear-l{justify-self:start}.ear-r{justify-self:end;text-align:right}
.motto{margin:0;display:inline-block;border:1px solid var(--ink);padding:.5rem .85rem .55rem;font:italic 400 1.02rem/1.28 var(--plate);text-align:center}
.motto-m{display:none}
.fx{margin:0;font:500 .82rem/1.5 var(--sans);color:var(--ink-2);font-variant-numeric:tabular-nums}
.fx b{display:block;font-weight:600;color:var(--ink);margin-bottom:.15rem}
.fx span{display:block}.fx i{font-style:normal;font-size:.72em;color:var(--muted);margin-left:.3em}
.band{background:var(--band);color:var(--band-ink)}
.band .wrap{display:grid;grid-template-columns:minmax(0,1fr) auto minmax(0,1fr);align-items:center;gap:1rem}
.today{font:500 .8rem/1 var(--sans);color:var(--band-muted);white-space:nowrap}
.band nav{display:flex;gap:clamp(1.1rem,2.4vw,2.2rem);font:600 .96rem/1 var(--sans);padding-block:1rem;overflow-x:auto;scrollbar-width:none}
.band nav::-webkit-scrollbar{display:none}
@media (max-width:60rem){.band nav{-webkit-mask-image:linear-gradient(to right,#000 82%,transparent);mask-image:linear-gradient(to right,#000 82%,transparent);padding-right:2rem}}
.band nav a{white-space:nowrap}
.band nav a:hover,.util a:hover{color:var(--lime);text-decoration:none}
.band nav a[aria-current="page"]{color:var(--lime)}
.util{justify-self:end;display:flex;gap:1.2rem;font:500 .8rem/1 var(--sans);color:var(--band-muted);white-space:nowrap}
.band :focus-visible,.foot :focus-visible{outline-color:var(--lime)}
@media (max-width:60rem){.ear{display:none}.np-row{grid-template-columns:1fr;padding-block:.95rem .8rem}
 .motto-m{display:block;margin:.3rem 0 0;font:italic 400 1rem/1.2 var(--plate);color:var(--ink-2)}
 .today{display:none}.band .wrap{grid-template-columns:minmax(0,1fr) auto}}
@media (max-width:40rem){.util .tg{display:none}.band nav{padding-block:.9rem}}
/* общие элементы */
main{padding-block:1.6rem 1rem}
.sh{display:flex;align-items:baseline;justify-content:space-between;gap:1rem;border-top:2px solid var(--ink);padding-top:.5rem;margin:0 0 1rem}
.sh h2{margin:0;font:700 1.22rem/1.2 var(--serif);letter-spacing:-.005em}
.sh .all{font:500 .82rem/1.2 var(--sans);color:var(--muted);white-space:nowrap}
.kick{display:flex;flex-wrap:wrap;align-items:baseline;gap:.15rem .7rem;margin:0 0 .35rem;font:500 .78rem/1.3 var(--sans);color:var(--muted)}
.rub{font-weight:600;color:var(--olive)}
.ph{display:block;aspect-ratio:3/2;overflow:hidden;background:var(--panel)}
.ph img{width:100%;height:100%;object-fit:cover}
.dek{margin:0;font:400 .96rem/1.5 var(--serif);color:var(--ink-2)}
.credit{margin:.35rem 0 .85rem;font:400 .72rem/1.3 var(--sans);color:var(--muted);text-align:right}
.pt{font-weight:700}.vs{font-weight:400;font-style:italic;color:var(--muted)}
h2 a:hover,h3 a:hover{text-decoration-thickness:2px}
/* главная: первый экран */
.top{display:grid;grid-template-columns:minmax(0,2.2fr) minmax(0,1fr) minmax(0,.98fr);padding-bottom:1.6rem;border-bottom:1px solid var(--rule)}
.top>*{min-width:0;padding-inline:1.4rem}
.top>*+*{border-left:1px solid var(--rule)}
.top>:first-child{padding-left:0}.top>:last-child{padding-right:0}
.top.no-col{grid-template-columns:minmax(0,2.2fr) minmax(0,1fr)}
.lead h2{margin:.1rem 0 .55rem;font:700 clamp(1.75rem,2.7vw,2.3rem)/1.1 var(--serif);letter-spacing:-.014em;text-wrap:balance}
.lead .dek{font-size:1.08rem;line-height:1.5;margin-bottom:1rem}
.lead .credit{margin-bottom:0}
.sub{display:grid;grid-template-columns:1fr 1fr;gap:1.4rem;margin-top:1.1rem;padding-top:1.1rem;border-top:1px solid var(--rule)}
.second .s+.s{margin-top:1rem;padding-top:1rem;border-top:1px solid var(--rule)}
.second .ph{margin-bottom:.65rem}
.second h3{margin:0 0 .35rem;font:700 1.18rem/1.22 var(--serif);text-wrap:balance}
.second .dek{font-size:.92rem;display:-webkit-box;-webkit-line-clamp:4;-webkit-box-orient:vertical;overflow:hidden}
.mini{list-style:none;margin:0;padding:0}
.mini li{padding-block:.65rem;border-bottom:1px solid var(--rule);break-inside:avoid}
.mini li:first-child{padding-top:0}
.mini a{display:block;font:400 1.02rem/1.27 var(--serif)}
.mini .st{display:block;margin-top:.25rem;font:400 .8rem/1.4 var(--sans);color:var(--muted)}
.more{display:inline-block;margin-top:.7rem;font:600 .82rem/1.3 var(--sans);color:var(--olive)}
.dates{margin-top:1.6rem}
.dates ol{list-style:none;margin:0;padding:0}
.dates li{padding-block:.55rem;border-bottom:1px solid var(--rule);font:400 .86rem/1.38 var(--sans)}
.dates li:first-child{padding-top:0}
.dates time{display:block;margin-bottom:.1rem;font-weight:700}
@media (max-width:72rem){.top{grid-template-columns:minmax(0,1.7fr) minmax(0,1fr)}
 .top>.col{grid-column:1/-1;border-left:0;padding:1.4rem 0 0;margin-top:1.4rem;border-top:1px solid var(--rule);display:grid;grid-template-columns:minmax(0,1.6fr) minmax(0,1fr);gap:0 2rem}
 .col .mini{columns:2 15rem;column-gap:2rem}.col .dates{margin-top:0}}
@media (max-width:48rem){.top{grid-template-columns:1fr}.top>*{padding-inline:0!important;border-left:0!important}
 .second{margin-top:1.3rem;padding-top:1.2rem;border-top:1px solid var(--rule)}.top>.col{display:block}.col .mini{columns:1}.col .dates{margin-top:1.5rem}}
/* главная: рубрики */
.sect{margin-top:2.4rem}
.feat{display:grid;grid-template-columns:repeat(4,minmax(0,1fr));gap:1.5rem 1.5rem}
.f-big{grid-column:span 2;grid-row:span 2}
.f-big .ph{margin-bottom:.7rem}
.f-big h3{margin:.1rem 0 .5rem;font:700 clamp(1.4rem,2.2vw,1.8rem)/1.15 var(--serif);letter-spacing:-.01em;text-wrap:balance}
.f-big .dek{font-size:1.02rem}
.cards{display:grid;grid-template-columns:repeat(auto-fit,minmax(14.5rem,1fr));gap:1.5rem}
.card .ph{margin-bottom:.6rem}
.card h3{margin:.05rem 0 .35rem;font:700 1.06rem/1.26 var(--serif);text-wrap:balance}
.card .dek{font-size:.9rem;line-height:1.45}
.card .st{margin:0;font:400 .82rem/1.4 var(--sans);color:var(--muted)}
.trio{display:grid;grid-template-columns:repeat(auto-fit,minmax(14rem,1fr));gap:2rem 1.5rem}
.trio>div{min-width:0}
.duo{grid-template-columns:repeat(auto-fit,minmax(24rem,1fr))}
.duo .card,.solo .card{display:grid;grid-template-columns:minmax(0,1.1fr) minmax(0,1fr);column-gap:1.2rem;align-content:start}
.duo .card .ph,.solo .card .ph{grid-row:1/span 4;margin:0}
.solo{grid-template-columns:minmax(0,1fr)}
.heads{list-style:none;margin:.8rem 0 0;padding:0}
.heads li{padding-block:.6rem;border-top:1px solid var(--rule);break-inside:avoid}
.heads>li>a{font:700 .98rem/1.3 var(--serif)}
.heads .kick{margin:0 0 .2rem}
.rest .heads{margin-top:0}.rest .heads li:first-child{border-top:0;padding-top:0}
@media (max-width:64rem){.feat{grid-template-columns:repeat(2,minmax(0,1fr))}}
@media (max-width:36rem){.feat,.cards,.sub{grid-template-columns:1fr;gap:0}.sub>*{padding-block:1rem;border-top:1px solid var(--rule)}.sub>:first-child{border-top:0;padding-top:0}
 .feat>*,.cards>*{padding-block:1rem;border-top:1px solid var(--rule)}
 .feat>:first-child,.cards>:first-child{border-top:0;padding-top:0}
 .card,.duo .card,.solo .card{display:grid;grid-template-columns:minmax(0,1fr) 6.8rem;column-gap:.9rem;align-items:start}
 .card .ph{grid-column:2;grid-row:1/span 4;margin:0}.card>:not(.ph){grid-column:1}.card .dek{display:none}}
/* рубрика */
.pagehead{padding-block:.4rem 1.2rem;margin-bottom:1.5rem;border-bottom:1px solid var(--rule)}
.pagehead h1{margin:0;font:700 clamp(2rem,4.4vw,3.1rem)/1.05 var(--serif);letter-spacing:-.016em}
.pagehead p{margin:.45rem 0 0;font:400 1rem/1.5 var(--sans);color:var(--muted);max-width:62ch}
.with-rail{display:grid;grid-template-columns:minmax(0,1fr) 21rem;gap:0 clamp(2rem,4vw,3.5rem);align-items:start}
.r-lead{display:grid;grid-template-columns:minmax(0,1.35fr) minmax(0,1fr);gap:1.5rem;padding-bottom:1.5rem;border-bottom:1px solid var(--rule)}
.r-lead h2{margin:.1rem 0 .5rem;font:700 clamp(1.45rem,2.5vw,2rem)/1.13 var(--serif);letter-spacing:-.01em;text-wrap:balance}
.row{display:grid;grid-template-columns:minmax(0,1fr) 12.5rem;gap:1.4rem;padding-block:1.3rem;border-bottom:1px solid var(--rule)}
.row h3{margin:.05rem 0 .4rem;font:700 1.22rem/1.24 var(--serif);text-wrap:balance}
.row .ph,.r-lead .ph{align-self:start}
.mdock{display:flex;flex-wrap:wrap;gap:.2rem 1.2rem;margin:.55rem 0 0;font:400 .8rem/1.4 var(--sans);color:var(--muted)}
.mdock b{font-weight:600;color:var(--ink)}
.note{font:400 1rem/1.5 var(--sans);color:var(--muted);max-width:60ch}
@media (max-width:62rem){.with-rail{grid-template-columns:1fr}.with-rail>.rail{margin-top:2.5rem}}
@media (max-width:48rem){.r-lead{grid-template-columns:1fr}.row{grid-template-columns:minmax(0,1fr) 6.8rem;gap:.9rem}.row h3{font-size:1.06rem}.row .dek{display:none}}
/* материал */
.story-head{max-width:50rem;padding-top:.2rem}
.story-head h1{margin:.15rem 0 .65rem;font:700 clamp(1.95rem,4.3vw,3rem)/1.1 var(--serif);letter-spacing:-.016em;text-wrap:balance}
.story-head .dek{font-size:clamp(1.08rem,1.7vw,1.27rem);line-height:1.45}
.byline{display:flex;flex-wrap:wrap;align-items:center;justify-content:space-between;gap:.7rem 1.5rem;margin:1.15rem 0 1.4rem;padding-block:.7rem;border-block:1px solid var(--rule);font:400 .84rem/1.4 var(--sans);color:var(--muted)}
.byline .when{display:flex;flex-wrap:wrap;gap:.15rem 1rem}
.byline .by{font-weight:600;color:var(--ink)}
.share{display:flex;flex-wrap:wrap;align-items:center;gap:.4rem}
.share a,.share button{font:600 .78rem/1 var(--sans);color:var(--ink);background:none;border:1px solid var(--rule);border-radius:2rem;padding:.48rem .75rem;cursor:pointer}
.share a:hover,.share button:hover{border-color:var(--ink);text-decoration:none}
.hero{margin:0 0 1.6rem}
figcaption{margin-top:.5rem;font:400 .82rem/1.45 var(--sans);color:var(--ink-2)}
figcaption .cr{color:var(--muted)}
figcaption a{text-decoration:underline;text-decoration-color:var(--rule)}
.story-grid{display:grid;grid-template-columns:minmax(0,1fr) 22rem;grid-template-rows:auto 1fr;grid-template-areas:"hero rail" "body rail";column-gap:clamp(2rem,4vw,3.5rem);align-items:start}
.story-grid.has-file{grid-template-areas:"hero file" "body rail"}
.hero{grid-area:hero;max-width:42rem}.body{grid-area:body;max-width:42rem}.file{grid-area:file}.story-grid>.rail{grid-area:rail}
.body>p{margin:0 0 1.15em;font:400 1.1875rem/1.64 var(--serif)}
.body strong{font-weight:700}
.body a{text-decoration:underline;text-decoration-color:var(--olive);text-underline-offset:.15em}
.graphic{margin:1.6rem 0 1.9rem}.graphic img{border:1px solid var(--rule)}
.box{background:var(--panel);border-top:3px solid var(--ink);padding:1rem 1.15rem 1.15rem;margin-bottom:1.6rem}
.box h2{margin:0 0 .8rem;font:700 .95rem/1.2 var(--sans)}
.docket{display:grid;gap:.75rem;margin:0;font:400 .88rem/1.42 var(--sans)}
.docket dt{color:var(--muted);font-size:.78rem}
.docket dd{margin:.1rem 0 0;font-weight:600}
.latest ol{list-style:none;margin:0;padding:0}
.latest li{display:grid;grid-template-columns:5.6rem minmax(0,1fr);gap:.8rem;align-items:start;padding-block:.75rem;border-bottom:1px solid var(--rule)}
.latest li:first-child{padding-top:.1rem}
.latest a.t{font:700 .95rem/1.28 var(--serif)}
.latest .kick{margin:.25rem 0 0}
.sources{margin-top:2.4rem;padding-top:.7rem;border-top:2px solid var(--ink);font:400 .92rem/1.5 var(--sans)}
.sources h2{margin:0 0 .6rem;font:700 1rem/1.2 var(--sans)}
.sources ul{margin:0;padding-left:1.1rem}.sources li+li{margin-top:.35rem}
.sources a{text-decoration:underline;text-decoration-color:var(--rule)}
.body>.sign{margin:1.6rem 0 0;font:400 .92rem/1.55 var(--sans);color:var(--muted)}
.sign strong{color:var(--ink)}.sign a{text-decoration:underline;text-decoration-color:var(--rule)}
.related{margin-top:3rem}
@media (max-width:62rem){.story-grid,.story-grid.has-file{grid-template-columns:1fr;grid-template-rows:auto;grid-template-areas:"hero" "file" "body" "rail"}.body,.hero{max-width:none}.story-grid>.rail{margin-top:2.6rem}.docket{grid-template-columns:repeat(auto-fit,minmax(12rem,1fr))}}
@media (max-width:48rem){.hero{margin-inline:calc(-1*clamp(1rem,3vw,2rem))}.hero figcaption{padding-inline:clamp(1rem,3vw,2rem)}.body>p{font-size:1.0625rem;line-height:1.62}.byline{align-items:flex-start}}
/* о проекте */
.prose{max-width:42rem}
.prose h2{margin:2.2rem 0 .7rem;font:700 1.4rem/1.25 var(--serif)}
.prose p{margin:0 0 1.1em;font:400 1.1rem/1.65 var(--serif)}
.prose a{text-decoration:underline;text-decoration-color:var(--olive)}
.contact{font:700 1.25rem/1.3 var(--sans)!important}
/* подвал */
.foot{background:var(--band);color:var(--band-muted);margin-top:3rem;padding-block:2.2rem 2.8rem;font:400 .85rem/1.55 var(--sans)}
.foot .wrap{display:grid;grid-template-columns:auto minmax(0,1fr);gap:1.5rem 3.5rem;align-items:start}
.foot .np{font-size:2.3rem;color:var(--band-ink)}
.foot .fm{margin:.35rem 0 0;font:italic 400 1rem/1.2 var(--plate)}
.foot nav{display:flex;flex-wrap:wrap;gap:.5rem 1.5rem;font:600 .92rem/1.4 var(--sans);color:var(--band-ink)}
.foot nav a:hover,.foot p a:hover{color:var(--lime);text-decoration:none}
.foot p{margin:.8rem 0 0;max-width:68ch}
.foot p a{color:var(--band-ink)}
@media (max-width:48rem){.foot .wrap{grid-template-columns:1fr}}
"""

JS = """(function(){var en=document.documentElement.lang==='en',M=en?'January February March April May June July August September October November December'.split(' '):'января февраля марта апреля мая июня июля августа сентября октября ноября декабря'.split(' '),
W=en?'Sunday Monday Tuesday Wednesday Thursday Friday Saturday'.split(' '):'воскресенье понедельник вторник среда четверг пятница суббота'.split(' '),
n=new Date(Date.now()+(180+new Date().getTimezoneOffset())*6e4),p=function(x){return(x<10?'0':'')+x},iso=n.getFullYear()+'-'+p(n.getMonth()+1)+'-'+p(n.getDate());
var t=document.querySelector('[data-today]');if(t)t.textContent=en?W[n.getDay()]+', '+n.getDate()+' '+M[n.getMonth()]+' '+n.getFullYear():n.getDate()+' '+M[n.getMonth()]+' '+n.getFullYear()+', '+W[n.getDay()];
var cur=document.querySelector('.band nav [aria-current]');if(cur&&cur.offsetLeft+cur.offsetWidth>cur.parentNode.clientWidth)cur.parentNode.scrollLeft=cur.offsetLeft-16;
document.querySelectorAll('[data-d]').forEach(function(li){if(li.getAttribute('data-d')<iso)li.remove()});
document.querySelectorAll('.dates').forEach(function(s){if(!s.querySelector('li'))s.remove()});
document.querySelectorAll('[data-copy]').forEach(function(b){b.addEventListener('click',function(){if(navigator.clipboard)navigator.clipboard.writeText(location.href).then(function(){b.textContent=b.getAttribute('data-copy')})})});
var fx=document.getElementById('fx');if(!fx||!window.fetch||getComputedStyle(fx.parentNode).display==='none')return;
fetch('https://www.cbr-xml-daily.ru/daily_json.js').then(function(r){return r.json()}).then(function(d){var V=d.Valute,ds=d.Date.slice(0,10).split('-'),day=+ds[2],mo=M[+ds[1]-1],
f=function(x){return x.toFixed(2).replace('.',en?'.':',')},h='<b>'+(en?'Bank of Russia rates, '+day+' '+mo:'Курсы ЦБ на '+day+' '+mo)+'</b>';
[['USD','$'],['EUR','€'],['CNY','¥']].forEach(function(c){var v=V[c[0]];if(!v)return;var a=v.Value/v.Nominal,b=v.Previous/v.Nominal;h+='<span>'+c[1]+' '+f(a)+(a>b?'<i title="'+(en?'up':'вырос')+'">▲</i>':a<b?'<i title="'+(en?'down':'снизился')+'">▼</i>':'')+'</span>'});
fx.innerHTML=h;fx.hidden=false}).catch(function(){})})();"""

FONTS = ('<link rel="preload" href="/fonts/literata-cyrillic-standard-normal.woff2" as="font" type="font/woff2" crossorigin>'
         '<link rel="preload" href="/fonts/old-standard-tt-cyrillic-700-normal.woff2" as="font" type="font/woff2" crossorigin>'
         '<link rel="preload" href="/fonts/golos-text-cyrillic-wght-normal.woff2" as="font" type="font/woff2" crossorigin>')


def url_of(path):
    return f"{SITE_URL}/" + (path[:-len("index.html")] if path.endswith("index.html") else path)


def page(path, title, desc, main, up="", current="", extra_head="", og_image="img/og.png", og_type="website",
         lang="ru", alts=None, switch=None):
    """Возвращает (head, body). up — префикс до корня сайта ('', '../', '../../').
    alts — список (hreflang, url) для парных страниц; switch — ссылка переключателя языка."""
    url = url_of(path)
    cur = lambda k: ' aria-current="page"' if current == k else ""
    en = lang == "en"
    if en:
        base = f"{up}en/"
        rub = "".join(f'<a href="{base}{f}"{cur(k)}>{n}</a>' for k, (n, f, _) in RUBRICS_EN.items())
        nav = rub + f'<a href="{base}about.html"{cur("about")}>About</a>'
        lang_a = f'<a href="{switch or up + "index.html"}" lang="ru" hreflang="ru">Русский</a>'
        name, home, wm, motto, motto2 = EN_NAME, f"{base}index.html", EN_NAME, EN_MOTTO, "Conflicts,<br>money, power"
        tg, today = "Telegram", f"{WEEKDAYS_EN[NOW_MSK.weekday()]}, {ru_date(NOW_MSK, 'en')}"
        foot = (f"© {NOW_MSK.year} {EN_NAME}. Based on public sources, linked in every article. Opinions are those of the editors. "
                "Photos are used under free licences (Wikimedia Commons, Kremlin.ru, the White House and others); authors and licences are credited under each photo.")
        fl = f'{rub}<a href="{base}about.html">About</a><a href="{base}rss.xml">RSS</a><a href="{up}index.html" lang="ru">Русская версия</a>'
        rss, locale, navlabel = f"{SITE_URL}/en/rss.xml", "en_US", "Sections"
    else:
        rub = "".join(f'<a href="{up}{f}"{cur(k)}>{n}</a>' for k, (n, f, _) in RUBRICS.items())
        nav = rub + f'<a href="{up}o-proekte.html"{cur("about")}>О проекте</a>'
        lang_a = f'<a href="{switch or up + "en/index.html"}" lang="en" hreflang="en">English</a>'
        name, home, wm, motto, motto2 = SITE_NAME, f"{up}index.html", BRAND, MOTTO, "Конфликты,<br>деньги, власть"
        tg, today = "Телеграм-канал", f"{ru_date(NOW_MSK)}, {WEEKDAYS[NOW_MSK.weekday()]}"
        foot = (f"© {NOW_MSK.year} «{SITE_NAME}». Материалы подготовлены по открытым источникам, ссылки на них даны в каждом тексте. Оценки отражают мнение редакции. "
                "Фото используются по свободным лицензиям (Wikimedia Commons, Kremlin.ru, Белый дом и другие), автор и лицензия указаны под каждым снимком.")
        fl = f'{rub}<a href="{up}o-proekte.html">О проекте</a><a href="{CHANNEL}" rel="noopener">Телеграм-канал</a><a href="{up}rss.xml">RSS</a><a href="{up}en/index.html" lang="en">English</a>'
        rss, locale, navlabel = f"{SITE_URL}/rss.xml", "ru_RU", "Рубрики"
    hl = "".join(f'\n<link rel="alternate" hreflang="{h}" href="{u}">' for h, u in (alts or []))
    head = f"""<title>{esc(title)}</title>
<meta name="description" content="{esc(desc)}">
<link rel="canonical" href="{url}">{hl}
<meta property="og:site_name" content="{name}"><meta property="og:type" content="{og_type}"><meta property="og:locale" content="{locale}">
<meta property="og:title" content="{esc(title)}"><meta property="og:description" content="{esc(desc)}">
<meta property="og:url" content="{url}"><meta property="og:image" content="{SITE_URL}/{og_image}">
<meta name="twitter:card" content="summary_large_image">
<meta name="theme-color" content="#141922">
<link rel="icon" href="{up}favicon.ico" sizes="48x48">
<link rel="icon" href="{up}favicon-96.png" type="image/png" sizes="96x96">
<link rel="icon" href="{up}favicon-192.png" type="image/png" sizes="192x192">
<link rel="icon" href="{up}favicon.svg" type="image/svg+xml">
<link rel="apple-touch-icon" href="{up}apple-touch-icon.png">
<link rel="alternate" type="application/rss+xml" title="{name}" href="{rss}">
<link rel="preconnect" href="https://www.cbr-xml-daily.ru" crossorigin>
{FONTS}
<style>{CSS}</style>{extra_head}"""
    body = f"""<a class="skip" href="#main">{"Skip to content" if en else "К материалам"}</a>
<header class="mast"><div class="wrap np-row">
<div class="ear ear-l"><p class="motto">{motto2}</p></div>
<div class="np-c"><a class="np" href="{home}">{wm}</a><p class="motto-m">{motto}</p></div>
<div class="ear ear-r"><p class="fx" id="fx" hidden></p></div>
</div>
<div class="band"><div class="wrap"><span class="today" data-today>{today}</span>
<nav aria-label="{navlabel}">{nav}</nav>
<span class="util"><a class="tg" href="{CHANNEL}" rel="noopener">{tg}</a>{lang_a}</span></div></div></header>
<main id="main"><div class="wrap">
{main}
</div></main>
<footer class="foot"><div class="wrap">
<div><a class="np" href="{home}">{wm}</a><p class="fm">{motto}</p></div>
<div><nav aria-label="{navlabel}">{fl}</nav><p>{foot}</p></div>
</div></footer>
<script>{JS}</script>"""
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
    return f'<a class="rub" href="{up}{f}">{n}</a>'


def kick(p, up="", lang="ru", rub=True):
    r = rub_link(p, up, lang) if rub else ""
    return f'<div class="kick">{r}<time datetime="{p["date"].isoformat()}">{card_date(p["date"], lang)}</time></div>'


def img(p, sizes, eager=False):
    if not p.get("image"):
        return ""
    stem = p["image"].rsplit(".", 1)[0]
    load_attr = 'fetchpriority="high"' if eager else 'loading="lazy" decoding="async"'
    return (f'<img src="/img/{stem}-800.jpg" srcset="/img/{stem}-400.jpg 400w, /img/{stem}-800.jpg 800w, /img/{stem}.jpg 1600w" '
            f'sizes="{sizes}" width="1600" height="1067" alt="{esc(p.get("image_caption", ""))}" {load_attr}>')


def ph(p, href, sizes, eager=False):
    """Фото-ссылка карточки: дублирует заголовок, поэтому скрыта от клавиатуры и экранных дикторов."""
    return f'<a class="ph" href="{href}" tabindex="-1" aria-hidden="true">{img(p, sizes, eager)}</a>' if p.get("image") else ""


def credit(p, lang="ru"):
    if not p.get("image_credit"):
        return ""
    en = lang == "en"
    lic = p.get("image_license", "")
    if lic == "PD":
        lic_h = "public domain" if en else "общественное достояние"
    elif lic in LICENSES:
        lic_h = f'<a href="{LICENSES[lic]}{"en" if en else "ru"}" rel="license noopener">{lic}</a>'
    else:
        lic_h = esc(lic)
    who = f'<a href="{esc(p["image_src"])}" rel="noopener">{esc(p["image_credit"])}</a>' if p.get("image_src") else esc(p["image_credit"])
    return f'{"Photo" if en else "Фото"}: {who}, {lic_h}'


def docket(p, lang="ru"):
    labels = ("Court", "Case No.", "At stake", "Status") if lang == "en" else ("Суд", "Номер дела", "Цена вопроса", "Стадия")
    rows = zip(labels, (p.get("sud"), p.get("delo"), p.get("cena"), p.get("stadiya")))
    return '<dl class="docket">' + "".join(f"<div><dt>{k}</dt><dd>{esc(v)}</dd></div>" for k, v in rows if v) + "</dl>"


def parties(p, lang="ru"):
    vs, b = ("v.", p["b"]) if lang == "en" else ("против", p.get("b_rod", p["b"]))
    return f'<span class="pt">{esc(p["a"])}</span> <span class="vs">{vs}</span> <span class="pt">{esc(b)}</span>'


def short(t, n=110):
    t = re.split(r"(?<=[.;])\s", t or "", maxsplit=1)[0].rstrip(";.")
    return t if len(t) <= n else t[:n].rsplit(" ", 1)[0] + "…"


def is_case(p):
    return p["rubric"] == "konflikty" and p.get("a") and p.get("b")


def card(p, lang="ru", up="", rub=False, dek=True, sizes="(min-width:78rem) 17rem, (min-width:36rem) 45vw, 7rem"):
    href = f"{up}{art_path(p, lang)}"
    if is_case(p):
        inner = f'<h3><a href="{href}">{parties(p, lang)}</a></h3><p class="st">{esc(short(p.get("stadiya", ""), 90))}</p>'
    else:
        inner = f'<h3><a href="{href}">{esc(p["title"])}</a></h3>' + (f'<p class="dek">{esc(p["description"])}</p>' if dek else "")
    return f'<article class="card">{ph(p, href, sizes)}{kick(p, up, lang, rub)}{inner}</article>'


def sect_head(title, href=None, all_label=None):
    h = f'<a href="{href}">{title}</a>' if href else title
    a = f'<a class="all" href="{href}">{all_label}</a>' if href and all_label else ""
    return f'<div class="sh"><h2>{h}</h2>{a}</div>'


def upcoming(posts, lang="ru", n=5):
    ev = sorted(((d, t, p) for p in posts for d, t in p["next"] if d >= NOW_MSK.date()), key=lambda e: (e[0], e[1]))[:n]
    if not ev:
        return ""
    li = "".join(f'<li data-d="{d.isoformat()}"><time datetime="{d.isoformat()}">{ru_date(d, lang, year=d.year != NOW_MSK.year)}</time><a href="{art_path(p, lang)}">{esc(t)}</a></li>' for d, t, p in ev)
    return f'<section class="dates">{sect_head("Coming up" if lang == "en" else "Ближайшие даты")}<ol>{li}</ol></section>'


def front(posts, lang="ru"):
    """Главная: первый экран (главный материал, ещё три, колонка споров и календарь), затем рубрики."""
    en = lang == "en"
    R = RUBRICS_EN if en else RUBRICS
    shown = set()

    def take(items, n):
        out = [p for p in items if p["slug"] not in shown][:n]
        shown.update(p["slug"] for p in out)
        return out

    L = take(posts, 1)[0]
    sub = take(posts, 2)
    sec = take(posts, 3)
    cases = sorted([p for p in posts if is_case(p)], key=lambda p: p["updated"], reverse=True)
    col = take(cases, 5)
    lead = f"""<div class="lead-col"><article class="lead">{kick(L, '', lang)}
<h2><a href="{art_path(L, lang)}">{esc(L['title'])}</a></h2><p class="dek">{esc(L['description'])}</p>
{ph(L, art_path(L, lang), "(min-width:72rem) 40rem, (min-width:48rem) 60vw, 100vw", eager=True)}<p class="credit">{credit(L, lang)}</p></article>
{f'<div class="sub">{"".join(card(p, lang, rub=True, dek=False, sizes="(min-width:72rem) 19rem, (min-width:36rem) 30vw, 7rem") for p in sub)}</div>' if sub else ""}</div>"""
    second = "".join(f'<article class="s">{ph(p, art_path(p, lang), "(min-width:72rem) 18rem, (min-width:48rem) 35vw, 100vw") if i == 0 else ""}{kick(p, "", lang)}'
                     f'<h3><a href="{art_path(p, lang)}">{esc(p["title"])}</a></h3><p class="dek">{esc(p["description"])}</p></article>' for i, p in enumerate(sec))
    second = f'<div class="second">{second}</div>' if sec else ""
    mini = "".join(f'<li><a href="{art_path(c, lang)}">{parties(c, lang)}</a><span class="st">{esc(short(c.get("stadiya", "")))}</span></li>' for c in col)
    k_name, k_file = R["konflikty"][0], R["konflikty"][1]
    cases_box = f'<div>{sect_head(k_name, k_file)}<ul class="mini">{mini}</ul><a class="more" href="{k_file}">{"All case files" if en else "Все разборы"}</a></div>' if col else ""
    dates = upcoming(posts, lang)
    column = f'<aside class="col">{cases_box}{dates}</aside>' if cases_box or dates else ""
    out = [f'<section class="top{"" if column else " no-col"}">{lead}{second}{column}</section>']

    all_l = "All stories" if en else "Все материалы"
    eco = take([p for p in posts if p["rubric"] == "ekonomika"], 5)
    if eco:
        big, rest = eco[0], eco[1:]
        href = art_path(big, lang)
        fb = (f'<article class="f-big">{ph(big, href, "(min-width:78rem) 37rem, (min-width:36rem) 92vw, 100vw")}{kick(big, "", lang, False)}'
              f'<h3><a href="{href}">{esc(big["title"])}</a></h3><p class="dek">{esc(big["description"])}</p></article>')
        out.append(f'<section class="sect">{sect_head(R["ekonomika"][0], R["ekonomika"][1], all_l)}<div class="feat">{fb}{"".join(card(p, lang, dek=False) for p in rest)}</div></section>')
    more_cases = take(cases, 4)
    if more_cases:
        cls = {1: "cards solo", 2: "cards duo"}.get(len(more_cases), "cards")
        out.append(f'<section class="sect">{sect_head(k_name, k_file, "All case files" if en else "Все разборы")}<div class="{cls}">{"".join(card(p, lang) for p in more_cases)}</div></section>')
    cols = []
    for k in ("politika", "mir", "ukraina"):
        items = take([p for p in posts if p["rubric"] == k], 3)
        if items:
            heads = "".join(f'<li>{kick(p, "", lang, False)}<a href="{art_path(p, lang)}">{esc(p["title"])}</a></li>' for p in items[1:])
            cols.append(f'<div>{sect_head(R[k][0], R[k][1])}{card(items[0], lang)}{f"<ul class=heads>{heads}</ul>" if heads else ""}</div>')
    rest = take(posts, 8)
    if rest:
        li = "".join(f'<li>{kick(p, "", lang)}<a href="{art_path(p, lang)}">{esc(p["title"])}</a></li>' for p in rest)
        cols.append(f'<div class="rest">{sect_head("More stories" if en else "Ещё материалы")}<ul class="heads">{li}</ul></div>')
    if cols:
        out.append(f'<section class="sect trio">{"".join(cols)}</section>')
    return "\n".join(out)


def latest_rail(posts, exclude, lang="ru", up="", n=5, title=None):
    items = [p for p in posts if p["slug"] not in exclude][:n]
    if not items:
        return ""
    li = "".join(f'<li>{ph(p, up + art_path(p, lang), "6rem")}<div><a class="t" href="{up}{art_path(p, lang)}">{esc(p["title"])}</a>{kick(p, up, lang)}</div></li>' for p in items)
    return f'<section class="latest">{sect_head(title or ("Latest" if lang == "en" else "Последние материалы"))}<ol>{li}</ol></section>'


def rubric_main(items, posts, lang="ru"):
    en = lang == "en"
    if not items:
        return f'<p class="note">{"English coverage in this section is coming soon." if en else "Материалы в этой рубрике появятся скоро."}</p>'

    def head(p):
        return parties(p, lang) if is_case(p) else esc(p["title"])

    def extra(p):
        if not is_case(p):
            return f'<p class="dek">{esc(p["description"])}</p>'
        st = ("At stake", "Status") if en else ("Цена вопроса", "Стадия")
        md_ = "".join(f"<span><b>{k}:</b> {esc(short(p.get(f), 120))}</span>" for k, f in zip(st, ("cena", "stadiya")) if p.get(f))
        return f'<p class="dek">{esc(p["title"])}</p><p class="mdock">{md_}</p>'

    f, rest = items[0], items[1:]
    lead = (f'<article class="r-lead">{ph(f, art_path(f, lang), "(min-width:78rem) 32rem, (min-width:48rem) 55vw, 100vw", eager=True)}'
            f'<div>{kick(f, "", lang, False)}<h2><a href="{art_path(f, lang)}">{head(f)}</a></h2>{extra(f)}</div></article>')
    rows = "".join(f'<article class="row"><div>{kick(p, "", lang, False)}<h3><a href="{art_path(p, lang)}">{head(p)}</a></h3>{extra(p)}</div>'
                   f'{ph(p, art_path(p, lang), "(min-width:48rem) 12.5rem, 7rem")}</article>' for p in rest)
    rail = latest_rail([p for p in posts if p["rubric"] != items[0]["rubric"]], set(), lang, n=6,
                       title="Elsewhere" if en else "Другие рубрики")
    return f'<div class="with-rail"><div>{lead}{rows}</div><aside class="rail">{rail}</aside></div>'


def article_main(p, posts, path, lang="ru", ru_link=""):
    """Страница материала: шапка, фото, текст и правая колонка (карточка дела и последние материалы)."""
    en = lang == "en"
    url = url_of(path)
    upd = f'<span>{"Updated" if en else "Обновлено"} <time datetime="{p["updated"].isoformat()}">{ru_date(p["updated"], lang)}, {p["updated"]:%H:%M}</time></span>' if p["updated"] != p["date"] else ""
    by = "Kurs Media editorial team" if en else f"Редакция «{BRAND}»"
    share = (f'<div class="share"><a href="https://t.me/share/url?url={quote(url, safe="")}&amp;text={quote(p["title"], safe="")}" rel="noopener" target="_blank">{"Telegram" if en else "Телеграм"}</a>'
             f'<a href="https://vk.com/share.php?url={quote(url, safe="")}" rel="noopener" target="_blank">{"VK" if en else "ВКонтакте"}</a>'
             f'<button type="button" data-copy="{"Link copied" if en else "Ссылка скопирована"}">{"Copy link" if en else "Скопировать ссылку"}</button></div>')
    head = f"""<header class="story-head"><div class="kick">{rub_link(p, '../', lang)}</div><h1>{esc(p['title'])}</h1><p class="dek">{esc(p['description'])}</p></header>
<div class="byline"><div class="when"><span class="by">{by}</span><time datetime="{p['date'].isoformat()}">{ru_date(p['date'], lang)}, {p['date']:%H:%M}</time>{upd}</div>{share}</div>"""
    hero = (f'<figure class="hero"><div class="ph">{img(p, "(min-width:78rem) 46rem, (min-width:62rem) 62vw, 100vw", eager=True)}</div>'
            f'<figcaption>{esc(p.get("image_caption", ""))}. <span class="cr">{credit(p, lang)}</span></figcaption></figure>') if p.get("image") else ""
    paras = list(p["paras"])
    if p.get("graphic"):
        g = (f'<figure class="graphic"><img src="/img/{p["graphic"]}" width="1440" height="900" alt="{esc(p.get("graphic_alt", ""))}" loading="lazy">'
             f'<figcaption>{"Graphic" if en else "Инфографика"}: «{BRAND}»</figcaption></figure>')
        paras.insert(min(2, len(paras)), g)
    src = "".join(f'<li><a href="{esc(u)}" rel="noopener">{esc(t)}</a></li>' for t, u in p["sources"])
    note = '<p class="note" style="margin:0 0 .6rem">Most sources are in Russian.</p>' if en else ""
    if en:
        sign = f'<p class="sign"><strong>Kurs Media editorial team.</strong> Corrections and statements from the parties: <a href="mailto:{EMAIL}">{EMAIL}</a>.{ru_link}</p>'
    else:
        sign = (f'<p class="sign"><strong>Редакция «{SITE_NAME}»</strong>. Канал в телеграме: <a href="{CHANNEL}" rel="noopener">t.me/economskepticism</a>. '
                f'Позиции сторон и исправления: <a href="mailto:{EMAIL}">{EMAIL}</a>. По вопросам коммуникаций в корпоративных спорах: <a href="../o-proekte.html">как связаться</a>.</p>')
    file = f'<div class="file box"><h2>{"Case file" if en else "Карточка дела"}</h2>{docket(p, lang)}</div>' if p["rubric"] == "konflikty" else ""
    related = [q for q in posts if q["rubric"] == p["rubric"] and q["slug"] != p["slug"]][:4]
    related += [q for q in posts if q["slug"] != p["slug"] and q not in related][:4 - len(related)]
    rail = latest_rail(posts, {p["slug"], *[q["slug"] for q in related]}, lang, "../")
    rel = "".join(card(q, lang, "../", rub=True) for q in related)
    return f"""<article>{head}
<div class="story-grid{' has-file' if file else ''}">{hero}{file}<div class="body">
{chr(10).join(paras)}
<section class="sources"><h2>{"Sources" if en else "Источники"}</h2>{note}<ul>{src}</ul></section>
{sign}
</div><aside class="rail">{rail}</aside></div></article>
<section class="related">{sect_head("More on this topic" if en else "Ещё по теме")}<div class="cards">{rel}</div></section>"""


def news_ld(p, path, lang="ru"):
    name, home = (EN_NAME, SITE_URL + "/en/") if lang == "en" else (SITE_NAME, SITE_URL + "/")
    return {"@context": "https://schema.org", "@type": "NewsArticle", "headline": p["title"], "description": p["description"],
            "datePublished": p["date"].isoformat() + "+03:00", "dateModified": p["updated"].isoformat() + "+03:00", "inLanguage": lang,
            "author": {"@type": "Organization", "name": name, "url": home}, "publisher": {"@type": "Organization", "name": name, "url": SITE_URL + "/"},
            "mainEntityOfPage": url_of(path), "image": f"{SITE_URL}/img/{p.get('image', 'og.png')}"}


def og_of(p):
    return f"img/{p['image']}" if p.get("image") else "img/og.png"


def build():
    posts = load()
    posts_en = load(SRC_EN) if SRC_EN.exists() else []
    check_photos(posts, posts_en)
    en_of = {p["ru"]: p for p in posts_en if p.get("ru")}   # русский слаг → английский материал
    if OUT.exists():
        shutil.rmtree(OUT)
    shutil.copytree(STATIC, OUT)
    cases = [p for p in posts if is_case(p)]
    pair = lambda ru, en: [("ru", url_of(ru)), ("en", url_of(en)), ("x-default", url_of(ru))]
    ld_tag = lambda d: f'\n<script type="application/ld+json">{json.dumps(d, ensure_ascii=False)}</script>'

    # главная
    ld = {"@context": "https://schema.org", "@type": "WebSite", "name": SITE_NAME, "url": SITE_URL + "/", "description": TAGLINE, "inLanguage": "ru"}
    head, body = page("index.html", f"{SITE_NAME} — {MOTTO.lower()}: корпоративные споры, экономика и политика", TAGLINE, front(posts),
                      alts=pair("index.html", "en/index.html"), og_image=og_of(posts[0]), extra_head=ld_tag(ld))
    write("index.html", head, body)
    index_parts = (head, body)

    # рубрики
    for key, (name, fname, rdesc) in RUBRICS.items():
        items = [p for p in posts if p["rubric"] == key]
        main = f'<div class="pagehead"><h1>{name}</h1><p>{rdesc}</p></div>{rubric_main(items, posts)}'
        en_f = "en/" + RUBRICS_EN[key][1]
        write(fname, *page(fname, f"{name} — {SITE_NAME}", rdesc, main, current=key, alts=pair(fname, en_f), switch=en_f,
                           og_image=og_of(items[0]) if items else "img/og.png"))

    # материалы
    for p in posts:
        path = f"materialy/{p['slug']}.html"
        en = en_of.get(p["slug"])
        en_path = f"en/{art_path(en, 'en')}" if en else None
        write(path, *page(path, f"{p['seo_title']} — {SITE_NAME}", p["description"], article_main(p, posts, path), up="../", current=p["rubric"],
                          og_image=og_of(p), og_type="article", alts=pair(path, en_path) if en else None, switch=f"../{en_path}" if en else None,
                          extra_head=ld_tag(news_ld(p, path))))

    # о проекте
    main = f"""<div class="pagehead"><h1>О проекте</h1><p>Редакция, правила и контакты.</p></div><div class="prose">
<p>«{SITE_NAME}» — издание о политике, экономике и корпоративных спорах. У издания есть <a href="{CHANNEL}" rel="noopener">телеграм-канал</a>, он внесён в реестр Роскомнадзора.</p>
<h2>Как мы пишем о конфликтах</h2>
<p>В рубрике «Конфликты» разбираются публичные корпоративные споры: иски, арбитражи, разбирательства компаний с регуляторами и друг с другом. Правила для всех разборов одни.</p>
<p>Позиции сторон излагаются одинаково подробно и по их собственным заявлениям. Решения судов приводятся с номером дела, инстанцией и статусом: вступило ли решение в силу, обжалуется ли оно. О том, кто прав по существу, мы не судим: это дело суда. Мы описываем публичные действия сторон: иски, заявления, раскрытия.</p>
<p>Разборы обновляются, когда в деле появляется новое решение или заявление. Если ваша компания участвует в споре и её позиция изложена неточно, напишите на {EMAIL}. Мы сверим текст с документами, исправим и укажем дату правки.</p>
<p>Разборы не публикуются, не правятся и не снимаются за плату.</p>
<h2>Фотографии</h2>
<p>Мы используем снимки по свободным лицензиям: из Wikimedia Commons, с сайтов Kremlin.ru и Белого дома и из других открытых источников. Под каждым фото указаны автор и лицензия. Если вы автор снимка и видите ошибку в подписи, напишите на {EMAIL}.</p>
<h2>Консультации</h2>
<p>Редакция консультирует компании и акционеров по публичной коммуникации в корпоративных спорах и по защите репутации: позиция на время разбирательства, работа с прессой, ответ на информационные кампании.</p>
<h2>Связаться</h2>
<p>Редакция, запросы и позиции сторон, исправления:</p>
<p class="contact"><a href="mailto:{EMAIL}">{EMAIL}</a></p>
<p>Консультации и реклама в канале, телеграм:</p>
<p class="contact">{CONTACT}</p>
</div>"""
    write("o-proekte.html", *page("o-proekte.html", f"О проекте — {SITE_NAME}", "Кто пишет «Курс дела Медиа», правила рубрики о корпоративных конфликтах и контакты.", main, current="about",
                                  alts=pair("o-proekte.html", "en/about.html"), switch="en/about.html"))

    en_urls = build_en(posts_en, {p["slug"]: p for p in posts}, pair)

    # 404
    write("404.html", *page("404.html", f"Страница не найдена — {SITE_NAME}", "Такой страницы нет.",
                            '<div class="pagehead"><h1>Такой страницы нет</h1><p>Возможно, адрес изменился.</p></div><p class="note"><a href="/index.html">Перейти на главную</a></p>', up="/"))

    # служебные файлы
    urls = ["", *[f for _, f, _ in RUBRICS.values()], "o-proekte.html", *[f"materialy/{p['slug']}.html" for p in posts], *en_urls]
    last = {f"materialy/{p['slug']}.html": p["updated"].date().isoformat() for p in posts}
    last.update({f"en/articles/{p['slug']}.html": p["updated"].date().isoformat() for p in posts_en})
    pics = {f"materialy/{p['slug']}.html": p for p in posts if p.get("image")}
    pics.update({f"en/articles/{p['slug']}.html": p for p in posts_en if p.get("image")})
    today = max(p["updated"] for p in posts).date().isoformat()
    sm = lambda u: (f"<image:image><image:loc>{SITE_URL}/img/{pics[u]['image']}</image:loc></image:image>" if u in pics else "")
    (OUT / "sitemap.xml").write_text('<?xml version="1.0" encoding="UTF-8"?>\n<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9" xmlns:image="http://www.google.com/schemas/sitemap-image/1.1">\n' +
        "".join(f"<url><loc>{SITE_URL}/{u}</loc><lastmod>{last.get(u, today)}</lastmod>{sm(u)}</url>\n" for u in urls) + "</urlset>\n", encoding="utf-8")
    (OUT / "robots.txt").write_text(f"User-agent: *\nAllow: /\n\nSitemap: {SITE_URL}/sitemap.xml\n", encoding="utf-8")
    (OUT / "rss.xml").write_text(rss_feed(posts, SITE_NAME, SITE_URL + "/", TAGLINE, "ru", lambda p: f"{SITE_URL}/materialy/{p['slug']}.html"), encoding="utf-8")
    llms = [f"# {SITE_NAME}", "", f"> {TAGLINE} Отдельная рубрика посвящена публичным корпоративным конфликтам: стороны, позиции, решения судов.", "",
            "## Конфликты", *[f"- [{p['a']} против {p.get('b_rod', p['b'])}]({SITE_URL}/materialy/{p['slug']}.html): {p['description']}" for p in cases], "",
            "## Материалы", *[f"- [{p['title']}]({SITE_URL}/materialy/{p['slug']}.html): {p['description']}" for p in posts if not is_case(p)], "",
            "## О проекте", f"- [Правила и контакты]({SITE_URL}/o-proekte.html)", ""]
    (OUT / "llms.txt").write_text("\n".join(llms), encoding="utf-8")
    (OUT / ".nojekyll").write_text("", encoding="utf-8")
    (OUT / "CNAME").write_text(SITE_URL.split("//", 1)[1] + "\n", encoding="utf-8")   # домен для GitHub Pages
    (OUT / "favicon.svg").write_text('<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 64 64"><rect width="64" height="64" rx="12" fill="#141922"/><rect x="12" y="46" width="40" height="4" rx="2" fill="#CCFF33"/><text x="32" y="39" text-anchor="middle" font-family="Georgia,serif" font-weight="700" font-size="30" fill="#F3F4EF">КД</text></svg>', encoding="utf-8")

    # главная без обёртки документа: для предпросмотра
    pv = re.sub(r"<title>.*?</title>", f"<title>{SITE_NAME}</title>", index_parts[0], count=1)
    (ROOT / "preview_index.html").write_text(pv + "\n" + index_parts[1] + "\n", encoding="utf-8")
    print(f"Собрано: {len(posts)} материалов, {len(posts_en)} на английском, {len(list(OUT.rglob('*.html')))} страниц → {OUT}")


def rss_feed(posts, title, link, desc, lang, url):
    def enc(p):
        if not p.get("image"):
            return ""
        f = STATIC / "img" / p["image"]
        return f'<enclosure url="{SITE_URL}/img/{p["image"]}" length="{f.stat().st_size}" type="image/jpeg"/>'
    items = "".join(f"<item><title>{esc(p['title'])}</title><link>{url(p)}</link><guid>{url(p)}</guid>"
                    f"<pubDate>{p['date'].strftime('%a, %d %b %Y %H:%M:%S')} +0300</pubDate><description>{esc(p['description'])}</description>{enc(p)}</item>\n" for p in posts[:30])
    return (f'<?xml version="1.0" encoding="UTF-8"?>\n<rss version="2.0"><channel><title>{esc(title)}</title><link>{link}</link>'
            f"<description>{esc(desc)}</description><language>{lang}</language>\n{items}</channel></rss>\n")


def build_en(posts, ru_by_slug, pair):
    """Английский раздел /en/. Возвращает список путей для sitemap."""
    urls = []
    ld_tag = lambda d: f'\n<script type="application/ld+json">{json.dumps(d)}</script>'

    def put(path, title, desc, main, up, alts=None, switch=None, **kw):
        write(path, *page(path, title, desc, main, up=up, lang="en", alts=alts, switch=switch, **kw), lang="en")
        urls.append(path[:-len("index.html")] if path.endswith("index.html") else path)

    # главная
    main = front(posts, "en") if posts else '<p class="note">English coverage starts soon.</p>'
    ld = {"@context": "https://schema.org", "@type": "WebSite", "name": EN_NAME, "url": SITE_URL + "/en/", "description": EN_TAGLINE, "inLanguage": "en"}
    put("en/index.html", f"{EN_NAME} — Russian business conflicts, money and power", EN_TAGLINE, main, "../",
        alts=pair("index.html", "en/index.html"), switch="../index.html", og_image=og_of(posts[0]) if posts else "img/og.png", extra_head=ld_tag(ld))

    # рубрики
    for key, (name, fname, rdesc) in RUBRICS_EN.items():
        items = [p for p in posts if p["rubric"] == key]
        main = f'<div class="pagehead"><h1>{name}</h1><p>{rdesc}</p></div>{rubric_main(items, posts, "en")}'
        ru_f = RUBRICS[key][1]
        put(f"en/{fname}", f"{name} — {EN_NAME}", rdesc, main, "../", current=key, alts=pair(ru_f, f"en/{fname}"), switch=f"../{ru_f}")

    # материалы
    for p in posts:
        path = f"en/{art_path(p, 'en')}"
        ru = ru_by_slug.get(p.get("ru"))
        ru_link = f' <a href="../../materialy/{ru["slug"]}.html" lang="ru">Read in Russian</a>.' if ru else ""
        ru_path = f"materialy/{ru['slug']}.html" if ru else None
        put(path, f"{p['seo_title']} — {EN_NAME}", p["description"], article_main(p, posts, path, "en", ru_link), "../../", current=p["rubric"],
            og_image=og_of(p), og_type="article", alts=pair(ru_path, path) if ru else None, switch=f"../../{ru_path}" if ru else None,
            extra_head=ld_tag(news_ld(p, path, "en")))

    # о проекте
    main = f"""<div class="pagehead"><h1>About</h1><p>Who we are, how we cover disputes, how to reach us.</p></div><div class="prose">
<p>Kurs Media is an independent Russian outlet covering business, money and power in Russia. The English edition focuses on corporate conflicts: lawsuits, arbitration and disputes between companies, shareholders and regulators. The Russian edition is at <a href="../index.html" lang="ru">kursmedia.com</a>; its Telegram channel <a href="{CHANNEL}" rel="noopener">«Курс дела»</a> is registered with Russia's media regulator.</p>
<h2>How we cover disputes</h2>
<p>We set out each party's position in equal detail, based on their own statements and filings. Court rulings are cited with the court, case number and status — whether a ruling is final or under appeal. We do not judge who is right on the merits; that is for the courts. Russian legal terms are explained for international readers, and ruble amounts are given alongside approximate dollar figures where useful.</p>
<p>Case files are updated when a new ruling or statement appears. If your company is a party to a dispute and its position is stated inaccurately, write to {EMAIL}. We will check the text against the documents, correct it and note the date of the correction.</p>
<p>Coverage is never published, edited or removed for payment.</p>
<h2>Photos</h2>
<p>We use photos under free licences: from Wikimedia Commons, Kremlin.ru, the White House and other open sources. The author and licence are credited under every photo. If you took a photo and the credit is wrong, write to {EMAIL}.</p>
<h2>Contact</h2>
<p>Editorial, statements from the parties, corrections:</p>
<p class="contact"><a href="mailto:{EMAIL}">{EMAIL}</a></p>
</div>"""
    put("en/about.html", f"About — {EN_NAME}", "Who writes Kurs Media, how we cover Russian corporate disputes, and how to contact the editors.", main, "../",
        current="about", alts=pair("o-proekte.html", "en/about.html"), switch="../o-proekte.html")

    (OUT / "en" / "rss.xml").write_text(rss_feed(posts, EN_NAME, SITE_URL + "/en/", EN_TAGLINE, "en", lambda p: url_of("en/" + art_path(p, "en"))), encoding="utf-8")
    return urls


if __name__ == "__main__":
    build()
