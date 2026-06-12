"""
IEEE Formatter: Fill IEEE.docx template with paper content from Markdown.

Usage:
    python format_ieee.py <template.docx> <source.md> <figure_dir> <output.docx>

Args:
    template.docx  - IEEE template file
    source.md      - Rewritten Markdown paper
    figure_dir     - Directory containing figure images
    output.docx    - Output path for the formatted document
"""
import os, re, shutil, subprocess, tempfile, sys, copy
from copy import deepcopy
from docx import Document
from docx.shared import Inches, Pt, Cm, Emu
from docx.oxml.ns import qn, nsdecls
from docx.oxml import parse_xml
from lxml import etree
from PIL import Image
import numpy as np
from parse_markdown import (
    clean_ref_markdown,
    extract_abstract,
    extract_body_and_refs,
    extract_keywords,
    extract_md_tables,
    extract_title,
    join_multiline_equations,
    parse_md_table,
    renumber_equations,
    renumber_references,
    strip_blank_lines_around_blocks,
)
from word_blocks import (
    build_ref_heading,
    clean_chinese_from_element,
    clear_paragraph_text,
    create_inline_drawing,
    escape_xml,
    make_data_table,
    make_equation_table,
    make_para,
    make_para_with_formatting,
    paragraph_has_sectPr,
    paragraph_style,
    set_inline_math_converter,
    strip_cell_indent,
)

args = [a for a in sys.argv[1:] if not a.startswith('--')]
if len(args) != 4:
    print("Usage: python format_ieee.py [--strict] <template.docx> <source.md> <figure_dir> <output.docx>")
    print("  --strict: Exit on HARD contract violations instead of proceeding")
    sys.exit(1)

TEMPLATE = args[0]
MD_PATH  = args[1]
FIG_DIR  = args[2]
OUTPUT   = args[3]

W_NS = 'http://schemas.openxmlformats.org/wordprocessingml/2006/main'
M_NS = 'http://schemas.openxmlformats.org/officeDocument/2006/math'
TABLE_BORDER_SZ = "2"
FIG_WIDTH_INCHES = 3.3
DASH_CHARS = '\u2014\u2013-'


# ============================================================================
# Section 0: Contract preflight check
# ============================================================================

