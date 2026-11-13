#!/bin/sh
# LimenOS launcher entry, run as root by the stock firmware through
# /tmp/cmd_to_run.sh. Writes nothing to internal flash.
PROGDIR=$(dirname "$0")
cd "$PROGDIR" || exit 1
echo 1 > /tmp/stay_awake 2>/dev/null
SAY="$PROGDIR/limen-say"
[ -x "$SAY" ] || SAY=/bin/true
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
"$SAY" --title "Ports" "$@" "" "> Press a button to return"


( sleep 60; kill -TERM $$ 2>/dev/null ) & WATCH=$!
dd if=/dev/input/event5 bs=16 count=4 >/dev/null 2>&1 || sleep 6
kill $WATCH 2>/dev/null

rm -f /tmp/stay_awake 2>/dev/null
exit 0
