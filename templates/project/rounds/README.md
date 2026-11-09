# 심사 라운드 (S10)

- `round0_submitted/`: 처음 투고한 원고(동결). 동결한 폴더는 고치지 않습니다.
- `round<N>/`: 받은 의견(`comments.md`), 수정 계획(`plan.md`), 답변 표(`responses.toml`), 답변서(`letter/`).
- `round<N>_submitted/`: 그 라운드에 보낸 수정본(동결).
- `final/`: 게재 승인 뒤 최종본과 최종 점검표.

명령: `python -m pa round new | split | letter | freeze | diff round0_submitted current | final`
