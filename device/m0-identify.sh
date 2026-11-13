#!/bin/sh
# ============================================================================
# LimenOS M0 — identify this specific Flip.
# ============================================================================
# RUN ON THE DEVICE (stock firmware). Read-only; changes nothing.
#
#   ./m0-identify.sh [> /mnt/SDCARD/limen-identify.txt]
#
# The Flip ships more than one Wi-Fi part across hardware revisions, and the
# answer changes what LimenOS can deliver. Find out which one you have before
# planning anything wireless.
# ============================================================================
set -u
sec() { echo; echo "=== $* ==="; }

echo "LimenOS M0 — device identification"
echo "generated: $(date 2>/dev/null)"

sec "board"
echo "model      : $(cat /proc/device-tree/model 2>/dev/null | tr -d '\0')"
echo "compatible : $(cat /proc/device-tree/compatible 2>/dev/null | tr -d '\0')"
echo "serial     : $(grep -i serial /proc/cpuinfo 2>/dev/null | head -1)"
echo "uname      : $(uname -a)"
echo "uptime     : $(uptime 2>/dev/null)"

sec "cpu / memory"
grep -E "^(processor|model name|Features)" /proc/cpuinfo 2>/dev/null | sort -u
grep -E "^(MemTotal|MemFree|SwapTotal)" /proc/meminfo 2>/dev/null

sec "WI-FI CHIP  <-- the one that matters"
echo "cached answer (/data/wifi_chip): $(cat /data/wifi_chip 2>/dev/null || echo '<not set>')"
echo
echo "-- USB devices (the radio is on USB, not SDIO) --"
lsusb 2>/dev/null || echo "lsusb unavailable"
echo
echo "-- USB VID:PID from sysfs --"
for d in /sys/bus/usb/devices/*; do
    [ -r "$d/idVendor" ] || continue
    printf '  %-12s %s:%s  %s\n' "$(basename "$d")" \
        "$(cat "$d/idVendor" 2>/dev/null)" "$(cat "$d/idProduct" 2>/dev/null)" \
        "$(cat "$d/product" 2>/dev/null)"
done
echo
echo "-- loaded modules --"
lsmod 2>/dev/null
echo
echo "-- kernel messages mentioning a Realtek part --"
dmesg 2>/dev/null | grep -iE "rtl|rtw|8733|8188|8189|wlan|ieee80211" | tail -25

sec "wireless interfaces"
ip link 2>/dev/null || ifconfig -a 2>/dev/null
echo
iw dev 2>/dev/null || echo "(no iw on stock — expected)"
cat /proc/net/wireless 2>/dev/null

sec "bluetooth"
hciconfig -a 2>/dev/null || echo "(hci down or absent)"

sec "MTD layout"
cat /proc/mtd 2>/dev/null

sec "block devices / cards"
cat /proc/partitions 2>/dev/null
echo
blkid 2>/dev/null
echo
df -h 2>/dev/null

sec "USB gadget capability"
echo "UDC present   : $(ls /sys/class/udc/ 2>/dev/null | tr '\n' ' ')"
echo "configfs      : $(mountpoint -q /sys/kernel/config 2>/dev/null && echo mounted || echo 'not mounted')"
echo "android state : $(cat /sys/class/android_usb/android0/state 2>/dev/null)"
echo "gadget funcs  : $(ls /sys/kernel/config/usb_gadget/rockchip/functions 2>/dev/null | tr '\n' ' ')"

sec "power"
for b in /sys/class/power_supply/*; do
    [ -d "$b" ] || continue
    echo "  $(basename "$b"): $(cat "$b/capacity" 2>/dev/null)% $(cat "$b/status" 2>/dev/null)"
done

echo
echo "=== done — save this file, it decides what M2 can deliver ==="
