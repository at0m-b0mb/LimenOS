# Miyoo Flip — Hardware & Stock Firmware Ground Truth

Everything below was **measured** from `250527 Firmware.zip`
(`miyoo355_fw_20250527`, build stamp `20250527210639`) unless a line is
explicitly marked *(external source)*. Nothing here is recalled from memory.

## 1. Identity

| Field | Value | How we know |
|---|---|---|
| Vendor model id | `miyoo355` | image header bytes 0x00–0x16 |
| Board | `MIYOO RK3566 355 V10 Board` | DTB `model` property |
| DT compatible | `rockchip,rk3566-miyoo-355-v10-linux` | DTB root node |
| SoC | Rockchip **RK3566** (4× Cortex-A55, Mali-G52 2EE) | U-Boot strings, DTB |
| Arch | **aarch64** (ARM64) | kernel `Image`, `ld-linux-aarch64.so.1` |
| Vendor build host | `raymanfeng@nuc`, tree `miyoo355_linux5.1` | kernel version string |

## 2. Flash layout (SPI NAND, 128 MB total)

The updater script embedded at offset 512 of `miyoo355_fw.img` is explicit:

| Image offset | Size | Target | Contents |
|---|---|---|---|
| 0 | 512 B | — | `model:` / `version:` header |
| 512 | ~3.5 KB | — | `/bin/sh` flashing script |
| 1 MB | 7 MB | `/dev/mtd1` | `uboot.img` |
| 8 MB | 72 MB | `/dev/mtd2` | `boot.img` (Android bootimg) |
| 80 MB | 48 MB | `/dev/mtd3` | `rootfs.img` (squashfs, read-only) |

It flashes with `flash_erase` + `dd` to raw MTD character devices. **There is
no A/B slot and no verification step.** A bad write to `mtd1` is an unbootable
device recoverable only over USB maskrom or SPI flash clip.

Runtime mounts (`/etc/fstab`): `PARTLABEL=oem → /oem`, `PARTLABEL=userdata →
/userdata` (both ext4). `/data` is a symlink to `/userdata`.

## 3. Stock software stack

| Component | Version |
|---|---|
| Bootloader | U-Boot **2017.09** (built 2025-05-27), Rockchip fork |
| Kernel | Linux **5.10.160** SMP, built 2025-05-26 (`#152`) |
| Userland | **Buildroot 2021.11**, `rockchip_rk3566_defconfig` |
| libc | **glibc 2.36** (not musl, not uClibc) |
| init | BusyBox SysV-style `/etc/init.d/S*` |
| Root fs | squashfs v4.0, zlib, **read-only**, 3847 inodes |

`glibc 2.36` matters: Debian arm64 binaries (bookworm = 2.36, trixie = 2.41)
are ABI-compatible enough that a **chroot works without recompiling anything**.

Already present in the stock rootfs and useful to us: `bash`, `curl`, `dropbear`
(SSH), `hostapd`, `wpa_supplicant`, `dnsmasq`, `udhcpd`, `iproute2` (`ip`, `tc`),
`iptables`-era tooling, `parted`, `e2fsprogs`, `lsusb`, `i2c-tools`,
`mtd-utils`, `tcpdump`-less but `AF_PACKET` is available (see §5).

## 4. Radios — the single most important finding

The stock kernel config contains exactly **one** WLAN driver:

```
CONFIG_WLAN=y
CONFIG_RTL8733BU=y        # built-in (=y), NOT a module
```

- The Wi-Fi/BT combo is a **Realtek RTL8733BU on the USB bus**, not SDIO.
  Confirmed by `lib/firmware/rtl8733bu_fw` + `rtl8733bu_config` and by
  `CONFIG_RTL8733BU=y`.
- Bluetooth is the same chip via `usr/lib/modules/rtk_btusb.ko`
  (`vermagic=5.10.160 SMP mod_unload aarch64`).
- `/usr/bin/rk_wifibt_init` is Rockchip's **runtime chip autodetect**: it walks
  `/sys/bus/usb/devices`, `/sys/bus/sdio/devices`, `/sys/bus/pci/devices`,
  matches `PRODUCT=` VID:PID, caches the answer in `/data/wifi_chip`, then
  `insmod`s the matching `.ko`. **The Flip ships more than one Wi-Fi part
  across revisions** — `/system/lib/modules/RTL8189FU.ko` (really an RTL8188FU,
  2.4 GHz 802.11n) is the alternate. `S36load_wifi_modules` hardcodes
  `insmod /system/lib/modules/RTL8188FU.ko`, a filename that does not exist in
  this image — stale vendor script.

