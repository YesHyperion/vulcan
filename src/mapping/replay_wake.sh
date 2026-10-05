#!/usr/bin/env bash
# VULCAN - replay a captured CAN log to the bench cluster to wake it up.
#
# The cluster is asleep at first and won't ACK, so the controller reaches bus-off
# (candleLight can't auto-restart). We therefore LOOP: (re)bring-up + canplayer, for
# DUR seconds. Each pass re-delivers the wake burst (the 0x350 flood at the log's
# start); once the cluster wakes and starts ACKing, a pass runs the full sequence.
#
# Usage: sudo bash src/mapping/replay_wake.sh <logfile> [seconds]
set -u
IFACE=can0
BR=500000
LOG=${1:?"usage: sudo bash src/mapping/replay_wake.sh <logfile> [seconds]"}
DUR=${2:-30}
[ -f "$LOG" ] || { echo "!! log not found: $LOG"; exit 1; }

echo "== replaying $LOG on $IFACE @ ${BR} for ${DUR}s =="
echo "   >>> WATCH the cluster (screen / needles / LEDs) and the PSU current <<<"
end=$((SECONDS + DUR))
passes=0
while [ $SECONDS -lt $end ]; do
  sudo ip link set "$IFACE" down 2>/dev/null
  sudo ip link set "$IFACE" up type can bitrate "$BR" 2>/dev/null
  canplayer -I "$LOG" 2>/dev/null
  passes=$((passes + 1))
done
sudo ip link set "$IFACE" down 2>/dev/null
sudo ip link set "$IFACE" up type can bitrate "$BR" 2>/dev/null
echo "== done ($passes passes). Interface left up. =="
