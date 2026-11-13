#!/bin/sh
# LimenOS launcher entry, run as root by the stock firmware through
# /tmp/cmd_to_run.sh. Writes nothing to internal flash.
PROGDIR=$(dirname "$0")
cd "$PROGDIR" || exit 1
echo 1 > /tmp/stay_awake 2>/dev/null
SAY="$PROGDIR/limen-say"
[ -x "$SAY" ] || SAY=/bin/true
exec >>/tmp/limen-app.log 2>&1
echo "=== LimenOS Neighbours $(date 2>/dev/null) ==="

need() {   # need <binary> ; echo the path or empty, and record what is absent
  p=$(command -v "$1" 2>/dev/null)
  if [ -n "$p" ]; then echo "$p"; else MISSING="$MISSING $1"; fi
}
MISSING=""


IP=$(ip -4 addr show wlan0 2>/dev/null | awk '/inet /{print $2}' | head -1)
NET=$(echo "$IP" | cut -d. -f1-3)
set --
if [ -z "$NET" ]; then
    set -- "> Not connected to Wi-Fi" "" "Join a network first, in Settings."
else
    # a bounded sweep: this is your own subnet, and it is only ARP/ICMP
    i=1
    while [ $i -le 254 ]; do
        ping -c 1 -W 1 "$NET.$i" >/dev/null 2>&1 &
        i=$((i+1))
        [ $((i % 64)) -eq 0 ] && wait
    done
    wait
    HOSTS=$(ip neigh 2>/dev/null | grep -v FAILED | awk '{printf "%-16s %s\n", $1, $5}' | head -12)
    N=$(echo "$HOSTS" | grep -c .)
    set -- "> $N devices seen on $NET.0/24" "" "this device   $IP" ""
    OLDIFS=$IFS; IFS="
"
    for l in $HOSTS; do set -- "$@" "$l"; done
    IFS=$OLDIFS
fi
"$SAY" --title "Neighbours" "$@" "" "> Press a button to return"


( sleep 60; kill -TERM $$ 2>/dev/null ) & WATCH=$!
dd if=/dev/input/event5 bs=16 count=4 >/dev/null 2>&1 || sleep 6
kill $WATCH 2>/dev/null

rm -f /tmp/stay_awake 2>/dev/null
exit 0
