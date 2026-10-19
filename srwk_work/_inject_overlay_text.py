# -*- coding: utf-8 -*-
"""_inject_overlay_text.py — fix YameSoft overlay strings in place (v1.30).

YameSoft wrote a word break as TWO half-width spaces (0x20 0x20) so the 2-byte
alignment survives. Several renderers read strictly 2 bytes per glyph and give up
on the whole string when they meet the pair 0x2020: the post-ending save prompt
「타이틀로  돌아갑니다  좋습니까？」 (ovl_015) showed an EMPTY box (issue #8).
Replace each pair with the SJIS full-width space 0x8140 — same length, so no
offsets move. Only strings that sit where the JP overlay also has text are
touched, so code/data never changes. Plus explicit text fixes (TEXT).

Writes kr/overlays/ovl_NNN_patched.bin (starting from an existing patched file
when there is one, e.g. ovl_003/ovl_004). build_rom_all injects every patched
overlay whose size matches."""
import io, os, sys, glob, struct
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')
from srwk_codec import HAN2CODE

TEXT = {   # (overlay, offset): new Korean text (must fit the original slot)
    (14, 0x05154): '이대로　괜찮습니까？',     # これでよろしいですか？ (was 「이것으로  좋습니까か？」)
}

def enc(s):
    out = bytearray()
    for ch in s:
        if ch in HAN2CODE: out += struct.pack('>H', HAN2CODE[ch])
        else: out += ch.encode('cp932')
    return bytes(out)

def jp_text_starts(jp):
    """offsets where the JP overlay has a NUL-terminated SJIS text string."""
    out = set(); i = 0
    while i < len(jp):
        if jp[i] >= 0x81 and (i == 0 or jp[i-1] == 0):
            j = jp.find(b'\x00', i)
            if j < 0: break
            try:
                s = jp[i:j].decode('cp932')
                if len(s) >= 2: out.add(i)
            except UnicodeDecodeError:
                pass
            i = j + 1
        else:
            i += 1
    return out

def fix_pairs(buf, off, jp):
    """walk one string; replace 0x20 0x20 at a character boundary with 0x8140."""
    i = off; n = 0
    while i < len(buf) and buf[i] != 0:
        b = buf[i]
        if b >= 0x81:
            i += 2
        elif b == 0x20 and i + 1 < len(buf) and buf[i+1] == 0x20 and jp[i:i+2] != b'  ':
            buf[i:i+2] = b'\x81\x40'; n += 1; i += 2
        else:
            i += 1
    return n

total = 0; written = []
for jpf in sorted(glob.glob('jp/overlays/ovl_*.bin')):
    idx = int(os.path.basename(jpf)[4:7])
    krp = f'kr/overlays/ovl_{idx:03d}_patched.bin'
    src = krp if os.path.exists(krp) else f'kr/overlays/ovl_{idx:03d}.bin'
    jp = open(jpf, 'rb').read(); kr = bytearray(open(src, 'rb').read())
    if len(jp) != len(kr):
        continue
    orig = bytes(kr); n = 0
    for off in sorted(jp_text_starts(jp)):
        if kr[off] >= 0x81 or kr[off] == 0x20:
            n += fix_pairs(kr, off, jp)
    for (o, off), ko in TEXT.items():
        if o != idx: continue
        b = enc(ko); end = off
        while orig[end] != 0: end += 1
        slot = end - off
        assert len(b) <= slot, (o, hex(off), len(b), slot)
        kr[off:off+len(b)] = b
        for k in range(off+len(b), end): kr[k] = 0
        n += 1
    if bytes(kr) != orig:
        assert len(kr) == len(orig)
        if '--write' in sys.argv:
            open(krp, 'wb').write(bytes(kr))
        written.append((idx, n)); total += n
print(f'overlays fixed: {len(written)}  edits: {total}')
for idx, n in written: print(f'  ovl_{idx:03d}: {n}')
if '--write' not in sys.argv: print('(dry run — pass --write to save)')
