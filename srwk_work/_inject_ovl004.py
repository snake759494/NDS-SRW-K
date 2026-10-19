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


OVL_BASE = 0x021E6700          # ovl_004 load address (shared window with ovl_003)
KIZUNA_FULL_PTR = 0x36a20      # spirit 絆 record: +0 full name, +4 short name
KIZUNA_SHORT = 0x350bc         # 1-glyph short-name slot (4 bytes)


def kizuna():
    """絆 was 「반」 (on-yomi of the kanji) in both names. The full name becomes
    「인연」 (matches the battle line 「인연이 빛난다!」, issue #8); it lives in arm9
    because ovl_004 has no free room. Short name -> 「인」 like 열(열혈), 집(집중)."""
    import json, os
    if not os.path.exists('kr/arm9_extra.json'):
        print('  (kr/arm9_extra.json missing: run the arm9 stage first)'); return
    addr = json.load(open('kr/arm9_extra.json'))['kizuna_full']
    data = bytearray(open(OUT, 'rb').read())
    assert struct.unpack_from('<I', data, KIZUNA_FULL_PTR)[0] == OVL_BASE + KIZUNA_SHORT
    struct.pack_into('<I', data, KIZUNA_FULL_PTR, addr)
    data[KIZUNA_SHORT:KIZUNA_SHORT + 2] = enc('인')
    open(OUT, 'wb').write(data)
    print(f'  spirit 絆: full name -> 0x{addr:08x} (인연), short -> 인')


if __name__ == "__main__":
    main()
    kizuna()
