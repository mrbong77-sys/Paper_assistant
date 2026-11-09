"""Mechanical manuscript checks keyed to the rule IDs of docs/style/core_rules.md (LA = language, KO = Korean
prose, HR = house rules). Step 5 of docs/review_procedure.md. It flags candidates only; the reviewer judges each one.

    python -m pa check MANUSCRIPT [--profile engineering] [--max-words N] [--max-displays N] [--out report.md]

Reads .md, .txt, .tex or .docx (the text of word/document.xml; no extra package). The field profile
(pa/profiles/<name>.toml) sets the thresholds and which rules apply: for example the humanities profile allows the
first person, and the korean profile counts sentence length in characters and adds translationese patterns.
"""
from __future__ import annotations

import re
import sys
import tomllib
import zipfile
from pathlib import Path

PROFILES = Path(__file__).resolve().parent / "profiles"

# phrase (regex, case-insensitive) -> (rule IDs, hint). English prose.
PHRASES_EN = [
    (r"\bin recent years\b|\brecent advances in\b|\bnowadays\b", "LA-18", "stock opening; start with the problem"),
    (r"\bhas (attracted|received|gained) (increasing|growing|considerable|much) attention\b", "LA-18", "stock opening"),
    (r"\blittle is known\b", "ST-04", "say exactly what is unknown"),
    (r"\bit is (important|worth|interesting) to note that\b|\bit should be noted that\b", "LA-06", "delete or use 'Note that'"),
    (r"\bin order to\b", "LA-05", "use 'to'"),
    (r"\bdue to the fact that\b", "LA-05", "use 'because'"),
    (r"\ba (large|great|small) number of\b", "LA-05", "give the number or use 'many/few'"),
    (r"\bhas the ability to\b|\bis able to\b", "LA-05", "use 'can'"),
    (r"\bas (can be|is) seen (in|from)\b|\bas illustrated in\b|\bas shown in (Table|Figure|Fig)", "LA-24",
     "make the finding the subject, reference in brackets"),
    (r"\butili[sz]e[sd]?\b|\butili[sz]ation\b", "LA-05", "use 'use'"),
    (r"\b(perform|conduct|carr(y|ied) out)(ed|s)? (an?|the) \w+(ion|sis|ment)\b", "LA-04", "use the verb"),
    (r"\bnovel\b|\binnovative\b|\bgroundbreaking\b", "LA-09", "replace with the specific property"),
    (r"\bto the best of (our|the authors') knowledge\b", "LA-09", "unsupported claim; cite the search instead"),
    (r"\bthe (paper|rest of (the|this) paper) is (structured|organi[sz]ed) as follows\b", "SE-05", "one short sentence per section, or delete"),
    (r"\bthis paper has (described|presented)\b", "LA-19", "do not open Conclusions this way"),
    (r"\bmay (provide|offer) (new )?insights?\b", "LA-19", "say what the insight is"),
    (r"\bmore research is needed\b|\bfurther research is (needed|required)\b", "LA-19", "name the next study, not as the last sentence"),
    (r"\b(failed to|ignored|overlooked)\b", "LA-20", "check the tone when describing other work"),
    (r"\b(very|highly|dramatically|extremely|quite)\b", "LA-07", "delete or give a number"),
    (r"\b(remarkabl[ey]|notabl[ey]|striking(ly)?)\b", "LA-08", "at most two in the whole manuscript"),
    (r"\b(pivotal|crucial|essential|paramount)\b", "LA-09", "do not use for own results"),
    (r"\bit is (clear|evident|obvious) that\b|\bclearly\b|\bobviously\b", "LA-06", "delete"),
    (r"\bit was (found|observed|shown) that\b", "LA-06", "state the finding directly"),
    (r"\be\.g\.[^.]*\betc\b", "LA-21", "no 'etc.' after 'e.g.'"),
    (r"\bin conclusion\b", "LA-19", "only to close a Discussion"),
    (r"\b(might|may|could) (possibly|perhaps|potentially)\b|\bpossibly (might|may|could)\b", "LA-22", "stacked hedges"),
]
# Korean prose (KO rules). Candidates only; many have legitimate uses.
PHRASES_KO = [
    (r"에 있어(서)?", "KO-01", "번역투: '~에서', '~할 때'로"),
    (r"을 통해(서)?|를 통해(서)?", "KO-02", "'~으로', '~해서'로 바꿀 수 있는지"),
    (r"되어지|되어져|되어진|지게 되", "KO-03", "이중 피동: '~된다'로"),
    (r"것으로 (보인다|판단된다|사료된다|생각된다)|것으로 보입니다", "KO-04", "결과 서술에 추정 어미 금지(측정값은 단정, 해석만 유보)"),
    (r"(의미|중요성|특징|장점|한계)를 (가진다|갖는다|가지고 있다|갖습니다|가집니다)", "KO-05", "'가지다' 직역: '~이 있다', '~하다'로"),
    (r"에 대한 [^ ]+에 대한|에 대해 [^ ]+에 대해", "KO-06", "'~에 대한' 겹침"),
    (r"하는 것이 필요하다|하는 것이 필요합니다|할 필요가 있다", "KO-10", "'~해야 한다'로"),
    (r"(으)?로부터", "KO-11", "'~에서'로 바꿀 수 있는지"),
    (r"에 의해(서)? ", "KO-12", "피동 대신 능동 주어를 쓸 수 있는지"),
    (r"매우|굉장히|상당히|아주", "LA-07", "빈 강조어: 지우거나 수치로"),
    (r"최근 들어|최근 몇 년간|오늘날", "LA-18", "상투적 첫 문장"),
    (r"추가 연구가 필요하다|후속 연구가 필요하다", "LA-19", "다음 연구를 구체적으로, 마지막 문장은 피함"),
    (r"새로운 통찰", "LA-19", "통찰의 내용을 씀"),
    (r"유의(미)?(하게|한)", "LA-17", "검정 결과(검정명, p)를 같은 문장에"),
]
FIRST_PERSON_EN = r"\b(we|our|ours|us|ourselves)\b"
FIRST_PERSON_KO = r"(우리는|우리의|우리가|본 연구자|필자는)"
SIGNIFICANT = r"\bsignificant(ly)?\b|유의(미)?(하게|한)"
STAT_NEAR = (r"\bp\s*[<=>≤]|\bp-value|\bMcNemar\b|\bt-test\b|\bchi|\bconfidence interval|\bCI\b|\bHolm\b|\bp = |"
             r"\bANOVA\b|\bWilcoxon\b|\bMann|\bF\(|\bt\(|검정|신뢰 ?구간")
