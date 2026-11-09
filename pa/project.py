"""Project folders, stages, gates and the two work lanes (HITL = human in the loop, CITL = Claude in the loop).

A project is one folder (``projects/<slug>/`` by default) with a ``project.toml`` written by ``pa new``.
Stage status lives in ``log/state.json``; decisions and approvals in ``log/decisions.md``; open questions for the
person in ``log/hitl_queue.md``; work Claude can do without the person in ``log/citl_queue.md``.
See docs/pipeline.md and docs/hitl_citl.md.
"""
from __future__ import annotations

import datetime as _dt
import json
import os
import re
import shutil
import tomllib
from dataclasses import dataclass
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
TEMPLATES = ROOT / "templates" / "project"
PLACEHOLDER = re.compile(r"\[(TODO|TBD|FILL|PENDING|ref|refs|citation needed|insert)[^\]]*\]|\{\{\s*fill\s*\}\}", re.I)


@dataclass(frozen=True)
class Stage:
    sid: str            # S1 ... S10
    name: str
    folder: str
    artifacts: tuple    # files that must exist (relative to the project) before the gate
    gate: str           # "HITL": the person approves; "CITL": mechanical checks only; "BOTH"
    command: str        # the slash command that runs the stage
    goal: str


STAGES = (
    Stage("S1", "topic", "01_topic", ("01_topic/topic.md",), "HITL", "/pa-topic",
          "연구 질문(RQ)과 기여를 한 문장씩 확정"),
    Stage("S2", "literature", "02_literature", ("02_literature/refs.bib", "02_literature/index.json"), "BOTH", "/pa-refs",
          "원문 확보, 서지 대조, 문헌 카드(KB)"),
    Stage("S3", "hypotheses", "03_hypotheses", ("03_hypotheses/hypotheses.md",), "HITL", "/pa-hypothesis",
          "검증 가능한 가설과 반증 조건"),
    Stage("S4", "design", "04_design", ("04_design/design.md",), "HITL", "/pa-design",
          "실험 설계와 사전 등록(지표, 운영점, 분석 계획)"),
    Stage("S5", "data", "05_data", ("05_data/numbers.csv",), "CITL", "/pa-data",
          "실행 결과 정리와 수치 원장(numbers.csv)"),
    Stage("S6", "figures", "06_figures", ("06_figures/figures.md",), "CITL", "/pa-figures",
          "표·그림 생성 스크립트와 점검"),
    Stage("S7", "draft", "07_manuscript", ("07_manuscript/manuscript.md",), "CITL", "/pa-draft",
          "원고 초고와 기계 점검"),
    Stage("S8", "review", "08_review", (), "BOTH", "/pa-review",
          "독립 세션 검수(8단계), 차단 0건"),
    Stage("S9", "build", "07_manuscript/build", (), "HITL", "/pa-build",
          "LaTeX/DOCX 조립, 투고 묶음, 사람의 최종 승인과 제출"),
    Stage("S10", "rounds", "rounds", (), "HITL", "/pa-round",
          "심사 라운드: 의견 분해, 수정, 답변서, 재제출"),
)
STAGE_BY_ID = {s.sid: s for s in STAGES}
STAGE_BY_NAME = {s.name: s for s in STAGES}


def today() -> str:
    return _dt.date.today().isoformat()


def now() -> str:
    return _dt.datetime.now().astimezone().strftime("%Y-%m-%d %H:%M %Z").strip()


def projects_dir() -> Path:
    return Path(os.environ.get("PA_PROJECTS", ROOT / "projects"))


def find_project(path: str | Path | None = None) -> Path:
    """The project folder: the given path, or the nearest parent of the current directory holding project.toml."""
    if path:
        p = Path(path)
        if not (p / "project.toml").exists() and (projects_dir() / str(path) / "project.toml").exists():
            p = projects_dir() / str(path)
        if not (p / "project.toml").exists():
            raise SystemExit(f"not a project folder (no project.toml): {p}")
        return p.resolve()
    here = Path.cwd().resolve()
    for d in (here, *here.parents):
        if (d / "project.toml").exists():
            return d
    raise SystemExit("no project.toml here or above; pass --project <folder or slug>")


def load_config(project: Path) -> dict:
    with open(project / "project.toml", "rb") as f:
        return tomllib.load(f)


