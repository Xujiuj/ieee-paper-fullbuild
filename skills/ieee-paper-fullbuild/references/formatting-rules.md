# Formatting Rules Reference

All rules learned from 12+ build iterations. Each rule prevents a specific
failure mode in the output `.docx`.

## 1. Template Editing

- **Edit in place**: Copy the template to the output path, then open with
  python-docx. NEVER clear the body element.
- **Anchor on Keywords**: All new body content goes after the Keywords
  paragraph via `addnext()`. Never anchor after the references-sectPr.
- **sectPr preservation**: Never remove paragraphs that own a `<w:sectPr>`.
  These anchor the two-column layout.

## 2. Front Matter

| Element | Style | Auto-number | Notes |
|---------|-------|-------------|-------|
| Title | `papertitle` | No | Replace runs only; keep paragraph |
| Abstract | `Abstract` | No | Last Abstract paragraph has text |
| Keywords | `Keywords` | No | Format: `Keywords—term1, term2, ...` |
| Author | `Author` | No | READ-ONLY; strip mojibake only |
| Affiliation | `Affiliation` | No | READ-ONLY; strip mojibake only |

**Author Preservation**: NEVER delete Author/Affiliation paragraphs. Strip
only runs whose text matches `[一-鿿（）]` or `[\xc0-\xff]{3,}`.

## 3. Headings

| Level | Style | Auto-number (numId) | Text format |
|-------|-------|---------------------|-------------|
| H1 | `1` | 4 | Descriptive title only, NO `I.` prefix |
| H2 | `2` | 4 | Descriptive title only, NO `A.` prefix |

**Rule**: The template auto-numbers headings. Adding manual prefixes like
"I. INTRODUCTION" causes doubled output "I. I. INTRODUCTION".

## 4. Body Text

- Style: `a3` (Body Text)
- Justification: both (justified)
- No manual indent needed (style handles it)

## 5. Figures

- **Order**: Image paragraph FIRST, then figurecaption paragraph BELOW
- **Caption text**: Descriptive title only (e.g., "Overall architecture").
  Do NOT include "Fig. N." — the style auto-numbers via numId=2.
- **Caption rules**: ≤12 words, NO trailing punctuation (period, comma, etc.).
  Caption is a concise noun phrase, not a sentence.
- **Size**: Max width 3.3 inches, maintain aspect ratio
- **Quality filter**: Reject images with aspect_ratio < 1.0 AND
  white_ratio > 0.5 (scanned letters)
- **Centering**: Image paragraph must have `<w:jc w:val="center"/>`
- **Inline images**: Use `<w:drawing><wp:inline>` with `<a:blip r:embed>`

## 6. Equations

- **Source**: Convert LaTeX through `pandoc --mathml` to OMML
- **Structure**: Embed in borderless 1x2 table: left=equation, right=(N)
- **Column widths**: Left=8000 dxa, Right=1000 dxa
- **Verification**: Must contain structural OMML elements:
  `m:f`, `m:nary`, `m:sSub`, `m:sSup`, `m:d`, `m:rad`
- **Cell indent**: Set firstLine=0, left=0, right=0 on all cell paragraphs

## 7. Tables

- **Font size**: 8pt (sz=16 half-points) for all table cell text
- **Style**: Use `a3` style in cells for consistent formatting
- **Borders**: Top/bottom/left/right=single (sz=2), insideH/insideV=single
  (sz=4). Full grid for data tables. Equation tables remain borderless.
- **Cell indent**: Set firstLine=0, left=0, right=0
- **Alignment**: Center (`<w:jc w:val="center"/>`)
- **Caption**: Use `tablehead` style (auto-numbers via numId=9)
- **Placement**: Inline in body text, after the paragraph that references
  the table. Parse from markdown table syntax (`| col | col |`).

## 8. References

- **Style**: `references` (auto-numbers via numId=8)
- **Text format**: Entry body only, NO `[N]` prefix
- **Order**: First-appearance order in body text (renumber body citations
  to match)
