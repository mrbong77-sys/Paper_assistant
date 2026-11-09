"""Tests of the pa toolkit. Everything runs in pytest's temporary directories; no network, no real manuscript."""
from __future__ import annotations

import json
import shutil
import zipfile
from pathlib import Path

import pytest

from pa import build as B
from pa import check as C
from pa import cli
from pa import figures as F
from pa import numbers as N
from pa import project as P
from pa import refs as R
from pa import rounds as Rd

ROOT = Path(__file__).resolve().parents[1]
EXAMPLE = ROOT / "examples" / "demo_project"


@pytest.fixture
def proj(tmp_path, monkeypatch):
    monkeypatch.setenv("PA_PROJECTS", str(tmp_path))
    return P.new_project("t1", "A test study", "engineering", "en", "Test Journal")


# ------------------------------------------------------------------ project, gates, lanes

def test_new_project_layout(proj):
    for f in ("project.toml", "01_topic/topic.md", "04_design/design.md", "05_data/numbers.csv", "log/state.json",
              "log/history.md", ".gitignore", "07_manuscript/manuscript.md"):
        assert (proj / f).exists(), f
    cfg = P.load_config(proj)
    assert cfg["project"]["title"] == "A test study" and cfg["journal"]["name"] == "Test Journal"
    with pytest.raises(SystemExit):
        P.new_project("t1", dest=proj)                      # never overwrites


def test_gate_blocks_on_placeholders_and_needs_approval(proj):
    probs = P.gate(proj, "S1")
    assert any("placeholder" in p for p in probs) and any("approval" in p for p in probs)
    with pytest.raises(SystemExit):
        P.approve(proj, "S1", "Ann")                         # placeholders left: approval refused
    (proj / "01_topic" / "topic.md").write_text("# topic\nRQ1: is A better than B?\n", encoding="utf-8")
    assert P.gate(proj, "S1") == ["S1 needs the person's approval: python -m pa approve S1 --by <name>"]
    with pytest.raises(SystemExit):
        P.approve(proj, "S1", " ")                           # a name is required
    P.approve(proj, "S1", "Ann", "RQ fixed")
    assert P.gate(proj, "S1") == [] and P.load_state(proj)["stages"]["S1"] == "done"
    assert "APPROVED S1" in (proj / "log" / "decisions.md").read_text(encoding="utf-8")


def test_citl_stage_cannot_be_marked_done_while_blocked(proj):
    with pytest.raises(SystemExit):
        P.mark(proj, "S5", "done")                           # empty ledger
    N.add(proj / "05_data" / "numbers.csv", "acc", "91.2", "%", "r.json:acc")
    P.mark(proj, "S5", "done")
    assert P.load_state(proj)["stages"]["S5"] == "done"


def test_queues(proj):
    h = P.queue_add(proj, "hitl", "S1", "Which journal?", ["A", "B"], 1)
    c = P.queue_add(proj, "citl", "S2", "collect refs")
    assert (h, c) == ("H-001", "C-001")
    assert P.queue_rows(proj, "hitl")[0][5] == "B"           # recommended option letter
    assert any("open HITL" in p for p in P.gate(proj, "S1"))
    P.queue_close(proj, h, "B", by="Ann")
    assert P.queue_rows(proj, "hitl")[0][1] == "closed"
    assert "H-001: B" in (proj / "log" / "decisions.md").read_text(encoding="utf-8")
    assert P.queue_add(proj, "hitl", "S1", "next?") == "H-002"


def test_status_text(proj):
    s = P.status(proj)
    assert "| S1 | topic | todo | HITL |" in s and "다음 단계: S1" in s


# ------------------------------------------------------------------ numbers ledger

