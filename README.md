# Paper Assistant

**연구 주제 한 줄에서 게재 승인까지, Claude Code와 함께 논문 한 편을 끝까지 이끄는 도구 세트이자 자동 파이프라인입니다.**

[English summary](README.en.md)

이 저장소를 클론해서 Claude Code로 열면, Claude는 [`CLAUDE.md`](CLAUDE.md)의 운영 규칙과 `/pa-*` 명령으로 다음 일을 합니다.

- 대화로 연구 주제를 **연구 질문**으로 좁히고, 저널 규정표와 하우스 규칙을 만듭니다.
- 문헌을 찾고, 서지를 **원 기록(Crossref·arXiv)과 대조**하고, **열린 원문만** 확보하고, 문헌마다 **카드(지식 베이스)** 를 씁니다.
- **가설**(예측·반증 조건·경쟁 가설)과 **실험 설계·사전 등록**(지표, 운영점, 자료 격리, 분석 계획)을 세웁니다.
- 결과 파일에서 **수치 원장**을 만들어, 원고의 모든 숫자가 출처까지 거슬러 올라가게 합니다.
- 일관된 스타일로 **그림**을 만들고 해상도·형식을 점검합니다.
- 원고를 쓰고, **분야별 문체**(공학, 자연과학, 의생명, 사회과학, 인문학, 한국어)로 네 번에 나눠 윤문합니다.
- **작성 세션과 다른 세션**이 8단계로 검수하고(편집자 판정 포함), 큰 원고는 **역할별 6인 검수단**이 나눠 봅니다.
- **DOCX**(pandoc, 저널 Word 템플릿)나 **LaTeX**(빈 폴더 재조판 검증)로 조립하고, 맹검판과 투고 묶음을 만듭니다.
- **round1, round2, … final** 심사 라운드를 폴더별로 관리하고, 보낸 판을 동결하고, 표 형식 **답변서**를 만들고 빠진 답을 찾습니다.
- 모든 단계에 **관문(gate)** 이 있고, 사람이 결정할 일(**HITL**)과 Claude가 할 일(**CITL**)을 두 대기열로 나눠 서로의 병목을 메웁니다.

파이썬 도구(`python -m pa`)는 **표준 라이브러리만** 씁니다. pandoc, TeX Live, poppler, LibreOffice, matplotlib은 있으면 더 많은 일을 합니다.

---

## 목차

