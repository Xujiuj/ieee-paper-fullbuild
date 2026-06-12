#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Markdown parsing and normalization for IEEE formatter.

This module treats Markdown as a structured intermediate representation.
It does not create or inspect WordprocessingML.
"""
import re

DASH_CHARS = '\u2014\u2013-'

def parse_md_table(table_lines):
    """Parse a markdown table block into (headers, rows). Returns None if invalid."""
    if len(table_lines) < 2:
        return None
    def split_cells(line):
        line = line.strip()
        if line.startswith('|'):
            line = line[1:]
        if line.endswith('|'):
            line = line[:-1]
        return [c.strip() for c in line.split('|')]
    headers = split_cells(table_lines[0])
    if not re.match(r'^[\s|:-]+$', table_lines[1]):
        return None
    rows = []
    for tl in table_lines[2:]:
        cells = split_cells(tl)
        if cells:
            rows.append(cells)
    if not headers or not rows:
        return None
    return (headers, rows)


def extract_title(lines):
    """Extract title from first # heading (not ##). Falls back to first non-empty line."""
    for line in lines:
        if line.startswith('# ') and not line.startswith('## '):
            return line[2:].strip()
    # Fallback: first non-empty, non-metadata line
    for line in lines:
        stripped = line.strip()
        if stripped and not stripped.startswith('**') and not stripped.startswith('#'):
            return stripped
    return ''


def extract_abstract(lines):
    """Extract abstract text from ## Abstract section or **Abstract** — format.

    Handles both:
      - ## Abstract / ## ABSTRACT heading
      - **Abstract** — bold text on first line (IEEE style)
    """
    in_abstract = False
    abstract_lines = []

    # Format 1: **Abstract** — inline bold (IEEE style on first content line)
    for i, line in enumerate(lines):
        m = re.match(r'\*?\*?Abstract\*?\*?\s*[—–\-]\s*(.*)', line.strip())
        if m:
            first_part = m.group(1).strip()
            abstract_lines.append(first_part) if first_part else None
            # Collect continuation lines until ## heading, keywords, or ---
            for j in range(i + 1, len(lines)):
                ln = lines[j].strip()
                if not ln:
                    break
                if ln.startswith('#') or ln.startswith('**') or ln == '---':
                    break
                abstract_lines.append(ln)
            return ' '.join(abstract_lines)

    # Format 2: ## Abstract / ## ABSTRACT heading
    for line in lines:
        if line.strip().startswith('## Abstract') or line.strip().startswith('## ABSTRACT'):
            in_abstract = True
            continue
        if in_abstract:
            if line.startswith('## ') or re.match(r'\*\*Keywords?\*?\*?\s*[:：]', line, re.IGNORECASE) or line.strip() == '---':
                break
            if line.strip():
                abstract_lines.append(line.strip())
    return ' '.join(abstract_lines)


def extract_keywords(lines):
    """Extract keywords from **Keywords:** line."""
    dash_class = '[' + re.escape(DASH_CHARS) + ']'
    for line in lines:
        kw_m = re.match(
            r'\*\*\s*Keywords?\s*:?\s*\*\*\s*(?:' + dash_class + r'|:|：)\s*(.*)',
            line,
            re.IGNORECASE,
        )
        if kw_m:
            return 'Keywords—' + kw_m.group(1).strip()
    return 'Keywords—'


def extract_body_and_refs(lines):
    """Extract clean body lines and reference lines from markdown.

    Body boundary: after keywords/abstract section → before ## ACKNOWLEDGMENT or ## REFERENCES.
    Strips ## Abstract section to prevent double-insertion.
    Strips --- separators.
    """
    kw_idx = None
    ack_idx = None
    refs_idx = None

    for i, line in enumerate(lines):
        if re.match(r'\*\*\s*Keywords?\s*:?\s*\*\*', line, re.IGNORECASE):
            kw_idx = i
        if line.upper().startswith('## ACKNOWLEDGMENT'):
            ack_idx = i
        if line.upper().startswith('## REFERENCES'):
            refs_idx = i

    body_start = (kw_idx + 1) if kw_idx is not None else 0
    body_end = ack_idx if ack_idx is not None else refs_idx
    if body_end is None:
        body_end = len(lines)

    body_lines = lines[body_start:body_end]
    ref_lines = lines[refs_idx + 1:] if refs_idx is not None else []

    # Remove ## Abstract section (everything before first non-abstract ## heading)
    skip_end = 0
    for idx, bl in enumerate(body_lines):
        if bl.strip().startswith('## ') and 'abstract' not in bl.lower():
            skip_end = idx
            break
    if skip_end > 0:
        print(f"Removed {skip_end} lines (Abstract section) from body_lines")
        body_lines = body_lines[skip_end:]

    # Strip --- separators
    body_lines = [l for l in body_lines if l.strip() != '---']

    return body_lines, ref_lines


