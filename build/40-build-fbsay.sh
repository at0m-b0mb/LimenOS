#!/usr/bin/env bash
# Build limen-say: a static aarch64 framebuffer text renderer for the Flip.
# Static because the device runs glibc 2.36 and the builder is newer.
set -euo pipefail
HERE="$(cd "$(dirname "$0")/.." && pwd)"
mkdir -p "$HERE/build/bin"
docker run --rm --platform linux/arm64 \
  -v "$HERE/tools/fbsay":/src:ro -v "$HERE/build/bin":/out \
  debian:trixie-slim bash -euo pipefail -c '
    export DEBIAN_FRONTEND=noninteractive
    apt-get update -qq
    apt-get install -y -qq gcc libc6-dev python3-pil fonts-dejavu-core >/dev/null
    cp -r /src /build && cd /build
    # DejaVu Sans Mono advances 0.602em, so a 14px cell wants a ~23px face.
    # The first build used a 16px face in a 16px cell and the tracking was
    # visibly loose on the device.
    python3 mkfont.py 14 26 /usr/share/fonts/truetype/dejavu/DejaVuSansMono-Bold.ttf font.h
    gcc -O2 -static -o /out/limen-say limen-say.c
    aarch64-linux-gnu-strip /out/limen-say 2>/dev/null || strip /out/limen-say
    echo "  built: $(ls -lh /out/limen-say | awk "{print \$5}")"
    file /out/limen-say
  '
