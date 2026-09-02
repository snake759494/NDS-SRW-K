# 처음부터 직접 빌드하기

이 문서대로 하면 **이 저장소와 ROM 두 개만으로** 배포본과 **바이트 단위로 똑같은** 결과물이 나옵니다.
번역을 고치거나, 이미지를 새로 그리거나, 패치를 이어서 개발하려는 분을 위한 문서입니다.
그냥 게임을 하고 싶다면 [PATCHING.md](PATCHING.md)를 보세요.

---

## 1. 준비물

### 1.1 ROM 2개 (저장소에 없음 — 직접 준비)

| 파일 | 설명 |
|---|---|
| `Super Robot Wars K (Japan).nds` | 일본판 원본. **CRC32 `D16DB8AF`** — 빌드 스크립트가 검사합니다 |
| `Super Robot Wars K (Korean)-기존패치.nds` | **YameSoft 한글패치가 적용된 ROM** |

두 번째 파일이 왜 필요한지: 이 패치는 백지에서 만든 게 아니라 **YameSoft 한글패치를 기반으로** 미번역 부분을 채운 것입니다. 시나리오 1~24화 등 기존 번역과 한글 폰트 테이블이 그 ROM에 들어 있고, 빌드는 거기에 얹는 방식입니다. YameSoft 패치는 이 저장소에 포함되어 있지 않습니다(그들의 저작물입니다). 배포처에서 구해 일본판에 적용한 뒤 위 이름으로 저장하세요.

두 ROM을 **저장소 최상위**에 둡니다:

```
SRWK/                                       <- 이 저장소를 클론한 폴더
├─ Super Robot Wars K (Japan).nds           <- 직접 준비
├─ Super Robot Wars K (Korean)-기존패치.nds  <- 직접 준비
├─ srwk_work/     도구 일체
├─ data/          한국어 번역 데이터
├─ patch/         배포용 xdelta
└─ docs/
```

### 1.2 실행 환경

- **Python 3.10+**
- 의존 패키지: `pip install -r requirements.txt` (ndspy · Pillow · numpy · capstone)
- **맑은 고딕(Malgun Gothic)** — `C:\Windows\Fonts\malgun.ttf`, `malgunbd.ttf`
  이미지 안의 한글(아이캐치·전투 플레이트·정신기 등)을 이 폰트로 렌더링합니다. **Windows에서 빌드하는 것을 전제**로 합니다. MS 폰트는 재배포할 수 없어 저장소에 넣지 못했고, 다른 폰트로 바꾸면 이미지가 배포본과 달라집니다(게임은 정상 동작합니다).
