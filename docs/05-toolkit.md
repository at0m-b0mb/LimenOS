# LimenOS — Toolkit

Chosen against the silicon (`docs/04`), not copied from a Kali metapackage.
Rule: **if it needs a GPU or 8 GB of RAM, it doesn't ship.** This deck
captures, parses, scans, proxies and reports; heavy compute leaves the device.

`✅` works at M1 (stock kernel) · `🔑` needs the M2 deck kernel

## Core / always

```
tmux  zsh  vim  git  curl  wget  jq  ripgrep  fzf  htop  ncdu  pv
python3  python3-pip  python3-venv  build-essential  bc
zram-tools  rsync  screen  socat  netcat-openbsd
```

## Network recon ✅

```
nmap  masscan  arp-scan  netdiscover  dnsutils  whois  traceroute
tcpdump  tshark  termshark  ngrep  iftop  nload  mtr
python3-scapy  impacket-scripts  netexec
```
`AF_PACKET=y` on the stock kernel is what makes all of this work at M1.

## Wireless 🔑

```
aircrack-ng  kismet  hcxdumptool  hcxtools  wifite  bettercap
hostapd  dnsmasq  iw  wireless-tools  reaver  bully  mdk4
```
`hostapd` + `dnsmasq` are already in the stock rootfs. Everything that needs
**monitor mode or injection needs M2** and realistically an external adapter —
see the honesty note on the internal RTL8733BU in `docs/04`.

## Bluetooth / BLE ✅ (scan) 🔑 (some)

```
bluez  bluez-tools  btscanner  python3-bluepy  gattool  ubertooth(-host only)
```
`rtk_btusb.ko` gives you the internal radio at M1. Ubertooth needs its own
hardware on the upper port.

## Web & application ✅

```
sqlmap  ffuf  gobuster  nikto  whatweb  wafw00f  dirb
mitmproxy  burpsuite(headless/community via jre)  wpscan  nuclei
```
Without `TUN` at M1, transparent interception is limited to `iptables REDIRECT`.
Full proxying behaviour arrives with M2.

## Hardware / RF / serial ✅ *(this is where the Flip is genuinely strong)*

```
minicom  picocom  screen  flashrom  avrdude  openocd  sigrok-cli
binwalk  squashfs-tools  mtd-utils  i2c-tools  spi-tools  can-utils
```
CP210x, FTDI, PL2303 and OTI6858 all bind on the **upper** port on the stock
kernel. A handheld with a real host port, native serial drivers and a 1.5 Mbaud
debug UART is a better hardware-hacking tool than it is a Wi-Fi tool.

## Gadget / physical ✅

```
# USB HID keystroke injection — CONFIG_USB_F_HID=y + CONFIG_USB_CONFIGFS=y
limen-hid     (configfs HID gadget, Ducky-script compatible)
limen-storage (configfs mass-storage gadget)
limen-net     🔑 ECM/NCM/RNDIS gadget — the "ssh limen.local" link
```

## Analysis / offline

```
hashid  hash-identifier  john(CPU, small lists only)  cewl  crunch(bounded)
exiftool  foremost  testdisk  sleuthkit  yara
```
**No `hashcat`.** `docs/04` explains why: there is no usable GPU compute path on
Mali-G52, and CPU cracking on 4× A55 is measured in weeks. Ship handshakes off
the device.

## Deliberately excluded

| Excluded | Reason |
|---|---|
| `hashcat`, large GPU tooling | no OpenCL path on Mali-G52 |
| `metasploit-framework` | ~2 GB, Ruby, thrashes 1 GB RAM. Run it on your laptop and pivot. |
| Large wordlists (`rockyou+`) | put them on the exFAT partition, not in the image |
| Jammers / deauth-flood "stress" modes | illegal spectrum interference, not testing |
| Any unattended attack mode | see `SCOPE.md` |

## Repository layout

Debian `trixie` arm64 as the base, with the Kali repo **pinned low** so it
supplies only the security packages and never replaces Debian's libc or
toolchain:

```
# /etc/apt/preferences.d/kali
Package: *
Pin: release o=Kali
Pin-Priority: 100
```

Pinning this way is what stops a `dist-upgrade` from quietly swapping your base
system out from under a kernel you built by hand.
