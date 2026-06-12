# Pipeline Root Cause Analysis & Standardization

> 本文档记录 IEEE 论文生成管道中出现的所有质量问题，从源头溯源到应该在哪一步被解决，提出标准化约束规则。

---

## 一、问题清单与溯源

### 问题 P1：表格全部堆在文档末尾（F15 复发）

| 维度 | 内容 |
|------|------|
| **现象** | 4 张表格全部出现在文档最后，不在正文引用位置 |
| **表象原因** | `strip_blank_lines_around_blocks()` 删除了 TABLE caption 和表数据行之间的空行 |
| **根因** | 该函数只识别了 equation、figure、table data rows 为 block，没有识别 TABLE caption 行。空行被删除后，caption 和表数据合并为一行，`extract_md_tables()` 的 caption 匹配全部失败 → 所有表格变成"未匹配" → 全部堆到最后 |
| **应在哪步解决** | **Phase 4 (FORMAT)** — format_ieee.py 的 `strip_blank_lines_around_blocks()` 本身就应该理解 MarkdownOutputContract C5 的格式（`**TABLE N. Title**` + 空行 + 表格数据），在做 block 检测时同时检测 caption 行 |
| **缺失的约束** | format_ieee.py 没有将 MarkdownOutputContract 作为解析前置条件。block 检测函数不了解"TABLE caption → 空行 → table data"的三段式结构 |
| **当前状态** | ✅ 已修复 — 添加了 `is_table_caption` 保护逻辑 |

### 问题 P2：TABLE 标题缺少自动编号（TABLE I., TABLE II. 等）

| 维度 | 内容 |
|------|------|
| **现象** | tablehead 段落没有显示 "TABLE I.", "TABLE II." 前缀 |
| **表象原因** | `make_data_table()` 中使用了 `num_id='0'`，显式覆盖了样式自带的 numId=9 编号 |
| **根因** | 之前修复"文本重复"问题时，没有理解模板 tablehead 样式的 numPr 定义（numId=9 → abstractNumId=20 → `lvlText="TABLE %1."` + `numFmt=upperRoman`），而是用 `num_id='0'` 粗暴压制了整个编号机制 |
| **应在哪步解决** | **Phase 4 (FORMAT)** — 应该先理解模板样式定义再决定策略。numId=9 的 `lvlText="TABLE %1."` 负责生成 "TABLE I." 前缀，caption 文本只需包含纯标题（代码第 561 行已经 strip 了 "TABLE N." 前缀）。两者不冲突 |
| **缺失的约束** | format_ieee.py 缺少"模板样式 numPr 继承规则"文档。formatting-rules.md 第 7 节提到了 `tablehead` 样式有 numId=9，但没有明确说明 caption 文本不应包含 "TABLE N." 前缀 |
| **当前状态** | ✅ 已修复 — 移除 `num_id='0'`，恢复样式继承 |

### 问题 P3：图片在正文中没有引用（C9 违规）

| 维度 | 内容 |
|------|------|
| **现象** | Fig. 1-6 定义了但正文没有 `Fig. N.` 引用 |
| **表象原因** | paper.md 正文中缺少 "as shown in Fig. 1" 等引用语句 |
| **根因** | ARS 生成的 paper.md 不了解 MarkdownOutputContract C9 规则。rewriter_agent (Phase 3) 的 `contract_check()` 包含 C9 检查，但本次管道中 rewriter 可能未严格执行或未运行自检 |
| **应在哪步解决** | **Phase 3 (POLISH)** — 这是 rewriter_agent 的核心职责。contract_check() 中的 C9 检查已经存在，必须作为硬性前置条件（不是 warning） |
| **缺失的约束** | C9 在 MarkdownOutputContract 中标记为 "CONTRACT VIOLATION"，但在 validation-checks.md 的 "MarkdownOutputContract Consistency Checks" 表中只有 warning 级别（"These are WARNINGS, not hard failures"）。这个不一致导致执行时可以跳过 |
| **当前状态** | ⚠️ 需要标准化 — 将 C9 提升为硬性约束 |

### 问题 P4：表格标题作为占位符（格式不符）

| 维度 | 内容 |
|------|------|
| **现象** | 正文中只有 TABLE 占位符，没有正确格式的 `**TABLE N. Title**` |
| **表象原因** | ARS 输出的 paper.md 可能使用了 HTML 注释 `<!-- TABLE ... -->` 或其他格式 |
| **根因** | ARS 不知道 MarkdownOutputContract C5 格式要求。convert_for_ieee.py 作为中间层做了转换，但增加了管道复杂度和出错机会 |
| **应在哪步解决** | **Phase 3 (POLISH)** — rewriter 是 Contract 合规的唯一责任方。无论输入格式如何，输出必须是 `**TABLE N. Title**` 格式 |
| **缺失的约束** | 没有明确规定：rewriter 必须将所有表格标记转换为 Contract 格式，不能依赖中间脚本 |
| **当前状态** | ⚠️ 需要标准化 — 消除 convert_for_ieee.py 中间层 |