LEFTOVER = r"\[(ref|refs|citation needed|TBD|TODO|to be|insert|pending|fill)[^\]]*\]|\{\{\s*fill\s*\}\}"
US_UK = [("behavior", "behaviour"), ("defense", "defence"), ("center", "centre"), ("color", "colour"),
         ("modeling", "modelling"), ("labeled", "labelled"), ("analyze", "analyse"), ("optimize", "optimise"),
         ("generalize", "generalise"), ("organization", "organisation"), ("favor", "favour"), ("toward", "towards"),
         ("program", "programme"), ("gray", "grey")]
REAL_WORD_TYPOS = r"\bform (the|a|an|which)\b|\btrail(s)?\b|\bcasual\b|\bweighed\b|\bthen (the )?(baseline|previous|other)\b|\bexcept (the|a) (offer|invitation)\b"
ABBREV = r"\b[A-Z][A-Z0-9]{1,}[a-z]?(?:-[A-Z0-9]+)*\b"
ABBREV_OK = {"AI", "GPU", "CPU", "API", "URL", "US", "UK", "OK", "ID", "IDs", "PDF", "GB", "MB", "KB", "DOI", "ISBN",
             "ORCID", "USA", "EU", "PhD", "MSc", "BSc", "DNA", "RNA", "II", "III", "IV", "VI", "VII", "VIII", "IX", "XI"}
HOUSE_INTERNAL = r"\b(v\d+\.\d+(\.\d+)?|iter(ation)?[ _-]?\d+|run[_-]\d+|exp[_-]?\d+|patch \d+|TODO|FIXME)\b"


def load_profile(name: str = "engineering") -> dict:
    p = Path(name)
    if not p.suffix:
        p = PROFILES / f"{name}.toml"
    if not p.exists():
        raise SystemExit(f"no profile {name}; available: {', '.join(sorted(x.stem for x in PROFILES.glob('*.toml')))}")
    with open(p, "rb") as f:
        prof = tomllib.load(f)
    base = {"name": p.stem, "language": "en", "first_person": "forbid", "sentence_unit": "words",
            "sentence_review": 25, "sentence_long": 30, "sentence_long_max": 4, "sentence_cap": 32,
            "sentence_target": [15, 18], "paragraph_max": 150, "check_spelling": True, "check_abbrev": True,
            "disabled": [], "extra_phrases": []}
    base.update(prof)
    return base


