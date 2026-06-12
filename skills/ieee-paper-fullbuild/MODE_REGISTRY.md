# Mode Registry

Single source of truth for all modes in ieee-paper-fullbuild plugin.

**2 modes** — each maps to a distinct pipeline. Each mode has a manual slash command entry point.

---

## ieee-paper-fullbuild (2 modes)

| Mode | Slash Command | Output | Oversight | Triggers |
|------|--------------|--------|-----------|----------|
| `rewrite` | `/ieee-rewrite` | IEEE-formatted .docx from existing paper | Autonomous | "改写论文", "rewrite paper", "IEEE format", "转成IEEE" |
| `scratch` | `/ieee-scratch` | IEEE-formatted .docx from title only | Autonomous | "从头写IEEE论文", "write IEEE paper from scratch" |

---

## Mode Selection Rules

| User provides | Mode | First agent | Work folder name |
|---------------|------|-------------|-----------------|
| Existing .docx or .pdf file | `rewrite` | `extractor_agent` | Source filename (sans extension) |
| Existing .md with full paper | `rewrite` | `rewriter_agent` (skip extraction) | Source filename (sans extension) |
| Title/topic only | `scratch` | `/ars-full` | Sanitized English title |

## Pipeline Comparison

```
rewrite:  extractor -> rewriter -> visual -> md gate -> formatter -> structure gate -> validator -> deliver
scratch:  /ars-full -> visual -> rewriter -> md gate -> formatter -> structure gate -> validator -> deliver
```

Both share the tail: **md gate -> formatter -> structure gate -> validator -> deliver**

## Autonomous Execution

All phases execute without user confirmation. The orchestrator auto-creates the work directory, runs each phase, verifies output, and proceeds. Only stops when validation fails after max retries (3 per invariant).

