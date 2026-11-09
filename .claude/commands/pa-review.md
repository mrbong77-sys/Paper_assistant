---
description: S8 — 원고를 쓰지 않은 세션에서 8단계 검수(이야기, 구조, 수치, 표·그림, 문장, 참고문헌, 최종 점검, 편집자 판정)를 합니다.
argument-hint: [slug]
---

독립 검수. 절차는 `docs/review_procedure.md`, 규칙은 `docs/style/core_rules.md`, 보고서 템플릿은 `templates/review/review_report.md`입니다.

0. **독립성 확인.** 이 세션이 이 원고를 썼거나 윤문했으면, 그 사실을 알리고 새 세션에서 다시 실행하도록 안내합니다. 사람이 그래도 진행하라고 하면 `.claude/agents/`의 검수 에이전트(별도 맥락)로 돌리는 `/pa-panel`을 권합니다.
1. **검수자는 원고를 고치지 않습니다.** 읽고, 점검 명령을 돌리고, 보고서 한 파일만 씁니다.
2. **준비(0단계).** 저널 규정표, 하우스 규칙, 분야 프로필, 수치 원장, 저자 의도(`01_topic/topic.md`, `log/decisions.md`)를 읽습니다. 기계 점검을 돌리되 결과는 5단계에서 엽니다:
   ```
   python -m pa check 07_manuscript/manuscript.md --out 08_review/check_<날짜>.md
   python -m pa numbers audit
   python -m pa refs verify
   python -m pa fig check 06_figures/out
   ```
3. **단계 1–8**을 순서대로 합니다. 1단계는 여섯 조각(제목, 초록, 서론 첫·마지막 단락, 고찰 첫 단락, 결론 마지막 단락)만 보고 O·C·A·R·take-home을 복원해 저자 의도와 대조합니다. 차단이 나오면 그 단계에서 보고서를 마무리하고 작성 세션에 넘깁니다.
4. **보고서.** `08_review/<YYYY-MM-DD>_review.md`. 첫머리에 단계별 판정 표와 **"차단 N건, 수정 N건, 권고 N건입니다."** 줄. 발견마다 한 행: 단계, 등급, 위치(섹션·줄), 규칙 ID, 문제, 고칠 방향. 사람이 결정할 것은 따로 표로(선택지와 권장안).
5. 커밋하고, 사람에게 차단 항목과 결정할 것만 보고합니다.
6. 작성 세션이 고친 뒤 다시 부르면, 차단 항목과 기계 점검만 다시 확인하고 새 날짜의 보고서를 씁니다. 차단 0건이면 사람에게 S8 승인을 청합니다.
