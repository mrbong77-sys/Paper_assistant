"""Assembly: Markdown -> DOCX, LaTeX -> PDF (marked and clean copies), and the submission package.

    python -m pa build docx  [--project P] [--blind] [--reference-doc T.docx] [--csl style.csl]
    python -m pa build latex [--project P] [--main main.tex] [--clean-copy]
    python -m pa build package [--project P] [--main main.tex]

DOCX: ``07_manuscript/manuscript.md`` -> ``{{num:key}}`` filled from the numbers ledger -> pandoc (citations from
02_literature/refs.bib through --citeproc). Without pandoc a small built-in writer produces headings, paragraphs,
bold/italic and pipe tables (no citations, no images) so a draft can still be read in Word.
--blind removes everything between ``<!-- identifying -->`` and ``<!-- /identifying -->`` (authors, affiliations,
acknowledgements, self-identifying links) for double-blind review.

LaTeX: pdflatex + bibtex (or biber) until cross-references settle; the build fails on a LaTeX error, an undefined
reference or citation, or a pending rerun. With templates/latex/revmarks.sty, ``--clean-copy`` builds the copy
without revision colours.

package: collects only the files main.tex uses into ``submission/latex_source.zip``, unpacks it into an empty
directory and builds it there, so the journal receives a source that is known to compile (PK-05).
"""
from __future__ import annotations

import re
import shutil
import subprocess
import tempfile
import zipfile
from pathlib import Path
from xml.sax.saxutils import escape

from pa import numbers as N

BLIND = re.compile(r"<!--\s*identifying\s*-->.*?<!--\s*/identifying\s*-->", re.S)


def prepare_markdown(project: Path, blind: bool = False) -> tuple[str, list[str]]:
    text = (project / "07_manuscript" / "manuscript.md").read_text(encoding="utf-8")
    ledger = project / "05_data" / "numbers.csv"
    rows = N.load(ledger) if ledger.exists() else {}
    text, missing = N.fill(text, rows)
    if blind:
        text = BLIND.sub("", text)
    return text, missing


def build_docx(project: Path, blind: bool = False, reference_doc: Path | None = None, csl: Path | None = None,
               out: Path | None = None, force_builtin: bool = False) -> Path:
    text, missing = prepare_markdown(project, blind)
    if missing:
        raise SystemExit(f"numbers missing from 05_data/numbers.csv: {', '.join(sorted(set(missing)))}")
    build = project / "07_manuscript" / "build"
    build.mkdir(parents=True, exist_ok=True)
    out = out or build / ("manuscript_blind.docx" if blind else "manuscript.docx")
    src = build / ("_filled_blind.md" if blind else "_filled.md")
    src.write_text(text, encoding="utf-8")
    if shutil.which("pandoc") and not force_builtin:
        cmd = ["pandoc", str(src), "-o", str(out), "--resource-path", str(project / "07_manuscript") + ":" + str(project)]
        bib = project / "02_literature" / "refs.bib"
        if bib.exists() and bib.read_text(encoding="utf-8").strip():
            cmd += ["--citeproc", "--bibliography", str(bib)]
            if csl:
                cmd += ["--csl", str(csl)]
        ref = reference_doc or project / "07_manuscript" / "template.docx"
        if ref and Path(ref).exists():
            cmd += ["--reference-doc", str(ref)]
        r = subprocess.run(cmd, capture_output=True, encoding="utf-8", errors="replace")
        if r.returncode != 0:
            raise SystemExit("pandoc failed:\n" + r.stderr[-3000:])
        warn = [l for l in r.stderr.splitlines() if "citeproc" in l.lower() or "not found" in l.lower()]
        if warn:
            print("pandoc warnings:\n" + "\n".join(warn[:20]))
    else:
        write_docx_builtin(text, out)
    return out


# ------------------------------------------------------------------ small DOCX writer (no dependencies)

