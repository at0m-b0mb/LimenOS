#!/usr/bin/env python3
"""
LimenOS brandkit — the mark, the banner, the favicon.

Self-contained: a clone rebuilds every asset identically with

    python3 tools/brandkit.py

House palette and type, shared with the rest of the catalogue. One glyph,
the *threshold*: LIMEN is the sill — the stone at the foot of a doorway, the
line you step over. So the heavy element is at the BOTTOM, which is what
distinguishes it from a lintel (a slab carried on top).

Nothing here is decorative for its own sake. The mark has to survive being
16 pixels tall in a browser tab, so it is three rectangles and an opening.
"""
from __future__ import annotations

import os
import sys

try:
    from PIL import Image, ImageDraw, ImageFont
except ImportError:
    sys.exit("needs Pillow:  python3 -m pip install Pillow")

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
OUT = os.path.join(ROOT, "images")

SERIF = "/System/Library/Fonts/Supplemental/Iowan Old Style.ttc"
SANS = "/System/Library/Fonts/SFNS.ttf"
MONO = "/System/Library/Fonts/Menlo.ttc"

# House palette — identical to the rest of the catalogue.
PAPER, SURFACE = "#F3F1EC", "#FFFFFF"
INK, MUTED, FAINT = "#1B1813", "#575144", "#6B6554"
RULE, RULE_STRONG = "#DCD6C9", "#C4BCAA"
BRASS, SHINE = "#7A5D18", "#C39B24"

D_BG, D_SURFACE = "#000000", "#131312"
D_INK, D_MUTED, D_FAINT = "#F3F0E9", "#A29C91", "#8C877C"
D_RULE = "#2B2B28"
D_BRASS, D_SHINE = "#D9B75C", "#F1C84B"


def pal(dark: bool) -> dict:
    if dark:
        return dict(bg=D_BG, surface=D_SURFACE, ink=D_INK, muted=D_MUTED,
                    faint=D_FAINT, rule=D_RULE, brass=D_BRASS, shine=D_SHINE)
    return dict(bg=PAPER, surface=SURFACE, ink=INK, muted=MUTED,
                faint=FAINT, rule=RULE, brass=BRASS, shine=SHINE)


def _g(frac: float, s: int) -> float:
    return frac * s


def font(path: str, size: int, index: int = 0):
    try:
        return ImageFont.truetype(path, size, index=index)
    except Exception:
        return ImageFont.load_default()


def draw_threshold(d: ImageDraw.ImageDraw, s: int, fg: str) -> None:
    """Two jambs and a heavy sill, OPEN at the top.

    An enclosed rectangle reads as a picture frame, not a doorway — that was
    the first attempt and it was wrong. Leaving the head open, making the
    opening clearly portrait, and letting the sill overhang both jambs makes
    it read as a threshold: something you step over, which is what limen means.

    Survives 16px because it is three rectangles with no interior detail.
    """
    post = max(2, int(_g(0.085, s)))          # jamb thickness
    sill_h = max(3, int(_g(0.150, s)))        # the sill — heaviest element

    left, right = _g(0.325, s), _g(0.675, s)  # portrait opening
    top_y = _g(0.145, s)
    sill_y = _g(0.690, s)

    # jambs, running from the open head down to the sill
    d.rectangle([left - post, top_y, left, sill_y], fill=fg)
    d.rectangle([right, top_y, right + post, sill_y], fill=fg)
    # the sill: overhangs both jambs, and is the thickest thing here
    d.rectangle([_g(0.175, s), sill_y, _g(0.825, s), sill_y + sill_h], fill=fg)


def render_mark(path: str, size: int, dark: bool = False) -> None:
    """A brass tile with the threshold punched out of it."""
    ss = 4 if size >= 64 else 8
    s = size * ss
    p = pal(dark)
    img = Image.new("RGBA", (s, s), (0, 0, 0, 0))
    d = ImageDraw.Draw(img)
    r = int(_g(0.22, s))
    d.rounded_rectangle([0, 0, s - 1, s - 1], radius=r, fill=p["brass"])
    draw_threshold(d, s, p["bg"] if dark else PAPER)
    img = img.resize((size, size), Image.LANCZOS)
    img.save(path)


