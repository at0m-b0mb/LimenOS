#!/bin/sh
# LimenOS launcher entry, run as root by the stock firmware through
# /tmp/cmd_to_run.sh. Writes nothing to internal flash.
PROGDIR=$(dirname "$0")
cd "$PROGDIR" || exit 1
echo 1 > /tmp/stay_awake 2>/dev/null
SAY="$PROGDIR/limen-say"
[ -x "$SAY" ] || SAY=/bin/true
exec >>/tmp/limen-app.log 2>&1
echo "=== LimenOS Audit $(date 2>/dev/null) ==="

need() {   # need <binary> ; echo the path or empty, and record what is absent
  p=$(command -v "$1" 2>/dev/null)
  if [ -n "$p" ]; then echo "$p"; else MISSING="$MISSING $1"; fi
}
MISSING=""


# Looks only at this device. No network is touched.
ROOTPW=$(awk -F: '$1=="root"{print ($2==""?"EMPTY":"set")}' /etc/shadow 2>/dev/null)
SSHON=$(pgrep dropbear >/dev/null 2>&1 && echo "running" || echo "stopped")
KEYS=$([ -f /root/.ssh/authorized_keys ] && echo "installed" || echo "none")
TELNET=$(pgrep telnetd >/dev/null 2>&1 && echo "RUNNING - turn this off" || echo "off")
LISTEN=$(netstat -ltn 2>/dev/null | awk 'NR>2' | wc -l)
HIDG=$([ -e /dev/hidg0 ] && echo "ARMED" || echo "off")
"$SAY" --title "Audit" \
  "> This device, checked against itself" \
  "" \
  "root password   $ROOTPW" \
  "ssh (dropbear)  $SSHON" \
  "ssh keys        $KEYS" \
  "telnetd         $TELNET" \
  "listening ports $LISTEN" \
  "usb hid gadget  $HIDG" \
  "cores online    $(cat /sys/devices/system/cpu/online)" \
  "" \
  "The stock root password is a vendor" \
  "default and is widely known. Anyone on" \
  "your network can reach this device over" \
  "SSH while it is powered on." \
  "" \
  "> Press a button to return"


( sleep 60; kill -TERM $$ 2>/dev/null ) & WATCH=$!
dd if=/dev/input/event5 bs=16 count=4 >/dev/null 2>&1 || sleep 6
kill $WATCH 2>/dev/null

rm -f /tmp/stay_awake 2>/dev/null
exit 0
