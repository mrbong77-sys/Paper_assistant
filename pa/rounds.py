"""Review rounds: frozen snapshots, the comment list, the response table and the response letter.

Layout (one folder per round, nothing inside a closed round is edited again):
  rounds/round0_submitted/      the manuscript as first submitted (frozen by ``pa round freeze``)
  rounds/round1/comments.md     the decision letter pasted as received (headings: ## Editor, ## Reviewer 1, ...)
  rounds/round1/responses.toml  one [[item]] per comment (id, comment, response, change, status, in_paper)
                                and one [[own]] per change made without a request
  rounds/round1/plan.md         the revision plan: per item who acts (HITL/CITL), what to run, which files change
  rounds/round1/letter/         response_letter.md / .tex / .docx (``pa round letter``)
  rounds/round1_submitted/      the revised manuscript as sent
  rounds/final/                 the accepted version and the final files

    python -m pa round new           # opens the next round, freezes the previous submission if needed
    python -m pa round split         # comments.md -> [[item]] stubs in responses.toml
    python -m pa round letter        # responses.toml -> letter (Markdown, LaTeX, DOCX) + completeness check
    python -m pa round freeze        # copies 07_manuscript into rounds/round<N>_submitted/
    python -m pa round diff A B      # word-level changes of manuscript.md between two snapshots
    python -m pa round final         # opens rounds/final/ with the final checklist
"""
from __future__ import annotations

import difflib
import re
import shutil
import tomllib
from pathlib import Path

from pa import project as P

STATUS = {"done": "Done", "partly": "Partly done", "declined": "Not changed (reason given)", "pending": "PENDING"}


def _round_dir(project: Path, n: int) -> Path:
    return project / "rounds" / f"round{n}"


def freeze(project: Path, label: str | None = None) -> Path:
    st = P.load_state(project)
    n = st.get("round", 0)
    dest = project / "rounds" / (label or f"round{n}_submitted")
    if dest.exists():
        raise SystemExit(f"{dest} exists; a frozen snapshot is never overwritten")
    src = project / "07_manuscript"
    shutil.copytree(src, dest, ignore=shutil.ignore_patterns("build", "_filled*.md", "*.aux", "*.log"))
    for extra in ("05_data/numbers.csv", "02_literature/refs.bib"):
        if (project / extra).exists():
            (dest / "_with").mkdir(exist_ok=True)
            shutil.copy(project / extra, dest / "_with" / Path(extra).name)
    P.log_event(project, f"frozen snapshot {dest.name}")
    P.record_decision(project, f"snapshot {dest.name} frozen (what was sent)", stage="S9" if n == 0 else "S10")
    return dest


def new_round(project: Path) -> Path:
    st = P.load_state(project)
    prev = st.get("round", 0)
    if not (project / "rounds" / f"round{prev}_submitted").exists():
        freeze(project)
    n = prev + 1
    d = _round_dir(project, n)
    d.mkdir(parents=True, exist_ok=False)
    tpl = P.ROOT / "templates" / "response"
    for name in ("comments.md", "plan.md", "responses.toml"):
        t = (tpl / name).read_text(encoding="utf-8").replace("{{ROUND}}", str(n))
        (d / name).write_text(t, encoding="utf-8")
    st["round"] = n
    st["stages"]["S10"] = "doing"
    P.save_state(project, st)
    P.log_event(project, f"round {n} opened")
    return d


def split_comments(text: str) -> list[dict]:
    """Headings name the reviewer (## Editor, ## Reviewer 2); each numbered point or paragraph is one comment."""
    items, who, prefix, k = [], None, None, 0
    para: list[str] = []

    def flush():
        nonlocal k, para
        body = " ".join(x.strip() for x in para).strip()
        para = []
        if who and body:
            k += 1
            items.append({"id": f"{prefix}.{k}", "reviewer": who, "comment": body})
    for line in text.splitlines():
        h = re.match(r"^#{1,3}\s+(.*)", line)
        if h:
            flush()
            who = h.group(1).strip()
            if not re.match(r"(the\s+)?(handling\s+|academic\s+|associate\s+)?(editor|reviewer|referee)\b|"
                            r"(편집|심사위원|심사자|검토자)", who, re.I):
                who = None                       # a title or notes heading, not a commenter
                continue
            m = re.search(r"(\d+)", who)
            prefix = "E" if who.lower().startswith(("editor", "편집")) else (f"R{m.group(1)}" if m else re.sub(r"\W", "", who)[:3].upper())
            k = 0
            continue
        if line.strip().startswith(">") or line.strip().startswith("<!--"):
            continue
        if re.match(r"^\s*(\d+[.)]|[-*])\s+", line):
            flush()
            para.append(re.sub(r"^\s*(\d+[.)]|[-*])\s+", "", line))
        elif not line.strip():
            flush()
        else:
            para.append(line)
    flush()
    return items


