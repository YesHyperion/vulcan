"""VULCAN - UDS discovery (Phase 2).

Four routines, plus a CLI that ties them together:
  find_ecus()          : sweep request IDs, find (tx, rx) diagnostic pairs that answer.
  probe_services()     : which UDS services does the ECU recognise?
  did_scan()           : which ReadDataByIdentifier (0x22) DIDs return data / are locked?
  check_security()     : is SecurityAccess (0x27) present, and what seed does it hand out?

Run from the repo root, e.g.:
    python -m src.uds.discovery --find
    python -m src.uds.discovery --tx 0x7E0 --rx 0x7E8 --services --did-scan 0xF180 0xF1FF --sec

Defaults for channel / diagnostic IDs are read from config/bus.yaml when present.
Safe by design: service probing sends a bare SID (no valid parameters) so a recognised
service is *rejected*, never executed.
"""
from __future__ import annotations

import argparse
import time
from pathlib import Path

import can

from . import nrc
from .uds_client import UdsClient

REPO = Path(__file__).resolve().parents[2]


# ----------------------------------------------------------------------------- config
def load_config() -> dict:
    cfg_path = REPO / "config" / "bus.yaml"
    channel, tx, rx = "can0", None, None
    try:
        import yaml
        cfg = yaml.safe_load(cfg_path.read_text())
        channel = cfg.get("interface", {}).get("channel", channel)
        diag = cfg.get("arbitration_ids", {}).get("diagnostic", {})
        tx, rx = diag.get("request_id"), diag.get("response_id")
    except Exception:
        pass
    return {"channel": channel, "tx": tx, "rx": rx}


def _hexint(s: str) -> int:
    return int(s, 0)


# --------------------------------------------------------------------------- discovery
def find_ecus(channel: str, tx_range=range(0x700, 0x800), bustype="socketcan",
              listen: float = 0.05, verbose: bool = True) -> list[tuple[int, int]]:
    """Send DiagnosticSessionControl(default) to each candidate ID; record who answers.

    A UDS answer to 0x10 is a single frame whose 2nd byte is 0x50 (positive) or 0x7F
    with the rejected SID 0x10 (negative). Returns a list of (request_id, response_id).
    """
    bus = can.Bus(channel=channel, interface=bustype, receive_own_messages=False)
    found: list[tuple[int, int]] = []
    probe = bytes([0x02, 0x10, 0x01, 0, 0, 0, 0, 0])   # ISO-TP single frame
    try:
        for txid in tx_range:
            # drain stale traffic
            while bus.recv(timeout=0):
                pass
            bus.send(can.Message(arbitration_id=txid, data=probe, is_extended_id=False))
            deadline = time.time() + listen
            while time.time() < deadline:
                msg = bus.recv(timeout=listen)
                if not msg or msg.arbitration_id == txid:
                    continue
                d = msg.data
                if len(d) >= 3 and (d[1] == 0x50 or (d[1] == 0x7F and d[2] == 0x10)):
                    found.append((txid, msg.arbitration_id))
                    if verbose:
                        kind = "positive" if d[1] == 0x50 else f"NRC 0x{d[3]:02X}"
                        print(f"  ECU: request 0x{txid:03X} -> response 0x{msg.arbitration_id:03X} ({kind})")
                    break
    finally:
        bus.shutdown()
    return found


def probe_services(client: UdsClient, timeout: float = 0.3) -> list[tuple[int, str, str]]:
    """Send a bare SID for each known service; classify support by the NRC.

    'serviceNotSupported'(0x11)/'serviceNotSupportedInActiveSession'(0x7F) => not there.
    Anything else (positive, or another NRC) => the ECU recognises the service.
    """
    out: list[tuple[int, str, str]] = []
    for sid in sorted(nrc.SERVICES):
        r = client.request([sid], timeout=timeout)
        if r is None:
            continue
        if not r.positive and r.nrc in (0x11, 0x7F):
            continue
        verdict = "positive" if r.positive else f"NRC 0x{r.nrc:02X} {r.nrc_name}"
        out.append((sid, nrc.service_name(sid), verdict))
        print(f"  0x{sid:02X} {nrc.service_name(sid):<32} supported  ({verdict})")
    return out


