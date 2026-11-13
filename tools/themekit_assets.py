#!/usr/bin/env python3
"""
LimenOS themekit — the complete asset set.

The stock themes ship ~187 skin files; a minimal theme leaves the launcher
falling back to the vendor art, which looks wrong next to ours. This module
generates every one of them, plus the 1080p HDMI set.

Imported by themekit.py. Sizes are taken from a real installed theme, not
guessed: see docs/08-theme-contract.md.
"""
from __future__ import annotations
import math, os

from PIL import Image, ImageDraw, ImageFont

PAPER   = (243, 241, 236, 255)
SURFACE = (255, 255, 255, 255)
INK     = (27, 24, 19, 255)
MUTED   = (87, 81, 68, 255)
FAINT   = (107, 101, 84, 255)
RULE    = (220, 214, 201, 255)
RULE_S  = (196, 188, 170, 255)
BRASS   = (122, 93, 24, 255)
SHINE   = (195, 155, 36, 255)
CLEAR   = (0, 0, 0, 0)

SERIF = "/System/Library/Fonts/Supplemental/Iowan Old Style.ttc"
SANS  = "/System/Library/Fonts/SFNS.ttf"
SS = 4


def _f(path, size):
    try:
        return ImageFont.truetype(path, size)
    except Exception:
        return ImageFont.load_default()


def _new(w, h, bg=CLEAR):
    return Image.new("RGBA", (w * SS, h * SS), bg)


def _save(img, w, h, path):
    img.resize((w, h), Image.LANCZOS).save(path)


def threshold(d, x, y, s, fill):
    """The LimenOS mark: two jambs, a heavy sill, open at the head."""
    post = max(1, int(s * 0.085))
    sill = max(2, int(s * 0.150))
    left, right = x + s * 0.325, x + s * 0.675
    top, sy = y + s * 0.145, y + s * 0.690
    d.rectangle([left - post, top, left, sy], fill=fill)
    d.rectangle([right, top, right + post, sy], fill=fill)
    d.rectangle([x + s * 0.175, sy, x + s * 0.825, sy + sill], fill=fill)


# ---------------------------------------------------------------- nav tiles
NAV = {
    "game":      ("Games",    "grid"),
    "app":       ("Apps",     "square"),
    "favorite":  ("Favourite","star"),
    "recent":    ("Recent",   "clock"),
    "retroarch": ("RetroArch","chip"),
    "setting":   ("Settings", "gear"),
}


def _nav_glyph(d, kind, cx, cy, r, fg, w):
    if kind == "grid":
        s = r * 0.62
        for gx in (-1, 1):
            for gy in (-1, 1):
                d.rounded_rectangle([cx + gx * s - s * 0.78, cy + gy * s - s * 0.78,
                                     cx + gx * s + s * 0.30, cy + gy * s + s * 0.30],
                                    radius=int(s * 0.22), fill=fg)
    elif kind == "square":
        d.rounded_rectangle([cx - r * .72, cy - r * .72, cx + r * .72, cy + r * .72],
                            radius=int(r * 0.22), outline=fg, width=w)
        d.rounded_rectangle([cx - r * .28, cy - r * .28, cx + r * .28, cy + r * .28],
                            radius=int(r * 0.12), fill=fg)
    elif kind == "star":
        pts = []
        for i in range(10):
            a = -math.pi / 2 + i * math.pi / 5
            rad = r * (0.95 if i % 2 == 0 else 0.42)
            pts.append((cx + rad * math.cos(a), cy + rad * math.sin(a)))
        d.polygon(pts, fill=fg)
    elif kind == "clock":
        d.ellipse([cx - r * .85, cy - r * .85, cx + r * .85, cy + r * .85], outline=fg, width=w)
        d.line([cx, cy, cx, cy - r * .50], fill=fg, width=w)
        d.line([cx, cy, cx + r * .38, cy + r * .16], fill=fg, width=w)
    elif kind == "chip":
        d.rounded_rectangle([cx - r * .66, cy - r * .66, cx + r * .66, cy + r * .66],
                            radius=int(r * 0.16), outline=fg, width=w)
        d.rounded_rectangle([cx - r * .26, cy - r * .26, cx + r * .26, cy + r * .26],
                            radius=int(r * 0.08), fill=fg)
        for i in (-1, 0, 1):
            o = i * r * 0.40
            d.line([cx + o, cy - r * .92, cx + o, cy - r * .66], fill=fg, width=w)
            d.line([cx + o, cy + r * .66, cx + o, cy + r * .92], fill=fg, width=w)
            d.line([cx - r * .92, cy + o, cx - r * .66, cy + o], fill=fg, width=w)
            d.line([cx + r * .66, cy + o, cx + r * .92, cy + o], fill=fg, width=w)
    elif kind == "gear":
        d.ellipse([cx - r * .52, cy - r * .52, cx + r * .52, cy + r * .52], outline=fg, width=w)
        for i in range(8):
            a = i * math.pi / 4
            d.line([cx + r * .62 * math.cos(a), cy + r * .62 * math.sin(a),
                    cx + r * .95 * math.cos(a), cy + r * .95 * math.sin(a)],
                   fill=fg, width=int(w * 1.6))
    elif kind == "shield":
        d.polygon([(cx, cy - r), (cx + r * .82, cy - r * .55),
                   (cx + r * .82, cy + r * .28), (cx, cy + r),
                   (cx - r * .82, cy + r * .28), (cx - r * .82, cy - r * .55)],
                  outline=fg, width=w)