- **Heading**: Style `1` with numId=0 (suppresses auto-numbering)

## 9. Chinese Cleanup

After all content insertion:
1. Walk all `<w:rFonts>` — remove `w:eastAsia` attributes containing
   Chinese characters `[一-鿿]`
2. Walk all `<w:t>` — strip Chinese substrings `[一-鿿]`

## 10. Table Cell Indent

After all table insertion:
- Walk every `<w:tc>` → every `<w:p>` → `<w:pPr>`
- Set `<w:ind w:firstLine="0" w:left="0" w:right="0"/>`

## 11. Reference Renumbering

When body citations don't match reference list order:
1. Scan body text for `[N]` markers, record first-appearance order
2. Build old→new number mapping
3. Remap all `[N]` in body text
4. Reorder reference entries to match new numbering

## 12. Abstract Section Handling

The `## Abstract` section in markdown serves double duty: its text
replaces the template abstract AND it must NOT appear in body text.

**Rule**: After extracting abstract text for template replacement, remove
the `## Abstract` section from `body_lines`. Find the first `## ` heading
that is NOT `## Abstract` — everything before that index is removed.

**Why**: Without this, the abstract appears twice: once in the template's
abstract area and once as a body section with heading.

## 13. Table Caption Deduplication

When a markdown table has a text line before it (e.g., "Table I: ..."),
that line must serve as the table caption only, not as a body paragraph.

**Rule**: Build a set of all table caption texts. In
`flush_para_and_try_table()`, check if the paragraph text is in the
caption set. If so, skip body insertion but still run table matching.

**Why**: Without this, the caption text appears twice: once as a body
paragraph and once as the table's caption via `make_data_table()`.

## 14. Inline Math Conversion

Inline LaTeX (`$...$`) must be converted to OMML `<w:oMath>` elements
within text runs, not left as literal dollar signs.

**Rule**: In `make_para_with_formatting()`, before processing bold/italic:
1. Scan text for `$...$` patterns (non-greedy, not `$$`)
2. Convert each via `inline_latex_to_omml()` (pandoc with `$...$` delimiters)
3. Replace with `§§MATH_N§§` placeholders
4. After bold/italic splitting, insert `<w:oMath>` elements for each placeholder

**Critical**: Pandoc requires `$...$` delimiters in the LaTeX source.
Bare text like `x G x` won't trigger math parsing.

## 15. Bold/Italic Markdown Conversion

`**text**` → bold (`<w:b/>`), `*text*` → italic (`<w:i/>`).

**Rule**: Use `make_para_with_formatting()` (not `make_para()`) for all
body text paragraphs. The function handles bold, italic, and inline math
in a single pass.

**Note**: `make_para()` is still used for headings and captions where no
inline formatting is needed.

## 16. Abstract 3-Run Structure

The template's abstract paragraph (paragraph 20) has exactly 3 runs:
1. `('Abstract', italic=True)` — the label
2. `('—', normal)` — em-dash separator
3. Body text — the abstract content

**Rule**: `replace_abstract()` must always create this 3-run structure.
Never use a conditional "prepend Abstract " approach. Always clear existing
runs and insert the three runs in order.

**Why**: The template defines a specific visual hierarchy. The italic label,
em-dash, and body text create a consistent look. Conditional prepending
leads to inconsistent formatting across builds.

## 17. Heading Auto-Numbering

The template's Heading 1 style (id="1") and Heading 2 style (id="2") both
have `numId=4` in their style definition, providing auto-numbering:
- H1: I., II., III., IV., ...
- H2: A., B., C., D., ...

**Rule**:
- H1 headings: Strip Roman numerals (`I.`, `II.`, ...) before insertion.
  Use `make_para('1', heading)` WITHOUT `num_id` parameter.
- H2 headings: Strip letter prefixes (`A.`, `B.`, ...) before insertion.
  Use `make_para('2', heading)` WITHOUT `num_id` parameter.
- References heading: Use `make_para('1', 'References', num_id='0')` to
  SUPPRESS auto-numbering with explicit numId=0.

