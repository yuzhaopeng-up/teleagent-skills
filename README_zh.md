# TeleAgent Skills

[![License: Apache 2.0](https://img.shields.io/badge/License-Apache%202.0-blue.svg)](LICENSE)
[![Skills](https://img.shields.io/badge/Skills-6-green.svg)]()
[![Compatible](https://img.shields.io/badge/Compatible-TeleAgent%20%7C%20Claude%20Code%20%7C%20Cursor%20%7C%20OpenClaw-orange)]()

> **面向AI驱动业务流程的生产级Agent技能组件** — 开箱即用，支持4阶段编排、可配置规则、多源证据分析、自然语言转SQL和交互式可视化。

## 为什么选择 TeleAgent Skills？

大多数AI Agent技能将业务规则硬编码在提示词中。我们的不是。每个技能遵循三大原则：

1. **规则参数化** — 业务变了？更新YAML配置，不用改技能代码
2. **组件可组合** — 4阶段编排，阶段间标准化JSON契约
3. **每个技能都有降级机制** — 子组件失败时优雅降级，而不是崩溃

## 快速开始

```bash
# 克隆仓库
git clone https://github.com/yuzhaopeng-up/teleagent-skills.git

# 复制技能到你的Agent技能目录
cp -r teleagent-skills/skills/scoring-engine ~/.config/TeleAgent/skills/
```

## 技能一览

| 技能 | 描述 | 适用场景 |
|------|------|---------|
| [评分引擎](skills/scoring-engine/) | 多维度加权评分，规则可配置 | 客户评分、风险评估、供应商评价 |
| [证据链](skills/evidence-chain/) | 多源交叉验证与根因分析 | 故障诊断、投诉核查、审计验证 |
| [数据聚合器](skills/data-aggregator/) | 统计聚合与同比环比分析 | 业务报表、趋势分析、KPI看板 |
| [可视化渲染器](skills/visualization-renderer/) | 自动图表推荐 + 交互式ECharts HTML | 数据看板、报表可视化、演示汇报 |
| [自然语言查询](skills/nl2-query/) | 自然语言转结构化查询，含置信度评分 | 自助数据查询、商业智能 |

## 架构

每个技能遵循4阶段组件编排模式：

```
┌─ 阶段1：抽取 (Info-Extractor) ─────────┐
│  解析输入 → 结构化JSON                     │
└──────────────────┬──────────────────────┘
                   ▼
┌─ 阶段2：分析 (Data-Analyst) ────────────┐
│  计算评分 / 校验 / 聚合                     │
└──────────────────┬──────────────────────┘
                   ▼
┌─ 阶段3：生成 (Report-Generator) ────────┐
│  5模块模板格式化输出                         │
└──────────────────┬──────────────────────┘
                   ▼
┌─ 阶段4：归档 (Archive-Manager) ─────────┐
│  脱敏 + 持久化 + 审计追踪                    │
└─────────────────────────────────────────┘
```

**核心设计决策：**
- 阶段间JSON契约 — 不传递自由文本
- 每个阶段可由独立子Agent执行
- 优雅降级：任何组件失败时，技能以降级模式运行并明确标注

## 快速示例

### 评分引擎 — 评估商机
```json
{
  "target_object": {
    "name": "某大型企业",
    "tier": "Tier-1",
    "revenue": "5000万",
    "existing_products": ["产品A", "产品B"],
    "cooperation_years": 2,
    "recent_complaints": 1,
    "competitor_contact": true
  },
  "scoring_config_name": "客户商机评分 v2"
}
```

### 证据链 — 三源交叉验证
```json
{
  "evidence_sources": [
    {"source_name": "客户报告", "source_type": "complaint_report", "content": "..."},
    {"source_name": "系统告警", "source_type": "system_alert", "content": "..."},
    {"source_name": "SLA协议", "source_type": "contract_term", "content": "..."}
  ],
  "analysis_question": "是否存在真实的服务质量问题？"
}
```

### 自然语言查询 — 自然语言转SQL
```
输入: "上个月哪个套餐的工单最多？"
输出: SELECT plan, COUNT(*) AS ticket_count FROM support_ticket 
      WHERE month='2026-05' GROUP BY plan ORDER BY ticket_count DESC LIMIT 10
```

## 行业应用场景

| 行业 | 评分引擎 | 证据链 | 数据聚合器 | 可视化渲染器 | 自然语言查询 |
|------|---------|--------|-----------|------------|------------|
| 金融服务 | 信用评分、风险评级 | 欺诈调查、理赔验证 | 投资组合分析 | 风险看板 | "显示高风险账户" |
| 制造业 | 供应商评估 | 设备故障诊断 | 产线统计 | 质量看板 | "哪条产线缺陷最多？" |
| 零售 | 门店评分 | 客诉分析 | 销售分析 | 业绩看板 | "收入前十的门店" |
| 医疗 | 患者风险评估 | 不良事件调查 | 临床统计 | 结局看板 | "各科室再入院率" |

## 参与贡献

详见 [CONTRIBUTING.md](CONTRIBUTING.md)。欢迎：
- 遵循4阶段模式的新技能
- 行业专属规则配置
- Bug修复和改进
- 文档翻译

## 安全

- 所有示例数据已完全匿名化
- 任何文件中不含真实客户信息
- 安全策略详见 [SECURITY.md](SECURITY.md)

## 许可证

Apache License 2.0 — 可免费用于商业和个人用途。

---

如果这些技能对你有用，请给个Star！这有助于更多人发现它。