def _runs(text: str) -> str:
    parts = re.split(r"(\*\*[^*]+\*\*|\*[^*]+\*|`[^`]+`)", text)
    out = []
    for p in parts:
        if not p:
            continue
        rpr = ""
        if p.startswith("**") and p.endswith("**"):
            p, rpr = p[2:-2], "<w:rPr><w:b/></w:rPr>"
        elif p.startswith("*") and p.endswith("*"):
            p, rpr = p[1:-1], "<w:rPr><w:i/></w:rPr>"
        elif p.startswith("`") and p.endswith("`"):
            p, rpr = p[1:-1], '<w:rPr><w:rFonts w:ascii="Consolas" w:hAnsi="Consolas"/></w:rPr>'
        out.append(f'<w:r>{rpr}<w:t xml:space="preserve">{escape(p)}</w:t></w:r>')
    return "".join(out)


def _para(text: str, style: str | None = None) -> str:
    ppr = f'<w:pPr><w:pStyle w:val="{style}"/></w:pPr>' if style else ""
    return f"<w:p>{ppr}{_runs(text)}</w:p>"


def _table(rows: list[list[str]]) -> str:
    cells = []
    for i, r in enumerate(rows):
        tc = "".join(f'<w:tc><w:tcPr><w:tcW w:w="0" w:type="auto"/></w:tcPr>{_para(("**" + c + "**") if i == 0 and c else c)}</w:tc>' for c in r)
        cells.append(f"<w:tr>{tc}</w:tr>")
    borders = "".join(f'<w:{b} w:val="single" w:sz="4" w:space="0" w:color="000000"/>' for b in ("top", "bottom", "insideH"))
    return (f'<w:tbl><w:tblPr><w:tblW w:w="0" w:type="auto"/><w:tblBorders>{borders}</w:tblBorders></w:tblPr>'
            + "".join(cells) + "</w:tbl>")


def write_docx_builtin(md: str, out: Path) -> Path:
    body, table = [], []
    for line in md.splitlines() + [""]:
        s = line.rstrip()
        if s.startswith("|"):
            cells = [c.strip() for c in s.strip("|").split("|")]
            if not all(re.fullmatch(r":?-{2,}:?", c) for c in cells):
                table.append(cells)
            continue
        if table:
            body.append(_table(table))
            table = []
        if not s.strip() or s.startswith(("<!--", "![")):
            continue
        m = re.match(r"^(#{1,4})\s+(.*)", s)
        if m:
            body.append(_para(m.group(2), f"Heading{len(m.group(1))}"))
        elif re.match(r"^\s*([-*]|\d+\.)\s+", s):
            body.append(_para("• " + re.sub(r"^\s*([-*]|\d+\.)\s+", "", s)))
        else:
            body.append(_para(s))
    doc = ('<?xml version="1.0" encoding="UTF-8" standalone="yes"?>'
           '<w:document xmlns:w="http://schemas.openxmlformats.org/wordprocessingml/2006/main"><w:body>'
           + "".join(body) + '<w:sectPr><w:pgSz w:w="11906" w:h="16838"/>'
           '<w:pgMar w:top="1440" w:right="1440" w:bottom="1440" w:left="1440"/></w:sectPr></w:body></w:document>')
    heading = "".join(f'<w:style w:type="paragraph" w:styleId="Heading{n}"><w:name w:val="heading {n}"/><w:basedOn w:val="Normal"/>'
                      f'<w:pPr><w:keepNext/><w:spacing w:before="240" w:after="120"/><w:outlineLvl w:val="{n - 1}"/></w:pPr>'
                      f'<w:rPr><w:b/><w:sz w:val="{32 - 4 * n}"/></w:rPr></w:style>' for n in range(1, 5))
    styles = ('<?xml version="1.0" encoding="UTF-8" standalone="yes"?>'
              '<w:styles xmlns:w="http://schemas.openxmlformats.org/wordprocessingml/2006/main">'
              '<w:docDefaults><w:rPrDefault><w:rPr><w:rFonts w:ascii="Times New Roman" w:hAnsi="Times New Roman" w:eastAsia="Batang"/>'
              '<w:sz w:val="22"/></w:rPr></w:rPrDefault><w:pPrDefault><w:pPr><w:spacing w:after="120" w:line="276" w:lineRule="auto"/>'
              '</w:pPr></w:pPrDefault></w:docDefaults><w:style w:type="paragraph" w:default="1" w:styleId="Normal">'
              '<w:name w:val="Normal"/></w:style>' + heading + "</w:styles>")
    ct = ('<?xml version="1.0" encoding="UTF-8" standalone="yes"?>'
          '<Types xmlns="http://schemas.openxmlformats.org/package/2006/content-types">'
          '<Default Extension="rels" ContentType="application/vnd.openxmlformats-package.relationships+xml"/>'
          '<Default Extension="xml" ContentType="application/xml"/>'
          '<Override PartName="/word/document.xml" ContentType="application/vnd.openxmlformats-officedocument.wordprocessingml.document.main+xml"/>'
          '<Override PartName="/word/styles.xml" ContentType="application/vnd.openxmlformats-officedocument.wordprocessingml.styles+xml"/>'
          "</Types>")
    rels = ('<?xml version="1.0" encoding="UTF-8" standalone="yes"?>'
            '<Relationships xmlns="http://schemas.openxmlformats.org/package/2006/relationships">'
            '<Relationship Id="rId1" Type="http://schemas.openxmlformats.org/officeDocument/2006/relationships/officeDocument" Target="word/document.xml"/>'
            "</Relationships>")
    drels = ('<?xml version="1.0" encoding="UTF-8" standalone="yes"?>'
             '<Relationships xmlns="http://schemas.openxmlformats.org/package/2006/relationships">'
             '<Relationship Id="rId1" Type="http://schemas.openxmlformats.org/officeDocument/2006/relationships/styles" Target="styles.xml"/>'
             "</Relationships>")
    out.parent.mkdir(parents=True, exist_ok=True)
    with zipfile.ZipFile(out, "w", zipfile.ZIP_DEFLATED) as z:
        z.writestr("[Content_Types].xml", ct)
        z.writestr("_rels/.rels", rels)
        z.writestr("word/document.xml", doc)
        z.writestr("word/styles.xml", styles)
        z.writestr("word/_rels/document.xml.rels", drels)
    return out


