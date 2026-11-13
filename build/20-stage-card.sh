#!/usr/bin/env bash
# ============================================================================
# Stage the LimenOS bootstrap + device tools onto an already-flashed card.
# ============================================================================
#   ./build/20-stage-card.sh            auto-detect the LIMEN_BOOT volume
#   ./build/20-stage-card.sh /Volumes/LIMEN_BOOT
#
# Copies onto the card's FAT partition:
#   miyoo355/app/MainUI   the vendor extension point runmiyoo.sh already calls
#   limen/                the device scripts (limen-hid, limen-chroot, m0-*)
#
# Writes only to the SD card. Needs no sudo and touches no device node.
# ============================================================================
set -euo pipefail
HERE="$(cd "$(dirname "$0")/.." && pwd)"

DEST="${1:-}"
if [ -z "$DEST" ]; then
    for v in /Volumes/LIMEN_BOOT /Volumes/LIMEN_DATA; do
        [ -d "$v" ] && { DEST="$v"; break; }
    done
fi
[ -n "$DEST" ] && [ -d "$DEST" ] || {
    echo "No LimenOS volume mounted."
    echo "Insert the flashed card and try again, or pass the path explicitly."
    echo "Mounted volumes:"; ls /Volumes/ | sed 's/^/  /'
    exit 1
}
echo "[limen] staging onto: $DEST"

# the vendor hook
mkdir -p "$DEST/miyoo355/app"
cp "$HERE/device/bootstrap/miyoo355/app/MainUI" "$DEST/miyoo355/app/MainUI"
chmod +x "$DEST/miyoo355/app/MainUI" 2>/dev/null || true

# the device tools
mkdir -p "$DEST/limen"
cp "$HERE/device/limen-hid" "$HERE/device/limen-chroot" \
   "$HERE/device/m0-dump-nand.sh" "$HERE/device/m0-identify.sh" "$DEST/limen/"
chmod +x "$DEST/limen/"* 2>/dev/null || true

cat > "$DEST/limen/README.txt" <<'TXT'
LimenOS — device tools

On the Flip these appear under /media/sdcard0/limen or /media/sdcard1/limen.
FAT32 does not carry the executable bit, so run them through sh:

  sh /media/sdcard0/limen/m0-identify.sh > /media/sdcard0/limen-identify.txt
  sh /media/sdcard0/limen/m0-dump-nand.sh /media/sdcard0/limen-backup
  sh /media/sdcard0/limen/limen-chroot

miyoo355/app/MainUI is the boot hook. runmiyoo.sh prefers an SD-card MainUI
over the internal one; ours installs an SSH key, starts dropbear, writes
LIMEN-STATUS.txt with the device address, then exits non-zero so the real
MainUI still runs and the console behaves normally.

To disable it, delete the miyoo355 folder from this card.
TXT

sync
echo "[limen] staged:"
find "$DEST/miyoo355" "$DEST/limen" -type f | sed "s|$DEST/|  |"
echo
echo "[limen] eject, put the card in the Flip, power on."
echo "[limen] after boot, read $DEST/LIMEN-STATUS.txt for its IP address."
