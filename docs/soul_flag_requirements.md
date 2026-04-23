# 万魂幡（Soul-Flag）需求落地方案（基于 Nuwa Skill 升级）

## 0) 升级目标（不是另起炉灶）

这版方案明确为：**在既有 `nuwa-skill` 工作流上增量升级**，而不是平行新系统。

- 保留：Nuwa 现有的研究蒸馏、`SKILL.md` 结构化产物、验证意识。
- 新增：任务失败触发的“自动补完通道”（Auto-Refine Lane）。
- 原则：**兼容优先、最小侵入、可回滚**。

---

## 1) 现有 Nuwa Skill 可复用资产

基于 `alchaincyf/nuwa-skill` 的公开文档，可复用能力包括：

1. **研究入口与诊断逻辑**：能把模糊需求转为明确研究对象。
2. **多源并行采集能力**：著作/访谈/社媒/批评/决策时间线。
3. **三重验证思想**：跨域复现、生成力、排他性。
4. **结构化 Skill 产出**：`SKILL.md` 模板化表达。
5. **质量测试意识**：已知题一致性 + 未知题不确定性。

> 升级结论：不推翻 Nuwa 的“认知蒸馏链”，而是给它增加“执行能力补完链”。

---

## 2) 升级后的双通道架构

```text
                 ┌──────────────────────────┐
User Task ─────► │ Nuwa Existing Skill Lane │ ─────► Success
                 └─────────────┬────────────┘
                               │ miss/fail
                               ▼
                 ┌──────────────────────────┐
                 │ Soul-Flag Auto-Refine    │
                 │ (new incremental lane)   │
                 └─────────────┬────────────┘
                               ▼
                    Skill Registry (Nuwa-compatible)
                               ▼
                        Re-run original task
```

### 通道定义

- **主通道（保留）**：优先走现有 Nuwa Skill 匹配与执行。
- **补完通道（新增）**：仅在主通道无法满足时触发（分值低或执行失败）。

---

## 3) 与 Nuwa 的接口兼容要求（核心）

### 3.1 Skill 产物兼容

新增技能必须同时产出：

- `SKILL.md`（延续 Nuwa 可读可审计规范）
- `runtime.py`（可执行 `execute()`）
- `meta.json`（版本、来源、风险、回滚信息）

### 3.2 元数据统一

```json
{
  "skill_id": "skill_refined_distributed_lock_cluster_v1",
  "origin": "soul-flag",
  "compatible_with": "nuwa-skill-v1",
  "evidence_count": 6,
  "safety_level": "sandboxed",
  "status": "canary"
}
```

### 3.3 调用契约

- 输入：沿用 Nuwa task context，新增 `gap_report` 字段。
- 输出：沿用 Nuwa result envelope，新增 `skill_patch_trace`（补完追踪）。

---

## 4) 新增模块（以插件方式挂载 Nuwa）

### A. Trigger（触动禁制）

- 触发条件：
  - Top-1 匹配分 `< 0.4`。
  - 或执行异常属于 `DependencyMissing` / `LogicGap` / `CapabilityNotFound`。
- 输出：
  - `gap_domain`
  - `gap_type`
  - `acceptance_tests`
  - `failure_trace`

### B. Expert Sourcing（全网搜魂）

- 检索源：GitHub / ArXiv / StackOverflow / 白名单技术博客。
- 专家簇评分：
  - 可信度（身份、机构、引用、star/fork、采纳率）
  - 新鲜度（最近更新时间、近 12 个月活跃）
  - 相关度（与 `gap_domain` 相似度）
- 输出：Top-K `evidence candidates`（不绑定单一“名人”）。

### C. Refining & Synthesis（神识炼化）

- 清洗：统一为 Markdown + Source Metadata。
- 证据包：`claim/evidence/confidence/risk_tag/license`。
- 生成：
  - 用模板约束生成 Nuwa 兼容 Skill 三件套（`SKILL.md` + `runtime.py` + `meta.json`）。
  - 必须附引用映射，确保“代码片段 ⇄ 证据来源”可追踪。

### D. Deployment（入幡执行）

- 沙箱门禁：
  1. `ruff/mypy/bandit`
  2. 资源限制（CPU/内存/超时）
  3. Contract tests（对齐 `acceptance_tests`）
- 注册策略：
  - 先 canary（仅当前租户/会话）
  - 达阈值后 promoted（全局）
  - 全程支持版本回滚

---

## 5) 升级映射表（旧能力 → 新能力）

| Nuwa 现有能力 | 升级动作 | 升级后收益 |
| :-- | :-- | :-- |
| 人物/主题蒸馏 | 增加失败触发补完入口 | 从“会分析”变“可自救” |
| `SKILL.md` 结构化输出 | 扩展为 `SKILL.md + runtime.py + meta.json` | 可读 + 可执行 + 可治理 |
| 研究验证 | 增加静态扫描+沙箱+合同测试 | 生产安全可控 |
| 一次性生成 | 增加 canary 与版本回滚 | 线上稳定性提升 |
| 经验积累 | 接入向量库与热点预热 | 高频问题响应更快 |

---

## 6) 实施顺序（严格按“先兼容后增强”）

### Phase 1：兼容接入（1~2 周）

- 新增 Auto-Refine Lane，但默认关闭（feature flag）。
- 仅支持 GitHub 单源 + `SKILL.md/runtime.py` 基础生成。
- 只在会话级 canary，不入全局库。

### Phase 2：安全闭环（2~4 周）

- 引入 `meta.json`、证据链映射、`bandit` + 合同测试。
- 增加失败分类与回滚策略。

### Phase 3：规模化优化（4~6 周）

- 多源检索（ArXiv/SO/Blogs）与信誉分重排。
- 向量库记忆、热点预热、领域知识图谱（万魂阵）。

---

## 7) Refiner 伪代码（Nuwa 升级版）

```python
class NuwaSoulFlagUpgrade:
    def __init__(self, nuwa_registry, search, crawler, llm, verifier):
        self.registry = nuwa_registry
        self.search = search
        self.crawler = crawler
        self.llm = llm
        self.verifier = verifier

    def run(self, task_ctx):
        # 1) 优先走现有 Nuwa 通道
        result = self.registry.execute_existing(task_ctx)
        if result.ok:
            return result

        # 2) 触发新增补完通道
        gap = self._build_gap_report(task_ctx, result.error)
        candidates = self._retrieve_expert_cluster(gap)
        evidence = self._build_evidence_pack(candidates)

        skill_bundle = self._synthesize_nuwa_compatible_bundle(gap, evidence)
        verify = self.verifier.gate(skill_bundle, gap.acceptance_tests)
        if not verify.passed:
            return result  # 回退原结果，不污染主链路

        skill_id = self.registry.register_canary(skill_bundle)
        return self.registry.retry_with(skill_id, task_ctx)
```

---

## 8) 验收标准（升级是否成功）

- **兼容性**：旧 Skill 执行成功率不下降（回归基线 >= 99%）。
- **补完成功率**：触发补完后一次成功率持续提升。
- **安全性**：高风险候选拦截率、违规代码零上线。
- **可追溯性**：生成技能证据映射覆盖率 >= 95%。
- **可运维性**：回滚平均耗时（MTTR）可量化。

---

## 9) 一句话结论

这不是“重做 Nuwa”，而是“给 Nuwa 长出第二条命”：
**保留原有蒸馏能力，新增失败自愈能力，让 Skill 系统从静态知识库升级为可进化执行体。**
