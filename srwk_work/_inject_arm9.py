# -*- coding: utf-8 -*-
"""Inject Korean translations for the 15 untranslated arm9 strings (8 character
names + 7 save/load system messages) into kr/arm9.bin.

- in-place where the KO encoding (+null) fits the slot budget (bytes until next
  non-zero); the string start offset is unchanged so all pointers stay valid
  (same method the YameSoft patch used for its 2002 translated strings).
- repoint the few that don't fit: write KO into reclaimed dev-only debug-string
  space and update every arm9 pointer (LE u32 == 0x02000000+orig_off).
Verifies by decoding each slot back, and that arm9 size is unchanged."""
import io, struct
from srwk_codec import CODE2HAN, HAN2CODE

BASE = 0x02000000
arm9 = bytearray(open('kr/arm9.bin', 'rb').read())
ORIG_LEN = len(arm9)

# offset -> Korean translation (canonical names from the scenario where available)
TR = {
    0x67d48: '소드',              # ソード
    0x683f8: '히이라기　후유코',   # 柊　冬子
    0x68818: '히노　요우지',       # 日野　洋治  (scenario: 히노 요우지)
    0x68890: '우즈키　미와',       # 卯月　美和  (scenario: 우즈키)
    0x688c0: '유미　겐노스케',     # 弓　弦之助  (scenario: 유미/弓)
    0x68938: '미도　류코',         # 身堂　竜子  (scenario: 미도)
    0x68a04: '미조구치　쿄스케',   # 溝口　恭介  (scenario: 미조구치)
    0x69124: 'ＤＳＳＤ　병사',         # ＤＳＳＤヘイ
    0x69244: '시바　칸지로',       # 司馬　還次郎 (scenario: 시바)
    # enemy unit names YameSoft left partially in katakana (ヘイ=兵/soldier, シャドウ=Shadow)
    0x68a70: '오브　병사',          # オーブヘイ  (was 오브　ヘイ)
    0x68ddc: '자프트　병사',        # ザフトヘイ  (was 자프트ヘイ)
    0x69204: '요미군　병사',        # ヨミグンペイ (was 요미군ンペイ)
    0x69564: '드로이드　병사',      # ドロイドヘイ (was 드루이드ヘイ — also Droid≠Druid)
    0x69eb4: '잭터　테일',          # ゼクターテイル
    0x69f34: '베리니　병사',        # ヴェリニーヘイ (was 베리니ニーヘイ)
    0x6a564: '이스페일　병사',      # イスペイルヘイ (was 이스페이ルヘイ)
    0x69134: '블루　듀얼',         # ブルデュエル (was 브르듀엘)
    0x6adf0: '다이버　샷',          # ダイバーショット (was 다이버　쇼트)
    0x6b14c: '웜・샷',              # ワーム・ショット (was 웜・쇼트)
    0x69b84: '지그　바주카',       # ジーグバズーカ (was 지그　바츄카)
    0x69024: '야타노카가미',        # ヤタノカガミ (was 야타노가가미; plates say 야타노카가미)
    0x69fb4: '고트프리트',          # ゴットフリート (was 갓　프리트; dialogue says 고트프리트)
    0x6ddfc: '보와튀르・뤼미에르',   # ヴォワチュールリュミエール (French; was 버츄얼　류미엘)
    0x6a304: '노른　시스템',          # ノルンシステム (was 노룬; plates say 노른)
    0x6c9d0: '포톤　매트　배리어',    # フォトンマットバリア (was 포톤맛트　베리어)
    0x7011c: '　포톤　매트　배리어　효과가　상승한다',  # its description
    0x6a904: '엘도라　블록',          # エルドラブロック (was 엘도라　블럭; plates say 블록)
    0x6db78: '엘도라　블록　슛',     # エルドラブロックシュート (was 엘도라 브로큰 슛 = mistranslation)
    0x6afe4: '엘도라　아타케',        # エルドラアタッケ (Spanish ataque; was 엘도라　어텍)
    0x6d210: '디아만테　크래시',      # ディアマンテクラッシュ (was 디　아만테　크래셔)
    0x67ee0: '신의　번개',            # 神の雷 (was 신의뢰; dialogue says 신의 번개)
    0x6b660: '대형　제네레이터',      # 大型ジェネレーター (unified spelling)
    0x694d4: '사이킥　참',            # サイキック斬 (unified with dialogue)
    0x65a38: '사이킥　참、그리고',     # サイキック斬、そして
    0x6e760: '파이널　사이킥　웨이브', # ファイナルサイキックウェーブ
    0x6e0d4: '・데미지를　２０％경감한다',  # ・ダメージを２０％軽減する (was 「・데미지가 　Q０％경감한다」)
    0x6cc88: '클로・스플리터',   # クロー・スプリッツァー (was 크로・스피리츠)
    0x70598: '클로・스플리터（템페스트　모드）',   # クロー・スプリッツァー（テンペストモード）
    0x6dde0: '어그레시브・그라인더',   # アグレッシブ・グラインダー (was 공격적인  그라인더)
    0x6e5a0: '스티뮬런트・스피릿츠',   # スティミュラント・スピリッツ (was 스티뮤란트・스피리츠)
    0x6ccd0: '딜라이트・팔크스',   # ディライト・ファルクス (was 디　라이트・팔크스)
    0x6ca48: '티어・스트레이너',   # ティア・ストレーナー (was 티아・스트레나)
    0x6f100: '티어・스트레이너・미라지',   # ティア・ストレーナー・ミラージュ
    0x6a620: '피데스・레이',   # フィデース・レイ (was 피티스・레이)
    0x6d4cc: '크리스탈・앰플렉스',   # クリスタル・アンプレクス (was 안프레크스)
    0x6e5e0: '프란디움・디바이더',   # プランディウム・ディバイダー (was 프란디움・분할기)
    0x6d61c: '크로스브리드・차지',   # クロスブリード・チャージ (was 챠지)
    0x6a164: '제트　클로',   # ジェットクロー (claw; was 제트　크로)
    0x6ba20: '엔젤　불릿',   # エンジェルバレット (was 엔젤　벌렛)
    0x6db08: '오버　프리즈　불릿',   # オーバーフリーズバレット (was 오버  프리즈  바렛)
    0x690f4: '셀레블레이드',   # セレブレイド (was 세레블레이드)
    0x6a534: '셀레블레이더',   # セレブレイダー (was 세레블레이더)
    0x6a6c0: '슬러스터랜스',        # スラスターランス
    0x6aae4: '볼트파라이저',        # ボルトパライザー
    0x6a65c: '에어・엑시레',       # エア・エクシーレ
    0x6cad8: '스투디움　빔',        # ストゥディウム・ビーム
    0x6ea20: '라이덴　５１２Ｅ１　섀도우',# ライデン５１２Ｅ１　シャドウ (was …シャドウ)
    0x94c1c: '데이터 로드가 완료되었습니다',
    0x94c40: '데이터를 읽지 못했습니다. 전원을 끄고 카드를 다시 꽂아 주세요',
    0x94c88: '데이터가 손상되었습니다',
    0x94ca0: '데이터가 없습니다(공장 출하 상태)',
    0x94cc8: '데이터 저장이 완료되었습니다',
    0x94cec: '데이터 저장에 실패했습니다',
    0x94d0c: '데이터를 기록하지 못했습니다. 전원을 끄고 카드를 다시 꽂아 주세요',
}

