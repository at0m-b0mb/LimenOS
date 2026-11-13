# LimenOS — Quickstart

What to actually do, in order. Nothing here writes to the Flip's internal
flash at any point.

---

## Before you start: one cable

A **CP2102 or FT232** USB-UART. **Not a CH340** — `CONFIG_USB_SERIAL_CH341`
is absent from the stock kernel, and CH340 is the commonest cheap adapter.
Check it can do 1,500,000 baud; many can't.

```
Flip debug UART:  ttyS2 @ 1500000 8N1, 3.3 V
```

You can do M1 without it. You cannot debug M2 without it.

---

## M0 — safety net (do this first, every time)

Get a shell on the stock firmware. Dropbear is already running, so once the
Flip is on your Wi-Fi:

```bash
ssh root@<flip-ip>
```

Copy the two M0 scripts to the SD card, then on the device:

```bash
sh /mnt/SDCARD/m0-identify.sh > /mnt/SDCARD/limen-identify.txt
```

Read it. The line that matters is **which Wi-Fi part you have** — RTL8733BU or
RTL8188FU. It changes what M2 can deliver, and the Flip ships both across
revisions.

Then the backup:

```bash
sh /mnt/SDCARD/m0-dump-nand.sh /mnt/SDCARD/limen-backup
```

This dumps every MTD partition with a SHA-256 manifest. **Then copy it off the
card onto a real machine.** A backup that only exists on the card inside the
device is not a backup.

> Your vendor `miyoo355_fw.img` is *not* a substitute: it contains no `mtd0`
> (idbloader / bl31 / OP-TEE) and no `userdata`.

---

## Try it before you build anything: BadUSB on stock firmware

This needs **no custom firmware at all**. It works on the Miyoo firmware you
have right now, because the stock kernel ships `CONFIG_USB_CONFIGFS_F_HID=y`
and Rockchip's own `usbdevice` already defines a HID function.

Copy `device/limen-hid` to the device, then:

```bash
limen-hid enable          # -> /dev/hidg0
limen-hid status
```

Plug the **lower** USB-C into a laptop, open a text editor on it, and:

```bash
limen-hid type "hello from a games console"
limen-hid key GUI r
```

To run a Ducky script you must arm it explicitly — keystroke injection is an
active attack and shouldn't be one typo away:

```bash
limen-hid run /mnt/SDCARD/payload.ducky --arm
```

When you're done:

```bash
limen-hid disable         # restores the stock gadget
```

The keymap is verified: `tests/test-hid-keymap.py` decodes the emitted HID
reports with an independently written table and checks all 95 printable ASCII
characters plus modifier combinations round-trip correctly.

---

## M1 — build the LimenOS card

On your Mac (needs Docker; `colima start` if it isn't running):

```bash
./build/00-workspace.sh
```

```bash
./build/10-build-rootfs.sh
```

```bash
./build/11-make-card.sh
```

That produces `out/limen-card.img`. Write it yourself — the script never
touches a device node:

```bash
diskutil list
```

```bash
diskutil unmountDisk /dev/diskN && sudo dd if=out/limen-card.img of=/dev/rdiskN bs=4m status=progress
```

Copy `device/limen-chroot` onto the stock side, insert the card, and:

```bash
limen-chroot
```

You're in Debian arm64 on a Miyoo Flip. First two things:

```bash
limen-zram on
```

```bash
limen-radio
```

`limen-radio` tells you honestly what the radios can do rather than implying
monitor mode works.

To capture, use the wrapper — it enforces rotation so a FAT32 4 GB limit or a
full card can't silently truncate your evidence:

```bash
limen-capture wlan0
```

Leaving:

```bash
exit
```

```bash
limen-chroot --umount
```

---

## What works at M1, honestly

| ✅ Works | ❌ Doesn't (needs M2) |
|---|---|
| tcpdump / tshark / scapy / nmap / masscan | any external USB Wi-Fi adapter |
| **BadUSB / HID injection** | monitor mode, injection |
| **CP210x / FTDI / PL2303 serial & UART work** | VPN, WireGuard, TUN |
| sqlmap / ffuf / gobuster / nikto | nftables, bridging, NAT |
| Bluetooth scanning | USB-Ethernet either direction |
| hostapd / dnsmasq AP | exFAT (FAT32 only, 4 GB/file) |
| forensics, binwalk, flashrom, openocd | CH340 serial adapters |

Full reasoning: [04-constraints.md](04-constraints.md).

---

## If something goes wrong

- **Card won't mount** — `blkid` on stock; the script looks for the label
  `LIMEN_ROOT`, not a device path, so it survives slot changes.
- **`/dev/hidg0` never appears** — read `/tmp/usbdevice.log`. Check
  `ls /sys/class/udc/` is non-empty; if it is empty the OTG port isn't in
  peripheral mode.
- **OOM kills** — `limen-zram on` first, every session. 1 GB is not enough
  without it.
- **Device won't boot at all** — this is why you did M0. Serial console,
  then restore from your NAND dump.
