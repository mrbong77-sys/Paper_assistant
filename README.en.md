# Paper Assistant (English summary)

A toolset and pipeline that takes one research paper from a rough topic to an accepted manuscript with
[Claude Code](https://docs.claude.com/en/docs/claude-code). Clone the repository, open it in Claude Code, and run the
`/pa-*` commands; Claude follows [`CLAUDE.md`](CLAUDE.md). The documentation is written in Korean; the commands, file
formats and the Python tool are language-neutral, and manuscripts can be written in English or Korean.

## What it does

| Stage | Command | Output | Gate |
|---|---|---|---|
| S1 Topic refinement by dialogue | `/pa-topic` | research questions, journal rule sheet, house rules | human approval |
| S2 Literature, open full texts, reference cards | `/pa-refs` | `refs.bib` checked against Crossref/arXiv, one card per reference | checks + human |
| S3 Hypotheses | `/pa-hypothesis` | predictions, falsification conditions, rival hypotheses | human |
| S4 Experimental design and preregistration | `/pa-design` | conditions, metrics, data isolation, analysis plan | human (no main run before) |
| S5 Runs and the numbers ledger | `/pa-data` | `numbers.csv`: every manuscript number with its source | checks |
| S6 Figures | `/pa-figures` | thin-line, colour-blind-safe figures; dpi/vector check | checks |
| S7 Draft and field-specific polishing | `/pa-draft`, `/pa-polish` | manuscript with `{{num:key}}` / `\NumKey` and `[@key]` | checks |
| S8 Independent review (separate session) | `/pa-review`, `/pa-panel` | eight-step report, six-role review panel | zero blocking + human |
| S9 Assembly and submission | `/pa-build` | DOCX via pandoc or LaTeX rebuilt from a clean folder, blind copy, frozen snapshot | human |
| S10 Review rounds | `/pa-round`, `/pa-final` | `rounds/round1…final`, response letter (MD/TeX/DOCX) with completeness checks | human |

Two work lanes: **HITL** (decisions, irreversible steps, experiments; `log/hitl_queue.md`) and **CITL** (work Claude
does without the person; `log/citl_queue.md`). Claude asks with options and a recommendation, keeps working on
reversible steps meanwhile, and never opens a human gate itself.

## Quick start

```bash
git clone https://github.com/mrbong77-sys/Paper_assistant.git && cd Paper_assistant
python -m pa --help                       # Python 3.11+, standard library only
python -m pa --project examples/demo_project status
claude                                    # then: /pa-new my-study
```

Optional: pandoc (DOCX, citations), TeX Live (LaTeX), poppler-utils (pdftotext), LibreOffice (DOCX to PDF), matplotlib.

Your projects live in `projects/` (ignored by git) or in a private repository set with `PA_PROJECTS`.
Downloaded papers and raw data are never committed; only open-access copies are fetched.

Field profiles (`python -m pa profiles`): engineering, natural_science, biomedical, social_science, humanities, korean.

License: Apache-2.0.
