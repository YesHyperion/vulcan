#!/usr/bin/env bash
# VULCAN - passive LISTEN-ONLY capture, safe on a LIVE vehicle OBD bus.
#
# Brings up can0 in listen-only mode (the controller transmits NOTHING - not even
# ACKs) and logs every frame to captures/ in candump log format (replayable later
# with canplayer). If the adapter refuses listen-only, it ABORTS - never fall back
# to a normal mode on a car.
#
# Usage:  sudo bash src/mapping/obd_capture.sh [bitrate]   (default 500000)
set -u
IFACE=can0
BR=${1:-500000}
REPO="$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd)"
mkdir -p "$REPO/captures"

sudo ip link set "$IFACE" down 2>/dev/null
if ! sudo ip link set "$IFACE" up type can bitrate "$BR" listen-only on 2>/dev/null; then
  echo "!! ERROR: listen-only refused at ${BR} bps."
  echo "!! Do NOT connect to the car without listen-only. Stop here and investigate."
  exit 1
fi

# confirm the mode really took
if ! ip -d link show "$IFACE" | grep -q 'LISTEN-ONLY'; then
  echo "!! WARNING: LISTEN-ONLY flag not confirmed by the kernel. Stop and check."
  ip -d link show "$IFACE" | sed 's/numtxqueues.*//'
  exit 1
fi

cd "$REPO/captures"
echo "== can0 UP @ ${BR} bps, LISTEN-ONLY (100% passive, transmits nothing) =="
echo "== Logging to $REPO/captures/candump-*.log =="
echo ">> Trigger events now: open a door, close it, lock/unlock, ignition ON/OFF."
echo ">> Say out loud / note the time of each action."
echo ">> Ctrl+C to stop."
candump -l "$IFACE"
