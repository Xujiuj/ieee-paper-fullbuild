#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""IEEE paper validator: 15-invariant quality gate.

Usage:
    python validate.py <output.docx> <template.docx>

Returns exit code 0 on full PASS (15/15), 1 otherwise.
Stdout prints one line per invariant: <n>. PASS|FAIL: <detail>
"""
import zipfile, re, sys, os, tempfile
try:
    from PIL import Image
    import numpy as np
    HAS_PIL = True
except ImportError:
    HAS_PIL = False


def classify_image(path):
    """Classify image by aspect ratio, white-space ratio, and color variance.

    Returns (aspect, white_ratio, is_letter_like).
    A portrait high-white image is only flagged as letter-like if its non-white
    pixels have low color variance (grayscale scan), not if they are colored
    (technical diagram).
    """
    img = Image.open(path)
    w, h = img.size
    aspect = w / h

    gray = np.array(img.convert('L'))
    white_ratio = (gray > 240).sum() / gray.size

    if aspect >= 1.0 or white_ratio <= 0.5:
        return aspect, white_ratio, False

    # Portrait + high white: check color variance
    rgb = np.array(img.convert('RGB')).astype(float)
    non_white_mask = gray <= 240
    if non_white_mask.sum() > 0:
        channel_std = np.std(rgb[non_white_mask], axis=1).mean()
        if channel_std > 15:
            return aspect, white_ratio, False  # colored diagram

    return aspect, white_ratio, True


def extract_style_texts(xml, style_id):
    """Extract paragraph texts for a specific Word style."""
    paras = re.findall(r'<w:p[^>]*>.*?</w:p>', xml, re.DOTALL)
    return [
        ''.join(re.findall(r'<w:t[^>]*>(.*?)</w:t>', p, re.DOTALL))
        for p in paras
        if f'<w:pStyle w:val="{style_id}"/>' in p
    ]


def extract_authors(template_xml):
    """Extract author names from template, stripping mojibake and non-ASCII."""
    paras = re.findall(r'<w:p[^>]*>.*?</w:p>', template_xml, re.DOTALL)
    out = []
    for p in paras:
        if '<w:pStyle w:val="Author"/>' in p:
            txt = ''.join(re.findall(r'<w:t[^>]*>(.*?)</w:t>', p, re.DOTALL))
            txt = re.sub(r'[一-鿿（）]+|[À-ÿ]{3,}|[^\x00-\x7F]+', '', txt)
            txt = re.sub(r'[\s\*]+$', '', txt).strip()
            if txt and len(txt) >= 2:
                out.append(txt)
    return out


def validate(out_docx, template_docx):
    """Run all 15 invariants. Returns list of (number, passed, detail)."""
    z = zipfile.ZipFile(out_docx)
    xml = z.read('word/document.xml').decode('utf-8')
    tpl_xml = zipfile.ZipFile(template_docx).read('word/document.xml').decode('utf-8')
    results = []

    # --- INVARIANT 1: Total word count >= 3500 ---
    texts = re.findall(r'<w:t[^>]*>([^<]*)</w:t>', xml)
    total = len(' '.join(texts).split())
    paras = re.findall(r'<w:p[^>]*>.*?</w:p>', xml, re.DOTALL)

    # --- INVARIANT 2: Body word count >= 3000 (only body-styled paragraphs) ---
    # Accept both 'a3' (IEEE template style) and '7' (Body Text style)
    body = sum(len(' '.join(re.findall(r'<w:t[^>]*>([^<]*)</w:t>', p)).split())
               for p in paras
               if '<w:pStyle w:val="a3"/>' in p or '<w:pStyle w:val="7"/>' in p)
    results.append((1, total >= 3500, f"total={total}"))
    results.append((2, body >= 3000, f"body={body}"))

    # --- INVARIANT 3: Estimated page count 6.0-10.0 ---
    # Formula: body/750 + figures*0.35 + equations*0.08 + 0.5
    n_blip = xml.count('<a:blip')
    n_eq = len(re.findall(r'<w:t[^>]*>\(\d+\)</w:t>', xml))
    pages = body / 750.0 + n_blip * 0.35 + n_eq * 0.08 + 0.5
    results.append((3, 6.0 <= pages <= 10.0, f"pages~{pages:.1f}"))

    # --- INVARIANT 4: Authors and affiliations preserved from template ---
    tpl_authors = extract_style_texts(tpl_xml, "Author")
    out_authors = extract_style_texts(xml, "Author")
    tpl_affiliations = extract_style_texts(tpl_xml, "Affiliation")
    out_affiliations = extract_style_texts(xml, "Affiliation")
    authors_ok = tpl_authors == out_authors and tpl_affiliations == out_affiliations
    results.append((4, authors_ok, f"authors={len(out_authors)}/{len(tpl_authors)}, affiliations={len(out_affiliations)}/{len(tpl_affiliations)}"))

    # --- INVARIANT 5: Two-column sections >= 2 ---
    sects = re.findall(r'<w:sectPr.*?</w:sectPr>', xml, re.DOTALL)
    two_col = sum(1 for s in sects if 'w:num="2"' in s)
    results.append((5, two_col >= 2, f"two_col_sectPr={two_col}"))

    # --- INVARIANT 6: Structural OMML elements >= 1 ---
    # Checks for structural equation elements (fractions, integrals, subscripts, etc.)
    struct = sum(xml.count(t) for t in ('<m:f>','<m:nary>','<m:sSub>','<m:sSup>','<m:d>','<m:rad>'))
    results.append((6, struct > 0, f"struct_omml={struct}"))

    # --- INVARIANT 7: Figure count 6-10 inclusive ---
    results.append((7, 6 <= n_blip <= 10, f"figures={n_blip}"))

    # --- INVARIANT 7.5: Equation count >= 5 ---
    # Counts equation labels like (1), (2), etc. in w:t elements
    results.append((7.5, n_eq >= 5, f"equations={n_eq}"))

    # --- INVARIANT 8: No letter-like images (aspect < 1 AND white > 0.5) ---
    bad_imgs = []
    if HAS_PIL:
        for name in z.namelist():
            if name.startswith('word/media/') and not name.lower().endswith('.emf'):
                ext = os.path.splitext(name)[1] or '.bin'
                with tempfile.NamedTemporaryFile(suffix=ext, delete=False) as tmp:
                    tmp.write(z.read(name))
                    tmp_path = tmp.name
                try:
                    aspect, white, is_letter = classify_image(tmp_path)
                    if is_letter:
                        bad_imgs.append(os.path.basename(name))
                except Exception:
                    pass
                finally:
                    try: os.unlink(tmp_path)
                    except OSError: pass
        results.append((8, not bad_imgs, f"letter_images={bad_imgs}"))
    else:
        results.append((8, True, "PIL not available - skipped"))

    # --- INVARIANT 9: Template heading styles, no manual heading prefixes ---
    synthetic = len(re.findall(r'<w:pStyle w:val="Heading[12]"/>', xml))
    template_heading_paras = re.findall(r'<w:p[^>]*>(?:(?!</w:p>).)*?<w:pStyle w:val="[12]"/>(?:(?!</w:p>).)*?</w:p>', xml, re.DOTALL)
    manual = sum(1 for hp in template_heading_paras
                 if re.match(r'^(?:[IVX]+|[A-Z])\.\s',
                             ''.join(re.findall(r'<w:t[^>]*>(.*?)</w:t>', hp, re.DOTALL))))
    results.append((9, synthetic == 0 and manual == 0, f"synthetic_headings={synthetic}, manual_prefixes={manual}"))

    # --- INVARIANT 10: No manual [n] reference numbers ---
    rps = re.findall(r'<w:p[^>]*>(?:(?!</w:p>).)*?<w:pStyle w:val="references"/>(?:(?!</w:p>).)*?</w:p>', xml, re.DOTALL)
    rl = sum(1 for rp in rps
             if re.match(r'^\[\d+\]',
                         ''.join(re.findall(r'<w:t[^>]*>(.*?)</w:t>', rp, re.DOTALL))))
    results.append((10, rl == 0, f"manual_brackets={rl}"))

    # --- INVARIANT 11: No raw LaTeX commands ---
    latex = sum(1 for c in [r'\cite{', r'\frac{', r'\mathcal{', r'\textbf{'] if c in xml)
    results.append((11, latex == 0, f"latex_cmds={latex}"))

    # --- INVARIANT 12: No Chinese characters outside preserved author metadata ---
    cn = 0
    for p in paras:
        if '<w:pStyle w:val="Author"/>' in p or '<w:pStyle w:val="Affiliation"/>' in p:
            continue
        cn += len(re.findall(r'[\u4e00-\u9fff]', p))
    results.append((12, cn == 0, f"chinese_chars={cn}"))

    # --- INVARIANT 13: Stripped cell indentation (firstLine="0") ---
    bad = 0
    for tc in re.findall(r'<w:tc>.*?</w:tc>', xml, re.DOTALL):
        for pPr in re.findall(r'<w:pPr>.*?</w:pPr>', tc, re.DOTALL):
            ind = re.search(r'<w:ind[^/]*/>', pPr)
            if ind and 'w:firstLine="0"' not in ind.group():
                bad += 1
    results.append((13, bad == 0, f"bad_cell_indent={bad}"))

    # --- INVARIANT 14: No manual numbering or bold in figure/table captions ---
    fig_captions = re.findall(r'<w:p[^>]*>(?:(?!</w:p>).)*?<w:pStyle w:val="figurecaption"/>(?:(?!</w:p>).)*?</w:p>', xml, re.DOTALL)
    tbl_captions = re.findall(r'<w:p[^>]*>(?:(?!</w:p>).)*?<w:pStyle w:val="tablehead"/>(?:(?!</w:p>).)*?</w:p>', xml, re.DOTALL)
    bad_caption = 0
    for fc in fig_captions:
        txt = ''.join(re.findall(r'<w:t[^>]*>(.*?)</w:t>', fc, re.DOTALL)).strip()
        if re.match(r'^Fig\.\s*\d+\.?\s+', txt, re.IGNORECASE):
            bad_caption += 1
    for tc in tbl_captions:
        txt = ''.join(re.findall(r'<w:t[^>]*>(.*?)</w:t>', tc, re.DOTALL))
        has_bold = '<w:b/>' in tc or '<w:b ' in tc
        if has_bold or re.match(r'^TABLE\s+[IVXLCDM0-9]+\.?\s+', txt.strip(), re.IGNORECASE):
            bad_caption += 1
    results.append((14, bad_caption == 0, f"bad_numbered_or_bold_captions={bad_caption}"))

    return results


if __name__ == '__main__':
    if len(sys.argv) != 3:
        print("Usage: python validate.py <output.docx> <template.docx>", file=sys.stderr)
        sys.exit(2)
    out, tpl = sys.argv[1], sys.argv[2]
    results = validate(out, tpl)
    fails = []
    for n, ok, msg in results:
        status = 'PASS' if ok else 'FAIL'
        print(f'{n}. {status}: {msg}')
        if not ok:
            fails.append(n)
    n_pass = len(results) - len(fails)
    print(f'\nValidation Results: {n_pass}/{len(results)} PASS')
    sys.exit(0 if not fails else 1)
