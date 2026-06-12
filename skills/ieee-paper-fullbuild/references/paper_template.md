# IEEE Conference Paper — Strict Markdown Template
#
# RULES:
# - This template defines the EXACT structure of paper.md
# - Agents MUST fill [PLACEHOLDER] values without changing structure
# - HTML comments (<!-- -->) contain format rules — follow them strictly
# - After filling, run: python scripts/validate_md.py paper.md
#
# Quick Reference (C1-C10 + Extensions):
#   C1: Abstract must start with **Abstract** — (NOT ## Abstract)
#   C2: Keywords must use **Keywords** — format
#   C3: H1 = ## I. Title | H2 = ### A. Title (Roman numerals + Letters)
#   C4: Figures = ![Fig. N. Caption](file.png) | sequential N, ≤12 words, no trailing punctuation
#   C5: Tables = **TABLE N. Title** | ≤8 words, no trailing punctuation, then blank line + | data |
#   C6: Equations = $$...\tag{eq:N}$$ | sequential N, ≥5 equations
#   C7: References ≤ 15, ## REFERENCES heading (all caps)
#   C8: Generated images must contain no text/labels (handled by visual_agent)
#   C9: Every Fig./TABLE MUST be cited in body text as Fig. N. / Table N.
#   C10: No **bold** or `code` in reference entries (single *italic* for journals OK)
#   EXT: ≥3500 words, no Chinese, no raw LaTeX (\cite{}, \frac{})

# [TITLE — plain text, ≤15 words, must contain algorithmic keyword]
<!-- C3: Title is plain text, no markdown formatting -->
<!-- EXT: Title must contain at least one algorithmic keyword (algorithm, model, optimization, framework, method, network, learning, detection, prediction, classification, etc.) -->

