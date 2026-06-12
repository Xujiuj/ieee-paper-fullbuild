#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Word-count gate for the rewriter.

Usage:
    python wordcount_gate.py <markdown_file>

Reports total / per-section word counts and exit code 0 if all floors
are met:
    - Total >= 3500
    - Body (sections excluding refs/captions) >= 3000
    - Each H1 section >= 280

Exit code 1 if any floor is missed; stderr prints which floor failed.
"""
import re, sys

TOTAL_FLOOR = 3500
BODY_FLOOR = 3000
SECTION_FLOOR = 280

def main(md_path):
    with open(md_path, 'r', encoding='utf-8') as f:
        text = f.read()

    text_no_code = re.sub(r'```.*?```', '', text, flags=re.DOTALL)
    total = len(text_no_code.split())

    sections = re.split(r'^# (.+?)$', text_no_code, flags=re.MULTILINE)

    section_counts = {}
    body_total = 0
    if len(sections) > 1:
        for i in range(1, len(sections), 2):
            title = sections[i].strip()
            body = sections[i + 1] if i + 1 < len(sections) else ''
            wc = len(body.split())
            section_counts[title] = wc
            if title.lower() not in ('references', 'acknowledgments',
                                     'acknowledgment'):
                body_total += wc

    print(f"Total words: {total}")
    print(f"Body words:  {body_total}")
    print(f"Per-section:")
    for title, wc in section_counts.items():
        marker = '' if wc >= SECTION_FLOOR else f'  (UNDER {SECTION_FLOOR})'
        print(f"  {title}: {wc}{marker}")

    fails = []
    if total < TOTAL_FLOOR:
        fails.append(f"total {total} < {TOTAL_FLOOR}")
    if body_total < BODY_FLOOR:
        fails.append(f"body {body_total} < {BODY_FLOOR}")
    short_sections = [t for t, wc in section_counts.items()
                      if wc < SECTION_FLOOR and t.lower() not in
                      ('references', 'acknowledgments', 'acknowledgment',
                       'abstract')]
    for s in short_sections:
        fails.append(f"section '{s}' < {SECTION_FLOOR}")

    if fails:
        print("\nGATE FAIL:", file=sys.stderr)
        for f in fails:
            print(f"  - {f}", file=sys.stderr)
        return 1
    else:
        print("\nGATE PASS")
        return 0

if __name__ == '__main__':
    if len(sys.argv) != 2:
        print("Usage: python wordcount_gate.py <markdown_file>",
              file=sys.stderr)
        sys.exit(2)
    sys.exit(main(sys.argv[1]))
