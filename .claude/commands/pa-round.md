---
description: S10 — 심사 결정 서신을 받아 의견을 나누고, HITL/CITL 수정 계획을 세우고, 고친 뒤 답변서를 만듭니다.
argument-hint: [slug] [new|plan|letter]
---

심사 라운드. 인자: $ARGUMENTS. 절차는 `docs/rounds.md`입니다.

1. **열기.** `python -m pa round new` → `rounds/round<N>/`. 사람이 받은 결정 서신을 `comments.md`에 고치지 않고 붙입니다(제목: `## Editor`, `## Reviewer 1`, …). 받은 날·결정·마감을 머리에 적습니다.
2. **나누기.** `python -m pa round split` → `responses.toml`에 의견별 항목(E.1, R1.1 …). 한 의견에 요구가 둘 이상이면 항목을 나눕니다.
3. **계획.** `plan.md`에 항목마다: 요지, 필요한 조치, 맡는 쪽(HITL/CITL), 바뀌는 파일·위치, 새 실험 여부.
   - 꼭 필요한 조치만 합니다. 비싼 새 실험 전에 기존 기록으로 답할 수 있는지 봅니다.
   - 사람의 판단이 필요한 항목(동의하지 않을지, 새 실험을 할지)은 `pa ask`로 결정 카드를 올리고, 그동안 CITL 항목을 진행합니다.
   - 계획을 커밋한 뒤 첫 수정을 시작합니다.
4. **수정.** 원고를 고칩니다. 수정본 표시는 저널 방식(변경 추적, `\rev{}` 색). 재실험으로 바뀐 주장은 원고에서 이력 없이 고치고 경위는 답변서에만(RV-08). 바뀐 수치는 수치 원장부터 고칩니다.
5. **답변.** `responses.toml`의 각 항목에 response(완전한 문장, 정중하게, 방어 문구 없이), change(정확한 위치), status, in_paper를 채웁니다. 요청 밖에서 고친 것은 `[[own]]`에 적고 in_paper를 구분합니다.
6. **답변서.** `python -m pa round letter` → `letter/response_letter.{md,tex,docx}`와 빠진 곳 목록. 문제가 0건이 될 때까지 고칩니다. `python -m pa round diff round<N-1>_submitted current`로 변경 위치가 맞는지 대조합니다.
7. **검수.** 새 세션에서 `/pa-review`(수정본: RV-01–RV-08 포함).
8. **제출.** 사람이 답변서와 수정본을 승인하면 `python -m pa approve S10 --by <이름> --note "round <N>"`, `python -m pa round freeze`. 업로드는 사람이 합니다.
