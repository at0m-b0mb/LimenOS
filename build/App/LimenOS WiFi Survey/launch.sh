#!/bin/sh
# LimenOS launcher entry, run as root by the stock firmware through
# /tmp/cmd_to_run.sh. Writes nothing to internal flash.
PROGDIR=$(dirname "$0")
cd "$PROGDIR" || exit 1
echo 1 > /tmp/stay_awake 2>/dev/null
SAY="$PROGDIR/limen-say"
[ -x "$SAY" ] || SAY=/bin/true
exec >>/tmp/limen-app.log 2>&1
echo "=== LimenOS WiFi Survey $(date 2>/dev/null) ==="

need() {   # need <binary> ; echo the path or empty, and record what is absent
  p=$(command -v "$1" 2>/dev/null)
  if [ -n "$p" ]; then echo "$p"; else MISSING="$MISSING $1"; fi
}
MISSING=""


WPA=$(need wpa_cli)
LINES=""
if [ -n "$WPA" ]; then
    wpa_cli -i wlan0 scan >/dev/null 2>&1
    sleep 3
    LINES=$(wpa_cli -i wlan0 scan_results 2>/dev/null | tail -n +2 | \
        awk '{sig=$3; sec="open"; if ($0 ~ /WPA3/) sec="WPA3"; else if ($0 ~ /WPA2/) sec="WPA2";
              else if ($0 ~ /WPA/) sec="WPA"; else if ($0 ~ /WEP/) sec="WEP";
              name=""; for(i=5;i<=NF;i++) name=name (i>5?" ":"") $i;
              if (name=="") name="<hidden>";
              printf "%-22.22s %4s dBm  %s\n", name, sig, sec}' | sort -k2 -rn | head -11)
fi
set --
if [ -z "$WPA" ]; then
    set -- "> wpa_cli is not on this firmware" "" \
           "Wi-Fi scanning needs it. The LimenOS" \
           "card carries iw and a full toolkit."
elif [ -z "$LINES" ]; then
    set -- "> No networks returned" "" "The radio may be off, or the scan" "found nothing. Try again."
else
    set -- "> $(echo "$LINES" | wc -l) networks" ""
    OLDIFS=$IFS; IFS="
"
    for l in $LINES; do set -- "$@" "$l"; done
    IFS=$OLDIFS
    set -- "$@" "" "WEP and open networks are the ones" "worth fixing on your own kit."
fi
"$SAY" --title "WiFi Survey" "$@" "" "> Press a button to return"


( sleep 60; kill -TERM $$ 2>/dev/null ) & WATCH=$!
dd if=/dev/input/event5 bs=16 count=4 >/dev/null 2>&1 || sleep 6
kill $WATCH 2>/dev/null

rm -f /tmp/stay_awake 2>/dev/null
exit 0
