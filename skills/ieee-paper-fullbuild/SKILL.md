---
name: ieee-paper-fullbuild
description: "IEEE conference paper formatting plugin. 2 modes (rewrite/scratch). 5-agent pipeline. English-only output. Algorithm-focused content strategy. Auto-answers ARS with algorithm-biased defaults. Enforces cross-reference completeness (C9) and reference format purity (C10). Rejects survey and application-focused papers. Delegates to /nature-polishing, /nature-figure, /gpt-image, /ars-full. Triggers: IEEE paper, conference paper, 转成IEEE, IEEE会议论文, 改写论文, 从头写IEEE论文."
metadata:
  version: "1.5.0"
  last_updated: "2026-06-12"
  status: active
  related_skills:
    - nature-polishing
    - nature-figure
    - gpt-image
    - academic-research-skills (ARS)
---

# IEEE Paper Full Build — Orchestrator Plugin

> You are the orchestrator. You do NOT do specialized work yourself.
> You delegate to agents, receive their results, and make decisions.
> **You execute autonomously — no user confirmation between phases.**

**2 modes**: `rewrite` (existing paper) | `scratch` (from title)

---

## Quick Start

**Slash commands** (manual entry points):

| Command | Mode | Usage |
|---------|------|-------|
| `/ieee-scratch` | scratch | Write an IEEE paper from a title/topic |
| `/ieee-rewrite` | rewrite | Convert an existing paper (.docx/.pdf/.md) to IEEE format |

**Mode A — Rewrite existing paper:**
```
Rewrite this paper for IEEE conference: @paper.docx
```

**Mode B — From scratch:**
```
Write an IEEE paper on lightweight YOLO for edge detection
```

---

## Trigger Conditions

### Trigger Keywords

**English**: IEEE paper, conference paper, IEEE format, rewrite paper, format paper, convert to IEEE

**中文**: 转成IEEE, IEEE会议论文, 改写论文, 从头写IEEE论文, 会议论文格式

### Does NOT Trigger

| Scenario | Use Instead |
|----------|-------------|
| Nature/Science journal paper | `/nature-polishing` alone |
| General academic writing | ARS `academic-paper` |
| Just polishing English | `/nature-polishing` |
| Pure literature review / survey | **REJECT** — not eligible for this plugin |

---

## Language Policy

⛔ **HARD RULE**: All output is **English only**, regardless of input language.

| Input language | Behavior |
|----------------|----------|
| Chinese title/topic | Translate to English, generate English paper |
| Chinese source .docx | Extract → translate → polish → format in English |
| English | Proceed as-is |

- ARS questions and answers: always in English
- Rewriter output: always English
- All agent communication: English
- The only Chinese allowed: the user's initial trigger command

---

## Content Policy

⛔ **REJECT** pure survey/literature-review articles. This plugin is for **original research papers** with experimental/analytical contributions.

⛔ **ALGORITHM-FOCUS POLICY**: The paper's core contribution MUST be algorithmic
(a novel algorithm, model, optimization method, or computational framework).
Application domain is validation context ONLY, not the contribution itself.

**Eligible**: Papers proposing novel algorithms, computational models, optimization
methods with experimental validation on benchmarks or datasets.

**NOT eligible**: Pure literature surveys, application-focused papers without
algorithm novelty, opinion pieces, organizational/management studies.

If ARS proposes an application-focused paper, redirect to algorithm framing or reject.
See `references/ars-defaults.md` for the full Content Focus Directive.

---

## Work Directory Strategy

🚧 **GATE**: Before any agent runs, create the work directory.

| Mode | Folder name source | Example |
|------|-------------------|---------|
| `scratch` | Sanitized paper title (English) | `Innovation-in-Full-Process-Bidding/` |
| `rewrite` (.docx/.pdf) | Source filename without extension | `SM383/` |
| `rewrite` (.md) | Source filename without extension | `paper/` |

### Naming Rules