def nav_tile(path, kind, label, w, h, selected):
    img = _new(w, h)
    d = ImageDraw.Draw(img)
    W, H = w * SS, h * SS
    pad = int(W * 0.045)
    if selected:
        d.rounded_rectangle([pad, pad, W - pad, H - pad], radius=int(W * 0.10),
                            fill=SURFACE, outline=BRASS, width=max(2, int(W * 0.022)))
        fg, lab = BRASS, INK
        d.rectangle([W * 0.34, H - pad - int(H * 0.030), W * 0.66, H - pad - int(H * 0.012)],
                    fill=BRASS)
    else:
        d.rounded_rectangle([pad, pad, W - pad, H - pad], radius=int(W * 0.10),
                            fill=SURFACE, outline=RULE, width=max(1, int(W * 0.010)))
        fg, lab = MUTED, MUTED
    # No baked label here either: MainUI draws the name itself, and two
    # labels in two faces is what made the UI look broken on the device.
    r = W * 0.235
    _nav_glyph(d, kind, W / 2, H * 0.44, r, fg, max(2, int(W * 0.026)))
    _save(img, w, h, path)


# ---------------------------------------------------------------- small icons
def _chip(w, h, radius_f=0.26, fill=None, outline=None, width=2):
    img = _new(w, h)
    d = ImageDraw.Draw(img)
    W, H = w * SS, h * SS
    d.rounded_rectangle([1, 1, W - 2, H - 2], radius=int(min(W, H) * radius_f),
                        fill=fill, outline=outline, width=width)
    return img, d, W, H


def glyph_icon(path, w, h, draw_fn, fg=MUTED, bg=None, pad=0.16):
    img = _new(w, h)
    d = ImageDraw.Draw(img)
    W, H = w * SS, h * SS
    if bg:
        d.rounded_rectangle([0, 0, W - 1, H - 1], radius=int(min(W, H) * 0.24), fill=bg)
    draw_fn(d, W, H, fg, max(2, int(min(W, H) * 0.075)))
    _save(img, w, h, path)


def battery(path, w, h, pct, charging=False):
    img = _new(w, h)
    d = ImageDraw.Draw(img)
    W, H = w * SS, h * SS
    bw, bh = W * 0.74, H * 0.46
    x0, y0 = W * 0.08, (H - bh) / 2
    lw = max(2, int(W * 0.045))
    d.rounded_rectangle([x0, y0, x0 + bw, y0 + bh], radius=int(bh * 0.22),
                        outline=MUTED, width=lw)
    d.rounded_rectangle([x0 + bw + lw, y0 + bh * 0.30, x0 + bw + lw * 3.0, y0 + bh * 0.70],
                        radius=int(bh * 0.10), fill=MUTED)
    inner = bw - lw * 3
    fillw = inner * max(0.0, min(1.0, pct / 100.0))
    if fillw > 1:
        col = BRASS if pct > 20 else (140, 44, 32, 255)
        d.rounded_rectangle([x0 + lw * 1.5, y0 + lw * 1.5,
                             x0 + lw * 1.5 + fillw, y0 + bh - lw * 1.5],
                            radius=int(bh * 0.10), fill=col)
    if charging:
        cx, cy, s = W * 0.46, H * 0.5, H * 0.30
        d.polygon([(cx + s * .18, cy - s), (cx - s * .34, cy + s * .14),
                   (cx + s * .02, cy + s * .14), (cx - s * .18, cy + s),
                   (cx + s * .38, cy - s * .16), (cx - s * .02, cy - s * .16)],
                  fill=SHINE)
    _save(img, w, h, path)


def volume(path, w, h, level, maxlevel=20):
    img = _new(w, h)
    d = ImageDraw.Draw(img)
    W, H = w * SS, h * SS
    lw = max(2, int(W * 0.065))
    # speaker body
    d.polygon([(W * .18, H * .40), (W * .32, H * .40), (W * .48, H * .22),
               (W * .48, H * .78), (W * .32, H * .60), (W * .18, H * .60)], fill=MUTED)
    if level == 0:
        d.line([W * .58, H * .36, W * .84, H * .64], fill=(140, 44, 32, 255), width=lw)
        d.line([W * .84, H * .36, W * .58, H * .64], fill=(140, 44, 32, 255), width=lw)
    else:
        arcs = max(1, round(level / maxlevel * 3))
        for i in range(3):
            col = BRASS if i < arcs else RULE
            r = W * (0.14 + i * 0.11)
            d.arc([W * .50 - r, H * .5 - r, W * .50 + r, H * .5 + r],
                  -55, 55, fill=col, width=lw)
    _save(img, w, h, path)


