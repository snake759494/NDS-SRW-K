# -*- coding: utf-8 -*-
"""export_data.py — produce the publishable translation data for the repository.

The working JSONs carry the Japanese original in a `jp` field purely as a
translator's reference; the builders never read it (see build_native.py /
build_battle.py). Publishing it would mean redistributing the game's script, so
the repo copies ship **Korean-only**. `restore_jp.py` puts `jp` back from your
own ROM whenever you want it for editing.

    python export_data.py           # write ../_repo/data/*.json
"""
import io, os, sys, json, copy
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')

HERE = os.path.dirname(os.path.abspath(__file__))
os.chdir(HERE)
# repo layout: <root>/data ; author's tree keeps the repo clone in _repo/
_D = [os.path.join(os.path.dirname(HERE), 'data'),
      os.path.join(os.path.dirname(HERE), '_repo', 'data')]
OUT = next((d for d in _D if os.path.isdir(d)), _D[0])

SCEN_ABOUT = ("SRW K 시나리오 — 대사 박스 단위 편집용. 각 항목의 'ko'(한국어)만 수정하세요. "
              "c1=화자/초상화, c2=플래그, name=이름오버라이드, sec=섹션시작 — 모두 그대로 유지(빌드용). "
              "①②③ 등 동그라미 숫자는 게임이 런타임에 캐릭터 이름으로 치환하는 자리표시자 — 번역/삭제 금지. "
              "줄당 최대 176px(한글 12/그외 8). 일본어 원문은 저작권상 포함하지 않습니다 — "
              "`python restore_jp.py`로 본인 ROM에서 복원해 넣을 수 있습니다. "
              "빌드: rebuild_all.py (또는 build_native.py → build_rom_all.py).")
BATTLE_ABOUT = ("SRW K 전투대사(add05dat.bin). 'ko'만 편집. 줄당 폭<=176px(한글12/그외8). "
                "표는 반각 '!' ' ' '…' '。' '·' 사용(전각 '！？　，、' 없음). "
                "sp(화자코드)와 보이스라인/서브라인(;) 구조는 그대로 유지. "
                "일본어 원문은 포함하지 않습니다 — restore_jp.py로 복원 가능.")


def strip_jp(obj):
    """Recursively drop every 'jp' key, keeping everything the builders use."""
    if isinstance(obj, dict):
        return {k: strip_jp(v) for k, v in obj.items() if k != 'jp'}
    if isinstance(obj, list):
        return [strip_jp(v) for v in obj]
    return obj


def dump(path, obj):
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with io.open(path, 'w', encoding='utf-8') as f:
        json.dump(obj, f, ensure_ascii=False, indent=1)
    return os.path.getsize(path)


def main():
    sc = json.load(io.open('srwk_scenario_clean.json', encoding='utf-8'))
    sc = strip_jp(sc); sc['_about'] = SCEN_ABOUT
    n1 = dump(os.path.join(OUT, 'scenario_ko.json'), sc)

    bt = json.load(io.open('srwk_battle.json', encoding='utf-8'))
    bt = strip_jp(bt); bt['_about'] = BATTLE_ABOUT
    n2 = dump(os.path.join(OUT, 'battle_ko.json'), bt)

    cr = json.load(io.open('_credits_tr.json', encoding='utf-8'))
    n3 = dump(os.path.join(OUT, 'credits_ko.json'), cr)

    for name, n, src in (('scenario_ko.json', n1, 'srwk_scenario_clean.json'),
                         ('battle_ko.json', n2, 'srwk_battle.json'),
                         ('credits_ko.json', n3, '_credits_tr.json')):
        o = os.path.getsize(src)
        print(f'  {name:20} {n/1024:8.1f} KB  (원본 {o/1024:.1f} KB, 일본어 원문 제거)')
    # sanity: nothing named 'jp' survived
    blob = io.open(os.path.join(OUT, 'scenario_ko.json'), encoding='utf-8').read()
    assert '"jp"' not in blob, 'jp field leaked into the published data!'
    print('  검증: 공개 데이터에 "jp" 필드 없음 OK')


if __name__ == '__main__':
    main()