def preflight_check(md_text):
    """Validate markdown by delegating to validate_md.py (Phase 3.5 Layer 1).
    Falls back to inline checks if validate_md.py is not available."""
    # Try to run validate_md.py
    script_dir = os.path.dirname(os.path.abspath(__file__))
    validator_path = os.path.join(script_dir, 'validate_md.py')

    if os.path.exists(validator_path):
        try:
            result = subprocess.run(
                [sys.executable, validator_path, MD_PATH],
                capture_output=True, text=True, timeout=30
            )
            output = result.stdout
            hard = []
            soft = []
            for line in output.split('\n'):
                if '[FAIL/HARD]' in line:
                    hard.append(line.strip().replace('[FAIL/HARD] ', ''))
                elif '[FAIL/SOFT]' in line:
                    soft.append(line.strip().replace('[FAIL/SOFT] ', ''))
            # Also print the validate_md.py output for visibility
            print(output)
            return {'hard': hard, 'soft': soft}
        except (subprocess.TimeoutExpired, FileNotFoundError, OSError) as e:
            print(f"  [INFO] validate_md.py failed ({e}), falling back to inline checks")

    # Fallback: minimal inline checks (original logic, simplified)
    warnings = []

    if not re.search(r'\*\*Abstract\*\*\s*[—–\-]', md_text):
        warnings.append("C1: Missing **Abstract** — format (may fail to extract)")

    if not re.search(r'\*\*Keywords?\*\*\s*[—–\-]', md_text):
        warnings.append("C2: Missing **Keywords** — format")

    fig_nums = [int(x) for x in re.findall(r'!\[Fig\.\s*(\d+)', md_text)]
    if fig_nums:
        expected = list(range(1, len(fig_nums) + 1))
        if fig_nums != expected:
            warnings.append(f"C4: Figure numbers not sequential: {fig_nums}")

    fig_captions = re.findall(r'!\[Fig\.\s*\d+\.\s*(.+?)\]', md_text)
    long_caps = [c for c in fig_captions if len(c.split()) > 12]
    if long_caps:
        warnings.append(f"C4: Figure captions too long (>12 words): {long_caps[:3]}")
    punct_caps = [c for c in fig_captions if re.search(r'[.,;:!?]$', c.strip())]
    if punct_caps:
        warnings.append(f"C4: Figure captions end with punctuation: {punct_caps[:3]}")

    tbl_captions = re.findall(r'\*\*TABLE\s+[IVXLCDM]+\.?\s*(.+?)\*\*', md_text)
    long_caps = [c for c in tbl_captions if len(c.split()) > 8]
    if long_caps:
        warnings.append(f"C5: Table captions too long (>8 words): {long_caps[:3]}")
    tbl_punct = [c for c in tbl_captions if re.search(r'[.,;:!?]$', c.strip())]
    if tbl_punct:
        warnings.append(f"C5: Table captions end with punctuation: {tbl_punct[:3]}")

    eq_tags = re.findall(re.escape(chr(92)) + r'tag\{eq:(\d+)\}', md_text)
    if len(eq_tags) < 5:
        warnings.append(f"C6: Only {len(eq_tags)} equations (validator needs ≥5)")

    refs_match = re.search(r'## REFERENCES\s*\n(.*?)$', md_text, re.DOTALL | re.IGNORECASE)
    if refs_match:
        ref_count = len(re.findall(r'^\[\d+\]', refs_match.group(1), re.MULTILINE))
        if ref_count > 15:
            warnings.append(f"C7: {ref_count} references (max 15)")
        elif ref_count == 0:
            warnings.append("C7: No reference entries found in REFERENCES section")

    body_match = re.search(r'^## .+?\n(.*?)(?=^## (?:REFERENCES|ACKNOWLEDGMENT))', md_text, re.DOTALL | re.MULTILINE)
    if body_match:
        body_text = body_match.group(1)
        for fig_m in re.finditer(r'!\[Fig\.\s*(\d+)\.\s*(.+?)\]', md_text):
            fig_num = fig_m.group(1)
            if not re.search(r'Fig\.\s*' + re.escape(fig_num) + r'[^0-9]', body_text):
                warnings.append(f"C9: Fig. {fig_num} exists but is never cited in body text")
        for tbl_m in re.finditer(r'\*\*TABLE\s+([IVXLCDM]+)\.?\s*(.+?)\*\*', md_text):
            tbl_roman = tbl_m.group(1)
            if not re.search(r'Table\s+' + re.escape(tbl_roman) + r'[^A-Za-z]', body_text, re.IGNORECASE):
                warnings.append(f"C9: TABLE {tbl_roman} exists but is never cited in body text")

    if refs_match:
        for ref_line in refs_match.group(1).strip().split('\n'):
            if not ref_line.strip() or not re.match(r'^\[\d+\]', ref_line.strip()):
                continue
            if re.search(r'\*\*[^*]+\*\*', ref_line):
                warnings.append("C10: Bold markers (**) in reference: " + ref_line.strip()[:60])
                break
            if '`' in ref_line:
                warnings.append("C10: Backticks in reference: " + ref_line.strip()[:60])
                break
            if '~~' in ref_line:
                warnings.append("C10: Strikethrough in reference: " + ref_line.strip()[:60])
                break

    for w in warnings:
        print("  [CONTRACT WARNING] %s" % w)

    hard_prefixes = ('C4:', 'C5_format:', 'C6:', 'C9:', 'C10:')
    hard = [w for w in warnings if w.startswith(hard_prefixes)]
    hard = [w for w in hard if 'too long' not in w]
    soft = [w for w in warnings if w not in hard]

    return {'hard': hard, 'soft': soft}


# ============================================================================
# Section 1: Utility functions
# ============================================================================


