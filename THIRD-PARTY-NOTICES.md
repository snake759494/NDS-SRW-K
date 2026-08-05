# 제3자 저작물 고지

이 저장소의 코드와 문서는 [MIT 라이선스](LICENSE)입니다. 아래는 예외입니다.

## 갈무리11 (Galmuri11)

`srwk_work/Galmuri11.ttf` — 게임 내 대사 폰트로 사용하며, 저장소에 포함되어 있습니다.

- © 정예하 (quiple)
- SIL Open Font License 1.1 — 전문: [`srwk_work/assets/OFL-1.1.txt`](srwk_work/assets/OFL-1.1.txt)
- 홈페이지: <https://galmuri.quiple.dev/> · 저장소: <https://github.com/quiple/galmuri>

OFL은 폰트의 재배포를 허용하되 라이선스 전문을 함께 배포할 것을 요구합니다. 그래서 위 파일을 같이 넣었습니다.

## 맑은 고딕 (Malgun Gothic)

이미지 안의 한글(아이캐치·전투 플레이트·정신기 등)을 렌더링할 때 Windows 시스템 폰트인 맑은 고딕을 사용합니다.

**저장소에 포함되어 있지 않습니다.** Microsoft 폰트는 재배포할 수 없습니다. 빌드하려면 Windows의 `C:\Windows\Fonts\malgun.ttf`, `malgunbd.ttf`가 필요합니다. 자세한 내용은 [docs/BUILD.md](docs/BUILD.md).

## YameSoft 한글패치

이 패치는 YameSoft의 슈퍼로봇대전 K 한글패치를 **기반으로** 미번역 부분을 채운 것입니다.

- YameSoft의 번역물(시나리오 1~24화 등)과 한글 폰트 테이블은 **저장소에 포함되어 있지 않습니다.**
- 빌드하려면 YameSoft 패치가 적용된 ROM을 직접 준비해야 합니다.
- YameSoft는 게임 내 고지에서 **패치된 ROM 파일의 배포와 상업적 이용을 금지**하고 있습니다. 이 저장소는 그 조건을 따릅니다 — 배포물은 xdelta 차분 파일뿐입니다.

## 게임 데이터

**반다이남코게임스 / 반프레스토**의 저작물입니다.

이 저장소에는 ROM, 추출한 게임 바이너리(arm9 / add0Xdat / overlay), 원본 게임 스크립트가 **일절 포함되어 있지 않으며** 앞으로도 포함하지 않습니다. `data/*_ko.json`은 한국어 번역문만 담고 있고, 일본어 원문은 제외했습니다([data/README.md](data/README.md) 참고).

도구를 쓰려면 본인이 합법적으로 소유한 카트리지에서 직접 덤프해야 합니다.
