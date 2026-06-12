#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""IEEE Markdown Validator — Pre-conversion format gate.

Validates paper.md against MarkdownOutputContract C1-C10 + structural rules
BEFORE format_ieee.py runs. This is Layer 1 of the Phase 3.5 dual validation.

Usage:
    python validate_md.py <paper.md>

Exit codes:
    0 = All checks PASS
    1 = HARD failures (BLOCK — do not run format_ieee.py)
    2 = SOFT warnings only (proceed with caution)
"""
import re
import sys
import os


# ============================================================================
# Check functions — each returns (id, level, passed, message)
# ============================================================================

def check_c1_abstract(md_text):
    """C1: **Abstract** — format exists."""
    if re.search(r'\*\*Abstract\*\*\s*[—–\-]', md_text):
        return ('C1', 'HARD', True, '**Abstract** — format found')
    return ('C1', 'HARD', False, 'Missing **Abstract** — format (must be **Abstract** — text, NOT ## Abstract)')

def check_c1_no_heading(md_text):
    """C1b: No ## Abstract heading."""
    if re.search(r'^##\s+Abstract', md_text, re.MULTILINE | re.IGNORECASE):
        return ('C1b', 'HARD', False, 'Found ## Abstract heading — use **Abstract** — format instead')
    return ('C1b', 'HARD', True, 'No ## Abstract heading (correct)')

def check_c2_keywords(md_text):
    """C2: **Keywords** — format exists."""
    if re.search(r'\*\*Keywords?\*\*\s*[—–\-]', md_text, re.IGNORECASE):
        return ('C2', 'HARD', True, '**Keywords** — format found')
    return ('C2', 'HARD', False, 'Missing **Keywords** — format (must be **Keywords** — term1, term2, ...)')

def check_c3a_h1_headings(md_text):
    """C3a: All ## headings start with Roman numeral."""
    exceptions = {'## REFERENCES', '## ACKNOWLEDGMENT'}
    bad = []
    for m in re.finditer(r'^## (.+)$', md_text, re.MULTILINE):
        heading = m.group(0).strip()
        if heading.upper() in exceptions or heading.upper().startswith('## ACKNOWLEDGMENT'):
            continue
        if not re.match(r'^## [IVX]+\.\s+', heading):
            bad.append(heading[:60])
    if bad:
        return ('C3a', 'HARD', False, f'H1 headings without Roman numeral: {bad[:5]}')
    return ('C3a', 'HARD', True, 'All H1 headings have Roman numeral prefix')

def check_c3b_h2_headings(md_text):
    """C3b: All ### headings start with Letter."""
    bad = []
    for m in re.finditer(r'^### (.+)$', md_text, re.MULTILINE):
        heading = m.group(0).strip()
        if not re.match(r'^### [A-Z]\.\s+', heading):
            bad.append(heading[:60])
    if bad:
        return ('C3b', 'HARD', False, f'H2 headings without Letter prefix: {bad[:5]}')
    return ('C3b', 'HARD', True, 'All H2 headings have Letter prefix')

def check_c4a_figure_numbers(md_text):
    """C4a: Figure numbers sequential from 1, no gaps."""
    fig_nums = sorted([int(x) for x in re.findall(r'!\[Fig\.\s*(\d+)\.', md_text)])
    if not fig_nums:
        return ('C4a', 'SOFT', True, 'No figures found (ok if not applicable)')
    expected = list(range(1, len(fig_nums) + 1))
    if fig_nums == expected:
        return ('C4a', 'HARD', True, f'Figure numbers sequential: {fig_nums}')
    return ('C4a', 'HARD', False, f'Figure numbers not sequential: found {fig_nums}, expected {expected}')

def check_c4b_figure_caption_length(md_text):
    """C4b: Figure captions <=12 words."""
    captions = re.findall(r'!\[Fig\.\s*\d+\.\s*(.+?)\]', md_text)
    long = [c for c in captions if len(c.split()) > 12]
    if long:
        return ('C4b', 'HARD', False, f'Figure captions >12 words: {[c[:40]+"..." if len(c)>40 else c for c in long[:3]]}')
    if captions:
        return ('C4b', 'HARD', True, f'All {len(captions)} figure captions <=12 words')
    return ('C4b', 'HARD', True, 'No figure captions to check')