1. **Translate** Chinese titles to English first
2. **Sanitize**: replace spaces with hyphens, remove special characters (`/`, `\`, `:`, `*`, `?`, `"`, `<`, `>`, `|`)
3. **Truncate** to 80 characters max
4. **Lowercase** the result

### Directory Structure

```
<work_dir>/
  paper.md          ← intermediate markdown
  figures/          ← all figures
  <name>.docx       ← final IEEE output (same name as folder)
```

### Final Output Naming

The output `.docx` file uses the **same name as the work directory**:

| Mode | Output file |
|------|-------------|
| `scratch` | `<work_dir>/<title>.docx` |
| `rewrite` | `<work_dir>/<source_filename>.docx` |

Example: scratch title "Innovation-in-Full-Process-Bidding" → `Innovation-in-Full-Process-Bidding/Innovation-in-Full-Process-Bidding.docx`

---

## Agent Team (5 Agents / 5 Standalone Skills)

Each agent is also a standalone skill that can be invoked independently.

| # | Agent | Skill | Role | Phase |
|---|-------|-------|------|-------|
| 1 | `extractor_agent` | `${SKILL_DIR}/skills/extract/` | .docx/.pdf → Markdown + images | Rewrite Phase 1 |
| 2 | `rewriter_agent` | `${SKILL_DIR}/skills/rewrite/` | Polish/translate via /nature-polishing | Both modes |
| 3 | `visual_agent` | `${SKILL_DIR}/skills/visual/` | Figures via /nature-figure, /gpt-image | Both modes |
| 3.5 | `md_validator_agent` | `${SKILL_DIR}/skills/validate/` | Semantic MD validation (Phase 3.5 Layer 2) | Both modes |
| 4 | `formatter_agent` | `${SKILL_DIR}/skills/format/` | Markdown → IEEE Word | Both modes |
| 5 | `validator_agent` | `${SKILL_DIR}/skills/validate/` | 15-invariant final quality gate | Both modes |

---

## Mode Registry

| Mode | Output | Triggers |
|------|--------|----------|
| `rewrite` | IEEE .docx from existing paper | "改写论文", "rewrite paper", "IEEE format" |
| `scratch` | IEEE .docx from title only | "从头写IEEE论文", "write IEEE paper from scratch" |

> See `MODE_REGISTRY.md` for full mode selection rules.

---

## Mode Selection

🚧 **GATE**: Determine mode from user input.

| User provides | Mode | First agent |
|---------------|------|-------------|
| Existing .docx/.pdf | `rewrite` | `extractor_agent` |
| Existing .md | `rewrite` | `rewriter_agent` |
| Title/topic only | `scratch` | `/ars-full` |

---

## Autonomous Execution Policy

⛔ **HARD RULE**: The orchestrator executes the **entire pipeline without user confirmation**.

### Behavior

- **Phase transitions**: Automatic. Do NOT ask user to confirm before proceeding.
- **Internal checkpoints**: Verify output quality silently. If OK → proceed. If NOT OK → auto-fix or re-delegate.
- **Validation failures**: Follow `failure_recovery.md`. Re-delegate up to 3 times per invariant. **Do NOT ask user.**
- **Max retries exceeded**: Report to user with full failure details. This is the ONLY time the orchestrator pauses.
- **Final delivery**: Report completed file path, word count, invariant results to user.

### What the orchestrator NEVER does

- Ask "Should I proceed to the next phase?"
- Ask "Do you want me to format the paper?"
- Ask "Ready to validate?"
- Present intermediate results for user approval
- Stop after a successful phase waiting for instructions

### What the orchestrator DOES

- Execute Phase 1 → verify → Phase 2 → verify → ... → Phase 5 → deliver
- Auto-answer ARS questions using `references/ars-defaults.md`
- Auto-recover from validation failures using `shared/failure_recovery.md`
- Report final result: file path + metrics

---

## Orchestration Workflow

### Mode `rewrite`: 6 Gates

```
Phase 1: EXTRACT    → [extractor_agent]   → Markdown + images
Phase 2: POLISH     → [rewriter_agent]    → Polished Markdown
Phase 3: VISUALS    → [visual_agent]      → Figures ready
Phase 3.5: MD GATE  → [validate_md.py] + [md_validator_agent] → Validation PASS
Phase 4: FORMAT     → [formatter_agent]   → IEEE Word
Phase 4.5: STRUCTURE → [check_docx_structure.py] → Template invariants PASS
Phase 5: VALIDATE   → [validator_agent]   → 15/15 PASS → Deliver
```

### Mode `scratch`: 6 Gates

```
Phase 1: GENERATE   → /ars-full pipeline    → Full Markdown
Phase 2: VISUALS    → [visual_agent]        → Figures generated
Phase 3: POLISH     → [rewriter_agent]      → Polished Markdown
Phase 3.5: MD GATE  → [validate_md.py] + [md_validator_agent] → Validation PASS
Phase 4: FORMAT     → [formatter_agent]   → IEEE Word
Phase 4.5: STRUCTURE → [check_docx_structure.py] → Template invariants PASS
Phase 5: VALIDATE   → [validator_agent]   → 15/15 PASS → Deliver
```

---

## Phase Details

### Phase 0: Setup Work Directory

🚧 **GATE**: Create work directory before any agent runs.

```
Mode: <rewrite|scratch>
Title/filename: <sanitized_name>
Work dir: <project_root>/<sanitized_name>
```

**Steps**:
1. Determine mode from user input
2. Compute folder name (see Work Directory Strategy)
3. Create `<work_dir>/figures/` directory
4. Set all subsequent paths relative to `<work_dir>`

---

### Phase 1 (rewrite): Extract Content

🚧 **GATE**: User provided source file (.docx/.pdf).

🛠️ **EXECUTION**: Delegate to `extractor_agent`.

```
Source: <source_path>
Output dir: <work_dir>
```

**Auto-verify**: Received extraction report. Check ≥ 5 sections, ≥ 3 figures. If missing → re-extract with adjusted parameters.

→ **Auto-proceed to Phase 2**.

---

### Phase 1 (scratch): Generate via ARS Full Pipeline

🚧 **GATE**: User provided title/topic.

🛠️ **EXECUTION**: Call `/ars-full` (academic-research-skills full pipeline).

⛔ **Do NOT call `academic-paper` alone.** Use `/ars-full` which runs the
complete pipeline: research planning → literature review → outline →
full paper writing → revision. This produces a substantially better
paper than `academic-paper` alone.

**Language**: All prompts and output in English. Translate Chinese input first.

**ARS Interaction Protocol**:

When `/ars-full` asks clarifying questions, auto-answer with these defaults:

| Question type | Default answer | Rationale |
|---------------|---------------|-----------|
| Paper type | **Original research with novel algorithmic contribution** | Plugin requires algorithm design + validation |
| Methodology | **Algorithm design + theoretical analysis + experimental evaluation** | Strongest for IEEE conference |
| Scope | **Focused on specific computational problem** | Conference papers need depth not breadth |
| Contribution | **Novel algorithm/method + theoretical analysis + empirical evaluation** | Matches plugin pipeline capabilities |
| Target venue | **IEEE conference** | Plugin's formatting target |
| Language | **English** | Hard rule |
| Page limit | **6-8 pages** | IEEE conference standard |
| Word count | **3500+ words** | Validator invariant floor |

⛔ **ALGORITHM-FOCUS ENFORCEMENT** (see `references/ars-defaults.md` for full policy):
- The paper title MUST contain at least one algorithmic keyword
- Introduction/Related Work must emphasize algorithmic literature, not domain applications
- Methodology section is 100% algorithm design — zero application detail
- Experiments compare with SOTA algorithms, not domain baselines
- Literature review: ≥70% algorithm/method papers; ≤30% domain papers

⛔ **REJECT** if ARS proposes:
- Pure survey / literature review paper
- Application-focused paper without algorithm novelty
- Opinion piece without data
- Paper type that cannot produce experimental results
- Title without algorithmic keywords

See `references/ars-defaults.md` for full question-answer reference.

```
Title: <user's title>
Target: IEEE conference paper, 6-8 pages, 3500+ words
Citation format: IEEE
Output: <work_dir>/paper.md
Language: English (always)
```

**Auto-verify**: Received full markdown. Check language is English, paper has experimental content,
word count ≥ 3500, title contains algorithmic keyword. If title is application-descriptive,
rewrite it to emphasize the algorithmic contribution before proceeding to Phase 2.

→ **Auto-proceed to Phase 2**.

---

### Phase 2: Polish & Translate

🚧 **GATE**: Phase 1 complete; markdown exists at `<work_dir>/paper.md`.

🛠️ **EXECUTION**: Delegate to `rewriter_agent`.

```
Source: <work_dir>/paper.md
Mode: <existing|scratch>
Target words: 3500
Language: English (always — translate if source is Chinese)
Algorithm focus: Enforce content strategy (see rewriter_agent.md §Content Strategy)
```

**Auto-verify**: Word count ≥ 3500. Language is English. All content preserved.
Title contains algorithmic keyword. Every figure/table cited in body text (C9).
No markdown symbols in references (C10).

→ **Auto-proceed to Phase 3**.

---

### Phase 3: Prepare Figures

🚧 **GATE**: Phase 2 complete.

🛠️ **EXECUTION**: Delegate to `visual_agent`.

```
Paper: <work_dir>/paper.md
Figures dir: <work_dir>/figures/
Mode: <reuse|generate>
```

**Auto-verify**: All figure references resolved. Each figure file exists.

→ **Auto-proceed to Phase 3.5**.

---

### Phase 3.5: Markdown Validation Gate (HARD GATE)

🚧 **HARD GATE**: Phase 4 (FORMAT) CANNOT execute until Phase 3.5 passes completely.

This is a dual-layer validation gate. Both layers must pass for the pipeline to proceed.

**Layer 1 — Python Automated Validation (regex/format/counts)**:

```bash
python ${SKILL_DIR}/scripts/validate_md.py <work_dir>/paper.md
```

- Exit 0: **PASS** → proceed to Layer 2
- Exit 1: **HARD FAIL** → collect error list, return to Phase 2 (rewriter_agent) for fixes
- Exit 2: **SOFT WARN** → proceed to Layer 2, log warnings

**Layer 2 — Independent Semantic Validation (subagent)**:

Delegate to `md_validator_agent` (definition: `agents/md_validator_agent.md`).

```
Input: <work_dir>/paper.md (read-only path)
```

⛔ **CONTEXT ISOLATION**: The md_validator_agent receives ONLY the file path. No conversation history, no previous validation results, no rewriter context. This prevents context contamination.

- Returns `[RESULT] overall: PASS` → proceed to Phase 4
- Returns `[RESULT] overall: FAIL` → collect fix suggestions, return to Phase 2 (rewriter_agent)

**Failure Recovery**:

| Layer | Failure | Recovery |
|-------|---------|----------|
| Layer 1 | HARD violations | Pass error list from validate_md.py to rewriter_agent |
| Layer 2 | Semantic violations | Pass fix suggestions from md_validator_agent to rewriter_agent |
| Either | After fix | Re-run from Layer 1 |

- Max **3 retries** total (combined across both layers)
- Each retry: re-delegate to rewriter_agent with specific fix instructions
- After fix: re-run Layer 1 → Layer 2 sequence

⛔ **STOP ONLY IF**: Max retries exceeded. Report all unresolved violations to user.

→ **Auto-proceed to Phase 4** (only when both layers PASS).

---

### Phase 4: Format to IEEE Word

🚧 **GATE**: Phase 3.5 dual-layer Markdown validation passed completely.

🛠️ **EXECUTION**: Delegate to `formatter_agent`.

```
Template: <template.docx>
Source: <work_dir>/paper.md
Figures: <work_dir>/figures/
Output: <work_dir>/<name>.docx
```

**Auto-verify**: Output .docx exists and file size > 0.

→ **Auto-proceed to Phase 4.5**.

---

---

### Phase 4.5: Structure Gate

🚧 **GATE**: Phase 4 complete.

🛠️ **EXECUTION**: Run structural template validation.

```bash
python ${SKILL_DIR}/scripts/check_docx_structure.py <work_dir>/<name>.docx <template.docx>
```

**Hard invariants**: Author/Affiliation unchanged, template section anchors preserved, Heading/Figure/Table/Reference auto-numbered styles contain no manual prefixes.

→ **Auto-proceed to Phase 5** only when structure PASS.

### Phase 5: Validate & Deliver

🚧 **GATE**: Phase 4.5 structure gate passed.

🛠️ **EXECUTION**: Delegate to `validator_agent`.

⛔ **AUTO-RECOVERY**: If any invariant FAILS:
1. Read failure report
2. Consult `shared/failure_recovery.md` for agent mapping
3. Re-delegate to responsible agent with fix brief
4. Re-run formatter + validator
5. Max 3 retries per invariant
6. **Do NOT ask user** — recover automatically

⛔ **STOP ONLY IF**: Max retries exceeded for any invariant. Report full failure details to user.

✅ **DELIVER**: 15/15 PASS → Report to user:
- Final file path: `<work_dir>/<name>.docx`
- Word count, page count
- Figure/equation/table/reference counts
- Validation result: 15/15 PASS

---

## Resource Manifest

### Agents (each is also a standalone skill)

| Agent | Skill Directory | Agent Definition |
|-------|----------------|-----------------|
| `extractor_agent` | `${SKILL_DIR}/skills/extract/` | `skills/extract/extractor_agent.md` |
| `rewriter_agent` | `${SKILL_DIR}/skills/rewrite/` | `skills/rewrite/rewriter_agent.md` |
| `visual_agent` | `${SKILL_DIR}/skills/visual/` | `skills/visual/visual_agent.md` |
| `md_validator_agent` | `${SKILL_DIR}/skills/validate/` | `agents/md_validator_agent.md` |
| `formatter_agent` | `${SKILL_DIR}/skills/format/` | `skills/format/formatter_agent.md` |
| `validator_agent` | `${SKILL_DIR}/skills/validate/` | `skills/validate/validator_agent.md` |

### Scripts

| Script | Purpose |
|--------|---------|
| `${SKILL_DIR}/scripts/format_ieee.py` | Markdown → IEEE Word |
| `${SKILL_DIR}/scripts/parse_markdown.py` | Structured Markdown parser and contract normalization |
| `${SKILL_DIR}/scripts/word_blocks.py` | WordprocessingML block builders for headings, captions, tables, equations |
| `${SKILL_DIR}/scripts/extract_docx.py` | .docx → Markdown |
| `${SKILL_DIR}/scripts/check_docx_structure.py` | Template structure validation (Phase 4.5) |
| `${SKILL_DIR}/scripts/validate.py` | 15-invariant validation (Phase 5) |
| `${SKILL_DIR}/scripts/validate_md.py` | Markdown pre-conversion validation (Phase 3.5 Layer 1) |

### Shared Protocols

| Resource | Path |
|----------|------|
| Failure recovery | `${SKILL_DIR}/shared/failure_recovery.md` |
| Formatting rules | `${SKILL_DIR}/references/formatting-rules.md` |
| Validation checks | `${SKILL_DIR}/references/validation-checks.md` |
| Postmortem | `${SKILL_DIR}/references/postmortem.md` |
| ARS question defaults | `${SKILL_DIR}/references/ars-defaults.md` |
| Strict MD template | `${SKILL_DIR}/references/paper_template.md` |
| MarkdownOutputContract | `${SKILL_DIR}/references/MarkdownOutputContract.md` |

### External Skills

| Skill | Via Agent | When |
|-------|-----------|------|
| `/nature-polishing` | `rewriter_agent` | Polish/translate |
| `/nature-figure` | `visual_agent` | Data plots |
| `/gpt-image` | `visual_agent` | Diagrams |
| `/ars-full` | Direct call | Scratch mode (default) |

### Dependencies

- Python: `python-docx`, `lxml`, `Pillow`, `numpy`
- CLI: `pandoc` (LaTeX → OMML)
