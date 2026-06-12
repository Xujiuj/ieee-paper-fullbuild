# Postmortem: 18 Failures the Skill Now Prevents

This document records the failure modes observed across 11 IEEE paper
generation attempts on the SM383 lunar transport project. Each failure
took 2-4 hours of round-trip iteration to diagnose. The skill encodes
each lesson as a hard gate or invariant.

## F1. Body 4 pages instead of 6-8

**Symptom**: Generated docx renders only 3.5-4 pages in Word. Reviewer
rejects as too short for a conference paper.

**Root cause**: Body word count fell below 3000. The rewriter compressed
the source paper to a synopsis instead of an academic rewrite.

**Fix**: Hard floor of 3000 body words and 3500 total words enforced by
the validator (invariants 1, 2). Rewriter reports per-section word counts
so undershoots are caught at source.

## F2. Two-column layout collapsed into one column

**Symptom**: Body text spans the full page width; abstract is the only
two-column section.

**Root cause**: Build script cleared the entire body element of the
template, deleting the sectPr paragraphs that anchored the two-
column section.

**Fix**: Edit template in place. Anchor new content on the keywords
paragraph. Never remove paragraphs that own a sectPr.
Validator invariant 5 catches recurrence.

## F3. Equations rendered as plain letters

**Symptom**: T_SE = M_SE / 537000 shows up as plain text, not as a
typeset fraction.

**Root cause**: Equations were inserted as Unicode strings inside w:t
text runs rather than as Word OMML objects.

**Fix**: Convert every display equation through pandoc -t docx and
extract the resulting m:oMath block. Validator invariant 6 verifies
that structural OMML elements (m:f, m:nary, m:sSub, m:sSup, m:d, m:rad)
are present.

## F4. "I. I. Introduction" doubled headings

**Symptom**: Headings render as "I. I. Introduction", "II. II. Optimal
Strategy", etc.

**Root cause**: Heading text was prepended with manual Roman numerals
even though the template style "1" auto-numbers via numId 4.

**Fix**: Heading text is descriptive only; never prepend manual
numerals. Validator invariant 9 catches recurrence.

## F5. "[1] [1] Author X" doubled references

**Symptom**: References render as "[1] [1] Author X", "[2] [2] Author Y".

**Root cause**: Reference text prepended with [n] even though the
references style auto-numbers via numId 8.

**Fix**: Reference text contains only the entry body; never prepend
[n]. Validator invariant 10 catches recurrence.

## F6. A scanned letter inserted as Figure 8

**Symptom**: The paper has a portrait-orientation page-image of a
hand-written letter at the end of Section VI.

**Root cause**: The figure pool included image16.jpeg, a scanned
letter, and the formatter inserted images by index without content
classification.

**Fix**: Run the figure quality classifier. Reject any image with
aspect_ratio < 1.0 AND white_ratio > 0.5. Validator invariant 8
catches recurrence.

## F7. Authors deleted or renamed

**Symptom**: The output paper has only one author (Siming Li) but the
template originally listed four. Or the paper has fabricated names.

**Root cause**: Build script deleted "extra" Author paragraphs to fit
a perceived single-author requirement, or replaced template authors
with content-derived placeholders.

**Fix**: Authors are read-only. Strip placeholder mojibake runs only;
never delete an Author or Affiliation paragraph. Never change author
names without an explicit user request and confirmation. Validator
invariant 4 catches recurrence.

## F8. Notation/Symbol Table as its own section

**Symptom**: Section II is "Notation" and consists of a long table of
symbols and their meanings. Reviewer flags this as unscholarly.

**Root cause**: The rewriter copied the source paper's notation table
verbatim instead of integrating symbol definitions inline at first use.

**Fix**: Forbid Notation sections in the rewriter's output spec.
Symbols are defined inline at first use.

## F9. Chinese mojibake in document body

**Symptom**: Garbled characters visible in the rendered output.

**Root cause**: Template fragments contain w:rFonts w:eastAsia="宋体"
references and stray Chinese characters in trailing paragraphs. Build
script left them intact.

**Fix**: After insertion, walk all w:rFonts elements and remove any
w:eastAsia attribute whose value contains Chinese characters; walk
all w:t elements and strip Chinese substrings. Validator invariant
12 catches recurrence.

## F10. Empty cells indented like body text

**Symptom**: Equation tables show the equation pushed right by half a
column; reference tables show numbers offset.

**Root cause**: Cells inherited the body style's first-line indent.

**Fix**: Apply firstLine=0, left=0, right=0 to every paragraph inside
every table cell. Validator invariant 13 catches recurrence.

## F11. Pandoc reference-doc loses IEEE formatting

**Symptom**: Output looks like a generic Word document, not an IEEE
paper. Title centering, two-column layout, and font sizes wrong.

**Root cause**: Build script ran pandoc --reference-doc=template.docx
which copies styles by name but does not preserve section breaks,
auto-numbering, or sectPr blocks.

**Fix**: Never use pandoc for the layout. Use pandoc only for OMML
equation conversion. Open the template directly with python-docx and
edit in place.

## F12. Figure caption above image instead of below

**Symptom**: Caption paragraph appears above the figure image.

**Root cause**: Formatter inserted figurecaption paragraph before the
image paragraph.

**Fix**: Insert image paragraph FIRST, then figurecaption paragraph AFTER.
Validator catches this by visual inspection.

## F13. Figure caption doubled ("Fig. 1. Fig. 1. ...")

**Symptom**: Caption shows "Fig. 1. Fig. 1. Overall architecture".

