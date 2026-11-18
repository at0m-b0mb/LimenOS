#!/usr/bin/env python3
"""Compose real launcher screens from the generated theme, for judging it."""
import json, os, sys
from PIL import Image, ImageDraw, ImageFont

T = sys.argv[1] if len(sys.argv) > 1 else "build/Themes/LimenOS"
cfg = json.load(open(os.path.join(T, "config.json")))
FONT = os.path.join(T, "limen.ttf")

def f(sz):
    try: return ImageFont.truetype(FONT, sz)
    except Exception: return ImageFont.load_default()
def L(n): return Image.open(os.path.join(T, n)).convert("RGBA")
def hx(h):
    h = h.lstrip("#"); return tuple(int(h[i:i+2], 16) for i in (0, 2, 4)) + (255,)

INK  = hx(cfg["title"]["color"]);  MUT = hx(cfg["grid"]["color"])
HINT = hx(cfg["hint"]["color"]);   GOLD = hx(cfg["total"]["color"])

def chrome(img, title, right=None):
    d = ImageDraw.Draw(img)
    img.alpha_composite(L("skin/bg-title.png"), (0, 0))
    d.text((22, 30), title, font=f(cfg["title"]["size"]), fill=INK, anchor="lm")
    img.alpha_composite(L("skin/icon-wifi-signal-04.png").resize((24, 24), Image.LANCZOS), (500, 18))
    img.alpha_composite(L("skin/power-80%-icon.png").resize((28, 28), Image.LANCZOS), (534, 16))
    d.text((618, 30), right or "06:37", font=f(20), fill=INK, anchor="rm")
    img.alpha_composite(L("skin/tips-bar-bg.png"), (0, 420))
    return d

def hints(img, d, pairs, right=None):
    x = 20
    for btn, lab in pairs:
        img.alpha_composite(L(f"skin/icon-{btn}-54.png").resize((28, 28), Image.LANCZOS), (x, 436))
        d.text((x + 36, 450), lab, font=f(cfg["hint"]["size"]), fill=HINT, anchor="lm")
        x += 40 + int(f(cfg["hint"]["size"]).getlength(lab)) + 26
    if right:
        d.text((618, 450), right, font=f(cfg["hint"]["size"]), fill=GOLD, anchor="rm")

# 1. main menu
a = L("skin/background.png").copy(); d = chrome(a, "")
a.alpha_composite(L("skin/miyoo-topbar.png"), (18, 12))
x = 14
for key, lab, sel in (("favorite", "Favorite", 1), ("game", "Game", 0),
                      ("retroarch", "RetroArch", 0), ("app", "App", 0)):
    a.alpha_composite(L(f"skin/ic-{key}-{'f' if sel else 'n'}.png").resize((150, 264), Image.LANCZOS), (x, 78))
    d.text((x + 75, 300), lab, font=f(cfg["grid"]["grid1x4"]), fill=INK if sel else MUT, anchor="mm")
    x += 154
for i in range(5):
    a.alpha_composite(L("skin/dot-a.png" if i == 0 else "skin/dot-n.png"), (288 + i * 24, 400))
hints(a, d, [("A", "OPEN"), ("B", "BACK")])
a.convert("RGB").save("build/s1.png")

# 2. console grid
b = L("skin/background.png").copy(); d = chrome(b, "Game", "72   06:37")
gx, gy = 16, 76
for i, (key, name) in enumerate((("arcade","ARCADE"),("lynx","ATARI LYNX"),("7800","ATARI7800"),
                                 ("dc","DC"),("dos","DOS"),("easyrpg","EasyRPG"),
                                 ("cps2","FBNEO"),("mame","MAME2003PLUS"))):
    sel = (i == 1)
    b.alpha_composite(L("skin/bg-game-item-f.png" if sel else "skin/bg-game-item-n.png").resize((150, 164), Image.LANCZOS), (gx, gy))
    b.alpha_composite(L(f"icons/{'sel/' if sel else ''}{key}.png").resize((86, 94), Image.LANCZOS), (gx + 32, gy + 14))
    d.text((gx + 75, gy + 140), name, font=f(cfg["grid"]["grid3x4"]), fill=INK if sel else MUT, anchor="mm")
    gx += 154
    if gx > 620: gx, gy = 16, gy + 172
hints(b, d, [("A", "OPEN"), ("B", "BACK")], "1/5")
b.convert("RGB").save("build/s2.png")

# 3. settings list
c = L("skin/background.png").copy(); d = chrome(c, "Settings")
y = 76
for i, (ic, lab, val) in enumerate([("icon-setting-wifi.png", "Wi-Fi", "Sunset12"),
                                    ("icon-brightness-48.png", "Brightness", "6"),
                                    ("icon-theme.png", "Theme", "LimenOS"),
                                    ("icon-font-size.png", "Font size", "26"),
                                    ("icon-device-info-48.png", "About", "RK3566")]):
    c.alpha_composite(L("skin/bg-list-s.png"), (0, y))
    if i == 2:
        c.alpha_composite(L("skin/list-item-select-bg-short.png").resize((640, 56), Image.LANCZOS), (0, y))
    c.alpha_composite(L(f"skin/{ic}").resize((24, 24), Image.LANCZOS), (34, y + 16))
    d.text((74, y + 28), lab, font=f(cfg["list"]["size"]), fill=INK if i == 2 else MUT, anchor="lm")
    d.text((606, y + 28), val, font=f(cfg["hint"]["size"]), fill=GOLD if i == 2 else HINT, anchor="rm")
    y += 58
hints(c, d, [("A", "SELECT"), ("B", "BACK")])
c.convert("RGB").save("build/s3.png")

ims = [Image.open(f"build/s{i}.png") for i in (1, 2, 3)]
W = sum(i.width for i in ims) + 16 * 4
comp = Image.new("RGB", (W, ims[0].height + 32), (18, 18, 17)); x = 16
for im in ims: comp.paste(im, (x, 16)); x += im.width + 16
comp.save("build/preview.png")
print("  preview:", comp.size)
