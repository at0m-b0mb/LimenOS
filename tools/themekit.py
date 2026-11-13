#!/usr/bin/env python3
"""
LimenOS themekit — generates a Miyoo Flip theme in the LimenOS house style.

    python3 tools/themekit.py [outdir]        default: build/Themes/LimenOS

Warm paper and gold, hairline rules, one accent used sparingly. The mark is
the LimenOS threshold: two jambs and a heavy sill, open at the head.

The Flip's theming contract (reverse-engineered from the stock themes):
    Themes/<Name>/config.json     typography and colours
    Themes/<Name>/skin/           the UI art, at fixed sizes
    Themes/<Name>/icons/          system icons, 132x143
    Themes/<Name>/icons/sel/      their selected variants
    system.json "theme" points at the chosen folder.

Adding a theme folder changes nothing else on the card: existing themes,
games and saves are untouched, and the Flip switches between them in
Settings.
"""
from __future__ import annotations
import json, os, sys

try:
    from PIL import Image, ImageDraw, ImageFont, ImageFilter
except ImportError:
    sys.exit("needs Pillow:  python3 -m pip install Pillow")

# ---- house palette --------------------------------------------------------
PAPER       = (243, 241, 236, 255)   # #F3F1EC
SURFACE     = (255, 255, 255, 255)
INK         = (27, 24, 19, 255)      # #1B1813
MUTED       = (87, 81, 68, 255)
FAINT       = (107, 101, 84, 255)
RULE        = (220, 214, 201, 255)
RULE_STRONG = (196, 188, 170, 255)
BRASS       = (122, 93, 24, 255)     # #7A5D18
SHINE       = (195, 155, 36, 255)    # #C39B24
CLEAR       = (0, 0, 0, 0)

SERIF = "/System/Library/Fonts/Supplemental/Iowan Old Style.ttc"
SANS  = "/System/Library/Fonts/SFNS.ttf"

SS = 3   # supersample factor


def font(path, size, index=0):
    try:
        return ImageFont.truetype(path, size, index=index)
    except Exception:
        return ImageFont.load_default()


def canvas(w, h, bg=CLEAR):
    return Image.new("RGBA", (w * SS, h * SS), bg)


def done(img, w, h, path):
    img.resize((w, h), Image.LANCZOS).save(path)


def rounded(d, box, r, fill=None, outline=None, width=1):
    d.rounded_rectangle(box, radius=r, fill=fill, outline=outline, width=width)


def threshold(d, x, y, s, fill):
    """The LimenOS mark: two jambs, a heavy overhanging sill, open head."""
    post = max(2, int(s * 0.085))
    sill = max(3, int(s * 0.150))
    left, right = x + s * 0.325, x + s * 0.675
    top, sy = y + s * 0.145, y + s * 0.690
    d.rectangle([left - post, top, left, sy], fill=fill)
    d.rectangle([right, top, right + post, sy], fill=fill)
    d.rectangle([x + s * 0.175, sy, x + s * 0.825, sy + sill], fill=fill)


# ---- the skin -------------------------------------------------------------
def bg_main(w, h, path):
    """Paper, a whisper of the mark, one gold hairline.

    The first attempt drew the threshold in full RULE grey at 115% of the
    screen height. On the list screens it showed between the rows and read as
    a rendering fault rather than texture. A background has to sit *under* the
    interface: it is now ~12% opacity and tucked into the lower right, where
    the content does not sit.
    """
    img = canvas(w, h, PAPER)
    gs = int(h * SS * 0.78)
    g = Image.new("RGBA", (gs, gs), CLEAR)
    threshold(ImageDraw.Draw(g), 0, 0, gs, RULE)
    g.putalpha(g.getchannel("A").point(lambda a: int(a * 0.12)))
    img.alpha_composite(g, (int(w * SS - gs * 0.72), int(h * SS - gs * 0.80)))
    d = ImageDraw.Draw(img)
    # a single gold hairline along the top: the one accent
    d.rectangle([0, 0, w * SS, max(1, int(2 * SS))], fill=BRASS)
    done(img, w, h, path)


def bar(w, h, path, strong=False):
    img = canvas(w, h, CLEAR)
    d = ImageDraw.Draw(img)
    d.rectangle([0, 0, w * SS, h * SS], fill=SURFACE if strong else PAPER)
    d.rectangle([0, h * SS - max(1, int(1.5 * SS)), w * SS, h * SS], fill=RULE)
    done(img, w, h, path)