def check_image(path):
    """Reject scanned-letter images; allow genuine technical diagrams.

    Scanned letters: portrait (aspect < 1), very high white ratio (> 0.7),
    and low color variance in non-white pixels (grayscale text).
    Technical diagrams pass because they have colored regions even on white backgrounds.
    """
    img = Image.open(path)
    w, h = img.size
    aspect = w / h

    gray = np.array(img.convert('L'))
    white_ratio = (gray > 240).sum() / gray.size

    # Quick pass for landscape or low-white images
    if aspect >= 1.0 or white_ratio <= 0.5:
        print(f"  OK: {os.path.basename(path)} ({w}x{h}, aspect={aspect:.2f}, white={white_ratio:.2f})")
        return True

    # Portrait + high white: check if non-white content has color (diagram) vs grayscale (scan)
    rgb = np.array(img.convert('RGB')).astype(float)
    non_white_mask = gray <= 240
    if non_white_mask.sum() > 0:
        non_white_rgb = rgb[non_white_mask]
        # Std dev across RGB channels for each pixel — high = colored diagram, low = grayscale scan
        channel_std = np.std(non_white_rgb, axis=1).mean()
        if channel_std > 15:
            print(f"  OK (colored diagram): {os.path.basename(path)} ({w}x{h}, aspect={aspect:.2f}, white={white_ratio:.2f}, ch_std={channel_std:.1f})")
            return True

    print(f"  REJECTED: {os.path.basename(path)} (aspect={aspect:.2f}, white={white_ratio:.2f})")
    return False


def strip_mojibake_runs(para):
    """Remove runs whose text contains Chinese characters or mojibake sequences."""
    chinese_re = re.compile(r'[一-鿿（）]')
    mojibake_re = re.compile(r'[\xc0-\xff]{3,}')
    for r in para.findall('{%s}r' % W_NS):
        for t in r.findall('{%s}t' % W_NS):
            txt = t.text or ''
            if chinese_re.search(txt) or mojibake_re.search(txt):
                para.remove(r)
                break


# ============================================================================
# Section 2: OMML / equation conversion
# ============================================================================

def latex_to_omml(latex_str):
    """Convert display LaTeX to OMML via pandoc --mathml."""
    latex_str = latex_str.strip()
    with tempfile.NamedTemporaryFile(mode='w', suffix='.tex', delete=False, encoding='utf-8') as f:
        f.write('\\documentclass{article}\n\\begin{document}\n')
        f.write('$' + latex_str + '$\n')
        f.write('\\end{document}\n')
        tex_path = f.name
    docx_path = tex_path.replace('.tex', '.docx')
    try:
        result = subprocess.run(['pandoc', tex_path, '-o', docx_path, '--mathml'],
                                capture_output=True, text=True, timeout=30)
        if result.returncode != 0:
            print(f"  Pandoc error: {result.stderr}")
            return None
        temp_doc = Document(docx_path)
        for p in temp_doc.element.body.iter('{%s}oMath' % M_NS):
            return deepcopy(p)
        for p in temp_doc.element.body.iter('{%s}p' % W_NS):
            omath = p.find('{%s}oMath' % M_NS)
            if omath is not None:
                return deepcopy(omath)
        print(f"  No OMML found for: {latex_str[:50]}")
        return None
    finally:
        for p in [tex_path, docx_path]:
            try:
                os.unlink(p)
            except:
                pass


def inline_latex_to_omml(latex_str):
    """Convert inline LaTeX to an OMML oMath element via pandoc."""
    latex_str = latex_str.strip()
    with tempfile.NamedTemporaryFile(mode='w', suffix='.tex', delete=False, encoding='utf-8') as f:
        f.write('\\documentclass{article}\n')
        f.write('\\begin{document}\n')
        f.write('x $' + latex_str + '$ x\n')
        f.write('\\end{document}\n')
        tex_path = f.name
    docx_path = tex_path.replace('.tex', '.docx')
    try:
        result = subprocess.run(['pandoc', tex_path, '-o', docx_path],
                                capture_output=True, text=True, timeout=30)
        if result.returncode != 0:
            print(f"  Pandoc error (inline): {result.stderr[:200]}")
            return None
        temp_doc = Document(docx_path)
        for p in temp_doc.element.body.iter('{%s}p' % W_NS):
            omath = p.find('{%s}oMath' % M_NS)
            if omath is not None:
                return deepcopy(omath)
        for omath in temp_doc.element.body.iter('{%s}oMath' % M_NS):
            return deepcopy(omath)
        print(f"  No OMML found for inline: {latex_str[:30]}")
        return None
    finally:
        for p in [tex_path, docx_path]:
            try:
                os.unlink(p)
            except:
                pass


