# Template Inspection Guide

## Purpose

Inspect an IEEE Word template to record the data the formatter needs:

- Style IDs (papertitle, Abstract, Keywords, Heading 1, Body Text,
  figurecaption, references, equation, etc.)
- Auto-numbering map (which styles carry numId, what level)
- sectPr layout (single-column / two-column transitions)
- Table border w:sz value
- Original Author/Affiliation paragraph fingerprints

## Tool

Run `${SKILL_DIR}/scripts/inspect_template.py <template.docx>`. The
script outputs a JSON report. Pass an output path to persist it:

```bash
python .claude/skills/ieee-paper-fullbuild/scripts/inspect_template.py \
       template/IEEE.docx \
       paper/<id>/template_map.json
```

## What to verify

The output report should show:

- `styles.papertitle.present == true`
- `styles.Author.present == true` and `styles.Affiliation.present == true`
- `styles["1"].auto_numbered == true` (Heading 1 uses numId)
- `styles.figurecaption.auto_numbered == true`
- `styles.references.auto_numbered == true`
- `styles.tablehead.auto_numbered == true`
- At least 2 entries in `sectPr_map` with `two_column == true`
- `table_border_sz` is a positive integer string (typically "2")
- `authors` lists at least one cleaned author name
- `affiliations` lists at least one cleaned affiliation

If any of these is missing, the template is incompatible with the IEEE
paper full-build pipeline. Report the issue to the user; do not proceed.

## Auto-numbering reference

Common IEEE templates use these `numId` assignments:

| Style | numId | Effect |
|-------|-------|--------|
| 1 (Heading 1) | 4 | "I.", "II.", "III.", ... |
| 2 (Heading 2) | 4 | "A.", "B.", "C.", ... |
| 3 (Heading 3) | 4 | "1)", "2)", "3)", ... |
| figurecaption | 2 | "Fig. 1.", "Fig. 2.", ... |
| tablehead | 9 | "TABLE I.", "TABLE II.", ... |
| references | 8 | "[1]", "[2]", "[3]", ... |
| equation | (varies, often manual) | "(1)", "(2)" via tab stop |

If the template's numId values differ, the formatter must respect them
exactly; never substitute.
