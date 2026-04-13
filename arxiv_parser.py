from __future__ import annotations

import io
import re
from pathlib import Path
from xml.etree.ElementTree import Element, SubElement, tostring, indent
from pypdf import PdfReader


_SECTION_PATTERNS = [
    re.compile(
        r"^(?P<num>(?:\d+\.?)+|[A-Z]\.?)\s{1,4}(?P<title>[A-Z][A-Za-z &\-/:,()]{2,60})$"
    ),
    # ALL-CAPS headings: "INTRODUCTION", "METHODS AND MATERIALS"
    re.compile(r"^(?P<title>[A-Z][A-Z &\-/:]{3,50})$"),
    # Title-case common sections (no number)
    re.compile(
        r"^(?P<title>(?:Abstract|Introduction|Background|Related Work|"
        r"Literature Review|Motivation|Problem Statement|"
        r"Materials?(?:\s+and\s+Methods?)?|Patients?\s+and\s+Methods?|"
        r"Methods?(?:\s+and\s+Materials?)?|Methodology|"
        r"Study\s+Design|Data\s+(?:Collection|Analysis)|"
        r"Experimental\s+(?:Setup|Design|Results?)|"
        r"Results?(?:\s+and\s+Discussion)?|"
        r"Discussion|Findings|Analysis|Evaluation|Limitations?|"
        r"Conclusion(?:s)?|Summary|Future\s+Work|"
        r"Acknowledgements?|Funding|Declarations?|"
        r"Competing\s+Interests?|Author\s+Contributions?|"
        r"Ethical\s+(?:Approval|Considerations?)|"
        r"Supplementary|Appendix|References?|Bibliography))$",
        re.IGNORECASE,
    ),
]

# Medical-paper specific headings (IMRAD + clinical)
_MEDICAL_EXTRA = re.compile(
    r"^(?P<title>(?:Objectives?|Aims?|Purpose|Hypothesis|Rationale|"
    r"Patients?\s+(?:and\s+)?(?:Methods?|Population)|Population|"
    r"Participants?|Subjects?|Sample|Eligibility|"
    r"Inclusion\s+Criteria|Exclusion\s+Criteria|"
    r"Interventions?|Outcomes?(?:\s+Measures?)?|"
    r"Primary\s+Endpoint|Secondary\s+Endpoint|"
    r"Statistical\s+(?:Analysis|Methods?)|Ethics|"
    r"Clinical\s+(?:Characteristics|Features|Outcomes?)|"
    r"Adverse\s+Events?|Safety|Efficacy|Surveillance|"
    r"Follow-?[Uu]p|Diagnosis|Treatment|Prognosis|"
    r"Case\s+(?:Report|Presentation|Series)|"
    r"Imaging|Laboratory|Biomarkers?|Genomics?|"
    r"Survival\s+Analysis|Hazard\s+Ratio))$",
    re.IGNORECASE,
)

_ALL_PATTERNS = _SECTION_PATTERNS + [_MEDICAL_EXTRA]


def _extract_text_pypdf(pdf_bytes: bytes) -> list[dict]:
    """Fallback: flat text extraction via pypdf."""
    reader = PdfReader(io.BytesIO(pdf_bytes))
    lines = []
    for page_num, page in enumerate(reader.pages, start=1):
        raw = page.extract_text() or ""
        for text in raw.splitlines():
            text = text.strip()
            if text:
                lines.append({"text": text, "size": 10.0, "bold": False, "page": page_num})
    return lines


def _extract_lines(pdf_bytes: bytes) -> list[dict]:
        return _extract_text_pypdf(pdf_bytes)


