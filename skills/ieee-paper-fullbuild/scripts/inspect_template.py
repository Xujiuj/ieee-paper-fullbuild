#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Template inspector.

Extracts style IDs, auto-numbering map, sectPr layout, table border size,
and original Author/Affiliation paragraph text from an IEEE template.

Usage:
    python inspect_template.py <template.docx> [output.json]

If output.json is provided, writes the inspection report there.
Otherwise prints to stdout.
"""
import zipfile, re, sys, json

REQUIRED_STYLES = ('papertitle', 'Author', 'Affiliation', 'Abstract',
                   'Keywords', '1', '2', '3', 'a3', 'figurecaption',
                   'tablehead', 'references', 'equation')

def inspect(template_docx):
    z = zipfile.ZipFile(template_docx)
    styles_xml = z.read('word/styles.xml').decode('utf-8')
    doc_xml = z.read('word/document.xml').decode('utf-8')

    report = {'template': template_docx, 'styles': {}, 'sectPr_map': [],
              'table_border_sz': None, 'authors': [], 'affiliations': []}

    for sid in REQUIRED_STYLES:
        m = re.search(rf'<w:style[^>]*w:styleId="{sid}".*?</w:style>',
                      styles_xml, re.DOTALL)
        if m:
            s = m.group()
            num_id_m = re.search(r'<w:numId w:val="(\d+)"', s)
            report['styles'][sid] = {
                'present': True,
                'numId': num_id_m.group(1) if num_id_m else None,
                'auto_numbered': bool(num_id_m and num_id_m.group(1) != '0'),
            }
        else:
            report['styles'][sid] = {'present': False}

    sects = re.findall(r'<w:sectPr[^>]*>.*?</w:sectPr>', doc_xml, re.DOTALL)
    for i, s in enumerate(sects):
        cols = re.search(r'<w:cols([^/]*)/>', s)
        cols_attr = cols.group(1).strip() if cols else ''
        is_two = 'w:num="2"' in s
        report['sectPr_map'].append({
            'index': i,
            'cols': cols_attr,
            'two_column': is_two,
        })

    tblB = re.findall(r'<w:tblBorders>.*?</w:tblBorders>', doc_xml, re.DOTALL)
    if tblB:
        sz = re.search(r'w:sz="(\d+)"', tblB[0])
        report['table_border_sz'] = sz.group(1) if sz else None

    paras = re.findall(r'<w:p[^>]*>.*?</w:p>', doc_xml, re.DOTALL)
    for p in paras:
        if '<w:pStyle w:val="Author"/>' in p:
            txt = ''.join(re.findall(r'<w:t[^>]*>(.*?)</w:t>', p, re.DOTALL))
            cleaned = re.sub(r'[一-鿿（）]+|[À-ÿ]{3,}', '', txt).strip()
            if cleaned:
                report['authors'].append(cleaned)
        elif '<w:pStyle w:val="Affiliation"/>' in p:
            txt = ''.join(re.findall(r'<w:t[^>]*>(.*?)</w:t>', p, re.DOTALL))
            cleaned = re.sub(r'[一-鿿（）]+|[À-ÿ]{3,}', '', txt).strip()
            if cleaned:
                report['affiliations'].append(cleaned)

    return report

if __name__ == '__main__':
    if len(sys.argv) < 2 or len(sys.argv) > 3:
        print("Usage: python inspect_template.py <template.docx> [output.json]",
              file=sys.stderr)
        sys.exit(2)
    template = sys.argv[1]
    report = inspect(template)
    if len(sys.argv) == 3:
        with open(sys.argv[2], 'w', encoding='utf-8') as f:
            json.dump(report, f, indent=2, ensure_ascii=False)
        print(f"Wrote {sys.argv[2]}")
    else:
        print(json.dumps(report, indent=2, ensure_ascii=False))
