# 데이터 (S5)

- `raw/`: 없음. 자료는 `scripts/run_benchmark.py`가 고정 seed로 만듭니다.
- `processed/results.json`: 칸별 정확도와 거리별 요약.
- `numbers.csv`: 수치 원장. `scripts/make_ledger.py`가 `results.json`에서 만듭니다.

| 원자료 | 출처(주소·버전) | 받은 날 | 라이선스 | 비고 |
|---|---|---|---|---|
| 합성 가우스 자료 | `scripts/run_benchmark.py` | 2026-11-09 | 이 저장소와 같음 | seed 0–4 |

## 다시 만드는 명령

```
python examples/demo_project/05_data/scripts/run_benchmark.py
python examples/demo_project/05_data/scripts/make_ledger.py
python examples/demo_project/06_figures/scripts/fig1_accuracy.py
```