**Abstract** — [ABSTRACT TEXT HERE. 150-250 words. Single paragraph. Summarize the problem, proposed algorithm/method, key results, and significance. Do NOT use ## Abstract heading.]
<!-- C1: MUST start with **Abstract** — (bold keyword + em-dash). NOT ## Abstract -->
<!-- C1: Abstract text is one continuous paragraph, no line breaks within -->

**Keywords** — [keyword1, keyword2, keyword3, keyword4, keyword5]
<!-- C2: MUST use **Keywords** — (bold keyword + em-dash) -->
<!-- C2: 3-6 terms, comma-separated, lowercase except proper nouns, no period at end -->

---

<!-- Body sections start here. Each H1 section should be ≥280 words. -->

## I. [Introduction]
<!-- C3: H1 format: ## + Roman numeral + . + Space + Title Case -->
<!-- C3: Do NOT add manual numbering — the template auto-numbers. Roman numerals here are for readability only and are stripped by format_ieee.py -->

[Body paragraph text here. Citations use [N] format (e.g., [1], [2]). Inline math uses $...$ format (e.g., $x^2$). Reference figures as Fig. N. and tables as Table N. in natural sentences.]

[Body paragraph. Each paragraph should be substantive academic prose, not placeholder text.]

<!-- C9: Every figure defined below MUST be referenced in body text as "Fig. N." -->
<!-- C9: Every table defined below MUST be referenced in body text as "Table N." -->

## II. [Related Work]
<!-- C3: Sequential Roman numeral -->

### A. [Subsection Title]
<!-- C3b: H2 format: ### + Letter + . + Space + Title Case -->

[Body text...]

### B. [Another Subsection]

[Body text...]

## III. [Methodology / Proposed Approach]

### A. [Framework Overview]

[Body text describing the overall approach. Reference figures as needed.]

![Fig. 1. [DESCRIPTIVE CAPTION — ≤12 words, noun phrase, no trailing punctuation]](fig1_[name].png)
<!-- C4: Caption ≤12 words, noun phrase (not a sentence), no trailing .,;:!? -->
<!-- C4: Filename must be figN_[name].png where N matches figure number -->
<!-- C9: The body text above MUST contain "Fig. 1." in a natural sentence -->

[Body text continuing after the figure.]

### B. [Algorithm Design]

[Body text with detailed algorithm description. Include mathematical formulations.]

$$
[EQUATION_LATEX_HERE]
\tag{eq:1}
$$
<!-- C6: Block equation format: $$ on own lines, \tag{eq:N} on line before closing $$ -->
<!-- C6: N must be sequential starting from 1. At least 5 equations total required -->
<!-- C6: LaTeX must be valid — no double backslashes (use \alpha not \\alpha) -->

[Body text explaining the equation. Reference it naturally, e.g., "as defined in (1)."]

$$
[EQUATION_LATEX_HERE]
\tag{eq:2}
$$

[More body text with algorithmic detail.]

### C. [Complexity Analysis]

[Body text analyzing computational complexity.]

$$
[EQUATION_LATEX_HERE]
\tag{eq:3}
$$

## IV. [Experimental Setup / Evaluation]

### A. [Datasets and Baselines]

[Body text describing experimental configuration.]

**TABLE I. [SHORT TABLE TITLE — ≤8 words, noun phrase, no trailing punctuation]**

| [Column A] | [Column B] | [Column C] |
|------------|------------|------------|
| [data]     | [data]     | [data]     |
| [data]     | [data]     | [data]     |
<!-- C5: Table caption MUST be **bold**, format: **TABLE N. Title** -->
<!-- C5: Title ≤8 words, noun phrase, no trailing .,;:!? -->
<!-- C5: Blank line between caption and table data is REQUIRED -->
<!-- C9: The body text above MUST contain "Table I." in a natural sentence -->

### B. [Results and Analysis]

[Body text presenting results with analysis.]

![Fig. 2. [RESULTS FIGURE CAPTION — ≤12 words]](fig2_[name].png)
<!-- C4: Sequential figure number (2), ≤12 words, no trailing punctuation -->

**TABLE II. [ANOTHER TABLE TITLE — ≤8 words]**

| [Method] | [Metric 1] | [Metric 2] |
|----------|------------|------------|
| [data]   | [data]     | [data]     |

$$
[EQUATION_LATEX_HERE]
\tag{eq:4}
$$

### C. [Ablation Study]

[Body text with ablation analysis.]

![Fig. 3. [ABLATION FIGURE CAPTION]](fig3_[name].png)

**TABLE III. [ABLATION TABLE TITLE]**

| [Config] | [Result] |
|----------|----------|
| [data]   | [data]   |

## V. [Discussion / Analysis]

[Body text discussing implications, insights, and limitations.]

$$
[EQUATION_LATEX_HERE]
\tag{eq:5}
$$

![Fig. 4. [DISCUSSION FIGURE CAPTION]](fig4_[name].png)

## VI. [Conclusion]

[Body text summarizing contributions and future work.]

<!-- Note: ACKNOWLEDGMENT section is optional. Include if needed. -->

## ACKNOWLEDGMENT
<!-- Remove this entire section if no acknowledgment is needed -->

[Acknowledgment text here.]

## REFERENCES
<!-- C7: Heading MUST be exactly "## REFERENCES" (all caps) -->
<!-- C7: Maximum 15 references -->
<!-- C7: References sorted by first-appearance order in body text -->
<!-- C10: No **bold** or `code` markers in references. Single *italic* for journal names is OK -->
<!-- C10: Each reference in IEEE format: [N] Author, "Title," *Journal*, vol. X, no. Y, pp. Z-W, Year. -->

[1] A. Author and B. Author, "Title of paper," *Journal Name*, vol. X, no. Y, pp. Z-W, Year.
[2] C. Author, "Another title," in *Proc. IEEE Conference*, City, Country, Year, pp. Z-W.
<!-- Add up to [15] references. Each must be in proper IEEE citation format. -->
