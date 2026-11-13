#!/usr/bin/env python3
"""
LimenOS theme — full asset build.

    python3 tools/themekit_full.py [outdir]     default: build/Themes/LimenOS

Generates every file the stock themes ship, for both the 640x480 panel and
the 1080p HDMI output, so nothing falls back to vendor art.
"""
from __future__ import annotations
import json, os, sys, math
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from PIL import Image, ImageDraw, ImageFont
import themekit_assets as A
import themekit as T          # reuse the core generators already written

G = A.glyph_icon


# ---- settings glyphs ------------------------------------------------------
def g_sun(d, W, H, fg, w):
    r = min(W, H) * 0.20
    d.ellipse([W/2-r, H/2-r, W/2+r, H/2+r], outline=fg, width=w)
    for i in range(8):
        a = i * math.pi / 4
        d.line([W/2 + r*1.45*math.cos(a), H/2 + r*1.45*math.sin(a),
                W/2 + r*2.05*math.cos(a), H/2 + r*2.05*math.sin(a)], fill=fg, width=w)

def g_globe(d, W, H, fg, w):
    r = min(W, H) * 0.34
    d.ellipse([W/2-r, H/2-r, W/2+r, H/2+r], outline=fg, width=w)
    d.ellipse([W/2-r*0.42, H/2-r, W/2+r*0.42, H/2+r], outline=fg, width=max(1, int(w*0.8)))
    d.line([W/2-r, H/2, W/2+r, H/2], fill=fg, width=max(1, int(w*0.8)))

def g_gear(d, W, H, fg, w):
    A._nav_glyph(d, "gear", W/2, H/2, min(W, H)*0.36, fg, w)

def g_info(d, W, H, fg, w):
    r = min(W, H) * 0.34
    d.ellipse([W/2-r, H/2-r, W/2+r, H/2+r], outline=fg, width=w)
    d.ellipse([W/2-w*.7, H/2-r*.62-w*.7, W/2+w*.7, H/2-r*.62+w*.7], fill=fg)
    d.line([W/2, H/2-r*.18, W/2, H/2+r*.58], fill=fg, width=w)

def g_reset(d, W, H, fg, w):
    r = min(W, H) * 0.32
    d.arc([W/2-r, H/2-r, W/2+r, H/2+r], 40, 320, fill=fg, width=w)
    d.polygon([(W/2+r*.86, H/2-r*.60), (W/2+r*.30, H/2-r*.52),
               (W/2+r*.80, H/2-r*.04)], fill=fg)

def g_keys(d, W, H, fg, w):
    d.rounded_rectangle([W*.14, H*.28, W*.86, H*.72], radius=int(min(W,H)*0.12),
                        outline=fg, width=w)
    for i in range(3):
        d.rectangle([W*(.24+i*.20), H*.40, W*(.32+i*.20), H*.48], fill=fg)
    d.rectangle([W*.30, H*.56, W*.70, H*.64], fill=fg)

def g_font(d, W, H, fg, w):
    from PIL import ImageFont
    try: f = ImageFont.truetype(A.SERIF, int(min(W,H)*0.62))
    except Exception: f = ImageFont.load_default()
    d.text((W/2, H/2), "A", font=f, fill=fg, anchor="mm")

def g_vibrate(d, W, H, fg, w):
    d.rounded_rectangle([W*.36, H*.24, W*.64, H*.76], radius=int(min(W,H)*0.10),
                        outline=fg, width=w)
    for s in (-1, 1):
        for i in (1, 2):
            x = W/2 + s * W * (0.14 + i*0.09)
            d.line([x, H*(.40+i*.03), x, H*(.60-i*.03)], fill=fg, width=max(1,int(w*.8)))

def g_palette(d, W, H, fg, w):
    """Overlapping swatches.

    The first attempt was a circle with four dots inside it, which at 26px
    read unmistakably as a smiley face. Two offset rounded squares say
    "colour choice" without any chance of that.
    """
    s = min(W, H) * 0.42
    d.rounded_rectangle([W/2 - s*0.95, H/2 - s*0.75, W/2 + s*0.15, H/2 + s*0.45],
                        radius=int(s*0.22), outline=fg, width=w)
    d.rounded_rectangle([W/2 - s*0.15, H/2 - s*0.45, W/2 + s*0.95, H/2 + s*0.75],
                        radius=int(s*0.22), fill=A.BRASS)

