# src/mapping - Phase 1: passive cartography

Passive-only tooling to log and characterize what travels on the bus. **No frame is sent
in this phase** - we only observe.

| File | Role |
|---|---|
| `obd_capture.sh` | Listen-only (`candump -l`) capture, **safe on a live OBD bus** - aborts if the adapter refuses listen-only, never falls back to an active mode on a car. Writes timestamped logs to `captures/`. |
| `cartography.py` | Parse a candump log; per-ID stats (count, bus share, period/frequency, DLC, and a per-byte activity map: static / counter / live-signal). Flags IDs in the UDS diagnostic range (0x700-0x7FF). Standard library only. |
| `replay_wake.sh` | Loop-replay a captured log to the bench (with bus-off recovery) - used while investigating the wake frame. |

## Use it

```bash
python3 src/mapping/cartography.py captures/<your-candump>.log [--top N]
```

## Result (2026-09-04)

Run on a real Clio 4 OBD capture: **137,458 frames -> 29 distinct IDs** profiled by rate,
DLC and byte activity. Highlights: `0x0C6`/`0x12E` at 100 Hz (live signals); a 10 Hz
network-management block including **`0x350`** (rolling counter), identified as the
cluster's wake frame; no 0x700-0x7FF diagnostic traffic (expected for a passive capture -
those are the Phase 2 target). Summary written to `config/bus.yaml : arbitration_ids`.

Grounding: SavvyCAN for a visual cross-check (`docs/RESEARCH.md §7`).
