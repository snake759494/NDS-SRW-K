# -*- coding: utf-8 -*-
"""rebuild_all.py — regenerate EVERY patched binary from the stock extracts.

The individual `_inject_*.py` scripts each read the accumulated `kr/*_patched.bin`
and write it back, so on their own they only make sense in a particular order.
This script encodes that order, starting from the untouched YameSoft extracts, so
the whole patch can be rebuilt on a machine that has nothing but this repo plus
the two ROMs.

    python rebuild_all.py            # rebuild every patched binary, then the ROM
    python rebuild_all.py --verify   # also assert the result matches EXPECT_CRC
    python rebuild_all.py --stage add02   # rebuild one stage only

Order matters only where two steps touch the same block; `--verify` is the real
guarantee, so run it after changing anything here.
"""
import io, os, sys, glob, struct, zlib, shutil, subprocess

sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')
HERE = os.path.dirname(os.path.abspath(__file__))
os.chdir(HERE)
ROOT = os.path.dirname(HERE)

JP_ROM = os.path.join(ROOT, 'Super Robot Wars K (Japan).nds')
KR_ROM = os.path.join(ROOT, 'Super Robot Wars K (Korean)-기존패치.nds')
OUT_ROM = os.path.join(ROOT, 'Super Robot Wars K (Korean)-NEW.nds')

EXPECT_CRC = 0x37DD153B          # v1.31 result ROM
JP_CRC     = 0xD16DB8AF          # required Japanese base ROM

# ── stages ────────────────────────────────────────────────────────────────────
# Each stage: (name, stock source -> patched target, [scripts in order])
STAGES = [
    ('add02', [('kr/data/add02dat.bin', 'kr/add02_patched.bin')], [
        '_eyecatch_inject.py',       # 59 chapter eyecatch images            (v1.2)
        '_inject_misc_images.py',    # copyright / Bandai / save screens     (v1.3)
        '_inject_captions.py',       # time-skip captions                    (v1.5)
        '_inject_spirit.py',         # 51 spirit-command graphics       (v1.6/1.9)
        '_inject_battle_plates.py --write',  # battle ability/status atlas           (v1.7)
        '_inject_cmd1889.py --write',        # battle command kanji                  (v1.7)
        '_inject_userlogo.py --write',       # user-drawn title logo            (v1.11/12)
    ]),
    ('add04', [('kr/data/add04dat.bin', 'kr/add04_patched.bin')], [
        '_inject_plates.py',         # 96 ability/status plates              (v1.4)
        '_inject_titles.py',         # 14 series title cards                 (v1.4)
        '_inject_critical.py',       # クリティカル                          (v1.5)
        '_inject_muteki.py --write',         # 無敵 cut-in                           (v1.7)
    ]),
    # touches add02 AND add04, so it must run after both are otherwise complete
    ('widths', [], ['_fix_activation_widths.py --write']),                          # v1.15
    ('arm9', [('kr/arm9.bin', 'kr/arm9_patched.bin')], [
        '_inject_arm9.py',           # names / system messages
        '_inject_font.py --write',   # Galmuri11 dialogue font          (v1.13/14)
    ]),
    ('ovl_text', [('kr/overlays/ovl_004.bin', 'kr/overlays/ovl_004_patched.bin')], [
        '_inject_ovl004.py',         # support-count label typo (#43)
        '_inject_overlay_text.py --write',  # 0x20 0x20 -> 0x8140 in every overlay (v1.30)
    ]),
    ('credits', [('kr/overlays/ovl_003.bin', 'kr/overlays/ovl_003_patched.bin')],
        ['_inject_credits_fit.py --write',                                  # v1.17
         '_inject_overlay_text.py --write']),                               # v1.30
]


def die(msg):
    print('ERROR: ' + msg)
    sys.exit(1)