def test_numbers_macros_fill_audit(tmp_path):
    led = tmp_path / "numbers.csv"
    N.add(led, "acc_main", "91.2", "%", "r.json:acc")
    N.add(led, "n_test", "1,000", "", "r.json:n")
    N.add(led, "time_v2", "3.5", "h", "log.txt")
    rows = N.load(led)
    assert N.macro_name("time_v2") == "NumTimeVtwo"
    tex = N.macros(rows)
    assert r"\newcommand{\NumAccMain}{91.2\%\xspace}" in tex and r"{3.5\,h\xspace}" in tex
    text, missing = N.fill("Accuracy was {{num:acc_main}} on {{num:n_test}} items ({{num:nope}}).", rows)
    assert text.startswith("Accuracy was 91.2% on 1,000 items") and missing == ["nope"]
    res = N.audit("Accuracy was 91.2% and recall 77.7% (Smith, 2020) in Table 12, n = {{num:n_test}}.", rows)
    assert [v for _, v in res["untraced"]] == ["77.7%"]
    assert "time_v2" in res["unused"] and "n_test" in res["used"]
    with pytest.raises(SystemExit):
        N.add(led, "1bad", "1")


# ------------------------------------------------------------------ manuscript check

TEXT = """# Title

In recent years, we utilized a novel classifier (NC) in order to classify items [ref].
The error rate (ER) fell significantly (p = 0.01), and the AUC fell significantly.
| table | row we |
This is a sentence with exactly enough words to pass the long sentence threshold of twenty five words without any doubt at all on this particular day of testing.
The behavior and the behaviour differ, e.g. cats, dogs, etc. in this example of iteration_12.
"""


def test_check_engineering():
    r = C.check(TEXT, C.load_profile("engineering"), max_words=10, max_displays=8)
    assert [t for _, t in r["first_person"]] == ["we"]                       # the table row is skipped
    ids = " ".join(i for _, i, _, _ in r["phrases"])
    assert "LA-18" in ids and "LA-05" in ids and "LA-09" in ids and "LA-21" in ids
    assert r["leftover"] == [(3, "[ref]")]
    assert r["significant"] == []                                            # the line carries p =
    assert "AUC" in [a for _, a in r["abbrev"]] and "NC" not in [a for _, a in r["abbrev"]]
    assert r["spelling"] == [("behavior", 1, "behaviour", 1)]
    assert r["internal"] and r["counts"]["over_review"] == 1
    assert "Blocking candidates" in C.report(r, "x")


def test_check_profiles_differ():
    hum = C.check(TEXT, C.load_profile("humanities"))
    assert hum["first_person"] == [] and hum["abbrev"] == [] and hum["counts"]["over_review"] == 0
    assert C.project_profile({"project": {"field": "engineering"}, "journal": {"first_person": "allow"}})["first_person"] == "allow"
    with pytest.raises(SystemExit):
        C.load_profile("nope")


def test_check_korean():
    ko = "이 연구에 있어서 결과는 측정되어졌다. 정확도가 높은 것으로 보인다. 우리는 실험을 했습니다.\n"
    r = C.check(ko, C.load_profile("korean"))
    ids = {i for _, i, _, _ in r["phrases"]}
    assert {"KO-01", "KO-03", "KO-04"} <= ids
    assert r["first_person"] and r["register"] == {"formal": 1, "plain": 2}


def test_check_latex_and_docx(tmp_path):
    tex = tmp_path / "m.tex"
    tex.write_text("\\documentclass{article}\\begin{document}\\section{Intro}We show it \\cite{x}.\n"
                   "\\begin{equation}a=b\\end{equation}\\end{document}", encoding="utf-8")
    assert "We show it" in C.read_text(tex) and "a=b" not in C.read_text(tex)
    d = tmp_path / "m.docx"
    with zipfile.ZipFile(d, "w") as z:
        z.writestr("word/document.xml", "<w:document><w:p><w:t>We show it.</w:t></w:p></w:document>")
    out = tmp_path / "r.md"
    assert C.run(d, "engineering", out=out) == 0 and "L1: We" in out.read_text(encoding="utf-8")


def test_sentence_split():
    assert len(C.sentences("Results agree with Smith et al. and Fig. 2 shows it. Next one by Z. Lin follows.")) == 2