- **갈무리11(Galmuri11)** — 대사 폰트. `srwk_work/Galmuri11.ttf`로 **포함되어 있습니다**(SIL OFL 1.1, © 정예하(quiple), <https://galmuri.quiple.dev/>).

---

## 2. 빌드

```bash
pip install -r requirements.txt
python srwk_work/extract_roms.py      # ROM 2개 -> jp/ , kr/ 로 풀기
python srwk_work/rebuild_all.py --verify
```

끝입니다. `--verify`는 결과 ROM의 CRC32가 배포본과 같은지(`D3CEFEDE`) 검사하고, 다르면 0이 아닌 값으로 종료합니다.

결과물: `Super Robot Wars K (Korean)-NEW.nds` (저장소 최상위, 63,688,032 바이트)

배포용 xdelta를 만들려면:

```bash
python -c "import pyxdelta;pyxdelta.run('Super Robot Wars K (Japan).nds','Super Robot Wars K (Korean)-NEW.nds','patch/SRWK-Korean-v1.22.xdelta')"
```

### 시간이 오래 걸립니다

`add02` 단계(아이캐치 59장 + 정신기 51개 + 로고)는 이미지를 전부 다시 렌더링하고 LZSS로 재압축하므로 **수십 분** 걸립니다. 한 단계만 다시 만들려면:

```bash
python srwk_work/rebuild_all.py --stage add04
```

---

## 3. 빌드 파이프라인

`rebuild_all.py`가 하는 일 전부입니다. 각 `_inject_*.py`는 누적된 `kr/*_patched.bin`을 읽어서 다시 쓰므로 **순서가 중요**하고, 그 순서가 이 스크립트에 박혀 있습니다.

| 단계 | 시작점 | 실행 스크립트 (순서대로) |
|---|---|---|
| `add02` | `kr/data/add02dat.bin` | `_eyecatch_inject` → `_inject_misc_images` → `_inject_captions` → `_inject_spirit` → `_inject_battle_plates` → `_inject_cmd1889` → `_inject_userlogo` |
| `add04` | `kr/data/add04dat.bin` | `_inject_plates` → `_inject_titles` → `_inject_critical` → `_inject_muteki` |
| `widths` | (위 두 결과) | `_fix_activation_widths` — add02·add04 **양쪽**을 건드리므로 반드시 마지막 |
| `arm9` | `kr/arm9.bin` | `_inject_arm9` → `_inject_font` |
| `credits` | `kr/overlays/ovl_003.bin` | `_inject_credits_fit` |
| `rom` | `...기존패치.nds` | `build_rom_all` (시나리오·전투 텍스트를 빌드해 위 결과와 함께 주입) |

텍스트 두 종류는 매 빌드마다 JSON에서 새로 인코딩됩니다:

- `data/scenario_ko.json` → `build_native.py` → `data/add03dat.bin`
- `data/battle_ko.json` → `build_battle.py` → `data/add05dat.bin`

---

## 4. 번역 고치기

### 4.1 어느 파일을 고치나

| 고칠 대상 | 파일 |
|---|---|
| 시나리오 대사 | `data/scenario_ko.json` — 각 박스의 `ko`만 |
| 전투 대사 | `data/battle_ko.json` — `ko`만 |
| 스태프 크레딧 | `data/credits_ko.json` |
| 유닛명·시스템 메시지 | `srwk_work/_inject_arm9.py`의 `TR` 딕셔너리 |
| 이미지 속 한글 | 해당 `_inject_*.py`의 문자열 테이블 |

고친 뒤 `python srwk_work/rebuild_all.py`를 다시 돌리면 됩니다. 텍스트만 고쳤다면 `build_rom_all.py`만 돌려도 충분합니다(이미지 재렌더링을 건너뛰어 훨씬 빠릅니다).

### 4.2 일본어 원문을 옆에 놓고 번역하고 싶다면

공개된 JSON에는 **한국어만** 들어 있습니다. 게임의 일본어 원문은 저작물이라 재배포하지 않습니다. 본인 ROM에서 복원해 넣으세요:

```bash
python srwk_work/restore_jp.py
```

`srwk_scenario_clean.json` / `srwk_battle.json`이 `jp` 필드까지 갖춘 형태로 만들어지고, 그 파일이 있으면 빌드가 자동으로 그쪽을 씁니다. 빌더는 `jp`를 **읽지 않으므로** 결과물은 완전히 동일합니다(검증됨).

### 4.3 반드시 지켜야 하는 제약

- **줄당 최대 176 px** — 한글 12 px, 반각 8 px. 시나리오는 **최대 3줄**. 넘치면 빌더가 경고하고 원본을 유지합니다.
- **①②③ 같은 동그라미 숫자는 건드리지 마세요.** 게임이 실행 중에 캐릭터 이름으로 바꿔 넣는 자리표시자입니다.
- `c1`(화자/초상화) `c2`(플래그) `name` `sec` `sp` 등 **`ko` 이외의 필드는 그대로** 두세요.
- 전투 대사는 반각 `!` `…` `。` `·`를 씁니다(전각 `！？　，、`는 테이블에 없습니다).
- **크레딧은 일본어 원본 길이를 넘으면 안 됩니다.** 넘치면 화면이 깨지고 멈춥니다 — v1.0~v1.16을 괴롭힌 버그입니다. `_inject_credits_fit.py`가 강제로 검사하며, 긴 인명은 성만 남깁니다.

---

## 5. 재현성에 대해

- `add02` · `add04` · `arm9` · `ovl_003` 네 바이너리는 원본 추출본에서 다시 만들었을 때 **배포본과 바이트 단위로 일치**함을 확인했습니다.
- `data/*_ko.json`(한국어 전용)으로 빌드한 `add03dat.bin` / `add05dat.bin`이 일본어 원문을 포함한 원래 작업 파일로 빌드한 것과 **바이트 단위로 일치**함을 확인했습니다.
- 최종 `.nds` 패킹은 ndspy가 담당합니다. ndspy 버전이 다르면 파일 정렬이 미세하게 달라져 CRC가 바뀔 수 있습니다. `--verify`가 실패하면 먼저 `requirements.txt`의 버전을 확인하세요.

---

## 6. 파일 포맷 요약

바이너리를 직접 파고들 사람을 위한 요약입니다. 자세한 내용은 각 스크립트의 docstring에 있습니다.

**아카이브** — `data/add0Xdat.bin`은 `[u32 오프셋 테이블][블록…]`. 첫 u32를 4로 나누면 블록 개수. 그래픽은 `add02`(UI·타이틀·아이캐치·정신기) · `add04`(전투 애니·플레이트) · `add08`(스프라이트)에만 있습니다.

**그래픽** — 표준 Nintendo 포맷(NARC/NCGR)이 **아닙니다**. `ECD`/`IMG`/`PLT`/`CEL`/`MAP`/`SCR` 태그를 쓰는 자체 포맷 + **1024바이트 링버퍼 LZSS**(`_codec1024.py`의 `decomp_1024`, 반환값은 튜플이니 `[0]`). 재인코딩은 `_enc1024b.py`의 `build_ecd2(orig, new_pixels, cap=1024, new_preamble=)` — **원본 압축 크기 이하**여야 하고 원본 크기에 맞춰 패딩합니다.

**타일** — NDS 4bpp, 타일당 32바이트, 니블 0 = 투명, 팔레트는 BGR555.

**PAT 블록** — 스프라이트 조합(OAM) 테이블. `PAT\0` + u32 개수 + 개수×u32 오프셋 + 엔트리(`u16 셀수` + 셀들 `(u16 attr, s16 x, s16 y, u16 tilebase)`). 타일 인덱스가 **위치 기반**(`ty*w+tx`)이라, 한글을 원본과 같은 타일 열에 그리면 조합이 그대로 유지됩니다.

**대사 폰트** — arm9 안에 SJIS 인덱스 순으로 26바이트 레코드:
`offset(code) = 0x43EB8 + sjis_idx(code)*26`, `sjis_idx = (hi-0x81)*188 + (lo-0x40) - (lo>0x7F ? 1 : 0)`.
레코드 = `[코드 2바이트 BE][글리프 24바이트]`, 글리프 = **12행 × 2바이트(16비트 BE, MSB가 왼쪽)**, 잉크는 **왼쪽 12칸** → **12×12 셀**.
갈무리11은 em이 1200이라 **size 12에서 1px = 100유닛**으로 격자에 정확히 맞고 안티앨리어싱이 생기지 않습니다.

**오버레이 테이블** — 엔트리당 32바이트, `+8`이 ramSize, 마지막 워드가 `compSize(24비트) + flag(8비트)`. `ovl_003`(엔딩 크레딧)은 RAM 0x021E6700을 `ovl0/1/2/4/18`과 **공유**하므로 **절대 크기를 늘리면 안 됩니다**.

**⚠ 한글 폰트의 부작용** — 한글패치는 SJIS **0x889F~0x94FC** 구간을 한글 글리프로 덮어썼습니다. 그래서 그 구간의 한자는 **엉뚱한 한글로** 표시됩니다(「鈴木　克弘」 → 「鈴木　뱃눠」). 어떤 텍스트든 일본어로 되돌리는 것은 해결책이 되지 못합니다.
