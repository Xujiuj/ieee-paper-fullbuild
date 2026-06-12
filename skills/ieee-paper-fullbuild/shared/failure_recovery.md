# Failure Recovery Protocol

When validation fails, the orchestrator follows this protocol:

## Step 1: Identify

Read the validator's failure report. Map each failed invariant to the responsible agent.

## Step 2: Triage

| Invariant | Agent | Fix Brief |
|-----------|-------|-----------|
| 1, 2, 3 (word/page) | `rewriter_agent` | Expand sections |
| 4 (authors) | `formatter_agent` | Preserve template authors |
| 5 (layout) | `formatter_agent` | Anchor on keywords |
| 6 (OMML) | `formatter_agent` | Use pandoc OMML |
| 7 (figures) | `visual_agent` | Generate more figures |
| 7.5 (equations) | `rewriter_agent` | Add display equations (>= 5) |
| 8 (letter img) | `visual_agent` | Replace image |
| 9, 10 (numbering) | `formatter_agent` | Remove manual prefixes |
| 11 (LaTeX) | `rewriter_agent` | Convert to plain English |
| 12 (Chinese) | `formatter_agent` | Run cleanup |
| 13 (indent) | `formatter_agent` | Strip cell indent |

## Step 3: Re-delegate → Step 4: Re-validate → Step 5: Max 3 retries
