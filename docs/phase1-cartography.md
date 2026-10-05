# Phase 1 - CAN cartography of the Clio 4 bus

Automated characterization of a passive capture, produced by
[`src/mapping/cartography.py`](../src/mapping/cartography.py). The tool parses a
`candump -l` log and, per arbitration ID, derives frame count, bus share, mean
period / frequency (from timestamps), payload length (DLC), and a per-byte
activity map.

**Reproduce:**

```bash
python3 src/mapping/cartography.py captures/candump-2026-09-04_175943.log
```

## Capture

| | |
|---|---|
| Source | donor Clio 4, OBD-II port, **100 % passive listen-only** |
| Bus | 500 kbps (confirmed empirically) |
| Window | normal running traffic, cluster awake |
| Volume | **137,458 frames, 29 distinct IDs, 228.7 s** |

> Aggregate, non-identifying statistics only (per-ID timing/structure) - no VIN or
> payload secrets. Raw logs stay out of git (see `.gitignore`).

## Byte-map legend

`.` constant, `~` counter / few states, `#` live (high-variation) signal

## Per-ID profile (by bus share)

| ID | count | bus % | period | freq | DLC | byte-map |
|---|---:|---:|---:|---:|---:|---|
| `0x0C6` | 18,553 | 13.5 % | 10.0 ms | 100.5 Hz | 8 | `.~~~..##` |
| `0x12E` | 18,553 | 13.5 % | 10.0 ms | 100.5 Hz | 8 | `~~#.~...` |
| `0x211` | 11,515 | 8.4 % | 19.9 ms | 50.4 Hz | 8 | `.......~` |
| `0x214` | 11,515 | 8.4 % | 19.9 ms | 50.4 Hz | 2 | `..` |
| `0x29A` | 9,277 | 6.7 % | 19.9 ms | 50.2 Hz | 8 | `......##` |
| `0x242` | 9,276 | 6.7 % | 19.9 ms | 50.2 Hz | 7 | `.......` |
| `0x29C` | 9,276 | 6.7 % | 19.9 ms | 50.2 Hz | 8 | `........` |
| `0x352` | 4,638 | 3.4 % | 39.8 ms | 25.1 Hz | 4 | `....` |
| `0x354` | 4,638 | 3.4 % | 39.8 ms | 25.1 Hz | 8 | `........` |
| `0x392` | 3,710 | 2.7 % | 49.8 ms | 20.1 Hz | 4 | `.~..` |
| `0x350` | 2,307 | 1.7 % | 99.1 ms | 10.1 Hz | 8 | `~..~.~~~` |
| `0x552` | 2,303 | 1.7 % | 99.3 ms | 10.1 Hz | 2 | `..` |
| `0x303` | 2,303 | 1.7 % | 99.3 ms | 10.1 Hz | 7 | `.##....` |
| `0x3FA` | 2,303 | 1.7 % | 99.3 ms | 10.1 Hz | 2 | `..` |
| `0x5DE` | 2,303 | 1.7 % | 99.3 ms | 10.1 Hz | 8 | `.~.....~` |
| `0x5DF` | 2,303 | 1.7 % | 99.3 ms | 10.1 Hz | 2 | `.~` |
| `0x218` | 2,303 | 1.7 % | 99.3 ms | 10.1 Hz | 1 | `.` |
| `0x4FA` | 2,303 | 1.7 % | 99.3 ms | 10.1 Hz | 2 | `..` |
| `0x671` | 2,303 | 1.7 % | 99.3 ms | 10.1 Hz | 1 | `.` |
| `0x55D` | 2,302 | 1.7 % | 99.3 ms | 10.1 Hz | 8 | `....~...` |
| `0x3B7` | 2,300 | 1.7 % | 99.4 ms | 10.1 Hz | 6 | `......` |
| `0x4F8` | 2,300 | 1.7 % | 99.4 ms | 10.1 Hz | 8 | `........` |
| `0x581` | 2,198 | 1.6 % | 99.6 ms | 10.0 Hz | 4 | `~.~.` |
| `0x505` | 2,198 | 1.6 % | 99.6 ms | 10.0 Hz | 4 | `..~.` |
| `0x666` | 1,856 | 1.4 % | 99.5 ms | 10.0 Hz | 4 | `....` |
| `0x5D7` | 1,855 | 1.3 % | 99.5 ms | 10.0 Hz | 7 | `.......` |
| `0x646` | 460 | 0.3 % | 496.7 ms | 2.0 Hz | 8 | `........` |
| `0x69F` | 230 | 0.2 % | 993.4 ms | 1.0 Hz | 4 | `....` |
| `0x6FB` | 77 | 0.1 % | 2984.4 ms | 0.3 Hz | 8 | `........` |

## Reading the bus

The traffic sorts cleanly into **rate classes**, which is how a CAN bus is designed -
each function broadcasts at its own cadence:

- **100 Hz - live powertrain/dynamics.** `0x0C6` and `0x12E` dominate the bus (13.5 %
  each) and carry the only `#` (live-signal) bytes - the fast-changing values
  (speed / RPM-class signals).
- **50 Hz - chassis/body periodic.** `0x211`, `0x214`, `0x29A`, `0x242`, `0x29C`:
  mostly static or slow-moving payloads at a steady 20 ms cadence.
- **20-25 Hz - intermediate status.** `0x352`, `0x354`, `0x392`.
- **10 Hz - a large network-management block (~16 IDs).** This is where **`0x350`**
  lives, with a **rolling counter on byte 0** (`~..~.~~~`). This matches the
  asleep->awake transition capture, where `0x350` is the *first* ID to appear on an
  otherwise-silent bus before every other node cascades online - i.e. the cluster's
  **wake / network-management frame** (see `../lab-notebook/2026-09-04-obd-wake-capture.md`).
- **< 2 Hz - housekeeping.** `0x646`, `0x69F`, `0x6FB`: slow status/config.

## Diagnostic surface

**No frames in the UDS diagnostic range `0x700-0x7FF`** appear in a passive capture -
diagnostics only surface when a tester actively queries the ECU. Eliciting and mapping
that surface (sessions, DIDs, NRCs, SecurityAccess `0x27`) is exactly the job of the
Phase 2 tooling in [`src/uds/`](../src/uds/).

---

*Methodology grounding: `docs/RESEARCH.md`. Lab entry: `lab-notebook/2026-09-04-obd-wake-capture.md`.*
