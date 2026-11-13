# Provenance of the files in this directory

These are **derived artifacts**, extracted from a stock Miyoo Flip firmware
image (`miyoo355_fw_20250527`, build stamp `20250527210639`) with
[`build/01-unpack-stock-firmware.sh`](../../build/01-unpack-stock-firmware.sh).
They are kept here because every factual claim in
[`docs/01-hardware-ground-truth.md`](../../docs/01-hardware-ground-truth.md) is
checkable against them.

| File | What it is | Licence |
|---|---|---|
| `stock-kernel-5.10.160.config` | The kernel configuration, decompressed from the `IKCFG_ST` blob inside the shipped kernel image. | A Linux kernel `.config` is a build input to a **GPL-2.0** work and is distributed as part of it. |
| `miyoo355-v10.dtb` | The device tree blob, from the Rockchip resource image inside `boot.img`. | Compiled from kernel-tree DTS — **GPL-2.0**. |
| `S36load_wifi_modules` | A BusyBox init script from the vendor's Buildroot rootfs. | Vendor script, reproduced verbatim as **evidence** for a documented claim (it `insmod`s a filename that does not exist in the image). |
| `stock-fstab` | The stock `/etc/fstab`. | Configuration data; facts, not authorship. |

**No vendor binaries, firmware blobs, bootloader, kernel image or root
filesystem are redistributed here.** To obtain those, download the official
firmware from Miyoo and run the unpack script against it yourself.

If you are Miyoo and would like any of these removed, open an issue and they
will be taken down.
