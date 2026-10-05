# Cluster connector pinout - Renault Clio 4 instrument cluster

> **Status: CORE PINS DECODED (2026-08-07).** +12 V, GND and the CAN pair confirmed by
> multimeter - the §4.2 gate is met for the pins we will connect. Still to pin down:
> CAN-H vs CAN-L orientation (needs power) and whether a separate +APC pin exists.

## Target

| Field | Value |
|---|---|
| Cluster reference | **248106952R** - CONFIRMED from label (2026-07-31) |
| Supplier code | VPFRRF-10849-BD |
| Serial | LCBDX12867 |
| Firmware | SW 08.13, HW VPFRRF-14B115-AD |
| Build date | 11/03/2016 06:18 (Phase 1) |
| Maker | Visteon (Pameia plant) |
| Connector | Single rear connector, **24 pins in 2 rows** (top 1-12, bottom 13-24). Recount at decode to be sure. |

## What we must identify before power

The five pins that matter for a static bench bring-up:

| Signal | Role | How to recognize it | Pin # | Confidence |
|---|---|---|---|---|
| **B+**    | Permanent +12 V (battery) | +12 V rail; many pins' protection diodes clamp to it | **3, 16, 17, 20** | CONFIRMED rail (all shorted, matching diode drops) |
| **+APC**  | Switched +12 V (ignition/accessory) | Wakes the cluster; may be needed for it to boot | not separately found | May share the rail or be distinct - hunt only if the cluster won't wake |
| **GND**   | Ground | Diode: lights ~0.9-1.9 V to ~17 pins (everything references it) | **15** | CONFIRMED (2026-08-07) |
| **CAN-H** | CAN high | ~2.5 V idle (powered); pairs with CAN-L; ~120/60 Ω across the pair | **23 or 24** | Pair confirmed (120.4 Ω); H vs L TBD |
| **CAN-L** | CAN low  | ~2.5 V idle (powered); pairs with CAN-H | **23 or 24** | Pair confirmed (120.4 Ω); H vs L TBD |

## Decode procedure (multimeter, cluster UNPOWERED)

1. **Photograph** the rear connector straight-on, well lit, with the keying visible. Save to `docs/` and reference it here.
2. **Continuity -> GND:** find the pin(s) with continuity to the metal cluster body / connector shell.
3. **CAN pair -> resistance:** probe pin pairs for ~120 Ω (single termination) or ~60 Ω (dual). That pair is CAN-H / CAN-L. Record the reading - it also answers the termination question in `config/bus.yaml`.
4. **Power pins:** cross-reference the connector against a Clio 4 cluster pinout diagram (service manual / community DB) to tell B+ from +APC. Do **not** guess from wire colour alone - verify against the diagram + connector keying.
5. Only when **all five** rows above are filled with real confidence do we move to `docs/bench-setup.md` power-up.

## Candidate pinout - UNVERIFIED HYPOTHESIS (from forums, MUST be confirmed at the multimeter)

> Source: MHH Auto thread on the sibling variant **248109247R** (our cluster is 248106952R -
> same Clio 4 family, connector may differ). These are Renault **schematic net names**, NOT
> physical connector positions - mapping net -> physical pin still requires the wiring diagram
> or continuity testing. **Do not power on the basis of this table (§4.2).**

| Signal | Renault net (hypothesis) | Physical pin # | Verified? |
|---|---|---|---|
| CAN-H | 133B | pin 23 or 24 |  pair found (120.4 Ω); H/L TBD |
| CAN-L | 133C | pin 23 or 24 |  pair found (120.4 Ω); H/L TBD |
| GND   | NBT  | **15** |  confirmed (diode -> ~17 pins) |
| B+ (permanent)   | BP69 | **3 / 16 / 17 / 20** |  +12 V rail confirmed |
| +APC (after contact) | AP29 | not found | hunt if needed |

**Wake-up note (important for Phase 1):** multiple bench reports say the Clio 4 cluster powers
its gauges on 12 V but stays mostly dark / idle until it receives a **CAN wake-up frame**
(normally sent by the UCH body computer). So "quiet on power-up" is expected - bringing it
fully alive is a CAN task, not a wiring fault. This is a Phase 1 objective, not a Phase 0 blocker.

- [ ] Confirm physical connector part number and pin count against the photo.
- [ ] Map each net above to a physical pin (diagram + multimeter continuity).

## Measurement log

| Date | Instrument | Reading | Interpretation |
|---|---|---|---|
| 2026-08-07 | KAIWEETS (Ω) | **120.4 Ω across pins 23-24** | CAN pair - single internal 120 Ω termination (textbook). All other pairs: OL (open). |
| 2026-08-07 | KAIWEETS (Ω) | 12<->23 = 120.4 Ω ; 12<->24 ~ 0.4 Ω | Pin 12 is the **same CAN line as pin 24** (clean 120 Ω to 23 = it's a CAN line, not GND). GND still unknown. |
| 2026-08-07 | KAIWEETS (diode) | pin 1 = OL both ways | Pin 1 = **not connected (NC)** |
| 2026-08-07 | KAIWEETS (diode) | BLACK on pin 3, ~0.5 V to many RED pins | **Pin 3 = +12 V supply rail** (B+ or +APC, TBD) |
| 2026-08-07 | KAIWEETS (diode) | BLACK on 23: 3/16/17/20 = ~0.71 V | +12 V rail = pins **3, 16, 17, 20** (same net) |
| 2026-08-07 | KAIWEETS (diode) | RED on 15 -> ~17 pins light (0.9-1.9 V) | **Pin 15 = GND** (confirmed). 6-10 ~ 1.86 V = LED/illumination pins |