def list_item(w, h, path, selected=False, radius=8):
    img = canvas(w, h, CLEAR)
    d = ImageDraw.Draw(img)
    pad = int(6 * SS)
    box = [pad, pad // 2, w * SS - pad, h * SS - pad // 2]
    if selected:
        rounded(d, box, radius * SS, fill=SURFACE, outline=BRASS, width=max(2, int(2 * SS)))
        # gold tab on the leading edge marks the selection
        d.rounded_rectangle([pad, pad // 2 + int(6 * SS), pad + int(5 * SS),
                             h * SS - pad // 2 - int(6 * SS)],
                            radius=int(2.5 * SS), fill=BRASS)
    else:
        rounded(d, box, radius * SS, fill=SURFACE, outline=RULE_STRONG, width=max(2, int(1.6 * SS)))
    done(img, w, h, path)


def game_card(w, h, path, selected=False):
    img = canvas(w, h, CLEAR)
    d = ImageDraw.Draw(img)
    pad = int(4 * SS)
    box = [pad, pad, w * SS - pad, h * SS - pad]
    if selected:
        rounded(d, box, int(10 * SS), fill=SURFACE, outline=BRASS, width=max(2, int(2.5 * SS)))
        d.rectangle([int(w * SS * 0.30), h * SS - pad - int(5 * SS),
                     int(w * SS * 0.70), h * SS - pad - int(1 * SS)], fill=BRASS)
    else:
        rounded(d, box, int(10 * SS), fill=SURFACE, outline=RULE, width=max(1, int(1.2 * SS)))
    done(img, w, h, path)


def button(w, h, path, selected=False, radius=10):
    img = canvas(w, h, CLEAR)
    d = ImageDraw.Draw(img)
    box = [int(1 * SS), int(1 * SS), w * SS - int(1 * SS), h * SS - int(1 * SS)]
    if selected:
        rounded(d, box, radius * SS, fill=BRASS)
    else:
        rounded(d, box, radius * SS, fill=SURFACE, outline=RULE_STRONG, width=max(1, int(1.2 * SS)))
    done(img, w, h, path)


def popup(w, h, path):
    img = canvas(w, h, CLEAR)
    d = ImageDraw.Draw(img)
    pad = int(3 * SS)
    rounded(d, [pad, pad, w * SS - pad, h * SS - pad], int(12 * SS),
            fill=SURFACE, outline=RULE_STRONG, width=max(1, int(1.5 * SS)))
    d.rectangle([pad + int(14 * SS), pad + int(10 * SS),
                 pad + int(46 * SS), pad + int(13 * SS)], fill=BRASS)
    done(img, w, h, path)


def dot(w, h, path, active=False):
    img = canvas(w, h, CLEAR)
    d = ImageDraw.Draw(img)
    r = int(min(w, h) * SS * 0.30)
    cx, cy = w * SS // 2, h * SS // 2
    if active:
        d.ellipse([cx - r, cy - r, cx + r, cy + r], fill=BRASS)
    else:
        d.ellipse([cx - r, cy - r, cx + r, cy + r], fill=RULE_STRONG)
    done(img, w, h, path)


def pill(w, h, path):
    img = canvas(w, h, CLEAR)
    d = ImageDraw.Draw(img)
    rounded(d, [0, 0, w * SS, h * SS], int(h * SS * 0.5), fill=BRASS)
    done(img, w, h, path)


def plain(w, h, path, fill=PAPER):
    img = canvas(w, h, fill)
    done(img, w, h, path)


# ---- system icons ---------------------------------------------------------
# Short, readable marks rather than console photographs: at 132x143 on a 3.5"
# screen a logo becomes mush, while two or three letters stay legible. The
# label under each icon is drawn by MainUI itself, so these carry the glyph.
ICONS = {
    "32X": "32X", "5200": "5200", "7800": "7800", "amiga": "AMI", "arcade": "ARC",
    "arduboy": "ARD", "atari": "2600", "atarist": "ST", "c64": "C64", "col": "COL",
    "cpc": "CPC", "cps1": "CP1", "cps2": "CP2", "cps3": "CP3", "dc": "DC",
    "dos": "DOS", "easyrpg": "RPG", "fairchild": "CHF", "fc": "FC", "fds": "FDS",
    "gb": "GB", "gba": "GBA", "gbc": "GBC", "gg": "GG", "gw": "G&W", "itv": "ITV",
    "lynx": "LNX", "mame": "MAME", "md": "MD", "megaduck": "DUCK", "msu1": "MSU",
    "msumd": "MSU", "msx": "MSX", "n64": "N64", "nds": "NDS", "neocd": "NCD",
    "neogeo": "NEO", "ngp": "NGP", "ngpc": "NGPC", "ody": "ODY", "openbor": "BOR",
    "pce": "PCE", "pcecd": "PCCD", "pico": "PICO", "poke": "PKM", "ports": "PORT",
    "ppsspp": "PSP", "ps": "PS1", "psp": "PSP", "satella": "SAT", "scummvm": "SCUM",
    "search": "FIND", "segacd": "SCD", "segasgone": "SG1", "sfc": "SFC", "sgb": "SGB",
    "sgfx": "SGFX", "shoot": "SHMP", "sms": "SMS", "sufami": "SUFA",
    "supervision": "SV", "tic": "TIC", "vb": "VB", "vdp": "VDP", "vectrex": "VEC",
    "ws": "WS", "wsc": "WSC", "zxs": "ZX",
}
ICON_W, ICON_H = 132, 143


# Systems grouped by what you physically put in the machine. Without text an
# icon has to say something, and a single shared mark told you nothing: 68
# identical cartridges is no better than 68 blanks.
FAMILY = {
    "disc":   {"ps","psp","ppsspp","dc","segacd","neocd","pcecd","satella","scummvm","dos"},
    "hand":   {"gb","gbc","gba","gg","lynx","ngp","ngpc","ws","wsc","supervision",
               "megaduck","pico","arduboy","vb","gw","tic"},
    "arcade": {"arcade","mame","cps1","cps2","cps3","neogeo","openbor","shoot","sgfx"},
    "micro":  {"msx","c64","cpc","amiga","atarist","zxs","easyrpg","poke","ports"},
}
def _family(key):
    for fam, keys in FAMILY.items():
        if key in keys:
            return fam
    return "cart"


def _mark(d, fam, cx, cy, w, h, fg, lw):
    """Draw a family mark inside a strict box.

    The first version took half-extents straight off the icon size (bh =
    h*0.68) and every shape overflowed the tile -- handhelds, arcades and
    micros were all visibly clipped. Everything is now derived from HX/HY,
    the real half-extents available between the tile padding and the accent
    rule, so nothing can run outside.
    """
    HX = w * 0.255          # half-width  available
    HY = h * 0.225          # half-height available

    if fam == "disc":
        r = min(HX, HY)
        d.ellipse([cx - r, cy - r, cx + r, cy + r], outline=fg, width=lw)
        d.ellipse([cx - r * .24, cy - r * .24, cx + r * .24, cy + r * .24], fill=fg)
        d.arc([cx - r * .66, cy - r * .66, cx + r * .66, cy + r * .66],
              205, 315, fill=fg, width=max(1, int(lw * .7)))

    elif fam == "hand":
        bw, bh = HX * 0.74, HY
        d.rounded_rectangle([cx - bw, cy - bh, cx + bw, cy + bh],
                            radius=int(bw * 0.36), outline=fg, width=lw)
        d.rounded_rectangle([cx - bw * .54, cy - bh * .66, cx + bw * .54, cy - bh * .04],
                            radius=int(bw * 0.14), fill=fg)
        d.rectangle([cx - bw * .46, cy + bh * .26, cx - bw * .12, cy + bh * .38], fill=fg)
        d.ellipse([cx + bw * .14, cy + bh * .22, cx + bw * .44, cy + bh * .52], fill=fg)

    elif fam == "arcade":
        bw, bh = HX * 0.88, HY
        d.polygon([(cx - bw, cy + bh), (cx - bw, cy - bh * .46),
                   (cx - bw * .58, cy - bh), (cx + bw * .58, cy - bh),
                   (cx + bw, cy - bh * .46), (cx + bw, cy + bh)],
                  outline=fg, width=lw)
        d.rounded_rectangle([cx - bw * .54, cy - bh * .50, cx + bw * .54, cy + bh * .06],
                            radius=int(bw * 0.12), fill=fg)
        d.rectangle([cx - bw * .30, cy + bh * .40, cx + bw * .30, cy + bh * .54], fill=fg)

    elif fam == "micro":
        # a keyboard with a screen behind it, both inside the box
        kw, kh = HX, HY * 0.42
        ky = cy + HY * 0.30
        d.rounded_rectangle([cx - kw, ky - kh, cx + kw, ky + kh],
                            radius=int(kw * 0.10), outline=fg, width=lw)
        for row in (0, 1):
            for i in range(5):
                x = cx - kw * .70 + i * kw * .35
                y = ky - kh * .40 + row * kh * .60
                d.rectangle([x, y, x + kw * .18, y + kh * .30], fill=fg)
        sw, sh = HX * 0.52, HY * 0.42
        sy = cy - HY * 0.52
        d.rounded_rectangle([cx - sw, sy - sh, cx + sw, sy + sh],
                            radius=int(sw * 0.14), fill=fg)

    else:  # cart
        bw, bh = HX * 0.92, HY * 0.84
        d.rounded_rectangle([cx - bw, cy - bh, cx + bw, cy + bh],
                            radius=int(bw * 0.17), outline=fg, width=lw)
        d.rounded_rectangle([cx - bw * .56, cy - bh * .54, cx + bw * .56, cy + bh * .02],
                            radius=int(bw * 0.08), fill=fg)
        for i in (-2, -1, 0, 1, 2):
            x = cx + i * bw * .29
            d.rectangle([x - bw * .075, cy + bh * .30, x + bw * .075, cy + bh * .82], fill=fg)


def icon(key, path, selected=False):
    """One system icon. NO TEXT.

    These used to carry the system name typographically. It looked good in
    isolation and wrong on the device: MainUI draws its own label underneath
    in its own face, so every entry appeared twice in two different fonts and
    read as a rendering fault. hideIconTitle and hideLabels.icons did not
    suppress it. Icons are pictures; the launcher owns the words.
    """
    img = canvas(ICON_W, ICON_H, CLEAR)
    d = ImageDraw.Draw(img)
    pad = int(5 * SS)
    box = [pad, pad, ICON_W * SS - pad, ICON_H * SS - pad]
    if selected:
        rounded(d, box, int(14 * SS), fill=BRASS)
        fg, rule = PAPER, PAPER
    else:
        rounded(d, box, int(14 * SS), fill=SURFACE, outline=RULE,
                width=max(1, int(1.4 * SS)))
        fg, rule = INK, BRASS

    cx = ICON_W * SS // 2
    cy = int(ICON_H * SS * 0.45)
    _mark(d, _family(key), cx, cy, ICON_W * SS, ICON_H * SS, fg,
          max(2, int(ICON_W * SS * 0.030)))

    rw = int(ICON_W * SS * 0.26)
    ry = int(ICON_H * SS * 0.78)
    d.rectangle([cx - rw, ry, cx + rw, ry + max(2, int(3 * SS))], fill=rule)
    done(img, ICON_W, ICON_H, path)


CONFIG = {
    "name": "LimenOS",
    "author": "at0m-b0mb",
    "description": "Warm paper and gold. One accent, used sparingly.",
    # Back to the stock value. Every working theme ships hideIconTitle:false,
    # and setting it true did NOT stop the duplicate label -- the selected
    # item still rendered twice. Matching the themes that demonstrably work
    # is worth more than a flag whose meaning I inferred.
    "hideIconTitle": False,
    "hideLabels": {"icons": False, "hints": False},
    "frame": {"border-left": 0, "border-right": 0},
    "batteryPercentage": {
        "visible": True, "font": "limen.ttf", "size": 14, "color": "#575144",
        "textAlign": "center", "fixed": True, "offsetX": 0, "offsetY": 0,
    },
    # A theme MUST name a font and ship it. Without one MainUI cannot draw
    # text and sits on the loading screen forever -- it does not crash, so
    # there is nothing in dmesg to find. The installer copies a font off the
    # device rather than redistributing a typeface with the project.
    "title":       {"font": "limen.ttf", "size": 30, "color": "#1B1813"},
    "hint":        {"font": "limen.ttf", "size": 24, "color": "#6B6554"},
    "currentpage": {"color": "#1B1813"},
    "total":       {"color": "#7A5D18"},
    # grid1x4 and grid3x4 are the label sizes for the 4-across and 12-across
    # layouts, and MainUI neither truncates nor shrinks a long name: on the
    # real screen "ATARI LYNX" ran straight out of its 155px tile. They are
    # held EQUAL as well, because the report from the device was "double
    # font" on the SELECTED item -- two sizes overlapping is exactly what that
    # looks like, and matching them makes any double draw invisible whatever
    # is causing it. Same reasoning for the two colours.
    "grid":        {"font": "limen.ttf", "grid1x4": 18, "grid3x4": 18,
                    "color": "#1B1813", "selectedcolor": "#1B1813"},
    "list":        {"font": "limen.ttf", "size": 27, "color": "#1B1813"},
}


def build(out):
    skin = os.path.join(out, "skin")
    icons = os.path.join(out, "icons")
    sel = os.path.join(icons, "sel")
    for p in (skin, icons, sel, os.path.join(out, "skin_640_480")):
        os.makedirs(p, exist_ok=True)

    S = lambda n: os.path.join(skin, n)

    for n in ("background.png", "background.1.png", "background-small.png"):
        bg_main(640, 480, S(n))
    bg_main(640, 360, S("bg-gamelist.png"))

    bar(640, 60, S("bg-title.png"), strong=True)
    bar(640, 60, S("tips-bar-bg.png"))
    # barbg sits under the status row in the TOP-LEFT. An opaque fill there
    # reads as a stray bar across the corner, which is what it looked like on
    # the device. A slot that must exist but show nothing is transparent.
    plain(320, 38, S("barbg.png"), fill=CLEAR)

    list_item(640, 90, S("bg-list-l.png"))
    list_item(640, 56, S("bg-list-s.png"))
    list_item(320, 60, S("bg-list-s2.png"))
    list_item(320, 60, S("list-item-select-bg-short.png"), selected=True)
    list_item(640, 56, S("bg-ra-list-item.png"))

    game_card(155, 170, S("bg-game-item-n.png"))
    game_card(155, 170, S("bg-game-item-f.png"), selected=True)
    game_card(156, 176, S("bg-grid-s.png"))

    button(50, 50, S("bg-btn-01-n.png"))
    button(50, 50, S("bg-btn-01-f.png"), selected=True)
    button(111, 50, S("bg-btn-02-n.png"))
    button(111, 50, S("bg-btn-02-f.png"), selected=True)
    button(48, 48, S("bg-btn-nor.png"))
    button(50, 50, S("bg-btn-sel.png"), selected=True)
    button(111, 50, S("bg-button-nor.png"))
    button(412, 52, S("bg-input.png"))

    for n, h in (("bg-pop-menu-1.png", 70), ("bg-pop-menu-2.png", 130),
                 ("bg-pop-menu-3.png", 190), ("bg-pop-menu-4.png", 250)):
        popup(320, h, S(n))

    dot(24, 14, S("dot-n.png"))
    dot(24, 14, S("dot-a.png"), active=True)
    pill(44, 24, S("num-bg.png"))
    pill(90, 14, S("list-num.png"))

    for key in ICONS:
        icon(key, os.path.join(icons, key + ".png"))
        icon(key, os.path.join(sel, key + ".png"), selected=True)

    # Ship a single-face TTF alongside the config. See 30-install-theme.sh
    # for why a .ttc is actively harmful here.
    import shutil
    for cand in ("build/limen-ui.ttf", os.path.join(os.path.dirname(__file__),
                                                    "..", "build", "limen-ui.ttf")):
        if os.path.exists(cand):
            shutil.copy2(cand, os.path.join(out, "limen.ttf")); break
    else:
        print("  WARNING: build/limen-ui.ttf missing - theme will have no font")

    with open(os.path.join(out, "config.json"), "w") as fh:
        json.dump(CONFIG, fh, indent=4)

    n = sum(len(f) for _, _, f in os.walk(out))
    print(f"  {n} files -> {out}")
    return 0


if __name__ == "__main__":
    out = sys.argv[1] if len(sys.argv) > 1 else "build/Themes/LimenOS"
    os.makedirs(out, exist_ok=True)
    raise SystemExit(build(out))
