# The Miyoo Flip theme contract

Reverse-engineered from the stock firmware and the themes shipped with it.
It does not appear to be documented anywhere, so it is written down here.

## Where a theme lives

```
/media/sdcard0/Themes/<Name>/
    config.json          typography and colours
    skin/                the 640x480 panel art      (~190 files)
    skin_1080p/          the HDMI art               (~110 files)
    icons/               system icons, 132x143
    icons/sel/           their selected variants
    sound/               UI sounds (change.wav)
    <font>.ttf           referenced by config.json
```

`system.json` selects it:

```json
"theme": "/media/sdcard0/Themes/LimenOS/"
```

**`/media/sdcard0` is a symlink to `/mnt/sdcard`,** which is the *first*
partition of the card in slot one. MainUI hardcodes that path, so a theme has
to be on that partition.

## config.json

Every key observed across the installed themes:

```json
{
  "name": "...", "author": "...", "description": "...",
  "hideIconTitle": false,
  "hideLabels":  { "icons": false, "hints": false },
  "frame":       { "border-left": 0, "border-right": 0 },
  "batteryPercentage": { "visible": true, "font": "x.ttf", "size": 14,
                         "color": "#RRGGBB", "textAlign": "center",
                         "fixed": true, "offsetX": 0, "offsetY": 0 },
  "title":       { "font": "x.ttf", "size": 28, "color": "#RRGGBB" },
  "hint":        { "font": "x.ttf", "size": 22, "color": "#RRGGBB" },
  "currentpage": { "color": "#RRGGBB" },
  "total":       { "color": "#RRGGBB" },
  "grid":        { "font": "x.ttf", "grid1x4": 24, "grid3x4": 17,
                   "color": "#RRGGBB", "selectedcolor": "#RRGGBB" },
  "list":        { "font": "x.ttf", "size": 25, "color": "#RRGGBB" }
}
```

## The sizes that matter

Taken by measuring a real installed theme, not guessed.

| File | 640x480 | 1080p |
|---|---|---|
| `background.png` | 640x480 | 1920x1080 |
| `bg-title.png`, `tips-bar-bg.png` | 640x60 | 1920x100 |
| `ic-{game,app,favorite,recent,retroarch,setting}-{n,f}.png` | 156x278 | 320/338x600 |
| `bg-game-item-{n,f}.png` | 155x170 | 355/336x399 |
| `bg-list-{l,s}.png` | 640x90 / 640x56 | 1920x176 / 1920x100 |
| `bg-list-s2.png`, `list-item-select-bg-short.png` | 320x60 | 500x110 |
| `bg-pop-menu-{1..4}.png` | 320x{70,130,190,250} | — |
| `icon-volume-{00..20}.png` | 48x48 | — |
| `power-{0,20,50,80,full}%-icon.png` | 48x48 | 75x60 |
| `ic-power-charge-{0,25,50,75,100}%.png` | 48x48 | 75x60 |
| `icon-wifi-signal-{01..04}.png` | 48x48 | 60x60 |
| `app_loading_{01..05}.png` | 166x480 | 200x1080 |
| `charging-{01..05}.png` | 192x82 | — |
| `icons/*.png` | 132x143 | — |

## Notes worth having

- **Themes can be partial.** The installed ones range from 302 to 562 files;
  anything absent falls back to the vendor art, which looks wrong next to a
  complete theme. LimenOS generates all 441.
- **Icon labels are drawn by MainUI**, not baked into the icon, so an icon
  carries only its glyph.
- **At 132x143 on a 3.5" panel a console logo is mush.** Short typographic
  marks stay legible; that is why LimenOS uses them.
- An **enclosed rectangle reads as a picture frame**, and a **circle with dots
  inside reads as a smiley face**. Both were drawn, looked at, and redrawn.
- A background must sit *under* the interface. A full-strength watermark shows
  between list rows and reads as a rendering fault; LimenOS keeps it near 12%
  opacity and away from where content sits.