set_inline_math_converter(inline_latex_to_omml)


# ============================================================================
# Section 3: Table construction
# ============================================================================


# ============================================================================
# Section 4: Drawing / image insertion
# ============================================================================


# ============================================================================
# Section 5: Markdown parsing — title, abstract, keywords
# ============================================================================


# ============================================================================
# Section 6: Body boundary detection
# ============================================================================


# ============================================================================
# Section 7: Reference renumbering
# ============================================================================


# ============================================================================
# Section 8: Equation extraction and conversion
# ============================================================================

def extract_and_convert_equations(md):
    """Extract $$...\\tag{eq:N}$$ from markdown, convert to OMML. Returns dict {num: omml}."""
    eq_pattern = re.compile(r'\$\$(.+?)' + re.escape(chr(92)) + r'tag\{eq:([a-zA-Z0-9]+)\}\s*\$\$', re.DOTALL)
    equations = {m.group(2): m.group(1).strip() for m in eq_pattern.finditer(md)}

    omml_cache = {}
    for eq_num, latex in equations.items():
        print(f"  Converting eq:{eq_num}...")
        omml = latex_to_omml(latex)
        if omml is not None:
            omml_cache[eq_num] = omml
            print(f"  Success: eq:{eq_num}")
        else:
            print(f"  FAILED: eq:{eq_num}")
    return omml_cache


# ============================================================================
# Section 9: Markdown table extraction from body lines
# ============================================================================


# ============================================================================
# Section 10: Front matter — template paragraph replacement
# ============================================================================


def replace_title(title_para, title_text):
    """Replace title paragraph runs with new title text."""
    for r in title_para.findall('{%s}r' % W_NS):
        title_para.remove(r)
    new_run = parse_xml('<w:r %s><w:t xml:space="preserve">%s</w:t></w:r>' % (nsdecls('w'), escape_xml(title_text)))
    title_para.append(new_run)
    print(f"Replaced title: {title_text[:60]}...")


def replace_abstract(abs_para, abstract_text):
    """Replace abstract paragraph with 3 runs: italic 'Abstract', em-dash, body text.

    Matches template paragraph 20 structure exactly.
    """
    for r in abs_para.findall('{%s}r' % W_NS):
        abs_para.remove(r)
    # Run 1: "Abstract" in italic
    r1 = parse_xml('<w:r %s/>' % nsdecls('w'))
    r1Pr = parse_xml('<w:rPr %s><w:i/></w:rPr>' % nsdecls('w'))
    r1.insert(0, r1Pr)
    r1t = parse_xml('<w:t %s xml:space="preserve">Abstract</w:t>' % nsdecls('w'))
    r1.append(r1t)
    abs_para.append(r1)
    # Run 2: em-dash
    r2 = parse_xml('<w:r %s><w:t %s xml:space="preserve">— </w:t></w:r>' % (nsdecls('w'), nsdecls('w')))
    abs_para.append(r2)
    # Run 3: body text
    r3 = parse_xml('<w:r %s><w:t %s xml:space="preserve">%s</w:t></w:r>' % (nsdecls('w'), nsdecls('w'), escape_xml(abstract_text)))
    abs_para.append(r3)
    print(f"Replaced abstract ({len(abstract_text)} chars)")


def replace_keywords(keywords_para, kw_text):
    """Replace keywords paragraph runs with new keywords text."""
    for r in keywords_para.findall('{%s}r' % W_NS):
        keywords_para.remove(r)
    new_run = parse_xml('<w:r %s><w:t xml:space="preserve">%s</w:t></w:r>' % (nsdecls('w'), escape_xml(kw_text)))
    keywords_para.append(new_run)
    print(f"Replaced keywords: {kw_text[:60]}...")


