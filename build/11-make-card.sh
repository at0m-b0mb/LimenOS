#!/usr/bin/env bash
# ============================================================================
# LimenOS M1 — assemble a bootable SD card IMAGE from the rootfs tarball.
# ============================================================================
#   ./build/11-make-card.sh [tarball] [size_gb]
#
# PARTITION LAYOUT (docs/02-architecture.md):
#   p1    32M   FAT32  LIMEN_BOOT   kernel, dtb, extlinux.conf (M2)
#   p2   ~5G    ext4   LIMEN_ROOT   the Debian rootfs
#   p3   rest   FAT32  LIMEN_DATA   capture vault
#
# WHY NO LOOP DEVICES: inside a container `losetup -P` creates /dev/loopN but
# no /dev/loopNpX partition nodes, because udev isn't running. Rather than
# fight that with kpartx or mknod, we build each filesystem as its own plain
# file and populate it WITHOUT MOUNTING —
#     mkfs.ext4 -d <dir>   (e2fsprogs)      and   mcopy (mtools)
# — then dd the finished filesystems into the card at fixed sector offsets.
# No privileged mounts, no loop devices, fully reproducible.
#
# ---------------------------------------------------------------------------
# !! THIS BUILDS A CARD, NOT A BOOT CHAIN !!
# At M1 the Flip still boots the VENDOR kernel from NAND; LimenOS is entered
# from the running stock system via device/limen-chroot. Self-booting needs
# the M2 kernel and a verified U-Boot path, and M0 step 4 must pass first.
# This script writes NO bootloader and NEVER touches a device node.
# ============================================================================
set -euo pipefail

HERE="$(cd "$(dirname "$0")/.." && pwd)"
TARBALL="${1:-$HERE/out/limen-rootfs.tar.zst}"
SIZE_GB="${2:-8}"
OUT="$HERE/out/limen-card.img"
# Exact card size in bytes (from: diskutil info diskN | grep "Disk Size").
# When set, the image is built to match the card exactly so no space is wasted.
CARD_BYTES="${LIMEN_CARD_BYTES:-}"
# Rootfs partition size in GiB. 1.1G is used; the rest is headroom for apt.
ROOT_GIB="${LIMEN_ROOT_GIB:-8}"

[ -f "$TARBALL" ] || { echo "no rootfs tarball at $TARBALL — run build/10-build-rootfs.sh first"; exit 1; }
command -v docker >/dev/null && docker info >/dev/null 2>&1 || { echo "docker/colima needed"; exit 1; }

echo "[limen] building ${SIZE_GB}G card image -> $OUT"
mkdir -p "$HERE/out"

