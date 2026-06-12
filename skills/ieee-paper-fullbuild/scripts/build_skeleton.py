#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""IEEE paper builder skeleton (reference implementation).

This is the canonical reference that survived all 13 validator
invariants on the SM383 lunar transport paper.

Copy this file into your project, customize the imports of
TITLE/ABSTRACT/KEYWORDS/BODY/FIGURES/REFERENCES, then run.

Invariants honored:
1. Edit template in place; do NOT clear body
2. Anchor body content on keywords paragraph
3. Strip placeholder runs from Author/Affiliation paragraphs but never
   delete a paragraph
4. Convert (eq:N) markers to OMML tables
5. Reject letter images via aspect+white classifier
6. No manual Roman / [n] / Fig. n. prefixes
7. Strip indent in every table cell
8. Clean residual Chinese eastAsia fonts
9. Use template auto-numbering
10. References paragraphs use 'references' style with numId 8
11. Equations are borderless 1x2 tables: equation | (n)
"""
import sys, os
sys.stdout.reconfigure(encoding='utf-8')

from docx import Document
from docx.shared import Inches
from docx.oxml.ns import qn
from docx.oxml import OxmlElement
from docx.enum.text import WD_ALIGN_PARAGRAPH
from lxml import etree

W = 'http://schemas.openxmlformats.org/wordprocessingml/2006/main'
M = 'http://schemas.openxmlformats.org/officeDocument/2006/math'

def make_run(text, italic=False, bold=False):
    r = OxmlElement('w:r')
    if italic or bold:
        rPr = OxmlElement('w:rPr')
        if italic:
            rPr.append(OxmlElement('w:i'))
            rPr.append(OxmlElement('w:iCs'))
        if bold:
            rPr.append(OxmlElement('w:b'))
        r.append(rPr)
    t = OxmlElement('w:t')
    t.set(qn('xml:space'), 'preserve')
    t.text = text
    r.append(t)
    return r

def make_para(style_id, text=None):
    p = OxmlElement('w:p')
    pPr = OxmlElement('w:pPr')
    pStyle = OxmlElement('w:pStyle')
    pStyle.set(qn('w:val'), style_id)
    pPr.append(pStyle)
    p.append(pPr)
    if text is not None:
        p.append(make_run(text))
    return p

def has_sectPr(p):
    pPr = p.find(qn('w:pPr'))
    return pPr is not None and pPr.find(qn('w:sectPr')) is not None

def is_placeholder_text(s):
    if not s: return False
    import re
    if re.search(r'[一-鿿（）]', s): return True
    if re.search(r'[À-ÿ]{3,}', s): return True
    return False

def load_omml(eq_xml_path):
    with open(eq_xml_path, 'r', encoding='utf-8') as f:
        xml_str = f.read()
    wrapper = f'<root xmlns:m="{M}" xmlns:w="{W}">{xml_str}</root>'
    return etree.fromstring(wrapper)[0]

def _make_cell(width_dxa):
    tc = OxmlElement('w:tc')
    tcPr = OxmlElement('w:tcPr')
    tcW = OxmlElement('w:tcW')
    tcW.set(qn('w:w'), width_dxa)
    tcW.set(qn('w:type'), 'dxa')
    tcPr.append(tcW)
    tcB = OxmlElement('w:tcBorders')
    for edge in ('top','left','bottom','right'):
        b = OxmlElement(f'w:{edge}')
        b.set(qn('w:val'), 'nil')
        tcB.append(b)
    tcPr.append(tcB)
    vA = OxmlElement('w:vAlign')
    vA.set(qn('w:val'), 'center')
    tcPr.append(vA)
    tc.append(tcPr)
    return tc

def _make_cell_para(right=False):
    p = OxmlElement('w:p')
    pPr = OxmlElement('w:pPr')
    ind = OxmlElement('w:ind')
    ind.set(qn('w:firstLine'), '0')
    ind.set(qn('w:left'), '0')
    ind.set(qn('w:right'), '0')
    pPr.append(ind)
    jc = OxmlElement('w:jc')
    jc.set(qn('w:val'), 'right' if right else 'center')
    pPr.append(jc)
    p.append(pPr)
    return p

def make_equation_table(eq_xml_path, label):
    tbl = OxmlElement('w:tbl')
    tblPr = OxmlElement('w:tblPr')
    tblW = OxmlElement('w:tblW')
    tblW.set(qn('w:w'), '5000')
    tblW.set(qn('w:type'), 'pct')
    tblPr.append(tblW)
    jc = OxmlElement('w:jc')
    jc.set(qn('w:val'), 'center')
    tblPr.append(jc)
    tblBorders = OxmlElement('w:tblBorders')
    for edge in ('top','left','bottom','right','insideH','insideV'):
        b = OxmlElement(f'w:{edge}')
        b.set(qn('w:val'), 'nil')
        tblBorders.append(b)
    tblPr.append(tblBorders)
    tbl.append(tblPr)

    tblGrid = OxmlElement('w:tblGrid')
    for wv in ('3500','500'):
        gc = OxmlElement('w:gridCol')
        gc.set(qn('w:w'), wv)
        tblGrid.append(gc)
    tbl.append(tblGrid)

    tr = OxmlElement('w:tr')
    tc1 = _make_cell('3500')
    p1 = _make_cell_para()
    p1.append(load_omml(eq_xml_path))
    tc1.append(p1)
    tr.append(tc1)
    tc2 = _make_cell('500')
    p2 = _make_cell_para(right=True)
    p2.append(make_run(f'({label})'))
    tc2.append(p2)
    tr.append(tc2)
    tbl.append(tr)
    return tbl

# Build flow excerpt (full impl: paper/sm383/build_ieee_final.py):
#   doc = Document(TEMPLATE); body = doc.element.body
#   Replace papertitle / Abstract / Keywords runs
#   Strip placeholder runs from Author/Affiliation; DELETE NONE
#   Find keywords_p; find next sectPr-bearing paragraph (boundary)
#   Remove every body element strictly between them
#   anchor = keywords_p
#   for kind, payload in BODY: insert via anchor.addnext(elem); advance anchor
#   Append References heading (style '1' with numId=0) then each ref para
#   Walk rFonts: remove eastAsia attrs with Chinese chars
#   Walk w:t: strip Chinese substrings
#   doc.save(OUTPUT)

if __name__ == '__main__':
    print("This is a reference skeleton; copy into your project and customize.")
