"""VULCAN - a minimal virtual UDS ECU, for testing the client on vcan0.

Answers a handful of UDS services so `discovery.py` can be exercised end-to-end
without the real cluster. Mirrors the client: it listens on the client's tx ID and
answers on the client's rx ID.

    # terminal A
    bash src/bringup/vcan_up.sh
    python -m src.uds.sim_ecu --channel vcan0
    # terminal B
    python -m src.uds.discovery --channel vcan0 --find
"""
from __future__ import annotations

import argparse
import time

import can
import isotp

# DIDs this virtual ECU exposes (0x22). Values echo the REAL cluster's identifiers.
DIDS: dict[int, bytes] = {
    0xF190: b"VF1RFA00000VULCAN",        # VIN (fake, 17 chars)
    0xF18C: b"LCBDX12867",               # ECU serial (real, from the cluster label)
    0xF194: b"SW08.13",                  # software version (real)
    0xF191: b"VPFRRF-14B115-AD",         # hardware version (real)
    0xF187: b"248106952R",               # spare part number (real cluster ref)
}
LOCKED_DID = 0xF1A0                       # returns securityAccessDenied
SUPPORTED = {0x10, 0x11, 0x19, 0x22, 0x27, 0x31, 0x3E}
SEED = bytes([0xDE, 0xAD, 0xBE, 0xEF])   # fixed SecurityAccess seed


def handle(req: bytes) -> bytes | None:
    """Return the UDS response payload for a request, or None to stay silent."""
    if not req:
        return None
    sid = req[0]
    if sid not in SUPPORTED:
        return bytes([0x7F, sid, 0x11])                      # serviceNotSupported

    if sid == 0x10:                                          # DiagnosticSessionControl
        if len(req) < 2:
            return bytes([0x7F, sid, 0x13])                  # incorrectMessageLength
        return bytes([0x50, req[1], 0x00, 0x32, 0x01, 0xF4])
    if sid == 0x3E:                                          # TesterPresent
        return bytes([0x7E, req[1] if len(req) > 1 else 0x00])
    if sid == 0x22:                                          # ReadDataByIdentifier
        if len(req) < 3:
            return bytes([0x7F, sid, 0x13])
        did = (req[1] << 8) | req[2]
        if did == LOCKED_DID:
            return bytes([0x7F, sid, 0x33])                  # securityAccessDenied
        if did in DIDS:
            return bytes([0x62, req[1], req[2]]) + DIDS[did]
        return bytes([0x7F, sid, 0x31])                      # requestOutOfRange
    if sid == 0x27:                                          # SecurityAccess
        if len(req) < 2:
            return bytes([0x7F, sid, 0x13])
        level = req[1]
        if level % 2 == 1:                                   # odd = request seed
            return bytes([0x67, level]) + SEED
        return bytes([0x7F, sid, 0x35])                      # even w/o valid key = invalidKey
    if sid == 0x11:                                          # ECUReset
        if len(req) < 2:
            return bytes([0x7F, sid, 0x13])
        return bytes([0x51, req[1]])
    if sid == 0x19:                                          # ReadDTCInformation
        return bytes([0x59, req[1] if len(req) > 1 else 0x02, 0xFF, 0x00])
    if sid == 0x31:                                          # RoutineControl
        if len(req) < 4:
            return bytes([0x7F, sid, 0x13])
        return bytes([0x71, req[1], req[2], req[3]])
    return bytes([0x7F, sid, 0x11])


def main() -> int:
    ap = argparse.ArgumentParser(description="Virtual UDS ECU for vcan testing.")
    ap.add_argument("--channel", default="vcan0")
    ap.add_argument("--rx", type=lambda s: int(s, 0), default=0x7E0, help="ID we listen on")
    ap.add_argument("--tx", type=lambda s: int(s, 0), default=0x7E8, help="ID we answer on")
    args = ap.parse_args()

    bus = can.Bus(channel=args.channel, interface="socketcan", receive_own_messages=False)
    addr = isotp.Address(isotp.AddressingMode.Normal_11bits, txid=args.tx, rxid=args.rx)
    stack = isotp.CanStack(bus=bus, address=addr, params={"tx_padding": 0x00})
    print(f"virtual ECU up on {args.channel}: listening 0x{args.rx:03X}, answering 0x{args.tx:03X}")
    print("services: " + " ".join(f"0x{s:02X}" for s in sorted(SUPPORTED)) + "   (Ctrl+C to stop)")
    try:
        while True:
            stack.process()
            if stack.available():
                req = stack.recv()
                resp = handle(req)
                print(f"  <- {req.hex(' ')}   -> {resp.hex(' ') if resp else '(silent)'}")
                if resp:
                    stack.send(resp)
                    while stack.transmitting():
                        stack.process()
                        time.sleep(stack.sleep_time())
            time.sleep(stack.sleep_time())
    except KeyboardInterrupt:
        print("\nstopped.")
    finally:
        bus.shutdown()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
