"""Command line: ``python -m pa <command> ...``. Every command accepts --project (folder or slug); without it the
nearest folder above the current directory that holds project.toml is used.

  new SLUG            create a project from templates/project
  status              stages, gates, open HITL/CITL items, next step
  gate SID            what still blocks a stage gate (exit 1 when blocked)
  mark SID STATE      todo | doing | done (done only when the gate passes)
  approve SID --by    record the person's approval of a stage (HITL gate)
  ask / task          add a HITL question for the person / a CITL task for Claude
  answer ID           close a queue item with the answer or result
  queue               list both lanes
  log TEXT            add a line to log/history.md
  refs ...            add | verify | manual | fetch | text | contexts | cards | list
  numbers ...         add | macros | fill | audit
  check FILE          mechanical manuscript check with the project's field profile
  fig check DIR       figure files: dpi, vector copy, width
  build ...           docx | latex | package
  round ...           new | split | letter | freeze | diff | final
  profiles            list the field profiles
"""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

from pa import project as P


def _proj(a) -> Path:
    return P.find_project(getattr(a, "project", None))


def cmd_new(a):
    d = P.new_project(a.slug, a.title or "", a.field, a.language, a.journal or "", Path(a.dest) if a.dest else None)
    print(f"created {d}\nnext: open Claude Code in this repository and run /pa-topic {P.slugify(a.slug)}")


def cmd_status(a):
    print(P.status(_proj(a)))


def cmd_gate(a):
    probs = P.gate(_proj(a), a.sid)
    if probs:
        print(f"{a.sid} gate blocked:\n- " + "\n- ".join(probs))
        return 1
    print(f"{a.sid} gate passes")
    return 0


def cmd_mark(a):
    P.mark(_proj(a), a.sid, a.state)
    print(f"{a.sid} -> {a.state}")


def cmd_approve(a):
    P.approve(_proj(a), a.sid, a.by, a.note or "")
    print(f"{a.sid} approved by {a.by}")


def cmd_ask(a):
    opts = [o.strip() for o in (a.options or "").split("|") if o.strip()]
    qid = P.queue_add(_proj(a), "hitl", a.stage, a.text, opts, a.recommend)
    print(qid)


def cmd_task(a):
    print(P.queue_add(_proj(a), "citl", a.stage, a.text))


def cmd_answer(a):
    P.queue_close(_proj(a), a.qid, a.text, a.by or "")
    print(f"{a.qid} closed")


def cmd_queue(a):
    p = _proj(a)
    for lane in ("hitl", "citl"):
        rows = [r for r in P.queue_rows(p, lane) if a.all or r[1] == "open"]
        print(f"## {lane.upper()} ({len(rows)})")
        for r in rows:
            print("  " + " | ".join(r[:6] if lane == "hitl" else r[:4]))


def cmd_log(a):
    P.log_event(_proj(a), a.text)


def cmd_refs(a):
    from pa import refs as R
    p = _proj(a)
    lib = R.Library(p / "02_literature")
    if a.action == "add":
        print(lib.add(doi=a.doi or "", arxiv_id=a.arxiv or "", title=a.title or "", key=a.key or ""))
    elif a.action == "verify":
        diffs = lib.verify()
        for d in diffs:
            print(f"- {d['key']} [{d['field']}]: {d['problem']}")
        print(f"{len(lib.bib)} entries, {len(diffs)} problem(s)")
        return 1 if diffs else 0
    elif a.action == "manual":
        lib.mark_manual(a.key, a.note or "")
        print(f"{a.key} marked verified by hand")
    elif a.action == "fetch":
        for k, s in lib.fetch(a.key or "").items():
            print(f"- {k}: {s}")
    elif a.action == "text":
        for k, s in lib.extract().items():
            print(f"- {k}: {s}")
    elif a.action == "contexts":
        m = Path(a.manuscript) if a.manuscript else p / "07_manuscript" / "manuscript.md"
        found = lib.contexts(m)
        never = [k for k, v in found.items() if not v]
        print(f"{sum(len(v) for v in found.values())} citing sentences; never cited: {', '.join(never) or 'none'}")
    elif a.action == "cards":
        made = lib.cards(overwrite=a.overwrite)
        print(f"{len(made)} card(s) written to 02_literature/cards/")
    elif a.action == "list":
        for k, f in lib.bib.items():
            it = lib.index["items"].get(k, {})
            print(f"- {k}: {f.get('title', '')[:70]} | verified={it.get('verified')} ({it.get('verified_by', '-')}) | {it.get('status', '-')}")