def project_profile(cfg: dict, name: str | None = None) -> dict:
    """The field profile of a project, with the journal's first-person rule applied on top (journal > profile)."""
    prof = load_profile(name or cfg.get("project", {}).get("field", "engineering"))
    fp = cfg.get("journal", {}).get("first_person", "")
    if fp in ("forbid", "allow"):
        prof["first_person"] = fp
    return prof


def read_text(path: Path) -> str:
    if path.suffix.lower() == ".docx":
        with zipfile.ZipFile(path) as z:
            xml = z.read("word/document.xml").decode("utf-8")
        xml = re.sub(r"</w:p>", "\n", xml)
        return re.sub(r"<[^>]+>", "", xml)
    text = path.read_text(encoding="utf-8")
    if path.suffix.lower() == ".tex":
        text = strip_latex(text)
    return text


def strip_latex(text: str) -> str:
    """Rough prose view of LaTeX: drops comments, preamble, environments that are not prose, and commands."""
    text = re.sub(r"(?<!\\)%.*", "", text)
    if "\\begin{document}" in text:
        text = text.split("\\begin{document}", 1)[1]
    for env in ("equation", "align", "figure", "table", "tabular", "lstlisting", "verbatim", "thebibliography"):
        text = re.sub(rf"\\begin\{{{env}\*?\}}.*?\\end\{{{env}\*?\}}", "", text, flags=re.S)
    text = re.sub(r"\\(section|subsection|subsubsection|paragraph)\*?\{([^}]*)\}", r"# \2", text)
    text = re.sub(r"\\(cite[pt]?|ref|eqref|autoref|label|cref|Cref)\{[^}]*\}", "[cite]", text)
    text = re.sub(r"\\(emph|textbf|textit|mbox|text)\{([^}]*)\}", r"\2", text)
    text = re.sub(r"\\[A-Za-z]+\*?(\[[^\]]*\])?", "", text)
    return text.replace("{", "").replace("}", "").replace("~", " ")


def prose_lines(text: str) -> list[tuple[int, str]]:
    """(line number, text) of prose lines: skips headings, tables, code, quotes, HTML comments and bracket notes."""
    out, code = [], False
    for i, line in enumerate(text.splitlines(), 1):
        s = line.strip()
        if s.startswith("```"):
            code = not code
            continue
        if code or not s or s.startswith(("#", "|", ">", "<!--", "---", "![")) or re.fullmatch(r"\[[^\]]*\]", s):
            continue
        out.append((i, re.sub(r"[*_`]", "", re.sub(r"^\s*([-*+]|\d+[.)])\s+", "", s))))
    return out


_PROTECT = [("e.g.", "e<g>"), ("i.e.", "i<e>"), ("et al.", "et al<>"), ("Fig.", "Fig<>"), ("vs.", "vs<>"),
            ("Eq.", "Eq<>"), ("Ch.", "Ch<>"), ("No.", "No<>"), ("approx.", "approx<>"), ("cf.", "cf<>")]


def sentences(line: str) -> list[str]:
    for a, b in _PROTECT:
        line = line.replace(a, b)
    line = re.sub(r"\b([A-Z])\. (?=[A-Z][a-z])", r"\1<> ", line)       # initials: "Z. Lin"
    parts = re.split(r"(?<=[.!?。])\s+(?=[A-Z(\"'가-힣0-9])|(?<=[다요까죠]\.)\s*", line)
    out = []
    for p in parts:
        if not p:
            continue
        for a, b in _PROTECT:
            p = p.replace(b, a)
        p = re.sub(r"\b([A-Z])<> ", r"\1. ", p)
        if p.strip():
            out.append(p.strip())
    return out


def length(s: str, unit: str) -> int:
    if unit == "chars":
        return len(re.sub(r"\s+", "", s))
    return len(re.findall(r"[A-Za-z0-9가-힣][A-Za-z0-9가-힣'’.\-–%×⁻⁰¹²³⁴⁵⁶⁷⁸⁹]*", s))