def g_power(d, W, H, fg, w):
    r = min(W, H) * 0.32
    d.arc([W/2-r, H/2-r, W/2+r, H/2+r], 300, 240, fill=fg, width=w)
    d.line([W/2, H/2-r*1.05, W/2, H/2-r*0.10], fill=fg, width=w)

def g_folder(d, W, H, fg, w):
    d.polygon([(W*.12, H*.76), (W*.12, H*.30), (W*.42, H*.30),
               (W*.50, H*.40), (W*.88, H*.40), (W*.88, H*.76)], outline=fg, width=w)

def g_hotspot(d, W, H, fg, w):
    A.wifi.__wrapped__ if False else None
    cx, cy = W/2, H*0.70
    for i in range(3):
        r = min(W,H) * (0.14 + i*0.12)
        d.arc([cx-r, cy-r, cx+r, cy+r], 210, 330, fill=fg, width=w)
    d.ellipse([cx-w, cy-w, cx+w, cy+w], fill=fg)

def g_tf(d, W, H, fg, w):
    d.polygon([(W*.22, H*.16), (W*.70, H*.16), (W*.82, H*.30),
               (W*.82, H*.86), (W*.22, H*.86)], outline=fg, width=w)
    for i in range(3):
        d.line([W*(.34+i*.12), H*.22, W*(.34+i*.12), H*.38], fill=fg, width=max(1,int(w*.8)))

def g_joy(d, W, H, fg, w):
    r = min(W,H)*0.30
    d.ellipse([W/2-r, H/2-r, W/2+r, H/2+r], outline=fg, width=w)
    d.ellipse([W/2-r*.34, H/2-r*.34, W/2+r*.34, H/2+r*.34], fill=fg)

def g_cross(d, W, H, fg, w):
    a = min(W,H)*0.17
    d.rectangle([W/2-a, H/2-a*2.6, W/2+a, H/2+a*2.6], fill=fg)
    d.rectangle([W/2-a*2.6, H/2-a, W/2+a*2.6, H/2+a], fill=fg)

def g_trigger(d, W, H, fg, w):
    d.rounded_rectangle([W*.16, H*.34, W*.84, H*.62], radius=int(min(W,H)*0.12),
                        outline=fg, width=w)
    d.rectangle([W*.30, H*.20, W*.48, H*.36], fill=fg)

def g_es(d, W, H, fg, w):
    A._nav_glyph(d, "chip", W/2, H/2, min(W,H)*0.33, fg, w)

def g_shield(d, W, H, fg, w):
    A._nav_glyph(d, "shield", W/2, H/2, min(W,H)*0.36, fg, w)


SETTINGS = {
    "icon-brightness-48.png":      (40, 40, g_sun),
    "icon-language-48.png":        (40, 40, g_globe),
    "icon-key-setting-48.png":     (40, 40, g_keys),
    "icon-device-info-48.png":     (40, 40, g_info),
    "icon-factory-reset-48.png":   (40, 40, g_reset),
    "icon-font-size.png":          (40, 40, g_font),
    "icon-vibrate-48.png":         (40, 40, g_vibrate),
    "icon-theme.png":              (40, 40, g_palette),
    "icon-Shutdown.png":           (40, 40, g_power),
    "icon-folder.png":             (60, 60, g_folder),
    "icon-game.png":               (60, 60, g_es),
    "icon-hotspot-wifi.png":       (40, 40, g_hotspot),
    "icon-setting-wifi.png":       (40, 40, g_hotspot),
    "icon-trigger.png":            (40, 40, g_trigger),
    "icon-TF.png":                 (19, 24, g_tf),
    "icon-emulationstation.png":   (46, 46, g_es),
    "icon-joystick-calibrate.png": (46, 46, g_joy),
    "icon-joystick-test.png":      (46, 46, g_joy),
    "icon-core.png":               (32, 32, g_shield),
    "icon-character.png":          (32, 32, g_font),
    "icon-abc.png":                (36, 36, g_font),
    "fixit.png":                   (40, 40, g_gear),
    "headphone-icon.png":          (22, 23, g_joy),
    "icon-wait-tf-card.png":       (160, 160, g_tf),
}

