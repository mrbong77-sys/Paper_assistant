---
description: S7 — 골격을 정하고 원고 초고를 쓴 뒤 기계 점검과 수치 감사를 돌립니다.
argument-hint: [slug] [섹션]
---

S7 원고 작성. 산출물은 `07_manuscript/manuscript.md`(또는 `07_manuscript/tex/main.tex`, 템플릿 `templates/latex/`)입니다.

1. **골격.** `07_manuscript/outline.md`에 섹션별 목표 분량(저널 상한 안), 답하는 RQ, 놓을 표·그림, 핵심 문장 하나를 정하고 사람에게 확인합니다.
2. **쓰는 순서.** 방법 → 결과 → 고찰 → 서론 → 결론 → 초록 → 제목. 결과를 다 쓴 뒤에 서론의 질문과 고찰의 답을 맞춥니다.
3. **재료.** 서론은 `01_topic/topic.md`의 확정 문장, 관련 연구는 `02_literature/synthesis.md`와 카드의 사실(쪽 확인된 것만), 방법은 `04_design/design.md`, 결과는 수치 원장.
4. **규칙.**
   - 수치는 `{{num:key}}`(Markdown) 또는 `\NumKey`(LaTeX, `python -m pa numbers macros`). 직접 타이핑하지 않습니다.
   - 인용은 `[@key]`(pandoc) 또는 `\cite{key}`. 카드의 판정이 Supported인 사실만 인용합니다.
   - 확인한 수치와 관찰만 씁니다. 추정 설명은 쓰지 않습니다(EV-10).
   - 경과가 아니라 결과를 씁니다(HR-03). 내부 코드명 대신 원고에서 정한 이름(HR-07).
   - 분야 프로필과 하우스 규칙의 문체(1인칭, 시제, 문장 길이)를 따릅니다.
   - 아직 모르는 것은 `[TODO: …]`로 남깁니다. 지어내지 않습니다.
   - 저자·소속·사사처럼 맹검판에서 빠질 것은 `<!-- identifying -->` … `<!-- /identifying -->` 안에 둡니다.
5. **점검.** 섹션을 다 쓸 때마다:
   ```
   python -m pa check 07_manuscript/manuscript.md --out 08_review/check_<날짜>.md
   python -m pa numbers audit
   python -m pa refs contexts
   ```
   미추적 수치는 원장에 넣거나(출처와 함께) 결과가 아님을 확인합니다. 인용 문맥이 바뀌었으면 카드의 판정표를 갱신합니다.
6. 섹션마다 커밋합니다. 다 쓰면 `/pa-polish`로 윤문하고, `/pa-review`는 **새 세션**에서 돌리도록 안내합니다.
