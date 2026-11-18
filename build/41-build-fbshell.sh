#!/usr/bin/env bash
# Build limen-shell: the on-device terminal with an on-screen keyboard.
set -euo pipefail
HERE="$(cd "$(dirname "$0")/.." && pwd)"
mkdir -p "$HERE/build/bin"
docker run --rm --platform linux/arm64 \
  -v "$HERE/tools/fbshell":/src:ro -v "$HERE/tools/fbsay":/fbsay:ro \
  -v "$HERE/build/bin":/out \
  debian:trixie-slim bash -euo pipefail -c '
    export DEBIAN_FRONTEND=noninteractive
    apt-get update -qq
    apt-get install -y -qq gcc libc6-dev python3-pil fonts-dejavu-core >/dev/null
    cp -r /src /build && cp /fbsay/mkfont.py /build/ && cd /build
    python3 mkfont.py 14 26 /usr/share/fonts/truetype/dejavu/DejaVuSansMono-Bold.ttf font.h
    gcc -O2 -static -Wall -o /out/limen-shell limen-shell.c
    strip /out/limen-shell
    echo "  built: $(ls -lh /out/limen-shell | awk "{print \$5}")"
  '
