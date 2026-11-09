"""Literature: bibliographic records, open-access full texts, extracted text, citation contexts and reference cards.

Files (in ``02_literature/``):
  refs.bib              the bibliography (BibTeX), one entry per key
  index.json            per key: metadata, where the record was checked, open-access location, file paths, status
  papers/               downloaded PDFs (git-ignored: copyrighted works)
  text/                 extracted text (git-ignored unless the project repository is private)
  citation_contexts.json  every sentence of the manuscript that cites each key
  cards/<key>.md        reference card: record check, what the work did, usable facts with pages, verdict per citation

Rules enforced in code:
  - Only open-access copies are downloaded (Unpaywall's OA location or arXiv). Paywalls are never bypassed; a work
    without an open copy is marked "no open copy" and a person obtains it through a library.
  - A record counts as verified only after it was compared with a primary record (Crossref, arXiv, or a person's
    manual check with --manual and a note saying where).
Network calls go through ``_get`` so tests can replace it.
"""
from __future__ import annotations

import datetime as _dt
import json
import os
import re
import shutil
import subprocess
import urllib.parse
import urllib.request
import xml.etree.ElementTree as ET
from pathlib import Path

UA = "paper-assistant/0.1 (+https://github.com/mrbong77-sys/Paper_assistant)"


def _ua() -> str:
    mail = os.environ.get("PA_EMAIL", "").strip()
    return UA[:-1] + (f"; mailto:{mail})" if mail else ")")


def _get(url: str, binary: bool = False, timeout: int = 30):
    req = urllib.request.Request(url, headers={"User-Agent": _ua()})
    with urllib.request.urlopen(req, timeout=timeout) as r:
        data = r.read()
    return data if binary else data.decode("utf-8", errors="replace")


# ------------------------------------------------------------------ BibTeX

def parse_bib(text: str) -> dict[str, dict]:
    """A small BibTeX reader: @type{key, field = {value} | "value" | number, ...}. Nested braces are kept."""
    out: dict[str, dict] = {}
    i = 0
    while True:
        m = re.compile(r"@(\w+)\s*\{\s*([^,\s]+)\s*,").search(text, i)
        if not m:
            break
        typ, key = m.group(1).lower(), m.group(2)
        j, depth = m.end(), 1
        while j < len(text) and depth:
            depth += {"{": 1, "}": -1}.get(text[j], 0)
            j += 1
        body = text[m.end():j - 1]
        fields = {"ENTRYTYPE": typ}
        k = 0
        while True:
            fm = re.compile(r"\s*(\w[\w-]*)\s*=\s*").match(body, k)
            if not fm:
                break
            name, k = fm.group(1).lower(), fm.end()
            if k < len(body) and body[k] == "{":
                d, s = 1, k + 1
                k += 1
                while k < len(body) and d:
                    d += {"{": 1, "}": -1}.get(body[k], 0)
                    k += 1
                val = body[s:k - 1]
            elif k < len(body) and body[k] == '"':
                e = body.index('"', k + 1)
                val, k = body[k + 1:e], e + 1
            else:
                vm = re.compile(r"[^,]+").match(body, k)
                val, k = (vm.group(0).strip(), vm.end()) if vm else ("", k)
            fields[name] = re.sub(r"\s+", " ", val).strip()
            cm = re.compile(r"\s*,").match(body, k)
            k = cm.end() if cm else k
        if typ not in ("comment", "string", "preamble"):
            out[key] = fields
        i = j
    return out


def format_bib(key: str, f: dict) -> str:
    order = ["author", "title", "journal", "booktitle", "publisher", "year", "volume", "number", "pages", "doi",
             "eprint", "archiveprefix", "url", "note"]
    names = [n for n in order if f.get(n)] + sorted(n for n in f if n not in order and n != "ENTRYTYPE" and f[n])
    width = max((len(n) for n in names), default=0)
    lines = [f"@{f.get('ENTRYTYPE', 'article')}{{{key},"]
    lines += [f"  {n.ljust(width)} = {{{f[n]}}}," for n in names]
    return "\n".join(lines) + "\n}\n"


def write_bib(path: Path, entries: dict[str, dict]) -> None:
    path.write_text("\n".join(format_bib(k, v) for k, v in entries.items()), encoding="utf-8")


def make_key(authors: list[str], year: str, taken: set[str]) -> str:
    first = authors[0] if authors else "Anon"
    family = first.split(",")[0] if "," in first else first.split()[-1]
    sur = re.sub(r"[^A-Za-z]", "", family)
    if sur.isupper():
        sur = sur.capitalize()
    base = f"{sur or 'Anon'}{year or 'nd'}"
    key, n = base, 0
    while key in taken:
        n += 1
        key = base + "abcdefghijklmnopqrstuvwxyz"[n - 1]
    return key


