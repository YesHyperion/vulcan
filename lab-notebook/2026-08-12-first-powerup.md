# 2026-08-12 - First power-up (cluster energized)

**Phase:** 0 (bench bring-up)
**Operator:** Marc
**PSU:** WANPTEK DPS305U - 12.0 V, ~2 A limit, OCP on

## Setup
- Contacts: female Dupont ends on connector pins (decoded 2026-08-07).
- Wiring (power only): **+12 V (pin 3) <- red <- PSU +**, **GND (pin 15) <- black <- PSU -**.
- CAN (pins 23/24) not yet connected. SH-C30G not connected.

## Safety gate (PROJECT.md §4)
- [x] §4.2 pinout verified at the multimeter before power.
- [x] §4.3 PSU current-limited (12.0 V / ~2 A / OCP on).
- [x] Bench-only, owned cluster.

## Result
- Output ON -> **12.00 V holds, 0.030 A (30 mA), C.V mode.**
- Healthy low standby draw; no short, no reverse polarity. Voltage stable.
- Cluster visible behavior: **nothing** (no needles / backlight / LED) - expected: it stays asleep
  until a CAN wake-up frame (Phase 1).

## Outcome & next step
**First successful energization.** Cluster draws ~30-40 mA on B+ alone (deep-sleep standby).

## CAN bring-up + wake-up investigation (2026-08-12)
- `can0` up @ 500 kbps via gs_usb (candleLight); interface healthy (ERROR-ACTIVE, counters 0).
- **Passive listen: total silence** - cluster transmits nothing (`bus-errors = 0` -> not a bitrate
  mismatch, genuinely no activity).
- **Active probe (`cansend`): no ACK** - controller goes ERROR-PASSIVE, `error-pass` climbs.
- **CAN wiring proven good:** 120 Ω across CAN-H/CAN-L at the SH-C30G (through the cluster's
  internal termination), unpowered. (Debugged: female Dupont contact, then a CAN-H/CAN-L short -
  both fixed.)
- **Both CAN-H/CAN-L orientations tested -> neither ACKs** -> orientation is NOT the issue.
- **Bitrate scan (`scan_bitrate.sh`) 500k/250k/125k/100k/83k3/50k -> no ACK at ANY rate.**
- `restart-ms` unsupported by candleLight.

### Conclusion
The cluster is in **deep sleep / partial-networking**: its CAN controller ignores arbitrary
frames and won't ACK or transmit until it receives its **specific Renault wake-up frame** (sent
by the BCM/UCH in the car). This frame is model-specific and not public (built into commercial
emulators; normally captured by sniffing a real car's OBD on door-open). **This is the Phase 1
research frontier.**

### +APC hunt (2026-08-12) - done, negative
- No power-input signature on any non-B+ pin (resistance-to-GND: all candidates OL; only B+/pin3
  shows a DC path, 2.89 kΩ).
- **12 V applied (firm male-male contact) to the 5 "fully quiet" pins (2, 5, 13, 14, 18)**, cluster
  on B+, **watching CAN (candump) + error counters + display + current** -> **nothing**: current
  stayed 0.03 A, display dark, `bus-errors = 0`, `RX = 0`. No wake on any of them.
- Online search for the exact Clio 4 wake frame: **not public** (model-specific, built into
  commercial emulators; captured by sniffing a real car).

### Conclusion (firm)
Within-our-control avenues are **exhausted and documented**: both CAN orientations, all common
bitrates, and +APC on all safe candidate pins - none wake the cluster. It is a **partial-networking
cluster requiring a specific Renault CAN wake-up frame** we cannot synthesize without a reference
(donor car OBD sniff, or a commercial emulator used as ground truth to capture the sequence).

### Genuine paths forward
1. **Capture the wake sequence** - sniff a donor Renault (Clio 4 / Captur / Mégane era) at the OBD
   on door-open, OR run a ~€28 emulator clone once with the SH-C30G listening, then **replicate the
   frames ourselves** (turns it into ground-truth data we then own).
2. **Last within-control experiment:** sustained *varied* CAN flood with bus-off auto-recovery
   (low odds - retransmitted single frames didn't wake it - but genuinely untried).
3. Keep mining community data / DBCs (ddt4all, opendbc, forums).

**Note:** the entire VULCAN toolchain (bench, CAN interface, decode, tooling) is validated. The
wake frame is a one-time unlock; once obtained, Phases 2-4 proceed on everything already built.
