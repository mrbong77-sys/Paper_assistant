# 폴더 체계

## 이 저장소

```
Paper_assistant/
├── CLAUDE.md               Claude가 이 저장소에서 따르는 운영 규칙
├── README.md               사용법(빠른 시작, 단계별 예시)
├── .claude/
│   ├── commands/           슬래시 명령: /pa-new, /pa-topic, … /pa-round (단계별 절차)
│   ├── agents/             역할별 검수 에이전트: pa-editor, pa-numbers, … (읽기 전용)
│   └── settings.json       `python -m pa` 실행 허용
├── pa/                     파이썬 도구(표준 라이브러리만; 그림은 matplotlib, DOCX는 pandoc 권장)
│   └── profiles/           분야 프로필(TOML)
├── templates/
│   ├── project/            새 프로젝트의 뼈대(pa new가 복사)
│   ├── response/           라운드 문서 템플릿
│   ├── review/             검수 보고서 템플릿
│   └── latex/              main.tex, revmarks.sty
├── docs/                   파이프라인, HITL/CITL, 검수 절차, 라운드, 문체 규칙, KB 구축
├── knowledge/              공개 가능한 지식 베이스(규칙 세트 색인). private/는 git 제외
├── examples/demo_project/  가상의 예시 프로젝트(전 단계가 채워져 있음)
├── projects/               사용자 프로젝트(git 제외)
└── tests/                  pytest, 임시 디렉터리에서만 실행
```

## 프로젝트 하나

`templates/project/README.md`가 각 폴더의 역할을 설명합니다. 요약:

| 폴더 | 단계 | 커밋 | 내용 |
|---|---|---|---|
| `01_topic/` | S1 | 예 | 주제 구체화, 저널 규정표, 하우스 규칙 |
| `02_literature/` | S2 | refs.bib·index.json·cards만 | 원문 `papers/`와 텍스트 `text/`는 저작물이라 제외 |
| `03_hypotheses/` | S3 | 예 | 가설 |
| `04_design/` | S4 | 예 | 설계와 사전 등록 |
| `05_data/` | S5 | raw 제외 | 원자료는 읽기 전용, 결과는 스크립트로만 |
| `06_figures/` | S6 | 예 | 예산표, 스크립트, 출력 |
| `07_manuscript/` | S7 | build 제외 | 원고 원본 |
| `08_review/` | S8 | 예 | 검수 보고서 |
| `rounds/` | S10 | 예 | 라운드별 동결본과 소통 기록 |
| `submission/` | S9 | 예 | 투고 묶음 |
| `log/` | 전체 | 예 | 이력, 결정, 두 대기열, 상태 |

## 사용자 프로젝트를 어디에 둘까

- 이 저장소의 `projects/`는 git에서 제외됩니다. 원고와 자료가 공개 저장소로 나가지 않습니다.
- 버전 관리를 하려면 **비공개** 저장소를 하나 만들고 `PA_PROJECTS` 환경 변수로 가리킵니다.
- 실험 코드와 원자료가 큰 연구는 연구 저장소를 따로 두고, 프로젝트의 `05_data/README.md`에 결과 파일의 위치(저장소, 커밋)를 적습니다. 수치 원장의 `source`에 `연구저장소:경로@커밋`을 씁니다.
