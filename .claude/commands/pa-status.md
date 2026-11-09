---
description: 프로젝트 현황 — 단계, 막힌 관문, HITL 질문, CITL 작업, 다음 할 일.
argument-hint: [slug]
---

프로젝트 `$ARGUMENTS`(없으면 하나뿐인 프로젝트, 여럿이면 물음)의 현황을 보고합니다.

1. `python -m pa --project <slug> status`와 `python -m pa --project <slug> queue`를 실행합니다.
2. `log/decisions.md`의 최근 결정 5개와 `git log --oneline -5`(프로젝트가 저장소 안에 있으면)를 확인합니다.
3. 사람에게 다음 순서로 짧게 보고합니다.
   - **사람이 할 일:** 열린 HITL 질문(선택지와 권장안을 그대로), 사람이 실행할 명령, 승인이 필요한 관문.
   - **Claude가 이어서 할 일:** 열린 CITL 작업과 다음 단계.
   - **막힌 것:** 관문을 막는 이유(파일:항목).
4. 사람이 답하면 `python -m pa answer H-00N "<답>" --by <이름>`으로 기록하고, 그 답으로 풀린 일을 진행합니다.
