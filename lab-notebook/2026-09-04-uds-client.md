# 2026-09-04 - UDS client built and validated (Phase 2 tooling)

**Phase:** 2 prep (no hardware - developed & tested on `vcan0`).
**Operator:** Marc

## What was built (`src/uds/`)
- `nrc.py` - UDS service table (25) + NRC table (27); the fuzzer's future oracle.
- `uds_client.py` - `UdsClient`: ISO-TP (can-isotp CanStack) + request/response, transparent
  0x78 responsePending handling. Runs on `can0` and `vcan0` alike.
- `discovery.py` - `find_ecus` / `probe_services` (safe: bare-SID probe) / `did_scan` /
  `check_security` + CLI. Reads defaults from `config/bus.yaml`.
- `sim_ecu.py` - virtual UDS ECU for `vcan0` testing (DIDs echo the real cluster identifiers).

## End-to-end validation on vcan0 
`python -m src.uds.sim_ecu --channel vcan0` + `python -m src.uds.discovery --channel vcan0 --find`:
- **ECU found:** request 0x7E0 -> response 0x7E8.
- **Extended session** 0x10 0x03 -> positive.
- **Service probe:** 0x10 0x11 0x19 0x22 0x27 0x31 0x3E all detected as supported.
- **DID scan 0xF180-0xF1FF:** read F187=248106952R, F18C=LCBDX12867, F190(VIN), F191=VPFRRF-14B115-AD,
  F194=SW08.13; F1A0 correctly returned securityAccessDenied.
- **SecurityAccess 0x27:** seed `DE AD BE EF` received -> 0x27 detection path works.
- Syntax + venv-import checks pass (python-can, can-isotp resolve).

## Outcome & next step
Phase 2 discovery pipeline is **built and proven virtually.** When the 2nd SH-C30G arrives (~09-11)
and the bench cluster is woken, point the same commands at `can0` to enumerate the *real* cluster's
services, DIDs and its 0x27 seed - then write the discovered diagnostic (tx,rx) into `config/bus.yaml`.
