# LimenOS — Roadmap

Four milestones. **Each one is independently useful** — if the project stops
after any of them you still have a working device, and no milestone can brick
the Flip because the NAND is never written.

---

## M0 — Safety net & recon *(do this before anything else)*

Nothing is built. The point is that every later step is reversible.

1. **Dump your own NAND.** Boot stock, get a shell, `nanddump` all of
   `/dev/mtd0..3` to an SD card. The vendor `miyoo355_fw.img` is *not* a
   substitute — it has no `mtd0` (idbloader/bl31/OP-TEE) and no `userdata`.
2. **Find the UART pads.** `ttyS2`, 1,500,000 baud, 3.3 V. **You cannot debug a
   non-booting kernel without this.**
   ⚠️ **Use a CP2102 or FT232 — a CH340 will not work.**
   `CONFIG_USB_SERIAL_CH341` is absent from the stock kernel, and CH340 is the
   most common cheap adapter. Stock binds CP210x / FTDI / PL2303 / OTI6858 /
   Keyspan only. Also check your adapter does 1.5 Mbaud — many CH340s don't.
3. **Identify your radio.** On stock: `cat /data/wifi_chip`, `lsusb`,
   `dmesg | grep -i rtl`. Record whether you have the RTL8733BU or the
   RTL8188FU — it changes what M2 can deliver.
4. **Confirm SD boot order.** Verify the BootROM/U-Boot picks a card over NAND
   on *your* unit before trusting dual-boot.

**Done when:** you have a full NAND image on your laptop, a serial console, and
a known radio part.

---

## M1 — "Limen Lite": Debian chroot on the stock kernel

Zero kernel work. Runs on the firmware you already have. Ships in days.

- Debian `trixie` arm64 rootfs on SD partition 2, entered by `chroot` (or
  `systemd-nspawn` — `USER_NS`/`PID_NS`/`NET_NS`/`SECCOMP` are all `=y`).
- Overlay a writable layer on the read-only squashfs via `CONFIG_OVERLAY_FS=y`.
- ZRAM up immediately — 1 GB is not enough without it.

**What genuinely works at M1** (all backed by `CONFIG_PACKET=y`,
`USB_F_HID=y`, `USB_SERIAL_*=y`):

- Packet capture and analysis — `tcpdump`, `tshark`, `scapy`
- Network scanning — `nmap`, `masscan`, ARP/LLMNR/mDNS tooling
- **BadUSB / HID keystroke injection** over the lower USB-C (`USB_F_HID=y` +
  `USB_CONFIGFS=y`) — the P4wnP1 trick, on hardware you already own
- **Hardware & UART work** — CP210x/FTDI/PL2303/OTI6858 adapters bind on the
  upper port today. Serial console tapping, baud hunting, flash dumping
- Web/app testing — `sqlmap`, `ffuf`, `nikto`, `mitmproxy` (no TUN, so
  transparent interception is limited to what `iptables` REDIRECT gives you)
- Local AP — `hostapd` + `dnsmasq` are already in the stock rootfs

**What does not work at M1:** external Wi-Fi adapters, monitor mode, injection,
VPN, nftables, bridging, USB-Ethernet. See `docs/04`.

**Done when:** `ssh` into a Debian shell on the Flip over the internal Wi-Fi,
`apt install` succeeds, a HID gadget payload types into a laptop.

---

## M2 — "Limen": the deck kernel *(the real work)*

Replace the kernel; keep the card layout. This is where it becomes a cyberdeck.

1. **Pick the tree.** Start from the lineage that already boots this board —
   the archived ROCKNIX Flip fork → [Zlyme](https://github.com/Zetarancio).
   Our extracted `miyoo355-v10.dtb` is the reference for what the BSP enables.
2. **Apply the LimenOS deck config** (`kernel/limen-deck.config`): TUN,
   BRIDGE, VETH, VLAN, NF_TABLES, WIREGUARD, the full USB Wi-Fi driver set
   (`ath9k_htc`, `mt76x2u`, `mt7921u`, `rt2800usb`, `carl9170`, `rtl8xxxu`),
   USB-Ethernet (`cdc_ether`, `ax88179_178a`, `r8152`), and gadget
   `ECM`/`NCM`/`RNDIS`.
3. **Build RTL8733BU as `=m`**, so a monitor-mode-patched build can replace it.
4. **Out-of-tree injection drivers**: morrownr `88x2bu`/`8812au`, and the
   libc0607 `rtl8733bu` fork. Modules load unsigned —
   `CONFIG_MODULE_SIG` is absent and `MODULE_FORCE_LOAD=y`.
5. **Keep a known-good M1 card** in your pocket while M2 is unstable.

**Done when:** an external adapter enters monitor mode, `aireplay-ng
--test` passes, and the Flip appears as a network interface when plugged into a
laptop.

---

## M3 — The deck UX

The part every handheld-pentest project skips, and the reason they all end up
unused.

- **640×480 TUI launcher**, D-pad + ABXY only, font sized to actually read at
  3.5". Pick interface → pick action → watch output.
- **On-screen keyboard** for the rare SSID/passphrase.
- **tmux session manager** so a capture survives closing the lid.
- **One-button gadget mode**: plug into a laptop, get `ssh limen.local`.
- **Capture vault** on the exFAT partition — pull the card, read it anywhere.
- **Stock-OS launcher entry** so LimenOS is reachable from the games menu.

---

## M4 — Polish *(optional)*

Battery/thermal telemetry, suspend-with-capture-running, signed releases,
reproducible card images, an updater that is *not* the vendor's `dd`-to-MTD.
