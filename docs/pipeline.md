# 파이프라인: 주제에서 게재까지 열 단계

한 논문은 한 프로젝트 폴더(`projects/<slug>/`)에서 S1–S10을 거칩니다. 단계마다 **산출물**, **관문(gate)**, **명령**이 있습니다. 관문은 다음 단계로 넘어가도 되는지 판정하는 지점입니다. 관문의 종류는 셋입니다.

- **HITL 관문:** 사람이 승인해야 열립니다(`python -m pa approve S1 --by <이름>`). 목표를 바꾸는 결정, 되돌릴 수 없는 일, 사람만 할 수 있는 판단이 여기에 있습니다.
- **CITL 관문:** 기계 점검만 통과하면 열립니다. Claude가 사람을 기다리지 않고 진행합니다.
- **BOTH:** 기계 점검을 통과하고 사람도 승인해야 열립니다.

`python -m pa status`가 단계별 상태, 막힌 이유, 다음 단계를 보여 주고, `python -m pa gate S4`가 한 관문의 남은 조건을 보여 줍니다. 산출물에 `[TODO]`·`[TBD]` 같은 자리 표시가 남아 있으면 관문은 열리지 않습니다.

| 단계 | 이름 | 명령 | 산출물 | 관문 | 관문 조건 |
|---|---|---|---|---|---|
| S1 | 주제 구체화 | `/pa-topic` | `01_topic/topic.md`, `journal.md`, `house_rules.md` | HITL | 확정 표(O·C·RQ·A·R·기여·쓰임·범위)에 자리 표시 없음, 사람 승인 |
| S2 | 자료 수집·원문·KB | `/pa-refs` | `02_literature/refs.bib`, `index.json`, `search_log.md`, `cards/` | BOTH | 모든 서지가 원문 기록과 대조됨(`verified`), 사람 승인 |
| S3 | 가설 수립 | `/pa-hypothesis` | `03_hypotheses/hypotheses.md` | HITL | 가설마다 예측·반증 조건·경쟁 가설, 사람 승인 |
| S4 | 실험 설계·사전 등록 | `/pa-design` | `04_design/design.md` | HITL | 지표·운영점·자료 격리·분석 계획, 사람 승인(이 승인 전에는 본 실험을 돌리지 않음) |
| S5 | 실행과 데이터 정리 | `/pa-data` | `05_data/processed/`, `numbers.csv` | CITL | 수치 원장에 행이 있고 모든 행에 출처가 있음 |
| S6 | 시각화 | `/pa-figures` | `06_figures/figures.md`, `scripts/`, `out/` | CITL | 표·그림 예산표에 자리 표시 없음, `pa fig check` 통과(권장) |
| S7 | 원고 작성 | `/pa-draft`, `/pa-polish` | `07_manuscript/manuscript.md`(또는 `tex/`) | CITL | 자리 표시 0, 기계 점검 실행 |
| S8 | 독립 검수 | `/pa-review`, `/pa-panel` | `08_review/<날짜>_review.md` | BOTH | 다른 세션의 보고서, 차단 0건, 사람 승인 |
| S9 | 조립과 투고 | `/pa-build` | `07_manuscript/build/`, `submission/`, `rounds/round0_submitted/` | HITL | 사람의 최종 승인. 제출(업로드)은 사람이 함 |
| S10 | 심사 라운드 | `/pa-round` | `rounds/round<N>/`, 답변서, `rounds/final/` | HITL | 답변서 점검 문제 0건, 사람 승인과 재제출 |

## 단계별 요점

### S1 주제 구체화
대화로 관심사를 연구 질문으로 좁힙니다. Claude는 한 번에 질문 하나만, 선택지와 권장안을 붙여 묻습니다. 확정할 것은 표 하나입니다: 큰 문제(O), 공백(C), 연구 질문(RQ), 접근(A), 기대하는 답의 형태(R), 기여의 유형, 쓰임, 범위 밖, 대상 독자와 저널 후보. 실행 가능성(자료, 자원, 윤리, 사람이 할 실험)도 이 단계에서 봅니다. 저널이 정해지면 규정표(`journal.md`)를 원 사이트에서 채웁니다.