**Stripping patterns**:
- H1: `re.sub(r'^[IVX]+\.\s+', '', text)` — removes Roman numeral prefix
- H2: `re.sub(r'^[A-Z]\.\s+', '', text)` — removes letter prefix

**Why**: The user corrected that "只有reference是不带自动编号的" — only
References should suppress auto-numbering. Both H1 and H2 styles auto-number,
so manual prefixes from the markdown must be stripped to prevent duplication.

## 18. Body Boundary Detection

The body content in markdown is bounded by:
- **Start**: The Keywords line (e.g., `Keywords: term1, term2`)
- **End**: `## ACKNOWLEDGMENT` or `## REFERENCES`

**Rule**: `extract_body_and_refs()` finds the keywords line index as
body start. It finds the first `## ACKNOWLEDGMENT` or `## REFERENCES`
as body end. It removes the `## Abstract` section (all lines before the
first non-abstract `##` heading).

**Why**: Without proper boundary detection, the body may include:
- The `## Abstract` section (causing F19: abstract inserted twice)
- The `## REFERENCES` section (causing F23: duplicate reference headings)
- Content before keywords (template front matter area)

## 19. Equation Label Format

Equations use the format `$...\tag{eq:N}$` in markdown, where N is the
equation number (1, 2, 3, ...).

**Rule**: The validator counts equation labels by matching `(\d+)` in
`<w:t>` elements (invariant 7.5). The format must be exactly `(\d+)`
where N is a positive integer.

**Why**: This is the IEEE standard for equation labeling. The validator
needs a consistent pattern to count equations accurately. Other formats
like `Eq. (N)` or `[N]` are not used in the output.

---

## 20. MarkdownOutputContract Compliance

The formatter now references `MarkdownOutputContract.md` as the single
source of truth for Markdown format. Rules C1–C10 in that document define
the exact patterns the formatter parses. This means:

- **No defensive regex**: The formatter does NOT handle format deviations.
  If the Markdown doesn't match the contract, the output will have bugs.
- **Rewriter is the first line of defense**: The rewriter_agent must
  produce contract-compliant Markdown BEFORE it reaches the formatter.
- **Preflight check**: `format_ieee.py` runs `preflight_check()` at startup
  to warn about contract violations before processing.

### Contract ↔ Formatter Mapping

| Contract Rule | Formatter Function | Regex Pattern |
|--------------|-------------------|---------------|
| C1 Abstract | `extract_abstract()` | `\*?\*?Abstract\*?\*?\s*[—–\-]` |
| C2 Keywords | `extract_keywords()` | `\*\*Keywords?\*\*\s*[—–\-]` |
| C3 Headings | Main loop | `^## [IVX]+\.\s+` / `^### [A-Z]\.\s+` |
| C4 Figures | Main loop | `!\[Fig\.\s*(\d+)\.\s*(.+?)\]\((.+?)\)` |
| C5 Tables | `extract_md_tables()` | `\*\*TABLE\s+[IVXLCDM]+\.?\s*(.+?)\*\*` |
| C6 Equations | `extract_and_convert_equations()` | `\$\$(.+?)\\tag\{eq:(\d+)\}\$\$` |
| C7 References | `renumber_references()` | `^## REFERENCES$` + `^\[(\d+)\]` |

### Contract Self-Check (rewriter_agent)

The rewriter_agent runs a `contract_check()` function before returning
paper.md. This catches format issues BEFORE they reach the formatter.
See `skills/rewrite/rewriter_agent.md` for the check implementation.

---

## 21. Display Equation Spacing

Display equations should have NO extra blank paragraphs above or below.
Extra blank lines around `$$...\tag{eq:N}$$` in markdown cause unwanted
vertical spacing in the output Word document.

**Rule**: `strip_blank_lines_around_blocks()` preprocesses `body_lines`
before the main insertion loop. It removes blank lines immediately before
and after equation, figure, and table blocks.

**Why**: Markdown convention uses blank lines around display equations for
readability, but these blank lines become empty `<w:p>` elements in the
output, creating visible gaps between equations and surrounding text.

