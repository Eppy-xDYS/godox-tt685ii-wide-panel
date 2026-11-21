#!/usr/bin/env python3
"""Decode first-generation Godox TT685 .fri firmware files to Intel HEX text.

Each byte after the header is bit-rotated left by (i % 4) + 2, where i is the
byte's index after the header. The result is Intel HEX for an AVR MCU.

Usage: python decode_fri.py input.fri output.hex [header_len]
"""
import sys


def rol8(b: int, n: int) -> int:
    return ((b << n) | (b >> (8 - n))) & 0xFF


def main() -> None:
    if len(sys.argv) < 3:
        sys.exit(__doc__)
    header_len = int(sys.argv[3]) if len(sys.argv) > 3 else 32
    data = open(sys.argv[1], "rb").read()[header_len:]
    out = bytes(rol8(b, (i % 4) + 2) for i, b in enumerate(data))
    open(sys.argv[2], "wb").write(out)
    print(f"wrote {len(out)} bytes of Intel HEX to {sys.argv[2]}")


if __name__ == "__main__":
    main()
