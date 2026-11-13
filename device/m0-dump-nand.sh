#!/bin/sh
# ============================================================================
# LimenOS M0 — dump the Miyoo Flip's internal SPI NAND to an SD card.
# ============================================================================
# RUN THIS ON THE DEVICE, on the STOCK firmware, BEFORE you change anything.
#
#   ./m0-dump-nand.sh [/mnt/SDCARD/limen-backup]
#
# This script is READ-ONLY with respect to the NAND. It never opens an mtd
# device for writing and never calls flash_erase/nandwrite. Your vendor
# miyoo355_fw.img is NOT a substitute for this: it has no mtd0 (idbloader /
# bl31 / OP-TEE) and no userdata, so a restore from it alone can leave you
# with an unbootable device.
#
# Tools used are all present in stock firmware: nanddump, sha256sum, df.
# ============================================================================
set -u

DEST="${1:-/mnt/SDCARD/limen-backup}"
STAMP="$(date +%Y%m%d-%H%M%S 2>/dev/null || echo unknown)"
OUT="$DEST/nand-$STAMP"

die() { echo "FATAL: $*" >&2; exit 1; }
say() { echo "[limen] $*"; }

# --- sanity -----------------------------------------------------------------
[ -r /proc/mtd ] || die "/proc/mtd unreadable — is this the Flip, as root?"
command -v nanddump >/dev/null 2>&1 || die "nanddump not found"

say "MTD layout as the running kernel sees it:"
cat /proc/mtd
echo

# --- figure out how much we need --------------------------------------------
NEED=0
PARTS=""
while read -r dev size erase name; do
    case "$dev" in mtd*:) ;; *) continue ;; esac
    idx="${dev%:}"
    sz=$(( 0x$size ))
    NEED=$(( NEED + sz ))
    PARTS="$PARTS $idx"
    printf '  %-6s %10d bytes  %s\n' "$idx" "$sz" "$name"
done < /proc/mtd
[ -n "$PARTS" ] || die "no MTD partitions parsed from /proc/mtd"
echo
say "total to dump: $(( NEED / 1024 / 1024 )) MiB"

mkdir -p "$OUT" 2>/dev/null || die "cannot create $OUT (is the card mounted & writable?)"

# df in busybox reports 1K blocks
AVAIL_K=$(df -k "$OUT" 2>/dev/null | awk 'NR==2 {print $4}')
[ -n "${AVAIL_K:-}" ] || die "cannot determine free space on $OUT"
NEED_K=$(( NEED / 1024 + 8192 ))
say "free on destination: $(( AVAIL_K / 1024 )) MiB, need ~$(( NEED_K / 1024 )) MiB"
[ "$AVAIL_K" -gt "$NEED_K" ] || die "not enough free space on $OUT"

# --- dump --------------------------------------------------------------------
MANIFEST="$OUT/MANIFEST.txt"
{
  echo "LimenOS M0 NAND backup"
  echo "date        : $(date 2>/dev/null)"
  echo "uname       : $(uname -a)"
  echo "model       : $(cat /proc/device-tree/model 2>/dev/null | tr -d '\0')"
  echo "wifi_chip   : $(cat /data/wifi_chip 2>/dev/null || echo unknown)"
  echo
  echo "--- /proc/mtd ---"
  cat /proc/mtd
  echo
} > "$MANIFEST"

RC=0
for idx in $PARTS; do
    src="/dev/$idx"
    dst="$OUT/$idx.bin"
    [ -e "$src" ] || { say "SKIP $src (no device node)"; continue; }
    say "dumping $src -> $dst"
    # --omitoob keeps the image flashable by the vendor dd path;
    # --bb=dumpbad records bad blocks rather than aborting on them.
    if nanddump --omitoob --bb=dumpbad -f "$dst" "$src" 2>>"$OUT/nanddump.log"; then
        :
    else
        say "WARNING: nanddump reported errors on $src (see nanddump.log)"
        RC=1
    fi
    sum=$(sha256sum "$dst" 2>/dev/null | awk '{print $1}')
    sz=$(wc -c < "$dst" 2>/dev/null)
    printf '%-8s %12s bytes  sha256=%s\n' "$idx" "$sz" "$sum" >> "$MANIFEST"
done

sync
echo
say "manifest:"
cat "$MANIFEST"
echo
if [ "$RC" -eq 0 ]; then
    say "DONE — backup at $OUT"
else
    say "DONE WITH WARNINGS — check $OUT/nanddump.log before trusting this backup"
fi
say "Now copy this directory off the card and onto a real machine."
say "A backup that only exists on the SD card in the device is not a backup."
exit "$RC"