def load_state(project: Path) -> dict:
    p = project / "log" / "state.json"
    if p.exists():
        return json.loads(p.read_text(encoding="utf-8"))
    return {"stages": {s.sid: "todo" for s in STAGES}, "round": 0}


def save_state(project: Path, state: dict) -> None:
    p = project / "log" / "state.json"
    p.parent.mkdir(parents=True, exist_ok=True)
    p.write_text(json.dumps(state, ensure_ascii=False, indent=1) + "\n", encoding="utf-8")


def slugify(s: str) -> str:
    s = re.sub(r"[^A-Za-z0-9가-힣]+", "-", s.strip()).strip("-").lower()
    return s or "project"


def toml_str(s: str) -> str:
    return '"' + s.replace("\\", "\\\\").replace('"', '\\"') + '"'


def new_project(slug: str, title: str = "", field: str = "engineering", language: str = "en",
                journal: str = "", dest: Path | None = None) -> Path:
    """Create a project folder from templates/project. Refuses to overwrite an existing folder."""
    slug = slugify(slug)
    dest = Path(dest) if dest else projects_dir() / slug
    if dest.exists() and any(dest.iterdir()):
        raise SystemExit(f"folder exists and is not empty: {dest}")
    shutil.copytree(TEMPLATES, dest, dirs_exist_ok=True)
    values = {"SLUG": slug, "TITLE": title or slug, "FIELD": field, "LANGUAGE": language,
              "JOURNAL": journal, "DATE": today()}
    for f in dest.rglob("*"):
        if f.is_file() and f.suffix in {".md", ".toml", ".csv", ".bib", ".json", ".tex"}:
            t = f.read_text(encoding="utf-8")
            for k, v in values.items():
                t = t.replace("{{" + k + "}}", v)
            f.write_text(t, encoding="utf-8")
    cfg = dest / "project.toml"
    t = cfg.read_text(encoding="utf-8")
    t = re.sub(r'^title = .*$', "title = " + toml_str(title or slug), t, count=1, flags=re.M)
    t = re.sub(r'^name = .*$', "name = " + toml_str(journal), t, count=1, flags=re.M)
    cfg.write_text(t, encoding="utf-8")
    save_state(dest, {"stages": {s.sid: "todo" for s in STAGES}, "round": 0})
    log_event(dest, f"project created: {title or slug} (field {field}, language {language})")
    return dest


# ------------------------------------------------------------------ logs and the two lanes

def log_event(project: Path, text: str) -> None:
    p = project / "log" / "history.md"
    p.parent.mkdir(parents=True, exist_ok=True)
    if not p.exists():
        p.write_text("# 작업 이력\n\n| 시각 | 내용 |\n|---|---|\n", encoding="utf-8")
    with p.open("a", encoding="utf-8") as f:
        f.write(f"| {now()} | {text.replace('|', '/')} |\n")


def _next_id(text: str, prefix: str) -> str:
    nums = [int(n) for n in re.findall(rf"\b{prefix}-(\d+)\b", text)]
    return f"{prefix}-{(max(nums) + 1) if nums else 1:03d}"


QUEUE_HEAD = {"hitl": "# HITL 대기열 — 사람이 답하거나 승인할 것\n\n"
                      "Claude가 올리고 사람이 답합니다. 답이 오기 전에는 되돌릴 수 있는 일만 권장안으로 진행합니다.\n\n"
                      "| ID | 상태 | 단계 | 질문 | 선택지 | 권장 | 올린 시각 | 답 |\n|---|---|---|---|---|---|---|---|\n",
              "citl": "# CITL 대기열 — Claude가 사람 없이 할 수 있는 일\n\n"
                      "사람이 맡기거나 Claude가 찾아 올립니다. 사람을 기다리는 동안 이 목록을 처리합니다.\n\n"
                      "| ID | 상태 | 단계 | 할 일 | 올린 시각 | 결과 |\n|---|---|---|---|---|---|\n"}


def queue_path(project: Path, lane: str) -> Path:
    return project / "log" / f"{lane}_queue.md"


