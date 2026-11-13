#!/bin/sh
# LimenOS launcher entry, run as root by the stock firmware through
# /tmp/cmd_to_run.sh. Writes nothing to internal flash.
PROGDIR=$(dirname "$0")
cd "$PROGDIR" || exit 1
echo 1 > /tmp/stay_awake 2>/dev/null
SAYBIN="$PROGDIR/limen-say"
PNG=/tmp/limen-screen.png
FBPID=""
# Render to a PNG and display it with the vendor's own fbdisplay.
#
# Writing straight to /dev/fb0 is NOT reliably visible: MainUI composites
# through DRM and its plane sits above the fbdev emulation, so the pixels can
# land where the panel never shows them. fbdisplay is the path the firmware
# itself uses for its loading screen, so it is the one that works. It runs
# until /tmp/fbdisplay_exit appears, which is how runmiyoo.sh stops it.
show() {
  [ -x "$SAYBIN" ] || return 1
  rm -f /tmp/fbdisplay_exit 2>/dev/null
  "$SAYBIN" --png "$PNG" "$@" || return 1
  fbdisplay "$PNG" >/dev/null 2>&1 &
  FBPID=$!
}
hide() {
  touch /tmp/fbdisplay_exit 2>/dev/null
  sleep 1
  [ -n "$FBPID" ] && kill "$FBPID" 2>/dev/null
  rm -f /tmp/fbdisplay_exit 2>/dev/null
}
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
show --title "USB HID" --footer "> Press a button to return" "$@" "" "> Run again to toggle"


# Hold the screen until a button is pressed.
# struct input_event is 24 bytes on this 64-bit kernel, not 16, and a single
# press emits several events, so drain whatever is already queued first and
# then block for a fresh one. Without the drain the screen flashed past
# before it could be read.
( sleep 90; kill -TERM $$ 2>/dev/null ) & WATCH=$!
dd if=/dev/input/event5 iflag=nonblock of=/dev/null bs=24 count=64 2>/dev/null
dd if=/dev/input/event5 bs=24 count=2 >/dev/null 2>&1 || sleep 8
kill $WATCH 2>/dev/null
hide

rm -f /tmp/stay_awake 2>/dev/null
exit 0
