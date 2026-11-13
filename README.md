# LimenOS

**A security-work firmware for the Miyoo Flip.**
Turns a £70 clamshell retro handheld into a pocket Linux deck for authorised
testing — packet capture, hardware/UART work, HID gadget payloads, scanning
and analysis — without ever writing to the console's internal flash.

> **LIMEN** — Latin, *threshold*: the stone at the doorway, the line you cross.
> A clamshell opens at a threshold, and security work is boundary work:
> deciding what may cross, and proving what did.

---

## Status: M0 + M1 tooling built and tested. M2 not started.

The hardware teardown is **done and verified against your own firmware image**,
and the M0/M1 tooling is written, syntax-clean and — where it can be — tested.
`docs/03-roadmap.md` has the milestones; [docs/06-quickstart.md](docs/06-quickstart.md)
is what to actually do.

**Working now, on your stock firmware, no custom firmware needed:**
`device/limen-hid` — a USB HID keyboard gadget (BadUSB) with Ducky-script
support. Its keymap is verified by `tests/test-hid-keymap.py`, which decodes
the emitted HID reports using an independently written usage table and checks
all 95 printable ASCII characters and modifier combinations round-trip.

| | |
|---|---|
| Target | Miyoo Flip — `miyoo355`, `MIYOO RK3566 355 V10 Board` |
| SoC | Rockchip RK3566, 4× Cortex-A55, aarch64 |
| Analysed firmware | `250527 Firmware.zip` (`20250527210639`) |
| Stock stack | U-Boot 2017.09 · Linux 5.10.160 · Buildroot 2021.11 · glibc 2.36 |

---

## The one-paragraph version

The Flip is a **better hardware-hacking tool than it is a Wi-Fi tool**, and
nobody says so. Its stock kernel already gives you `AF_PACKET` raw sockets, a
USB **HID gadget** (BadUSB), native **CP210x/FTDI/PL2303** serial drivers and a
real powered USB host port — so capture, scanning, keystroke injection and UART
work all run on the firmware you have today. What it does **not** have is a
single USB Wi-Fi driver beyond its own soldered-on radio, no `TUN`, no
`BRIDGE`, no `nftables`, no conntrack or NAT, and no USB-Ethernet. Plug an Alfa
in and nothing binds. So LimenOS is two projects: a Debian userland you can
have in days, and a kernel that makes the wireless half real.

---

## What's measured, not assumed

Everything in `docs/01-hardware-ground-truth.md` came out of your firmware
image this session — the vendor's own flash script, the device tree, and the
**live kernel config extracted from the `IKCFG_ST` blob inside the kernel**
(saved at `research/stock-firmware/stock-kernel-5.10.160.config`, 191 KB).

Headline findings:

| Finding | Why it matters |
|---|---|
| `CONFIG_RTL8733BU=y` is the **only** WLAN driver | **0/10** external adapter families supported. Built-in, so not even swappable. |
| `CONFIG_PACKET=y` | tcpdump / scapy / nmap work **today** |
| `CONFIG_USB_F_HID=y` + `USB_CONFIGFS=y` | **BadUSB works today** |
| `CONFIG_USB_SERIAL_{CP210X,FTDI,PL2303}=y` | hardware/UART hacking works **today** |
| No `MODULE_SIG`, `MODULE_FORCE_LOAD=y` | unsigned out-of-tree drivers load freely |
| `CONFIG_TUN`, `BRIDGE`, `NF_TABLES`, `NF_CONNTRACK` all absent | no VPN, no bridging, no nftables, no NAT |
| 128 MB SPI NAND, `dd`-to-MTD updater, no A/B slot | the OS **cannot** live internally, and flashing it is unsafe |

Verify any of it yourself:

```bash
./build/02-audit-kernel-config.sh research/stock-firmware/stock-kernel-5.10.160.config
```

---

## Core design decision

**LimenOS lives on an SD card. The internal NAND is never written.**