def queue_add(project: Path, lane: str, stage: str, text: str, options: list[str] | None = None,
              recommend: int | None = None) -> str:
    p = queue_path(project, lane)
    if not p.exists():
        p.parent.mkdir(parents=True, exist_ok=True)
        p.write_text(QUEUE_HEAD[lane], encoding="utf-8")
    body = p.read_text(encoding="utf-8")
    qid = _next_id(body, "H" if lane == "hitl" else "C")
    text = text.replace("|", "/").replace("\n", " ")
    if lane == "hitl":
        opts = " / ".join(f"({chr(65 + i)}) {o}" for i, o in enumerate(options or []))
        rec = chr(65 + recommend) if recommend is not None and options else ""
        row = f"| {qid} | open | {stage} | {text} | {opts} | {rec} | {now()} | |\n"
    else:
        row = f"| {qid} | open | {stage} | {text} | {now()} | |\n"
    with p.open("a", encoding="utf-8") as f:
        f.write(row)
    log_event(project, f"{lane.upper()} {qid} added ({stage}): {text}")
    return qid


def queue_rows(project: Path, lane: str) -> list[list[str]]:
    p = queue_path(project, lane)
    if not p.exists():
        return []
    rows = []
    for line in p.read_text(encoding="utf-8").splitlines():
        if re.match(r"^\| [HC]-\d+ \|", line):
            rows.append([c.strip() for c in line.strip().strip("|").split("|")])
    return rows


def queue_close(project: Path, qid: str, answer: str, by: str = "") -> None:
    lane = "hitl" if qid.upper().startswith("H") else "citl"
    p = queue_path(project, lane)
    lines = p.read_text(encoding="utf-8").splitlines() if p.exists() else []
    done = False
    for i, line in enumerate(lines):
        if line.startswith(f"| {qid} |"):
            cells = [c.strip() for c in line.strip().strip("|").split("|")]
            cells[1] = "closed"
            cells[-1] = (answer + (f" — {by}" if by else "")).replace("|", "/")
            lines[i] = "| " + " | ".join(cells) + " |"
            done = True
    if not done:
        raise SystemExit(f"no queue item {qid}")
    p.write_text("\n".join(lines) + "\n", encoding="utf-8")
    if lane == "hitl":
        record_decision(project, f"{qid}: {answer}", by=by)
    log_event(project, f"{qid} closed: {answer}")


def record_decision(project: Path, text: str, by: str = "", stage: str = "") -> None:
    p = project / "log" / "decisions.md"
    if not p.exists():
        p.parent.mkdir(parents=True, exist_ok=True)
        p.write_text("# 결정 기록\n\n사람이 내린 결정과 단계 승인만 적습니다. 지우지 않고, 바뀌면 새 행을 더합니다.\n\n"
                     "| 시각 | 단계 | 결정 | 결정한 사람 |\n|---|---|---|---|\n", encoding="utf-8")
    with p.open("a", encoding="utf-8") as f:
        f.write(f"| {now()} | {stage} | {text.replace('|', '/')} | {by.replace('|', '/')} |\n")


def approve(project: Path, sid: str, by: str, note: str = "") -> None:
    if sid not in STAGE_BY_ID:
        raise SystemExit(f"unknown stage {sid}")
    if not by.strip():
        raise SystemExit("an approval needs the person's name (--by)")
    record_decision(project, f"APPROVED {sid} {STAGE_BY_ID[sid].name}" + (f": {note}" if note else ""), by=by, stage=sid)
    st = load_state(project)
    st["stages"][sid] = "done"
    save_state(project, st)
    log_event(project, f"{sid} approved by {by}")


def approved(project: Path, sid: str) -> bool:
    p = project / "log" / "decisions.md"
    return p.exists() and bool(re.search(rf"\| APPROVED {sid} ", p.read_text(encoding="utf-8")))


# ------------------------------------------------------------------ gates