---

## 二、系统性缺陷分析

### 缺陷 1：Formatter 过度防御（Contract 违规容忍）

**现状**：
- formatting-rules.md §20 说 "formatter does NOT handle format deviations"
- 但 format_ieee.py 实际上做了大量防御性处理（strip markdown bold, strip TABLE prefix, strip Figure prefix 等）
- `strip_blank_lines_around_blocks()` 不理解 Contract C5 格式，盲目删除空行

**问题**：Formatter 一边声称"不处理偏差"，一边又在做防御性处理。这种不一致导致 bug 在 formatter 内部潜伏。

**标准化方向**：
- Formatter 只接受 Contract 合规的 Markdown
- 合规检查在入口处（preflight_check），不合规直接报错
- 不在解析过程中做"猜测性"修复

### 缺陷 2：Contract 检查是 Warning 而非 Gate

**现状**：
- MarkdownOutputContract.md 定义了 C1-C10 规则
- validation-checks.md 说 "These are WARNINGS, not hard failures"
- rewriter_agent.md 的 contract_check() 列出了所有 C1-C10 检查

**问题**：Warning 意味着可以被跳过。C9 (cross-reference) 这种"没有引用 = 结构性错误"的问题不应该只是 warning。

**标准化方向**：
- C1-C10 区分为 "hard" (必须通过) 和 "soft" (warning)
- Hard: C4 (figure numbering), C5 (table format), C6 (equations), C9 (cross-reference), C10 (reference purity)
- Soft: C5 word count (can overflow), C7 reference count (can exceed with user approval)

### 缺陷 3：缺少 Pipeline 质量门（各阶段间无交接验证）

**现状**：
- Phase 1 (ARS) → Phase 3 (Rewriter) 之间没有格式验证
- Phase 3 (Rewriter) → Phase 4 (Formatter) 之间没有 Contract 合规检查
- Phase 4 (Formatter) → Phase 5 (Validator) 之间只有 14 不变量检查

**问题**：每个阶段假设上游输出是正确的，但实际上不是。Bug 从上游传播到下游，最后在 Phase 5 才被发现（或完全不被发现）。

**标准化方向**：
- 每个阶段的输出必须通过交接验证才能进入下一阶段
- 交接验证是硬性门控，不是建议

### 缺陷 4：模板样式知识没有被系统化

**现状**：
- formatting-rules.md 提到了样式的 numId，但不完整
- 本次 tablehead 的 numId=9 → abstractNumId=20 → `lvlText="TABLE %1."` 是手动调查才发现的
- 没有文档记录"哪些样式有自动编号，文本应该如何配合"

**标准化方向**：
- 创建 "Template Style Registry"，记录每个样式的自动编号行为
- 明确每个样式的"文本职责"（应包含什么、不应包含什么）

---

## 三、标准化方案：Pipeline Quality Gate System

### 5 阶段管道 + 4 个质量门

```
Phase 1: GENERATE  ──→ [G0: Language Gate] ──→ Phase 2: VISUALS
Phase 2: VISUALS   ──→ [G1: Asset Gate]   ──→ Phase 3: POLISH
Phase 3: POLISH    ──→ [G2: Contract Gate] ──→ Phase 4: FORMAT
Phase 4: FORMAT    ──→ [G3: Structure Gate]──→ Phase 5: VALIDATE
Phase 5: VALIDATE  ──→ [G4: Final Gate]    ──→ DELIVER
```

### Gate 0: Language Gate (Phase 1 → Phase 2)

**检查项**：
| ID | 检查 | 通过条件 | 失败处理 |
|----|------|---------|---------|
| G0.1 | 语言 | 全文英文，无中文字符 | 拒绝，要求重写 |
| G0.2 | 章节结构 | ≥5 个 `##` 标题 | 拒绝，要求补全 |
| G0.3 | 字数 | ≥3000 words | 拒绝，要求扩展 |

### Gate 1: Asset Gate (Phase 2 → Phase 3)

**检查项**：
| ID | 检查 | 通过条件 | 失败处理 |
|----|------|---------|---------|
| G1.1 | 图片数量 | 6-10 张 PNG/JPG | 拒绝，要求补全 |
| G1.2 | 图片质量 | 每张 aspect ≥ 1.0 或 white ≤ 0.5 | 拒绝问题图片 |
| G1.3 | 图片命名 | fig{N}_{name}.png，N 与 paper.md 中引用一致 | 拒绝，要求重命名 |

### Gate 2: Contract Gate (Phase 3 → Phase 4) ⭐ 最重要