def _toml_text(s: str) -> str:
    return '"""' + s.replace("\\", "\\\\").replace('"""', '\\"\\"\\"') + '"""'


def split(project: Path) -> int:
    d = _round_dir(project, P.load_state(project)["round"])
    items = split_comments((d / "comments.md").read_text(encoding="utf-8"))
    path = d / "responses.toml"
    have = tomllib.loads(path.read_text(encoding="utf-8")).get("item", [])
    known = {i["id"] for i in have}
    add = [i for i in items if i["id"] not in known]
    with path.open("a", encoding="utf-8") as f:
        for i in add:
            f.write(f'\n[[item]]\nid = "{i["id"]}"\nreviewer = "{i["reviewer"]}"\ncomment = {_toml_text(i["comment"])}\n'
                    f'response = ""\nchange = ""\nstatus = "pending"\nlane = "CITL"\nin_paper = true\n')
    return len(add)


def load_responses(path: Path) -> dict:
    data = tomllib.loads(path.read_text(encoding="utf-8"))
    data.setdefault("letter", {})
    data.setdefault("item", [])
    data.setdefault("own", [])
    return data


def problems(data: dict) -> list[str]:
    """Completeness rules RV-01 to RV-04 of docs/style/core_rules.md."""
    out = []
    ids = [i.get("id") for i in data["item"]]
    for dup in {x for x in ids if ids.count(x) > 1}:
        out.append(f"{dup}: duplicate id")
    for i in data["item"]:
        st = i.get("status", "pending")
        if st not in STATUS:
            out.append(f"{i.get('id')}: unknown status '{st}'")
        if st == "pending" or not i.get("response", "").strip():
            out.append(f"{i.get('id')}: no response yet (RV-01)")
        if st in ("done", "partly") and i.get("in_paper", True) and not i.get("change", "").strip():
            out.append(f"{i.get('id')}: says the paper changed but gives no location (RV-02)")
        if st == "declined" and len(i.get("response", "")) < 40:
            out.append(f"{i.get('id')}: declined without a reasoned answer (RV-03)")
        if re.search(r"\b(we believe|we feel|obviously|clearly|as stated)\b", i.get("response", ""), re.I):
            out.append(f"{i.get('id')}: defensive or vague wording in the response (RV-04)")
    for o in data["own"]:
        if "in_paper" not in o:
            out.append(f"{o.get('id')}: own-initiative change must say whether the paper changed (in_paper)")
    return out


def _md_cell(s: str) -> str:
    return s.replace("|", "/").replace("\n", " ")


def letter_markdown(data: dict) -> str:
    L = data["letter"]
    out = [f"# Response to the editor and reviewers", "",
           f"Manuscript: {L.get('manuscript_id', '')} — \"{L.get('title', '')}\"" + (f", {L['journal']}" if L.get("journal") else ""), ""]
    if L.get("intro"):
        out += [L["intro"].strip(), ""]
    groups: dict[str, list] = {}
    for i in data["item"]:
        groups.setdefault(i.get("reviewer", "Reviewer"), []).append(i)
    for who, items in groups.items():
        out += [f"## {who}", "", "| # | Comment | Response | Change in the manuscript | Status |", "|---|---|---|---|---|"]
        for i in items:
            out.append(f"| {i['id']} | {_md_cell(i.get('comment', ''))} | {_md_cell(i.get('response', ''))} | "
                       f"{_md_cell(i.get('change', '') or '—')} | {STATUS.get(i.get('status', 'pending'), i.get('status'))} |")
        out.append("")
    if data["own"]:
        out += ["## Changes made without a request", "",
                "| # | Change | Reason | Location | In the paper |", "|---|---|---|---|---|"]
        for o in data["own"]:
            out.append(f"| {o.get('id')} | {_md_cell(o.get('change', ''))} | {_md_cell(o.get('reason', ''))} | "
                       f"{_md_cell(o.get('location', '') or '—')} | {'Yes' if o.get('in_paper') else 'No (record only)'} |")
        out.append("")
    return "\n".join(out)


def _tex(s: str) -> str:
    s = s.replace("\\", r"\textbackslash{}")
    for a, b in (("&", r"\&"), ("%", r"\%"), ("#", r"\#"), ("_", r"\_"), ("$", r"\$"), ("{", r"\{"), ("}", r"\}")):
        s = s.replace(a, b)
    return s.replace("\\textbackslash\\{\\}", r"\textbackslash{}").replace("§", r"\S{}")


