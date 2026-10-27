#!/usr/bin/env python3
"""Готовит фото к публикации: кадр 3:2 вокруг точки интереса, sRGB, три размера.

  python3 tools/photo.py исходник.jpg слаг [fx fy]

fx, fy — точка интереса в долях кадра (0.5 0.5 — центр). Результат в static/img:
  слаг.jpg (1600×1067), слаг-800.jpg, слаг-400.jpg.
В материале: image: слаг.jpg, плюс image_alt, image_caption, image_credit, image_link.
"""
import io, sys
from pathlib import Path
from PIL import Image, ImageCms, ImageFilter, ImageOps

OUT = Path(__file__).resolve().parent.parent / "static" / "img"
SIZES = {"": 1600, "-800": 800, "-400": 400}
RATIO = 3 / 2


def to_srgb(im):
    icc = im.info.get("icc_profile")
    if icc:
        try:
            src = ImageCms.ImageCmsProfile(io.BytesIO(icc))
            im = ImageCms.profileToProfile(im, src, ImageCms.createProfile("sRGB"), outputMode="RGB")
        except Exception:
            pass
    return im.convert("RGB")


def crop(im, fx=0.5, fy=0.5, ratio=RATIO):
    w, h = im.size
    if w / h > ratio:
        cw, ch = round(h * ratio), h
    else:
        cw, ch = w, round(w / ratio)
    x = min(max(round(fx * w - cw / 2), 0), w - cw)
    y = min(max(round(fy * h - ch / 2), 0), h - ch)
    return im.crop((x, y, x + cw, y + ch))


def make(src, slug, fx=0.5, fy=0.5, out=OUT):
    im = to_srgb(ImageOps.exif_transpose(Image.open(src)))
    im = crop(im, fx, fy)
    out.mkdir(parents=True, exist_ok=True)
    for suf, w in SIZES.items():
        r = im.resize((w, round(w / RATIO)), Image.LANCZOS)
        if w < 1600:
            r = r.filter(ImageFilter.UnsharpMask(radius=0.6, percent=55, threshold=2))
        r.save(out / f"{slug}{suf}.jpg", "JPEG", quality=80 if w == 1600 else 82, optimize=True, progressive=True)
    return im.size


if __name__ == "__main__":
    a = sys.argv[1:]
    if len(a) not in (2, 4):
        sys.exit(__doc__)
    print(make(a[0], a[1], *(float(v) for v in a[2:4])))
