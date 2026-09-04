# -*- coding: utf-8 -*-
"""Patch the ovl_004 support-count label in place.

The Korean base patch already contains the translated label, but one syllable
is a typo: 원호방어회수 should be 원호방어횟수.  Both strings occupy the same
number of Korean font slots, so the replacement preserves the overlay size and
all code/data addresses.
"""
import struct

from srwk_codec import HAN2CODE

SRC = "kr/overlays/ovl_004.bin"
OUT = "kr/overlays/ovl_004_patched.bin"
OLD = "원호방어회수"
NEW = "원호방어횟수"


def enc(text):
    out = bytearray()
    for ch in text:
        if ch not in HAN2CODE:
            raise ValueError(f"unencodable character {ch!r}")
        out += struct.pack(">H", HAN2CODE[ch])
    return bytes(out)


def main():
    old = enc(OLD)
    new = enc(NEW)
    assert len(old) == len(new)
    data = bytearray(open(SRC, "rb").read())
    assert data.count(old) == 1, f"expected one {OLD!r} occurrence"
    data[:] = data.replace(old, new)
    assert data.count(old) == 0
    assert data.count(new) == 1
    open(OUT, "wb").write(data)
    print(f"patched {OLD} -> {NEW} ({len(data)} bytes): {OUT}")


if __name__ == "__main__":
    main()
