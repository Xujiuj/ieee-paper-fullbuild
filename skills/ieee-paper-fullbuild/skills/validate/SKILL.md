---
name: validate
description: "Validate IEEE Word documents against 15 invariants. Read-only. Standalone or Phase 5. Triggers: validate IEEE, 验证论文."
---

# IEEE Validate — Quality Gate

> Standalone: validate .docx against 15 invariants. Read-only.

## Quick Start

```
Validate this IEEE paper: @output.docx
```

## Workflow

```bash
python ${SKILL_DIR}/../../scripts/validate.py <output.docx> <template.docx>
python ${SKILL_DIR}/../../scripts/check_docx_structure.py <output.docx> <template.docx>
```
