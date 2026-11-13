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
echo "=== LimenOS Deck $(date 2>/dev/null) ==="

# cores up, zram on, ssh up, and mount the LimenOS card if it is in a slot
for c in 2 3; do echo 1 > /sys/devices/system/cpu/cpu$c/online 2>/dev/null; done
pgrep dropbear >/dev/null 2>&1 || /etc/init.d/S50dropbear start >/dev/null 2>&1

ROOTDEV=$(blkid 2>/dev/null | sed -n 's|^\([^:]*\):.*LABEL="LIMEN_ROOT".*|\1|p' | head -1)
MNT=/tmp/limen
STATE="not inserted"
if [ -n "$ROOTDEV" ]; then
    mkdir -p $MNT
    mountpoint -q $MNT || mount -t ext4 "$ROOTDEV" $MNT 2>/dev/null
    if mountpoint -q $MNT; then
        for m in proc sys dev dev/pts run; do mkdir -p $MNT/$m; done
        mountpoint -q $MNT/proc    || mount -t proc proc $MNT/proc 2>/dev/null
        mountpoint -q $MNT/sys     || mount -t sysfs sysfs $MNT/sys 2>/dev/null
        mountpoint -q $MNT/dev     || mount --bind /dev $MNT/dev 2>/dev/null
        mountpoint -q $MNT/dev/pts || mount -t devpts devpts $MNT/dev/pts 2>/dev/null
        mountpoint -q $MNT/run     || mount -t tmpfs tmpfs $MNT/run 2>/dev/null
        cp /etc/resolv.conf $MNT/etc/resolv.conf 2>/dev/null
        [ -x $MNT/usr/local/bin/limen-zram ] && \
            chroot $MNT /usr/local/bin/limen-zram on 768 >/dev/null 2>&1
        STATE="mounted at $MNT"
    else
        STATE="found but would not mount"
    fi
fi
IP=$(ip -4 addr show wlan0 2>/dev/null | awk '/inet /{print $2}' | cut -d/ -f1 | head -1)
"$SAY" --title "Deck" \
  "> Ready" \
  "" \
  "ssh root@${IP:-<no wifi>}" \
  "" \
  "cores     $(cat /sys/devices/system/cpu/online)" \
  "swap      $(awk '/SwapTotal/{printf "%d MB", $2/1024}' /proc/meminfo)" \
  "limen sd  $STATE" \
  "" \
  "Then:  chroot /tmp/limen /bin/bash -l" \
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
