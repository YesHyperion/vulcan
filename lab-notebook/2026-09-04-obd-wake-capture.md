# 2026-09-04 - OBD capture of the Clio 4 wake-up sequence

**Phase:** 1 (mapping) - obtaining the cluster wake stimulus
**Operator:** Marc
**Source:** donor vehicle = Marc's own **Clio 4**, OBD-II port, SH-C30G in **LISTEN-ONLY** (100% passive).

## Setup
- OBD-II pigtail -> SH-C30G. Wires identified on the car by multimeter (voltages, GND via chassis):
  - **CAN-H = Vert** (~2.43 V active) -> OBD pin 6
  - **CAN-L = Bordeaux-et-blanc** (~2.28 V active) -> OBD pin 14
  - **GND = Jaune / Orange** (0 V, continuity to chassis) -> OBD pin 4/5
  - +12 V battery = Vert-et-blanc (12.75 V) -> OBD pin 16 - **isolated, never connected**
- Bitrate **500 kbps** confirmed (clean frames). Capture via `src/mapping/obd_capture.sh` (listen-only).

## Captures (in captures/, gitignored)
- `candump-2026-09-04_175943.log` - **93 197 frames** of normal running traffic (cluster awake).
- `candump-2026-09-04_181536.log` - **15 252 frames**, the **asleep->awake transition** (locked car,
  waited for bus sleep, then opened a door).

## Key finding - the wake frame
The transition log **opens with ID `0x350` sent ~16x in ~4 ms** (data `C0697D5D1470A485`, byte 0 is a
counter) on an otherwise-silent bus, **before any other ID appears** - then all other nodes cascade
online (4F8, 55D, 218, 4FA, 671, 211, 214, 303, 552, ...).

-> **`0x350` is the prime wake-up / network-management frame** the cluster reacts to.

## Replay attempt (bench) - blocked by the single-node ACK problem
Replayed the wake log to the bench cluster (`src/mapping/replay_wake.sh`, both CAN orientations):
**no wake.** Counters: ~11 490 TX attempts, **11 426 errors, only 3 ACKed.** The cluster (asleep)
doesn't ACK, so every frame is error-flagged -> it never receives a clean `0x350`. candleLight
**refuses both `presume-ack` and `one-shot`**, so we can't send clean frames with a single node.
-> **Fix ordered: a 2nd identical SH-C30G** to sit on the bus and ACK our replay (clean transmission
-> cluster receives clean frames -> wakes). Arrives ~2026-09-11. Not on the critical path for Phase 1.

## Cartography of the capture (Phase 1) - `src/mapping/cartography.py`
- Running-traffic log `candump-2026-09-04_175943.log`: **137 458 frames, 29 distinct IDs, 229 s.**
- Structure by rate: 100 Hz (`0x0C6`,`0x12E`, live signals), 50 Hz (`0x211`,`0x214`,`0x29A`,...),
  25-20 Hz (`0x352`,`0x354`,`0x392`), a 10 Hz block (~16 IDs incl. `0x350`), 1-0.3 Hz housekeeping.
- **`0x350`** = 10 Hz, rolling counter on byte 0 -> the NM/wake frame.
- **No 0x700-0x7FF (UDS diagnostic) traffic** - expected for a passive capture; Phase 2 target.
- **Bitrate 500 kbps confirmed empirically** (resolves the last Phase-0 unknown).

## Next step
Phase 2 prep while the 2nd node ships: build the **UDS client** (`src/uds/`) so we can immediately
do diagnostic discovery (0x10 session, 0x22 DID sweep, detect 0x27) the moment the cluster wakes.