**Consequence: detect the radio at runtime, never assume.**

*(External source — [Zetarancio's RE wiki](https://github.com/Zetarancio/Miyoo-Flip-Mainline-Linux-Reverse-Engineering))*:
the 8733bu tree only implements **software rfkill**; true power-off needs a
separate GPIO-enable driver.

## 5. Stock kernel capability audit

Extracted from the live `IKCFG_ST` blob inside the kernel image
(`research/stock-firmware/stock-kernel-5.10.160.config`, 191 KB).

### Present — usable today

| Option | Why it matters |
|---|---|
| `CONFIG_PACKET=y` | **AF_PACKET raw sockets** → tcpdump, scapy, nmap, arp tooling |
| `CONFIG_CFG80211=y`, `CONFIG_MAC80211=y` | full wireless stack is compiled in |
| `CONFIG_USB_F_HID=y` + `CONFIG_USB_CONFIGFS=y` | **USB HID gadget → BadUSB / keystroke injection** |
| `CONFIG_USB_F_MASS_STORAGE`, `F_FS`, `F_ACM` | gadget storage / FunctionFS / serial |
| `CONFIG_USB_SERIAL_{CP210X,FTDI_SIO,PL2303,OTI6858}` | **UART/serial hardware hacking adapters work out of the box** |
| `CONFIG_USB_{EHCI,OHCI,XHCI}_HCD`, `USB_STORAGE=y` | upper USB-C is a real host port |
| `CONFIG_NAMESPACES`, `USER_NS`, `PID_NS`, `NET_NS`, `CGROUPS`, `SECCOMP` | chroot / containers / nspawn viable |
| `CONFIG_OVERLAY_FS=y` | writable overlay on the read-only squashfs |
| `CONFIG_MODULES=y`, **no `MODULE_SIG`**, `MODULE_FORCE_LOAD=y` | **unsigned out-of-tree modules load freely** |
| `CONFIG_INPUT_UINPUT=y` | synthetic input injection |
| `CONFIG_ZRAM=y`, `ZSMALLOC=y` | compressed swap — essential at 1 GB RAM |
| `CONFIG_NETFILTER_XTABLES`, `IP_NF_IPTABLES`, `NETFILTER_ADVANCED` | legacy iptables |
| `CONFIG_CRYPTO_USER_API=y`, `KEYS=y`, `FTRACE=y` | AF_ALG, keyrings, tracing |

### Absent — hard blockers requiring a kernel rebuild

| Missing | What it costs you |
|---|---|
| **Any USB Wi-Fi driver except RTL8733BU** | ❌ Plug in an Alfa / ath9k_htc / MT7921AU and **nothing binds**. No external adapter works. |
| `CONFIG_TUN` | ❌ No OpenVPN, no WireGuard, no tun/tap, no most pivot tooling |
| `CONFIG_BRIDGE` | ❌ No bridging — breaks rogue-AP/evil-twin forwarding patterns |
| `CONFIG_NF_TABLES` | ❌ nftables unavailable; iptables-legacy only |
| `CONFIG_VETH`, `MACVLAN`, `VLAN_8021Q` | ❌ No veth pairs, no VLAN tagging, weak container networking |
| `CONFIG_USB_NET_*` (cdc_ether, ax88179, r8152) | ❌ No USB-to-Ethernet adapters |
| `CONFIG_USB_CONFIGFS_{ECM,RNDIS,NCM}` | ❌ No USB-ethernet **gadget** — can't plug into a laptop and get a network interface |
| `CONFIG_WIREGUARD` | ❌ No in-kernel WG |
| `RTL8733BU` is `=y` not `=m` | ❌ Can't unload the stock driver to swap in a monitor-mode-patched build |

`CONFIG_CFG80211_REQUIRE_SIGNED_REGDB=y` + `CFG80211_USE_KERNEL_REGDB_KEYS=y`
also means regulatory-domain enforcement is on and a replacement kernel must
carry a signed `regulatory.db` or channel/TX-power control will be restricted.

## 6. USB topology *(external source, matches our DTB)*

DTB confirms `usb@fd800000`, `usb@fd840000`, `rockchip,rk3568-dwc3`,
`usb2-phy@fe8a0000`/`@fe8b0000`, `usb3-host`, `usb3-otg`, `otg-port`,
`host-port`, `OTG_SWITCH`.

- **Upper USB-C — host.** EHCI/OHCI + `vcc5v0_host` VBUS. This is where
  external adapters go.
- **Lower USB-C — charge + gadget.** `dr_mode = "otg"` on the xHCI.
  **It cannot supply VBUS to a bus-powered device.**

## 7. Other verified-by-others facts

*(External source — Zetarancio RE wiki; treat as strong but unconfirmed here)*

- RAM: LPDDR4 (capacity commonly reported as 1 GB)
- Display: 640×480 MIPI DSI 2-lane RGB888, backlight on PWM4
- PMIC RK817 (+ RK8600 for VDD_CPU at I²C 0x40); RK817 audio codec
- Battery: 3.7 V / 3000 mAh / 11.1 Wh
- **Debug UART: `ttyS2` @ 1,500,000 baud, 3.3 V** — your serial lifeline
- Mainline Linux is *demonstrated* on this board (ROCKNIX fork → Zlyme):
  boot, display, audio, Wi-Fi+BT, GPU (mali_kbase + libmali), SPI NAND,
  both SD slots, HDMI, VPU/RGA, suspend

---

## 8. Measured on real hardware — 2026-11-13

Everything above §7 came from unpacking a firmware image. This section was
taken from a running Miyoo Flip over SSH. Where the two disagree, this wins.

The running kernel reports `Linux rk3566-buildroot 5.10.160 #152 SMP Mon May 26
14:30:16 CST 2025`, byte-identical to the build string in the analysed image,
so the static findings apply to this device exactly.

### The radio, settled

```
lsusb                     ID 0bda:b733
/sys/.../product          "802.11n  WLAN Adapter"
driver                    RTW (built in; only rtk_btusb is a loadable module)
```

**This unit has the RTL8733BU, not the RTL8188FU alternate.** It is on the USB
bus, confirming the kernel config.

| Capability | Result |
|---|---|
| 2.4 GHz | **14 channels** |
| 5 GHz | **28 channels** — despite the "802.11n" product string, it was associated on channel 157 at 40 MHz |
| Max TX power | 20.0 dBm advertised |
| **Monitor mode** | **NOT SUPPORTED** |
| Mesh point | not supported |
| WDS | not supported |

```
Supported interface modes:
     * IBSS      * managed      * AP
     * P2P-client               * P2P-GO

# iw phy phy1 interface add mon0 type monitor
command failed: Operation not supported (-95)
```

This is now a measured fact, not an estimate. The vendor driver does not
advertise monitor mode and the kernel refuses to create the interface. **No
amount of userland tooling changes this** — it needs a different driver, which
needs a different kernel, which is M2.

### What does work, confirmed

- **`AF_PACKET` capture on the managed interface.** `tcpdump -i wlan0` captured
  live mDNS traffic with zero dropped packets. The M1 capture claim holds.
- **ext4 is in the stock kernel** (`/proc/filesystems`), so the LimenOS root
  partition mounts natively.
- **A full Debian trixie arm64 chroot runs**: 455 packages, `uname -m` =
  `aarch64`, with `nmap`, `tcpdump`, `scapy`, `iw`, `tmux`, `binwalk` and
  `flashrom` all present and executing.
- **Root code execution from the SD card at boot** via the vendor's own
  `${CUSTOMER_DIR}/app/MainUI` hook, with the console still booting normally.

### Corrections to earlier assumptions

- **`/mnt` is read-only.** The rootfs is squashfs, so a chroot mountpoint must
  live on tmpfs (`/tmp`) or `/userdata`. `limen-chroot` defaulted to
  `/mnt/limen` and could not work.
- **Card mountpoints are not stable.** On this boot the FAT partitions landed
  on `/mnt/sdcard` and `/media/sdcard2` — not `sdcard0`/`sdcard1`. Anything
  that hunts for files by path must search, or find them by LABEL.
- **The 32 MiB FAT boot partition mounted fine under Linux** even though macOS
  refused it. Linux is lenient about the FAT32 cluster-count minimum; that is
  not a reason to ship an out-of-spec filesystem, but no device was affected.
- **The stock root password is `rockchip`**, the Rockchip BSP default, in
  firmware `20250527210639`.