def docx_to_pdf(docx: Path) -> Path | None:
    if not shutil.which("soffice"):
        return None
    with tempfile.TemporaryDirectory() as tmp:
        subprocess.run(["soffice", "--headless", f"-env:UserInstallation=file://{Path(tmp) / 'profile'}",
                        "--convert-to", "pdf", "--outdir", str(docx.parent), str(docx)],
                       check=True, capture_output=True, timeout=300)
    pdf = docx.with_suffix(".pdf")
    return pdf if pdf.exists() else None


# ------------------------------------------------------------------ LaTeX

def _run(cmd: list[str], cwd: Path) -> subprocess.CompletedProcess:
    return subprocess.run(cmd, cwd=cwd, capture_output=True, encoding="utf-8", errors="replace")


def latex_problems(log: str, blg: str = "") -> list[str]:
    bad = [l for l in log.splitlines() if re.search(r"^! |undefined|Rerun to get|There were multiply", l)]
    bad += [l for l in blg.splitlines() if l.startswith(("Warning--", "I couldn't", "I was expecting", "ERROR"))]
    return bad


def build_latex(texdir: Path, main: str = "main.tex", clean_copy: bool = False) -> Path:
    if not shutil.which("pdflatex"):
        raise SystemExit("pdflatex not found (install TeX Live or MiKTeX)")
    stem = Path(main).stem
    job = f"{stem}_clean" if clean_copy else stem
    pdf = ["pdflatex", "-interaction=nonstopmode", "-halt-on-error"]
    arg = [f"-jobname={job}", r"\def\cleancopy{}\input{" + stem + "}"] if clean_copy else [main]
    r = _run(pdf + arg, texdir)
    if r.returncode != 0:
        raise SystemExit(f"pdflatex failed:\n{r.stdout[-3000:]}")
    aux = (texdir / f"{job}.aux").read_text(encoding="utf-8", errors="replace") if (texdir / f"{job}.aux").exists() else ""
    if "\\abx@aux" in aux or (texdir / f"{job}.bcf").exists():
        _run(["biber", job], texdir)
    elif "\\bibdata" in aux:
        _run(["bibtex", job], texdir)
    log = ""
    for _ in range(4):
        r = _run(pdf + arg, texdir)
        log = (texdir / f"{job}.log").read_text(encoding="utf-8", errors="replace")
        if "Rerun to get" not in log and "Please rerun" not in log:
            break
    blg = (texdir / f"{job}.blg").read_text(encoding="utf-8", errors="replace") if (texdir / f"{job}.blg").exists() else ""
    bad = latex_problems(log, blg)
    if bad or not (texdir / f"{job}.pdf").exists():
        raise SystemExit(f"{job}: build problems:\n" + "\n".join(bad))
    return texdir / f"{job}.pdf"


