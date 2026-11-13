#!/usr/bin/env bash
# ============================================================================
# Install the LimenOS theme onto a Miyoo Flip card. PURELY ADDITIVE.
# ============================================================================
#   ./build/30-install-theme.sh [/Volumes/YOUR_CARD]
#
# It copies ONE new folder:   Themes/LimenOS/
#
# It does NOT delete anything. It does NOT overwrite another theme. It does
# NOT touch Roms, BIOS, Emu, RetroArch, App, Imgs or your saves. By default it
# does not even edit system.json — you pick the theme in the Flip's own
# Settings, which is both safer and reversible by the same route.
#
#   --activate   additionally point system.json at it, after backing the file
#                up to system.json.limen-backup. Undo by restoring that file
#                or by choosing another theme in Settings.
# ============================================================================
set -euo pipefail
HERE="$(cd "$(dirname "$0")/.." && pwd)"
SRC="$HERE/build/Themes/LimenOS"
ACTIVATE=0
DEST=""
for a in "$@"; do
    case "$a" in
        --activate) ACTIVATE=1 ;;
        *) DEST="$a" ;;
    esac
done

[ -d "$SRC" ] || { echo "theme not built — run: python3 tools/themekit.py"; exit 1; }

# find the card: it must look like a Miyoo card, not just any volume
if [ -z "$DEST" ]; then
    for v in /Volumes/*; do
        [ -d "$v/miyoo355" ] && [ -d "$v/Roms" ] && { DEST="$v"; break; }
    done
fi
[ -n "$DEST" ] && [ -d "$DEST" ] || {
    echo "No Miyoo card found. Insert it, or pass the path."
    echo "Volumes:"; ls /Volumes/ | sed 's/^/  /'; exit 1; }

[ -d "$DEST/miyoo355" ] || { echo "$DEST has no miyoo355/ — refusing, that is not a Miyoo card"; exit 1; }
[ -d "$DEST/Themes" ] || mkdir -p "$DEST/Themes"

echo "[limen] card   : $DEST"
echo "[limen] adding : Themes/LimenOS"
echo "[limen] existing themes, which stay exactly as they are:"
ls "$DEST/Themes" | sed 's/^/           /'
echo

export COPYFILE_DISABLE=1
rm -rf "$DEST/Themes/LimenOS.tmp"
cp -R "$SRC" "$DEST/Themes/LimenOS.tmp"
# replace our own previous copy only, never anyone else's theme
[ -d "$DEST/Themes/LimenOS" ] && rm -rf "$DEST/Themes/LimenOS"
mv "$DEST/Themes/LimenOS.tmp" "$DEST/Themes/LimenOS"
find "$DEST/Themes/LimenOS" -name "._*" -delete 2>/dev/null || true
find "$DEST/Themes/LimenOS" -name ".DS_Store" -delete 2>/dev/null || true

# The theme MUST ship a font, and it must be a SINGLE-FACE .ttf.
#
# A theme with no font makes MainUI hang on the loading screen: it cannot
# draw text and does not crash, so nothing appears in dmesg. And borrowing
# the firmware's wqy-microhei.ttc is worse than nothing -- a .ttc is a font
# COLLECTION ("ttcf" magic), and renaming one to .ttf made MainUI render
# every string twice, which reads exactly like a drop shadow. A real single
# face starts 00 01 00 00.
if [ ! -f "$HERE/build/Themes/LimenOS/limen.ttf" ]; then
    echo "[limen] WARNING: no limen.ttf in the theme - MainUI will hang on loading"
fi

sync
echo "[limen] installed: $(find "$DEST/Themes/LimenOS" -type f | wc -l | tr -d ' ') files, $(du -sh "$DEST/Themes/LimenOS" | cut -f1)"

if [ "$ACTIVATE" -eq 1 ]; then
    SJ="$DEST/system.json"
    if [ -f "$SJ" ]; then
        cp "$SJ" "$SJ.limen-backup"
        python3 - "$SJ" <<'PY'
import json, sys
p = sys.argv[1]
cfg = json.load(open(p))
cfg["theme"] = "/media/sdcard0/Themes/LimenOS/"
json.dump(cfg, open(p, "w"), indent=1)
print("  system.json now points at Themes/LimenOS")
print("  previous file saved as system.json.limen-backup")
PY
        sync
    else
        echo "  no system.json on this card; pick the theme in Settings instead"
    fi
else
    echo
    echo "[limen] NOT activated, by design. On the Flip:"
    echo "          Settings  ->  Theme  ->  LimenOS"
    echo "        Or re-run with --activate to set it for you."
fi
echo
echo "[limen] nothing was deleted. Your games, saves and other themes are untouched."