# ------------------------------------------------------------------ literature

BIB = """@article{Smith2020,
  author = {Smith, Ann and Lee, Bo},
  title = {A {Study} of Things},
  journal = {J. Things},
  year = 2020,
  doi = {10.1234/abc},
}
@misc{Kim2024, author = "Kim, C.", title = "Preprint", year = {2024}, eprint = {2401.00001}}
"""


def test_parse_and_format_bib():
    e = R.parse_bib(BIB)
    assert set(e) == {"Smith2020", "Kim2024"} and e["Smith2020"]["title"] == "A {Study} of Things"
    assert e["Smith2020"]["year"] == "2020" and e["Kim2024"]["eprint"] == "2401.00001"
    again = R.parse_bib(R.format_bib("Smith2020", e["Smith2020"]))
    assert again["Smith2020"] == e["Smith2020"]
    assert R.make_key(["FISHER, R. A."], "1936", set()) == "Fisher1936"
    assert R.make_key(["Ann Smith"], "2020", {"Smith2020"}) == "Smith2020a"


def test_verify_contexts_cards_offline(tmp_path, monkeypatch):
    lit = tmp_path / "02_literature"
    lit.mkdir()
    (lit / "refs.bib").write_text(BIB, encoding="utf-8")
    crossref_json = json.dumps({"message": {"title": ["A Study of Things"], "author": [{"family": "Smith", "given": "Ann"},
                               {"family": "Lee", "given": "Bo"}], "issued": {"date-parts": [[2021]]}, "DOI": "10.1234/abc",
                               "type": "journal-article", "container-title": ["J. Things"]}})
    atom = ('<feed xmlns="http://www.w3.org/2005/Atom" xmlns:arxiv="http://arxiv.org/schemas/atom"><entry>'
            '<title>Preprint</title><published>2024-01-01T00:00:00Z</published><author><name>C. Kim</name></author>'
            '<arxiv:journal_ref>Proc. Things 2024</arxiv:journal_ref></entry></feed>')
    monkeypatch.setattr(R, "_get", lambda url, binary=False, timeout=30: crossref_json if "crossref" in url else atom)
    lib = R.Library(lit)
    diffs = lib.verify()
    fields = {(d["key"], d["field"]) for d in diffs}
    assert ("Smith2020", "year") in fields and ("Kim2024", "venue") in fields
    assert lib.index["items"]["Smith2020"]["verified"] is False and lib.index["items"]["Kim2024"]["verified"] is True
    lib.mark_manual("Smith2020", "publisher page checked")
    assert R.Library(lit).index["items"]["Smith2020"]["verified"] is True
    ms = tmp_path / "m.md"
    ms.write_text("Things vary [@Smith2020].\nKim (2024) disagreed. Also \\cite{Kim2024, Smith2020}.\n", encoding="utf-8")
    found = lib.contexts(ms)
    assert [c["line"] for c in found["Smith2020"]] == [1, 2] and [c["line"] for c in found["Kim2024"]] == [2, 2]
    assert lib.cards() == ["Smith2020", "Kim2024"]
    assert "Things vary" in (lit / "cards" / "Smith2020.md").read_text(encoding="utf-8")
    assert lib.cards() == []                                     # existing cards are kept


def test_fetch_takes_only_open_copies(tmp_path, monkeypatch):
    lit = tmp_path / "02_literature"
    lit.mkdir()
    (lit / "refs.bib").write_text(BIB, encoding="utf-8")
    monkeypatch.delenv("PA_EMAIL", raising=False)
    monkeypatch.setattr(R, "_get", lambda url, binary=False, timeout=60: b"%PDF-1.4 x" if "arxiv.org/pdf" in url else b"<html>")
    st = R.Library(lit).fetch()
    assert st["Smith2020"].startswith("no open copy") and st["Kim2024"] == "downloaded"
    assert (lit / "papers" / "Kim2024.pdf").exists() and not (lit / "papers" / "Smith2020.pdf").exists()


# ------------------------------------------------------------------ figures and build

