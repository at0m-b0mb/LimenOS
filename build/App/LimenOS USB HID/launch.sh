#!/bin/sh
# LimenOS launcher entry, run as root by the stock firmware through
# /tmp/cmd_to_run.sh. Writes nothing to internal flash.
PROGDIR=$(dirname "$0")
cd "$PROGDIR" || exit 1
echo 1 > /tmp/stay_awake 2>/dev/null
SAY="$PROGDIR/limen-say"
[ -x "$SAY" ] || SAY=/bin/true
exec >>/tmp/limen-app.log 2>&1
echo "=== LimenOS USB HID $(date 2>/dev/null) ==="

need() {   # need <binary> ; echo the path or empty, and record what is absent
  p=$(command -v "$1" 2>/dev/null)
  if [ -n "$p" ]; then echo "$p"; else MISSING="$MISSING $1"; fi
}
MISSING=""


# Arms the HID gadget only. It types nothing: sending keystrokes is a
# deliberate, separate act over SSH with limen-hid and an explicit --arm.
CFG=/tmp/.usb_config
if [ -e /dev/hidg0 ]; then
    echo "usb_adb_en" > "$CFG"
    usbdevice restart >/dev/null 2>&1
    sleep 2
    set -- "> Disarmed" "" \
      "The USB keyboard gadget is off and" \
      "the port is back to its normal mode."
else
    echo "usb_hid_en" > "$CFG"
    usbdevice restart >/dev/null 2>&1 || usbdevice start >/dev/null 2>&1
    n=0; while [ $n -lt 12 ] && [ ! -e /dev/hidg0 ]; do n=$((n+1)); sleep 1; done
    if [ -e /dev/hidg0 ]; then
        set -- "> Armed  -  /dev/hidg0" "" \
          "report   $(cat /sys/kernel/config/usb_gadget/rockchip/functions/hid.usb0/report_length 2>/dev/null) bytes" \
          "udc      $(cat /sys/kernel/config/usb_gadget/rockchip/UDC 2>/dev/null)" \
          "state    $(cat /sys/class/android_usb/android0/state 2>/dev/null)" "" \
          "Plug the LOWER USB-C into the target." \
          "It will appear as a keyboard, and will" \
          "type NOTHING until you tell it to." "" \
          "Only use this on machines you own or" \
          "are authorised to test."
    else
        set -- "> Could not arm it" "" "/dev/hidg0 never appeared." "See /tmp/usbdevice.log"
    fi
fi
"$SAY" --title "USB HID" "$@" "" "> Run again to toggle"


( sleep 60; kill -TERM $$ 2>/dev/null ) & WATCH=$!
dd if=/dev/input/event5 bs=16 count=4 >/dev/null 2>&1 || sleep 6
kill $WATCH 2>/dev/null

rm -f /tmp/stay_awake 2>/dev/null
exit 0
