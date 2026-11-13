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
echo "=== LimenOS Ports $(date 2>/dev/null) ==="

need() {   # need <binary> ; echo the path or empty, and record what is absent
  p=$(command -v "$1" 2>/dev/null)
  if [ -n "$p" ]; then echo "$p"; else MISSING="$MISSING $1"; fi
}
MISSING=""


SER=$(ls /dev/ttyUSB* /dev/ttyACM* 2>/dev/null | tr '\n' ' ')
USBN=$(lsusb 2>/dev/null | grep -vc "1d6b:")
LISTEN=$(netstat -ltn 2>/dev/null | awk 'NR>2{print $4}' | sed 's/.*://' | sort -un | tr '\n' ' ')
set -- "> Hardware and exposure" "" \
  "usb devices   ${USBN:-0} (excluding root hubs)" \
  "serial        ${SER:-none attached}" \
  "listening     ${LISTEN:-none}" ""
OLDIFS=$IFS; IFS="
"
for l in $(lsusb 2>/dev/null | grep -v "1d6b:" | cut -c1-44 | head -6); do
    set -- "$@" "$l"
done
IFS=$OLDIFS
set -- "$@" "" \
  "CP210x, FTDI and PL2303 adapters work" \
  "on the UPPER port. CH340 does not:" \
  "this kernel has no ch341 driver."
show --title "Ports" --footer "> Press a button to return" "$@" 


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