def used_files(texdir: Path, main: str = "main.tex") -> list[str]:
    """main.tex and every file it pulls in (\\input, \\include, \\includegraphics, \\bibliography, local .sty/.cls/.bst)."""
    seen, todo = [], [main]
    while todo:
        f = todo.pop()
        p = texdir / f
        if not p.suffix and (texdir / (f + ".tex")).exists():
            f, p = f + ".tex", texdir / (f + ".tex")
        if f in seen or not p.exists():
            continue
        seen.append(f)
        if p.suffix != ".tex":
            continue
        t = re.sub(r"(?<!\\)%.*", "", p.read_text(encoding="utf-8", errors="replace"))
        for m in re.findall(r"\\(?:input|include|subfile)\{([^}]+)\}", t):
            todo.append(m)
        for m in re.findall(r"\\includegraphics(?:\[[^\]]*\])?\{([^}]+)\}", t):
            cands = [m] if Path(m).suffix else [m + e for e in (".pdf", ".png", ".jpg", ".eps")]
            todo += [c for c in cands if (texdir / c).exists()][:1]
        for grp in re.findall(r"\\(?:bibliography|addbibresource)\{([^}]+)\}", t):
            for b in grp.split(","):
                b = b.strip()
                todo.append(b if b.endswith(".bib") else b + ".bib")
        for grp in re.findall(r"\\(?:usepackage|RequirePackage|documentclass)(?:\[[^\]]*\])?\{([^}]+)\}", t):
            for s in grp.split(","):
                for ext in (".sty", ".cls"):
                    if (texdir / (s.strip() + ext)).exists():
                        todo.append(s.strip() + ext)
        for b in re.findall(r"\\bibliographystyle\{([^}]+)\}", t):
            if (texdir / (b + ".bst")).exists():
                todo.append(b + ".bst")
    return sorted(seen)


def build_package(texdir: Path, out: Path, main: str = "main.tex", readme: str = "") -> dict:
    out.mkdir(parents=True, exist_ok=True)
    files = used_files(texdir, main)
    zpath = out / "latex_source.zip"
    with zipfile.ZipFile(zpath, "w", zipfile.ZIP_DEFLATED) as z:
        for f in files:
            info = zipfile.ZipInfo(f, date_time=(2020, 1, 1, 0, 0, 0))
            info.compress_type = zipfile.ZIP_DEFLATED
            info.external_attr = 0o644 << 16
            z.writestr(info, (texdir / f).read_bytes())
        if readme:
            z.writestr("README.txt", readme)
    result = {"zip": str(zpath), "files": files, "built": False}
    if shutil.which("pdflatex"):
        with tempfile.TemporaryDirectory() as tmp:
            d = Path(tmp)
            with zipfile.ZipFile(zpath) as z:
                z.extractall(d)
            pdf = build_latex(d, main)
            shutil.copy(pdf, out / pdf.name)
            if (d / "revmarks.sty").exists():
                pdf2 = build_latex(d, main, clean_copy=True)
                shutil.copy(pdf2, out / pdf2.name)
            result["built"] = True
            if shutil.which("pdftoppm"):
                (out / "render").mkdir(exist_ok=True)
                subprocess.run(["pdftoppm", "-r", "60", "-png", str(out / pdf.name), str(out / "render" / "page")], check=False)
    return result
