---
description: 게재 승인 뒤 최종본 — 최종 점검표, 맹검 해제, 공개 자료 확인, 교정쇄 대조.
argument-hint: [slug]
---

최종본.

1. `python -m pa round final` → `rounds/final/final_checklist.md`.
2. 점검표의 항목을 차례로 확인하고 근거(명령 결과, 파일, 주소)를 적습니다: 마지막 라운드 반영, 저널 최종본 규정, 맹검 해제(저자·소속·사사·연구비·링크 복원), 데이터·코드 공개 위치와 DOI가 실제로 열림, `pa numbers audit`, `pa refs verify`, 독립 검수 차단 0건.
3. 교정쇄(proof)가 오면 원고와 대조합니다: 표·그림·수식·참고문헌 번호, 수치, 저자 정보. 다른 곳을 표로 정리해 사람에게 줍니다.
4. 사소한 수정으로 공개 자료(코드, 데이터 릴리스)를 새로 내지 않습니다. 새 릴리스가 필요한지는 사람이 정합니다(HITL).
5. 사람이 승인하면 `python -m pa round freeze --label final_submitted`. 업로드는 사람이 합니다.
