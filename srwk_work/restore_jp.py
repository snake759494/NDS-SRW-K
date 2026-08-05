# -*- coding: utf-8 -*-
"""restore_jp.py — put the Japanese reference text back into the translation data.

The published JSONs are Korean-only: the game's original script is not ours to
redistribute. Translating is much easier with the original in view, so this
re-extracts it from *your* copy of the Japanese ROM and merges it back in as the
`jp` field, exactly as the working files had it.

    python restore_jp.py            # data/*_ko.json -> srwk_*.json (with jp)

Requires jp/ (run extract_roms.py first). The builders ignore `jp`, so the result
builds byte-identically either way.
"""
import io, os, sys, json
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')

HERE = os.path.dirname(os.path.abspath(__file__))
os.chdir(HERE)


def pick(*cands):
    for c in cands:
        if os.path.exists(c):
            return c
    return None


def restore_scenario():
    src = pick('data/scenario_ko.json', '../_repo/data/scenario_ko.json')
    if not src:
        print('  scenario: 한국어 데이터 없음 — 건너뜀'); return
    import extract_native
    ko = json.load(io.open(src, encoding='utf-8'))
    jp = extract_native.extract(rom_path=None, side='jp')   # {block: [[lines],...]}
    n = 0
    for bkey, blk in ko['scenarios'].items():
        ref = jp.get(int(bkey)) or jp.get(bkey) or []
        for i, box in enumerate(blk['boxes']):
            box['jp'] = ref[i] if i < len(ref) else []
            n += 1
    out = 'srwk_scenario_clean.json'
    json.dump(ko, io.open(out, 'w', encoding='utf-8'), ensure_ascii=False, indent=1)
    print(f'  scenario: {n} boxes -> {out}')


def restore_battle():
    src = pick('data/battle_ko.json', '../_repo/data/battle_ko.json')
    if not src:
        print('  battle: 한국어 데이터 없음 — 건너뜀'); return
    import extract_battle
    ko = json.load(io.open(src, encoding='utf-8'))
    jp = extract_battle.extract(side='jp')
    n = 0
    for i, e in enumerate(ko['entries']):
        ref = jp[i] if i < len(jp) else None
        if ref is not None:
            e['jp'] = ref.get('ko', ref) if isinstance(ref, dict) else ref
            n += 1
    out = 'srwk_battle.json'
    json.dump(ko, io.open(out, 'w', encoding='utf-8'), ensure_ascii=False, indent=1)
    print(f'  battle: {n} entries -> {out}')


if __name__ == '__main__':
    if not os.path.isdir('jp'):
        print('ERROR: jp/ 추출본이 없습니다. 먼저 `python extract_roms.py`를 실행하세요.')
        sys.exit(1)
    print('일본어 원문 복원 (본인 ROM에서 추출)')
    restore_scenario()
    restore_battle()
