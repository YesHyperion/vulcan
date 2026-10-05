#!/usr/bin/env python3
"""VULCAN - Phase 0 sanity check.

Opens the CAN bus defined in config/bus.yaml and listens for a few seconds,
reporting how many frames arrive and from which arbitration IDs. This is the
first "is anything alive on the bus?" check after power-up and bring_up_can.sh.

It reads the interface/bitrate from config/bus.yaml so nothing is hard-coded
(PROJECT.md §8). Requires: python-can, pyyaml. Does not transmit anything.
"""
from __future__ import annotations

import argparse
import collections
import pathlib
import sys
import time

REPO_ROOT = pathlib.Path(__file__).resolve().parents[2]
CONFIG = REPO_ROOT / "config" / "bus.yaml"


def load_bus_config() -> dict:
    try:
        import yaml
    except ImportError:
        sys.exit("missing dependency: pyyaml  (pip install -r requirements.txt)")
    with CONFIG.open() as fh:
        return yaml.safe_load(fh)["interface"]


def main() -> int:
    ap = argparse.ArgumentParser(description="Passive CAN sanity check (listen-only).")
    ap.add_argument("-t", "--seconds", type=float, default=10.0,
                    help="how long to listen (default: 10s)")
    ap.add_argument("-c", "--channel", default=None,
                    help="override the SocketCAN channel from config/bus.yaml "
                         "(e.g. vcan0 for a hardware-free test)")
    args = ap.parse_args()

    try:
        import can
    except ImportError:
        sys.exit("missing dependency: python-can  (pip install -r requirements.txt)")

    cfg = load_bus_config()
    channel = args.channel or cfg["channel"]
    bustype = cfg["bustype"]
    print(f"listening on {channel} ({bustype}) for {args.seconds:g}s - no frames sent")

    counts: collections.Counter = collections.Counter()
    total = 0
    # receive_own_messages=False + a listen-only stance: we never call bus.send() here.
    with can.Bus(channel=channel, interface=bustype) as bus:
        deadline = time.time() + args.seconds
        while time.time() < deadline:
            msg = bus.recv(timeout=0.5)
            if msg is None:
                continue
            total += 1
            counts[msg.arbitration_id] += 1

    print(f"\n{total} frames, {len(counts)} distinct arbitration IDs")
    for arb_id, n in sorted(counts.items()):
        print(f"  0x{arb_id:03X}: {n}")
    if total == 0:
        print("\n(no traffic - normal for an isolated cluster, or check bitrate/wiring)")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
