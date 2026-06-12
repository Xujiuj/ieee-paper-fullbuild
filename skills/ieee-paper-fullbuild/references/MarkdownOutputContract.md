# Markdown Output Contract

This document is the **single source of truth** for the Markdown format that
`rewriter_agent` must produce and `formatter_agent` (via `format_ieee.py`)
must consume. Every rule here is enforced — deviation causes formatting bugs.

## How to Use

- **rewriter_agent**: Your output MUST match C1–C10. Run self-check before
  returning paper.md.
- **visual_agent**: Your images MUST comply with C4, C8, and C9.
- **formatter_agent**: Parse C1–C10 formats directly. Do NOT add defensive
  regex for deviations — they should not exist.
- **validate.py**: Optional preflight checks reference these rules.

---

## C1. Abstract Format

**The abstract MUST start with the bold keyword `Abstract` followed by an
em-dash (—), en-dash (–), or hyphen (-).**

```
**Abstract** — The abstract text begins here and continues for one or more
sentences. Multiple paragraphs are joined with spaces into a single block.
```

**Rules:**
- MUST use `**Abstract**` (markdown bold), not `## Abstract` (heading)
- Separator after `**Abstract**` must be `—`, `–`, or `-` (em-dash, en-dash, or hyphen)
- Abstract text follows immediately on the same line (or next non-empty line)
- The abstract block ends at the first `##` heading, `**` bold line, `---`, or blank line
- DO NOT include the word "Abstract" in the body text — it lives only in the template header

**Self-check:** The first content line of paper.md (after title) must match:
`**Abstract** —` or `**Abstract** –` or `**Abstract** -`

---

## C2. Index Terms / Keywords

**Keywords appear immediately after the abstract as a bold line.**

```
**Keywords** — term1, term2, term3, term4, term5
```

**Rules:**
- MUST use `**Keywords**` (markdown bold) with em-dash/en-dash/hyphen separator
- 3–6 terms, comma-separated, lowercase (except proper nouns)
- No period at the end
- Appears on its own line between abstract and first `##` heading

**Self-check:** Line matching `\*\*Keywords?\*\*\s*[—–-]\s*.+` exists.

---

## C3. Section Headings

```
## I. Introduction
## II. Related Work
## III. System Design
### A. Hierarchical Permission Model
### B. Visualization Architecture
## IV. Implementation
## V. Evaluation
## VI. Conclusion
```

**Rules:**
- Level-1 headings: `## ` prefix + Roman numeral + `. ` + Title
- Level-2 headings: `### ` prefix + Letter + `. ` + Title
- Titles use Title Case, no trailing period
- Roman numerals: I, II, III, IV, V, VI (typical range for 6–8 page paper)
- Letters: A, B, C, D, ...
- The template auto-numbers headings — the Roman/letter prefixes are for
  readability only; `format_ieee.py` strips them before insertion

**Self-check:** Every `## ` line matches `## [IVX]+\.\s+` and every `### ` line matches `### [A-Z]\.\s+`.

---

## C4. Figure References (Strict Format)

```
![Fig. 1. Descriptive caption text](fig1_name.png)
```

**Rules:**
- MUST match exactly: `![Fig. N. Caption](filename.png)`
- `N`: consecutive integer starting from 1 (1, 2, 3, ...)
- Caption: ≤12 English words, NO "Fig. N." prefix (template auto-numbers)
- Caption: NO trailing punctuation — no period, comma, semicolon, question/exclamation mark
- Caption is a concise noun phrase, not a sentence
- Filename: `fig{n}_{name}.png` where n matches the figure number
- All figures in paper.md must have sequential numbering with no gaps
- Text references in body must use the format `Fig. N.` (e.g., "as shown in Fig. 1")

**Self-check:** Extract all `![Fig. N.` — numbers must be `[1, 2, 3, ...]` with no gaps.

**Example (correct):**
```markdown
![Fig. 1. Five-tier hierarchical RBAC model](fig1_rbac_hierarchy.png)
![Fig. 2. Permission matrix visualization](fig2_permission_matrix.png)
The system architecture is illustrated in Fig. 3.
```

**Example (WRONG — will cause bugs):**
```markdown
![Figure 1: Five-tier hierarchical RBAC model](fig1_rbac_hierarchy.png)  ← "Figure" not "Fig."
![Fig. 1. Five-tier RBAC model with detailed annotations and labels](fig1.png)  ← caption too long
```

---

## C5. Tables (Strict Format)

```
**TABLE I. Short Descriptive Title**

| Column A | Column B | Column C |
|----------|----------|----------|
| data     | data     | data     |
```

**Rules:**
- Caption MUST start with `**TABLE` (markdown bold) — this is how the formatter detects it
- Format: `**TABLE {Roman}. {Title}**` where Roman is I, II, III, ...
- Title: ≤8 English words, NO "TABLE N." prefix (template auto-numbers)
- NO trailing punctuation — no period, comma, semicolon, question/exclamation mark
- Title is a concise noun phrase, not a sentence
- Blank line before the caption, blank line after the table
- The caption is the ONLY line before the `|` table — no other text between

**Self-check:** Every table is preceded by a line matching `\*\*TABLE\s+[IVXLCDM]+\.\s*`.

**Example (correct):**
```markdown
**TABLE I. Task Completion Time Comparison**

| Method | Avg. Time (s) | Accuracy (%) |
|--------|---------------|--------------|
| Manual | 45.2 | 78.3 |
```

**Example (WRONG — will cause bugs):**
```markdown
TABLE I. Task Completion Time Comparison
  ← missing ** bold markers; not detected by formatter

**TABLE I. Comparison of task completion time across different management approaches in university project settings**
  ← title too long (>8 words); will overflow caption area
```

