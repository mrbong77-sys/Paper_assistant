# 데이터 (S5)

- `raw/`: 받은 그대로의 원자료. 읽기 전용으로 다루고 고치지 않습니다. 커밋하지 않습니다(.gitignore). 출처와 받은 날짜는 아래 표에 적습니다.
- `processed/`: 스크립트가 만든 결과 파일(JSON, CSV). 손으로 고치지 않습니다.
- `scripts/`: `raw/` → `processed/` 변환과 분석 스크립트. 명령 한 줄로 다시 만들 수 있어야 합니다.
- `numbers.csv`: 수치 원장. 원고에 쓰는 모든 수치를 `key,value,unit,source,note`로 적습니다. `source`는 결과 파일과 그 안의 키, 또는 계산식입니다.

| 원자료 | 출처(주소·버전) | 받은 날 | 라이선스 | 비고 |
|---|---|---|---|---|

## 다시 만드는 명령

```
[TODO: 예: python 05_data/scripts/analyze.py --out 05_data/processed/results.json]
```
