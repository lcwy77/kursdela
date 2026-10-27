#!/usr/bin/env python3
"""Обложки «Курса дела»: превью ссылок (og, 1200×630) и картинки для постов в канале (post, 1600×1000).

Шаблоны:
  news    фото и заголовок        python3 tools/cover.py news --slug sulejmanov-delo-zaversheno
  case    спор: стороны, на кону  python3 tools/cover.py case --slug rosnano-protiv-chubaysa
  quote   цитата и фото           python3 tools/cover.py quote --text "Коррупция во время войны — это яд" --who "Виталий Кличко, мэр Киева" --photo static/img/klichko-korrupciya-yad.jpg --rubric Украина
  number  крупная цифра           python3 tools/cover.py number --num "$50" --text "цена нефти, от которой бюджет считает расходы с 2027 года" --source "Минфин" --rubric Экономика
  flash   срочно, без фото        python3 tools/cover.py flash --title "Заголовок"
  site    превью для всех материалов сайта → static/img/og/ (спор — шаблон case, остальное — news)

Общие ключи: --title --rubric --photo --credit --focus "50% 35%" --format og|post|both (по умолчанию both)
             --lang ru|en --name имя-файла --out папка (по умолчанию covers/)
С --slug поля берутся из материала: content/<slug>.md, с --lang en — content_en/<slug>.md.
Для спора можно задать в материале cena_short: коротко, что на кону («почти 20 млрд рублей»).
"""
import argparse, base64, html, sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))
import build  # noqa: E402  (материалы, рубрики, наборы символов шрифтов)

FONTS = ROOT / "static" / "fonts"
SIZES = {"og": (1200, 630), "post": (1600, 1000)}
INK, LIME, PAPER, MUTED = "#141922", "#CCFF33", "#F3F4EF", "#9AA2AF"
L = {"ru": {"np": build.BRAND, "vs": "против", "stake": "На кону", "photo": "Фото", "flash": "Срочно", "site": "kursmedia.com"},
     "en": {"np": build.EN_NAME, "vs": "v.", "stake": "At stake", "photo": "Photo", "flash": "Breaking", "site": "kursmedia.com/en"}}


def esc(s):
    return html.escape(str(s or ""), quote=True)


def font_css():
    out = []
    for fam, f, w, s in build.FACES:
        for sub, rng in (("cyrillic", build.CYR), ("latin", build.LAT)):
            b64 = base64.b64encode((FONTS / f"{f.format(sub)}.woff2").read_bytes()).decode()
            out.append(f"@font-face{{font-family:'{fam}';src:url(data:font/woff2;base64,{b64}) format('woff2');font-weight:{w};font-style:{s};unicode-range:{rng}}}")
    return "".join(out)


def data_uri(path):
    p = Path(path)
    mime = "image/png" if p.suffix.lower() == ".png" else "image/jpeg"
    return f"data:{mime};base64,{base64.b64encode(p.read_bytes()).decode()}"


