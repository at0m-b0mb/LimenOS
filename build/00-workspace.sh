#!/usr/bin/env bash
# LimenOS — create a case-sensitive work volume (macOS hosts only).
#
# WHY: the stock Miyoo rootfs contains BOTH /mnt/SDCARD and /mnt/sdcard.
# macOS APFS is case-INsensitive by default, so unsquashfs dies with
#   "failed to make directory .../mnt/sdcard, because File exists"
# A case-sensitive sparse image fixes it and costs nothing.
set -euo pipefail

VOL="${LIMEN_VOL:-/Volumes/LimenWork}"
IMG="${LIMEN_IMG:-$HOME/.limenos/limenwork.sparseimage}"
SIZE="${LIMEN_SIZE:-24g}"

[[ "$(uname -s)" == "Darwin" ]] || { echo "macOS only; on Linux just use a normal dir."; exit 0; }

if mount | grep -q " on $VOL "; then
  echo "already mounted: $VOL"; df -h "$VOL" | tail -1; exit 0
fi

mkdir -p "$(dirname "$IMG")"
if [[ ! -f "$IMG" ]]; then
  echo "creating $SIZE case-sensitive sparse image at $IMG"
  hdiutil create -type SPARSE -fs 'Case-sensitive APFS' -size "$SIZE" \
    -volname "$(basename "$VOL")" "${IMG%.sparseimage}" -quiet
fi

hdiutil attach "$IMG" -mountpoint "$VOL" -nobrowse -quiet
echo "mounted $VOL"; df -h "$VOL" | tail -1
echo "detach with:  hdiutil detach $VOL"