1. [전체 흐름](#1-전체-흐름)
2. [설치](#2-설치)
3. [빠른 시작 (10분)](#3-빠른-시작-10분)
4. [예시 프로젝트 둘러보기](#4-예시-프로젝트-둘러보기)
5. [단계별 사용법과 예시](#5-단계별-사용법과-예시)
6. [HITL과 CITL](#6-hitl과-citl)
7. [검수 체계](#7-검수-체계)
8. [분야별 문체와 윤문](#8-분야별-문체와-윤문)
9. [명령 레퍼런스](#9-명령-레퍼런스)
10. [내 프로젝트를 비공개로 두기, 저작권, 보안](#10-내-프로젝트를-비공개로-두기-저작권-보안)
11. [문제 해결](#11-문제-해결)
12. [저장소 구조](#12-저장소-구조)

---

## 1. 전체 흐름

```
 S1 주제 구체화 ──▶ S2 문헌·원문·KB ──▶ S3 가설 ──▶ S4 설계·사전 등록 ──▶ S5 실행·수치 원장
   [HITL 승인]        [기계+사람]          [HITL]        [HITL, 승인 전 실행 금지]    [CITL]
                                                                                      │
 S10 심사 라운드 ◀── S9 조립·투고 ◀── S8 독립 검수 ◀── S7 원고·윤문 ◀── S6 시각화 ◀────┘
   round1…final       [HITL, 업로드는 사람]  [다른 세션, 차단 0건]  [CITL]        [CITL]
```

| 단계 | 명령 | 산출물 | 관문 |
|---|---|---|---|
| S1 주제 구체화 | `/pa-topic` | `01_topic/topic.md`, `journal.md`, `house_rules.md` | HITL |
| S2 자료 수집·원문·KB | `/pa-refs` | `02_literature/refs.bib`, `index.json`, `cards/` | 기계 + 사람 |
| S3 가설 | `/pa-hypothesis` | `03_hypotheses/hypotheses.md` | HITL |
| S4 실험 설계·사전 등록 | `/pa-design` | `04_design/design.md` | HITL |
| S5 실행·데이터 정리 | `/pa-data` | `05_data/processed/`, `numbers.csv` | 기계 |
| S6 시각화 | `/pa-figures` | `06_figures/` | 기계 |
| S7 원고·윤문 | `/pa-draft`, `/pa-polish` | `07_manuscript/` | 기계 |
| S8 독립 검수 | `/pa-review`, `/pa-panel` | `08_review/<날짜>_review.md` | 기계 + 사람 |
| S9 조립·투고 | `/pa-build` | `07_manuscript/build/`, `submission/`, `rounds/round0_submitted/` | HITL |
| S10 심사 라운드 | `/pa-round`, `/pa-final` | `rounds/round<N>/`, `rounds/final/` | HITL |

관문은 산출물에 `[TODO]`가 남았거나, 서지가 대조되지 않았거나, 수치에 출처가 없거나, 검수 차단이 남았거나, 사람이 승인하지 않았으면 열리지 않습니다. 자세한 정의는 [`docs/pipeline.md`](docs/pipeline.md).

## 2. 설치

필수: Python 3.11 이상, git, [Claude Code](https://docs.claude.com/en/docs/claude-code).

```bash
git clone https://github.com/mrbong77-sys/Paper_assistant.git
cd Paper_assistant
python -m pa --help            # 설치 확인 (추가 패키지 없음)
python -m pytest -q            # 선택: 테스트 (pip install pytest)
```

선택 도구(있으면 쓰고, 없으면 그 기능만 건너뜁니다):

| 도구 | 쓰는 곳 | 설치 예 |
|---|---|---|
| pandoc | Markdown → DOCX, 인용 처리(citeproc) | `winget install pandoc` / `brew install pandoc` / `apt install pandoc` |
| TeX Live 또는 MiKTeX | LaTeX 조판, 투고 묶음 재조판 | 배포판 설치 |
| poppler-utils | `pdftotext`(원문 텍스트), `pdftoppm`(쪽 렌더링) | `apt install poppler-utils` / `brew install poppler` |
| LibreOffice | DOCX → PDF | 배포판 설치 |
| matplotlib | 그림 스타일(`pa.figures`) | `pip install matplotlib` |

환경 변수(선택):

| 변수 | 뜻 |
|---|---|
| `PA_PROJECTS` | 프로젝트를 둘 폴더(기본: 이 저장소의 `projects/`, git 제외). 비공개 저장소를 가리키면 프로젝트를 버전 관리할 수 있습니다. |
| `PA_EMAIL` | Crossref·Unpaywall에 보내는 연락용 주소. Unpaywall로 열린 원문을 찾을 때 필요합니다. 파일에 쓰지 말고 환경 변수로만 두십시오. |

## 3. 빠른 시작 (10분)

### Claude Code로 (권장)

```bash
cd Paper_assistant
claude
```

Claude Code 안에서:

```
/pa-new sleep-memory 수면 시간과 단기 기억
```

Claude가 분야 프로필, 원고 언어, 대상 저널, 프로젝트 위치를 한 번에 묻고(선택지와 권장안), 프로젝트를 만듭니다. 이어서:

```
/pa-topic sleep-memory
```

Claude가 한 번에 질문 하나씩, 선택지를 붙여 묻습니다.

> **Claude:** 이 연구의 큰 문제를 고르십시오. (A) 수면 부족이 학습 성과를 낮춘다는 실무적 문제 (B) 수면과 기억 응고의 기전 문제 (C) 직접 쓰기. 권장: A — 측정 가능한 결과로 연구 질문을 좁히기 쉽습니다.
>
> **사람:** A. 대학생 대상으로.

대화가 끝나면 `01_topic/topic.md`의 확정 표(큰 문제, 공백, 연구 질문, 접근, 기대 답, 기여, 쓰임, 범위 밖)가 채워지고, Claude가 승인을 청합니다. "S1 승인합니다"라고 답하면 Claude가 승인을 기록하고 `/pa-refs`로 넘어갑니다.

언제든 현황을 보려면:

```
/pa-status
```

### 명령줄만으로

Claude 없이도 모든 도구를 쓸 수 있습니다.

```bash
python -m pa new sleep-memory --title "Sleep duration and short-term memory" --field social_science --journal "Example Journal"
python -m pa --project sleep-memory status
python -m pa --project sleep-memory gate S1
```

## 4. 예시 프로젝트 둘러보기

[`examples/demo_project/`](examples/demo_project)는 **가상의 연구**(합성 자료에서 로지스틱 회귀와 최근접 중심 분류기 비교)를 S1부터 1차 심사 답변서까지 채워 둔 것입니다. 저널과 심사 의견은 지어낸 것이고, 자료는 스크립트가 고정 seed로 만듭니다. 참고문헌 세 편은 실제 문헌이며 원 기록과 대조했습니다.

```bash
python -m pa --project examples/demo_project status      # 모든 관문과 열린 질문
python -m pa --project examples/demo_project queue       # H-002: 재제출 승인 대기, C-001: 수정본 재검수
```

| 보면 좋은 파일 | 보여 주는 것 |
|---|---|
| `01_topic/topic.md` | 확정 표와 대화 기록(선택지와 사람의 답) |
| `03_hypotheses/hypotheses.md` | 가설, 예측, 반증 조건, 경쟁 가설. 결과는 H1을 반박했습니다(부정적 결과도 그대로 보고) |
| `04_design/design.md` | 사전 등록: 조건, 지표, 자료 격리, 판정 기준 |
| `05_data/scripts/run_benchmark.py` | 무인 실행, 이어서 실행, `--check` 점검 모드 |
| `05_data/numbers.csv` | 수치 원장 39행, 모든 행에 출처 |
| `07_manuscript/manuscript.md` | `{{num:key}}`와 `[@key]`로 쓴 원고, `<!-- identifying -->` 맹검 구역 |
| `02_literature/cards/Fisher1936.md` | 문헌 카드와 인용 판정("Partly supported" → 1차 라운드에서 고침) |
| `08_review/2026-11-09_review.md` | 8단계 검수 보고서(차단 0, 수정 4, 권고 2) |
| `rounds/round1/` | 심사 의견, 의견별 답변 표, 생성된 답변서(MD·TeX·DOCX) |
| `log/decisions.md`, `log/history.md` | 사람의 결정과 전체 이력 |

다시 만들어 보기:

```bash
python examples/demo_project/05_data/scripts/run_benchmark.py --check    # 점검 실행 → results_check.json (본 결과는 그대로)
python examples/demo_project/05_data/scripts/run_benchmark.py            # 본 실행(1초 미만)
python examples/demo_project/05_data/scripts/make_ledger.py              # 수치 원장
python examples/demo_project/06_figures/scripts/fig1_accuracy.py         # 그림 1 (matplotlib)
python -m pa --project examples/demo_project build docx                  # 07_manuscript/build/manuscript.docx
python -m pa --project examples/demo_project build docx --blind          # 맹검판
python -m pa --project examples/demo_project round letter                # 답변서 + 빠진 곳 점검
```

## 5. 단계별 사용법과 예시

아래 예시의 `--project <slug>`는 프로젝트 폴더 안에서 실행하면 생략할 수 있습니다.

### S1 주제 구체화 — `/pa-topic`

- Claude는 열린 질문 대신 **선택지와 권장안**을 붙여 한 번에 하나씩 묻고, 빠른 문헌 확인으로 이미 답이 있는 질문인지 봅니다.
- 저널이 정해지면 투고 안내에서 `01_topic/journal.md`(분량, 초록, 표·그림 상한, 참고문헌 형식, 맹검, 선언문)를 채우고, `project.toml`의 `[journal]` 수치를 맞춥니다. 이 표가 모든 문체 규칙보다 우선합니다.
- `01_topic/house_rules.md`에는 저자·지도교수의 규칙이 쌓입니다(기본값 HR-01–08: 평이한 문체, 결과만 쓰기, 실제 약점만 한계로, 수치 추적, 원문 대조 참고문헌, 내부 라벨 금지, 설계 오류는 재실행으로 바로잡기).

### S2 문헌·원문·지식 베이스 — `/pa-refs`

```bash
python -m pa refs add --doi 10.1111/j.2517-6161.1958.tb00292.x     # Crossref 원 기록으로 BibTeX 생성
python -m pa refs add --arxiv 2401.01234                            # arXiv 기록, 게재본이 있으면 알려 줌
python -m pa refs verify                                            # 모든 항목을 원 기록과 대조
python -m pa refs manual --key Book2020 --note "출판사 페이지에서 ISBN·판 확인"
PA_EMAIL=you@example.org python -m pa refs fetch                    # 열린 사본만 (Unpaywall, arXiv)
python -m pa refs text                                              # pdftotext
python -m pa refs contexts                                          # 원고의 인용 문장 찾기
python -m pa refs cards                                             # 카드 뼈대 → Claude가 원문을 읽고 채움
```

`refs verify` 출력 예:

```
- Pedregosa2012 [venue]: Published version: Journal of Machine Learning Research (2011) (cite the published version, RE-02)
3 entries, 1 problem(s)
```

카드에는 "무엇을 한 연구인가", "원고에 쓸 수 있는 사실(쪽)", "인용 문장별 판정(Supported / Partly supported / Not supported / Wrong source / Usage citation)"이 들어갑니다. 원문 PDF와 텍스트는 커밋되지 않습니다.

### S3 가설 — `/pa-hypothesis`

가설마다 예측(방향·크기), 반증 조건, 경쟁 가설을 결과를 보기 전에 씁니다. 바꾸면 "변경 기록"에 남깁니다.

### S4 실험 설계·사전 등록 — `/pa-design`

조건·변인·기준선·ablation, 주 지표와 운영점, **자료 격리**(평가 자료는 학습·보정에 쓰지 않음), 분석 계획과 판정 기준, 재현 방법을 정합니다. 실행 스크립트는 명령 한 줄 무인 실행, 이어서 실행, `--check` 점검 모드를 갖추게 합니다. 사람이 승인한 뒤에만 본 실험을 돌립니다.

### S5 실행과 수치 원장 — `/pa-data`

```bash
python -m pa numbers add acc_main 91.2 --unit % --source "05_data/processed/results.json:main.accuracy" --note "test, n=500"
python -m pa numbers macros            # LaTeX: 07_manuscript/numbers.tex 의 \NumAccMain
python -m pa numbers audit             # 원고에 손으로 친 수치 중 원장에 없는 것
```

원고에는 Markdown이면 `{{num:acc_main}}`, LaTeX이면 `\NumAccMain`을 씁니다. 결과가 바뀌면 원장만 고치면 원고 전체가 따라옵니다.

### S6 시각화 — `/pa-figures`

```python
from pa.figures import apply_style, save
apply_style()                     # 0.6 pt 선, 작은 표식, 8 pt 글꼴, 색맹 안전 팔레트 + 선 모양·표식 순환
fig, ax = plt.subplots(figsize=(3.4, 2.4))
...
save(fig, "06_figures/out/fig2_accuracy")   # PDF + 600 dpi PNG
```

```bash
python -m pa fig check 06_figures/out --min-dpi 600 --width-in 3.5
```

### S7 원고와 윤문 — `/pa-draft`, `/pa-polish`

```bash
python -m pa check 07_manuscript/manuscript.md --out 08_review/check_2026-11-09.md
```

출력 일부(예시):

```
- Sentences: 59, mean 13.6 words (target 15–18, LA-01)
- Over 25 words: 5; over 30: 0 (at most 4); over 32: 0 (split)
## First person (LA-16, forbidden by this profile or the house rules) — 0
## Phrases — 2
- L17 [LA-05] `in order to` — use 'to'
- L42 [LA-09] `novel` — replace with the specific property
```

`/pa-polish`는 구조 → 명료성 → 간결성·어휘 → 분야 문체 순서로 네 번 고치고, 수치·인용·참조가 바뀌지 않았는지 전후로 확인합니다.

### S8 독립 검수 — `/pa-review`, `/pa-panel`

**원고를 쓴 세션이 아닌 새 세션**에서 실행합니다. 보고서는 `08_review/<날짜>_review.md`이고, 첫머리의 "차단 N건" 줄을 관문이 읽습니다. `/pa-panel`은 편집장·수치·표그림·언어·참고문헌·투고 묶음 여섯 에이전트를 동시에 돌려 하나로 합칩니다.

### S9 조립과 투고 — `/pa-build`

```bash
python -m pa build docx --reference-doc journal_template.docx --csl apa.csl    # 저널 Word 템플릿과 인용 형식
python -m pa build docx --blind                                               # 맹검판
python -m pa build latex                                                      # 오류·미해결 참조가 있으면 실패
python -m pa build latex --clean-copy                                         # 수정본의 깨끗한 판(revmarks.sty)
python -m pa build package                                                    # 쓰인 파일만 zip → 빈 폴더에서 재조판
python -m pa round freeze                                                     # 사람이 승인한 뒤, 보낸 판 동결
```

업로드는 사람이 합니다.

### S10 심사 라운드 — `/pa-round`, `/pa-final`

```bash
python -m pa round new          # rounds/round1/ (직전 제출본이 동결되어 있지 않으면 먼저 동결)
#   → 결정 서신을 rounds/round1/comments.md에 그대로 붙여 넣기 (## Editor, ## Reviewer 1 …)
python -m pa round split        # 의견별 항목 E.1, R1.1, R1.2 … → responses.toml
#   → plan.md에 항목별 조치와 HITL/CITL 구분, 원고 수정, responses.toml 채우기
python -m pa round letter       # letter/response_letter.{md,tex,docx} + 빠진 곳 점검
python -m pa round diff round0_submitted current   # 단어 단위 변경 대조
python -m pa round freeze       # 사람이 승인한 뒤 round1_submitted로 동결
python -m pa round final        # 게재 승인 뒤 rounds/final/final_checklist.md
```

`round letter`가 잡는 것: 답이 없는 의견(RV-01), 위치 없는 변경(RV-02), 근거 없는 거절(RV-03), 방어 문구(RV-04), 요청 밖 수정의 논문 반영 여부 누락(RV-07). 자세한 것은 [`docs/rounds.md`](docs/rounds.md).

## 6. HITL과 CITL

| | HITL (사람) | CITL (Claude) |
|---|---|---|
| 맡는 일 | 목표를 바꾸는 결정, 되돌릴 수 없는 일(투고, 공개, 발송), 실험 실행, 최종 책임 | 검색, 대조, 카드, 원장, 그림, 초안, 윤문, 검수, 답변서 초안, 조립 |
| 병목 | 시간과 부재 | 근거 없는 확신, 권한 없음, 맥락 소실, 자기 검수 편향 |
| 기록 | `log/hitl_queue.md`, `log/decisions.md` | `log/citl_queue.md`, `log/history.md`, git |

- Claude는 사람에게 **결정 카드**(선택지 2–4개, 권장안, 이유)로 묻고, 답을 기다리는 동안 되돌릴 수 있는 일은 권장안으로 진행합니다.
- 사람은 **관문에서 승인**하고, 수치는 **사람이 돌린 결과 파일**에서만, 서지는 **원 기록**에서만 오게 해 Claude의 환각을 막습니다.
- 검수는 **다른 세션**이 해서 자기 검수 편향을 막습니다.

```bash
python -m pa ask "투고할 저널을 고르십시오" --stage S1 --options "A 저널 | B 저널" --recommend 1
python -m pa task "그림 2의 선 굵기를 0.4 pt로" --stage S6
python -m pa queue
python -m pa answer H-001 "B" --by "홍길동"
python -m pa approve S4 --by "홍길동" --note "운영점 0.03 확정"
```

자세한 설명과 하루의 흐름 예시: [`docs/hitl_citl.md`](docs/hitl_citl.md).

## 7. 검수 체계

- **우선순위:** 저널 규정 > 하우스 규칙(저자·지도교수 지시) > 분야 프로필 > 규칙 세트([`docs/style/core_rules.md`](docs/style/core_rules.md)) > 사용자의 책 지식 베이스.
- **8단계:** 1 이야기(제목·초록·서론·고찰·결론 여섯 조각만 보고 메시지 복원) → 2 구조와 섹션 → 3 근거와 수치 → 4 표와 그림 → 5 문장과 어휘(기계 점검은 여기서 처음 엶) → 6 참고문헌과 윤리 → 7 최종 점검과 투고 묶음 → 8 편집자 판정(일곱 질문과 반려 사유 대입).
- **등급:** 차단(고치기 전 투고 안 함) / 수정(이번 판에서) / 권고(저자 판단).
- **규칙 ID:** ST(이야기), SE(섹션), EV(근거·수치), DI(표·그림), LA(문장), KO(한국어), RE(참고문헌·윤리), ED(편집자), PK(투고 묶음), RV(답변서), HR(하우스 규칙).

절차 전문: [`docs/review_procedure.md`](docs/review_procedure.md).

## 8. 분야별 문체와 윤문

`project.toml`의 `field`가 분야 프로필을 고릅니다(`python -m pa profiles`).

| 프로필 | 1인칭 | 문장 길이(평균 목표/검토선/상한) | 특히 보는 것 |
|---|---|---|---|
| `engineering` | 금지(기본) | 15–18 / 25 / 32 단어 | 비교 대상과 차이의 수치, 과장어, 재현 설정 |
| `natural_science` | 허용 | 15–20 / 25 / 35 | 불확도, 단위, "prove" |
| `biomedical` | 허용 | 15–20 / 25 / 35 | 보고 지침(CONSORT 등), 윤리·등록, 효과 크기 |
| `social_science` | 허용 | 16–22 / 28 / 40 | 구성 개념, 인과 표현, APA 용어 |
| `humanities` | 허용 | 18–26 / 35 / 55 | 논제, 인용과 해석, 원전 쪽수 |
| `korean` | 금지(기본) | 40–60 / 80 / 120 자 | 번역투, 이중 피동, 추정 어미, 문체 통일 |

저널이 1인칭을 정하면 `project.toml`의 `[journal] first_person = "allow"`(또는 `"forbid"`)가 프로필을 덮어씁니다. 새 분야는 프로필 파일을 복사해 고치면 됩니다. 윤문 절차: [`docs/style/polishing.md`](docs/style/polishing.md).

가지고 있는 글쓰기 책으로 자기만의 규칙 지식 베이스를 만들 수도 있습니다(`/pa-kb`, [`docs/kb_building.md`](docs/kb_building.md)). 결과는 `knowledge/private/`(git 제외)에 둡니다.

## 9. 명령 레퍼런스

### Claude Code 명령

| 명령 | 하는 일 |
|---|---|
| `/pa-new <slug> [제목]` | 새 프로젝트 |
| `/pa-status [slug]` | 현황, 사람이 할 일, Claude가 할 일, 막힌 것 |
| `/pa-topic` | S1 대화로 주제 구체화 |
| `/pa-refs` | S2 문헌·원문·카드 |
| `/pa-kb <책>` | 책 지식 베이스(비공개) |
| `/pa-hypothesis` | S3 가설 |
| `/pa-design` | S4 설계·사전 등록 |
| `/pa-data` | S5 결과 정리, 수치 원장 |
| `/pa-figures` | S6 그림·표 |
| `/pa-draft` | S7 초고 |
| `/pa-polish` | S7 윤문(4단계) |
| `/pa-review` | S8 독립 검수(다른 세션) |
| `/pa-panel` | S8 역할별 6인 검수단 |
| `/pa-build` | S9 조립, 맹검판, 투고 묶음 |
| `/pa-round` | S10 심사 라운드, 답변서 |
| `/pa-final` | 게재 승인 뒤 최종본 |

### `python -m pa` 명령

| 명령 | 하는 일 |
|---|---|
| `new SLUG [--title --field --language --journal --dest]` | 프로젝트 만들기 |
| `status` · `gate SID` · `mark SID todo/doing/done` · `approve SID --by NAME [--note]` | 단계와 관문 |
| `ask TEXT --stage --options "A | B" --recommend N` · `task TEXT --stage` · `answer ID TEXT [--by]` · `queue [--all]` · `log TEXT` | HITL/CITL 대기열과 이력 |
| `refs add/verify/manual/fetch/text/contexts/cards/list` | 문헌 |
| `numbers add/macros/fill/audit` | 수치 원장 |
| `check FILE [--profile --max-words --max-displays --out]` | 원고 기계 점검(.md/.tex/.docx) |
| `fig check DIR [--min-dpi --width-in]` | 그림 파일 점검 |
| `build docx [--blind --reference-doc --csl --pdf --builtin]` · `build latex [--clean-copy]` · `build package` | 조립 |
| `round new/split/letter/freeze [--label]/diff A B/final` | 심사 라운드 |
| `profiles` | 분야 프로필 목록 |

모든 명령은 `--project <폴더 또는 slug>`를 받습니다. 없으면 현재 폴더 위의 `project.toml`을 찾습니다.

## 10. 내 프로젝트를 비공개로 두기, 저작권, 보안

- 이 저장소의 `projects/`는 **git에서 제외**됩니다. 원고·자료·심사 의견이 공개 저장소로 나가지 않습니다. 프로젝트를 버전 관리하려면 비공개 저장소를 만들고 `PA_PROJECTS`로 가리키십시오.
- 내려받은 원문 PDF와 추출 텍스트(`02_literature/papers/`, `text/`), 원자료(`05_data/raw/`)는 프로젝트 `.gitignore`로 제외됩니다.
- 도구는 **열린 사본만** 내려받고 페이월을 우회하지 않습니다.
- 공개 규칙 세트는 글쓰기 책의 원리를 이 저장소의 말로 요약한 것이며 원문을 옮기지 않았습니다. 책으로 만든 지식 베이스는 `knowledge/private/`에만 두십시오.
- 토큰, 비밀번호, 이메일 같은 값은 파일에 쓰지 말고 환경 변수로 두십시오. 승인 기록에는 이름만 남깁니다.

## 11. 문제 해결

| 증상 | 해결 |
|---|---|
| `no project.toml here or above` | `--project <slug>`를 주거나 프로젝트 폴더 안에서 실행 |
| 관문이 안 열림 | `python -m pa gate S3`가 남은 조건을 줄별로 보여 줍니다. `[TODO]`를 채우거나, 사람이 승인 |
| `approve`가 거부됨 | 승인 전에 기계 조건(자리 표시, 미대조 서지 등)이 먼저 통과해야 합니다 |
| DOCX에 인용·그림이 없음 | pandoc이 없어 내장 작성기가 쓰였습니다. pandoc을 설치하십시오 |
| `pdflatex not found` | TeX Live/MiKTeX 설치. LaTeX 없이 쓰려면 Markdown 원고와 `build docx` |
| Windows에서 한글이 깨짐 | PowerShell에서 `$env:PYTHONUTF8 = "1"`. 직접 쓰는 스크립트는 `subprocess.run(..., encoding="utf-8")` |
| PowerShell 5에서 `&&` 오류 | `명령1; if ($?) { 명령2 }` |
| `refs fetch`가 모두 "no open copy" | `PA_EMAIL`을 설정해야 Unpaywall을 씁니다. 그래도 없으면 도서관에서 받아 `papers/<키>.pdf`로 |

## 12. 저장소 구조

```
Paper_assistant/
├── CLAUDE.md                 Claude 운영 규칙
├── .claude/commands/         /pa-* 단계 명령 16개
├── .claude/agents/           역할별 검수 에이전트 6개(읽기 전용)
├── pa/                       python -m pa 도구 (profiles/ 분야 프로필)
├── templates/                project/ 뼈대, response/ 라운드, review/ 보고서, latex/
├── docs/                     pipeline, hitl_citl, review_procedure, rounds, kb_building, folder_layout, style/
├── knowledge/                규칙 세트 색인, private/(git 제외)
├── examples/demo_project/    가상의 예시 프로젝트
├── projects/                 내 프로젝트(git 제외)
└── tests/                    pytest
```

## 라이선스

Apache License 2.0 ([`LICENSE`](LICENSE)).
