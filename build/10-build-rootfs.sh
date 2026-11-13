#!/usr/bin/env bash
# ============================================================================
# LimenOS M1 — build the Debian arm64 rootfs.
# ============================================================================
#   ./build/10-build-rootfs.sh [outdir]
#
# Runs debootstrap inside an arm64 Linux container, because macOS cannot do it
# and because a reproducible build should not depend on the host's packages.
# On an Apple Silicon Mac the container runs NATIVELY (arm64), so this is fast
# and nothing is emulated.
#
# Output: <outdir>/limen-rootfs.tar.zst  +  a manifest of what's inside.
#
# Design notes that matter:
#  * Debian trixie, not Kali as the base. Kali's repo is pinned to priority 100
#    so it supplies security tools and NEVER replaces libc, the kernel or the
#    toolchain. A dist-upgrade must not silently swap the base system out from
#    under a kernel you built by hand.
#  * glibc: the stock Miyoo userland is glibc 2.36. Debian trixie is 2.41.
#    We are NOT mixing them — LimenOS runs its own complete rootfs and only
#    borrows the kernel. That is why the chroot works at M1.
#  * No hashcat, no metasploit. See docs/04-constraints.md.
# ============================================================================
set -euo pipefail

OUT="${1:-$(cd "$(dirname "$0")/.." && pwd)/out}"
SUITE="${LIMEN_SUITE:-trixie}"
MIRROR="${LIMEN_MIRROR:-http://deb.debian.org/debian}"
IMAGE="debian:${SUITE}-slim"
mkdir -p "$OUT"

command -v docker >/dev/null || { echo "docker not found (colima start)"; exit 1; }
docker info >/dev/null 2>&1 || { echo "docker daemon unreachable — run: colima start"; exit 1; }

HOST_ARCH="$(docker info --format '{{.Architecture}}' 2>/dev/null || echo unknown)"
echo "[limen] builder arch: $HOST_ARCH  (aarch64/arm64 = native, no emulation)"

PKGS_CORE="$(sed -n 's/^PKG //p' "$(dirname "$0")/../packages/m1-core.list" 2>/dev/null | tr '\n' ' ')"
[ -n "$PKGS_CORE" ] || PKGS_CORE="ca-certificates curl wget"

echo "[limen] building $SUITE arm64 rootfs -> $OUT/limen-rootfs.tar.zst"

docker run --rm --platform linux/arm64 \
  -v "$OUT":/out \
  -v "$(cd "$(dirname "$0")/.." && pwd)/packages":/pkgs:ro \
  -e SUITE="$SUITE" -e MIRROR="$MIRROR" -e ZSTD_LEVEL="${LIMEN_ZSTD:-10}" \
  "$IMAGE" bash -euo pipefail -c '
    export DEBIAN_FRONTEND=noninteractive
    apt-get update -qq
    apt-get install -y -qq debootstrap zstd ca-certificates >/dev/null

    R=/rootfs
    echo "[limen] debootstrap $SUITE ..."
    debootstrap --arch=arm64 --variant=minbase \
        --include=ca-certificates,apt-utils,gnupg \
        "$SUITE" "$R" "$MIRROR"

    # ---- apt sources ------------------------------------------------------
    cat > "$R/etc/apt/sources.list" <<EOF
deb $MIRROR $SUITE main contrib non-free non-free-firmware
deb $MIRROR ${SUITE}-updates main contrib non-free non-free-firmware
deb http://security.debian.org/debian-security ${SUITE}-security main contrib non-free non-free-firmware
EOF

    # Kali repo, pinned LOW: tools only, never the base system.
    cat > "$R/etc/apt/preferences.d/kali" <<EOF
Package: *
Pin: release o=Kali
Pin-Priority: 100
EOF

    # ---- identity ---------------------------------------------------------
    echo limen > "$R/etc/hostname"
    printf "127.0.0.1\tlocalhost\n127.0.1.1\tlimen\n" > "$R/etc/hosts"
    # NOTE: os-release is written AFTER apt, not here. The base-files package
    # owns /etc/os-release and replaces it with a symlink to
    # ../usr/lib/os-release during package install, silently clobbering any
    # identity written beforehand. Found by verifying the built card.

    # ---- install the M1 core set -----------------------------------------
    cp /etc/resolv.conf "$R/etc/resolv.conf" 2>/dev/null || \
        echo "nameserver 1.1.1.1" > "$R/etc/resolv.conf"
    mount -t proc proc "$R/proc" 2>/dev/null || true

    LIST=$(sed -n "s/^PKG //p" /pkgs/m1-core.list | tr "\n" " ")
    echo "[limen] installing: $LIST"
    chroot "$R" apt-get update -qq
    # shellcheck disable=SC2086
    chroot "$R" apt-get install -y --no-install-recommends $LIST \
        || { echo "[limen] FULL SET FAILED — retrying package-by-package to find culprits"; \
             for p in $LIST; do chroot "$R" apt-get install -y --no-install-recommends "$p" \
                 >/dev/null 2>&1 || echo "[limen] UNAVAILABLE: $p" | tee -a /out/unavailable.txt; done; }

    # ---- identity, AFTER apt (base-files would have clobbered it) --------
    cat > "$R/usr/lib/os-release" <<EOF
NAME="LimenOS"
PRETTY_NAME="LimenOS (Debian $SUITE arm64) — Miyoo Flip"
ID=limenos
ID_LIKE=debian
VARIANT="Miyoo Flip / miyoo355 / RK3566"
VARIANT_ID=miyoo355
HOME_URL="https://github.com/at0m-b0mb"
EOF
    ln -sf ../usr/lib/os-release "$R/etc/os-release"
    echo "[limen] identity: $(grep PRETTY_NAME "$R/usr/lib/os-release")"

    chroot "$R" apt-get clean
    rm -rf "$R/var/lib/apt/lists"/* "$R/var/cache/apt/archives"/*.deb
    umount "$R/proc" 2>/dev/null || true

    # ---- manifest ---------------------------------------------------------
    chroot "$R" dpkg-query -W -f="\${Package}\t\${Version}\t\${Installed-Size}\n" \
        | sort > /out/rootfs-manifest.tsv
    du -sh "$R" | tee /out/rootfs-size.txt

    echo "[limen] packing ..."
    # -19 took minutes on 1.1GB for a few % — not worth it on a script you
    # iterate on. -10 is seconds. Override with LIMEN_ZSTD=19 for a release.
    tar -C "$R" -cf - . | zstd "-${ZSTD_LEVEL}" -T0 -o /out/limen-rootfs.tar.zst -f
    ls -la /out/limen-rootfs.tar.zst
  '

echo
echo "[limen] done:"
ls -la "$OUT"/limen-rootfs.tar.zst "$OUT"/rootfs-manifest.tsv 2>/dev/null
[ -f "$OUT/unavailable.txt" ] && { echo "[limen] packages that were NOT available:"; cat "$OUT/unavailable.txt"; }
echo "[limen] packages installed: $(wc -l < "$OUT/rootfs-manifest.tsv" 2>/dev/null || echo 0)"