CSS = """
*{box-sizing:border-box;margin:0;padding:0}
html,body{width:100vw;height:100vh;overflow:hidden;background:@ink}
body{font-family:'Golos Text',Arial,sans-serif;-webkit-font-smoothing:antialiased;text-rendering:optimizeLegibility}
.c{position:relative;width:100vw;height:100vh;overflow:hidden;color:@paper;background:@ink}
.np{font:700 2.7vw/1 'Old Standard TT',Georgia,serif;letter-spacing:-.005em;white-space:nowrap}
.site{font:500 1.05vw/1 'Golos Text';color:@muted;letter-spacing:.01em}
.rub{font:600 1.45vw/1 'Golos Text';color:@lime}
.ph{background-size:cover;background-repeat:no-repeat}
.cr{position:absolute;font:400 .9vw/1.2 'Golos Text';color:rgba(243,244,239,.92);background:rgba(20,25,34,.62);padding:.35vw .65vw;border-radius:.3vw;max-width:46vw}
h1{font-family:'Literata',Georgia,serif;font-weight:700;letter-spacing:-.012em;line-height:1.09;text-wrap:balance}
/* news: фото сверху, тёмная плашка с заголовком снизу */
.news{display:flex;flex-direction:column}
.news .ph{flex:1 1 auto;min-height:0}
.news .panel{flex:0 0 auto;border-top:.42vw solid @lime;padding:2.2vw 4vw 2.9vw}
.news .row{display:flex;justify-content:space-between;align-items:center;margin-bottom:1.3vw}
.news .row .brand{display:flex;align-items:baseline;gap:1.1vw}
.news h1{font-size:4.5vw}
/* case: слева стороны спора и что на кону, справа фото */
.case{display:grid;grid-template-columns:48% 52%}
.case .panel{display:flex;flex-direction:column;padding:3.4vw 3.4vw 3vw;border-right:.42vw solid @lime;min-height:0}
.case h1{font-size:4.9vw;line-height:1.04;margin-top:1.8vw}
.case h1 span{display:block}
.case h1 .vs{font:italic 400 .6em/1.35 'Literata';color:@lime;margin:.15em 0}
.case .low{margin-top:auto;padding-top:1.6vw}
.case .lbl{font:500 1.15vw/1 'Golos Text';color:@muted;margin-bottom:.55vw}
.case .val{font:700 2.9vw/1.1 'Literata';color:@lime}
.case .stage{font:400 1.3vw/1.4 'Golos Text';color:#C9CED6;margin-top:1.1vw}
.case .brand{display:flex;align-items:baseline;gap:1.1vw;margin-top:1.8vw}
/* quote: цитата слева, фото справа */
.quote{display:grid;grid-template-columns:58% 42%}
.quote .panel{display:flex;flex-direction:column;padding:3.4vw 3.6vw 3vw;border-right:.42vw solid @lime;min-height:0}
.quote blockquote{font:italic 500 4.4vw/1.18 'Literata';letter-spacing:-.01em;text-wrap:balance;margin:auto 0;padding:2vw 0}
.quote .q{color:@lime;font-style:normal;font-weight:700}
.quote .who{font:600 1.55vw/1.3 'Golos Text';color:@lime}
.quote .brand{display:flex;align-items:baseline;gap:1.1vw;margin-top:1.6vw}
/* number: лаймовый фон, крупная цифра */
.number{background:@lime;color:@ink;display:flex;flex-direction:column;padding:3.4vw 4.2vw 3vw}
.number .row{display:flex;justify-content:space-between;align-items:center}
.number .rub,.number .site{color:@ink}
.number .mid{margin:auto 0}
.number .num{font:800 16vw/.9 'Literata';letter-spacing:-.035em}
.number .txt{font:500 2.9vw/1.22 'Literata';max-width:74vw;margin-top:1.8vw;text-wrap:balance}
.number .src{font:500 1.15vw/1.3 'Golos Text';opacity:.78}
/* flash: срочная новость без фото */
.flash{display:flex;flex-direction:column;padding:3.4vw 4.2vw 3vw}
.flash .row{display:flex;justify-content:space-between;align-items:center}
.flash .lbl{font:700 1.5vw/1 'Golos Text';color:@ink;background:@lime;padding:.6vw 1vw;border-radius:.3vw}
.flash h1{font-size:6vw;margin:auto 0}
.flash .foot{display:flex;justify-content:space-between;font:500 1.2vw/1 'Golos Text';color:@muted}
""".replace("@ink", INK).replace("@lime", LIME).replace("@paper", PAPER).replace("@muted", MUTED)

FIT = """
<script>
document.fonts.ready.then(() => {
  const c = document.querySelector('.c'), el = document.querySelector('[data-fit]'), box = document.querySelector('[data-box]') || c;
  const limit = parseFloat(c.dataset.limit || '0');
  const over = () => limit ? box.offsetHeight > innerHeight * limit : box.scrollHeight > box.clientHeight + 1;
  let s = parseFloat(getComputedStyle(el).fontSize);
  while (over() && s > 12) { s -= 1; el.style.fontSize = s + 'px'; }
  window.__done = true;
});
</script>"""


def credit_line(d, lang):
    if not d.get("credit"):
        return ""
    lic = d.get("license", "")
    lic = "" if lic in ("", "PD") else f", {lic}"
    return f"{L[lang]['photo']}: {d['credit']}{lic}"


def brand(lang):
    return f'<span class="np">{esc(L[lang]["np"])}</span><span class="site">{L[lang]["site"]}</span>'


def render_html(kind, d, lang):
    t = L[lang]
    ph = f'<div class="ph" style="background-image:url({data_uri(d["photo"])});background-position:{d.get("focus") or "50% 50%"}"></div>' if d.get("photo") else ""
    cr = credit_line(d, lang)
    if kind == "news":
        body = (f'<div class="c news" data-limit="0.5">{ph}<div class="panel" data-box><div class="row"><span class="rub">{esc(d.get("rubric"))}</span>'
                f'<span class="brand">{brand(lang)}</span></div><h1 data-fit>{esc(d["title"])}</h1></div>'
                + (f'<span class="cr" style="right:1.1vw;top:1.1vw">{esc(cr)}</span>' if cr else "") + "</div>")
    elif kind == "case":
        stake = f'<div class="lbl">{t["stake"]}</div><div class="val">{esc(d["stake"])}</div>' if d.get("stake") else ""
        stage = f'<div class="stage">{esc(d["stage"])}</div>' if d.get("stage") else ""
        body = (f'<div class="c case"><div class="panel" data-box><span class="rub">{esc(d.get("rubric"))}</span>'
                f'<h1 data-fit><span>{esc(d["a"])}</span><span class="vs">{t["vs"]}</span><span>{esc(d["b"])}</span></h1>'
                f'<div class="low">{stake}{stage}<div class="brand">{brand(lang)}</div></div></div>{ph}'
                + (f'<span class="cr" style="right:1.1vw;bottom:1.1vw">{esc(cr)}</span>' if cr else "") + "</div>")
    elif kind == "quote":
        body = (f'<div class="c quote"><div class="panel" data-box><span class="rub">{esc(d.get("rubric"))}</span>'
                f'<blockquote data-fit><span class="q">«</span>{esc(d["text"])}<span class="q">»</span></blockquote><div class="who">{esc(d.get("who"))}</div><div class="brand">{brand(lang)}</div></div>{ph}'
                + (f'<span class="cr" style="right:1.1vw;bottom:1.1vw">{esc(cr)}</span>' if cr else "") + "</div>")
    elif kind == "number":
        src = f'<div class="src">{esc(d["source"])}</div>' if d.get("source") else ""
        body = (f'<div class="c number"><div class="row"><span class="rub">{esc(d.get("rubric"))}</span><span class="brand" style="display:flex;align-items:baseline;gap:1.1vw">{brand(lang)}</span></div>'
                f'<div class="mid"><div class="num" data-fit>{esc(d["num"])}</div><div class="txt">{esc(d.get("text"))}</div></div>{src}</div>')
    elif kind == "flash":
        body = (f'<div class="c flash"><div class="row"><span class="lbl">{t["flash"]}</span><span class="brand" style="display:flex;align-items:baseline;gap:1.1vw">{brand(lang)}</span></div>'
                f'<h1 data-fit>{esc(d["title"])}</h1><div class="foot"><span>{esc(d.get("when"))}</span><span>{esc(d.get("rubric"))}</span></div></div>')
    else:
        raise SystemExit(f"Нет шаблона {kind}")
    return f'<!doctype html><html lang="{lang}"><head><meta charset="utf-8"><style>{font_css()}{CSS}</style></head><body>{body}{FIT}</body></html>'


