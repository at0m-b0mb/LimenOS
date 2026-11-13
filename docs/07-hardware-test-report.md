# LimenOS — Hardware Test Report

**Device:** Miyoo Flip, `MIYOO RK3566 355 V10 Board`
**Firmware:** stock `20250527210639`, kernel `5.10.160 #152`
**Date:** 2026-11-13
**Method:** LimenOS M1 (Debian trixie arm64 chroot) over SSH on the real device.

No network details from the test environment are recorded here.

---

## Summary

| Area | Result |
|---|---|
| Debian arm64 chroot | **works** — 455 packages |
| Security toolkit | **34 / 34 tools execute** |
| `AF_PACKET` capture | **works**, zero dropped packets |
| BadUSB / HID gadget | **works** — `/dev/hidg0`, boot keyboard |
| Monitor mode | **NOT SUPPORTED** (`-95`) |
| CPU | **2 of 4 cores were offline** — enabling them gives **2.26×** |
| zram | **works** — 1500 MB allocated on a 957 MB machine |
| Thermals | 79 °C after 3 min at full load, **no throttling** |

---

## 1. The CPU is running at half capacity

The single most actionable finding.

```
present : 0-3        possible : 0-3
online  : 0-1        offline  : 2-3
```

The stock firmware boots with **two of four Cortex-A55 cores offline**. The
frequency table also tops out at **1.992 GHz**, not the 1.8 GHz quoted in most
specifications.

Benchmark — SHA-512 over 60 000 × 4 KiB blocks per worker:

| Configuration | 1 worker | 4 workers |
|---|---|---|
| 2 cores (stock) | 1.37 s | **4.486 s** |
| 4 cores | 1.30 s | **1.986 s** |

**2.26× more parallel throughput**, for about 1 °C. Single-thread time is
unchanged, which confirms the gain is core count and not clock.

```bash
echo 1 > /sys/devices/system/cpu/cpu2/online
echo 1 > /sys/devices/system/cpu/cpu3/online
```

Reversible, and the chroot sees `nproc` = 4 immediately. Whether Miyoo disabled
them for battery life, thermals or both is unknown — see §5 before leaving them
on permanently.

## 2. Toolkit: 34 / 34 execute

Every tool was run, not merely located. nmap 7.95, tcpdump 4.99.5, tshark,
masscan 1.3.2, arp-scan, hping3, sqlmap 1.9.6, nikto, gobuster 3.6, ffuf 2.1.0,
whatweb, wafw00f, binwalk, flashrom 1.4.0, openocd 0.12.0, avrdude, sigrok-cli,
minicom 2.10, picocom 3.1, i2cdetect, john 1.9.0, hashid, yara 4.5.2,
sleuthkit 4.12.1, exiftool 13.25, foremost, tmux 3.5a, Python 3.13.5,
scapy 2.6.1, cryptography 43.0.0, iw 6.9, hostapd 2.10, bluetoothctl 5.82,
fsck.exfat.

> An earlier run of this suite reported 4 failures. All four were **defects in
> the test harness**, not the tools — `hostapd -v` exits non-zero by design,
> `fsck.exfat` has no `-V`, `john --list=build-info` is not a valid option, and
> masscan was mis-captured. Verified individually afterwards; masscan scans
> correctly. A test that cannot be trusted about its own failures is worse than
> no test.

## 3. Capture works; monitor mode does not

`tcpdump -i wlan0 -nn -c 20` captured live traffic: **20 captured, 23 received
by filter, 0 dropped**. `nmap -sn` over a /24 completed in **6.6–7.1 s**.
scapy 2.6.1 imports and enumerates interfaces.

The radio is `0bda:b733` (**RTL8733BU**), dual-band — 14 × 2.4 GHz and
28 × 5 GHz channels at 20 dBm, associated at 40 MHz on a 5 GHz channel, despite
a product string reading "802.11n".

```
Supported interface modes:
     * IBSS   * managed   * AP   * P2P-client   * P2P-GO

# iw phy phy1 interface add mon0 type monitor
command failed: Operation not supported (-95)
```

**No monitor mode, measured.** This is a driver limitation, not a configuration
one. See `docs/04-constraints.md`.

## 4. BadUSB works on stock firmware

```
/dev/hidg0 EXISTS
report length : 8      protocol : 1 (keyboard)
subclass      : 1      UDC bound : fcc00000.dwc3
```

Enabled purely through the vendor's own mechanism (`usb_hid_en` →
`usbdevice restart`), with no patching. `limen-hid` emits correct reports on
the device — `hello` produced 80 bytes (5 chars × press/release × 8), with
keycodes `0b 08 0f 0f 12`, correct per the HID usage table. The `--arm` safety
gate refuses to run a script without it. With no USB host attached, writes fail
cleanly (`Cannot send after transport endpoint shutdown`) rather than hanging.

## 5. Memory: zram earns its place

957 MB usable RAM. **No swap is configured by default** — the `zram0` device
exists but is unused, which is a real hazard on a 1 GB device.

With `limen-zram on` (768 MB, lz4, swappiness 180):

| Allocated | MemAvailable | Swap used |
|---|---|---|
| 800 MB | 44 MB | 29 MB |
| 1100 MB | 27 MB | 319 MB |
| **1500 MB** | 24 MB | **723 MB** |

OOM-killed at roughly **1500–1600 MB** — about **57 % more than physical RAM**.

> **Caveat, stated plainly:** the test pages were almost entirely zeros and
> compressed about 6:1 (`orig=30MB compressed=5MB`). Real workloads compress
> far worse, so treat 1.5 GB as an optimistic ceiling, not a budget.

## 6. Thermals: hot, but it does not throttle

Four cores, full load, 180 seconds:

| t (s) | SoC | GPU | CPU MHz |
|---|---|---|---|
| 10 | 45 °C | 42 °C | 1992 |
| 60 | 73 °C | 61 °C | 1992 |
| 120 | 78 °C | 65 °C | 1992 |
| 175 | **79 °C** | 67 °C | **1992** |

**No frequency throttling at any point.** Trip points are 75 °C and 85 °C
(passive) and 115 °C (critical); `thermal-cpufreq-0` cooling state stayed at 0,
and every "thermal" line in `dmesg` was boot-time governor registration, not a
throttle event. It cooled from 79 °C to **56 °C within 20 seconds** of idle.

Three minutes is not an endurance test. A plastic clamshell with no fan, already
at 79 °C and past the first passive trip point, will throttle on a longer run —
that remains unmeasured.

## 7. Corrections this testing forced

- **4 cores, not the 2 the stock OS runs**, and **1.992 GHz, not 1.8 GHz**.
- `/mnt` is read-only (squashfs), so `limen-chroot` could never have worked
  with its original mountpoint. Now tmpfs.
- Card mountpoints move between boots — the FAT partitions appeared on
  `/mnt/sdcard` and `/media/sdcard2`, not `sdcard0`/`sdcard1`. Find by LABEL.
  This also means **the vendor boot hook is not guaranteed to fire**, since it
  only checks `sdcard0` and `sdcard1`.
- The 32 MiB FAT boot partition mounts fine under Linux despite macOS refusing
  it as out-of-spec FAT32.
- The stock root password is the Rockchip BSP default.
