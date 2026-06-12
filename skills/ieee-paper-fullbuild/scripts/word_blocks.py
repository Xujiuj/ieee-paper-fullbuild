#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""WordprocessingML block builders for IEEE template filling.

This module does not parse Markdown or own pipeline flow.
"""
import re
from copy import deepcopy

from docx.oxml import parse_xml
from docx.oxml.ns import nsdecls

W_NS = 'http://schemas.openxmlformats.org/wordprocessingml/2006/main'
M_NS = 'http://schemas.openxmlformats.org/officeDocument/2006/math'
TABLE_BORDER_SZ = '2'

# Formatter injects the concrete converter to avoid a dependency cycle.
inline_latex_to_omml = None

def set_inline_math_converter(converter):
    global inline_latex_to_omml
    inline_latex_to_omml = converter

def escape_xml(text):
    return text.replace('&', '&amp;').replace('<', '&lt;').replace('>', '&gt;').replace('"', '&quot;')

def make_para(style_id, text=None, bold=False, num_id=None):
    """Create a paragraph with the given style.

    Args:
        style_id: Word style ID (e.g. '1' for Heading 1, 'a3' for Body Text)
        text: Optional text content
        bold: Whether to bold the text
        num_id: Optional numPr numId value. Set to '0' to suppress auto-numbering.
                Omit (None) to inherit the style's default numbering.
    """
    p = parse_xml('<w:p %s/>' % nsdecls('w'))
    pPr = parse_xml('<w:pPr %s><w:pStyle w:val="%s"/></w:pPr>' % (nsdecls('w'), style_id))
    if num_id is not None:
        numPr = parse_xml('<w:numPr %s><w:ilvl w:val="0"/><w:numId w:val="%s"/></w:numPr>' % (nsdecls('w'), num_id))
        pPr.append(numPr)
    p.insert(0, pPr)
    if text is not None:
        r = parse_xml('<w:r %s/>' % nsdecls('w'))
        if bold:
            rPr = parse_xml('<w:rPr %s><w:b/></w:rPr>' % nsdecls('w'))
            r.insert(0, rPr)
        t = parse_xml('<w:t %s xml:space="preserve">%s</w:t>' % (nsdecls('w'), escape_xml(text)))
        r.append(t)
        p.append(r)
    return p

def make_para_with_formatting(style_id, text):
    """Create paragraph with inline bold, italic, and inline math ($...$) formatting.

    Pipeline: extract inline math → OMML → placeholders → split bold/italic → assemble runs.
    """
    p = parse_xml('<w:p %s/>' % nsdecls('w'))
    pPr = parse_xml('<w:pPr %s><w:pStyle w:val="%s"/></w:pPr>' % (nsdecls('w'), style_id))
    p.insert(0, pPr)

    if text is None:
        return p

    math_ommls = {}
    math_counter = [0]

    def replace_math(m):
        key = f'§§MATH_{math_counter[0]}§§'
        math_counter[0] += 1
        omml = inline_latex_to_omml(m.group(1))
        if omml is not None:
            math_ommls[key] = omml
        else:
            math_ommls[key] = None
            key = m.group(1)
        return key

    processed = re.sub(r'(?<!\$)\$(?!\$)(.+?)(?<!\$)\$(?!\$)', replace_math, text)
    segments = re.split(r'(\*\*.*?\*\*|\*[^*]+?\*)', processed)

    for seg in segments:
        if not seg:
            continue
        if seg.startswith('**') and seg.endswith('**'):
            inner = seg[2:-2]
            r = parse_xml('<w:r %s/>' % nsdecls('w'))
            rPr = parse_xml('<w:rPr %s><w:b/></w:rPr>' % nsdecls('w'))
            r.insert(0, rPr)
            if '§§MATH_' in inner:
                _add_mixed_content(r, inner, math_ommls, bold=True)
            else:
                t = parse_xml('<w:t %s xml:space="preserve">%s</w:t>' % (nsdecls('w'), escape_xml(inner)))
                r.append(t)
            p.append(r)
            continue
        if seg.startswith('*') and seg.endswith('*') and not seg.startswith('**'):
            inner = seg[1:-1]
            r = parse_xml('<w:r %s/>' % nsdecls('w'))
            rPr = parse_xml('<w:rPr %s><w:i/></w:rPr>' % nsdecls('w'))
            r.insert(0, rPr)
            if '§§MATH_' in inner:
                _add_mixed_content(r, inner, math_ommls, italic=True)
            else:
                t = parse_xml('<w:t %s xml:space="preserve">%s</w:t>' % (nsdecls('w'), escape_xml(inner)))
                r.append(t)
            p.append(r)
            continue
        if '§§MATH_' in seg:
            _add_mixed_content_to_para(p, seg, math_ommls)
        else:
            r = parse_xml('<w:r %s/>' % nsdecls('w'))
            t = parse_xml('<w:t %s xml:space="preserve">%s</w:t>' % (nsdecls('w'), escape_xml(seg)))
            r.append(t)
            p.append(r)
    return p

def _add_mixed_content(run, text, math_ommls, bold=False, italic=False):
    """Add mixed text+math content to an existing run by splitting on math placeholders."""
    parts = re.split(r'(§§MATH_\d+§§)', text)
    for part in parts:
        if not part:
            continue
        if part in math_ommls and math_ommls[part] is not None:
            run.append(deepcopy(math_ommls[part]))
        elif part.startswith('§§MATH_') and part.endswith('§§'):
            r = parse_xml('<w:r %s/>' % nsdecls('w'))
            if bold:
                rPr = parse_xml('<w:rPr %s><w:b/></w:rPr>' % nsdecls('w'))
                r.insert(0, rPr)
            elif italic:
                rPr = parse_xml('<w:rPr %s><w:i/></w:rPr>' % nsdecls('w'))
                r.insert(0, rPr)
            t = parse_xml('<w:t %s xml:space="preserve">[math]</w:t>' % nsdecls('w'))
            r.append(t)
            run.append(t)
        else:
            t = parse_xml('<w:t %s xml:space="preserve">%s</w:t>' % (nsdecls('w'), escape_xml(part)))
            run.append(t)

def _add_mixed_content_to_para(para, text, math_ommls):
    """Add mixed text+math content directly to a paragraph (not inside a run)."""
    parts = re.split(r'(§§MATH_\d+§§)', text)
    for part in parts:
        if not part:
            continue
        r = parse_xml('<w:r %s/>' % nsdecls('w'))
        if part in math_ommls and math_ommls[part] is not None:
            para.append(deepcopy(math_ommls[part]))
            continue
        elif part.startswith('§§MATH_') and part.endswith('§§'):
            t = parse_xml('<w:t %s xml:space="preserve">[math]</w:t>' % nsdecls('w'))
        else:
            t = parse_xml('<w:t %s xml:space="preserve">%s</w:t>' % (nsdecls('w'), escape_xml(part)))
        r.append(t)
        para.append(r)

def strip_cell_indent(tbl_element):
    """Set firstLine=0, left=0, right=0 on every paragraph inside every table cell."""
    for tc in tbl_element.findall('.//{%s}tc' % W_NS):
        for p in tc.findall('{%s}p' % W_NS):
            pPr = p.find('{%s}pPr' % W_NS)
            if pPr is None:
                pPr = parse_xml('<w:pPr %s/>' % nsdecls('w'))
                p.insert(0, pPr)
            ind = pPr.find('{%s}ind' % W_NS)
            if ind is not None:
                pPr.remove(ind)
            ind = parse_xml('<w:ind %s w:firstLine="0" w:left="0" w:right="0"/>' % nsdecls('w'))
            pPr.append(ind)

def clean_chinese_from_element(element):
    """Remove Chinese characters from rFonts/eastAsia attributes and w:t text."""
    for rf in element.iter('{%s}rFonts' % W_NS):
        ea = rf.get('{%s}eastAsia' % W_NS)
        if ea and re.search(r'[一-鿿]', ea):
            del rf.attrib['{%s}eastAsia' % W_NS]
    for t in element.iter('{%s}t' % W_NS):
        if t.text:
            cleaned = re.sub(r'[一-鿿]', '', t.text)
            if cleaned != t.text:
                t.text = cleaned

def make_equation_table(omml_element, eq_label):
    """Create a borderless 1x2 table: left=equation OMML, right=(N) label."""
    tbl_xml = '''
    <w:tbl %s>
      <w:tblPr>
        <w:tblStyle w:val="a3"/>
        <w:tblW w:w="5000" w:type="pct"/>
        <w:tblBorders>
          <w:top w:val="none" w:sz="0" w:space="0" w:color="auto"/>
          <w:left w:val="none" w:sz="0" w:space="0" w:color="auto"/>
          <w:bottom w:val="none" w:sz="0" w:space="0" w:color="auto"/>
          <w:right w:val="none" w:sz="0" w:space="0" w:color="auto"/>
          <w:insideH w:val="none" w:sz="0" w:space="0" w:color="auto"/>
          <w:insideV w:val="none" w:sz="0" w:space="0" w:color="auto"/>
        </w:tblBorders>
        <w:tblLook w:val="04A0" w:firstRow="1" w:lastRow="0" w:firstColumn="1" w:lastColumn="0" w:noHBand="0" w:noVBand="1"/>
      </w:tblPr>
      <w:tblGrid>
        <w:gridCol w:w="8000"/>
        <w:gridCol w:w="1000"/>
      </w:tblGrid>
      <w:tr>
        <w:tc>
          <w:tcPr>
            <w:tcW w:w="8000" w:type="dxa"/>
            <w:vAlign w:val="center"/>
          </w:tcPr>
          <w:p>
            <w:pPr>
              <w:jc w:val="center"/>
              <w:ind w:firstLine="0" w:left="0" w:right="0"/>
            </w:pPr>
          </w:p>
        </w:tc>
        <w:tc>
          <w:tcPr>
            <w:tcW w:w="1000" w:type="dxa"/>
            <w:vAlign w:val="center"/>
          </w:tcPr>
          <w:p>
            <w:pPr>
              <w:jc w:val="center"/>
              <w:ind w:firstLine="0" w:left="0" w:right="0"/>
            </w:pPr>
            <w:r>
              <w:t xml:space="preserve">(%s)</w:t>
            </w:r>
          </w:p>
        </w:tc>
      </w:tr>
    </w:tbl>
    ''' % (nsdecls('w'), eq_label)
    tbl = parse_xml(tbl_xml)
    left_p = tbl.findall('.//{%s}tc' % W_NS)[0].find('{%s}p' % W_NS)
    left_p.append(deepcopy(omml_element))
    strip_cell_indent(tbl)
    return tbl

def _cell_inner_xml(text, bold=False):
    """Convert cell text with inline math ($...$) and bold/italic to XML runs + OMML.

    Returns raw XML string suitable for embedding inside a <w:tc> element.
    """
    if not text:
        return ''

    sz_attr = '<w:sz w:val="16"/>'
    b_attr = '<w:b/>' if bold else ''

    # --- Step 1: extract inline math, convert to OMML, replace with placeholders ---
    math_ommls = {}
    math_counter = [0]

    def _replace_math(m):
        key = f'§§TBLMATH_{math_counter[0]}§§'
        math_counter[0] += 1
        omml = inline_latex_to_omml(m.group(1))
        if omml is not None:
            math_ommls[key] = omml
        else:
            math_ommls[key] = None
            key = m.group(1)  # fallback: keep raw LaTeX
        return key

    processed = re.sub(r'(?<!\$)\$(?!\$)(.+?)(?<!\$)\$(?!\$)', _replace_math, text)

    # --- Step 2: split on bold/italic markers and math placeholders ---
    segments = re.split(r'(\*\*.*?\*\*|\*[^*]+?\*|§§TBLMATH_\d+§§)', processed)

    parts = []
    for seg in segments:
        if not seg:
            continue

        # Math placeholder
        if seg.startswith('§§TBLMATH_') and seg.endswith('§§'):
            omml_elem = math_ommls.get(seg)
            if omml_elem is not None:
                omml_str = etree.tostring(omml_elem, encoding='unicode')
                # Strip namespace declarations (keep m: prefix) so nested XML parses cleanly
                omml_str = re.sub(r'\s*xmlns:[a-z]+="[^"]*"', '', omml_str)
                parts.append(
                    '<w:r><w:rPr>%s%s</w:rPr>%s</w:r>' % (b_attr, sz_attr, omml_str)
                )
            else:
                parts.append(
                    '<w:r><w:rPr>%s%s</w:rPr>'
                    '<w:t xml:space="preserve">%s</w:t></w:r>' % (b_attr, sz_attr, escape_xml(seg))
                )
            continue

        # Bold
        if seg.startswith('**') and seg.endswith('**'):
            inner = seg[2:-2]
            parts.append(
                '<w:r><w:rPr><w:b/>%s</w:rPr>'
                '<w:t xml:space="preserve">%s</w:t></w:r>' % (sz_attr, escape_xml(inner))
            )
            continue

        # Italic
        if seg.startswith('*') and seg.endswith('*') and not seg.startswith('**'):
            inner = seg[1:-1]
            parts.append(
                '<w:r><w:rPr><w:i/>%s</w:rPr>'
                '<w:t xml:space="preserve">%s</w:t></w:r>' % (sz_attr, escape_xml(inner))
            )
            continue

        # Plain text
        parts.append(
            '<w:r><w:rPr>%s%s</w:rPr>'
            '<w:t xml:space="preserve">%s</w:t></w:r>' % (b_attr, sz_attr, escape_xml(seg))
        )

    return ''.join(parts)

def make_data_table(headers, rows, caption_text=None):
    """Create a Word data table from headers and rows, optionally with a tablehead caption."""
    elements = []
    if caption_text:
        # Strip markdown wrapper and manual number; tablehead style auto-numbers.
        clean = re.sub(r'\*\*(.+?)\*\*', r'\1', caption_text).strip()
        clean = re.sub(r'(?i)^table\s+[IVXLCDM0-9]+\.?\s*', '', clean).strip()
        elements.append(make_para('tablehead', clean))
    n_cols = len(headers)
    parts = ['<w:tbl %s %s>' % (nsdecls('w'), nsdecls('m'))]
    parts.append('''<w:tblPr>
      <w:tblStyle w:val="a3"/>
      <w:tblW w:w="5000" w:type="pct"/>
      <w:tblBorders>
        <w:top w:val="single" w:sz="%s" w:space="0" w:color="000000"/>
        <w:left w:val="single" w:sz="%s" w:space="0" w:color="000000"/>
        <w:bottom w:val="single" w:sz="%s" w:space="0" w:color="000000"/>
        <w:right w:val="single" w:sz="%s" w:space="0" w:color="000000"/>
        <w:insideH w:val="single" w:sz="%s" w:space="0" w:color="000000"/>
        <w:insideV w:val="single" w:sz="%s" w:space="0" w:color="000000"/>
      </w:tblBorders>
      <w:tblLook w:val="04A0" w:firstRow="1" w:lastRow="0" w:firstColumn="1" w:lastColumn="0" w:noHBand="0" w:noVBand="1"/>
    </w:tblPr>''' % ((TABLE_BORDER_SZ,) * 6))
    parts.append('<w:tblGrid>')
    col_w = 9000 // n_cols
    for _ in range(n_cols):
        parts.append('<w:gridCol w:w="%d"/>' % col_w)
    parts.append('</w:tblGrid>')
    parts.append('<w:tr>')
    for h in headers:
        inner = _cell_inner_xml(h, bold=True)
        parts.append('<w:tc><w:tcPr><w:tcW w:w="%d" w:type="dxa"/></w:tcPr>'
                     '<w:p><w:pPr><w:pStyle w:val="a3"/><w:jc w:val="center"/><w:ind w:firstLine="0" w:left="0" w:right="0"/></w:pPr>'
                     '%s</w:p></w:tc>'
                     % (col_w, inner))
    parts.append('</w:tr>')
    for row in rows:
        parts.append('<w:tr>')
        for cell in row:
            inner = _cell_inner_xml(str(cell))
            parts.append('<w:tc><w:tcPr><w:tcW w:w="%d" w:type="dxa"/></w:tcPr>'
                         '<w:p><w:pPr><w:pStyle w:val="a3"/><w:jc w:val="center"/><w:ind w:firstLine="0" w:left="0" w:right="0"/></w:pPr>'
                         '%s</w:p></w:tc>'
                         % (col_w, inner))
        parts.append('</w:tr>')
    parts.append('</w:tbl>')
    tbl = parse_xml(''.join(parts))
    elements.append(tbl)
    elements.append(make_para('a3', ''))
    return elements

def create_inline_drawing(rId, width_emu, height_emu):
    return '''
    <w:drawing %s>
      <wp:inline distT="0" distB="0" distL="0" distR="0">
        <wp:extent cx="%d" cy="%d"/>
        <wp:docPr id="100" name="Picture"/>
        <a:graphic %s>
          <a:graphicData uri="http://schemas.openxmlformats.org/drawingml/2006/picture">
            <pic:pic %s>
              <pic:nvPicPr>
                <pic:cNvPr id="0" name="Picture"/>
                <pic:cNvPicPr/>
              </pic:nvPicPr>
              <pic:blipFill>
                <a:blip r:embed="%s"/>
                <a:stretch><a:fillRect/></a:stretch>
              </pic:blipFill>
              <pic:spPr>
                <a:xfrm>
                  <a:off x="0" y="0"/>
                  <a:ext cx="%d" cy="%d"/>
                </a:xfrm>
                <a:prstGeom prst="rect"><a:avLst/></a:prstGeom>
              </pic:spPr>
            </pic:pic>
          </a:graphicData>
        </a:graphic>
      </wp:inline>
    </w:drawing>
    ''' % (nsdecls('w', 'wp', 'a', 'r', 'pic'), width_emu, height_emu,
           nsdecls('a'), nsdecls('pic'), rId, width_emu, height_emu)

def clear_paragraph_text(para):
    """Clear runs from a paragraph while preserving paragraph properties."""
    for r in list(para.findall('{%s}r' % W_NS)):
        para.remove(r)

def paragraph_has_sectPr(para):
    pPr = para.find('{%s}pPr' % W_NS)
    return pPr is not None and pPr.find('{%s}sectPr' % W_NS) is not None

def paragraph_style(para):
    pPr = para.find('{%s}pPr' % W_NS)
    if pPr is None:
        return ''
    pStyle = pPr.find('{%s}pStyle' % W_NS)
    return pStyle.get('{%s}val' % W_NS) if pStyle is not None else ''

def build_ref_heading():
    """Create References heading: Heading 1 style with numId=0 (suppresses auto-numbering)."""
    return make_para('1', 'References', num_id='0')

