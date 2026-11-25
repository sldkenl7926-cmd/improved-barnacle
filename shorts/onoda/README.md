# 실화 아카이브 쇼츠 — 오노다 히로 (29년 늦게 항복한 군인)

## 제목 3안 (v3)
1. 전쟁 끝나고 29년 더 싸운 군인
2. 전쟁 끝난 걸 29년간 안 믿은 군인
3. 판다·설인 찾다 발견된 일본군

## 장면표 v3 (예상 시간, 최종은 내레이션에 맞춰 자동 조정)
| # | 초 | 화면 | 내레이션 | 자막 | 효과음 |
|---|---|---|---|---|---|
| S01 | 0.0–2.9 | `photos/S03_onoda_young.jpg` | 전쟁이 끝나고도 이십구 년을 더 싸운 군인. | 29년 더 싸운 군인 | 임팩트 |
| S02 | 2.9–4.7 | `photos/X_onoda_brother_1944.jpg` | 일본군 소위 오노다 히로. | 일본군 소위 오노다 히로 |  |
| S03 | 4.7–6.6 | `diagrams/S05_order_detail.png` | 명령은 하나, 항복하지 마라. | 명령: 항복 금지 |  |
| S04 | 6.6–8.1 | `photos/S06_japan_surrender_1945.jpg` | 일본은 항복했지만, | 1945 일본 항복 |  |
| S05 | 8.1–10.5 | `diagrams/S08_trap.png` | 그는 종전 전단을 속임수라 믿었다. | 종전 전단 = 속임수? |  |
| S06 | 10.5–13.1 | `photos/X_kozuka.jpg` | 필리핀 정글에서 동료들이 쓰러져도, | 동료들이 쓰러져도 |  |
| S07 | 13.1–15.2 | `diagrams/S10_victims.png` | 섬 주민 약 삼십 명이 희생됐다. | 주민 약 30명 희생 |  |
| S08 | 15.2–17.8 | `diagrams/S11_not_army.png` | 그런데 그를 찾은 건 군대가 아니었다. | 그런데, 군대가 아니었다 | 반전 히트 |
| S09 | 17.8–20.4 | `diagrams/S12_suzuki_list.png` | 판다와 설인도 찾겠다던 청년이었다. | 판다·설인 찾던 청년 |  |
| S10 | 20.4–22.2 | `diagrams/S13_quote.png` | 상관 명령 없인 못 나간다. | "명령 없인 못 나간다" |  |
| S11 | 22.2–24.4 | `diagrams/S14_route.png` | 결국 옛 상관이 일본에서 날아와 | 옛 상관이 날아오다 |  |
| S12 | 24.4–26.1 | `diagrams/S16_date.png` | 임무 해제를 명령했고, | 1974.3.9 임무 해제 |  |
| S13 | 26.1–28.2 | `photos/S17_marcos_onoda_1974.jpg` | 그제야 그는 칼을 내려놓았다. | 29년 만에 칼을 내려놓다 | 임팩트 |
| S14 | 28.2–30.1 | `diagrams/S18_loop.png` | 단 한 줄의 명령을 기다리다, | 명령 한 줄을 기다리다 |  |

- 반전: S08 "그런데…" (약 48% 지점)
- 엔딩: S14 → S01 루프 ("단 한 줄의 명령을 기다리다, / 전쟁이 끝나고도 29년을 더 싸운 군인.")

## 내레이션 원고 v3 (한 줄 = 한 장면)
```
전쟁이 끝나고도 이십구 년을 더 싸운 군인.
일본군 소위 오노다 히로.
명령은 하나, 항복하지 마라.
일본은 항복했지만,
그는 종전 전단을 속임수라 믿었다.
필리핀 정글에서 동료들이 쓰러져도,
섬 주민 약 삼십 명이 희생됐다.
그런데 그를 찾은 건 군대가 아니었다.
판다와 설인도 찾겠다던 청년이었다.
상관 명령 없인 못 나간다.
결국 옛 상관이 일본에서 날아와
임무 해제를 명령했고,
그제야 그는 칼을 내려놓았다.
단 한 줄의 명령을 기다리다,
```

## 실제 사진 출처 (Wikimedia Commons, 모두 Public domain)
- S01 `File:Hiroo Onoda young.jpg` (얼굴 클로즈업 훅)
- S06 `File:JapaneseSurrender.jpg` (1945-09-02, 미 해군)
- S17 `File:President Marcos and Hiroo Onoda.jpg`
- S03 `File:Hiroo and shigeo onoda 1944.jpg` (오노다 부분만 크롭)
- S09 `File:Kozuka kinshichi.jpg`

나머지 장면은 직접 그린 지도·도해(`diagrams/`)이며, 재구성 이미지에는 화면에 '재구성/일러스트' 표기가 있습니다.

## 설명문 + 해시태그
종전 29년 뒤에 항복한 군인이 있다. 그를 정글에서 나오게 한 건 군대가 아니었다.
#실화 #오노다히로 #2차세계대전 #역사 #실화아카이브 #shorts

## 사실 확인 출처
- https://en.wikipedia.org/wiki/Hiroo_Onoda
- https://www.nippon.com/en/japan-topics/today03120/
- https://www.historyhit.com/hiroo-onoda-the-japanese-soldier-who-refused-to-surrender/

## 렌더링
`python3 scripts/render.py scenes.json out.mp4 [내레이션.mp3]` — 내레이션을 주면 문장 사이 쉼을 감지해 장면 길이를 자동으로 맞춥니다.