def check(text: str, profile: dict | None = None, max_words: int | None = None, max_displays: int | None = None) -> dict:
    prof = profile or load_profile()
    ko = prof["language"] == "ko"
    off = set(prof.get("disabled", []))
    phrases = (PHRASES_KO if ko else PHRASES_EN) + [tuple(x) for x in prof.get("extra_phrases", [])]
    phrases = [p for p in phrases if not set(p[1].split()) <= off]
    unit = prof["sentence_unit"]
    lines = prose_lines(text)
    res: dict = {"first_person": [], "long": [], "phrases": [], "significant": [], "leftover": [], "typos": [],
                 "abbrev": [], "spelling": [], "internal": [], "paragraphs": [], "counts": {}, "profile": prof["name"]}
    n_len, n_sent, n_words, first_abbrev = 0, 0, 0, {}
    code = False
    for ln, line in enumerate(text.splitlines(), 1):          # placeholders count on every line outside code
        if line.strip().startswith("```"):
            code = not code
        if not code and not line.strip().startswith("<!--"):
            for m in re.finditer(LEFTOVER, line, re.I):
                res["leftover"].append((ln, m.group(0)))
    ends = {"formal": 0, "plain": 0}
    for ln, line in lines:
        clean = re.sub(LEFTOVER, "", line, flags=re.I)
        n_words += length(clean, "words")
        para = length(clean, "words")
        if prof.get("paragraph_max") and para > prof["paragraph_max"] and not ko:
            res["paragraphs"].append((ln, para))
        for s in sentences(clean):
            if ko:
                if re.search(r"(니다|니까)[.?!]?$", s):
                    ends["formal"] += 1
                elif re.search(r"다[.?!]?$", s):
                    ends["plain"] += 1
            n = length(s, unit)
            n_len += n
            n_sent += 1
            if n > prof["sentence_review"]:
                res["long"].append((ln, n, s[:90]))
        if prof["first_person"] == "forbid" and "LA-16" not in off:
            for m in re.finditer(FIRST_PERSON_KO if ko else FIRST_PERSON_EN, clean, re.I):
                res["first_person"].append((ln, m.group(0)))
        for pat, ids, hint in phrases:
            for m in re.finditer(pat, clean, 0 if ko else re.I):
                res["phrases"].append((ln, ids, m.group(0), hint))
        if "LA-17" not in off and re.search(SIGNIFICANT, clean, re.I) and not re.search(STAT_NEAR, clean, re.I):
            res["significant"].append(ln)
        if not ko and "LA-15" not in off:
            for m in re.finditer(REAL_WORD_TYPOS, clean, re.I):
                res["typos"].append((ln, m.group(0)))
        if "HR-07" not in off:
            for m in re.finditer(HOUSE_INTERNAL, clean):
                res["internal"].append((ln, m.group(0)))
        if prof.get("check_abbrev") and "LA-11" not in off:
            for m in re.finditer(ABBREV, clean):
                a = m.group(0)
                if a in ABBREV_OK or a in first_abbrev or (a.endswith("s") and a[:-1] in first_abbrev):
                    continue
                defined = (clean[max(0, m.start() - 1):m.start()] == "(" or clean[m.end():m.end() + 2] == " ("
                           or bool(re.search(r"\(" + re.escape(a) + r"\b", clean)))
                first_abbrev[a] = (ln, defined)
    res["abbrev"] = [(ln, a) for a, (ln, defined) in first_abbrev.items() if not defined]
    res["register"] = ends if ko and ends["formal"] and ends["plain"] else None
    if prof.get("check_spelling") and not ko:
        low = text.lower()
        for us, uk in US_UK:
            cu, ck = len(re.findall(r"\b" + us + r"(?!s?\w)", low)), len(re.findall(r"\b" + uk, low))
            if cu and ck:
                res["spelling"].append((us, cu, uk, ck))
    displays = {m.group(0).replace("Fig.", "Figure").replace("표 ", "Table ").replace("그림 ", "Figure ")
                for m in re.finditer(r"\b(Table|Figure|Fig\.)\s+\d+|(표|그림)\s+\d+", text)}
    res["counts"] = {"words": n_words, "sentences": n_sent, "unit": unit,
                     "mean_sentence": round(n_len / n_sent, 1) if n_sent else 0,
                     "over_review": len(res["long"]),
                     "over_long": sum(1 for x in res["long"] if x[1] > prof["sentence_long"]),
                     "over_cap": sum(1 for x in res["long"] if x[1] > prof["sentence_cap"]),
                     "displays": len(displays), "max_words": max_words, "max_displays": max_displays}
    return res


