#!/usr/bin/env bash
# VULCAN - wake attempt: sustained VARIED CAN flood with bus-off auto-recovery.
#
# On a no-ACK bus the controller reaches bus-off quickly; candleLight can't auto-restart,
# so we loop: (re)bring-up the interface, then blast a burst of random-ID / random-data
# frames. Over DUR seconds this puts hundreds of *varied* frames on the bus - a long shot
# at hitting a wake-up ID/pattern the cluster reacts to.
#
# One interface can't cleanly listen while flooding, so the wake indicator is PHYSICAL:
#   >>> WATCH the PSU current and the cluster display while this runs. <<<
# A wake shows as the current jumping and/or the screen/gauges/LEDs lighting up.
# Needs sudo. Cluster must be powered on B+.
set -u
IFACE=can0
BR=500000
DUR=${1:-30}

echo "== wake flood: varied random frames on $IFACE @ ${BR} for ${DUR}s =="
echo "   >>> WATCH the PSU current + the cluster display the whole time <<<"
end=$((SECONDS + DUR))
cycles=0
while [ $SECONDS -lt $end ]; do
  sudo ip link set $IFACE down 2>/dev/null
  sudo ip link set $IFACE up type can bitrate $BR 2>/dev/null
  # burst of ~40 random frames (random 11-bit ID, 8 random data bytes, 2 ms gap)
  cangen $IFACE -g 2 -I r -L 8 -D r -n 40 2>/dev/null
  cycles=$((cycles + 1))
done
# leave it up and listening
sudo ip link set $IFACE down 2>/dev/null
sudo ip link set $IFACE up type can bitrate $BR 2>/dev/null
echo "== flood done ($cycles bursts sent). Interface left up. =="
echo "Now run:  candump can0   (see if the cluster started transmitting)"
