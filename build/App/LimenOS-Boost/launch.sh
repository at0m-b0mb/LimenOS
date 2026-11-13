#!/bin/sh
# LimenOS launcher entry. Run as root by the stock firmware, which executes
# ${{CUSTOMER_DIR}}/App/<name>/launch.sh through /tmp/cmd_to_run.sh.
# Nothing here writes to internal flash.
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
echo "=== LimenOS Boost $(date 2>/dev/null) ==="

ONLINE=$(cat /sys/devices/system/cpu/online)
case "$ONLINE" in
  0-3)
      for c in 2 3; do echo 0 > /sys/devices/system/cpu/cpu$c/online 2>/dev/null; done
      STATE="2 cores  (factory)"; NOTE="> Battery saver"
      ;;
  *)
      for c in 2 3; do echo 1 > /sys/devices/system/cpu/cpu$c/online 2>/dev/null; done
      STATE="4 cores  (boosted)"; NOTE="> 2.26x on parallel work"
      ;;
esac
sleep 1
show --title "CPU" --footer "> Press a button to return" \
  "$NOTE" \
  "" \
  "now       $STATE" \
  "online    $(cat /sys/devices/system/cpu/online)" \
  "clock     $(( $(cat /sys/devices/system/cpu/cpu0/cpufreq/scaling_cur_freq)/1000 )) MHz" \
  "soc       $(( $(cat /sys/class/thermal/thermal_zone0/temp)/1000 ))C" \
  "battery   $(cat /sys/class/power_supply/battery/capacity)%" \
  "" \
  "Single-thread speed is unchanged." \
  "Run this again to switch back." \


# wait for a button, so the screen can actually be read; cap it so a wedged
# input device cannot strand the launcher
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
