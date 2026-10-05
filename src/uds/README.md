# src/uds - Phase 2: UDS discovery

A small, self-contained UDS (ISO 14229) client over ISO-TP (ISO 15765-2) / SocketCAN.
Runs identically on the real bus (`can0`) and the virtual bus (`vcan0`), so it is tested
against a virtual ECU before ever touching the cluster.

## Modules
| File | Role |
|---|---|
| `nrc.py` | UDS service names + Negative Response Code (NRC) tables. The NRC is the fuzzer's key oracle. |
| `uds_client.py` | `UdsClient` - ISO-TP transport + request/response, transparent 0x78 responsePending handling. |
| `discovery.py` | `find_ecus`, `probe_services`, `did_scan`, `check_security` + a CLI. |
| `sim_ecu.py` | A virtual UDS ECU for `vcan0` testing (its DIDs echo the real cluster's SW/HW/part numbers). |

## Test it now on the virtual bus (no hardware)
```bash
# 1) bring up the virtual bus (needs sudo)
bash src/bringup/vcan_up.sh
# 2) start the virtual ECU (terminal A)
~/.venvs/vulcan/bin/python -m src.uds.sim_ecu --channel vcan0
# 3) run discovery against it (terminal B)
~/.venvs/vulcan/bin/python -m src.uds.discovery --channel vcan0 --find
```
Expected: discovery finds the ECU at `0x7E0 -> 0x7E8`, lists supported services, reads the
identification DIDs (VIN, serial, `SW08.13`, `248106952R`...), flags the locked DID, and receives a
SecurityAccess (0x27) seed.

## Use it on the real cluster (once it's awake - Phase 2 live)
```bash
python -m src.uds.discovery --channel can0 --find              # find the cluster's (tx,rx) pair
python -m src.uds.discovery --channel can0 --tx 0x7NN --rx 0x7NN --services --did-scan 0xF180 0xF1FF --sec
```
Write the discovered request/response IDs into `config/bus.yaml : arbitration_ids.diagnostic`
so later runs pick them up automatically.

## Design notes
- Service probing sends a **bare SID** (no valid parameters) -> a recognised service is *rejected*,
  never executed. Safe to run against a live ECU.
- Grounding: ECUFuzz uses UDS itself (0x19/0x14/0x10) as a fuzzing feedback channel
  (docs/RESEARCH.md §2). The NRC/timing bookkeeping here feeds Phase 3.
- `0x27` detection here is the entry point for the Phase 4 side-channel work on the seed->key path.
