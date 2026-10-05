#!/usr/bin/env bash
# VULCAN - bring up the SocketCAN interface for the SH-C30G (candleLight / gs_usb).
#
# Idempotent: safe to re-run. Brings the link down if already up, then reconfigures.
# Defaults mirror config/bus.yaml (channel: can0, bitrate: 500000) - keep them in sync.
#
# SAFETY (PROJECT.md §4): this script only configures the host NIC. It does NOT energize
# the cluster. Do not run the physical power-up until docs/pinout.md is fully decoded.
set -euo pipefail

IFACE="${1:-can0}"
BITRATE="${2:-500000}"   # mirror config/bus.yaml : interface.bitrate

if ! command -v ip >/dev/null 2>&1; then
  echo "error: 'ip' not found - this needs a Linux host with iproute2 (native or Pi)." >&2
  exit 1
fi

# candleLight/Canable presents via gs_usb. Ensure the module is loaded (harmless if
# already loaded or built-in; on WSL2 it auto-loads after `usbipd attach`).
sudo modprobe gs_usb 2>/dev/null || true

# Is the device present at all?
if ! ip link show "$IFACE" >/dev/null 2>&1; then
  echo "error: interface '$IFACE' not found." >&2
  echo "  - Is the SH-C30G plugged in and enumerated? (dmesg | grep -i gs_usb)" >&2
  echo "  - On WSL2 you must first attach the USB device with usbipd." >&2
  exit 1
fi

# Reconfigure idempotently.
sudo ip link set "$IFACE" down 2>/dev/null || true
sudo ip link set "$IFACE" up type can bitrate "$BITRATE"

echo "== $IFACE up @ ${BITRATE} bps =="
ip -details -statistics link show "$IFACE"
echo
echo "Next: candump $IFACE   (log with: candump -l $IFACE  -> writes candump-*.log)"