def cmd_numbers(a):
    from pa import numbers as N
    p = _proj(a)
    ledger = p / "05_data" / "numbers.csv"
    if a.action == "add":
        N.add(ledger, a.key, a.value, a.unit or "", a.source or "", a.note or "")
        print(f"{a.key} = {a.value}")
    elif a.action == "macros":
        out = p / "07_manuscript" / "numbers.tex"
        out.write_text(N.macros(N.load(ledger)), encoding="utf-8")
        print(f"wrote {out}")
    elif a.action == "fill":
        m = Path(a.manuscript) if a.manuscript else p / "07_manuscript" / "manuscript.md"
        text, missing = N.fill(m.read_text(encoding="utf-8"), N.load(ledger))
        sys.stdout.write(text)
        if missing:
            print(f"\nmissing keys: {', '.join(sorted(set(missing)))}", file=sys.stderr)
            return 1
    elif a.action == "audit":
        m = Path(a.manuscript) if a.manuscript else p / "07_manuscript" / "manuscript.md"
        res = N.audit(m.read_text(encoding="utf-8"), N.load(ledger))
        rep = N.report(res, m.name)
        out = p / "08_review" / "numbers_audit.md"
        out.parent.mkdir(exist_ok=True)
        out.write_text(rep, encoding="utf-8")
        print(f"wrote {out}: {len(res['untraced'])} untraced number(s), {len(res['unused'])} unused key(s)")


def cmd_check(a):
    from pa import check as C
    prof = a.profile
    mw, md = a.max_words, a.max_displays
    try:
        p = _proj(a)
        cfg = P.load_config(p)
        prof = C.project_profile(cfg, prof)
        j = cfg.get("journal", {})
        mw = mw or (j.get("max_words") or None)
        md = md or (j.get("max_displays") or None)
    except SystemExit:
        prof = prof or "engineering"
    return C.run(Path(a.path), prof, mw, md, Path(a.out) if a.out else None)


def cmd_fig(a):
    from pa import figures as F
    probs = F.check(Path(a.folder), a.min_dpi, a.width_in)
    print("\n".join(f"- {x}" for x in probs) or "figures pass")
    return 1 if probs else 0


def cmd_build(a):
    from pa import build as B
    p = _proj(a)
    if a.action == "docx":
        out = B.build_docx(p, a.blind, Path(a.reference_doc) if a.reference_doc else None, Path(a.csl) if a.csl else None,
                           force_builtin=a.builtin)
        print(f"wrote {out}")
        if a.pdf:
            pdf = B.docx_to_pdf(out)
            print(f"wrote {pdf}" if pdf else "soffice not found; no PDF")
    elif a.action == "latex":
        print(f"wrote {B.build_latex(p / '07_manuscript' / 'tex', a.main, a.clean_copy)}")
    elif a.action == "package":
        res = B.build_package(p / "07_manuscript" / "tex", p / "submission", a.main)
        print(json.dumps(res, indent=1))


def cmd_round(a):
    from pa import rounds as Rd
    p = _proj(a)
    if a.action == "new":
        print(f"opened {Rd.new_round(p)}\nnext: paste the decision letter into comments.md, then `python -m pa round split`")
    elif a.action == "split":
        print(f"{Rd.split(p)} comment(s) added to responses.toml")
    elif a.action == "letter":
        res = Rd.letter(p)
        print(f"letter in {res['folder']}: {res['items']} item(s), {res['own']} own change(s)")
        for x in res["problems"]:
            print(f"- {x}")
        return 1 if res["problems"] else 0
    elif a.action == "freeze":
        print(f"frozen {Rd.freeze(p, a.label)}")
    elif a.action == "diff":
        out = p / "08_review" / f"diff_{a.a}_{a.b}.md"
        out.parent.mkdir(exist_ok=True)
        out.write_text(Rd.diff(p, a.a, a.b), encoding="utf-8")
        print(f"wrote {out}")
    elif a.action == "final":
        print(f"opened {Rd.final(p)}")


def cmd_profiles(a):
    from pa import check as C
    for f in sorted(C.PROFILES.glob("*.toml")):
        print(f"- {f.stem}: {C.load_profile(f.stem).get('description', '')}")


def parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(prog="python -m pa", description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--project", help="project folder or slug (default: nearest project.toml above the current directory)")
    sub = ap.add_subparsers(dest="cmd", required=True)

    def sp(name, fn, help_):
        s = sub.add_parser(name, help=help_)
        s.add_argument("--project", default=argparse.SUPPRESS, help=argparse.SUPPRESS)
        s.set_defaults(fn=fn)
        return s

    s = sp("new", cmd_new, "create a project")
    s.add_argument("slug")
    s.add_argument("--title")
    s.add_argument("--field", default="engineering", help="field profile (python -m pa profiles)")
    s.add_argument("--language", default="en", choices=["en", "ko"])
    s.add_argument("--journal")
    s.add_argument("--dest", help="folder to create (default: $PA_PROJECTS/<slug> or ./projects/<slug>)")
    sp("status", cmd_status, "stages and queues")
    s = sp("gate", cmd_gate, "check a stage gate")
    s.add_argument("sid")
    s = sp("mark", cmd_mark, "set a stage state")
    s.add_argument("sid")
    s.add_argument("state")
    s = sp("approve", cmd_approve, "record the person's approval of a stage")
    s.add_argument("sid")
    s.add_argument("--by", required=True)
    s.add_argument("--note")
    s = sp("ask", cmd_ask, "HITL: a question for the person")
    s.add_argument("text")
    s.add_argument("--stage", default="-")
    s.add_argument("--options", help="'A | B | C'")
    s.add_argument("--recommend", type=int, help="index of the recommended option (0 = first)")
    s = sp("task", cmd_task, "CITL: a task Claude can do without the person")
    s.add_argument("text")
    s.add_argument("--stage", default="-")
    s = sp("answer", cmd_answer, "close a queue item")
    s.add_argument("qid")
    s.add_argument("text")
    s.add_argument("--by")
    s = sp("queue", cmd_queue, "list the HITL and CITL queues")
    s.add_argument("--all", action="store_true")
    s = sp("log", cmd_log, "add a line to the history")
    s.add_argument("text")
    s = sp("refs", cmd_refs, "literature")
    s.add_argument("action", choices=["add", "verify", "manual", "fetch", "text", "contexts", "cards", "list"])
    s.add_argument("--doi")
    s.add_argument("--arxiv")
    s.add_argument("--title")
    s.add_argument("--key")
    s.add_argument("--note")
    s.add_argument("--manuscript")
    s.add_argument("--overwrite", action="store_true")
    s = sp("numbers", cmd_numbers, "numbers ledger")
    s.add_argument("action", choices=["add", "macros", "fill", "audit"])
    s.add_argument("key", nargs="?")
    s.add_argument("value", nargs="?")
    s.add_argument("--unit")
    s.add_argument("--source")
    s.add_argument("--note")
    s.add_argument("--manuscript")
    s = sp("check", cmd_check, "mechanical manuscript check")
    s.add_argument("path")
    s.add_argument("--profile")
    s.add_argument("--max-words", type=int)
    s.add_argument("--max-displays", type=int)
    s.add_argument("--out")
    s = sp("fig", cmd_fig, "figure checks")
    s.add_argument("action", choices=["check"])
    s.add_argument("folder")
    s.add_argument("--min-dpi", type=int, default=300)
    s.add_argument("--width-in", type=float)
    s = sp("build", cmd_build, "assemble the manuscript")
    s.add_argument("action", choices=["docx", "latex", "package"])
    s.add_argument("--blind", action="store_true")
    s.add_argument("--reference-doc")
    s.add_argument("--csl")
    s.add_argument("--builtin", action="store_true", help="use the built-in DOCX writer even when pandoc exists")
    s.add_argument("--pdf", action="store_true", help="also convert the DOCX to PDF with LibreOffice")
    s.add_argument("--main", default="main.tex")
    s.add_argument("--clean-copy", action="store_true")
    s = sp("round", cmd_round, "review rounds")
    s.add_argument("action", choices=["new", "split", "letter", "freeze", "diff", "final"])
    s.add_argument("a", nargs="?", help="diff: first snapshot (e.g. round0_submitted)")
    s.add_argument("b", nargs="?", default="current", help="diff: second snapshot (default: current)")
    s.add_argument("--label", help="freeze: snapshot folder name")
    sp("profiles", cmd_profiles, "list field profiles")
    return ap


def main(argv=None) -> int:
    try:
        sys.stdout.reconfigure(encoding="utf-8")
    except Exception:
        pass
    a = parser().parse_args(argv)
    if a.cmd == "numbers" and a.action == "add" and (not a.key or a.value is None):
        raise SystemExit("usage: numbers add KEY VALUE [--unit U] --source FILE")
    return a.fn(a) or 0
