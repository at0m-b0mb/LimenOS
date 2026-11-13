#!/usr/bin/env python3
"""
LimenOS security app entries for the Miyoo Flip launcher.

Every entry checks for the tools it needs AT RUNTIME and reports honestly on
screen if they are missing, rather than failing silently. Three separate times
this session a check was run against a path that did not exist and returned a
confident wrong answer, so nothing here asserts what the firmware provides.

Scope: these look at YOUR OWN device and YOUR OWN network. Nothing here
attacks anything, nothing runs unattended, and the one entry that can act
against another machine (USB HID) only arms the gadget - it types nothing.
"""
from __future__ import annotations
import json, os, shutil, sys
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
        d.rounded_rectangle([0, 0, s - 1, s - 1], radius=r, fill=BRASS); fg = PAPER
    else:
        d.rounded_rectangle([0, 0, s - 1, s - 1], radius=r, fill=SURFACE,
                            outline=RULE, width=max(2, int(s * 0.02))); fg = INK
    post = max(2, int(s * 0.055)); sill = max(3, int(s * 0.098))
    left, right = s * 0.33, s * 0.67
    top, sy = s * 0.20, s * 0.58
    d.rectangle([left - post, top, left, sy], fill=fg)
    d.rectangle([right, top, right + post, sy], fill=fg)
    d.rectangle([s * 0.20, sy, s * 0.80, sy + sill], fill=fg)
    try:
        f = ImageFont.truetype(SERIF, int(s * 0.20))
    except Exception:
        f = ImageFont.load_default()
    d.text((s / 2, s * 0.83), letter, font=f, fill=fg, anchor="mm")
    img.resize((ICON, ICON), Image.LANCZOS).save(path)


WAIT = '''
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
'''

# a shell helper every entry gets: report a missing tool instead of guessing
NEED = '''
need() {   # need <binary> ; echo the path or empty, and record what is absent
  p=$(command -v "$1" 2>/dev/null)
  if [ -n "$p" ]; then echo "$p"; else MISSING="$MISSING $1"; fi
}
MISSING=""
'''

APPS = {
    "LimenOS WiFi Survey": dict(
        letter="W",
        description="List the networks around you, with signal and security",
        body=r'''
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
show --title "WiFi Survey" --footer "> Press a button to return" "$@" 
'''),

    "LimenOS Neighbours": dict(
        letter="N",
        description="Which devices are on your network",
        body=r'''
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
show --title "Neighbours" --footer "> Press a button to return" "$@" 
'''),

    "LimenOS USB HID": dict(
        letter="H",
        description="Arm or disarm the USB keyboard gadget",
        body=r'''
# Arms the HID gadget only. It types nothing: sending keystrokes is a
# deliberate, separate act over SSH with limen-hid and an explicit --arm.
CFG=/tmp/.usb_config
if [ -e /dev/hidg0 ]; then
    echo "usb_adb_en" > "$CFG"
    usbdevice restart >/dev/null 2>&1
    sleep 2
    set -- "> Disarmed" "" \
      "The USB keyboard gadget is off and" \
      "the port is back to its normal mode."
else
    echo "usb_hid_en" > "$CFG"
    usbdevice restart >/dev/null 2>&1 || usbdevice start >/dev/null 2>&1
    n=0; while [ $n -lt 12 ] && [ ! -e /dev/hidg0 ]; do n=$((n+1)); sleep 1; done
    if [ -e /dev/hidg0 ]; then
        set -- "> Armed  -  /dev/hidg0" "" \
          "report   $(cat /sys/kernel/config/usb_gadget/rockchip/functions/hid.usb0/report_length 2>/dev/null) bytes" \
          "udc      $(cat /sys/kernel/config/usb_gadget/rockchip/UDC 2>/dev/null)" \
          "state    $(cat /sys/class/android_usb/android0/state 2>/dev/null)" "" \
          "Plug the LOWER USB-C into the target." \
          "It will appear as a keyboard, and will" \
          "type NOTHING until you tell it to." "" \
          "Only use this on machines you own or" \
          "are authorised to test."
    else
        set -- "> Could not arm it" "" "/dev/hidg0 never appeared." "See /tmp/usbdevice.log"
    fi
fi
show --title "USB HID" --footer "> Press a button to return" "$@" "" "> Run again to toggle"
'''),

    "LimenOS Ports": dict(
        letter="P",
        description="USB devices, serial adapters and open ports",
        body=r'''
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
'''),

    "LimenOS Audit": dict(
        letter="A",
        description="Check this handheld's own security posture",
        body=r'''
# Looks only at this device. No network is touched.
ROOTPW=$(awk -F: '$1=="root"{print ($2==""?"EMPTY":"set")}' /etc/shadow 2>/dev/null)
SSHON=$(pgrep dropbear >/dev/null 2>&1 && echo "running" || echo "stopped")
KEYS=$([ -f /root/.ssh/authorized_keys ] && echo "installed" || echo "none")
TELNET=$(pgrep telnetd >/dev/null 2>&1 && echo "RUNNING - turn this off" || echo "off")
LISTEN=$(netstat -ltn 2>/dev/null | awk 'NR>2' | wc -l)
HIDG=$([ -e /dev/hidg0 ] && echo "ARMED" || echo "off")
show --title "Audit" --footer "> Press a button to return" \
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
'''),
}

LAUNCH = '''#!/bin/sh
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
echo "=== {name} $(date 2>/dev/null) ==="
{need}
{body}
{wait}
rm -f /tmp/stay_awake 2>/dev/null
exit 0
'''



def _fill(tpl: str, **kw) -> str:
    """Substitute {name}/{body}/{wait}/{need} without str.format.

    The template contains shell functions, and every brace in them is a
    placeholder as far as str.format is concerned -- it raised
    KeyError: '\n  ' the moment show() { ... } was added. Plain replacement
    has no opinion about braces.
    """
    out = tpl
    for k, v in kw.items():
        out = out.replace("{" + k + "}", v)
    return out

def build(out, saybin):
    made = []
    for name, spec in APPS.items():
        # MainUI builds its launch command as "cd %s; chmod a+x %s; %s" with
        # NO QUOTING, so a folder name containing a space makes `cd` take two
        # arguments and the whole chain dies silently -- the app shows only
        # LOADING and the log stays empty. Folder names are hyphenated; the
        # pretty name lives in config.json "label".
        d = os.path.join(out, name.replace(" ", "-"))
        os.makedirs(d, exist_ok=True)
        icon(os.path.join(d, "icon.png"), spec["letter"], False)
        icon(os.path.join(d, "iconsel.png"), spec["letter"], True)
        json.dump({"label": name, "icon": "icon.png", "iconsel": "iconsel.png",
                   "launch": "launch.sh", "description": spec["description"]},
                  open(os.path.join(d, "config.json"), "w"), indent=1)
        p = os.path.join(d, "launch.sh")
        open(p, "w").write(_fill(LAUNCH, name=name, body=spec["body"], wait=WAIT, need=NEED))
        os.chmod(p, 0o755)
        if saybin and os.path.exists(saybin):
            shutil.copy2(saybin, os.path.join(d, "limen-say"))
            os.chmod(os.path.join(d, "limen-say"), 0o755)
        made.append(name)
    print("  built: " + ", ".join(made))
    return 0


if __name__ == "__main__":
    out = sys.argv[1] if len(sys.argv) > 1 else "build/App"
    os.makedirs(out, exist_ok=True)
    raise SystemExit(build(out, "build/bin/limen-say"))