### S2 자료 수집, 원문 확보, 지식 베이스
검색어와 데이터베이스를 `search_log.md`에 남기고, 고른 문헌을 DOI·arXiv 번호로 추가합니다(`pa refs add`). 서지는 원문 기록과 대조하고(`pa refs verify`), 열린 사본만 내려받고(`pa refs fetch`), 텍스트를 뽑고(`pa refs text`), 문헌마다 카드를 씁니다(`pa refs cards`). 카드는 "무엇을 한 연구인가", "원고에 쓸 수 있는 사실(쪽 번호)", "원고의 인용 문장별 판정"을 담습니다. 카드가 이 프로젝트의 문헌 지식 베이스입니다.

### S3 가설 수립
연구 질문마다 검증 가능한 가설, 예측(방향과 크기), 반증 조건, 경쟁 가설을 씁니다. 결과를 보기 전에 씁니다.

### S4 실험 설계와 사전 등록
조건·변인·기준선·ablation, 주 지표와 운영점, 자료 격리(평가 자료를 학습·보정에 쓰지 않음), 분석 계획, 성공·실패 판정 기준, 재현 방법을 정합니다. 사람이 승인한 뒤에 본 실험을 돌립니다. 실행 스크립트는 명령 한 줄로 무인 실행되고, 중단 후 이어서 돌 수 있고, `--check` 소규모 점검 모드를 두는 것을 권합니다. 긴 실행은 단계별 점검 관문으로 나누고, 작은 사전 시험을 먼저 돌립니다.

### S5 실행과 데이터 정리
GPU·실험실·현장 작업은 사람이 돌립니다(HITL). Claude는 결과 파일을 읽어 수치 원장 `numbers.csv`를 만듭니다. 원장의 각 행은 키, 값, 단위, 출처(결과 파일과 그 안의 키 또는 계산식), 메모입니다. 원고는 원장의 값만 씁니다(`{{num:key}}` 또는 `\NumKey`).

### S6 시각화
표·그림 예산표에서 하나에 메시지 하나를 정하고, 스크립트로 만듭니다. `pa.figures.apply_style()`가 가는 선, 작은 표식, 한 글꼴 크기, 색맹 안전 팔레트를 적용합니다. `pa fig check`로 해상도와 벡터 사본을 확인합니다.

### S7 원고 작성과 윤문
골격(`outline.md`)에서 섹션별 분량·답하는 RQ·표·그림·핵심 문장을 정한 뒤 씁니다. 다 쓰면 기계 점검(`pa check`)과 수치 감사(`pa numbers audit`)를 돌리고, 분야 문체로 윤문합니다(`/pa-polish`, [`style/polishing.md`](style/polishing.md)).

### S8 독립 검수
작성 세션과 다른 세션에서 8단계 검수를 합니다([`review_procedure.md`](review_procedure.md)). 큰 원고는 역할별 6인 검수단으로 나눕니다. 차단이 0건이 될 때까지 작성 세션이 고치고, 검수 세션은 차단 항목만 다시 봅니다.

### S9 조립과 투고
Markdown이면 `pa build docx`(pandoc, 저널 Word 템플릿을 `--reference-doc`으로), LaTeX이면 `pa build latex`와 `pa build package`. 맹검판은 `--blind`. 사람이 최종본을 보고 승인하면, 보낸 원고를 `rounds/round0_submitted/`로 동결합니다. 업로드는 사람이 합니다.

### S10 심사 라운드
결정 서신을 `rounds/round<N>/comments.md`에 그대로 붙이고, 의견별 항목을 만들고(`pa round split`), 항목마다 HITL/CITL을 나눈 수정 계획을 세웁니다. 고친 뒤 답변서를 만들고(`pa round letter`), 보낸 수정본을 동결합니다. 게재 승인 뒤에는 `rounds/final/`의 최종 점검표를 씁니다. 자세한 것은 [`rounds.md`](rounds.md).

## 단계를 건너뛰거나 되돌아갈 때

- 이미 실험을 끝낸 연구라면 S1–S4를 짧게 채우고(사후임을 `design.md`에 밝힘) S5부터 시작해도 됩니다. 관문은 그대로 적용됩니다.
- 앞 단계의 결정이 바뀌면 그 단계를 `python -m pa mark S3 doing`으로 되돌리고, 바뀐 이유를 `log/decisions.md`에 남깁니다. 뒤 단계 산출물 중 영향을 받는 것을 CITL 대기열에 올립니다.
- 모든 명령과 상태 변화는 `log/history.md`에 시각과 함께 남습니다.