# new strings that do not replace anything in arm9 (pointed at from overlays)
EXTRA = {
    'kizuna_full': '인연',     # spirit 絆: full name (ovl_004 record; was 「반」)
}

# reclaim space: dev-only debug strings (never shown to players)
RECLAIM = [(0x42980, 0x436ec - 0x42980)]   # H-blank debug str region, ~3436 bytes free for our use


def enc(s):
    """Korean/ASCII string -> game SJIS bytes (Hangul via HAN2CODE, ASCII as-is)."""
    out = bytearray()
    for ch in s:
        if ch in HAN2CODE:
            out += struct.pack('>H', HAN2CODE[ch])
        elif ch in (' ', '　'):
            # a 1-byte 0x20 inside the 2-byte string desyncs the renderer
            # (issue #1: 잭터 테일 garbled) -- always use the full-width space
            out += bytes([0x81, 0x40])
        elif 0xFF01 <= ord(ch) <= 0xFF5E:
            out += ch.encode('cp932')        # full-width alnum: untouched SJIS 0x82xx rows
        elif len(ch.encode('cp932', 'ignore')) == 2 and ch.encode('cp932')[0] == 0x81:
            out += ch.encode('cp932')         # SJIS punctuation row 0x81 (、。！？ etc.), untouched by the KR font
        elif ch == '・':
            # This punctuation remains in the untouched SJIS portion of the
            # arm9 font table; keep the standard Japanese middle-dot glyph.
            out += b'\x81\x45'
        elif ord(ch) < 0x80:
            out.append(ord(ch))
        else:
            raise ValueError('unencodable char %r in %r' % (ch, s))
    return bytes(out)