def renumber_equations(md_text):
    """Renumber \\tag{eq:N} tags to sequential order (1,2,3,...) based on position.

    ARS pipeline may generate non-sequential equation numbers. This function
    renumbers them to match their order of appearance in the document.
    Returns the renumbered markdown text.
    """
    pattern = re.compile(re.escape(chr(92)) + r'tag\{eq:(\d+)\}')
    matches = list(pattern.finditer(md_text))
    if not matches:
        return md_text

    # Check if already sequential
    nums = [int(m.group(1)) for m in matches]
    if nums == list(range(1, len(nums) + 1)):
        return md_text

    # Replace via placeholders to avoid cross-contamination
    result = md_text
    for m in reversed(matches):
        old_tag = m.group(1)
        result = result[:m.start()] + r'\tag{eq:__EQ_RENUM_' + old_tag + '__}' + result[m.end():]

    # Replace placeholders with new sequential numbers (last to first to keep positions stable)
    temp_pattern = re.compile(re.escape(chr(92)) + r'tag\{eq:__EQ_RENUM_(\d+)__\}')
    matches2 = list(temp_pattern.finditer(result))
    for i, m in enumerate(reversed(matches2)):
        new_tag = str(len(matches2) - i)
        result = result[:m.start()] + r'\tag{eq:' + new_tag + '}' + result[m.end():]

    print(f"  Renumbered {len(matches)} equations to sequential order")
    return result


def renumber_references(body_lines, ref_lines):
    """Renumber citations to first-appearance order.

    Returns (remapped_body_lines, ref_entries) where ref_entries = [(num, text), ...].
    Reference text is cleaned of non-journal markdown symbols (C10).
    """
    body_text_full = '\n'.join(body_lines)
    citation_order = []
    seen_cites = set()
    for m in re.finditer(r'\[(\d+)\]', body_text_full):
        n = m.group(1)
        if n not in seen_cites:
            citation_order.append(n)
            seen_cites.add(n)

    old_refs = {}
    for line in ref_lines:
        m = re.match(r'^\[(\d+)\]\s*(.*)', line.strip())
        if m:
            old_refs[m.group(1)] = clean_ref_markdown(m.group(2))

    old_to_new = {old: new for new, old in enumerate(citation_order, 1)}

    def remap_citations(text):
        def replace_cite(m):
            old_num = m.group(1)
            return f'[{old_to_new[old_num]}]' if old_num in old_to_new else m.group(0)
        return re.sub(r'\[(\d+)\]', replace_cite, text)

    body_lines = [remap_citations(line) for line in body_lines]

    ref_entries = []
    for old_num in citation_order:
        if old_num in old_refs:
            ref_entries.append((old_to_new[old_num], old_refs[old_num]))
    ref_entries.sort(key=lambda x: x[0])

    print(f"Remapped {len(citation_order)} references to first-appearance order")
    return body_lines, ref_entries


def clean_ref_markdown(text):
    """Strip non-journal Markdown symbols from reference text (C10).

    Preserves single *italic* for journal/conference names (IEEE convention).
    Removes: **bold**, `backticks`, ~~strikethrough~~, _emphasis_.
    """
    # Remove **bold** → plain text
    text = re.sub(r'\*\*(.+?)\*\*', r'\1', text)
    # Remove `backticks` → plain text
    text = re.sub(r'`(.+?)`', r'\1', text)
    # Remove ~~strikethrough~~ → plain text
    text = re.sub(r'~~(.+?)~~', r'\1', text)
    # Remove _emphasis_ (but not underscores in identifiers like some_name)
    # Only match _text with spaces_ pattern
    text = re.sub(r'(?<=\s)_(.+?)_(?=[\s,.])', r'\1', text)
    return text