---

## C6. Display Equations

```
$$
E = mc^2
\tag{eq:1}
$$
```

**Rules:**
- MUST use `$$...$$` delimiters with `\tag{eq:N}` inside
- `N`: consecutive integer starting from 1
- The `\tag{eq:N}` must be on its own line before the closing `$$`
- LaTeX must be valid (convertible by pandoc)
- At least 5 equations expected for invariant 7.5

**Self-check:** Extract all `\tag{eq:N}` — numbers must be `[1, 2, 3, ...]` with no gaps, count ≥ 5.

---

## C7. References

```
## REFERENCES

[1] A. Author, "Title of paper," *Journal Name*, vol. 10, no. 2, pp. 100-110, 2024.
[2] B. Author and C. Author, "Another paper title," in Proc. IEEE Conference, 2023, pp. 50-60.
```

**Rules:**
- Heading: `## REFERENCES` (case-sensitive, all caps)
- Entries: `[N]` prefix followed by IEEE citation format
- Maximum **15** references
- Body citations `[N]` must be consistent with reference list
- Reference list sorted by first-appearance order in body text
- No duplicate numbers

**Self-check:** Count `[N]` entries in REFERENCES section ≤ 15. All body citations `[N]` have corresponding entry.

---

## C8. Image Content Rules

**ALL images generated by `/gpt-image` or any image generation tool MUST NOT contain:**
- Figure numbers (Fig. 1, Figure 1, etc.)
- Title text or caption text
- English labels or annotations inside the image
- Axis labels with text (use numeric scales only)

**Required in image generation prompts:**
Append this to every prompt:
```
No text, no labels, no figure numbers, no captions inside the image.
Pure visual/technical diagram only. Clean white background.
```

**Allowed in images:**
- Color-coded regions, shapes, arrows, lines
- Numerical values on axes
- Color legends (swatches without text labels)
- Geometric patterns, flow diagrams (visual flow only)

**Self-check:** Before returning generated images, visually verify no text appears in them.

---

## C9. Cross-Reference Completeness (HARD GATE)

⛔ **This is a HARD GATE. Failure blocks pipeline progression from Phase 3 to Phase 4.**

**Every figure and table defined in the document MUST be explicitly cited (referenced) in the body text.**

**Rules:**
- For every `![Fig. N. Caption](file.png)`, the body text MUST contain at least one occurrence of `Fig. N.` (e.g., "as shown in Fig. 1")
- For every `**TABLE N. Title**`, the body text MUST contain at least one occurrence of `Table N.` (e.g., "as listed in Table I")
- The reference should appear in a natural sentence, NOT as a standalone line
- Figures and tables that are defined but never cited in body text are "orphans" — this is a **HARD GATE FAILURE**, not a warning

**Self-check:** For each figure number N found in `![Fig. N.]`, grep body text for `Fig. N.`. For each table numeral found in `**TABLE N.**`, grep body text for `Table N.`. All must match.

**Example (correct):**
```markdown
![Fig. 1. Algorithm convergence curves](fig1_convergence.png)

The convergence behavior of the proposed algorithm is shown in Fig. 1,
where the objective function value decreases monotonically over iterations.
```

**Example (WRONG — orphan figure):**
```markdown
![Fig. 3. Performance comparison](fig3_performance.png)

The results demonstrate significant improvement over baselines.
  ← Fig. 3 is never mentioned in body text
```

---

## C10. Reference Format Purity (No Markdown Symbols)

**Reference entries in the REFERENCES section MUST NOT contain any Markdown formatting symbols.**

**Rules:**
- NO `**bold**` markers — strip to plain text
- NO backtick code spans `` ` `` — strip to plain text
- NO strikethrough `~~` — strip to plain text
- Single `*italic*` for journal/conference names IS acceptable per IEEE convention
  (e.g., `*IEEE Trans. Pattern Anal. Mach. Intell.*`) — do NOT strip these
- All other Markdown symbols (`**`, `` ` ``, `~~`, `_` as emphasis) must be removed

**Self-check:** Scan each line in the REFERENCES section for `**`, `` ` ``, `~~`.
Found = violation. Single `*` around journal names = OK.

**Example (correct):**
```markdown
[1] A. Smith and B. Jones, "Efficient gradient descent algorithm," *IEEE Trans. Neural Netw.*, vol. 35, no. 2, pp. 100-110, 2024.
```

**Example (WRONG):**
```markdown
[1] A. Smith and B. Jones, **Efficient gradient descent algorithm**, `IEEE Trans. Neural Netw.`, vol. 35, 2024.
  ← bold and backtick markers are Markdown residue from source paper
```

---

## Appendix: Quick Self-Check Checklist

Before returning `paper.md`, verify:

| Rule | Check | How |
|------|-------|-----|
| C1 | `**Abstract** —` present | Grep first 5 lines |
| C2 | `**Keywords** —` present | Grep after abstract |
| C3 | All `## ` start with Roman numeral | Regex `## [IVX]+\.` |
| C4 | All `![Fig. N.` sequential | Extract numbers, check gapless |
| C5 | All tables have `**TABLE` caption | Grep `\*\*TABLE` |
| C6 | All `$$` have `\tag{eq:N}` | Count tags ≥ 5 |
| C7 | References ≤ 15 | Count `[N]` in REFERENCES |
| C8 | Generated images have no text | Visual inspection |
| C9 | Every Fig/Table cited in body | Grep body for `Fig. N.` / `Table N.` |
| C10 | No markdown symbols in refs | Scan refs for `**`, `` ` ``, `~~` |