**检查项**（全部通过才放行）：
| ID | 检查 | 通过条件 | 级别 |
|----|------|---------|------|
| G2.H1 | Contract C1 | `**Abstract** —` 存在 | HARD |
| G2.H2 | Contract C2 | `**Keywords** —` 存在 | HARD |
| G2.H3 | Contract C3 | 所有 `## ` 以 Roman numeral 开头 | HARD |
| G2.H4 | Contract C4 | `![Fig. N. Caption]` 编号连续无间隔，caption ≤12 words | HARD |
| G2.H5 | Contract C5 | `**TABLE N. Title**` 格式正确 | HARD |
| G2.H6 | Contract C6 | `$$...\tag{eq:N}$$` 数量 ≥5 | HARD |
| G2.H7 | Contract C7 | 参考文献 ≤15 | HARD |
| G2.H8 | Contract C9 | **每个 Fig./TABLE 在正文中被引用** | HARD |
| G2.H9 | Contract C10 | 参考文献无 markdown 符号 | HARD |
| G2.S1 | Table caption words | Table caption ≤8 words | SOFT |
| G2.S2 | Reference count | 参考文献数量 | SOFT |

**关键规则**：
- G2.H8 (C9) 是 **HARD GATE**，不是 warning。rewriter 必须保证每个 figure/table 在正文中有引用
- 失败后回到 Phase 3 修复，不进入 Phase 4
- 修复最多重试 3 次

### Gate 3: Structure Gate (Phase 4 → Phase 5)

**检查项**：
| ID | 检查 | 通过条件 | 失败处理 |
|----|------|---------|---------|
| G3.1 | 表格位置 | 每个 table 的 XML 位置在引用段落之后 | 拒绝 |
| G3.2 | 表格编号 | tablehead 段落 style=tablehead，继承 numId=9 | 拒绝 |
| G3.3 | 标题编号 | H1/H2 段落无手动 Roman/Letter 前缀 | 拒绝 |
| G3.4 | 参考文献编号 | references 段落无手动 `[N]` 前缀 | 拒绝 |
| G3.5 | 内联公式 | 正文中 `$...$` 已转为 OMML | 拒绝 |

### Gate 4: Final Gate (Phase 5 → DELIVER)

**= 现有 14 不变量检查 + Gate 3 结构检查**

---

## 四、具体改动清单

### A. MarkdownOutputContract.md — 新增 Enforcement Level

在 C1-C10 每条规则后新增 `Level: HARD | SOFT` 标记：
- HARD: C4, C5 (format), C6, C9, C10
- SOFT: C1, C2, C3, C5 (word count), C7, C8

### B. rewriter_agent.md — 强化 Contract 检查

1. **contract_check() 返回值改为** `{hard: [...], soft: [...]}`
2. **新增 Step 0: Input Format Detection**：自动将 ARS 输出转为 Contract 格式
3. **Step 2 强制执行**：hard errors 阻止输出

### C. format_ieee.py — 减少防御性代码

1. **新增 `preflight_contract_check()` 函数**：在处理前验证 Markdown 是否符合 C1-C10
2. **不合规时输出 WARNING（当前阶段）**，未来升级为 exit(1)
3. **`strip_blank_lines_around_blocks()` 理解 Contract 结构**：识别 TABLE caption 三段式

### D. formatting-rules.md — 新增 Template Style Registry

```markdown
## Template Style Registry

| Style ID | Style Name | Auto-num (numId) | lvlText | 文本职责 |
|----------|-----------|------------------|---------|---------|
| 1 | Heading 1 | 4 | %1. | 纯标题，无 Roman 前缀 |
| 2 | Heading 2 | 4 | %2. | 纯标题，无 Letter 前缀 |
| figurecaption | Figure Caption | 2 | Fig. %1. | 纯标题，无 "Fig. N." |
| tablehead | Table Head | 9 | TABLE %1. | 纯标题，无 "TABLE N." |
| references | References | 8 | [%1] | 纯正文，无 [N] |
```

### E. validation-checks.md — 新增 Gate 检查项

新增 G2 (Contract Gate) 和 G3 (Structure Gate) 检查项到验证脚本。

### F. 消除 convert_for_ieee.py 中间层

rewriter 直接输出 Contract 格式，format_ieee.py 直接读取 paper.md。

---

## 五、实施优先级

| 优先级 | 改动 | 影响范围 | 理由 |
|--------|------|---------|------|
| **P0** | Template Style Registry | formatting-rules.md | 直接导致 P2（表格缺少自动编号） |
| **P0** | C9 提升为 HARD gate | rewriter + contract | 直接导致 P3（图片没有引用） |
| **P0** | strip_blank_lines_around_blocks 理解 Contract | format_ieee.py | 直接导致 P1（表格堆在末尾） |
| **P1** | preflight_contract_check() | format_ieee.py | 防止 Contract 违规进入 formatter |
| **P1** | 消除 convert_for_ieee.py | 管道简化 | 减少一个出错环节 |
| **P2** | Gate System 完整实现 | validate.py + SKILL.md | 全面提升管道质量 |
| **P2** | rewriter 输入格式自动检测 | rewriter_agent.md | 兼容 ARS 和手动输入 |