## 22. Caption Conciseness

Figure and table captions must be concise noun phrases with no trailing
punctuation.

**Rules**:
- Figure captions: ≤12 words, no trailing period/comma/question mark
- Table captions: ≤8 words, no trailing period/comma/question mark
- Captions are descriptive titles, not sentences
- Example: "Algorithm convergence curves" ✓
- Example: "Convergence curves of the proposed algorithm over 100 iterations." ✗

**Enforcement**:
1. **Rewriter** (primary): contract_check() flags long or punctuated captions
2. **Preflight** (secondary): preflight_check() warns about punctuation
3. **MarkdownOutputContract C4/C5**: defines the canonical format

---

## 23. Template Style Registry (Auto-Numbering)

**This section is the single source of truth for template auto-numbering behavior.**
Before modifying `make_para()` or `make_data_table()`, consult this table.

### Core Principle

Each auto-numbered style has a `lvlText` pattern that generates the prefix
(e.g., "TABLE I.", "Fig. 1.", "[1]"). The paragraph text must contain ONLY
the descriptive content (the title/caption), NEVER the prefix that the style
generates automatically.

Adding a manual prefix causes **text duplication**: "TABLE I. TABLE I. Title".

### Style Registry

| Style ID | Style Name | numId | numFmt | lvlText | Text Content Rules |
|----------|-----------|-------|--------|---------|-------------------|
| `1` | Heading 1 | 4 | upperRoman | `%1.` | Descriptive title only. NO "I.", "II." prefix. |
| `2` | Heading 2 | 4 | upperRoman | `%1.` | Descriptive title only. NO "A.", "B." prefix. (H1/H2 share numId=4, sequential numbering across levels) |
| `figurecaption` | Figure Caption | 2 | decimal | `Fig. %1.` | Descriptive title only. NO "Fig. N." prefix. |
| `tablehead` | Table Head | 9 | upperRoman | `TABLE %1.` | Descriptive title only. NO "TABLE N." prefix. |
| `references` | References | 8 | decimal | `[%1]` | Entry body only. NO "[N]" prefix. |

### How Auto-Numbering Works

1. **Style definition** contains `<w:numPr><w:numId w:val="N"/></w:numPr>`
2. **Paragraph** uses `<w:pStyle w:val="styleId"/>` with NO explicit numPr (inherits style's numbering)
3. **Word** looks up numId → abstractNumId → reads `lvlText` pattern → prepends "TABLE I." etc.
4. **Counter** increments per paragraph using that style (numId + ilvl combination)

### Text Content Rules by Style

```python
# CORRECT: text = descriptive content only, style handles prefix
make_para('tablehead', "System Parameters for SBW-FMDA")
# Word renders: "TABLE I. System Parameters for SBW-FMDA"

# WRONG: text includes prefix → duplication
make_para('tablehead', "TABLE I. System Parameters for SBW-FMDA")
# Word renders: "TABLE I. TABLE I. System Parameters for SBW-FMDA"

# WRONG: num_id='0' → suppresses numbering entirely
make_para('tablehead', "System Parameters", num_id='0')
# Word renders: "System Parameters" (no TABLE I. prefix at all)
```

### num_id Parameter Usage

| Scenario | `num_id` value | Example |
|----------|---------------|---------|
| Normal auto-numbered style | `None` (omit) | `make_para('tablehead', text)` |
| Suppress auto-numbering | `'0'` | `make_para('1', 'References', num_id='0')` |
| **NEVER** | The style's own numId | Never pass `num_id='9'` to tablehead — it already inherits |

### Debugging Numbering Issues

If a style shows wrong or missing numbering:

1. Check this registry for the expected `lvlText`
2. Verify paragraph text does NOT contain the prefix
3. Check `<w:numPr>` in paragraph XML — should be absent (inherited from style)
4. Check `<w:pStyle w:val="styleId"/>` matches the expected style ID
5. Verify the abstractNumId definition in `word/numbering.xml`
