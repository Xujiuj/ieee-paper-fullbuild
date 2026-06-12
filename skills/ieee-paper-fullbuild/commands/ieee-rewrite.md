---
description: IEEE paper from existing file — extract → polish → format → IEEE Word
model: opus
---

Convert an existing paper (.docx, .pdf, or .md) into IEEE conference format, using the `ieee-paper-fullbuild` orchestrator in **rewrite mode**.

## What to do

1. Load the orchestrator: `ieee-paper-fullbuild/SKILL.md`
2. Determine mode: `rewrite`
3. Create work directory named after source filename (sans extension)
4. Execute the 6-gate pipeline **autonomously** (no user confirmation between phases):

```
Phase 1: EXTRACT    → [extractor_agent]   → Markdown + images
Phase 2: POLISH     → [rewriter_agent]    → Polished Markdown
Phase 3: VISUALS    -> [visual_agent]      -> Figures ready
Phase 3.5: MD GATE  -> [validate_md.py] + [md_validator_agent] -> structured Markdown PASS
Phase 4: FORMAT     -> [formatter_agent]   -> IEEE Word
Phase 4.5: STRUCTURE -> [check_docx_structure.py] -> template invariants PASS
Phase 5: VALIDATE   -> [validator_agent]   -> 15/15 PASS -> Deliver
```

## Input

The user provides an **existing file** (.docx, .pdf, or .md).

| Source format | First agent |
|---------------|-------------|
| .docx / .pdf  | `extractor_agent` (Phase 1: extract content + images) |
| .md           | `rewriter_agent` (skip extraction, start at polish) |

## Behavior

- **Language**: All output in English. If source is Chinese → extract → translate → polish → format in English.
- **Content**: Preserve all original content. Expand if below 3500 words.
- **Algorithm focus**: Rewrite title to emphasize algorithmic contribution. Prune application-domain literature from Introduction/Related Work. See `references/ars-defaults.md` for Content Focus Directive.
- **Cross-references**: Ensure every figure/table is cited in body text (C9).
- **Reference cleanup**: Strip markdown symbols from references (C10).
- **Figures**: Reuse extracted figures. Generate new ones if missing (via `/gpt-image` or `/nature-figure`).

## Output

Report to user:
- Final file path: `<work_dir>/<source_filename>.docx`
- Word count, page count, figure/equation/table/reference counts
- Validation result: 15/15 PASS

## References

- Orchestrator: `ieee-paper-fullbuild/SKILL.md`
- Mode registry: `ieee-paper-fullbuild/MODE_REGISTRY.md`
- Failure recovery: `ieee-paper-fullbuild/shared/failure_recovery.md`