def test_png_info_and_check(tmp_path):
    F.tiny_png(tmp_path / "a.png", 1200, 600, 600)
    F.tiny_png(tmp_path / "b.png", 600, 300, 150)
    (tmp_path / "a.pdf").write_bytes(b"%PDF")
    assert F.png_info(tmp_path / "a.png") == {"dpi": 600, "width": 1200, "height": 600}
    probs = F.check(tmp_path, 300, width_in=2.5)
    assert any("b.png: 150 dpi" in p for p in probs) and any("b.png: no vector" in p for p in probs)
    assert not any(p.startswith("a.png") for p in probs)


def test_builtin_docx_and_blind(proj):
    m = proj / "07_manuscript" / "manuscript.md"
    m.write_text("# Intro\n\n<!-- identifying -->\nBy Ann Lee.\n<!-- /identifying -->\n\nAccuracy was {{num:acc}}.\n\n"
                 "| a | b |\n|---|---|\n| 1 | **2** |\n", encoding="utf-8")
    with pytest.raises(SystemExit):
        B.build_docx(proj, force_builtin=True)                   # missing ledger key
    N.add(proj / "05_data" / "numbers.csv", "acc", "91.2", "%", "r.json")
    out = B.build_docx(proj, blind=True, force_builtin=True)
    xml = zipfile.ZipFile(out).read("word/document.xml").decode()
    assert "91.2%" in xml and "Ann Lee" not in xml and "<w:tbl>" in xml and "Heading1" in xml


@pytest.mark.skipif(shutil.which("pandoc") is None, reason="pandoc not installed")
def test_pandoc_docx(proj):
    (proj / "07_manuscript" / "manuscript.md").write_text("# Intro\n\nText.\n", encoding="utf-8")
    out = B.build_docx(proj)
    assert zipfile.is_zipfile(out)


def test_used_files_and_package_zip(tmp_path):
    t = tmp_path / "tex"
    (t / "sections").mkdir(parents=True)
    (t / "fig").mkdir()
    (t / "main.tex").write_text("\\documentclass{myclass}\\usepackage{revmarks}\\input{sections/a}"
                                "\\bibliographystyle{plain}\\bibliography{refs}", encoding="utf-8")
    (t / "sections" / "a.tex").write_text("\\includegraphics[width=1in]{fig/f1}% \\input{sections/unused}", encoding="utf-8")
    for f in ("myclass.cls", "revmarks.sty", "refs.bib", "fig/f1.pdf", "sections/unused.tex", "notes.txt"):
        (t / f).write_text("x", encoding="utf-8")
    assert B.used_files(t) == ["fig/f1.pdf", "main.tex", "myclass.cls", "refs.bib", "revmarks.sty", "sections/a.tex"]
    assert B.latex_problems("! Undefined control sequence.\nLaTeX Warning: Reference `x' undefined") != []
    if shutil.which("pdflatex") is None:
        res = B.build_package(t, tmp_path / "out")
        assert res["built"] is False and len(zipfile.ZipFile(res["zip"]).namelist()) == 6


# ------------------------------------------------------------------ rounds

COMMENTS = """# Round 1: comments as received

- received: today

## Editor

1. Shorten the abstract.

## Reviewer 1

1. Add a baseline.
   It should use the same split.

2. Fix Table 2.

## Reviewer 2

Report standard deviations.
"""


def test_split_comments():
    items = Rd.split_comments(COMMENTS)
    assert [i["id"] for i in items] == ["E.1", "R1.1", "R1.2", "R2.1"]
    assert items[1]["comment"] == "Add a baseline. It should use the same split."


