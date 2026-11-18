#!/bin/sh
# LimenOS Shell - a terminal with an on-screen keyboard.
#
# Runs limen-shell directly against /dev/fb0 and /dev/input/event5. It repaints
# on every keypress, so it cannot go through fbdisplay (which shows one static
# PNG). That is fine here: the launcher EXITS before running an app, so nothing
# is composing over the framebuffer while this is up.
PROGDIR=$(dirname "$0")
cd "$PROGDIR" || exit 1
echo 1 > /tmp/stay_awake 2>/dev/null
exec >>/tmp/limen-app.log 2>&1
echo "=== LimenOS Shell $(date 2>/dev/null) ==="
chmod +x "$PROGDIR/limen-shell" 2>/dev/null
"$PROGDIR/limen-shell"
echo "shell exited $?"
rm -f /tmp/stay_awake 2>/dev/null
exit 0
