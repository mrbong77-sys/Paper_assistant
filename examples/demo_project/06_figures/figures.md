# 표·그림 예산 (S6)

저널 상한: 표와 그림 합쳐서 3개.

| ID | 종류 | 메시지(한 문장) | 자료 출처 | 생성 스크립트 | 출력 파일 | 상태 |
|---|---|---|---|---|---|---|
| Figure 1 | 선 그림 | 두 분류기의 정확도는 모든 거리에서 거의 겹치고 베이즈 최적에 가깝다. | `05_data/processed/results.json` | `scripts/fig1_accuracy.py` | `out/fig1_accuracy.pdf`, `.png` | 완료, `pa fig check` 통과 |
| Table 1 | 표 | 거리별 평균 정확도, 차이, 베이즈 최적. | `05_data/numbers.csv` | 원고의 `{{num:…}}` | 원고 안 | 완료 |

점검: `python -m pa fig check 06_figures/out --min-dpi 600 --width-in 3.5`
