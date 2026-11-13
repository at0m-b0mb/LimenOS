#!/usr/bin/env bash
# LimenOS — tear a stock Miyoo Flip firmware image apart into its pieces.
#
#   ./01-unpack-stock-firmware.sh "/path/to/250527 Firmware.zip" [outdir]
#
# Produces: uboot.img  boot.img  rootfs.img  kernel.Image  resource.img
#           flip_*.dtb  kernel.config  rfs/   flash-script.sh
set -euo pipefail

ZIP="${1:?usage: $0 <firmware .zip or .img> [outdir]}"
OUT="${2:-${LIMEN_VOL:-/Volumes/LimenWork}/stock}"
mkdir -p "$OUT"; cd "$OUT"

# --- locate the raw .img --------------------------------------------------
if [[ "$ZIP" == *.zip ]]; then
  mkdir -p _zip && unzip -o -q "$ZIP" -d _zip
  IMG="$(find _zip -name '*_fw.img' | head -1)"
else
  IMG="$ZIP"
fi
[[ -f "$IMG" ]] || { echo "no *_fw.img found in $ZIP"; exit 1; }
echo "firmware: $IMG"
echo "header:   $(head -c 48 "$IMG" | tr -d '\0')"

# --- the vendor's own flashing script tells us the layout -----------------
dd if="$IMG" bs=1 skip=512 count=3584 2>/dev/null | tr -d '\0' > flash-script.sh
echo "--- vendor flash layout ---"; grep -E '^#[0-9]' flash-script.sh || true

# --- split (offsets per that script: 1M uboot / 8M boot / 80M rootfs) -----
dd if="$IMG" of=uboot.img  bs=1M skip=1  count=7  status=none
dd if="$IMG" of=boot.img   bs=1M skip=8  count=72 status=none
dd if="$IMG" of=rootfs.img bs=1M skip=80          status=none

# --- Android bootimg -> kernel + resource ---------------------------------
python3 -I - <<'PY'
import struct
d=open("boot.img","rb").read()
assert d[:8]==b'ANDROID!', "not an Android bootimg"
ks,_ka,rs,_ra,ss,_sa,_ta,ps = struct.unpack('<8I', d[8:40])
def pad(n): return (n+ps-1)//ps*ps
o=ps
open("kernel.Image","wb").write(d[o:o+ks]); o+=pad(ks)
if rs: open("ramdisk.img","wb").write(d[o:o+rs])
o+=pad(rs)
if ss: open("resource.img","wb").write(d[o:o+ss])
print(f"kernel={ks}B ramdisk={rs}B resource={ss}B page={ps}")
PY

# --- device trees out of the Rockchip resource image ----------------------
python3 -I - <<'PY'
import struct, os
if os.path.exists("resource.img"):
    d=open("resource.img","rb").read(); i=0; n=0
    while True:
        i=d.find(b'\xd0\x0d\xfe\xed', i)
        if i<0: break
        size,=struct.unpack('>I', d[i+4:i+8])
        if 1000 < size < 2_000_000 and i+size <= len(d):
            open(f"flip_{n}.dtb","wb").write(d[i:i+size])
            print(f"flip_{n}.dtb  offset={i} size={size}"); n+=1
        i+=4
PY

# --- embedded kernel config (IKCONFIG) ------------------------------------
python3 -I - <<'PY'
import gzip
d=open("kernel.Image","rb").read()
i=d.find(b'IKCFG_ST')
if i<0: print("no IKCFG_ST — kernel built without CONFIG_IKCONFIG"); raise SystemExit
blob=d[i+8:]; j=blob.find(b'IKCFG_ED')
cfg=gzip.decompress(blob[:j] if j>0 else blob[:400000])
open("kernel.config","wb").write(cfg)
print(f"kernel.config: {len(cfg)} bytes")
PY

# --- squashfs rootfs (needs a case-sensitive FS; see 00-workspace.sh) -----
command -v unsquashfs >/dev/null || { echo "install squashfs-tools"; exit 1; }
rm -rf rfs && unsquashfs -d rfs -q -no-xattrs rootfs.img >/dev/null
chmod -R u+w rfs 2>/dev/null || true
echo "rootfs extracted -> $OUT/rfs"

grep -E 'Linux version' <(strings kernel.Image) | head -1
echo "done. artifacts in $OUT"