Card in → LimenOS. Card out → your games console, bit-for-bit as it shipped.
Not caution for its own sake: 48 MB of squashfs in 128 MB of NAND physically
cannot hold a toolkit, and the vendor updater `flash_erase`s straight to
`/dev/mtd1` with no checksum and no rollback. Dual-boot is free; bricking is
not. Full reasoning in `docs/02-architecture.md`.

---

## Roadmap at a glance

| | Milestone | Needs | Gives you |
|---|---|---|---|
| **M0** | Safety net | a USB-UART, an SD card | NAND dump, serial console, known radio part |
| **M1** | *Limen Lite* — Debian chroot | **no kernel work** | capture, scanning, BadUSB, serial/hardware work, web tooling |
| **M2** | *Limen* — the deck kernel | the real engineering | external adapters, monitor mode, injection, VPN, nftables, laptop gadget link |
| **M3** | The deck UX | design work | 640×480 D-pad TUI, on-screen keyboard, one-button `ssh limen.local` |

**Start at M0.** It costs one USB-UART cable and makes everything after it
reversible.

---

## Layout

```
docs/01-hardware-ground-truth.md   measured facts + evidence for each
docs/02-architecture.md            the decisions and why
docs/03-roadmap.md                 M0–M4
docs/04-constraints.md             honesty ceilings — what it will never do
docs/05-toolkit.md                 package list, chosen against the silicon
kernel/limen-deck.config           236-line config fragment: every option the
                                   stock kernel is missing, with reasons
docs/06-quickstart.md              what to actually do, in order

build/00-workspace.sh              case-sensitive work volume (macOS)
build/01-unpack-stock-firmware.sh  full teardown: uboot/boot/rootfs/dtb/config
build/02-audit-kernel-config.sh    capability audit for any kernel .config
build/10-build-rootfs.sh           Debian trixie arm64 rootfs, built in Docker
build/11-make-card.sh              3-partition SD card image (never touches /dev)

device/m0-dump-nand.sh             read-only NAND backup w/ SHA-256 manifest
device/m0-identify.sh              which Wi-Fi part does THIS unit have?
device/limen-hid                   USB HID gadget / BadUSB — works on stock
device/limen-chroot                the M1 entry point: enter LimenOS from stock

overlay/rootfs/usr/local/bin/      limen-zram, limen-radio, limen-capture
packages/m1-core.list              108 packages, each justified or deferred
tests/test-hid-keymap.py           independent verification of the HID keymap
research/stock-firmware/           extracted stock kernel config, DTB, initscripts
SCOPE.md                           what this is for, and the lines it won't cross
```

---

## Honesty ceilings

Read `docs/04-constraints.md` before getting attached to an idea. The short
version: ~1 GB RAM, 4× A55, **no usable GPU compute — hashcat will not
accelerate here**, 3000 mAh, one host port, and the lower USB-C cannot power a
bus-powered adapter. This is a **capture-and-analyse deck, not a cracking rig.**
Monitor mode on the internal radio is *plausible but unproven* — plan on an
external adapter.

---

## Scope

For networks and devices you own, or engagements with written permission — no unattended attack modes, no jamming, no deauth floods.

See [SCOPE.md](SCOPE.md) for the full statement.

---

## Prior art

[CarlOS](https://github.com/CarlosPix/CarlOS) ·
[Surwish](https://github.com/Surwish/Surwish-Miyoo-Flip) ·
[GammaOS Core](https://github.com/TheGammaSqueeze/GammaOSCore) ·
[MinUI](https://github.com/shauninman/MinUI) — all gaming frontends on the
vendor kernel; useful for boot-chain reference, none of them touch the radio
stack.
[Zetarancio's RE wiki](https://github.com/Zetarancio/Miyoo-Flip-Mainline-Linux-Reverse-Engineering)
and the ROCKNIX Flip fork → Zlyme are the mainline lineage M2 should build on.
[baseos-my355](https://github.com/apommel/baseos-my355) is the minimal-boot
reference.