def _is_heading(line: dict, body_size: float) -> tuple[bool, str | None]:
    """
    Return (True, clean_title) if the line looks like a section heading.
    Uses font-size heuristic + regex patterns.
    """
    text = line["text"].strip()
    if len(text) < 2 or len(text) > 120:
        return False, None
    alpha_ratio = sum(c.isalpha() for c in text) / max(len(text), 1)
    if alpha_ratio < 0.4:
        return False, None

    size_boost = line["size"] >= body_size + 0.8 or line["bold"]

    for pat in _ALL_PATTERNS:
        m = pat.match(text)
        if m:
            title = m.group("title") if "title" in pat.groupindex else text
            # Numbered headings  title from the `title` capture group
            if "num" in pat.groupindex:
                num = m.group("num")
                title = f"{num} {title}"
            return True, title.strip()

    # Font-size only: a notably larger/bold line that starts with a capital
    if size_boost and text[0].isupper() and len(text.split()) <= 8:
        # Avoid false positives from bold sentences mid-paragraph
        if not text.endswith(".") and "," not in text:
            return True, text

    return False, None


def _estimate_body_size(lines: list[dict]) -> float:
    """Mode font size = body text size."""
    from collections import Counter
    sizes = [round(l["size"]) for l in lines if l["size"] > 0]
    if not sizes:
        return 10.0
    return float(Counter(sizes).most_common(1)[0][0])


# ─── Section assembly ────────────────────────────────────────────────────────

def _build_sections(lines: list[dict]) -> list[dict]:
    """
    Walk the lines and group them into sections:
    [{heading, page, lines: [str]}]
    """
    body_size = _estimate_body_size(lines)
    sections: list[dict] = []
    current: dict | None = None

    for line in lines:
        is_h, title = _is_heading(line, body_size)

        if current is None and not is_h:
            current = {"heading": "Preamble", "page": line["page"], "lines": []}

        if is_h:
            if current is not None:
                sections.append(current)
            current = {"heading": title, "page": line["page"], "lines": []}
        else:
            if current is not None:
                current["lines"].append(line["text"])

    if current is not None:
        sections.append(current)

    return sections


def _clean_section_text(raw_lines: list[str]) -> str:
    """Join lines, collapse hyphenated line-breaks, normalise whitespace."""
    joined = " ".join(raw_lines)
    joined = re.sub(r"-\s+([a-z])", r"\1", joined)
    joined = re.sub(r" {2,}", " ", joined)
    return joined.strip()


# ─── Serialisers ─────────────────────────────────────────────────────────────

def _to_xml(meta: dict, sections: list[dict]) -> str:
    root = Element("paper")

    meta_el = SubElement(root, "metadata")
    for k, v in meta.items():
        el = SubElement(meta_el, k)
        el.text = str(v)

    body_el = SubElement(root, "body")
    for sec in sections:
        sec_el = SubElement(body_el, "section")
        sec_el.set("page", str(sec["page"]))
        heading_el = SubElement(sec_el, "heading")
        heading_el.text = sec["heading"]
        content_el = SubElement(sec_el, "content")
        content_el.text = _clean_section_text(sec["lines"])

    indent(root, space="  ")
    return '<?xml version="1.0" encoding="utf-8"?>\n' + tostring(
        root, encoding="unicode"
    )
    title = meta.get("title", "arXiv Paper")
    parts = [
        "<!DOCTYPE html>",
        '<html lang="en">',
        "<head>",
        '  <meta charset="utf-8">',
        f"  <title>{_esc(title)}</title>",
        "  <style>",
        "    body { font-family: Georgia, serif; max-width: 860px; margin: 2rem auto; line-height: 1.7; color: #222; }",
        "    h1 { font-size: 1.5rem; border-bottom: 2px solid #333; padding-bottom: .4rem; }",
        "    h2 { font-size: 1.15rem; margin-top: 2rem; color: #444; }",
        "    .meta { background: #f5f5f5; padding: 1rem; border-radius: 6px; margin-bottom: 2rem; font-size: .9rem; }",
        "    .meta dt { font-weight: bold; display: inline; }",
        "    .meta dd { display: inline; margin: 0 0 0 .3rem; }",
        "    .meta dd::after { display: block; content: ''; }",
        "    section { margin-bottom: 1.5rem; }",
        "    .page-ref { font-size: .75rem; color: #888; margin-left: .5rem; }",
        "  </style>",
        "</head>",
        "<body>",
        f"  <h1>{_esc(title)}</h1>",
        "  <dl class='meta'>",
    ]
    for k, v in meta.items():
        if k != "title":
            parts.append(f"    <dt>{_esc(k.capitalize())}:</dt><dd>{_esc(str(v))}</dd>")
    parts.append("  </dl>")

    for sec in sections:
        page_ref = f'<span class="page-ref">(p.{sec["page"]})</span>'
        content = _esc(_clean_section_text(sec["lines"]))
        parts += [
            "  <section>",
            f"    <h2>{_esc(sec['heading'])}{page_ref}</h2>",
            f"    <p>{content}</p>",
            "  </section>",
        ]

    parts += ["</body>", "</html>"]
    return "\n".join(parts)


