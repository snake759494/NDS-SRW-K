# 패치 적용 방법 (일반 사용자용)

게임을 한글로 즐기고 싶을 뿐이라면 이 문서만 읽으면 됩니다.
직접 빌드하거나 번역을 고치고 싶다면 [BUILD.md](BUILD.md)로 가세요.

---

## 1. 준비물

| 필요한 것 | 설명 |
|---|---|
| **일본판 ROM** | `Super Robot Wars K (Japan).nds` — **CRC32 `D16DB8AF`**, 67,108,864 바이트 |
| **패치 파일** | [`patch/SRWK-Korean-v1.18.xdelta`](../patch/SRWK-Korean-v1.18.xdelta) (약 1.6 MB) |
| **xdelta3** | [xdelta3 공식 배포](https://github.com/jmacd/xdelta-gpl/releases) 또는 GUI 도구 |

> ROM은 이 저장소에 없고, 앞으로도 올리지 않습니다. **본인이 합법적으로 소유한 카트리지에서 직접 덤프**하세요.
> 이는 원 한글화 팀 YameSoft가 게임 내 고지에서 밝힌 조건("이 패치는 반드시 원본 카트리지를 소유하신 분에 한해서 사용할 수 있습니다")과도 같습니다.

### ROM이 맞는지 먼저 확인하세요

패치가 실패하는 원인은 거의 항상 ROM이 다른 것입니다. CRC32를 확인하세요.

```bash
python -c "import zlib,sys;print(format(zlib.crc32(open(sys.argv[1],'rb').read())&0xFFFFFFFF,'08X'))" "Super Robot Wars K (Japan).nds"
```

`D16DB8AF`가 나와야 합니다. 다르다면 다른 덤프(트림/헤더 변조/다른 리전)이며 패치가 적용되지 않습니다.

---

## 2. 패치 적용

### 명령줄

```bash
xdelta3 -d -s "Super Robot Wars K (Japan).nds" SRWK-Korean-v1.18.xdelta "Super Robot Wars K (Korean).nds"
```

### 결과 확인

| 항목 | 값 |
|---|---|
| 크기 | 63,688,032 바이트 |
| CRC32 | `A01F6796` |

CRC32가 다르면 적용된 ROM을 쓰지 마세요 — 원본 ROM이 다르거나 패치 파일이 손상된 것입니다.

---

## 3. 실행

실기(플래시카트) 및 주요 에뮬레이터(melonDS, DeSmuME, no$gba)에서 동작합니다.
melonDS를 권장합니다 — 개발 중 검증에 사용한 환경입니다.

---

## 4. 자주 겪는 문제

**"xdelta3: target window checksum mismatch"**
원본 ROM이 다릅니다. 위의 CRC32 확인을 다시 하세요.

**타이틀 화면에서 버전이 안 보입니다**
ROM 배너 제목에 `슈퍼로봇대전K 버전 1.18`이 들어 있습니다. 에뮬레이터의 ROM 정보/제목 표시에서 확인할 수 있습니다.

**엔딩 크레딧에서 멈춥니다**
v1.16 이하의 알려진 버그입니다. **v1.18로 다시 패치**하세요. 원인과 수정 내용은 [README](../README.md) 상단을 보세요.

**세이브 파일은 그대로 쓸 수 있나요?**
예. 이 패치는 세이브 포맷을 건드리지 않으므로 버전 간 `.sav`가 호환됩니다.

---

## 5. 하면 안 되는 것

- **패치된 ROM을 배포하지 마세요.** YameSoft가 게임 내 고지에서 명시적으로 금지하고 있고, 저작권 침해입니다. 배포는 xdelta 차분 파일로만 하세요.
- 상업적 이용 금지.