def check_c4c_figure_caption_punct(md_text):
    """C4c: Figure captions no trailing punctuation."""
    captions = re.findall(r'!\[Fig\.\s*\d+\.\s*(.+?)\]', md_text)
    bad = [c for c in captions if re.search(r'[.,;:!?]$', c.strip())]
    if bad:
        return ('C4c', 'HARD', False, f'Figure captions end with punctuation: {bad[:3]}')
    return ('C4c', 'HARD', True, 'No figure captions end with punctuation')

def check_c4d_figure_filename(md_text):
    """C4d: Figure filenames match figN_name.png pattern."""
    figs = re.findall(r'!\[Fig\.\s*(\d+)\.\s*.+?\]\((.+?)\)', md_text)
    bad = []
    for num, filename in figs:
        if not re.match(rf'fig{num}_', filename):
            bad.append(f'Fig.{num} -> {filename}')
    if bad:
        return ('C4d', 'HARD', False, f'Figure filename mismatch: {bad[:3]}')
    return ('C4d', 'HARD', True, 'All figure filenames match figN_name.png pattern')

def check_c5a_table_caption_format(md_text):
    """C5a: Table captions have **TABLE N. Title** format."""
    table_lines = [m.start() for m in re.finditer(r'^\|.+\|', md_text, re.MULTILINE)]
    if not table_lines:
        return ('C5a', 'SOFT', True, 'No tables found')
    captions = re.findall(r'\*\*TABLE\s+[IVXLCDM]+\.?\s*.+?\*\*', md_text)
    if not captions:
        return ('C5a', 'HARD', False, 'Tables found but no **TABLE N. Title** captions detected')
    return ('C5a', 'HARD', True, f'Found {len(captions)} TABLE captions with correct format')

def check_c5b_table_caption_length(md_text):
    """C5b: Table captions <=8 words (title part only)."""
    titles = re.findall(r'\*\*TABLE\s+[IVXLCDM]+\.?\s*(.+?)\*\*', md_text)
    long = [t for t in titles if len(t.split()) > 8]
    if long:
        return ('C5b', 'HARD', False, f'Table titles >8 words: {long[:3]}')
    if titles:
        return ('C5b', 'HARD', True, f'All {len(titles)} table titles <=8 words')
    return ('C5b', 'HARD', True, 'No table titles to check')

def check_c5c_table_caption_punct(md_text):
    """C5c: Table captions no trailing punctuation."""
    titles = re.findall(r'\*\*TABLE\s+[IVXLCDM]+\.?\s*(.+?)\*\*', md_text)
    bad = [t for t in titles if re.search(r'[.,;:!?]$', t.strip())]
    if bad:
        return ('C5c', 'HARD', False, f'Table titles end with punctuation: {bad[:3]}')
    return ('C5c', 'HARD', True, 'No table titles end with punctuation')

def check_c5d_table_blank_line(md_text):
    """C5d: TABLE caption and data rows separated by blank line."""
    lines = md_text.split('\n')
    issues = []
    for i, line in enumerate(lines):
        if re.match(r'\*\*TABLE\s+[IVXLCDM]', line.strip()):
            if i + 1 < len(lines) and lines[i + 1].strip() != '':
                issues.append(f'Line {i+1}: no blank line after TABLE caption')
    if issues:
        return ('C5d', 'HARD', False, '; '.join(issues[:3]))
    return ('C5d', 'HARD', True, 'TABLE captions have blank line before data')

def check_c6a_equation_tags(md_text):
    """C6a: Equations have \\tag{eq:N}."""
    eq_blocks = re.findall(r'\$\$(.+?)\$\$', md_text, re.DOTALL)
    if not eq_blocks:
        return ('C6a', 'HARD', False, 'No $$...$$ equation blocks found')
    missing = sum(1 for b in eq_blocks if '\\tag{eq:' not in b)
    if missing:
        return ('C6a', 'HARD', False, f'{missing} equation block(s) missing \\tag{{eq:N}}')
    return ('C6a', 'HARD', True, f'All {len(eq_blocks)} equations have \\tag{{eq:N}}')

def check_c6b_equation_count(md_text):
    """C6b: >=5 equations."""
    tags = re.findall(r'\\tag\{eq:(\d+)\}', md_text)
    if len(tags) >= 5:
        return ('C6b', 'HARD', True, f'{len(tags)} equations found (>=5)')
    return ('C6b', 'HARD', False, f'Only {len(tags)} equations found (need >=5)')

