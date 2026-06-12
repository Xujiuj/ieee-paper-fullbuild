# ARS Question Defaults — Algorithm-Focused Strategy

When `/ars-full` asks clarifying questions during the scratch pipeline,
the orchestrator auto-answers with these defaults. All answers are in
English.

⛔ **HARD POLICY**: Every answer biases toward **algorithmic contribution**.
Application domain (management, engineering, industry) is secondary context
ONLY — the paper's core contribution must be a novel algorithm, model,
optimization method, or computational framework.

---

## Content Focus Directive

This directive shapes ALL phases: ARS generation, rewriter polishing,
and final formatting.

### What to EMPHASIZE (algorithm side)

- Novel algorithm design, computational model, optimization formulation
- Mathematical derivation, complexity analysis, convergence proof
- Algorithm performance metrics: accuracy, convergence rate, computational cost,
  scalability, time complexity, space complexity
- Comparison with baseline algorithms (not domain baselines)
- Ablation studies on algorithmic components
- Theoretical contribution: theorem, lemma, proposition

### What to MINIMIZE (application side)

- Domain-specific business processes, organizational structures
- Management theories, industrial standards, regulatory frameworks
- Industry case studies (mention briefly as validation, not as contribution)
- "Bridging theory and practice" language
- Societal impact, policy implications

### Title Rules

The paper title MUST contain at least one algorithmic keyword:
`algorithm`, `model`, `optimization`, `framework`, `method`, `approach`,
`network`, `learning`, `detection`, `prediction`, `classification`,
`clustering`, `inference`, `reasoning`, `generation`, `estimation`,
`transformer`, `attention`, `graph-based`, `neural`, `deep`

⛔ **REJECT** titles that are purely application-descriptive without
algorithmic keywords. Examples of BAD titles:
- "Innovation in Full-Process Bidding Management"
- "Digital Transformation of University Projects"
- "Enterprise Resource Planning Optimization"

Examples of GOOD titles:
- "A Hierarchical Attention-Based Algorithm for Multi-Stage Decision Optimization"
- "Graph Neural Network with Adaptive Aggregation for Anomaly Detection"
- "Lightweight Transformer Architecture for Real-Time Edge Inference"

---

## Paper Type

| ARS question | Default answer |
|-------------|---------------|
| What type of paper? | Original research with novel algorithmic contribution |
| Survey or original research? | Original research proposing a new algorithm/method |
| Is this a review paper? | No — original research with algorithm design and experimental validation |

⛔ **REJECT** if ARS insists on pure survey/literature review.

---

## Methodology

| ARS question | Default answer |
|-------------|---------------|
| What methodology? | Algorithm design + theoretical analysis + experimental evaluation |
| Primary approach? | Propose novel algorithm/model, prove theoretical properties, validate empirically |
| Data collection? | Benchmark datasets + synthetic datasets for stress testing |
| Validation method? | Comparison with state-of-the-art algorithms on standard benchmarks |

---

## Scope & Depth

| ARS question | Default answer |
|-------------|---------------|
| Broad or focused? | Focused on a specific computational problem |
| Theoretical or applied? | **Theoretically grounded algorithm** with experimental validation |
| Single case or multiple? | Multiple benchmark experiments (3+ datasets) |

---

## Contribution

| ARS question | Default answer |
|-------------|---------------|
| Main contribution? | **Novel algorithm/method** + theoretical analysis + empirical evaluation |
| What's new? | A new computational approach that improves on existing methods in accuracy, efficiency, or scalability |
| Validation method? | Benchmark comparison with SOTA algorithms; ablation study on key components |

---

## Literature Review Focus

When ARS generates Related Work or literature review:

### INCLUDE (algorithm literature)
- Foundational algorithms in the problem domain
- Recent SOTA methods and their algorithmic innovations
- Mathematical frameworks relevant to the proposed method
- Computational complexity comparisons

### EXCLUDE or MINIMIZE
- Application-domain literature (management theories, industrial standards)
- Historical evolution of the application field
- Non-computational approaches to the same application problem
- Organizational or policy frameworks

---

## Section Weight Guidance

| Section | Algorithm focus | Application mention |
|---------|----------------|-------------------|
| Title | MANDATORY algorithm keyword | Optional, 1-2 words max |
| Abstract | 70% algorithm/method | 30% experimental setup + brief application |
| Introduction | 60% algorithmic motivation + literature | 20% application context, 20% contribution outline |
| Related Work | 80% algorithmic methods comparison | 20% domain context |
| Methodology | 100% algorithm design + math derivation | Zero application detail |
| Experiments | Algorithm metrics, ablation, SOTA comparison | Brief mention of application dataset as one benchmark |
| Discussion | Algorithmic insights, limitations of method | Brief practical implications only |
| Conclusion | Algorithmic contribution summary | 1 sentence on application potential |

---

## Venue & Format

| ARS question | Default answer |
|-------------|---------------|
| Target venue? | IEEE conference |
| Language? | English (hard rule — always) |
| Page limit? | 6-8 pages |
| Word count? | 3500+ words |
| Citation format? | IEEE numbered [1], [2], ... |

---

## Rejection Triggers

The orchestrator must REJECT or redirect if ARS proposes:

1. **Pure survey / literature review** — "This plugin requires original
   research with algorithmic contributions."

2. **Application-focused paper without algorithm novelty** — "The paper
   must contribute a novel algorithm or computational method. Application
   is validation context only."

3. **Opinion piece** — "Papers must include algorithm design, theoretical
   analysis, and experimental evaluation."

4. **Non-English output** — "All output must be in English."

5. **Title without algorithmic keywords** — "The title must contain at
   least one algorithmic keyword (algorithm, model, method, framework,
   optimization, etc.)."

---

## Response Template

When ARS asks a question, respond in this format:

```
<question from ARS>

Answer: <default answer from this reference>
Rationale: <brief reason tied to IEEE conference requirements and algorithmic focus>
```
