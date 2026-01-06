#!/usr/bin/env python3
from __future__ import annotations

import argparse
import re
from pathlib import Path
from typing import Iterable, List, Set


def extract_ascii_strings(data: bytes, min_len: int = 4, max_len: int = 80) -> List[str]:
    """Extract printable ASCII strings from a byte blob.

    This is a tiny, cross-platform replacement for the `strings` command so the repo
    works on older macOS installs and minimal Linux environments.
    """
    out: List[str] = []
    buf: bytearray = bytearray()

    def flush():
        nonlocal buf
        if min_len <= len(buf) <= max_len:
            try:
                out.append(buf.decode("ascii", errors="ignore"))
            except Exception:
                pass
        buf = bytearray()

    for b in data:
        if 32 <= b <= 126:  # printable ASCII
            buf.append(b)
            if len(buf) > max_len:
                # too long; flush and restart
                flush()
        else:
            flush()
    flush()
    return out


def main() -> int:
    ap = argparse.ArgumentParser(
        description="Extract likely OSC address strings from the Samplebrain executable (best-effort).\n"
                    "Tip: run this first, then probe candidates with tools/sb_probe.py"
    )
    ap.add_argument("--binary", required=True, help="Path to Samplebrain executable or any binary blob to scan")
    ap.add_argument("--min-len", type=int, default=4)
    ap.add_argument("--max-len", type=int, default=80)
    ap.add_argument("--filter", default="/", help="Substring filter (default: '/')")
    ap.add_argument("--regex", default=None, help="Optional regex filter applied after substring filter")
    ap.add_argument("--limit", type=int, default=500, help="Max strings to print")
    args = ap.parse_args()

    p = Path(args.binary)
    if not p.exists():
        raise SystemExit(f"[sb_strings] binary not found: {p}")

    data = p.read_bytes()
    strings = extract_ascii_strings(data, min_len=args.min_len, max_len=args.max_len)

    filt = args.filter
    rx = re.compile(args.regex) if args.regex else None

    uniq: List[str] = []
    seen: Set[str] = set()
    for s in strings:
        if filt and filt not in s:
            continue
        if rx and not rx.search(s):
            continue
        if s in seen:
            continue
        seen.add(s)
        uniq.append(s)

    # OSC-ish heuristic: prefer things that start with '/'
    uniq.sort(key=lambda x: (0 if x.startswith("/") else 1, len(x), x))

    print(f"[sb_strings] scanned: {p}")
    print(f"[sb_strings] candidates: {len(uniq)} (printing up to {args.limit})")
    for s in uniq[: args.limit]:
        print(s)

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
