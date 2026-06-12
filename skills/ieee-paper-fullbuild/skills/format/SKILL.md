---
name: format
description: "Convert Markdown into IEEE-formatted Word document. Runs format_ieee.py. Standalone or Phase 4. Triggers: format IEEE, 排版IEEE, 转成IEEE."
---

# IEEE Format — Word Formatting

> Standalone: Markdown → IEEE .docx

## Quick Start

```
Format this paper for IEEE: @paper.md
```

## Workflow

```bash
python ${SKILL_DIR}/../../scripts/format_ieee.py \
       <template.docx> <source.md> <figures_dir> <output.docx>

python ${SKILL_DIR}/../../scripts/check_docx_structure.py \
       <output.docx> <template.docx>
```