def wifi(path, w, h, bars, locked=False, connected=False):
    img = _new(w, h)
    d = ImageDraw.Draw(img)
    W, H = w * SS, h * SS
    lw = max(2, int(W * 0.075))
    cx, cy = W * 0.5, H * 0.74
    for i in range(4):
        col = BRASS if i < bars else RULE
        r = W * (0.11 + i * 0.115)
        d.arc([cx - r, cy - r, cx + r, cy + r], 210, 330, fill=col, width=lw)
    d.ellipse([cx - lw * .9, cy - lw * .9, cx + lw * .9, cy + lw * .9],
              fill=BRASS if bars else RULE)
    if locked:
        bw, bh = W * 0.26, H * 0.20
        bx, by = W * 0.68, H * 0.52
        d.rounded_rectangle([bx, by, bx + bw, by + bh], radius=int(bh * 0.2), fill=INK)
        d.arc([bx + bw * .18, by - bh * .62, bx + bw * .82, by + bh * .38],
              180, 360, fill=INK, width=max(2, int(lw * .7)))
    if connected:
        d.line([W * .62, H * .30, W * .72, H * .40], fill=BRASS, width=lw)
        d.line([W * .72, H * .40, W * .90, H * .16], fill=BRASS, width=lw)
    _save(img, w, h, path)


def key_cap(path, w, h, label, selected=False, round_f=0.30):
    img = _new(w, h)
    d = ImageDraw.Draw(img)
    W, H = w * SS, h * SS
    if selected:
        d.rounded_rectangle([1, 1, W - 2, H - 2], radius=int(min(W, H) * round_f), fill=BRASS)
        fg = PAPER
    else:
        d.rounded_rectangle([1, 1, W - 2, H - 2], radius=int(min(W, H) * round_f),
                            fill=SURFACE, outline=RULE_S, width=max(2, int(min(W, H) * 0.055)))
        fg = INK
    size = int(min(W, H) * (0.52 if len(label) <= 1 else 0.40 if len(label) <= 2 else 0.30))
    d.text((W / 2, H / 2), label, font=_f(SERIF, size), fill=fg, anchor="mm")
    _save(img, w, h, path)


def hline(path, w, h, col=RULE):
    img = _new(w, h)
    ImageDraw.Draw(img).rectangle([0, 0, w * SS, h * SS], fill=col)
    _save(img, w, h, path)


def panel(path, w, h, radius=12, fill=SURFACE, outline=RULE_S):
    img = _new(w, h)
    d = ImageDraw.Draw(img)
    W, H = w * SS, h * SS
    p = max(1, int(min(W, H) * 0.012))
    d.rounded_rectangle([p, p, W - p, H - p], radius=int(radius * SS),
                        fill=fill, outline=outline, width=max(1, int(1.4 * SS)))
    _save(img, w, h, path)


def loading_strip(path, w, h, phase):
    """A vertical strip used as a loading animation frame."""
    img = _new(w, h, CLEAR)
    d = ImageDraw.Draw(img)
    W, H = w * SS, h * SS
    n = 5
    for i in range(n):
        y = H * (0.34 + i * 0.075)
        on = (i == phase % n)
        r = W * (0.075 if on else 0.050)
        d.ellipse([W / 2 - r, y - r, W / 2 + r, y + r], fill=BRASS if on else RULE)
    _save(img, w, h, path)


def charging_frame(path, w, h, phase):
    img = _new(w, h)
    d = ImageDraw.Draw(img)
    W, H = w * SS, h * SS
    d.rounded_rectangle([1, 1, W - 2, H - 2], radius=int(H * 0.22),
                        fill=SURFACE, outline=RULE, width=max(2, int(H * 0.035)))
    bw = (W * 0.78) * ((phase + 1) / 5.0)
    d.rounded_rectangle([W * 0.11, H * 0.36, W * 0.11 + bw, H * 0.64],
                        radius=int(H * 0.10), fill=BRASS)
    _save(img, w, h, path)


def mask_shape(path, w, h, selected):
    img = _new(w, h)
    d = ImageDraw.Draw(img)
    W, H = w * SS, h * SS
    d.rounded_rectangle([1, 1, W - 2, H - 2], radius=int(min(W, H) * 0.30),
                        fill=BRASS if selected else RULE_S)
    _save(img, w, h, path)