ARROWS = {
    "icon-left-arrow-24.png":        (24, 24, -1),
    "icon-right-arrow-24.png":       (24, 24,  1),
    "icon-menu-left-arrow-24.png":   (25, 31, -1),
    "icon-menu-right-arrow-24.png":  (25, 31,  1),
}


def arrow(path, w, h, dirn):
    img = A._new(w, h)
    d = ImageDraw.Draw(img)
    W, H = w * A.SS, h * A.SS
    m = min(W, H) * 0.30
    if dirn > 0:
        d.polygon([(W/2-m*.5, H/2-m), (W/2+m*.7, H/2), (W/2-m*.5, H/2+m)], fill=A.MUTED)
    else:
        d.polygon([(W/2+m*.5, H/2-m), (W/2-m*.7, H/2), (W/2+m*.5, H/2+m)], fill=A.MUTED)
    A._save(img, w, h, path)


def wordmark(path, w, h):
    """The LimenOS wordmark on transparency, for the vendor logo slot.

    miyoo-topbar.png is drawn in the TOP-LEFT corner. An opaque bordered
    panel there reads as a stray block with nothing in it, which is exactly
    what it looked like on the device. Either the slot says something or it
    shows nothing; it must not be an empty box.
    """
    img = A._new(w, h)
    d = ImageDraw.Draw(img)
    W, H = w * A.SS, h * A.SS
    try:
        f = ImageFont.truetype(A.SERIF, int(H * 0.50))
    except Exception:
        f = ImageFont.load_default()
    d.text((W * 0.04, H * 0.44), "LimenOS", font=f, fill=A.INK, anchor="lm")
    tw = d.textlength("LimenOS", font=f)
    d.rectangle([W * 0.04, H * 0.72, W * 0.04 + tw, H * 0.72 + max(2, int(H * 0.055))],
                fill=A.BRASS)
    A._save(img, w, h, path)


