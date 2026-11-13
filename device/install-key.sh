#!/usr/bin/env bash
# ============================================================================
# Install the LimenOS SSH key onto the Flip. Run this from your Mac.
# ============================================================================
#   ./device/install-key.sh [ip]            default: 10.0.0.224
#
# You will be prompted for the Flip's root password ONCE, by ssh itself.
# Nothing here stores, echoes or automates it.
#
# Why not ssh-copy-id: /root lives in a read-only squashfs on this device, so
# ~/.ssh cannot be created. We bind-mount a writable copy of /root over it,
# with 0700 on the home and .ssh directories — dropbear silently ignores an
# authorized_keys file whose home or .ssh is group/world writable.
# ============================================================================
set -euo pipefail
IP="${1:-10.0.0.224}"
KEY="${LIMEN_KEY:-$HOME/.ssh/limen_flip}"

[ -f "$KEY.pub" ] || { echo "no public key at $KEY.pub"; exit 1; }
PUB="$(cat "$KEY.pub")"

echo "[limen] installing key on root@$IP"
echo "[limen] ssh will ask for the device password now"

ssh -o StrictHostKeyChecking=accept-new \
    -o UserKnownHostsFile="$HOME/.ssh/known_hosts" \
    -o PreferredAuthentications=password \
    -o PubkeyAuthentication=no \
    "root@$IP" "
      set -e
      mkdir -p /tmp/limen-root
      cp -a /root/. /tmp/limen-root/ 2>/dev/null || true
      mkdir -p /tmp/limen-root/.ssh
      chmod 700 /tmp/limen-root /tmp/limen-root/.ssh
      printf '%s\n' '$PUB' > /tmp/limen-root/.ssh/authorized_keys
      chmod 600 /tmp/limen-root/.ssh/authorized_keys
      umount /root 2>/dev/null || true
      mount --bind /tmp/limen-root /root
      echo '--- installed ---'
      ls -ld /root /root/.ssh /root/.ssh/authorized_keys
    "

echo
echo "[limen] verifying key authentication..."
if ssh -i "$KEY" -o BatchMode=yes -o PreferredAuthentications=publickey \
       -o StrictHostKeyChecking=accept-new -o ConnectTimeout=10 \
       "root@$IP" 'echo "[limen] KEY AUTH WORKS"; uname -a'; then
    echo
    echo "[limen] done — from here on, no password is needed:"
    echo "    ssh -i $KEY root@$IP"
else
    echo "[limen] key auth still failing. Check permissions above:"
    echo "    /root and /root/.ssh must be 0700, authorized_keys 0600."
    exit 1
fi
