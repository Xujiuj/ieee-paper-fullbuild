"""
Extract content from a .docx file to Markdown format.

Usage:
    python extract_docx.py <input.docx> <output.md> [figures_dir]

Extracts:
- Title (first large/bold paragraph)
- Headings (Heading 1/2/3)
- Body paragraphs
- Tables (to markdown table syntax)
- Images (to figures_dir, referenced in markdown)
"""
import os, re, sys, zipfile
from docx import Document
from docx.oxml.ns import qn

W_NS = 'http://schemas.openxmlformats.org/wordprocessingml/2006/main'
M_NS = 'http://schemas.openxmlformats.org/officeDocument/2006/math'
R_NS = 'http://schemas.openxmlformats.org/officeDocument/2006/relationships'

if len(sys.argv) < 3:
    print("Usage: python extract_docx.py <input.docx> <output.md> [figures_dir]")
    sys.exit(1)

input_docx = sys.argv[1]
output_md = sys.argv[2]
figures_dir = sys.argv[3] if len(sys.argv) > 3 else os.path.join(os.path.dirname(output_md), 'figures')

os.makedirs(figures_dir, exist_ok=True)

doc = Document(input_docx)
body = doc.element.body

# Extract images from docx zip
z = zipfile.ZipFile(input_docx)
media_files = [f for f in z.namelist() if f.startswith('word/media/')]
img_map = {}  # rId -> filename
for rel_name, rel in doc.part.rels.items():
    if hasattr(rel, 'target_ref') and 'media/' in str(rel.target_ref):
        media_name = 'word/' + str(rel.target_ref)
        if media_name in media_files:
            ext = os.path.splitext(media_name)[1]
            out_name = f"fig_{len(img_map) + 1}{ext}"
            out_path = os.path.join(figures_dir, out_name)
            with open(out_path, 'wb') as f:
                f.write(z.read(media_name))
            img_map[rel_name] = out_name

md_lines = []
fig_counter = 0

for elem in body:
    tag = elem.tag.split('}')[-1] if '}' in elem.tag else elem.tag

    if tag == 'p':
        pPr = elem.find('{%s}pPr' % W_NS)
        style = ''
        if pPr is not None:
            pStyle = pPr.find('{%s}pStyle' % W_NS)
            if pStyle is not None:
                style = pStyle.get('{%s}val' % W_NS, '')

        text = ''.join(t.text or '' for t in elem.iter('{%s}t' % W_NS))

        # Check for images in this paragraph
        for blip in elem.iter():
            if blip.tag.endswith('}blip'):
                r_embed = blip.get('{%s}embed' % R_NS)
                if r_embed and r_embed in img_map:
                    fig_counter += 1
                    md_lines.append(f"![Fig. {fig_counter}. Figure {fig_counter}]({img_map[r_embed]})")
                    md_lines.append("")

        # Check for OMML equations
        omath = elem.find('{%s}oMath' % M_NS)
        if omath is not None:
            md_lines.append("$$ [equation] $$")
            md_lines.append("")
            continue

        if not text.strip():
            continue

        # Style-based formatting
        if style in ('Heading1', '1', 'Title'):
            md_lines.append(f"# {text.strip()}")
            md_lines.append("")
        elif style in ('Heading2', '2'):
            md_lines.append(f"## {text.strip()}")
            md_lines.append("")
        elif style in ('Heading3', '3'):
            md_lines.append(f"### {text.strip()}")
            md_lines.append("")
        elif style == 'papertitle':
            md_lines.append(f"# {text.strip()}")
            md_lines.append("")
        elif style == 'Abstract':
            md_lines.append("## Abstract")
            md_lines.append("")
            md_lines.append(text.strip())
            md_lines.append("")
        elif style in ('Author', 'Affiliation'):
            continue  # Skip; template preserves these
        elif style == 'references':
            md_lines.append(text.strip())
            md_lines.append("")
        else:
            md_lines.append(text.strip())
            md_lines.append("")

    elif tag == 'tbl':
        rows = []
        for tr in elem.findall('{%s}tr' % W_NS):
            cells = []
            for tc in tr.findall('{%s}tc' % W_NS):
                cell_text = ''.join(t.text or '' for t in tc.iter('{%s}t' % W_NS))
                cells.append(cell_text.strip())
            if cells:
                rows.append(cells)

        if rows:
            n_cols = max(len(r) for r in rows)
            for r in rows:
                while len(r) < n_cols:
                    r.append('')
            md_lines.append('| ' + ' | '.join(rows[0]) + ' |')
            md_lines.append('| ' + ' | '.join(['---'] * n_cols) + ' |')
            for row in rows[1:]:
                md_lines.append('| ' + ' | '.join(row) + ' |')
            md_lines.append("")

with open(output_md, 'w', encoding='utf-8') as f:
    f.write('\n'.join(md_lines))

print(f"Extracted to {output_md}")
print(f"  Sections: {sum(1 for l in md_lines if l.startswith('# '))}")
print(f"  Tables: {sum(1 for l in md_lines if l.startswith('| '))}")
print(f"  Figures: {fig_counter}")
print(f"  Images saved to: {figures_dir}")
