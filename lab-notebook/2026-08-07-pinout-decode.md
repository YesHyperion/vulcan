# 2026-08-07 - Pinout decode (session 1, UNPOWERED)

**Phase:** 0 (bench bring-up, pre-power)
**Operator:** Marc
**Instrument:** KAIWEETS multimeter (continuity + resistance)

## Setup
- Cluster `248106952R` on the desk, **NOT powered** (no PSU connected).
- 24-pin connector, 2 rows (top 1-12, bottom 13-24).
- Measurements made by touching probe tips directly to the connector pins.

## Safety gate (PROJECT.md §4)
- [x] **No power this session** - pure resistance/continuity probing (§4.2 decode-before-power).
- [x] Bench-only, owned salvaged cluster.

## Pin map (fill as we go)
Number the pins consistently: top-left = 1 ... top-right = 12, bottom-left = 13 ... bottom-right = 24.

| Pin | Function (TBD) | Evidence |
|---|---|---|
| 1 | | |
| ... | | |
| 24 | | |

## Measurement 1 - CAN pair (resistance)
Goal: find the pair reading **~120 Ω** (single internal termination) or **~60 Ω** (double) -> that's CAN-H / CAN-L.

| Pin pair | Reading (Ω) | Note |
|---|---|---|
| **23-24** | **120.4** | Only pair with a defined resistance -> CAN pair (internal termination) |
| all others | OL (open) | normal - no other pins directly connected at DC |

Result: **CAN pair = pins 23 / 24** (H vs L orientation TBD). Cluster is internally terminated.

## Measurement 2 - GND candidates (continuity)
Goal: pins that are **commoned together** (beep) -> ground group.

| Reference pin | Beeps with pins | Interpretation |
|---|---|---|
| _TBD_ | | |

## Measurement 3 - power candidates (diode mode)
Goal: from a GND candidate, pins showing a **~0.3-0.7 V diode drop** -> likely B+ / +APC (protection diodes).

| Pin | Diode reading (V) | Note |
|---|---|---|
| 1 (as pivot) | OL both directions | Pin 1 = **not connected (NC)** - no internal diodes |
| **3** (BLACK, sweep RED) | ~0.5 V to MANY red pins | **Pin 3 = positive supply rail (VCC / +12 V)** - B+ or +APC (TBD). Many pins' protection diodes clamp to it. |

**Method note:** blind pivot-by-pivot over ALL pins is impractical, but a pivot on a *connected*
pin works - pin 3 revealed a power rail. Diode method retained; no need to open the cluster.
Next: find GND as the mirror (RED = candidate lights MANY blacks; or BLACK on a signal pin,
sweep RED -> the ~0.5 V hit is GND).

## Running pinout (2026-08-07)

| Function | Pin(s) | Confidence |
|---|---|---|
| CAN pair | **23 & 24** (12 = same net as 24; 11 maybe = 23) | High (120 Ω pair) - H vs L TBD |
| +12 V rail | **3, 16, 17, 20** (all shorted, matching diode drops) | High |
| GND | **15**  | CONFIRMED - RED=15 lit ~17 pins (0.9-1.9 V) |
| NC | pin 1 | - |
| LED/illumination | pins 6, 7, 8, 9, 10 (~1.86 V), 19, 21 | Low priority |
| +APC | not yet distinguished from B+ | - |

## Outcome & next step
**Core pinout decoded** - safe to plan a power-up on: **+12 V = 3/16/17/20, GND = 15, CAN = 23/24.**
Remaining: (1) durable connection to those ~4 pins; (2) current-limited power-up per
`docs/bench-setup.md`; (3) settle CAN-H vs CAN-L (idle ~2.5 V once powered); (4) find +APC only
if the cluster won't wake on B+ + CAN.
