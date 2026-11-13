# LimenOS — Honesty Ceilings

What this device will **not** do, written down before the first line of code so
nobody — including us — oversells it later. Each entry says *why*, measured
where possible.

## Hard physical ceilings (no software fixes these)

| Ceiling | Measurement | Consequence |
|---|---|---|
| **~1 GB LPDDR4** | board spec | No large-wordlist work in RAM. ZRAM + an SD swapfile are mandatory, and SD swap is slow enough to feel. Big `nmap` sweeps and `bettercap` with many modules will OOM. |
| **4× Cortex-A55 @ 1.8 GHz** | DTB / U-Boot | ~1/10th a laptop core for crypto. Handshake cracking is measured in *weeks*, not hours. |
| **Mali-G52 2EE, no usable compute** | board spec | **hashcat will not GPU-accelerate here.** Not "needs drivers" — there is no supported OpenCL path. Treat as CPU-only, then don't crack on it at all. |
| **128 MB SPI NAND** | updater script | The OS cannot live internally. Everything is on SD, forever. |
| **3000 mAh / 11.1 Wh** | board spec | An external Alfa in continuous monitor mode is a ~2 W load on top of the SoC. Budget **1.5–3 h** of real field work, less with injection. |
| **Lower USB-C cannot source VBUS** | DTB `dr_mode="otg"`, no host regulator | External adapters **must** go on the **upper** port. A 2 W adapter may still need a powered hub or Y-cable — and then you're carrying a hub. |
| **One host port** | board | Adapter *or* storage *or* Ethernet. Not two. A hub costs you power. |
| **640×480, no keyboard** | DTB panel | Any workflow needing real typing happens over SSH. Accept it and design for it. |

## Software ceilings on the *stock* kernel (M1 only)

These are why M2 exists. All verified in `stock-kernel-5.10.160.config`:

- **No external USB Wi-Fi adapter will work.** `CONFIG_RTL8733BU=y` is the only
  WLAN driver in the kernel. Nothing binds an Alfa, an ath9k_htc, an MT7921AU.
- **No monitor mode on the internal radio.** The vendor 8733bu driver is built
  `=y`, so it cannot even be unloaded to swap in a patched build.
- **No VPN, no tunnels** — `CONFIG_TUN` absent.
- **No nftables** — iptables-legacy only.
- **No bridging** — rogue-AP forwarding patterns don't assemble.
- **No USB-Ethernet** in either direction — no adapters, no laptop gadget link.
- **No exFAT.** `FAT_FS`/`VFAT_FS` are `=y`, `EXFAT_FS` is absent. The capture
  vault must be **FAT32 at M1**, which caps any single file at **4 GB** — long
  captures must be rotated (`tcpdump -C`). `FUSE_FS=y` means `exfat-fuse` is a
  working userspace fallback.
- **CH340/CH341 USB-serial adapters do not work.** `CONFIG_USB_SERIAL_CH341` is
  absent, and the CH340 is the most common cheap USB-UART in everyone's drawer.
  Stock binds **CP210x, FTDI, PL2303, OTI6858 and Keyspan** — buy a **CP2102 or
  FT232**, not the £2 CH340. (`CH341` is in the M2 deck fragment.)
- **No eBPF.** `CONFIG_BPF_SYSCALL` is absent — no `bpftrace`, no modern
  `tcpdump -j` offload, no eBPF-based tooling until M2.
- **No NBD** (`CONFIG_BLK_DEV_LOOP=y` but no `NBD`) — no network block devices
  for remote image work at M1.

## Ceilings that remain *after* M2 — and are uncertain

Flagged honestly as unverified. Do not plan around them until tested on
hardware.

- **Internal RTL8733BU monitor/injection is plausible, not proven.**
  The [libc0607 rtl8733bu fork](https://github.com/libc0607/rtl8733bu-20230626)
  (built for FPV, where injection matters) reports *"packet injection works
  well with legacy and MCS rates"* — but also that **monitor RX cannot decode
  any LDPC-encoded packet at any bandwidth**, and injection is unreliable for
  some MCS/length combinations. That fork targets kernel 6.8 and is ~3 years
  old. Treat the internal radio as a **management link**; buy an external
  adapter for real work.
- **2.4 GHz only on some units.** The alternate radio (`RTL8189FU.ko`, really
  an RTL8188FU) is 802.11n 2.4 GHz. If your unit has that part, 5 GHz work is
  off the table internally regardless of driver.
- **Regulatory enforcement is on.** `CONFIG_CFG80211_REQUIRE_SIGNED_REGDB=y` +
  `CFG80211_USE_KERNEL_REGDB_KEYS=y`. A replacement kernel needs a signed
  `regulatory.db` or you lose channels and TX power control.
- **Mainline GPU/VPU regressions.** Mainline is *demonstrated* on this board by
  others, but moving off the BSP kernel risks video decode, suspend quality and
  battery reporting. M1 keeps the stock kernel precisely so you have a working
  fallback card while M2 is unstable.
- **Thermals.** A handheld in a plastic clamshell with no fan, running a radio
  flat out. Sustained captures will throttle. Unmeasured — measure it.

## Things we are deliberately not building

- **No unattended/autonomous attack modes.** Nothing in LimenOS fires at a
  target without a human pressing a button for that specific action.
- **No jamming, no deauth-flood "stress" mode.** Same line already drawn in
  Themis: it's illegal spectrum interference, not a test.
- **No cracking rig pretensions.** See above — the silicon says no.
- **No stock-OS replacement.** The NAND is never written. If LimenOS ever
  requires flashing internal storage, that's a design failure, not a feature.