def render_favicon(path: str) -> None:
    imgs = []
    for sz in (16, 32, 48, 64, 128, 256):
        tmp = os.path.join(OUT, f".fav{sz}.png")
        render_mark(tmp, sz)
        imgs.append(Image.open(tmp).convert("RGBA"))
    imgs[0].save(path, format="ICO",
                 sizes=[(i.width, i.height) for i in imgs])
    for sz in (16, 32, 48, 64, 128, 256):
        os.remove(os.path.join(OUT, f".fav{sz}.png"))


def text(d, xy, s, fnt, fill, ls=0.0, anchor="la") -> float:
    """Draw text with optional letter-spacing; returns the advance."""
    if not ls:
        d.text(xy, s, font=fnt, fill=fill, anchor=anchor)
        return d.textlength(s, font=fnt)
    x, y = xy
    for ch in s:
        d.text((x, y), ch, font=fnt, fill=fill, anchor=anchor)
        x += d.textlength(ch, font=fnt) + ls
    return x - xy[0]


def render_banner(path: str, dark: bool = False) -> None:
    """README banner, 1280x448. All coordinates below are 1x; ss supersamples.

    Layout is explicit rather than derived from H*0.5, because the first
    version computed the wordmark from the centre and the mark from the same
    centre, and the two collided.
    """
    ss = 2
    W1, H1 = 1280, 448
    W, H = W1 * ss, H1 * ss
    p = pal(dark)
    img = Image.new("RGB", (W, H), p["bg"])

    # watermark: large, pale, cropped by the right edge so it reads as texture
    wm = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    gs = int(H * 1.05)
    g = Image.new("RGBA", (gs, gs), (0, 0, 0, 0))
    draw_threshold(ImageDraw.Draw(g), gs, p["rule"])
    # 0.80 shows both jambs with the sill bleeding off the edge, which still
    # reads as a threshold. Further right (0.60) leaves only one jamb and the
    # shape collapses into an L.
    wm.paste(g, (int(W - gs * 0.80), int(H * 0.5 - gs * 0.50)), g)
    img = Image.alpha_composite(img.convert("RGBA"), wm).convert("RGB")
    d = ImageDraw.Draw(img)

    PAD = 84            # safe margin (spec: >= 80)
    MARK = 92

    tmp = os.path.join(OUT, ".bnr_mark.png")
    render_mark(tmp, MARK * ss, dark)
    m = Image.open(tmp).convert("RGBA")
    img.paste(m, (PAD * ss, 74 * ss), m)
    os.remove(tmp)
    d = ImageDraw.Draw(img)

    # wordmark, well clear of the mark
    f_name = font(SERIF, 92 * ss)
    nx = PAD * ss
    base = 268 * ss                       # baseline
    d.text((nx, base), "LimenOS", font=f_name, fill=p["ink"], anchor="ls")
    wlen = d.textlength("LimenOS", font=f_name)
    d.rectangle([nx, base + 16 * ss, nx + wlen, base + 16 * ss + 3 * ss],
                fill=p["brass"])

    f_sub = font(SANS, 26 * ss)
    d.text((nx, base + 62 * ss),
           "A games console that becomes a security deck,",
           font=f_sub, fill=p["muted"], anchor="ls")
    d.text((nx, base + 96 * ss),
           "without touching its flash.",
           font=f_sub, fill=p["muted"], anchor="ls")

    f_meta = font(MONO, 19 * ss, index=0)
    text(d, (nx, 414 * ss),
         "Miyoo Flip  ·  RK3566  ·  aarch64", f_meta, p["faint"], ls=0.6 * ss)

    img.resize((W1, H1), Image.LANCZOS).save(path)


def main() -> int:
    os.makedirs(OUT, exist_ok=True)
    jobs = [
        ("mark-512.png", lambda p: render_mark(p, 512)),
        ("mark-512-dark.png", lambda p: render_mark(p, 512, dark=True)),
        ("mark-128.png", lambda p: render_mark(p, 128)),
        ("mark-64.png", lambda p: render_mark(p, 64)),
        ("mark-32.png", lambda p: render_mark(p, 32)),
        ("mark-16.png", lambda p: render_mark(p, 16)),
        ("favicon.ico", render_favicon),
        ("banner.png", lambda p: render_banner(p)),
        ("banner-dark.png", lambda p: render_banner(p, dark=True)),
    ]
    for name, fn in jobs:
        path = os.path.join(OUT, name)
        fn(path)
        print(f"  {name:22} {os.path.getsize(path)//1024:5} KB")
    print(f"\n  {len(jobs)} assets -> images/\n")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