**Root cause**: figurecaption style auto-numbers via numId=2, and the
formatter also prepended "Fig. N." to the caption text.

**Fix**: Caption text contains ONLY the descriptive title (e.g., "Overall
architecture"). The style handles "Fig. N." automatically.

## F14. Table font size mismatch

**Symptom**: Table text appears larger/smaller than expected (template
uses 8pt).

**Root cause**: Formatter did not set explicit font size on table cell
runs, so they inherited a different default.

**Fix**: Set `<w:sz w:val="16"/>` (8pt in half-points) on every `<w:rPr>`
inside table cells. Both header and data cells need this.

## F15. Tables grouped at end of document

**Symptom**: All tables appear after the last body section instead of
inline where referenced in the text.

**Root cause**: Formatter inserted tables in a batch after the body
content loop, rather than inline during paragraph insertion.

**Fix**: Parse markdown table syntax (`| col | col |`) and insert Word
tables immediately after the body paragraph that references them.

## F16. References not in citation order

**Symptom**: Body text cites [7] before [2], but the reference list
has [2] before [7].

**Root cause**: Reference list was in numerical order [1,2,3,...] instead
of first-appearance order in the body text.

**Fix**: Scan body text for first appearance of each [N], build
old→new mapping, remap all citations in body text, and reorder
reference entries accordingly.

## F17. Page count threshold too tight

**Symptom**: Validator fails on page count (9.1 > 9.0) for a paper
with 6 figures and 8 equations.

**Root cause**: Page estimate formula `body/750 + figs*0.35 + eqs*0.08`
can overshoot for figure-heavy papers. The 9.0 ceiling was too low.

**Fix**: Raise page count ceiling to 10.0 (IEEE conference standard
allows up to 10 pages).

## F18. ACKNOWLEDGMENT section missing or unwanted

**Symptom**: Formatter either skips the ACKNOWLEDGMENT section from the
markdown or inserts it when the user doesn't want it.

**Root cause**: The skill spec didn't clarify whether ACKNOWLEDGMENT
should be included.

**Fix**: Default behavior: parse and insert ACKNOWLEDGMENT from markdown
if present. User can override by specifying "no acknowledgment" in the
brief.

## F19. Abstract inserted twice (template + body)

**Symptom**: The abstract appears twice in the output: once in the
template's abstract area and again as a body section with "## Abstract"
heading.

**Root cause**: `format_ieee.py` extracts abstract text from `## Abstract`
in markdown and replaces the template abstract. However, `body_lines`
still contains the `## Abstract` section, so it gets processed again as
body content.

**Fix**: After extracting the abstract for template replacement, remove
the `## Abstract` section (from `## Abstract` to the next `##` heading)
from `body_lines` before the main body processing loop. The script now
skips all lines before the first non-abstract `## ` heading.

## F20. Table caption text appears twice

**Symptom**: Before a markdown table, a descriptive text line like
"Table I: Compliance Performance Metrics..." appears both as a body
paragraph AND as the table's caption.

**Root cause**: The text line before the markdown table is inserted as
a body paragraph via `flush_para_and_try_table()`, AND it's also used
as the table caption by `make_data_table()`.

**Fix**: Track all table caption texts in a set. In
`flush_para_and_try_table()`, check if the paragraph text matches a
caption BEFORE inserting it as body text. If it matches, skip the body
insertion but still run the table matching logic.

## F21. Inline LaTeX formulas rendered as literal text

**Symptom**: Inline math like `$G$`, `$w_1$` appears as literal
"$G$" and "$w_1$" in the Word output instead of as typeset math.

**Root cause**: `make_para_with_formatting()` only handled `**bold**`
markers. No code converted inline `$...$` LaTeX to OMML. The pandoc
conversion function `latex_to_omml()` was only called for display
equations (`$$...$$`).

**Fix**: Added `inline_latex_to_omml()` function that converts inline
LaTeX to OMML via pandoc. Rewrote `make_para_with_formatting()` to:
1. Extract all `$...$` inline math and convert to OMML
2. Replace with numbered placeholders (`§§MATH_N§§`)
3. Split by bold/italic markers on the placeholder text
4. Assemble runs: normal text, bold runs, italic runs, and `<w:oMath>`
   elements for each math expression

**Critical detail**: When writing LaTeX for pandoc, MUST use `$...$`
delimiters around the expression. Bare text like `x G x` won't trigger
pandoc's math parser.

## F22. `**` markdown symbols not converted to Word formatting

**Symptom**: `**bold text**` appears as literal asterisks in Word output
instead of as bold text.

**Root cause**: The original `make_para()` function only creates plain
text runs. No markdown-to-Word formatting conversion was implemented.

**Fix**: Added `make_para_with_formatting()` that splits text by
`**...**` (bold) and `*...*` (italic) markers and creates appropriate
`<w:rPr>` elements (`<w:b/>` for bold, `<w:i/>` for italic).

## F23. content_start=None causing duplicate headings

**Symptom**: The output contains `## REFERENCES` appearing twice: once
as a body section heading and once as the actual references heading.

**Root cause**: When no `---` separator exists in the markdown, the
variable `content_start` stays `None`. The body extraction uses
`lines[None:ack_start]` which slices from the beginning of the list,
including everything from line 0. This captures the `## REFERENCES`
section as body content, causing it to be inserted twice.

**Fix**: The restructured `extract_body_and_refs()` function uses the
Keywords line index as the body start (not a `---` separator). It finds
the first `## ACKNOWLEDGMENT` or `## REFERENCES` as the body end, and
removes the `## Abstract` section. This ensures clean body boundaries
regardless of whether `---` separators exist in the markdown.