def crc32(path):
    h = 0
    with open(path, 'rb') as f:
        for chunk in iter(lambda: f.read(1 << 20), b''):
            h = zlib.crc32(chunk, h)
    return h & 0xFFFFFFFF


STOCK = ('jp/data/add02dat.bin', 'jp/data/add04dat.bin',
         'kr/data/add02dat.bin', 'kr/data/add04dat.bin',
         'kr/arm9.bin', 'kr/overlays/ovl_003.bin',
         'kr/overlays/ovl_004.bin')


def preflight(need_rom=True):
    """Fail loudly and early rather than half-way through a 10-minute rebuild.

    The injection stages read the extracted jp/ and kr/ trees, so they only need
    the ROMs the first time (to produce those trees). Packing the final .nds does
    need the Korean base ROM."""
    if any(not os.path.exists(p) for p in STOCK):
        if not os.path.exists(JP_ROM) or not os.path.exists(KR_ROM):
            die('extracted jp/ and kr/ trees are missing and the source ROMs are '
                'not here.\n       Put both ROMs next to srwk_work/ and run '
                'extract_roms.py — see docs/BUILD.md.')
        print('  stock extracts missing — running extract_roms.py')
        run('extract_roms.py')
    if os.path.exists(JP_ROM) and crc32(JP_ROM) != JP_CRC:
        die(f'Japanese ROM CRC32 is {crc32(JP_ROM):08X}, expected {JP_CRC:08X}.')
    if need_rom and not os.path.exists(KR_ROM):
        die(f'YameSoft Korean ROM not found: {KR_ROM}\n'
            '       it is the base the final .nds is packed into — see docs/BUILD.md.')
    # translation data: working copy or the repo's Korean-only copy, either is fine
    for alts in (('srwk_scenario_clean.json', 'data/scenario_ko.json'),
                 ('srwk_battle.json', 'data/battle_ko.json'),
                 ('_credits_tr.json', 'data/credits_ko.json')):
        if not any(os.path.exists(a) for a in alts):
            die('translation data missing: ' + ' / '.join(alts))
    if not os.path.exists('Galmuri11.ttf'):
        die('Galmuri11.ttf missing — see docs/BUILD.md (SIL OFL 1.1).')
    if sys.platform == 'win32' and not os.path.exists('C:/Windows/Fonts/malgunbd.ttf'):
        die('Malgun Gothic (malgun.ttf / malgunbd.ttf) not found in C:/Windows/Fonts.')


def run(script):
    args = script.split()
    print(f'  -> {args[0]}')
    r = subprocess.run([sys.executable] + args, capture_output=True)
    if r.returncode != 0:
        sys.stdout.write(r.stdout.decode('utf-8', 'replace')[-3000:])
        sys.stdout.write(r.stderr.decode('utf-8', 'replace')[-3000:])
        die(f'{args[0]} failed (exit {r.returncode})')
    return r.stdout.decode('utf-8', 'replace')


def rebuild(only=None):
    preflight(need_rom=not only)
    for name, seeds, scripts in STAGES:
        if only and name != only:
            continue
        print(f'[{name}]')
        for src, dst in seeds:                     # start from the stock extract
            os.makedirs(os.path.dirname(dst) or '.', exist_ok=True)
            shutil.copyfile(src, dst)
            print(f'  seed {dst} <- {src}')
        for s in scripts:
            run(s)
    if only:
        return
    print('[rom]')
    run('build_rom_all.py')


def verify():
    got = crc32(OUT_ROM)
    ok = got == EXPECT_CRC
    print(f'\nresult ROM CRC32 {got:08X} (expected {EXPECT_CRC:08X}) -> '
          + ('MATCH' if ok else 'MISMATCH'))
    return ok


if __name__ == '__main__':
    stage = None
    if '--stage' in sys.argv:
        stage = sys.argv[sys.argv.index('--stage') + 1]
    rebuild(stage)
    if '--verify' in sys.argv and not stage:
        sys.exit(0 if verify() else 1)