def blocking(res: dict, prof: dict) -> list[str]:
    """Findings that are 'blocking' in docs/review_procedure.md section 3 (the reviewer still confirms them)."""
    c = res["counts"]
    out = []
    if res["leftover"]:
        out.append(f"{len(res['leftover'])} leftover placeholder(s)")
    if res["first_person"]:
        out.append(f"{len(res['first_person'])} first-person word(s) under a no-first-person rule")
    if c["max_words"] and c["words"] > c["max_words"]:
        out.append("word count above the journal limit")
    if c["max_displays"] and c["displays"] > c["max_displays"]:
        out.append("tables + figures above the journal limit")
    return out


def report(res: dict, name: str, prof: dict | None = None) -> str:
    prof = prof or load_profile(res.get("profile", "engineering"))
    c = res["counts"]
    u = "자" if c["unit"] == "chars" else "words"
    lo, hi = prof["sentence_target"]
    out = [f"# manuscript check: {name}", "",
           f"Profile `{prof['name']}`. Candidates only; the reviewer judges each one (docs/review_procedure.md, step 5).", "",
           "## Counts", "",
           f"- Words (prose lines): {c['words']}" + (f" / limit {c['max_words']} (PK-01)" if c["max_words"] else ""),
           f"- Sentences: {c['sentences']}, mean {c['mean_sentence']} {u} (target {lo}–{hi}, LA-01)",
           f"- Over {prof['sentence_review']} {u}: {c['over_review']}; over {prof['sentence_long']}: {c['over_long']} "
           f"(at most {prof['sentence_long_max']}); over {prof['sentence_cap']}: {c['over_cap']} (split)",
           f"- Distinct tables and figures referenced: {c['displays']}" + (f" / limit {c['max_displays']} (PK-01)" if c["max_displays"] else ""), ""]
    blk = blocking(res, prof)
    if blk:
        out += ["**Blocking candidates: " + "; ".join(blk) + "**", ""]
    sec = [("Leftover placeholders (PK-03, must be zero at submission)", [f"L{l}: `{t}`" for l, t in res["leftover"]]),
           ("First person (LA-16, forbidden by this profile or the house rules)", [f"L{l}: {t}" for l, t in res["first_person"]]),
           ("'significant' without a test in the same line (LA-17)", [f"L{l}" for l in res["significant"]]),
           ("Abbreviations without a definition at first use (LA-11)", [f"L{l}: {a}" for l, a in res["abbrev"]]),
           ("Internal labels or development history (HR-03, HR-07)", [f"L{l}: {t}" for l, t in res["internal"]]),
           ("Phrases", [f"L{l} [{ids}] `{t}` — {h}" for l, ids, t, h in res["phrases"]]),
           (f"Sentences over {prof['sentence_long']} {u} (LA-01)", [f"L{l} ({w} {u}): {s}…" for l, w, s in res["long"] if w > prof["sentence_long"]]),
           (f"Paragraph lines over {prof.get('paragraph_max')} words (LA-25)", [f"L{l} ({w} words)" for l, w in res["paragraphs"]]),
           ("Mixed US/UK spelling (LA-14)", [f"{a} ×{x} vs {b} ×{y}" for a, x, b, y in res["spelling"]]),
           ("Possible real-word typos (LA-15)", [f"L{l}: {t}" for l, t in res["typos"]]),
           ("Mixed register: 합니다체 and 한다체 endings (KO-09)",
            [f"합니다체 {res['register']['formal']} sentences, 한다체 {res['register']['plain']} sentences"] if res.get("register") else [])]
    for title, items in sec:
        out += [f"## {title} — {len(items)}", ""] + [f"- {x}" for x in items[:200]] + [""]
    return "\n".join(out)


def run(path: Path, profile: str | dict = "engineering", max_words: int | None = None, max_displays: int | None = None,
        out: Path | None = None) -> int:
    prof = profile if isinstance(profile, dict) else load_profile(profile)
    res = check(read_text(path), prof, max_words, max_displays)
    rep = report(res, path.name, prof)
    if out:
        out.parent.mkdir(parents=True, exist_ok=True)
        out.write_text(rep + "\n", encoding="utf-8")
        print(f"wrote {out}: {len(blocking(res, prof))} blocking candidate group(s), {len(res['phrases'])} phrase flags")
    else:
        sys.stdout.reconfigure(encoding="utf-8")
        print(rep)
    return 0