# ------------------------------------------------------------------ primary records

def crossref(doi: str) -> dict:
    data = json.loads(_get("https://api.crossref.org/works/" + urllib.parse.quote(doi)))["message"]
    authors = [f"{a.get('family', '')}, {a.get('given', '')}".strip(", ") for a in data.get("author", [])]
    date = (data.get("published-print") or data.get("published-online") or data.get("issued") or {}).get("date-parts", [[None]])[0]
    typ = {"journal-article": "article", "proceedings-article": "inproceedings", "book": "book",
           "book-chapter": "incollection", "posted-content": "misc"}.get(data.get("type"), "misc")
    rec = {"ENTRYTYPE": typ, "title": (data.get("title") or [""])[0], "author": " and ".join(authors),
           "year": str(date[0] or ""), "doi": data.get("DOI", doi), "volume": data.get("volume", ""),
           "number": data.get("issue", ""), "pages": data.get("page", "").replace("-", "--"),
           "publisher": data.get("publisher", "")}
    cont = (data.get("container-title") or [""])[0]
    rec["journal" if typ == "article" else "booktitle"] = cont
    return {k: v for k, v in rec.items() if v}


def crossref_search(title: str) -> str | None:
    q = urllib.parse.urlencode({"query.bibliographic": title, "rows": 3})
    items = json.loads(_get("https://api.crossref.org/works?" + q))["message"]["items"]
    t0 = _simple(title)
    for it in items:
        if _simple((it.get("title") or [""])[0]) == t0:
            return it.get("DOI")
    return None


def arxiv(aid: str) -> dict:
    aid = re.sub(r"^(arxiv:|https?://arxiv\.org/(abs|pdf)/)", "", aid.strip(), flags=re.I).removesuffix(".pdf")
    xml = _get("http://export.arxiv.org/api/query?id_list=" + urllib.parse.quote(aid))
    ns = {"a": "http://www.w3.org/2005/Atom", "x": "http://arxiv.org/schemas/atom"}
    e = ET.fromstring(xml).find("a:entry", ns)
    if e is None or e.find("a:title", ns) is None:
        raise SystemExit(f"arXiv has no record {aid}")
    authors = []
    for a in e.findall("a:author", ns):
        parts = a.find("a:name", ns).text.strip().split()
        authors.append(f"{parts[-1]}, {' '.join(parts[:-1])}".strip(", "))
    base = re.sub(r"v\d+$", "", aid)
    rec = {"ENTRYTYPE": "misc", "title": re.sub(r"\s+", " ", e.find("a:title", ns).text).strip(),
           "author": " and ".join(authors), "year": e.find("a:published", ns).text[:4], "eprint": aid,
           "archiveprefix": "arXiv", "doi": f"10.48550/arXiv.{base}",
           "url": f"https://arxiv.org/abs/{aid}"}
    jref = e.find("x:journal_ref", ns)
    if jref is not None and jref.text:
        rec["note"] = "Published version: " + jref.text.strip() + " (cite the published version, RE-02)"
    return rec


def unpaywall(doi: str) -> str | None:
    mail = os.environ.get("PA_EMAIL", "").strip()
    if not mail:
        return None
    data = json.loads(_get(f"https://api.unpaywall.org/v2/{urllib.parse.quote(doi)}?email={urllib.parse.quote(mail)}"))
    loc = data.get("best_oa_location") or {}
    return loc.get("url_for_pdf") or None


def _simple(s: str) -> str:
    return re.sub(r"[^a-z0-9]", "", re.sub(r"[{}\\]", "", s.lower()))


# ------------------------------------------------------------------ the literature folder

