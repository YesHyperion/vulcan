#!/usr/bin/env bash
# VULCAN - bring up a VIRTUAL CAN interface (vcan0) for hardware-free testing.
# Lets us validate the whole software pipeline (bring-up, sanity_check, mapping)
# with NO cluster and NO risk, before the real bench exists. Idempotent.
#
# Usage (inside WSL Ubuntu; prompts for sudo):
#   bash src/bringup/vcan_up.sh          # create vcan0
#   cangen vcan0 -g 10 &                 # generate fake traffic
#   python src/bringup/sanity_check.py -c vcan0 -t 5
#   bash src/bringup/vcan_up.sh down     # tear down
set -euo pipefail

IFACE="vcan0"

if [ "${1:-up}" = "down" ]; then
  sudo ip link set "$IFACE" down 2>/dev/null || true
  sudo ip link delete "$IFACE" 2>/dev/null || true
  echo "$IFACE removed"
  exit 0
fi

sudo modprobe vcan
if ! ip link show "$IFACE" >/dev/null 2>&1; then
  sudo ip link add dev "$IFACE" type vcan
fi
sudo ip link set up "$IFACE"
echo "== $IFACE up (virtual) =="
ip -details link show "$IFACE"
