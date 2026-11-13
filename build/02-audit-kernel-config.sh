#!/usr/bin/env bash
# LimenOS — audit a kernel .config for cyberdeck capability.
#
#   ./02-audit-kernel-config.sh <kernel.config>
#
# Run it on the stock config to see what's missing; run it on YOUR built
# kernel's .config to prove the deck fragment actually landed.
set -euo pipefail
C="${1:?usage: $0 <kernel.config>}"

ok(){ printf "  \033[32m✓\033[0m %-34s %s\n" "$1" "$2"; }
no(){ printf "  \033[31m✗\033[0m %-34s %s\n" "$1" "$2"; }
chk(){ if grep -qE "^$1=(y|m)" "$C"; then ok "$1" "$2"; else no "$1" "$2"; fi; }

echo; echo "=== capture & raw sockets ==="
chk CONFIG_PACKET          "AF_PACKET — tcpdump / scapy / nmap"
chk CONFIG_CFG80211        "wireless config stack"
chk CONFIG_MAC80211        "softmac — monitor mode infrastructure"
chk CONFIG_MAC80211_MESH   "mesh"
chk CONFIG_PACKET_DIAG     "socket diag"

echo; echo "=== tunnels & virtual interfaces ==="
for o in CONFIG_TUN CONFIG_BRIDGE CONFIG_VETH CONFIG_MACVLAN CONFIG_VLAN_8021Q CONFIG_WIREGUARD; do
  chk "$o" ""
done

echo; echo "=== firewall ==="
chk CONFIG_NF_TABLES       "nftables"
chk CONFIG_IP_NF_IPTABLES  "iptables-legacy"
chk CONFIG_NF_CONNTRACK    "conntrack"
chk CONFIG_IP_NF_NAT       "NAT"

echo; echo "=== USB Wi-Fi adapters (the stock blocker) ==="
n=0
for o in CONFIG_ATH9K_HTC CONFIG_CARL9170 CONFIG_MT7601U CONFIG_MT76x2U \
         CONFIG_MT7921U CONFIG_RT2800USB CONFIG_RTL8XXXU CONFIG_RTW88 \
         CONFIG_ZD1211RW CONFIG_P54_USB; do
  if grep -qE "^$o=(y|m)" "$C"; then ok "$o" ""; n=$((n+1)); else no "$o" ""; fi
done
echo "  --> $n/10 external adapter families supported"
[ "$n" -eq 0 ] && echo "  !! NO external USB Wi-Fi adapter will work on this kernel."

echo; echo "=== USB ethernet (host side) ==="
for o in CONFIG_USB_USBNET CONFIG_USB_NET_CDCETHER CONFIG_USB_NET_AX88179_178A CONFIG_USB_RTL8152; do
  chk "$o" ""
done

echo; echo "=== USB gadget (the 'ssh limen.local' link) ==="
for o in CONFIG_USB_CONFIGFS CONFIG_USB_F_HID CONFIG_USB_F_MASS_STORAGE \
         CONFIG_USB_F_ECM CONFIG_USB_F_NCM CONFIG_USB_F_RNDIS; do
  chk "$o" ""
done

echo; echo "=== serial / hardware hacking ==="
for o in CONFIG_USB_SERIAL_CP210X CONFIG_USB_SERIAL_FTDI_SIO \
         CONFIG_USB_SERIAL_PL2303 CONFIG_USB_SERIAL_CH341 CONFIG_USB_ACM; do
  chk "$o" ""
done

echo; echo "=== containers / memory ==="
for o in CONFIG_USER_NS CONFIG_NET_NS CONFIG_OVERLAY_FS CONFIG_SECCOMP_FILTER \
         CONFIG_ZRAM CONFIG_BPF_SYSCALL; do
  chk "$o" ""
done

echo; echo "=== capture vault filesystems ==="
chk CONFIG_VFAT_FS  "FAT32 — 4GB/file cap, rotate captures"
chk CONFIG_EXFAT_FS "exFAT — >4GB capture files"
chk CONFIG_FUSE_FS  "FUSE — exfat-fuse fallback if EXFAT_FS absent"
chk CONFIG_EXT4_FS  "ext4 rootfs"
if ! grep -qE "^CONFIG_EXFAT_FS=(y|m)" "$C" && grep -qE "^CONFIG_VFAT_FS=(y|m)" "$C"; then
  echo "  !! no native exFAT: vault must be FAT32 (4GB/file) or exfat-fuse."
fi

echo; echo "=== module policy ==="
chk CONFIG_MODULES "loadable modules"
if grep -qE "^CONFIG_MODULE_SIG_FORCE=y" "$C"; then
  no "CONFIG_MODULE_SIG_FORCE" "signed modules ENFORCED — out-of-tree drivers blocked"
else
  ok "unsigned modules" "out-of-tree drivers can load"
fi
grep -qE "^CONFIG_RTL8733BU=y" "$C" && \
  no "CONFIG_RTL8733BU=y" "built-in — cannot be unloaded for a patched build"
echo