def check_c6c_equation_numbers(md_text):
    """C6c: Equation numbers sequential."""
    nums = sorted([int(x) for x in re.findall(r'\\tag\{eq:(\d+)\}', md_text)])
    if not nums:
        return ('C6c', 'SOFT', True, 'No equations to number')
    expected = list(range(1, len(nums) + 1))
    if nums == expected:
        return ('C6c', 'HARD', True, f'Equation numbers sequential: {nums}')
    return ('C6c', 'HARD', False, f'Equation numbers not sequential: found {nums}, expected {expected}')

def check_c7_references(md_text):
    """C7: References <=15."""
    refs_match = re.search(r'## REFERENCES\s*\n(.*?)$', md_text, re.DOTALL | re.IGNORECASE)
    if not refs_match:
        return ('C7', 'HARD', False, 'No ## REFERENCES section found')
    ref_count = len(re.findall(r'^\[\d+\]', refs_match.group(1), re.MULTILINE))
    if ref_count == 0:
        return ('C7', 'HARD', False, '## REFERENCES section is empty')
    if ref_count <= 15:
        return ('C7', 'HARD', True, f'{ref_count} references (<=15)')
    return ('C7', 'HARD', False, f'{ref_count} references exceeds maximum of 15')

def check_c7_no_duplicate_refs(md_text):
    """C7b: No duplicate reference numbers."""
    refs_match = re.search(r'## REFERENCES\s*\n(.*?)$', md_text, re.DOTALL | re.IGNORECASE)
    if not refs_match:
        return ('C7b', 'HARD', True, 'No REFERENCES to check')
    nums = [int(x) for x in re.findall(r'^\[(\d+)\]', refs_match.group(1), re.MULTILINE)]
    if len(nums) != len(set(nums)):
        dupes = [n for n in set(nums) if nums.count(n) > 1]
        return ('C7b', 'HARD', False, f'Duplicate reference numbers: {dupes}')
    return ('C7b', 'HARD', True, 'No duplicate reference numbers')

def check_c9a_figure_cross_ref(md_text):
    """C9a: Every Fig. N cited in body text."""
    body_match = re.search(r'^## .+?\n(.*?)(?=^## (?:REFERENCES|ACKNOWLEDGMENT))', md_text, re.DOTALL | re.MULTILINE)
    if not body_match:
        return ('C9a', 'HARD', False, 'Cannot find body text (between ## headings and ## REFERENCES)')
    body_text = body_match.group(1)
    figs = re.findall(r'!\[Fig\.\s*(\d+)\.', md_text)
    orphans = []
    for fig_num in figs:
        if not re.search(r'Fig\.\s*' + re.escape(fig_num) + r'[^0-9]', body_text):
            orphans.append(fig_num)
    if orphans:
        return ('C9a', 'HARD', False, f'Figures not cited in body text: Fig. {", Fig. ".join(orphans)}')
    return ('C9a', 'HARD', True, f'All {len(figs)} figures cited in body text')

def check_c9b_table_cross_ref(md_text):
    """C9b: Every TABLE cited in body text."""
    body_match = re.search(r'^## .+?\n(.*?)(?=^## (?:REFERENCES|ACKNOWLEDGMENT))', md_text, re.DOTALL | re.MULTILINE)
    if not body_match:
        return ('C9b', 'HARD', False, 'Cannot find body text')
    body_text = body_match.group(1)
    tables = re.findall(r'\*\*TABLE\s+([IVXLCDM]+)', md_text)
    orphans = []
    for tbl_roman in tables:
        if not re.search(r'Table\s+' + re.escape(tbl_roman) + r'[^A-Za-z]', body_text, re.IGNORECASE):
            orphans.append(tbl_roman)
    if orphans:
        return ('C9b', 'HARD', False, f'Tables not cited in body text: Table {", Table ".join(orphans)}')
    return ('C9b', 'HARD', True, f'All {len(tables)} tables cited in body text')

