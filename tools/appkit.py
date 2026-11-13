#!/usr/bin/env python3
"""
LimenOS appkit — build the launcher entries that appear in the Flip's menu.

    python3 tools/appkit.py [outdir]      default: build/App

The stock launcher runs ${CUSTOMER_DIR}/App/<Name>/<launch> as root, via
/tmp/cmd_to_run.sh. Each entry here is a shell script plus an icon; none of
them modify the card, and deleting a folder removes the entry.
"""
from __future__ import annotations
import json, os, sys
from PIL import Image, ImageDraw, ImageFont

PAPER   = (243, 241, 236, 255)
SURFACE = (255, 255, 255, 255)
INK     = (27, 24, 19, 255)
RULE    = (220, 214, 201, 255)
BRASS   = (122, 93, 24, 255)
SERIF   = "/System/Library/Fonts/Supplemental/Iowan Old Style.ttc"
SS, ICON = 4, 81


def icon(path, letter, filled):
    s = ICON * SS
    img = Image.new("RGBA", (s, s), (0, 0, 0, 0))
    d = ImageDraw.Draw(img)
    r = int(s * 0.22)
    if filled:
        d.rounded_rectangle([0, 0, s - 1, s - 1], radius=r, fill=BRASS)
        fg = PAPER
    else:
        d.rounded_rectangle([0, 0, s - 1, s - 1], radius=r,
                            fill=SURFACE, outline=RULE, width=max(2, int(s * 0.02)))
        fg = INK
    # the threshold mark: two jambs and a heavy sill, open at the head
    post = max(2, int(s * 0.055))
    sill = max(3, int(s * 0.098))
    left, right = s * 0.33, s * 0.67
    top, sy = s * 0.20, s * 0.60
    d.rectangle([left - post, top, left, sy], fill=fg)
    d.rectangle([right, top, right + post, sy], fill=fg)
    d.rectangle([s * 0.20, sy, s * 0.80, sy + sill], fill=fg)
    if letter:
        try:
            f = ImageFont.truetype(SERIF, int(s * 0.21))
        except Exception:
            f = ImageFont.load_default()
        d.text((s / 2, s * 0.835), letter, font=f, fill=fg, anchor="mm")
    img.resize((ICON, ICON), Image.LANCZOS).save(path)


WAIT = '''
# wait for a button, so the screen can actually be read; cap it so a wedged
# input device cannot strand the launcher
( sleep 45; kill -TERM $$ 2>/dev/null ) &
WATCH=$!
dd if=/dev/input/event5 bs=16 count=4 >/dev/null 2>&1 || sleep 5
kill $WATCH 2>/dev/null
'''

APPS = {
    "LimenOS Boost": dict(
        letter="B",
        description="Turn on the two CPU cores Miyoo leaves off",
        body=r'''
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
'''),
    "LimenOS Status": dict(
        letter="S",
        description="Hardware and radio status",
        body=r'''
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
'''),
    "LimenOS Deck": dict(
        letter="D",
        description="Bring up the security deck",
        body=r'''
# cores up, zram on, ssh up, and mount the LimenOS card if it is in a slot
for c in 2 3; do echo 1 > /sys/devices/system/cpu/cpu$c/online 2>/dev/null; done

# Reinstall the SSH key. /root is a read-only squashfs so it has to be a
# bind-mount over a writable copy, which lives in tmpfs and therefore does
# NOT survive a reboot. Doing it here means SSH works after every boot
# without ever typing the device password.
# Dropbear silently ignores authorized_keys when the home or .ssh directory
# is group/world writable, so the 0700 modes below are load-bearing.
if [ -f "$PROGDIR/authorized_keys" ] && [ ! -f /root/.ssh/authorized_keys ]; then
    mkdir -p /tmp/limen-root
    cp -a /root/. /tmp/limen-root/ 2>/dev/null
    mkdir -p /tmp/limen-root/.ssh
    chmod 700 /tmp/limen-root /tmp/limen-root/.ssh
    cp "$PROGDIR/authorized_keys" /tmp/limen-root/.ssh/authorized_keys
    chmod 600 /tmp/limen-root/.ssh/authorized_keys
    chown -R 0:0 /tmp/limen-root 2>/dev/null
    mount --bind /tmp/limen-root /root && echo "ssh key reinstalled"
fi
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
'''),
}

LAUNCH = '''#!/bin/sh
# LimenOS launcher entry. Run as root by the stock firmware, which executes
# ${{CUSTOMER_DIR}}/App/<name>/launch.sh through /tmp/cmd_to_run.sh.
# Nothing here writes to internal flash.
PROGDIR=$(dirname "$0")
cd "$PROGDIR" || exit 1
echo 1 > /tmp/stay_awake 2>/dev/null
SAY="$PROGDIR/limen-say"
[ -x "$SAY" ] || SAY=/usr/bin/true
exec >>/tmp/limen-app.log 2>&1
echo "=== {name} $(date 2>/dev/null) ==="
{body}
{wait}
rm -f /tmp/stay_awake 2>/dev/null
exit 0
'''


def build(out, saybin):
    made = []
    for name, spec in APPS.items():
        d = os.path.join(out, name)
        os.makedirs(d, exist_ok=True)
        icon(os.path.join(d, "icon.png"), spec["letter"], False)
        icon(os.path.join(d, "iconsel.png"), spec["letter"], True)
        with open(os.path.join(d, "config.json"), "w") as fh:
            json.dump({"label": name, "icon": "icon.png", "iconsel": "iconsel.png",
                       "launch": "launch.sh", "description": spec["description"]},
                      fh, indent=1)
        p = os.path.join(d, "launch.sh")
        with open(p, "w") as fh:
            fh.write(LAUNCH.format(name=name, body=spec["body"], wait=WAIT))
        os.chmod(p, 0o755)
        if saybin and os.path.exists(saybin):
            import shutil
            shutil.copy2(saybin, os.path.join(d, "limen-say"))
            os.chmod(os.path.join(d, "limen-say"), 0o755)
        # the Deck entry carries the public key so SSH survives a reboot
        if name.endswith("Deck"):
            pub = os.path.expanduser("~/.ssh/limen_flip.pub")
            if os.path.exists(pub):
                import shutil
                shutil.copy2(pub, os.path.join(d, "authorized_keys"))
        made.append(name)
    print("  built: " + ", ".join(made))
    return 0


if __name__ == "__main__":
    out = sys.argv[1] if len(sys.argv) > 1 else "build/App"
    os.makedirs(out, exist_ok=True)
    raise SystemExit(build(out, "build/bin/limen-say"))