def did_scan(client: UdsClient, start: int = 0xF180, end: int = 0xF1FF,
             timeout: float = 0.3) -> list[tuple[int, str, bytes | None]]:
    """ReadDataByIdentifier (0x22) sweep. Records readable DIDs and security-locked ones."""
    out: list[tuple[int, str, bytes | None]] = []
    for did in range(start, end + 1):
        r = client.read_data_by_identifier(did, timeout=timeout)
        if r is None:
            continue
        if r.positive:
            # positive: echoes the DID (2 bytes) then the value
            value = r.data[2:] if len(r.data) >= 2 else r.data
            out.append((did, "readable", value))
            print(f"  DID 0x{did:04X}  readable : {value.hex(' ')}")
        elif r.nrc == 0x33:
            out.append((did, "security-locked", None))
            print(f"  DID 0x{did:04X}  locked   (securityAccessDenied)")
        # NRC 0x31 requestOutOfRange => DID absent, skip quietly
    return out


def check_security(client: UdsClient, level: int = 0x01, timeout: float = 0.5) -> None:
    """Request a SecurityAccess (0x27) seed - the core research target."""
    r = client.security_access_request_seed(level, timeout=timeout)
    print(f"\n== SecurityAccess (0x27), level 0x{level:02X} ==")
    if r is None:
        print("  no response.")
    elif r.positive:
        seed = r.data[1:] if r.data else b""
        print(f"  seed received: {seed.hex(' ') or '(empty - already unlocked?)'}")
        print("  ==> 0x27 is PRESENT. This is the Phase 4 side-channel target.")
    else:
        print(f"  NRC 0x{r.nrc:02X} {r.nrc_name}"
              + ("  (present but refused in this session)" if r.nrc != 0x11 else "  (not supported)"))


# --------------------------------------------------------------------------------- CLI
def main() -> int:
    cfg = load_config()
    ap = argparse.ArgumentParser(description="VULCAN UDS discovery (Phase 2).")
    ap.add_argument("--channel", default=cfg["channel"])
    ap.add_argument("--tx", type=_hexint, default=cfg["tx"], help="diagnostic request ID (hex)")
    ap.add_argument("--rx", type=_hexint, default=cfg["rx"], help="diagnostic response ID (hex)")
    ap.add_argument("--find", action="store_true", help="scan for ECU (tx,rx) pairs")
    ap.add_argument("--find-range", nargs=2, type=_hexint, default=[0x700, 0x7FF],
                    metavar=("START", "END"))
    ap.add_argument("--services", action="store_true", help="probe supported services")
    ap.add_argument("--did-scan", nargs=2, type=_hexint, metavar=("START", "END"))
    ap.add_argument("--sec", action="store_true", help="check SecurityAccess 0x27")
    args = ap.parse_args()

    print(f"# VULCAN UDS discovery on {args.channel}\n")

    if args.find or (args.tx is None and not any([args.services, args.did_scan, args.sec])):
        print(f"Scanning 0x{args.find_range[0]:03X}-0x{args.find_range[1]:03X} for ECUs...")
        ecus = find_ecus(args.channel, range(args.find_range[0], args.find_range[1] + 1))
        if not ecus:
            print("  no ECU answered. (Cluster asleep? wrong bus? no diagnostics enabled?)")
            return 0
        if args.tx is None:
            args.tx, args.rx = ecus[0]
            print(f"\nUsing first ECU: tx=0x{args.tx:03X} rx=0x{args.rx:03X}")

    if args.tx is None or args.rx is None:
        print("\nNo diagnostic (tx,rx) pair set. Use --find or pass --tx/--rx.")
        return 0

    with UdsClient(args.channel, args.tx, args.rx) as ecu:
        print(f"\n== Open extended session (0x10 0x03) on tx=0x{args.tx:03X} ==")
        r = ecu.diagnostic_session_control(0x03)
        print(f"  {r}" if r else "  no response (is the ECU awake?)")

        want_all = not any([args.services, args.did_scan, args.sec])
        if args.services or want_all:
            print("\n== Service probe ==")
            probe_services(ecu)
        if args.did_scan or want_all:
            s, e = (args.did_scan or (0xF180, 0xF1FF))
            print(f"\n== DID scan 0x{s:04X}-0x{e:04X} ==")
            did_scan(ecu, s, e)
        if args.sec or want_all:
            check_security(ecu)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