class Library:
    def __init__(self, folder: Path):
        self.dir = Path(folder)
        self.bib_path = self.dir / "refs.bib"
        self.index_path = self.dir / "index.json"
        self.dir.mkdir(parents=True, exist_ok=True)
        self.bib = parse_bib(self.bib_path.read_text(encoding="utf-8")) if self.bib_path.exists() else {}
        self.index = json.loads(self.index_path.read_text(encoding="utf-8")) if self.index_path.exists() else {"items": {}}
        self.index.setdefault("items", {})
        for k in self.bib:
            self.index["items"].setdefault(k, {"verified": False})

    def save(self) -> None:
        write_bib(self.bib_path, self.bib)
        self.index_path.write_text(json.dumps(self.index, ensure_ascii=False, indent=1) + "\n", encoding="utf-8")

    def add(self, doi: str = "", arxiv_id: str = "", title: str = "", key: str = "") -> str:
        if not doi and not arxiv_id and title:
            doi = crossref_search(title) or ""
            if not doi:
                raise SystemExit(f"Crossref found no exact title match for: {title} (add the entry by hand and verify it)")
        rec = crossref(doi) if doi else arxiv(arxiv_id)
        authors = [a.strip() for a in rec.get("author", "").split(" and ") if a.strip()]
        key = key or make_key(authors, rec.get("year", ""), set(self.bib))
        self.bib[key] = rec
        self.index["items"][key] = {"verified": True, "verified_by": "crossref" if doi else "arxiv",
                                    "checked": _dt.date.today().isoformat(), "doi": rec.get("doi", ""),
                                    "arxiv": rec.get("eprint", ""), "status": "record"}
        self.save()
        return key

    def verify(self) -> list[dict]:
        """Compare each entry with its primary record (DOI -> Crossref, eprint -> arXiv). Returns the differences."""
        diffs = []
        for key, f in self.bib.items():
            item = self.index["items"].setdefault(key, {})
            try:
                if f.get("doi") and not f["doi"].lower().startswith("10.48550/"):
                    src, rec = "crossref", crossref(f["doi"])
                elif f.get("eprint") or "arxiv" in f.get("doi", "").lower():
                    src, rec = "arxiv", arxiv(f.get("eprint") or f["doi"].split("arXiv.")[-1])
                else:
                    diffs.append({"key": key, "field": "-", "problem": "no DOI or arXiv id; verify by hand (--manual)"})
                    continue
            except Exception as e:  # network or record errors are reported, not fatal
                diffs.append({"key": key, "field": "-", "problem": f"lookup failed: {e}"})
                continue
            bad = []
            if _simple(f.get("title", "")) != _simple(rec.get("title", "")):
                bad.append(("title", f.get("title", ""), rec.get("title", "")))
            if f.get("year", "") != rec.get("year", "") and src == "crossref":
                bad.append(("year", f.get("year", ""), rec.get("year", "")))
            fa = [_simple(a.split(",")[0]) for a in f.get("author", "").split(" and ") if a.strip()]
            ra = [_simple(a.split(",")[0]) for a in rec.get("author", "").split(" and ") if a.strip()]
            if fa[:1] != ra[:1] or (len(fa) != len(ra) and "others" not in f.get("author", "")):
                bad.append(("author", f"{len(fa)} authors, first {fa[:1]}", f"{len(ra)} authors, first {ra[:1]}"))
            for field, mine, theirs in bad:
                diffs.append({"key": key, "field": field, "problem": f"entry '{mine}' vs {src} '{theirs}'"})
            if "note" in rec and "Published version" in rec["note"]:
                diffs.append({"key": key, "field": "venue", "problem": rec["note"]})
            item.update({"verified": not bad, "verified_by": src, "checked": _dt.date.today().isoformat()})
        self.save()
        return diffs

    def mark_manual(self, key: str, note: str) -> None:
        if key not in self.bib:
            raise SystemExit(f"no entry {key}")
        if not note.strip():
            raise SystemExit("a manual verification needs a note saying which primary record was checked")
        self.index["items"][key].update({"verified": True, "verified_by": "manual", "checked": _dt.date.today().isoformat(),
                                         "manual_note": note})
        self.save()

    def fetch(self, only: str = "") -> dict[str, str]:
        """Download open-access PDFs only (Unpaywall OA location, else arXiv). Returns key -> status."""
        papers = self.dir / "papers"
        papers.mkdir(exist_ok=True)
        out = {}
        for key, f in self.bib.items():
            if only and key != only:
                continue
            item = self.index["items"].setdefault(key, {})
            dest = papers / f"{key}.pdf"
            if dest.exists():
                out[key] = "have"
                continue
            url = None
            if f.get("doi") and not f["doi"].lower().startswith("10.48550/"):
                try:
                    url = unpaywall(f["doi"])
                except Exception:
                    url = None
            if not url and (f.get("eprint") or "arxiv" in f.get("doi", "").lower()):
                aid = f.get("eprint") or f["doi"].split("arXiv.")[-1]
                url = f"https://arxiv.org/pdf/{aid}"
            if not url:
                item["status"] = "no open copy"
                out[key] = "no open copy (obtain it through a library and save it as papers/%s.pdf)" % key
                continue
            try:
                data = _get(url, binary=True, timeout=60)
            except Exception as e:
                out[key] = f"download failed: {e}"
                continue
            if not data.startswith(b"%PDF"):
                out[key] = "not a PDF (landing page?); obtain it by hand"
                continue
            dest.write_bytes(data)
            item.update({"status": "full text", "oa_url": url, "file": f"papers/{key}.pdf"})
            out[key] = "downloaded"
        self.save()
        return out

    def extract(self) -> dict[str, str]:
        """pdftotext -layout for every PDF in papers/ (needs poppler-utils)."""
        txt = self.dir / "text"
        txt.mkdir(exist_ok=True)
        if not shutil.which("pdftotext"):
            raise SystemExit("pdftotext not found (install poppler-utils)")
        out = {}
        for pdf in sorted((self.dir / "papers").glob("*.pdf")):
            dest = txt / f"{pdf.stem}.txt"
            subprocess.run(["pdftotext", "-layout", str(pdf), str(dest)], check=True)
            self.index["items"].setdefault(pdf.stem, {})["text"] = f"text/{pdf.stem}.txt"
            out[pdf.stem] = f"{dest.stat().st_size} bytes"
        self.save()
        return out

    # -------------------------------------------------------------- citations in the manuscript

    def contexts(self, manuscript: Path) -> dict[str, list[dict]]:
        text = manuscript.read_text(encoding="utf-8")
        found: dict[str, list[dict]] = {k: [] for k in self.bib}
        surnames = {}
        for k, f in self.bib.items():
            auth = [a.split(",")[0].strip(" {}") for a in f.get("author", "").split(" and ") if a.strip()]
            if auth:
                surnames[k] = (auth[0].split()[-1] if "," not in f.get("author", "") else auth[0], f.get("year", ""), len(auth))
        for ln, line in enumerate(text.splitlines(), 1):
            for sent in re.split(r"(?<=[.!?])\s+(?=[A-Z])", line):
                keys = set(re.findall(r"@([A-Za-z][\w:-]*)", sent))
                for grp in re.findall(r"\\cite[pt]?\*?(?:\[[^\]]*\])*\{([^}]*)\}", sent):
                    keys |= {g.strip() for g in grp.split(",")}
                for k, (sur, year, n) in surnames.items():
                    if year and re.search(rf"\b{re.escape(sur)}\b[^()]{{0,40}}?,?\s*\(?{year}", sent):
                        keys.add(k)
                for k in keys:
                    if k in found:
                        found[k].append({"line": ln, "sentence": sent.strip()[:400]})
        out = self.dir / "citation_contexts.json"
        out.write_text(json.dumps(found, ensure_ascii=False, indent=1) + "\n", encoding="utf-8")
        return found

    def cards(self, contexts: dict[str, list[dict]] | None = None, overwrite: bool = False) -> list[str]:
        cdir = self.dir / "cards"
        cdir.mkdir(exist_ok=True)
        if contexts is None and (self.dir / "citation_contexts.json").exists():
            contexts = json.loads((self.dir / "citation_contexts.json").read_text(encoding="utf-8"))
        made = []
        for k, f in self.bib.items():
            dest = cdir / f"{k}.md"
            if dest.exists() and not overwrite:
                continue
            item = self.index["items"].get(k, {})
            rows = "\n".join(f"| {c['line']} | {c['sentence'][:160].replace('|', '/')} | [TODO verdict] | [TODO quote, p. N] | |"
                             for c in (contexts or {}).get(k, [])) or "| | (not cited yet) | | | |"
            dest.write_text(CARD.format(key=k, title=f.get("title", ""), entry=format_bib(k, f).strip(),
                                        verified=item.get("verified_by", "not yet"), status=item.get("status", "record"),
                                        file=item.get("file", "(no full text)"), rows=rows), encoding="utf-8")
            made.append(k)
        return made


CARD = """# {key}: {title}

- Entry:
```bibtex
{entry}
```
- Record check: {verified} — [TODO: say which primary record was compared, and any difference]
- Full text: {file} (status: {status})

## What the work did
[TODO: 3–6 sentences in your own words: question, data, method, main result with numbers and pages. No long quotes.]

## Facts usable in the manuscript (with pages)
- [TODO fact] (p. N)

## Citations in the manuscript
Verdicts: Supported / Partly supported / Not supported / Wrong source / Usage citation (cites a tool or dataset).

| Line | Sentence in the manuscript | Verdict | Evidence from the source (short quote, page) | Suggested fix |
|---|---|---|---|---|
{rows}
"""