def build(out):
    skin = os.path.join(out, "skin")
    hd   = os.path.join(out, "skin_1080p")
    for p in (skin, hd, os.path.join(out, "icons"),
              os.path.join(out, "icons", "sel"), os.path.join(out, "sound")):
        os.makedirs(p, exist_ok=True)
    S = lambda n: os.path.join(skin, n)
    D = lambda n: os.path.join(hd, n)

    # ---- the core set, from themekit.py -----------------------------------
    T.build(out)

    # ---- nav tiles (the main menu, 156x278) ------------------------------
    for key, (label, glyph) in A.NAV.items():
        A.nav_tile(S(f"ic-{key}-n.png"), glyph, label, 156, 278, False)
        A.nav_tile(S(f"ic-{key}-f.png"), glyph, label, 156, 278, True)
        A.nav_tile(D(f"ic-{key}-n.png"), glyph, label, 338, 600, False)
        A.nav_tile(D(f"ic-{key}-f.png"), glyph, label, 320, 600, True)
    A.nav_tile(S("ic-favorite-mark.png"), "star", "", 34, 39, True)
    A.nav_tile(D("ic-favorite-mark.png"), "star", "", 60, 60, True)

    # ---- battery ----------------------------------------------------------
    for n, pct in (("power-0%-icon.png", 5), ("power-20%-icon.png", 20),
                   ("power-50%-icon.png", 50), ("power-80%-icon.png", 80),
                   ("power-full-icon.png", 100)):
        A.battery(S(n), 48, 48, pct)
        A.battery(D(n), 75, 60, pct)
    for n, pct in (("ic-power-charge-0%.png", 5), ("ic-power-charge-25%.png", 25),
                   ("ic-power-charge-50%.png", 50), ("ic-power-charge-75%.png", 75),
                   ("ic-power-charge-100%.png", 100)):
        A.battery(S(n), 48, 48, pct, charging=True)
        A.battery(D(n), 75, 60, pct, charging=True)
    A.battery(S("ic-power-charge-0%.png"), 50, 40, 5, charging=True)

    # ---- volume (21 steps) ------------------------------------------------
    for i in range(21):
        A.volume(S(f"icon-volume-{i:02d}.png"), 48, 48, i)
    A.volume(S("sound-icon.png"), 48, 48, 14)
    A.volume(S("sound-mute-icon.png"), 48, 48, 0)
    A.volume(D("icon-sound.png"), 60, 60, 14)

    # ---- wifi -------------------------------------------------------------
    for i in range(1, 5):
        A.wifi(S(f"icon-wifi-signal-{i:02d}.png"), 48, 48, i)
        A.wifi(D(f"icon-wifi-signal-{i:02d}.png"), 60, 60, i)
    A.wifi(S("icon-wifi-connected.png"), 48, 48, 4, connected=True)
    A.wifi(S("icon-wifi-locked.png"), 48, 48, 3, locked=True)

    # ---- button caps ------------------------------------------------------
    caps = {"icon-A-54.png": (54, 54, "A"), "icon-B-54.png": (54, 54, "B"),
            "icon-x.png": (26, 26, "X"), "icon-y.png": (26, 26, "Y"),
            "icon-L2.png": (28, 26, "L2"), "icon-R2.png": (28, 26, "R2"),
            "icon-OK.png": (38, 26, "OK"), "icon-START.png": (48, 26, "START"),
            "ic-MENU.png": (90, 48, "MENU"), "ic-MENU+A.png": (118, 48, "MENU+A"),
            "icon-shift.png": (32, 32, "S"), "icon-shift-active.png": (32, 32, "S"),
            "icon-space.png": (32, 32, "_"), "icon-delete.png": (32, 32, "<")}
    for n, (w, h, lab) in caps.items():
        A.key_cap(S(n), w, h, lab, selected=n.endswith("-active.png"))
    for n, (w, h, lab) in {"icon-A-54.png": (40, 40, "A"), "icon-B-54.png": (40, 40, "B"),
                           "icon-y.png": (54, 40, "Y"), "icon-L2.png": (54, 40, "L2"),
                           "icon-R2.png": (54, 40, "R2"), "icon-OK.png": (40, 40, "OK"),
                           "icon-START.png": (71, 40, "START"),
                           "ic-MENU.png": (124, 40, "MENU"),
                           "ic-MENU+A.png": (168, 40, "MENU+A"),
                           "icon-shift.png": (40, 40, "S"),
                           "icon-shift-active.png": (40, 40, "S"),
                           "icon-space.png": (40, 40, "_"),
                           "icon-delete.png": (40, 40, "<"),
                           "icon-abc.png": (40, 40, "a"),
                           "icon-character.png": (40, 40, "A")}.items():
        A.key_cap(D(n), w, h, lab, selected=n.endswith("-active.png"))

    # ---- settings glyphs --------------------------------------------------
    for n, (w, h, fn) in SETTINGS.items():
        G(S(n), w, h, fn)
    for n, (w, h, fn) in SETTINGS.items():
        G(D(n), 60, 60, fn)
    G(D("icon-hardware-test.png"), 60, 60, g_gear)
    G(D("icon-hibernate.png"), 60, 60, g_power)

    # ---- arrows -----------------------------------------------------------
    for n, (w, h, dirn) in ARROWS.items():
        arrow(S(n), w, h, dirn)
        arrow(D(n), 60, 60, dirn)

    # ---- rules, panels, progress -----------------------------------------
    A.hline(S("div-line-h.png"), 640, 4)
    A.hline(S("div-02.png"), 292, 2)
    A.hline(S("div-line-v-01.png"), 1, 1, A.RULE)
    A.hline(S("div-line-v-02.png"), 1, 1, A.RULE)
    A.hline(D("div-line-h.png"), 1920, 8)
    A.hline(D("div-line-v-01.png"), 8, 880)
    A.hline(S("loading-progress-left.png"), 2, 25, A.BRASS)
    A.hline(S("loading-progress-mid.png"), 2, 25, A.BRASS)
    A.hline(S("loading-progress-right.png"), 2, 25, A.RULE)
    A.panel(S("loading-bg.png"), 254, 34, radius=8)
    A.panel(S("pop-bg.png"), 620, 360, radius=16)
    A.panel(D("pop-bg.png"), 620, 360, radius=16)
    A.panel(S("preview-bg.png"), 250, 360, radius=12)
    A.panel(D("preview-bg.png"), 610, 880, radius=16)
    A.panel(S("thumb-default.png"), 250, 360, radius=12, fill=A.PAPER)
    A.panel(S("save-default.png"), 330, 248, radius=12, fill=A.PAPER)
    A.panel(D("save-default.png"), 330, 248, radius=12, fill=A.PAPER)
    A.panel(S("menu-3line-bg.png"), 160, 89, radius=12)
    A.panel(S("menu-5line-bg.png"), 80, 74, radius=12)
    A.panel(S("menu-6line-bg.png"), 320, 420, radius=14)
    A.panel(S("menu-sub-bg.png"), 80, 75, radius=12)
    A.panel(S("menu-sub-title-bg.png"), 160, 18, radius=6, fill=A.PAPER)
    A.panel(D("menu-nline-bg.png"), 500, 980, radius=16)
    A.panel(D("menu-sub-bg.png"), 1420, 1080, radius=0)
    A.panel(D("menu-sub-title-bg.png"), 1200, 110, radius=8, fill=A.PAPER)
    A.panel(D("bg-pop-menu.png"), 500, 1080, radius=0)
    A.panel(S("input.png"), 592, 52, radius=10)
    A.panel(D("input.png"), 690, 100, radius=14)
    A.panel(S("Empty.png"), 245, 72, radius=10, fill=A.PAPER)
    A.panel(D("Empty.png"), 264, 78, radius=10, fill=A.PAPER)
    A.panel(S("bg-button-f.png"), 234, 69, radius=12, fill=A.BRASS, outline=A.BRASS)
    A.panel(S("color.png"), 44, 44, radius=8, fill=A.BRASS, outline=A.BRASS)
    A.panel(D("color.png"), 60, 60, radius=10, fill=A.BRASS, outline=A.BRASS)
    A.panel(S("bg-keysetting-f.png"), 160, 60, radius=10, fill=A.BRASS, outline=A.BRASS)
    wordmark(S("miyoo-topbar.png"), 152, 42)
    wordmark(D("miyoo-topbar.png"), 282, 60)
    A.panel(D("search-keyboard-bg.png"), 780, 884, radius=16)
    A.panel(D("bg-ra-list-item.png"), 499, 239, radius=14)
    A.panel(D("num-bg.png"), 248, 100, radius=20, fill=A.BRASS, outline=A.BRASS)
    A.panel(D("list-num.png"), 500, 100, radius=14, fill=A.PAPER)
    T.dot(20, 20, S("progress-dot.png"), active=True)
    T.dot(20, 20, D("progress-dot.png"), active=True)
    T.dot(20, 20, D("dot-a.png"), active=True)
    T.dot(20, 20, D("dot-n.png"))

    # ---- full-screen backgrounds -----------------------------------------
    T.bg_main(640, 480, S("app_loading_bg.png"))
    T.bg_main(640, 480, S("bg-io-testing.png"))
    T.bg_main(640, 480, S("bg-keysetting.png"))
    T.bg_main(640, 480, S("mask.png"))
    T.bg_main(1920, 1080, D("background.png"))
    T.bg_main(1920, 1080, D("app_loading_bg.png"))
    T.bg_main(1920, 1080, D("mask.png"))

    # ---- hd structural ----------------------------------------------------
    T.bar(1920, 100, D("bg-title.png"), strong=True)
    T.bar(1920, 100, D("tips-bar-bg.png"))
    T.list_item(1920, 176, D("bg-list-l.png"))
    T.list_item(1920, 100, D("bg-list-s.png"))
    T.list_item(500, 110, D("bg-list-s2.png"))
    T.list_item(500, 110, D("list-item-select-bg-short.png"), selected=True)
    T.game_card(355, 399, D("bg-game-item-n.png"))
    T.game_card(336, 380, D("bg-game-item-f.png"), selected=True)
    T.button(60, 100, D("bg-btn-01-n.png"))
    T.button(60, 100, D("bg-btn-01-f.png"), selected=True)
    T.button(130, 100, D("bg-btn-02-n.png"))
    T.button(130, 100, D("bg-btn-02-f.png"), selected=True)
    G(D("fixit.png"), 60, 60, g_gear)
    G(D("headphone-icon.png"), 60, 60, g_joy)
    G(D("icon-TF.png"), 60, 60, g_tf)
    G(D("icon-folder.png"), 60, 60, g_folder)
    G(D("icon-game.png"), 60, 60, g_es)
    G(D("icon-emulationstation.png"), 60, 60, g_es)
    G(D("icon-joystick-calibrate.png"), 60, 60, g_joy)
    G(D("icon-joystick-test.png"), 60, 60, g_joy)
    G(D("icon-Shutdown.png"), 60, 60, g_power)

    # ---- animations -------------------------------------------------------
    for i in range(1, 6):
        A.loading_strip(S(f"app_loading_{i:02d}.png"), 166, 480, i - 1)
        A.loading_strip(D(f"app_loading_{i:02d}.png"), 200, 1080, i - 1)
        A.charging_frame(S(f"charging-{i:02d}.png"), 192, 82, i - 1)

    # ---- hardware-test masks ---------------------------------------------
    masks = {"mask-ABXY": (30, 31), "mask-L2R2": (34, 19), "mask-LR": (34, 35),
             "mask-cross-key": (24, 25), "mask-joystick": (60, 61),
             "mask-menu": (20, 21), "mask-power": (6, 35)}
    for n, (w, h) in masks.items():
        A.mask_shape(S(f"{n}.png"), w, h, False)
        A.mask_shape(S(f"{n}-f.png"), w, h, True)
    A.panel(S("joystick-test-bg.png"), 250, 250, radius=120)
    A.panel(S("joystick-test-bg2.png"), 200, 200, radius=96)
    A.panel(S("joystick-test-dot.png"), 40, 40, radius=20, fill=A.BRASS, outline=A.BRASS)
    A.panel(S("joystick-test-dot2.png"), 32, 32, radius=16, fill=A.BRASS, outline=A.BRASS)

    # ---- grid/list edit affordances --------------------------------------
    for n in ("grid-edit-hide-nor", "grid-edit-show-nor"):
        T.game_card(135, 150, S(f"{n}.png"))
    for n in ("grid-edit-hide-sel", "grid-edit-show-sel"):
        T.game_card(135, 150, S(f"{n}.png"), selected=True)
    for n in ("ra-edit-hide-nor", "ra-edit-show-nor"):
        A.panel(S(f"{n}.png"), 196, 76, radius=12)
    for n in ("ra-edit-hide-sel", "ra-edit-show-sel"):
        A.panel(S(f"{n}.png"), 196, 76, radius=12, fill=A.BRASS, outline=A.BRASS)
    for n, (w, h) in (("nav-favorite-f", (47, 45)), ("nav-favorite-n", (34, 32)),
                      ("nav-file-f", (42, 38)), ("nav-file-n", (31, 27))):
        A.nav_tile(S(f"{n}.png"), "star" if "favorite" in n else "square",
                   "", w, h, n.endswith("-f"))
    T.bar(640, 360, S("bg-gamelist.png"))

    n = sum(len(f) for _, _, f in os.walk(out))
    print(f"  {n} files -> {out}")
    print(f"    skin        {len(os.listdir(skin))}")
    print(f"    skin_1080p  {len(os.listdir(hd))}")
    print(f"    icons       {len(os.listdir(os.path.join(out,'icons')))-1}"
          f" + {len(os.listdir(os.path.join(out,'icons','sel')))} selected")
    return 0


if __name__ == "__main__":
    out = sys.argv[1] if len(sys.argv) > 1 else "build/Themes/LimenOS"
    os.makedirs(out, exist_ok=True)
    raise SystemExit(build(out))