def test_round_cycle(proj):
    (proj / "07_manuscript" / "manuscript.md").write_text("Old text here.\n", encoding="utf-8")
    d = Rd.new_round(proj)
    assert (proj / "rounds" / "round0_submitted" / "manuscript.md").exists() and d.name == "round1"
    with pytest.raises(SystemExit):
        Rd.freeze(proj, "round0_submitted")                      # frozen snapshots are never overwritten
    (d / "comments.md").write_text(COMMENTS, encoding="utf-8")
    assert Rd.split(proj) == 4 and Rd.split(proj) == 0
    res = Rd.letter(proj)
    assert len(res["problems"]) == 4 and all("no response" in p for p in res["problems"])
    t = (d / "responses.toml").read_text(encoding="utf-8")
    t = t.replace('response = ""', 'response = "Done as asked; the new text is in place."', 1)
    t = t.replace('status = "pending"', 'status = "done"', 1)
    (d / "responses.toml").write_text(t, encoding="utf-8")
    res = Rd.letter(proj)
    assert "E.1: says the paper changed but gives no location (RV-02)" in res["problems"]
    for ext in ("md", "tex", "docx"):
        assert (d / "letter" / f"response_letter.{ext}").exists()
    (proj / "07_manuscript" / "manuscript.md").write_text("New text here.\n", encoding="utf-8")
    assert "~~Old~~ **New**" in Rd.diff(proj, "round0_submitted", "current")


def test_letter_problem_rules():
    data = {"letter": {}, "own": [{"id": "O1", "change": "x"}], "item": [
        {"id": "R1.1", "response": "No.", "status": "declined"},
        {"id": "R1.2", "response": "We believe this is clearly fine.", "status": "done", "change": "§2"},
        {"id": "R1.2", "response": "ok", "status": "maybe", "change": "§3"}]}
    p = Rd.problems(data)
    assert any("duplicate" in x for x in p) and any("RV-03" in x for x in p) and any("RV-04" in x for x in p)
    assert any("unknown status" in x for x in p) and any("in_paper" in x for x in p)


# ------------------------------------------------------------------ CLI and the worked example

def test_cli_end_to_end(tmp_path, monkeypatch, capsys):
    monkeypatch.setenv("PA_PROJECTS", str(tmp_path))
    assert cli.main(["new", "demo", "--title", "T", "--field", "korean", "--language", "ko"]) == 0
    assert cli.main(["--project", "demo", "ask", "Q?", "--stage", "S1", "--options", "A | B", "--recommend", "0"]) == 0
    assert cli.main(["--project", "demo", "numbers", "add", "acc", "91.2", "--unit", "%", "--source", "r.json"]) == 0
    assert cli.main(["--project", "demo", "gate", "S5"]) == 0
    assert cli.main(["--project", "demo", "gate", "S1"]) == 1
    assert cli.main(["profiles"]) == 0
    out = capsys.readouterr().out
    assert "H-001" in out and "korean" in out


def test_example_project_is_consistent(tmp_path):
    ex = tmp_path / "demo_project"
    shutil.copytree(EXAMPLE, ex)
    rows = N.load(ex / "05_data" / "numbers.csv")
    assert all(r.source for r in rows.values())
    text = (ex / "07_manuscript" / "manuscript.md").read_text(encoding="utf-8")
    _, missing = N.fill(text, rows)
    assert missing == []
    for sid in ("S1", "S2", "S3", "S4", "S5", "S6", "S7", "S8", "S9"):
        assert P.gate(ex, sid) == [], sid
    res = C.check(text, C.project_profile(P.load_config(ex)))
    assert res["leftover"] == [] and res["first_person"] == [] and res["counts"]["over_cap"] == 0
    letter = Rd.letter(ex, 1)
    assert letter["problems"] == []
    # the example's result file is reproducible from its script
    import runpy
    import sys
    out = tmp_path / "r.json"
    sys_argv = sys.argv
    try:
        sys.argv = ["run_benchmark.py", "--out", str(out)]
        with pytest.raises(SystemExit) as e:
            runpy.run_path(str(ex / "05_data" / "scripts" / "run_benchmark.py"), run_name="__main__")
        assert e.value.code == 0
    finally:
        sys.argv = sys_argv
    assert json.loads(out.read_text()) == json.loads((ex / "05_data" / "processed" / "results.json").read_text())