def check_c10_ref_format(md_text):
    """C10: No **bold** or `code` in references (single *italic* for journals is OK)."""
    refs_match = re.search(r'## REFERENCES\s*\n(.*?)$', md_text, re.DOTALL | re.IGNORECASE)
    if not refs_match:
        return ('C10', 'SOFT', True, 'No REFERENCES section to check')
    for line in refs_match.group(1).strip().split('\n'):
        line = line.strip()
        if not line or not re.match(r'^\[\d+\]', line):
            continue
        if re.search(r'\*\*[^*]+\*\*', line):
            return ('C10', 'HARD', False, f'Bold markers (**) in reference: {line[:60]}...')
        if '`' in line:
            return ('C10', 'HARD', False, f'Backticks in reference: {line[:60]}...')
        if '~~' in line:
            return ('C10', 'HARD', False, f'Strikethrough in reference: {line[:60]}...')
    return ('C10', 'HARD', True, 'No markdown symbols in references')

def check_ext1_total_words(md_text):
    """EXT1: Total word count >=3500."""
    clean = re.sub(r'```.*?```', '', md_text, flags=re.DOTALL)
    clean = re.sub(r'!\[.*?\]\(.*?\)', '', clean)
    clean = re.sub(r'\$\$.*?\$\$', '', clean, flags=re.DOTALL)
    clean = re.sub(r'\|[^\n]+\|', '', clean)
    clean = re.sub(r'<!--.*?-->', '', clean, flags=re.DOTALL)
    words = len(clean.split())
    if words >= 3500:
        return ('EXT1', 'HARD', True, f'Total word count: {words} (>=3500)')
    return ('EXT1', 'HARD', False, f'Total word count: {words} (<3500)')

def check_ext2_body_words(md_text):
    """EXT2: Body word count >=3000."""
    body_match = re.search(r'^## .+?\n(.*?)(?=^## (?:REFERENCES|ACKNOWLEDGMENT))', md_text, re.DOTALL | re.MULTILINE)
    if not body_match:
        return ('EXT2', 'HARD', False, 'Cannot find body text')
    body = body_match.group(1)
    body = re.sub(r'!\[.*?\]\(.*?\)', '', body)
    body = re.sub(r'\$\$.*?\$\$', '', body, flags=re.DOTALL)
    body = re.sub(r'\|[^\n]+\|', '', body)
    words = len(body.split())
    if words >= 3000:
        return ('EXT2', 'HARD', True, f'Body word count: {words} (>=3000)')
    return ('EXT2', 'HARD', False, f'Body word count: {words} (<3000)')

def check_ext3_no_chinese(md_text):
    """EXT3: No Chinese characters."""
    chinese = re.findall(r'[一-鿿]', md_text)
    if chinese:
        lines = md_text.split('\n')
        locations = []
        for i, line in enumerate(lines):
            if re.search(r'[一-鿿]', line):
                locations.append(f'line {i+1}')
                if len(locations) >= 3:
                    break
        return ('EXT3', 'HARD', False, f'Chinese characters found at: {locations}')
    return ('EXT3', 'HARD', True, 'No Chinese characters')

def check_ext4_no_raw_latex(md_text):
    """EXT4: No raw LaTeX commands in body text."""
    raw_patterns = [
        (r'\\cite\{', '\\cite{}'),
        (r'\\frac\{', '\\frac{}'),
        (r'\\begin\{', '\\begin{}'),
        (r'\\end\{', '\\end{}'),
        (r'\\textbf\{', '\\textbf{}'),
        (r'\\textit\{', '\\textit{}'),
        (r'\\ref\{', '\\ref{}'),
        (r'\\label\{', '\\label{}'),
    ]
    no_display = re.sub(r'\$\$.*?\$\$', '', md_text, flags=re.DOTALL)
    found = []
    for pattern, name in raw_patterns:
        if re.search(pattern, no_display):
            found.append(name)
    if found:
        return ('EXT4', 'HARD', False, f'Raw LaTeX commands found: {found}')
    return ('EXT4', 'HARD', True, 'No raw LaTeX commands in body text')

def check_ext5_no_hr_separators(md_text):
    """EXT5: No stray --- separators in body."""
    body_match = re.search(r'^## .+?\n(.*?)(?=^## (?:REFERENCES|ACKNOWLEDGMENT))', md_text, re.DOTALL | re.MULTILINE)
    if not body_match:
        return ('EXT5', 'SOFT', True, 'No body text to check')
    hrs = re.findall(r'^---\s*$', body_match.group(1), re.MULTILINE)
    if hrs:
        return ('EXT5', 'SOFT', False, f'{len(hrs)} stray --- separator(s) in body')
    return ('EXT5', 'SOFT', True, 'No stray --- separators in body')

