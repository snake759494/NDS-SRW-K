# -*- coding: utf-8 -*-
"""extract_roms.py — unpack the two source ROMs into jp/ and kr/.

Every other tool reads its inputs from these two trees rather than from the ROMs
directly, so this is the first thing to run on a fresh clone:

    python extract_roms.py

  jp/  <- Super Robot Wars K (Japan).nds            (CRC32 D16DB8AF)
  kr/  <- Super Robot Wars K (Korean)-기존패치.nds   (YameSoft's Korean patch)

Neither ROM is in this repository; supply your own (see docs/BUILD.md).
"""
import io, os, sys, zlib
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')
from srwk_rom import Rom

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
os.chdir(HERE)

SOURCES = [
    ('jp', os.path.join(ROOT, 'Super Robot Wars K (Japan).nds'), 0xD16DB8AF),
    ('kr', os.path.join(ROOT, 'Super Robot Wars K (Korean)-기존패치.nds'), None),
]
# files each tool expects to find; everything else in the ROM is left alone
WANTED = ['data/add01dat.bin', 'data/add02dat.bin', 'data/add03dat.bin',
          'data/add04dat.bin', 'data/add05dat.bin', 'data/add08dat.bin',
          'btlPicDat.bin', 'btlCutinPicData.bin']


def dump(tag, path, want_crc):
    if not os.path.exists(path):
        print(f'  !! {path} not found — skipping {tag}/')
        return False
    crc = zlib.crc32(open(path, 'rb').read()) & 0xFFFFFFFF
    if want_crc and crc != want_crc:
        print(f'  !! {tag}: CRC32 {crc:08X}, expected {want_crc:08X} — wrong ROM?')
        return False
    rom = Rom(path)
    n = 0
    for name in WANTED:
        if name not in rom.ids:
            continue
        out = os.path.join(tag, name)
        os.makedirs(os.path.dirname(out), exist_ok=True)
        open(out, 'wb').write(rom.get(name)); n += 1
    open(os.path.join(tag, 'arm9.bin'), 'wb').write(rom.rom.arm9)
    open(os.path.join(tag, 'arm7.bin'), 'wb').write(rom.rom.arm7)
    open(os.path.join(tag, 'arm9ovt.bin'), 'wb').write(rom.rom.arm9OverlayTable)
    os.makedirs(os.path.join(tag, 'overlays'), exist_ok=True)
    n_ov = len(rom.rom.arm9OverlayTable) // 32
    for i in range(n_ov):
        open(os.path.join(tag, 'overlays', f'ovl_{i:03d}.bin'), 'wb').write(rom.rom.files[i])
    print(f'  {tag}/ : CRC32 {crc:08X} | {n} archives + arm9/arm7 + {n_ov} overlays')
    return True


if __name__ == '__main__':
    print('extracting source ROMs')
    ok = all([dump(*s) for s in SOURCES])
    print('done' if ok else 'INCOMPLETE — see messages above')
    sys.exit(0 if ok else 1)