def gate(project: Path, sid: str) -> list[str]:
    """Problems that block the stage gate (empty list = the gate passes)."""
    st = STAGE_BY_ID[sid]
    problems = []
    for a in st.artifacts:
        f = project / a
        if not f.exists():
            problems.append(f"missing {a}")
            continue
        if f.suffix == ".md":
            text = f.read_text(encoding="utf-8")
            left = PLACEHOLDER.findall(text)
            if left:
                problems.append(f"{a}: {len(left)} placeholder(s) left ([TODO]/[TBD]/...)")
    if sid == "S2":
        idx = project / "02_literature" / "index.json"
        if idx.exists():
            items = json.loads(idx.read_text(encoding="utf-8")).get("items", {})
            bad = [k for k, v in items.items() if v.get("verified") is not True]
            if bad:
                problems.append(f"references not verified against a primary record: {', '.join(sorted(bad)[:10])}"
                                + (" …" if len(bad) > 10 else ""))
    if sid == "S5":
        from pa import numbers as N
        f = project / "05_data" / "numbers.csv"
        if f.exists():
            if not N.load(f):
                problems.append("05_data/numbers.csv has no rows yet")
            for r in N.load(f).values():
                if not r.source:
                    problems.append(f"numbers.csv: '{r.key}' has no source")
    if sid == "S7":
        from pa import check as C
        m = project / "07_manuscript" / "manuscript.md"
        if m.exists():
            res = C.check(C.read_text(m), C.project_profile(load_config(project)))
            if res["leftover"]:
                problems.append(f"manuscript: {len(res['leftover'])} leftover placeholder(s)")
    if sid == "S8":
        reviews = sorted((project / "08_review").glob("*_review.md"))
        if not reviews:
            problems.append("no review report in 08_review/ (run /pa-review in a separate session)")
        else:
            last = reviews[-1].read_text(encoding="utf-8")
            m = re.search(r"차단\s*(\d+)\s*건|blocking[:\s]+(\d+)", last, re.I)
            if not m:
                problems.append(f"{reviews[-1].name}: no blocking count line ('차단 N건')")
            elif int(m.group(1) or m.group(2)) > 0:
                problems.append(f"{reviews[-1].name}: {m.group(1) or m.group(2)} blocking item(s) open")
    if st.gate in ("HITL", "BOTH") and not approved(project, sid):
        problems.append(f"{sid} needs the person's approval: python -m pa approve {sid} --by <name>")
    open_h = [r for r in queue_rows(project, "hitl") if r[1] == "open" and r[2] == sid]
    if open_h:
        problems.append(f"open HITL questions for {sid}: {', '.join(r[0] for r in open_h)}")
    return problems


def status(project: Path) -> str:
    cfg = load_config(project)
    st = load_state(project)
    out = [f"# {cfg['project'].get('title', project.name)}", "",
           f"- folder: {project}", f"- field profile: {cfg['project'].get('field')}, language: {cfg['project'].get('language')}",
           f"- journal: {cfg.get('journal', {}).get('name') or '(not set)'}", f"- review round: {st.get('round', 0)}", "",
           "| 단계 | 이름 | 상태 | 관문 | 막힌 이유 | 명령 |", "|---|---|---|---|---|---|"]
    next_stage = None
    for s in STAGES:
        probs = gate(project, s.sid)
        state = st["stages"].get(s.sid, "todo")
        if state != "done" and not probs and s.gate == "CITL":
            state = "ready"
        if next_stage is None and state != "done":
            next_stage = s
        out.append(f"| {s.sid} | {s.name} | {state} | {s.gate} | {'; '.join(probs[:2]) or '-'} | {s.command} |")
    h = [r for r in queue_rows(project, "hitl") if r[1] == "open"]
    c = [r for r in queue_rows(project, "citl") if r[1] == "open"]
    out += ["", f"- 열린 HITL 질문 {len(h)}건" + (": " + ", ".join(f"{r[0]} {r[3][:40]}" for r in h[:5]) if h else ""),
            f"- 열린 CITL 작업 {len(c)}건" + (": " + ", ".join(f"{r[0]} {r[3][:40]}" for r in c[:5]) if c else "")]
    if next_stage:
        out.append(f"- 다음 단계: {next_stage.sid} {next_stage.name} — {next_stage.goal} ({next_stage.command})")
    return "\n".join(out)


def mark(project: Path, sid: str, state: str) -> None:
    if state not in ("todo", "doing", "done"):
        raise SystemExit("state must be todo, doing or done")
    if state == "done":
        probs = gate(project, sid)
        if probs:
            raise SystemExit("gate not passed:\n- " + "\n- ".join(probs))
    st = load_state(project)
    st["stages"][sid] = state
    save_state(project, st)
    log_event(project, f"{sid} -> {state}")
