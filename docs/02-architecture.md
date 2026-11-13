# LimenOS — Architecture & Design Decisions

## The name

**LIMEN** — Latin, *threshold*: the stone at the doorway, the line you cross.
A clamshell handheld literally opens at a threshold, and security work is
boundary work — deciding what may cross and proving what did. Sits beside
Janus, Bastion, Gatekeeper and Cardea in the same naming family.

## Decision 1 — LimenOS lives on an SD card. The NAND is never written.

**The stock OS stays in SPI NAND, untouched. Card in → LimenOS. Card out →
your games console, bit-for-bit as it shipped.**

Three independent reasons, all measured:

1. **128 MB of internal flash.** `mtd3` is 48 MB of squashfs in a 128 MB NAND.
   A Debian base alone is ~400 MB; a working toolkit is 4–8 GB. The rootfs
   physically cannot live in NAND. This is not a preference.
2. **The vendor updater has no safety net.** It `flash_erase`s and `dd`s
   straight to `/dev/mtd1..3` with no checksum, no A/B slot, no rollback. A
   bad U-Boot write means maskrom recovery or a SPI clip.
3. **The Flip has two SD slots and the RK3566 BootROM prefers SD.** Booting
   from card is already demonstrated on this board. We get dual-boot for free.

> **Consequence:** the entire project is "build a bootable SD card." Every
> milestone below is testable by swapping cards, and failure costs you nothing.

## Decision 2 — The kernel is the project, not the userland.

From the capability audit (`docs/01`, §5), the honest summary is:

> The stock 5.10 BSP kernel is a **dead end for the wireless half of a
> cyberdeck.** It has `mac80211` and `AF_PACKET`, but **zero USB Wi-Fi drivers
> other than the built-in RTL8733BU**, no `TUN`, no `BRIDGE`, no `nftables`,
> and no USB-Ethernet in either direction. You cannot plug in an Alfa and have
> it work. Not "it needs configuring" — there is no driver to bind it.

Assembling a userland is a weekend. Getting a kernel that boots this exact
board *and* carries the radio stack is the actual engineering. So:

- **Userland:** Debian `trixie` arm64, plus the Kali repo pinned for tooling.
  No Buildroot. No custom package format. `apt install` must work, or the
  project dies of maintenance.
- **Kernel:** mainline-derived, from the lineage that already boots this board
  (ROCKNIX Flip fork → Zlyme), carrying a **LimenOS deck config** on top.

## Decision 3 — Three radios, three roles. Stop pretending one does everything.

| Radio | Role | Status |
|---|---|---|
| Internal RTL8733BU | **Management link.** Your SSH-in, your uplink, your apt. | Works today |
| External USB adapter (upper port) | **Monitor + injection.** The work radio. | Needs M2 kernel |
| Internal Bluetooth (rtk_btusb) | BLE scan / recon | Works today |

Keeping the management link on the internal radio and the capture on an
external adapter is not a compromise — it is how you keep a shell while the
work interface is in monitor mode. Design for it from the start.

## Decision 4 — Interaction model: the screen is not the terminal.

640×480, 4:3, D-pad + two sticks + ABXY, **no keyboard**. A cyberdeck that
needs you to type is a cyberdeck you never use. Three input paths, in order of
how often you'll actually reach for them:

1. **USB gadget + SSH (primary).** Plug the *lower* USB-C into a laptop; the
   Flip enumerates as a USB-Ethernet gadget; you `ssh limen.local`. Full
   keyboard, full screen, device in your pocket. *(Requires M2 — the stock
   kernel has no ECM/RNDIS/NCM gadget.)*
2. **On-device TUI (secondary).** A launcher sized for 640×480 at readable
   font size, driven entirely by D-pad + ABXY: pick an interface, pick an
   action, watch output scroll. No free-text entry except an on-screen keyboard
   for the rare SSID/password.
3. **Serial console (recovery).** `ttyS2` @ 1500000 8N1, 3.3 V. This is how you
   debug a kernel that won't boot. Get a CP2102/FTDI and find the pads before
   you flash anything.

## Decision 5 — Capture-and-analyse deck, not a cracking rig.

4× Cortex-A55 @ 1.8 GHz, ~1 GB LPDDR4, Mali-G52 2EE. There is no usable
OpenCL/CUDA path for hashcat on this GPU. **Anything CPU-bound and long-running
belongs somewhere else.** LimenOS captures, parses, scans, proxies, injects and
reports; handshakes and hashes get shipped to a real machine. The toolkit in
`docs/05` is chosen on that basis, and `docs/04` is the list of things this
device will never do well.

## Target layout on the card

```
/dev/mmcblk?p1   16 MB   FAT    boot: U-Boot env, kernel Image, DTB, extlinux
/dev/mmcblk?p2   —       ext4   LimenOS rootfs (Debian trixie arm64)
/dev/mmcblk?p3   rest    FAT32  LIMEN_DATA — captures, wordlists, loot
                         (exFAT only from M2 — see below)
```

`p3` is a vendor-neutral FAT so you can pull the card and read your captures on
any laptop without root. Captures are the output of this device; make them easy
to get at.

**But not exFAT at M1.** The stock kernel has `CONFIG_FAT_FS=y` and
`CONFIG_VFAT_FS=y` and **no `CONFIG_EXFAT_FS`** — an exFAT vault simply will not
mount on the stock kernel. So:

- **M1: FAT32**, and live with the **4 GB per-file limit** — a long `tcpdump`
  run *will* hit it. Rotate from the start: `tcpdump -C 1000 -W 20 -w cap`.
- **M1 alternative:** `CONFIG_FUSE_FS=y` is present, so `exfat-fuse` works in
  userspace if you need >4 GB files before M2. Slower, but it works.
- **M2: native exFAT** via `CONFIG_EXFAT_FS=m`, already in the deck fragment.

## Build host

Builds run in a **Linux arm64 container** (Docker/Colima is already on this
Mac). macOS cannot build a Linux kernel, and its case-insensitive APFS cannot
even unpack the stock rootfs — the image contains both `/mnt/SDCARD` and
`/mnt/sdcard`. `build/00-workspace.sh` sets up a case-sensitive work volume for
exactly this reason.