def extract_md_tables(body_lines):
    """Find markdown tables in body_lines, return (md_tables, caption_set, cleaned_body_lines).

    md_tables: list of (start_idx, end_idx, headers, rows, caption)
    caption_set: set of caption texts to skip during body insertion
    cleaned_body_lines: body_lines with table rows removed
    """
    md_tables = []
    i = 0
    while i < len(body_lines):
        line = body_lines[i].rstrip()
        if line.strip().startswith('|') and i + 1 < len(body_lines) and re.match(r'^[\s|:-]+$', body_lines[i + 1].strip()):
            table_block = []
            j = i
            while j < len(body_lines) and body_lines[j].strip().startswith('|'):
                table_block.append(body_lines[j])
                j += 1
            parsed = parse_md_table(table_block)
            if parsed:
                headers, rows = parsed
                caption = None
                for k in range(i - 1, max(i - 8, -1), -1):
                    prev = body_lines[k].strip()
                    # Standard: **Table N. ...**, **TABLE N. ...**, or Table N. ...
                    if prev and re.match(r'\*{0,2}[Tt][Aa][Bb][Ll][Ee]\s+[IVXLCDM0-9]', prev):
                        caption = prev
                        break
                    # Also accept plain bold title lines: **TITLE** (all-caps, no TABLE prefix).
                    # This covers ARS-generated captions that omit the TABLE N. prefix.
                    bold_m = re.match(r'^\*\*(.+?)\*\*$', prev)
                    if bold_m:
                        inner = bold_m.group(1).strip()
                        if inner.upper() == inner and len(inner.split()) >= 2:
                            caption = prev
                            break
                    # Stop scanning if we hit a heading, figure, table, or another caption
                    if prev.startswith('#') or prev.startswith('![') or prev.startswith('|'):
                        break
                md_tables.append((i, j, headers, rows, caption))
                i = j
                continue
        i += 1

    # Remove table rows from body_lines
    table_line_indices = set()
    for start, end, _, _, _ in md_tables:
        for li in range(start, end):
            table_line_indices.add(li)
    cleaned = [body_lines[i] for i in range(len(body_lines)) if i not in table_line_indices]

    caption_set = set()
    for _, _, _, _, caption in md_tables:
        if caption:
            # Strip markdown bold markers for accurate matching in flush_para_and_try_table
            clean = re.sub(r'\*\*(.+?)\*\*', r'\1', caption).strip()
            caption_set.add(clean)

    print(f"Found {len(md_tables)} markdown tables")
    return md_tables, caption_set, cleaned


def join_multiline_equations(lines):
    """Join multiline display equations $$ ... \tag{eq:N} $$ into single lines.

    The main loop processes lines individually, so multiline equations like:
        $$
        z = x + y
        \tag{eq:1}
        $$
    must be collapsed into: $$z = x + y \tag{eq:1}$$
    """
    result = []
    i = 0
    while i < len(lines):
        s = lines[i].strip()
        if s == '$$' or (s.startswith('$$') and '\\tag{eq:' not in s and not s.endswith('$$')):
            # Start of a multiline equation
            eq_lines = [s.lstrip('$').strip()] if s != '$$' else []
            i += 1
            found_tag = False
            while i < len(lines):
                cur = lines[i].strip()
                if '\\tag{eq:' in cur:
                    # This line has the tag - join everything
                    eq_content = ' '.join(eq_lines + [cur.replace('$$', '').strip()])
                    result.append(f'$${eq_content}$$')
                    found_tag = True
                    i += 1
                    # Skip closing $$ if present
                    if i < len(lines) and lines[i].strip() == '$$':
                        i += 1
                    break
                elif cur == '$$':
                    # Closing $$ without tag - treat as single-line content
                    eq_content = ' '.join(eq_lines)
                    result.append(f'$${eq_content}$$')
                    found_tag = True
                    i += 1
                    break
                else:
                    eq_lines.append(cur)
                    i += 1
            if not found_tag:
                # Didn't find a tag, push original lines
                result.extend(lines[len(result):i])
        else:
            result.append(lines[i])
            i += 1
    return result


def strip_blank_lines_around_blocks(lines):
    """Remove blank lines immediately before/after equations, figures, and tables.

    Prevents extra vertical spacing around display equations (行间公式),
    figures, and tables in the output Word document.
    """
    is_block = [False] * len(lines)
    for i, line in enumerate(lines):
        s = line.strip()
        if re.match(r'\$\$(.+?)' + re.escape(chr(92)) + r'tag\{eq:\d+\}\s*\$\$', s):
            is_block[i] = True
        elif re.match(r'!\[Fig\.\s*\d+\.\s*(.+?)\]\((.+?)\)', s):
            is_block[i] = True
        elif s.startswith('|') and not re.match(r'^[\s|:-]+$', s):
            is_block[i] = True

    # Identify TABLE caption lines — blank line AFTER them must be preserved
    # to keep captions separate from table data rows.
    is_table_caption = [False] * len(lines)
    for i, line in enumerate(lines):
        if re.match(r'\*?\*?\s*TABLE\s+[IVXLCDM0-9]', line.strip()):
            is_table_caption[i] = True

    remove = set()
    for i, blk in enumerate(is_block):
        if not blk:
            continue
        # Remove blank line immediately BEFORE this block
        if i > 0 and lines[i - 1].strip() == '':
            # But keep it if the preceding line is a TABLE caption
            if i >= 2 and is_table_caption[i - 2]:
                pass  # preserve blank line between caption and table
            else:
                remove.add(i - 1)
        # Remove blank line immediately AFTER this block
        if i + 1 < len(lines) and lines[i + 1].strip() == '':
            remove.add(i + 1)

    # Also protect blank lines after TABLE captions (before table rows)
    for i, is_cap in enumerate(is_table_caption):
        if not is_cap:
            continue
        if i + 1 < len(lines) and lines[i + 1].strip() == '':
            remove.discard(i + 1)

    result = [lines[i] for i in range(len(lines)) if i not in remove]
    if remove:
        print(f"Stripped {len(remove)} blank lines around equations/figures/tables")
    return result


