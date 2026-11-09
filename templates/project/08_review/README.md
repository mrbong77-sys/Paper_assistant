# 검수 (S8)

- 검수는 원고를 쓴 세션과 **다른 세션**이 합니다(`/pa-review`). 같은 세션은 저자의 맥락을 알아 독자가 막히는 곳을 못 봅니다.
- 보고서: `<YYYY-MM-DD>_review.md`. 첫머리에 단계별 판정과 "차단 N건"을 적습니다. 관문 S8은 마지막 보고서의 차단이 0건일 때 열립니다.
- 역할별 검수(선택): `panel/<날짜>/editor.md`, `numbers.md`, `displays.md`, `language.md`, `references.md`, `package.md`.
- 기계 점검: `check_<날짜>.md`(`python -m pa check`), `numbers_audit.md`(`python -m pa numbers audit`).
