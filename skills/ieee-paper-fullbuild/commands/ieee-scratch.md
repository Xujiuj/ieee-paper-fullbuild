---
description: IEEE paper from scratch — full ARS pipeline → IEEE-formatted Word
model: opus
---

Generate an IEEE conference paper from scratch on the given topic, using the complete `ieee-paper-fullbuild` orchestrator in **scratch mode**.

## What to do

1. Load the orchestrator: `ieee-paper-fullbuild/SKILL.md`
2. Determine mode: `scratch`
3. Create work directory named after sanitized English title
4. Execute the 6-gate pipeline **autonomously** (no user confirmation between phases):

```
Phase 1: GENERATE   → /ars-full pipeline    → Full Markdown
Phase 2: VISUALS    → [visual_agent]        → Figures generated
Phase 3: POLISH     -> [rewriter_agent]      -> Polished Markdown
Phase 3.5: MD GATE  -> [validate_md.py] + [md_validator_agent] -> structured Markdown PASS
Phase 4: FORMAT     -> [formatter_agent]     -> IEEE Word
Phase 4.5: STRUCTURE -> [check_docx_structure.py] -> template invariants PASS
Phase 5: VALIDATE   -> [validator_agent]     -> 15/15 PASS -> Deliver
```

## Input

The user provides a **title/topic** (Chinese or English). Translate to English if needed.

## ARS defaults (auto-answer all ARS questions)

| Question | Default |
|----------|---------|
| Paper type | Original research with novel algorithmic contribution |
| Methodology | Algorithm design + theoretical analysis + experimental evaluation |
| Scope | Focused on specific computational problem |
| Contribution | Novel algorithm/method + theoretical analysis + empirical evaluation |
| Target venue | IEEE conference |
| Language | English |
| Page limit | 6-8 pages |
| Word count | 3500+ words |

⛔ **Algorithm-focus enforcement**: Title MUST contain algorithmic keyword. Introduction/Related Work emphasizes algorithmic literature. See `references/ars-defaults.md` for full Content Focus Directive.

## Output

Report to user:
- Final file path: `<work_dir>/<title>.docx`
- Word count, page count, figure/equation/table/reference counts
- Validation result: 15/15 PASS

## References

- Orchestrator: `ieee-paper-fullbuild/SKILL.md`
- Mode registry: `ieee-paper-fullbuild/MODE_REGISTRY.md`
- ARS defaults: `ieee-paper-fullbuild/references/ars-defaults.md`
