---
name: extract
description: "Extract content from .docx/.pdf into structured Markdown with figures, tables, equations, references. Standalone or Phase 1 of pipeline. Triggers: extract paper, parse docx, 提取论文."
---

# IEEE Extract — Content Extraction

> Standalone: .docx/.pdf → structured Markdown + images.

**Output**: `paper.md` + `figures/` directory

---

## Quick Start

```
Extract content from this paper: @paper.docx
```

## Trigger Keywords

**English**: extract paper, parse docx, parse pdf, convert to markdown
**中文**: 提取论文, 解析docx, 转成markdown

## Workflow

```bash
python ${SKILL_DIR}/../../scripts/extract_docx.py \
       <source.docx> <output_dir>/paper.md <output_dir>/figures
```

## Output Format

- `# Title`, `## Abstract`, `**Keywords**:`
- `## I. SECTION_NAME` body sections
- `![Fig. N. Caption](file)` figures
- `$$...$$` equations, `| col | col |` tables
- `[N]` citations, `## REFERENCES` list