docker run --rm --platform linux/arm64 \
  -v "$HERE/out":/out \
  -v "$HERE/overlay":/overlay:ro \
  -e SIZE_GB="$SIZE_GB" -e TARBALL="$(basename "$TARBALL")" \
  -e CARD_BYTES="$CARD_BYTES" -e ROOT_GIB="$ROOT_GIB" \
  debian:trixie-slim bash -euo pipefail -c '
    export DEBIAN_FRONTEND=noninteractive
    apt-get update -qq
    apt-get install -y -qq dosfstools e2fsprogs mtools zstd fdisk >/dev/null

    WORK=/work; mkdir -p $WORK; cd $WORK
    SECT=512
    if [ -n "${CARD_BYTES:-}" ]; then
        TOTAL=$(( CARD_BYTES / SECT ))
        echo "[limen] sizing to the real card: $CARD_BYTES bytes ($TOTAL sectors)"
    else
        TOTAL=$(( SIZE_GB * 1024 * 1024 * 1024 / SECT ))
    fi

    # --- fixed sector geometry (1MiB aligned) ---------------------------
    P1_START=2048;          P1_SIZE=$(( 32 * 1024 * 1024 / SECT ))      # 32 MiB
    P2_START=$(( P1_START + P1_SIZE ))
    P2_SIZE=$(( ROOT_GIB * 1024 * 1024 * 1024 / SECT ))                  # rootfs
    P3_START=$(( P2_START + P2_SIZE ))
    P3_SIZE=$(( TOTAL - P3_START ))
    [ "$P3_SIZE" -gt 262144 ] || { echo "card too small for a data partition"; exit 1; }
    echo "[limen] geometry (512B sectors):"
    printf "  p1 %10d +%10d  (%d MiB) FAT32 LIMEN_BOOT\n" $P1_START $P1_SIZE $(( P1_SIZE/2048 ))
    printf "  p2 %10d +%10d  (%d MiB) ext4  LIMEN_ROOT\n" $P2_START $P2_SIZE $(( P2_SIZE/2048 ))
    printf "  p3 %10d +%10d  (%d MiB) FAT32 LIMEN_DATA\n" $P3_START $P3_SIZE $(( P3_SIZE/2048 ))

    # --- unpack the rootfs ----------------------------------------------
    echo "[limen] unpacking rootfs ..."
    mkdir -p $WORK/root
    zstd -dc "/out/$TARBALL" | tar -C $WORK/root -xf -

    # --- overlay ----------------------------------------------------------
    if [ -d /overlay/rootfs ]; then
        echo "[limen] applying overlay ..."
        cp -a /overlay/rootfs/. $WORK/root/
        chmod +x $WORK/root/usr/local/bin/* 2>/dev/null || true
    fi

    # --- fstab + mountpoints ---------------------------------------------
    cat > $WORK/root/etc/fstab <<EOF
LABEL=LIMEN_ROOT  /            ext4   defaults,noatime           0 1
LABEL=LIMEN_BOOT  /boot/limen  vfat   defaults,noatime,noauto    0 2
LABEL=LIMEN_DATA  /data        vfat   defaults,noatime,nofail,uid=1000,gid=1000 0 2
tmpfs             /tmp         tmpfs  defaults,nosuid,nodev      0 0
EOF
    mkdir -p $WORK/root/data $WORK/root/boot/limen

    # --- p2: ext4 populated WITHOUT mounting ------------------------------
    echo "[limen] building ext4 root ($(du -sh $WORK/root | cut -f1)) ..."
    truncate -s $(( P2_SIZE * SECT )) p2.img
    mkfs.ext4 -q -F -L LIMEN_ROOT -d $WORK/root p2.img

    # --- p1: boot ----------------------------------------------------------
    truncate -s $(( P1_SIZE * SECT )) p1.img
    mkfs.vfat -F32 -n LIMEN_BOOT p1.img >/dev/null
    mkdir -p $WORK/boot
    cat > $WORK/boot/README.txt <<EOF
LIMEN_BOOT — empty at M1 by design.

At M1 the Flip boots the VENDOR kernel from internal NAND and LimenOS is
entered with device/limen-chroot. This partition is where the M2 deck kernel,
its DTB and extlinux.conf will go once SD boot is verified on your unit
(M0 step 4). Nothing here boots anything yet.
EOF
    mcopy -i p1.img $WORK/boot/README.txt ::/ 

    # --- p3: capture vault -------------------------------------------------
    truncate -s $(( P3_SIZE * SECT )) p3.img
    mkfs.vfat -F32 -n LIMEN_DATA p3.img >/dev/null
    mkdir -p $WORK/data
    cat > $WORK/data/README.txt <<EOF
LIMEN_DATA — LimenOS capture vault

captures/   pcaps and logs. FAT32 at M1: 4 GB per-file limit.
            Use limen-capture, which rotates for you.
loot/       engagement output. TREAT AS EVIDENCE — see SCOPE.md.
wordlists/  keep big lists here, never inside the rootfs image.
payloads/   .ducky scripts for limen-hid.

Pull the card and read this partition on any machine, no root needed.
EOF
    mmd -i p3.img ::/captures ::/loot ::/wordlists ::/payloads
    mcopy -i p3.img $WORK/data/README.txt ::/

    # --- assemble ----------------------------------------------------------
    IMG=/out/limen-card.img
    echo "[limen] assembling $IMG ..."
    rm -f "$IMG"; truncate -s $(( TOTAL * SECT )) "$IMG"
    sfdisk --quiet "$IMG" <<EOF
label: dos
${P1_START},${P1_SIZE},c,*
${P2_START},${P2_SIZE},83
${P3_START},${P3_SIZE},c
EOF
    # bs MUST be large. The first version used bs=$SECT (512) because the
    # seeks are expressed in sectors, which meant 16.7 million syscalls for an
    # 8 GiB partition and ~105 million for a 50 GiB one. Every partition here
    # starts on an exact MiB boundary, so seek in MiB and move real blocks.
    MIB=1048576
    P1_MIB=$(( P1_START * SECT / MIB ))
    P2_MIB=$(( P2_START * SECT / MIB ))
    P3_MIB=$(( P3_START * SECT / MIB ))

    # p3 is mostly empty FAT clusters written into an already-zeroed sparse
    # file, so only its metadata head has to be copied. 256 MiB is far more
    # than the two FATs plus reserved sectors need, at any cluster size.
    P3_HEAD_MIB=256

    dd if=p1.img of="$IMG" bs=1M seek=$P1_MIB conv=notrunc status=none
    echo "[limen] p1 written (32 MiB)"
    dd if=p2.img of="$IMG" bs=1M seek=$P2_MIB conv=notrunc status=none
    echo "[limen] p2 written ($(( ROOT_GIB )) GiB)"
    dd if=p3.img of="$IMG" bs=1M seek=$P3_MIB count=$P3_HEAD_MIB conv=notrunc status=none
    echo "[limen] p3 metadata written (${P3_HEAD_MIB} MiB head; tail is already zero)"
    sync

    echo "[limen] partition table:"
    sfdisk -l "$IMG"
    # The tail of p3 is empty FAT clusters; only its header+FATs matter.
    # Report how little actually has to reach the card.
    # must cover the p3 metadata head, not an unrelated 64 MiB guess
    MIN=$(( P3_START * SECT + P3_HEAD_MIB * MIB + 64 * MIB ))
    echo "MIN_WRITE_BYTES=$MIN" > /out/min-write.txt
    echo "[limen] minimum bytes that must be written: $MIN ($(( MIN / 1024 / 1024 )) MiB)"
    echo "[limen] filesystem check (ext4):"
    e2fsck -fn p2.img 2>&1 | tail -4
    ls -la "$IMG"
  '

echo
echo "[limen] card image ready: $OUT"
ls -la "$OUT"
echo
echo "To write it (CHECK THE DEVICE NODE TWICE — this erases the target):"
echo "  diskutil list"
echo "  diskutil unmountDisk /dev/diskN"
echo "  sudo dd if=$OUT of=/dev/rdiskN bs=4m status=progress"
echo
echo "Run that yourself. This script never touches a device node."