def letter_latex(data: dict) -> str:
    L = data["letter"]
    out = [r"\documentclass[10pt]{article}", r"\usepackage[a4paper,margin=2cm]{geometry}", r"\usepackage[T1]{fontenc}",
           r"\usepackage[utf8]{inputenc}", r"\usepackage{array,longtable,booktabs,parskip}", r"\usepackage[hidelinks]{hyperref}",
           r"\newcolumntype{P}[1]{>{\raggedright\arraybackslash}p{#1}}", r"\begin{document}",
           r"\begin{center}{\large\textbf{Response to the editor and reviewers}}\\[4pt]",
           f"Manuscript {_tex(L.get('manuscript_id', ''))}, ``{_tex(L.get('title', ''))}''" + (f"\\\\ {_tex(L['journal'])}" if L.get("journal") else ""),
           r"\end{center}"]
    if L.get("intro"):
        out.append(_tex(L["intro"].strip()))
    head = r"\textbf{\#} & \textbf{Comment} & \textbf{Response} & \textbf{Change} & \textbf{Status} \\ \midrule"
    groups: dict[str, list] = {}
    for i in data["item"]:
        groups.setdefault(i.get("reviewer", "Reviewer"), []).append(i)
    for who, items in groups.items():
        out += [f"\\section*{{{_tex(who)}}}", r"{\small\begin{longtable}{@{}P{0.9cm}P{4.4cm}P{6.6cm}P{2.6cm}P{1.5cm}@{}}",
                r"\toprule", head, r"\endhead", r"\bottomrule", r"\endfoot"]
        for i in items:
            out.append(f"{_tex(i['id'])} & {_tex(i.get('comment', ''))} & {_tex(i.get('response', ''))} & "
                       f"{_tex(i.get('change', '') or '--')} & {_tex(STATUS.get(i.get('status', 'pending'), ''))} \\\\ \\midrule")
        out.append(r"\end{longtable}}")
    if data["own"]:
        out += [r"\section*{Changes made without a request}", r"{\small\begin{longtable}{@{}P{0.9cm}P{6cm}P{4.6cm}P{2.4cm}P{2cm}@{}}",
                r"\toprule", r"\textbf{\#} & \textbf{Change} & \textbf{Reason} & \textbf{Location} & \textbf{In the paper} \\ \midrule",
                r"\endhead", r"\bottomrule", r"\endfoot"]
        for o in data["own"]:
            out.append(f"{_tex(o.get('id', ''))} & {_tex(o.get('change', ''))} & {_tex(o.get('reason', ''))} & "
                       f"{_tex(o.get('location', '') or '--')} & {'Yes' if o.get('in_paper') else 'No (record only)'} \\\\ \\midrule")
        out.append(r"\end{longtable}}")
    out.append(r"\end{document}")
    return "\n".join(out) + "\n"


def letter(project: Path, round_no: int | None = None) -> dict:
    from pa import build as B
    n = round_no or P.load_state(project)["round"]
    d = _round_dir(project, n)
    data = load_responses(d / "responses.toml")
    out = d / "letter"
    out.mkdir(exist_ok=True)
    md = letter_markdown(data)
    (out / "response_letter.md").write_text(md, encoding="utf-8")
    (out / "response_letter.tex").write_text(letter_latex(data), encoding="utf-8")
    B.write_docx_builtin(md, out / "response_letter.docx")
    probs = problems(data)
    return {"folder": str(out), "items": len(data["item"]), "own": len(data["own"]), "problems": probs}


def diff(project: Path, a: str, b: str, name: str = "manuscript.md") -> str:
    def load(label):
        p = project / "07_manuscript" / name if label == "current" else project / "rounds" / label / name
        if not p.exists():
            raise SystemExit(f"no {p}")
        return p.read_text(encoding="utf-8").split()
    wa, wb = load(a), load(b)
    out = []
    for op, i1, i2, j1, j2 in difflib.SequenceMatcher(a=wa, b=wb, autojunk=False).get_opcodes():
        if op == "equal":
            ctx = wa[i1:i2]
            out.append(" ".join(ctx if len(ctx) <= 12 else ctx[:6] + ["…"] + ctx[-6:]))
        if op in ("delete", "replace"):
            out.append("~~" + " ".join(wa[i1:i2]) + "~~")
        if op in ("insert", "replace"):
            out.append("**" + " ".join(wb[j1:j2]) + "**")
    return " ".join(out) + "\n"


def final(project: Path) -> Path:
    d = project / "rounds" / "final"
    d.mkdir(parents=True, exist_ok=True)
    t = (P.ROOT / "templates" / "response" / "final_checklist.md").read_text(encoding="utf-8")
    if not (d / "final_checklist.md").exists():
        (d / "final_checklist.md").write_text(t, encoding="utf-8")
    P.log_event(project, "final round opened")
    return d
