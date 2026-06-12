# Validation Checks (15 Invariants)

This document is the canonical reference for the 15 invariants used by
the `ieee-validator` subagent and the `ieee-paper-fullbuild` skill.

The implementation script lives at
`${SKILL_DIR}/scripts/validate.py` and is invoked as:

```bash
python .claude/skills/ieee-paper-fullbuild/scripts/validate.py \
       <output.docx> <template.docx>
```

It returns exit code 0 if all 15 PASS, 1 otherwise. Stdout contains one
line per invariant: `<n>. PASS|FAIL: <detail>`.

## The 15 Invariants

| # | Check | PASS criterion | Source signal |
|---|-------|---------------|---------------|
| 1 | Total word count | >= 3500 | join all w:t, split |
| 2 | Body word count | >= 3000 | only paragraphs with style "a3" or "1" |
| 3 | Estimated page count | 6.0 to 10.0 | body/750 + figs*0.35 + eqs*0.08 + 0.5 |
| 4 | Authors and affiliations preserved | Author/Affiliation paragraph texts match template exactly | style-scoped paragraph text compare |
| 5 | Two-column section | >= 2 sectPr blocks with w:num="2" | regex over sectPr |
| 6 | Structural OMML | >= 1 of m:f / m:nary / m:sSub / m:sSup / m:d / m:rad | substring count (covers both display and inline equations) |
| 7 | Figure count | 6 to 10 inclusive | count of `<a:blip` |
| 7.5 | Equation count | >= 5 | count equation labels (N) in w:t elements |
| 8 | No letter images | aspect < 1 AND white_ratio > 0.5 forbidden | PIL classify each word/media/* |
| 9 | Template heading styles | No synthetic Heading1/Heading2 and no manual heading prefixes | paragraph style + text regex |
| 10 | No manual [n] in references | references paras must not start with `[1]` `[2]` | regex on first text run |
| 11 | No raw LaTeX | No `\cite{` `\frac{` `\mathcal{` `\textbf{` | substring search |
| 12 | No Chinese outside author metadata | No Chinese outside preserved Author/Affiliation paragraphs | style-scoped paragraph XML regex |
| 13 | Stripped cell indent | Every w:ind in w:tc has firstLine="0" | regex per cell |
| 14 | No manual/bold captions | figurecaption/tablehead text has no manual Fig./TABLE prefix and tablehead is not bold | caption paragraph regex |

## Failure-to-Fix Mapping

| Failed invariant | Re-delegate to | Brief modifier |
|------------------|----------------|----------------|
| 1, 2, 3 | paper-rewriter | "Expand each section by N words" where N = (3500 - current_total) / 7 |
| 4 | ieee-formatter | "Author Preservation Rule was violated; reload template authors verbatim" |
| 5 | ieee-formatter | "Anchor inserted content on the keywords paragraph; do not anchor after references-sectPr" |
| 6 | ieee-formatter | "Use pandoc-generated OMML for every display equation; verify structural elements present" |
| 7 | ieee-formatter | "Insert N more figures from the source figure pool; current count below 6" |
| 7.5 | paper-rewriter | "Add more display equations (>= 5 required); use $$...\\tag{eq:N}$$ format" |
| 8 | ieee-formatter | "Reject offending image; pick another from the source pool" |
| 9, 10 | ieee-formatter | "Remove manual numeric prefix; trust template's numId" |
| 11 | paper-rewriter | "Source markdown contains raw LaTeX; convert to plain English" |
| 12 | ieee-formatter | "Run mojibake/Chinese cleanup pass on rFonts and w:t elements" |
| 13 | ieee-formatter | "Strip indent (firstLine=0, left=0, right=0) on every w:p inside every w:tc" |

## Known Non-Invariant Issues (caught by manual review)

| Issue | Agent | Fix |
|-------|-------|-----|
| Abstract in body text (F19) | ieee-formatter | Remove `## Abstract` section from body_lines |
| Table caption doubled (F20) | ieee-formatter | Skip caption text in flush_para_and_try_table() |
| Inline math literal (F21) | ieee-formatter | Use inline_latex_to_omml() in make_para_with_formatting() |
| `**` symbols in output (F22) | ieee-formatter | Use make_para_with_formatting() for body text |
| Orphan figures/tables (C9) | rewriter | Add "Fig. N." / "Table N." reference in body text for each orphan |
| Markdown in references (C10) | rewriter | Strip `**`, `` ` ``, `~~` from reference text; preserve single `*` for journals |

## MarkdownOutputContract Consistency Checks

These checks validate that the Markdown source conforms to the contract
(`references/MarkdownOutputContract.md`). They run as preflight in
`format_ieee.py` and as self-check in `rewriter_agent`.

⛔ **HARD checks block pipeline progression.** SOFT checks are warnings only.

| Contract Rule | Check | Level | Warning Trigger | Agent |
|--------------|-------|-------|-----------------|-------|
| C1 | Abstract format `**Abstract** —` | SOFT | Missing bold abstract line | rewriter |
| C2 | Keywords format `**Keywords** —` | SOFT | Missing bold keywords line | rewriter |
| C4 | Figure numbers sequential 1,2,3... | HARD | Gap or duplicate in numbering | rewriter |
| C5 | Table caption format `**TABLE N. Title**` | HARD | Missing or malformed caption | rewriter |
| C5 | Table caption length ≤8 words | SOFT | Caption exceeds 8 words | rewriter |
| C6 | Equation count ≥5 | HARD | Fewer than 5 `\tag{eq:N}` | rewriter |
| C7 | Reference count ≤15 | SOFT | More than 15 `[N]` entries | rewriter |
| C8 | No text in generated images | SOFT | Visual inspection fails | visual |
| C9 | Every figure/table cited in body | **HARD** | Orphan figure or table not referenced in text | rewriter |
| C10 | No markdown symbols in references | HARD | `**`, `` ` ``, `~~` found in reference entries | rewriter |

**Enforcement**: HARD failures in rewriter_agent's `contract_check()` MUST
block the output — the rewriter must fix the issue and re-run the check
before returning paper.md. SOFT failures produce warnings but do not block.

## Implementation

The full Python implementation is in
`${SKILL_DIR}/scripts/validate.py`. See that file for the canonical
source. The validator subagent should invoke it directly rather than
re-implementing the checks.