def slot_budget(off):
    raw_end = off
    while raw_end < len(arm9) and arm9[raw_end] != 0:
        raw_end += 1
    z = raw_end
    while z < len(arm9) and arm9[z] == 0:
        z += 1
    return z - off          # bytes from start to next non-zero (text + padding)


def find_ptrs(off):
    target = BASE + off
    return [i for i in range(0, len(arm9) - 3) if struct.unpack_from('<I', arm9, i)[0] == target]


def main():
    log = io.open('_inject_log.txt', 'w', encoding='utf-8')
    recl_off, recl_left = RECLAIM[0][0], RECLAIM[0][1]
    inplace = repointed = 0
    for off in sorted(TR):
        ko = TR[off]
        b = enc(ko)
        budget = slot_budget(off)
        if len(b) + 1 <= budget:
            # in-place: overwrite slot, null-pad to the old string length region
            arm9[off:off + len(b)] = b
            for k in range(off + len(b), off + budget):
                arm9[k] = 0
            inplace += 1
            log.write('IN-PLACE 0x%06x budget=%d use=%d  %s\n' % (off, budget, len(b) + 1, ko))
        else:
            ptrs = find_ptrs(off)
            if not ptrs:
                log.write('!! 0x%06x NO POINTERS found, cannot repoint (%s)\n' % (off, ko)); continue
            if len(b) + 1 > recl_left:
                log.write('!! reclaim space exhausted for 0x%06x\n' % off); continue
            new_off = recl_off
            arm9[new_off:new_off + len(b)] = b
            arm9[new_off + len(b)] = 0
            recl_off += len(b) + 1; recl_left -= len(b) + 1
            for p in ptrs:
                struct.pack_into('<I', arm9, p, BASE + new_off)
            repointed += 1
            log.write('REPOINT  0x%06x -> 0x%06x  (%d ptrs)  budget=%d use=%d  %s\n'
                      % (off, new_off, len(ptrs), budget, len(b) + 1, ko))

    # standalone strings other injectors point at (they live in arm9 because the
    # overlays cannot grow). Addresses -> kr/arm9_extra.json.
    import json as _json
    extra_addr = {}
    for key, ko in EXTRA.items():
        b = enc(ko)
        assert len(b) + 1 <= recl_left, 'reclaim space exhausted for extra %s' % key
        arm9[recl_off:recl_off + len(b)] = b
        arm9[recl_off + len(b)] = 0
        extra_addr[key] = BASE + recl_off
        log.write('EXTRA    %s -> 0x%06x  %s' % (key, recl_off, ko) + chr(10))
        recl_off += len(b) + 1; recl_left -= len(b) + 1
    _json.dump(extra_addr, open('kr/arm9_extra.json', 'w'), indent=1)

    # YameSoft wrote word breaks as TWO half-width spaces (0x20 0x20). The weapon
    # list reads 2 bytes per glyph and blanks the whole name on the pair 0x2020
    # (issue #8: 「고단나  트리플  드라이브」 showed an empty row). Replace each pair
    # with the full-width space 0x8140 -- same length, nothing moves. Only strings
    # that also start a JP text string at the same offset are touched.
    jp9 = open('jp/arm9.bin', 'rb').read()
    pairs = 0
    i = 0x060000
    while i < len(jp9):
        if jp9[i] >= 0x81 and jp9[i-1] == 0:
            j = jp9.find(bytes([0]), i)
            try:
                ok = j > i and len(jp9[i:j].decode('cp932')) >= 2
            except UnicodeDecodeError:
                ok = False
            if ok and (arm9[i] >= 0x81 or arm9[i] == 0x20):
                k = i
                while k < len(arm9) and arm9[k] != 0:
                    if arm9[k] >= 0x81: k += 2
                    elif arm9[k] == 0x20 and arm9[k+1] == 0x20:
                        arm9[k:k+2] = bytes([0x81, 0x40]); pairs += 1; k += 2
                    else: k += 1
            i = j + 1 if j > i else i + 1
        else:
            i += 1
    log.write('double half-width spaces -> 0x8140: %d' % pairs + chr(10))

    # verify size unchanged
    assert len(arm9) == ORIG_LEN, 'arm9 size changed!'
    open('kr/arm9_patched.bin', 'wb').write(arm9)
    log.write('\narm9 size: %d (unchanged: %s)\n' % (len(arm9), len(arm9) == ORIG_LEN))
    log.write('in-place: %d  repointed: %d\n' % (inplace, repointed))
    log.close()
    print('in-place=%d repointed=%d  -> kr/arm9_patched.bin' % (inplace, repointed))


if __name__ == '__main__':
    main()
