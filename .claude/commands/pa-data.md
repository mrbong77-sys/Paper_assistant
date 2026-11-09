---
description: S5 — 실행 결과를 정리하고 수치 원장(numbers.csv)을 만듭니다.
argument-hint: [slug]
---

S5 실행과 데이터 정리. 산출물은 `05_data/processed/`의 결과 파일과 `05_data/numbers.csv`입니다.

1. **실행 확인.** 사람이 돌릴 실행이 남아 있으면 HITL 대기열의 명령을 다시 보여 줍니다. 결과가 들어왔으면 실행 로그에서 오류·중단·건너뛴 항목을 먼저 확인합니다. 문제가 있으면 원인을 진단한 뒤에만 재실행을 제안합니다.
2. **원자료는 읽기 전용.** `05_data/raw/`는 고치지 않습니다. 정리는 `05_data/scripts/`의 스크립트로 `processed/`에 씁니다. 손으로 고친 결과 파일은 두지 않습니다.
3. **사전 등록 대조.** `04_design/design.md`의 지표·조건이 모두 결과 파일에 있는지 확인합니다. 빠진 조건은 HITL로 알립니다.
4. **수치 원장.** 원고에 쓸 수 있는 모든 수치를 한 행씩 넣습니다.
   ```
   python -m pa numbers add acc_main 91.2 --unit % --source "05_data/processed/results.json:main.accuracy" --note "test split, n=500"
   ```
   - 키는 영문자로 시작하는 영문·숫자·밑줄. 파생값(차이, 비율, 평균)도 행으로 넣고, `source`에 계산식과 입력 키를 씁니다(예: `acc_main - acc_base`). 차이는 반올림 전 값으로 계산합니다.
   - 백분율의 분모, 신뢰구간, 검정 결과(통계량, p)도 행으로 넣습니다.
5. **검증.** 원장 값을 결과 파일에서 다시 읽어 비교하는 짧은 스크립트(`05_data/scripts/check_numbers.py`)를 두면, 결과가 바뀔 때 원장이 어긋나지 않습니다.
6. **보고.** 가설별로 판정 기준에 비춘 결과를 사람에게 보고합니다(된 것, 예상과 다른 것, 추가 실험이 필요한지 — 선택지와 권장안). 예상과 다른 결과를 숨기거나 조건을 고르지 않습니다(EV-06).
7. `python -m pa gate S5`가 통과하면 `python -m pa mark S5 done`, 커밋합니다.
