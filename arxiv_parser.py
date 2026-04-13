from __future__ import annotations

import io
import re
import sys
import textwrap
from pathlib import Path
from typing import Literal
from xml.etree.ElementTree import Element, SubElement, tostring, indent

# ─── optional imports (checked at runtime) ──────────────────────────────────
try:
    import requests
    _HAS_REQUESTS = True
except ImportError:
    _HAS_REQUESTS = False

try:
    from pdfminer.high_level import extract_pages
    from pdfminer.layout import LTPage, LTTextBox, LTTextLine, LTChar, LTAnon, LTFigure
    _HAS_PDFMINER = True
except ImportError:
    _HAS_PDFMINER = False

try:
    from pypdf import PdfReader
    _HAS_PYPDF = True
except ImportError:
    _HAS_PYPDF = False


# ─── Section-heading patterns ────────────────────────────────────────────────

# Standard academic sections (ordered by priority)
_SECTION_PATTERNS = [
    # Numbered: "1  Introduction", "2.3 Related Work", "A. Appendix"
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


# ─── PDF text extraction ─────────────────────────────────────────────────────

def _extract_text_pdfminer(pdf_bytes: bytes) -> list[dict]:
    """
    Extract text with basic font-size metadata using pdfminer.
    Returns list of dicts: {text, size, bold, page}.
    """
    lines = []
    for page_num, page_layout in enumerate(
        extract_pages(io.BytesIO(pdf_bytes)), start=1
    ):
        for element in page_layout:
            if not isinstance(element, LTTextBox):
                continue
            for line in element:
                if not isinstance(line, LTTextLine):
                    continue
                text = line.get_text().strip()
                if not text:
                    continue
                sizes, bold_flags = [], []
                for char in line:
                    if isinstance(char, LTChar):
                        sizes.append(char.size)
                        bold_flags.append("Bold" in (char.fontname or ""))
                avg_size = sum(sizes) / len(sizes) if sizes else 10.0
                is_bold = bool(bold_flags) and (
                    sum(bold_flags) / len(bold_flags) > 0.5
                )
                lines.append(
                    {
                        "text": text,
                        "size": round(avg_size, 1),
                        "bold": is_bold,
                        "page": page_num,
                    }
                )
    return lines


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
    if _HAS_PDFMINER:
        return _extract_text_pdfminer(pdf_bytes)
    if _HAS_PYPDF:
        return _extract_text_pypdf(pdf_bytes)
    raise RuntimeError("Neither pdfminer.six nor pypdf is installed.")


# ─── Heading detection ───────────────────────────────────────────────────────

def _is_heading(line: dict, body_size: float) -> tuple[bool, str | None]:
    """
    Return (True, clean_title) if the line looks like a section heading.
    Uses font-size heuristic + regex patterns.
    """
    text = line["text"].strip()
    # Skip very short or very long lines
    if len(text) < 2 or len(text) > 120:
        return False, None
    # Skip lines that are mostly numbers/symbols (tables, equations)
    alpha_ratio = sum(c.isalpha() for c in text) / max(len(text), 1)
    if alpha_ratio < 0.4:
        return False, None

    size_boost = line["size"] >= body_size + 0.8 or line["bold"]

    for pat in _ALL_PATTERNS:
        m = pat.match(text)
        if m:
            title = m.group("title") if "title" in pat.groupindex else text
            # Numbered headings get title from the `title` capture group
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

        # Special-case: first lines before any heading → "Preamble" (title/authors)
        if current is None and not is_h:
            current = {"heading": "Preamble", "page": line["page"], "lines": []}

        if is_h:
            # Save previous section
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
    # Re-join hyphenated words split across lines (common in PDFs)
    joined = re.sub(r"-\s+([a-z])", r"\1", joined)
    # Collapse multiple spaces
    joined = re.sub(r" {2,}", " ", joined)
    return joined.strip()


# ─── Serialisers ─────────────────────────────────────────────────────────────

def _to_xml(meta: dict, sections: list[dict]) -> str:
    root = Element("paper")

    # Metadata
    meta_el = SubElement(root, "metadata")
    for k, v in meta.items():
        el = SubElement(meta_el, k)
        el.text = str(v)

    # Sections
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


def _to_html(meta: dict, sections: list[dict]) -> str:
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


def _esc(text: str) -> str:
    """HTML-escape a string."""
    return (
        text.replace("&", "&amp;")
            .replace("<", "&lt;")
            .replace(">", "&gt;")
            .replace('"', "&quot;")
    )


# ─── PDF acquisition ─────────────────────────────────────────────────────────

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

    # arXiv ID  (e.g. "2401.12345", "arxiv:2401.12345", or full URL)
    arxiv_id_pat = re.compile(
        r"(?:arxiv[:\s/]*)?(\d{4}\.\d{4,5}(?:v\d+)?)$", re.IGNORECASE
    )
    m = arxiv_id_pat.search(source_str)
    if m:
        arxiv_id = m.group(1)
        if not _HAS_REQUESTS:
            raise RuntimeError("'requests' is required to download from arXiv.")
        pdf_url = f"https://arxiv.org/pdf/{arxiv_id}"
        abs_url = f"https://arxiv.org/abs/{arxiv_id}"
        print(f"[arxiv_parser] Downloading {pdf_url} …", file=sys.stderr)
        resp = requests.get(pdf_url, timeout=60, headers={"User-Agent": "arxiv-parser/1.0"})
        resp.raise_for_status()
        meta = {"source": abs_url, "arxiv_id": arxiv_id}
        return resp.content, meta

    # Local file
    path = Path(source_str)
    if not path.exists():
        raise FileNotFoundError(f"File not found: {path}")
    return path.read_bytes(), {"source": str(path.resolve())}


# ─── Metadata extraction from preamble ───────────────────────────────────────

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

    # Title: usually the longest line in the first few, all-non-lower
    candidates = [l for l in lines[:10] if len(l) > 10]
    if candidates:
        # Heuristic: title tends to be the longest of the first 3 non-trivial lines
        title_line = max(candidates[:3], key=len)
        meta.setdefault("title", title_line)

    # Authors: line(s) after the title that contain commas or "and"
    if "title" in meta:
        title_idx = next(
            (i for i, l in enumerate(lines) if l == meta["title"]), -1
        )
        if title_idx >= 0 and title_idx + 1 < len(lines):
            author_candidate = lines[title_idx + 1]
            if re.search(r",|\band\b", author_candidate):
                meta.setdefault("authors", author_candidate)

    return meta


# ─── Main public function ─────────────────────────────────────────────────────

def parse_arxiv(
    source: str | Path | bytes,
    output_format: Literal["xml", "html"] = "xml",
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
    output_format : {"xml", "html"}
        Format of the returned string. Defaults to ``"xml"``.
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

    # Allow caller overrides
    if title:
        meta["title"] = title
    if authors:
        meta["authors"] = authors
    meta.setdefault("title", "Unknown Title")
    meta.setdefault("total_pages", max(l["page"] for l in lines))
    meta.setdefault("sections_found", len([s for s in sections if s["heading"] != "Preamble"]))

    if output_format == "html":
        return _to_html(meta, sections)
    return _to_xml(meta, sections)


# ─── CLI convenience ──────────────────────────────────────────────────────────

if __name__ == "__main__":
    import argparse

    ap = argparse.ArgumentParser(description="Parse an arXiv paper into XML or HTML.")
    ap.add_argument("source", help="arXiv ID (e.g. 2401.12345) or path to a PDF file")
    ap.add_argument(
        "--format", choices=["xml", "html"], default="xml", dest="fmt",
        help="Output format (default: xml)"
    )
    ap.add_argument("--output", "-o", default=None, help="Write to this file (default: stdout)")
    ap.add_argument("--title", default=None, help="Override paper title")
    ap.add_argument("--authors", default=None, help="Override authors")
    args = ap.parse_args()

    result = parse_arxiv(args.source, output_format=args.fmt, title=args.title, authors=args.authors)

    if args.output:
        Path(args.output).write_text(result, encoding="utf-8")
        print(f"Written to {args.output}", file=sys.stderr)
    else:
        print(result)