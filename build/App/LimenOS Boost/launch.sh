#!/bin/sh
# LimenOS launcher entry. Run as root by the stock firmware, which executes
# ${CUSTOMER_DIR}/App/<name>/launch.sh through /tmp/cmd_to_run.sh.
# Nothing here writes to internal flash.
PROGDIR=$(dirname "$0")
cd "$PROGDIR" || exit 1
echo 1 > /tmp/stay_awake 2>/dev/null
SAY="$PROGDIR/limen-say"
[ -x "$SAY" ] || SAY=/usr/bin/true
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
"$SAY" --title "CPU" \
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
  "" \
  "> Press a button to return"


# wait for a button, so the screen can actually be read; cap it so a wedged
# input device cannot strand the launcher
( sleep 45; kill -TERM $$ 2>/dev/null ) &
WATCH=$!
dd if=/dev/input/event5 bs=16 count=4 >/dev/null 2>&1 || sleep 5
kill $WATCH 2>/dev/null

rm -f /tmp/stay_awake 2>/dev/null
exit 0