# ============================================================================
# Section 11: Main pipeline
# ============================================================================

def main():
    shutil.copy2(TEMPLATE, OUTPUT)
    print(f"Copied template to {OUTPUT}")

    doc = Document(OUTPUT)
    body = doc.element.body

    # --- Locate template paragraphs by style ---
    title_para = None
    abstract_paras = []
    keywords_para = None
    author_paras = []
    affiliation_paras = []
    refs_sectPr_para = None

    for p_elem in body.iterchildren('{%s}p' % W_NS):
        pPr = p_elem.find('{%s}pPr' % W_NS)
        if pPr is None:
            continue
        pStyle = pPr.find('{%s}pStyle' % W_NS)
        style = pStyle.get('{%s}val' % W_NS) if pStyle is not None else ''
        sectPr = pPr.find('{%s}sectPr' % W_NS)

        if style == 'papertitle':
            title_para = p_elem
        elif style == 'Abstract':
            abstract_paras.append(p_elem)
        elif style == 'Keywords':
            keywords_para = p_elem
        elif style == 'Author':
            author_paras.append(p_elem)
        elif style == 'Affiliation':
            affiliation_paras.append(p_elem)
        elif style == 'references' and sectPr is not None:
            refs_sectPr_para = p_elem

    print(f"Found: title={title_para is not None}, abstracts={len(abstract_paras)}, "
          f"keywords={keywords_para is not None}, authors={len(author_paras)}, "
          f"affiliations={len(affiliation_paras)}, refs_sectPr={refs_sectPr_para is not None}")

    # --- Parse markdown ---
    with open(MD_PATH, 'r', encoding='utf-8') as f:
        md = f.read()
    lines = md.split('\n')

    title_text = extract_title(lines)
    abstract_text = extract_abstract(lines)
    kw_text = extract_keywords(lines)

    # --- Contract preflight check ---
    print("\n=== Contract Preflight Check (C1-C10) ===")
    preflight_result = preflight_check(md)
    hard_errors = preflight_result['hard']
    soft_warnings = preflight_result['soft']
    if not hard_errors and not soft_warnings:
        print("  All contract checks PASS")
    else:
        if hard_errors:
            print(f"  ⛔ {len(hard_errors)} HARD error(s) found:")
            for h in hard_errors:
                print(f"    [HARD] {h}")
            print("  These will cause structural bugs in the output .docx.")
            if '--strict' in sys.argv:
                print("  [STRICT MODE] Exiting.")
                sys.exit(1)
        if soft_warnings:
            print(f"  {len(soft_warnings)} soft warning(s) found — proceeding")
    print()

    # --- Replace front matter in template ---
    if title_para is not None and title_text:
        replace_title(title_para, title_text)

    if abstract_paras and abstract_text:
        replace_abstract(abstract_paras[-1], abstract_text)

    if keywords_para is not None and kw_text != 'Keywords—':
        replace_keywords(keywords_para, kw_text)

    print(f"Preserved {len(author_paras)} author + {len(affiliation_paras)} affiliation paragraphs")

    # --- Clear body content between Keywords and references-sectPr ---
    anchor = keywords_para
    to_remove = []
    current = anchor.getnext()
    while current is not None and current != refs_sectPr_para:
        if current.tag == '{%s}p' % W_NS and paragraph_has_sectPr(current):
            clear_paragraph_text(current)
        else:
            to_remove.append(current)
        current = current.getnext()
    for elem in to_remove:
        body.remove(elem)
    print(f"Removed {len(to_remove)} elements between Keywords and references-sectPr")

    # --- Extract body lines and references from markdown ---
    body_lines, ref_lines = extract_body_and_refs(lines)
    body_lines = join_multiline_equations(body_lines)
    body_lines = strip_blank_lines_around_blocks(body_lines)
    body_lines, ref_entries = renumber_references(body_lines, ref_lines)

    # --- Renumber equations to sequential order ---
    md = renumber_equations(md)
    # Also renumber in body_lines (already extracted from pre-renumber md)
    eq_renum_pat = re.compile(re.escape(chr(92)) + r'tag\{eq:(\d+)\}')
    eq_matches_body = []
    for idx, line in enumerate(body_lines):
        for m in eq_renum_pat.finditer(line):
            eq_matches_body.append((idx, m.start(), m.end(), m.group(1)))
    if eq_matches_body:
        num_map = {}
        for i, (_, _, _, old) in enumerate(eq_matches_body):
            num_map[old] = str(i + 1)
        for idx, start, end, old in reversed(eq_matches_body):
            new = num_map[old]
            line = body_lines[idx]
            body_lines[idx] = line[:start] + r'\tag{eq:' + new + '}' + line[end:]

    # --- Convert equations ---
    omml_cache = extract_and_convert_equations(md)

    # --- Extract markdown tables from body lines ---
    md_tables, caption_set, body_lines = extract_md_tables(body_lines)

    # --- Insert body content ---
    anchor = keywords_para
    para_count = 0
    eq_count = 0
    fig_count = 0
    tables_inserted = 0
    current_paragraph = []

    def ins(element):
        nonlocal anchor
        anchor.addnext(element)
        anchor = element
        return element

    def flush_para_and_try_table():
        nonlocal para_count, tables_inserted
        if not current_paragraph:
            return
        text = ' '.join(current_paragraph).strip()
        if not text:
            return
        # Skip table captions — they'll be inserted by make_data_table.
        # Strip ** bold markers for comparison since caption_set has them removed.
        norm_text = re.sub(r'\*\*(.+?)\*\*', r'\1', text).strip()
        is_caption = norm_text in caption_set
        if not is_caption:
            ins(make_para_with_formatting('a3', text)); para_count += 1
        # Match pending tables by caption (exact match on normalized text,
        # or prefix match when trailing content follows the caption).
        for tbl_info in md_tables:
            _, _, headers, rows, caption = tbl_info
            if caption and caption not in [t[4] for t in md_tables[:tables_inserted]]:
                cap_clean = re.sub(r'\*\*(.+?)\*\*', r'\1', caption).strip()
                if norm_text == cap_clean or norm_text.startswith(cap_clean + ' '):
                    for e in make_data_table(headers, rows, caption):
                        ins(e); para_count += 1
                    tables_inserted += 1
                    break

    i = 0
    while i < len(body_lines):
        line = body_lines[i].rstrip()

        if line.strip() == '---':
            i += 1
            continue

        # H1 heading: use the template style and strip the Markdown readability prefix.
        if line.startswith('## '):
            flush_para_and_try_table()
            current_paragraph = []
            heading = re.sub(r'^[IVX]+\.\s+', '', line[3:].strip())
            ins(make_para('1', heading)); para_count += 1
            i += 1
            continue

        # H2 heading: use the template style and strip the Markdown readability prefix.
        if line.startswith('### '):
            flush_para_and_try_table()
            current_paragraph = []
            heading = re.sub(r'^[A-Z]\.\s+', '', line[4:].strip())
            ins(make_para('2', heading)); para_count += 1
            i += 1
            continue

        # Figure
        fig_match = re.match(r'!\[Fig\.\s*(\d+)\.\s*(.+?)\]\((.+?)\)', line)
        if fig_match:
            flush_para_and_try_table()
            current_paragraph = []

            fig_num = fig_match.group(1)
            fig_caption = fig_match.group(2).strip()
            fig_file = fig_match.group(3).strip()
            fig_path = os.path.join(FIG_DIR, fig_file)

            if os.path.exists(fig_path) and check_image(fig_path):
                img_para = parse_xml('<w:p %s/>' % nsdecls('w'))
                pPr = parse_xml('<w:pPr %s><w:jc w:val="center"/><w:ind w:firstLine="0"/></w:pPr>' % nsdecls('w'))
                img_para.insert(0, pPr)

                doc_part = doc.part
                rId, _ = doc_part.get_or_add_image(fig_path)
                pil_img = Image.open(fig_path)
                w_px, h_px = pil_img.size
                width_emu = int(FIG_WIDTH_INCHES * 914400)
                height_emu = int(width_emu * h_px / w_px)
                drawing = parse_xml(create_inline_drawing(rId, width_emu, height_emu))
                r = parse_xml('<w:r %s/>' % nsdecls('w'))
                r.append(drawing)
                img_para.append(r)
                ins(img_para); para_count += 1

                # Caption AFTER image. The figurecaption style auto-numbers.
                ins(make_para('figurecaption', fig_caption))
                para_count += 1
                fig_count += 1
            else:
                print(f"  Skipping figure {fig_file}")
            i += 1
            continue

        # Display equation
        eq_match = re.match(r'\$\$(.+?)' + re.escape(chr(92)) + r'tag\{eq:(\d+)\}\s*\$\$', line)
        if eq_match:
            flush_para_and_try_table()
            current_paragraph = []
            eq_num = eq_match.group(2)
            if eq_num in omml_cache:
                ins(make_equation_table(omml_cache[eq_num], eq_num)); eq_count += 1
            i += 1
            continue

        # Regular text
        stripped = line.strip()
        if stripped == '':
            flush_para_and_try_table()
            current_paragraph = []
        else:
            # ── Caption fallback guard ──
            # If accumulated text is a table caption and the next line is a table row,
            # flush now — otherwise the caption gets buried in current_paragraph
            # and flush_para_and_try_table can't match it to a table.
            acc_text = ' '.join(current_paragraph).strip() if current_paragraph else ''
            acc_norm = re.sub(r'\*\*(.+?)\*\*', r'\1', acc_text).strip()
            if current_paragraph and stripped.startswith('|') and re.match(r'(?i)table\s+[IVXLCDM0-9]+\.?\s', acc_norm):
                for tbl_info in md_tables:
                    _, _, headers, rows, caption = tbl_info
                    if caption and tbl_info not in md_tables[:tables_inserted]:
                        cap_clean = re.sub(r'\*\*(.+?)\*\*', r'\1', caption).strip()
                        cap_core = re.sub(r'(?i)^[Tt][Aa][Bb][Ll][Ee]\s+[IVXLCDM0-9]+\.?\s*', '', cap_clean).strip()
                        acc_core = re.sub(r'(?i)^[Tt][Aa][Bb][Ll][Ee]\s+[IVXLCDM0-9]+\.?\s*', '', acc_norm).strip()
                        if acc_core == cap_core or acc_norm == cap_clean:
                            current_paragraph = []
                            for e in make_data_table(headers, rows, caption):
                                ins(e); para_count += 1
                            tables_inserted += 1
                            break
            current_paragraph.append(stripped)
        i += 1

    flush_para_and_try_table()

    # Insert any unmatched markdown tables at end
    for tbl_idx, tbl_info in enumerate(md_tables):
        _, _, headers, rows, caption = tbl_info
        if tbl_idx >= tables_inserted:
            print(f"  WARNING: Table '{caption or '(no caption)'}' not matched to body text, appending at end")
            for e in make_data_table(headers, rows, caption):
                ins(e); para_count += 1

    # --- References section ---
    ins(build_ref_heading()); para_count += 1
    for new_num, ref_body in ref_entries:
        ins(make_para_with_formatting('references', ref_body)); para_count += 1

    if refs_sectPr_para is not None and refs_sectPr_para.getparent() is not None:
        print("Preserved References section-break placeholder")

    # --- Post-processing ---
    for elem in body.iter('{%s}p' % W_NS):
        if paragraph_style(elem) in ('Author', 'Affiliation'):
            continue
        clean_chinese_from_element(elem)
    print("Cleaned Chinese characters")

    for tbl in body.findall('{%s}tbl' % W_NS):
        strip_cell_indent(tbl)
    print("Stripped cell indentation")

    doc.save(OUTPUT)
    print(f"\nSaved to {OUTPUT}")
    print(f"\n=== Summary ===")
    print(f"Figures inserted: {fig_count}")
    print(f"Equations inserted: {eq_count}")
    print(f"Paragraphs/elements inserted: {para_count}")
    print(f"References inserted: {len(ref_entries)}")


if __name__ == '__main__':
    main()