class Renderer:
    def __enter__(self):
        from playwright.sync_api import sync_playwright
        self.pw = sync_playwright().start()
        self.br = self.pw.chromium.launch()
        return self

    def shot(self, html_text, size, out):
        w, h = SIZES[size]
        pg = self.br.new_page(viewport={"width": w, "height": h})
        pg.set_content(html_text)
        pg.wait_for_function("window.__done === true", timeout=20000)
        out.parent.mkdir(parents=True, exist_ok=True)
        pg.screenshot(path=str(out), type="jpeg", quality=90)
        pg.close()
        return out

    def __exit__(self, *a):
        self.br.close()
        self.pw.stop()


def from_post(p, lang):
    """Поля обложки из материала сайта."""
    R = build.RUBRICS_EN if lang == "en" else build.RUBRICS
    d = {"title": p["title"], "rubric": R[p["rubric"]][0], "credit": p.get("image_credit"), "license": p.get("image_license"),
         "focus": p.get("image_focus"), "when": f"{build.ru_date(p['date'], lang)}, {p['date']:%H:%M}"}
    if p.get("image"):
        d["photo"] = ROOT / "static" / "img" / p["image"]
    if build.is_case(p):
        d.update(a=p["a"], b=p["b"] if lang == "en" else p.get("b_rod", p["b"]), stake=p.get("cena_short"), stage=build.short(p.get("stadiya", ""), 95))
        # «Анатолия Чубайса» — после «против» нужен родительный падеж, он и есть в b_rod
    return d


def load_post(slug, lang):
    posts = build.load(build.SRC_EN if lang == "en" else build.SRC)
    for p in posts:
        if p["slug"] == slug:
            return p
    raise SystemExit(f"Материал {slug} не найден")


def site_covers():
    """og-превью для всех материалов: static/img/og/<slug>.jpg и static/img/og/en-<slug>.jpg."""
    out_dir = ROOT / "static" / "img" / "og"
    n = 0
    with Renderer() as r:
        for lang, src, pre in (("ru", build.SRC, ""), ("en", build.SRC_EN, "en-")):
            for p in build.load(src):
                if not p.get("image"):
                    continue
                kind = "case" if build.is_case(p) else "news"
                r.shot(render_html(kind, from_post(p, lang), lang), "og", out_dir / f"{pre}{p['slug']}.jpg")
                n += 1
    print(f"Готово превью: {n} → {out_dir}")


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("kind", choices=["news", "case", "quote", "number", "flash", "site"])
    for k in ("slug", "title", "rubric", "photo", "credit", "license", "focus", "text", "who", "num", "source", "a", "b", "stake", "stage", "when", "name"):
        ap.add_argument(f"--{k}")
    ap.add_argument("--format", default="both", choices=["og", "post", "both"])
    ap.add_argument("--lang", default="ru", choices=["ru", "en"])
    ap.add_argument("--out", default=str(ROOT / "covers"))
    a = ap.parse_args()
    if a.kind == "site":
        return site_covers()
    d = from_post(load_post(a.slug, a.lang), a.lang) if a.slug else {}
    for k in ("title", "rubric", "photo", "credit", "license", "focus", "text", "who", "num", "source", "a", "b", "stake", "stage", "when"):
        if getattr(a, k):
            d[k] = getattr(a, k)
    name = a.name or a.slug or a.kind
    sizes = ["og", "post"] if a.format == "both" else [a.format]
    with Renderer() as r:
        for s in sizes:
            print(r.shot(render_html(a.kind, d, a.lang), s, Path(a.out) / f"{name}-{s}.jpg"))


if __name__ == "__main__":
    main()