def check_ext6_section_word_count(md_text):
    """EXT6: Each H1 section >=280 words."""
    sections = re.split(r'^(## [IVX]+\..+)$', md_text, flags=re.MULTILINE)
    short_sections = []
    section_counts = {}
    for i in range(1, len(sections), 2):
        heading = sections[i].strip()
        if 'REFERENCES' in heading or 'ACKNOWLEDGMENT' in heading:
            continue
        body = sections[i + 1] if i + 1 < len(sections) else ''
        body = re.sub(r'!\[.*?\]\(.*?\)', '', body)
        body = re.sub(r'\$\$.*?\$\$', '', body, flags=re.DOTALL)
        body = re.sub(r'\|[^\n]+\|', '', body)
        wc = len(body.split())
        section_counts[heading] = wc
        if wc < 280:
            short_sections.append(f'{heading} ({wc} words)')

    if short_sections:
        return ('EXT6', 'SOFT', False, f'Sections <280 words: {short_sections}')
    if section_counts:
        return ('EXT6', 'SOFT', True, f'All {len(section_counts)} sections >=280 words')
    return ('EXT6', 'SOFT', True, 'No H1 sections found')


# ============================================================================
# Main
# ============================================================================

ALL_CHECKS = [
    check_c1_abstract,
    check_c1_no_heading,
    check_c2_keywords,
    check_c3a_h1_headings,
    check_c3b_h2_headings,
    check_c4a_figure_numbers,
    check_c4b_figure_caption_length,
    check_c4c_figure_caption_punct,
    check_c4d_figure_filename,
    check_c5a_table_caption_format,
    check_c5b_table_caption_length,
    check_c5c_table_caption_punct,
    check_c5d_table_blank_line,
    check_c6a_equation_tags,
    check_c6b_equation_count,
    check_c6c_equation_numbers,
    check_c7_references,
    check_c7_no_duplicate_refs,
    check_c9a_figure_cross_ref,
    check_c9b_table_cross_ref,
    check_c10_ref_format,
    check_ext1_total_words,
    check_ext2_body_words,
    check_ext3_no_chinese,
    check_ext4_no_raw_latex,
    check_ext5_no_hr_separators,
    check_ext6_section_word_count,
]


def validate(md_path):
    """Run all checks on the given markdown file."""
    if not os.path.exists(md_path):
        print(f"[ERROR] File not found: {md_path}")
        return 1

    with open(md_path, 'r', encoding='utf-8') as f:
        md_text = f.read()

    print(f"=== IEEE Markdown Validation: {os.path.basename(md_path)} ===")
    print()

    results = []
    for check_fn in ALL_CHECKS:
        check_id, level, passed, message = check_fn(md_text)
        results.append((check_id, level, passed, message))
        status = 'PASS' if passed else 'FAIL'
        icon = '  [PASS]' if passed else f'  [FAIL/{level}]'
        print(f'{icon} {check_id}: {message}')

    # Summary
    print()
    total = len(results)
    passed_count = sum(1 for _, _, p, _ in results if p)
    failed_count = total - passed_count
    hard_fails = sum(1 for _, l, p, _ in results if not p and l == 'HARD')
    soft_fails = sum(1 for _, l, p, _ in results if not p and l == 'SOFT')

    print(f'Result: {passed_count}/{total} PASS, {failed_count} FAIL ({hard_fails} HARD, {soft_fails} SOFT)')

    if hard_fails > 0:
        print(f'\nGATE: BLOCKED -- {hard_fails} HARD violation(s) must be fixed before running format_ieee.py')
        return 1
    elif soft_fails > 0:
        print(f'\nGATE: PASS WITH WARNINGS -- {soft_fails} SOFT warning(s) (proceed with caution)')
        return 2
    else:
        print('\nGATE: PASS -- all checks passed, ready for format_ieee.py')
        return 0


if __name__ == '__main__':
    if len(sys.argv) != 2:
        print("Usage: python validate_md.py <paper.md>")
        print()
        print("Validates a Markdown paper against IEEE MarkdownOutputContract C1-C10")
        print("and structural extension rules. Must pass before running format_ieee.py.")
        sys.exit(2)
    sys.exit(validate(sys.argv[1]))
