#!/usr/bin/env python3
"""VULCAN - Phase 1 cartography of a candump (-l) capture log.

Reads a `candump -l` log and, for every CAN arbitration ID, reports:
  - frame count and share of the bus,
  - mean period (ms) and frequency (Hz) from the timestamps,
  - payload length (DLC),
  - a per-byte activity map: '.' static, '~' low-variation (counter/state),
    '#' high-variation (a live signal),
and flags IDs in the UDS diagnostic range (0x700-0x7FF).

Pure standard library - no dependencies. Usage:
    python3 src/mapping/cartography.py <logfile> [--top N]
"""
from __future__ import annotations
import re, sys
from collections import defaultdict

LINE = re.compile(r'\(([\d.]+)\)\s+\S+\s+([0-9A-Fa-f]+)#([0-9A-Fa-f]*)')


def byte_class(nvals: int) -> str:
    if nvals <= 1:
        return '.'          # constant
    if nvals <= 6:
        return '~'          # counter / a few states
    return '#'              # busy signal


def main() -> int:
    if len(sys.argv) < 2:
        sys.exit("usage: python3 cartography.py <logfile> [--top N]")
    path = sys.argv[1]
    top = None
    if '--top' in sys.argv:
        top = int(sys.argv[sys.argv.index('--top') + 1])

    ids: dict[int, dict] = defaultdict(
        lambda: {'ts': [], 'dlc': set(), 'bytes': defaultdict(set)})
    total = 0
    t0 = t1 = None
    with open(path) as fh:
        for line in fh:
            m = LINE.match(line.strip())
            if not m:
                continue
            ts, cid_s, data = m.groups()
            ts = float(ts)
            cid = int(cid_s, 16)
            b = bytes.fromhex(data) if data else b''
            rec = ids[cid]
            rec['ts'].append(ts)
            rec['dlc'].add(len(b))
            for i, byte in enumerate(b):
                rec['bytes'][i].add(byte)
            total += 1
            t0 = ts if t0 is None else t0
            t1 = ts

    rows = []
    for cid, rec in ids.items():
        cnt = len(rec['ts'])
        dur = rec['ts'][-1] - rec['ts'][0]
        period = (dur / (cnt - 1) * 1000) if cnt > 1 and dur > 0 else 0.0
        dlc = max(rec['dlc']) if rec['dlc'] else 0
        amap = ''.join(byte_class(len(rec['bytes'].get(i, ()))) for i in range(dlc))
        rows.append((cid, cnt, period, dlc, amap))
    rows.sort(key=lambda r: -r[1])

    span = (t1 - t0) if (t0 and t1) else 0
    print(f"# VULCAN cartography - {path.split('/')[-1]}")
    print(f"{total:,} frames, {len(ids)} distinct IDs, {span:.1f} s capture\n")
    print(f"{'ID':>5} {'count':>8} {'bus%':>5} {'period':>9} {'freq':>8} {'dlc':>3}  byte-map")
    print(f"{'':->5} {'':->8} {'':->5} {'':->9} {'':->8} {'':->3}  {'':->10}")
    shown = rows[:top] if top else rows
    for cid, cnt, per, dlc, amap in shown:
        share = 100 * cnt / total
        freq = (1000 / per) if per > 0 else 0
        diag = '  <- diag range' if 0x700 <= cid <= 0x7FF else ''
        pers = f"{per:>7.1f}ms" if per else "   once"
        print(f"0x{cid:03X} {cnt:>8,} {share:>4.1f}% {pers:>9} {freq:>6.1f}Hz {dlc:>3}  {amap}{diag}")
    if top and len(rows) > top:
        print(f"... {len(rows) - top} more IDs")

    diag = [r for r in rows if 0x700 <= r[0] <= 0x7FF]
    print(f"\n== UDS diagnostic-range IDs (0x700-0x7FF): {len(diag)} ==")
    if diag:
        for cid, cnt, per, dlc, amap in diag:
            print(f"   0x{cid:03X}  ({cnt} frames)")
    else:
        print("   none - normal for a passive capture (diagnostics appear only when a")
        print("   tester actively queries). These are the IDs we'll uncover in Phase 2.")
    print("\nlegend:  . constant   ~ counter/few-states   # live signal")
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