def _load_pdf(source: str | Path | bytes) -> tuple[bytes, dict]:
    """
    Accepts:
      - arXiv ID string like "2401.12345" or "arxiv:2401.12345"
      - local file path (str or Path)
      - raw PDF bytes

    Returns (pdf_bytes, meta_dict).
    """
    if isinstance(source, bytes):
        return source, {"source": "bytes"}

    source_str = str(source).strip()

    # Local file
    path = Path(source_str)
    if not path.exists():
        raise FileNotFoundError(f"File not found: {path}")
    return path.read_bytes(), {"source": str(path.resolve())}


def _extract_meta_from_preamble(sections: list[dict], base_meta: dict) -> dict:
    """
    Pull title/authors from the Preamble section heuristically.
    The preamble is typically the first section before any heading.
    """
    meta = dict(base_meta)
    preamble = next((s for s in sections if s["heading"] == "Preamble"), None)
    if preamble is None:
        return meta

    lines = preamble["lines"]
    if not lines:
        return meta

    candidates = [l for l in lines[:10] if len(l) > 10]
    if candidates:
        title_line = max(candidates[:3], key=len)
        meta.setdefault("title", title_line)

    if "title" in meta:
        title_idx = next(
            (i for i, l in enumerate(lines) if l == meta["title"]), -1
        )
        if title_idx >= 0 and title_idx + 1 < len(lines):
            author_candidate = lines[title_idx + 1]
            if re.search(r",|\band\b", author_candidate):
                meta.setdefault("authors", author_candidate)

    return meta


def parse_arxiv(
    source: str | Path | bytes,
    title: str | None = None,
    authors: str | None = None,
) -> str:
    """
    Parse an arXiv paper and return section-wise content as XML or HTML.

    Parameters
    ----------
    source : str | Path | bytes
        One of:
        - An arXiv ID  (e.g. ``"2401.12345"`` or ``"arxiv:2401.12345"``)
        - A local path to a PDF file (``str`` or ``pathlib.Path``)
        - Raw PDF bytes
    title : str, optional
        Override the detected paper title.
    authors : str, optional
        Override the detected authors string.

    Returns
    -------
    str
        Well-formed XML or HTML string containing all sections.

    Examples
    --------
    >>> xml_output = parse_arxiv("2401.12345")
    >>> html_output = parse_arxiv("paper.pdf", output_format="html")
    >>> result = parse_arxiv(pdf_bytes, output_format="xml")
    """
    pdf_bytes, base_meta = _load_pdf(source)
    lines = _extract_lines(pdf_bytes)

    if not lines:
        raise ValueError("No text could be extracted from the PDF.")

    sections = _build_sections(lines)
    meta = _extract_meta_from_preamble(sections, base_meta)

    if title:
        meta["title"] = title
    if authors:
        meta["authors"] = authors
    meta.setdefault("title", "Unknown Title")
    meta.setdefault("total_pages", max(l["page"] for l in lines))
    meta.setdefault("sections_found", len([s for s in sections if s["heading"] != "Preamble"]))

    return _to_xml(meta, sections)