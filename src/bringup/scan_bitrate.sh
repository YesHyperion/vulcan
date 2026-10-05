#!/usr/bin/env bash
# VULCAN - scan common CAN bitrates, testing for an ACK on each.
#
# For each rate: bring up can0, send one frame, wait, and check whether the
# frame was ACKed (controller stays ERROR-ACTIVE) or not (goes ERROR-PASSIVE
# because nothing on the bus acknowledged it). A bitrate that ACKs = the ECU
# is alive at that rate. Needs sudo (ip link). Cluster must be powered.
set -u
IFACE="${1:-can0}"

echo "== CAN bitrate scan on $IFACE (cluster must be ON) =="
for br in 500000 250000 125000 100000 83333 50000; do
  sudo ip link set "$IFACE" down 2>/dev/null
  if ! sudo ip link set "$IFACE" up type can bitrate "$br" 2>/dev/null; then
    printf "  %-8s : bring-up unsupported by adapter\n" "$br"
    continue
  fi
  cansend "$IFACE" 123#1122334455667788 2>/dev/null
  sleep 1
  st=$(ip -d link show "$IFACE" | grep -oE 'ERROR-[A-Z]+' | head -1)
  if [ "$st" = "ERROR-ACTIVE" ]; then
    printf "  %-8s : %-14s  <== ACK! this bitrate works\n" "$br" "$st"
  else
    printf "  %-8s : %-14s  (no ACK)\n" "$br" "$st"
  fi
done

# leave the interface back at 500k, down
sudo ip link set "$IFACE" down 2>/dev/null
sudo ip link set "$IFACE" up type can bitrate 500000 2>/dev/null
echo "== done (left up @ 500000) =="
