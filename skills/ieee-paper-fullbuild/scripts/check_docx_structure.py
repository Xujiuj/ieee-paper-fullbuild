#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Check source-level IEEE template fill invariants.

This is intentionally structural: it inspects WordprocessingML instead of
accepting a visually plausible .docx. The formatter is supposed to fill fixed
template slots, so section boundaries, front matter, and template styles must
survive generation.
"""
from __future__ import annotations

import re
import sys
import zipfile
from pathlib import Path

from lxml import etree

W_NS = "http://schemas.openxmlformats.org/wordprocessingml/2006/main"
W = f"{{{W_NS}}}"
NS = {"w": W_NS}


def _document_body(docx_path: Path):
    with zipfile.ZipFile(docx_path) as zf:
        xml = zf.read("word/document.xml")
    root = etree.fromstring(xml)
    return root.find("w:body", NS)


def _paragraphs(body):
    return [child for child in body if etree.QName(child).localname == "p"]


def _style(paragraph) -> str:
    p_style = paragraph.find("w:pPr/w:pStyle", NS)
    return p_style.get(W + "val") if p_style is not None else ""


def _text(paragraph) -> str:
    return "".join(paragraph.xpath(".//w:t/text()", namespaces=NS))


def _sect_cols(paragraph) -> str | None:
    cols = paragraph.find("w:pPr/w:sectPr/w:cols", NS)
    if cols is None:
        return None
    return cols.get(W + "num") or "1"


def _num_id(paragraph) -> str | None:
    num_id = paragraph.find("w:pPr/w:numPr/w:numId", NS)
    return num_id.get(W + "val") if num_id is not None else None


def _front_matter_text_by_style(body, style: str) -> list[str]:
    return [_text(p) for p in _paragraphs(body) if _style(p) == style]


def validate(output_docx: Path, template_docx: Path) -> list[tuple[bool, str]]:
    out_body = _document_body(output_docx)
    tpl_body = _document_body(template_docx)
    out_paras = _paragraphs(out_body)

    checks: list[tuple[bool, str]] = []

    for style in ("Author", "Affiliation"):
        expected = _front_matter_text_by_style(tpl_body, style)
        actual = _front_matter_text_by_style(out_body, style)
        checks.append((actual == expected, f"{style} paragraphs preserved exactly"))

    styles = [_style(p) for p in out_paras]
    checks.append(("Heading1" not in styles, "no synthetic Heading1 style paragraphs"))
    checks.append(("Heading2" not in styles, "no synthetic Heading2 style paragraphs"))
    checks.append((styles.count("1") >= 2, "IEEE heading style '1' used for headings"))

    tpl_sections = [
        (_style(p), _sect_cols(p))
        for p in _paragraphs(tpl_body)
        if _sect_cols(p) is not None
    ]
    out_sections = [
        (_style(p), _sect_cols(p))
        for p in out_paras
        if _sect_cols(p) is not None
    ]
    checks.append((out_sections == tpl_sections, f"section anchors match template: {out_sections}"))

    ref_heading = next((p for p in out_paras if _style(p) == "1" and _text(p).strip().lower() == "references"), None)
    checks.append((ref_heading is not None, "References heading uses IEEE style '1'"))
    if ref_heading is not None:
        checks.append((_num_id(ref_heading) == "0", "References heading suppresses auto-numbering"))

    body_headings = [
        _text(p).strip()
        for p in out_paras
        if _style(p) in {"1", "2"} and _text(p).strip().lower() != "references"
    ]
    manual = [h for h in body_headings if re.match(r"^(?:[IVX]+|[A-Z])\.\s+", h)]
    checks.append((not manual, f"manual heading prefixes stripped: {manual[:3]}"))

    bad_fig_captions = [
        _text(p).strip()
        for p in out_paras
        if _style(p) == "figurecaption" and re.match(r"^Fig\.\s*\d+\.?\s+", _text(p).strip(), re.I)
    ]
    bad_table_captions = [
        _text(p).strip()
        for p in out_paras
        if _style(p) == "tablehead" and re.match(r"^TABLE\s+[IVXLCDM0-9]+\.?\s+", _text(p).strip(), re.I)
    ]
    checks.append((not bad_fig_captions, f"figure captions rely on auto-numbering: {bad_fig_captions[:3]}"))
    checks.append((not bad_table_captions, f"table captions rely on auto-numbering: {bad_table_captions[:3]}"))

    return checks


def main() -> int:
    if len(sys.argv) != 3:
        print("Usage: python check_docx_structure.py <output.docx> <template.docx>", file=sys.stderr)
        return 2

    output_docx = Path(sys.argv[1])
    template_docx = Path(sys.argv[2])
    checks = validate(output_docx, template_docx)

    failed = False
    for ok, message in checks:
        print(("PASS" if ok else "FAIL") + f": {message}")
        failed = failed or not ok
    return 1 if failed else 0


if __name__ == "__main__":
    raise SystemExit(main())
