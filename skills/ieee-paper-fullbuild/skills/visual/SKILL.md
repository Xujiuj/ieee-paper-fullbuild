---
name: visual
description: "Generate and manage figures for IEEE papers. Delegates to /nature-figure and /gpt-image. Standalone or Phase 3. Triggers: generate figures, 生成图表."
---

# IEEE Visual — Figure Management

> Standalone: manage figures for IEEE papers.

**Delegates to**: `/nature-figure` (plots), `/gpt-image` (diagrams)

## Quick Start

```
Generate figures for this paper: @paper.md
```

## Workflow

1. Scan markdown for figure references
2. Data plots → `/nature-figure`; diagrams → `/gpt-image`
3. Save matching markdown references
