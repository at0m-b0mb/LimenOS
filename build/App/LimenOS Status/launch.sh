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
echo "=== LimenOS Status $(date 2>/dev/null) ==="

IP=$(ip -4 addr show wlan0 2>/dev/null | awk '/inet /{print $2}' | cut -d/ -f1 | head -1)
CARD=$(blkid 2>/dev/null | grep -c LIMEN_ROOT)
"$SAY" --title "Status" \
  "> $(tr -d '\0' < /proc/device-tree/model 2>/dev/null)" \
  "" \
  "kernel    $(uname -r)" \
  "cores     $(cat /sys/devices/system/cpu/online) of $(cat /sys/devices/system/cpu/present)" \
  "clock     $(( $(cat /sys/devices/system/cpu/cpu0/cpufreq/scaling_cur_freq)/1000 )) MHz" \
  "soc       $(( $(cat /sys/class/thermal/thermal_zone0/temp)/1000 ))C" \
  "gpu       $(( $(cat /sys/class/thermal/thermal_zone1/temp)/1000 ))C" \
  "battery   $(cat /sys/class/power_supply/battery/capacity)%  $(cat /sys/class/power_supply/battery/status)" \
  "memory    $(awk '/MemAvailable/{printf "%d MB free", $2/1024}' /proc/meminfo)" \
  "swap      $(awk '/SwapTotal/{printf "%d MB", $2/1024}' /proc/meminfo)" \
  "wifi      ${IP:-not connected}" \
  "ssh       $(pgrep dropbear >/dev/null 2>&1 && echo running || echo stopped)" \
  "limen sd  $([ "$CARD" -gt 0 ] && echo present || echo not inserted)" \
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
