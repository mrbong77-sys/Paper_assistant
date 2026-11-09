# 라운드 관리: round1, round2, … final

투고 뒤의 모든 소통(심사 의견, 수정, 답변서, 재제출)은 `rounds/` 아래 라운드별 폴더에 남습니다. 핵심 규칙은 두 가지입니다.

1. **보낸 것은 동결합니다.** 제출한 원고는 `rounds/round<N>_submitted/`로 복사하고 다시 고치지 않습니다(`pa round freeze`). 나중에 "그때 무엇을 보냈는가"를 정확히 답할 수 있어야 합니다.
2. **받은 것은 그대로 둡니다.** 결정 서신은 고치지 않고 `comments.md`에 붙입니다. 의견의 분해·해석은 `responses.toml`과 `plan.md`에서 합니다.

## 흐름

```
S9 투고 승인 ─▶ pa round freeze            → rounds/round0_submitted/
결정 서신 도착 ─▶ pa round new              → rounds/round1/{comments.md, plan.md, responses.toml}
                 (comments.md에 서신 붙여 넣기)
               ─▶ pa round split            → 의견별 [[item]] (E.1, R1.1, R1.2, R2.1 …)
               ─▶ plan.md 작성              → 항목별 조치, HITL/CITL, 바뀌는 파일, 새 실험 여부
                 (HITL 항목은 pa ask로 결정 카드, 새 실험은 사람이 실행)
               ─▶ 원고 수정 (07_manuscript/, 표시본은 \rev{} 또는 변경 추적)
               ─▶ responses.toml 채우기     → response, change(정확한 위치), status, in_paper
               ─▶ pa round letter           → letter/response_letter.{md,tex,docx} + 빠진 곳 점검
               ─▶ /pa-review (수정본 검수, RV-01–08)
               ─▶ pa approve S10 --by <이름>, pa round freeze → rounds/round1_submitted/
다음 결정 ────▶ pa round new                → rounds/round2/ …
게재 승인 ────▶ pa round final              → rounds/final/final_checklist.md
```

## 답변서 형식

`pa round letter`는 의견을 낸 사람별로 표를 만듭니다.

| # | Comment | Response | Change in the manuscript | Status |
|---|---|---|---|---|
| R1.2 | The baseline uses a different data split. | The baseline was re-run on the same split; Table 2 now reports both. | §4.1, Table 2 | Done |

요청 밖에서 고친 것은 따로 표를 만들고, 논문 반영 여부를 구분합니다.

| # | Change | Reason | Location | In the paper |
|---|---|---|---|---|
| O1 | Corrected the sample count in Table 2 | Found in our own check | Table 2 | Yes |

점검하는 것: 빈 답(RV-01), 위치 없는 변경(RV-02), 근거 없는 거절(RV-03), 방어 문구(RV-04), `[[own]]`의 `in_paper` 누락(RV-07).

## 두 판 비교

```
python -m pa round diff round0_submitted current      # 단어 단위 변경: ~~지운 것~~ **넣은 것**
```

답변서의 "변경 위치"가 실제 변경과 맞는지 확인할 때 씁니다.

## 이력과 소통 기록

- 라운드마다 받은 날, 결정, 마감을 `comments.md` 머리에 적습니다.
- 편집자에게 보낸 편지(커버 레터, 마감 연장 요청 등)는 `rounds/round<N>/correspondence/`에 날짜를 붙여 둡니다. 외부로 보내는 일은 사람이 합니다(HITL).
- 모든 단계 변화는 `log/history.md`에, 사람의 결정은 `log/decisions.md`에 남습니다.
