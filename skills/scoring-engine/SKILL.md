---
name: scoring-engine
description: >
  Configurable rule-based scoring engine for multi-dimensional weighted evaluation.
  Rules are parameterized in YAML configs — change rules without changing the Skill.
  4-Phase orchestrated pipeline: Phase1(Info-Extractor) → Phase2(Knowledge-RAG) → Phase3(Data-Analyst) → Phase4(Report-Generator).
  Use cases: customer opportunity scoring, churn risk assessment, supplier evaluation, partner tiering, and any multi-dimensional weighted scoring needs.
  Triggers: scoring, rate, opportunity scoring, customer scoring, churn risk, rule engine, multi-dimensional scoring, weighted scoring, rule hit detection.
  Activated when a user provides a business object (e.g., customer profile) and requests scoring against configurable rules.
name_cn: Scoring-Engine 规则引擎评分组件
description_cn: 基于可配置规则和权重对业务对象做多维度评分，规则参数化存在YAML中，业务变了改配置不用改Skill
version: "1.0.0"
author: "yuzhaopeng"
license: "Apache-2.0"
---

# Scoring-Engine

## Core Philosophy

Not a single rule, but a configurable rule engine — ordinary Skills hard-code rules in prompts; advanced Skills parameterize rules so that when business changes, you update the YAML config, not the Skill.

## Orchestration Architecture

This Skill uses a **4-Phase mandatory component orchestration**, driven by the `phase-orchestrator` skill to execute 4 independent sub-Agents. Each Phase runs in its own Agent; data is passed between Phases as structured JSON. No Phase may be skipped; no free-text substitution for component output is allowed.

```
┌─ Orchestrator Agent ──────────────────────────────┐
│  task → Sub-Agent1: Info-Extractor (Object Parse)  │
│  task → Sub-Agent2: Knowledge-RAG (Rule Loading)   │
│  task → Sub-Agent3: Data-Analyst (Score Calc)      │
│  task → Sub-Agent4: Report-Generator (Report Gen)  │
└───────────────────────────────────────────────────┘
```

**Execution**: Load the `skill` tool with `name: "phase-orchestrator"` and follow its generic dispatch flow. This Skill provides complete Phase prompt templates (see [references/pipeline-phases.md](references/pipeline-phases.md)). The current Agent reads templates, replaces placeholders, and constructs `pipeline_config` for the orchestrator. The orchestrator contains no scoring-engine business logic — it only handles dispatch, data passing, and fallback.

**Degraded Mode**: If the task tool is unavailable or phase-orchestrator fails to load, fall back to single-Agent mode: the current Agent manually executes all 4 Phases per the processing rules in [references/pipeline-phases.md](references/pipeline-phases.md), annotating `[Degraded: multi-Agent orchestration unavailable]`.

Detailed orchestration protocol (I/O JSON contracts, degradation strategy, data passing format) is in [references/orchestration.md](references/orchestration.md).
Sub-Agent prompt templates are in phase-orchestrator's [references/task-prompts.md](../phase-orchestrator/references/task-prompts.md).

## Input Parameters

### Required

| Parameter | Type | Description |
|-----------|------|-------------|
| `target_object` | JSON object | Business object to score, e.g. `{name:"Acme Manufacturing Corp", level:"Tier-1", revenue:"50M", existing_products:["Product A"], cooperation_years:2, recent_complaints:1, competitor_contact:true}` |
| `scoring_config_name` | string | Scoring rule set name, e.g. `"Customer Opportunity Scoring v2"`, `"Customer Churn Risk v1"` |

### Optional

| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `custom_weights` | JSON object | `null` | Custom weight overrides, e.g. `{"Business Scale":0.25,"Service Risk":0.15}`. Unspecified dimensions keep default weights. |
| `rule_adjustment` | boolean | `true` | Enable rule adjustment (auto-adjust total when special rules are hit) |
| `output_format` | enum | `markdown` | Report output format: `markdown` / `json` / `table` |

## Phase 1 - Object Parsing (Info-Extractor)

**Mandatory load**: Call `skill` tool with `name: "info-extractor"`

**Input Contract**:
- Raw text: serialized JSON of `target_object`
- Extraction template: 6 scoring dimension field mappings

```
Field mapping:
- Business Scale:       revenue / annual_revenue → annual revenue
- Technology Adoption:  existing_products / it_products → existing product list
- Solution Fit:         match_products / potential_products → matched product list
- Partnership History:  cooperation_years / contract_history → partnership duration
- Service Risk:         recent_complaints / complaint_count → complaints in last 3 months
- Competitive Landscape: competitor_contact / competitor_status → competitor contact status
```

**Output Contract** (must be structured JSON):
```json
{
  "phase": "extraction",
  "dimensions": {
    "Business Scale": {"raw_value": "50M", "field": "revenue"},
    "Technology Adoption": {"raw_value": ["Product A","Product B"], "field": "existing_products"},
    "Solution Fit": {"raw_value": ["Solution X","Solution Y"], "field": "match_products"},
    "Partnership History": {"raw_value": 2, "field": "cooperation_years"},
    "Service Risk": {"raw_value": 1, "field": "recent_complaints"},
    "Competitive Landscape": {"raw_value": true, "field": "competitor_contact"}
  },
  "missing_dimensions": []
}
```

Missing dimensions are annotated `"raw_value": null` and listed in `missing_dimensions`.

**Degradation**: If info-extractor fails to load, this Skill manually extracts per field mapping rules, same output format, annotated `[Degraded: Info-Extractor not loaded]`.

## Phase 2 - Rule Loading (Knowledge-RAG)

**Mandatory load**: Call `skill` tool with `name: "knowledge-rag"`

**Input Contract**:
- Knowledge document: [references/scoring-rules.md](references/scoring-rules.md) as RAG source
- Query: `"Load scoring rule set: {scoring_config_name}, return dimension list, weights, scoring criteria, special rules"`

**Core Task**: Retrieve the complete YAML config block for `scoring_config_name` from scoring-rules.md and return structured rule data.

**Output Contract** (must be structured JSON):
```json
{
  "phase": "rule_loading",
  "config_name": "Customer Opportunity Scoring v2",
  "dimensions": [
    {"name": "Business Scale", "weight": 0.20, "source_field": "revenue", "scoring_criteria": [...]},
    ...
  ],
  "special_rules": [
    {"name": "Tier-1 Churn Alert", "conditions": [...], "score_adjustment": -20, "reason": "...", "suggestion": "..."},
    ...
  ],
  "grade_thresholds": {"high": 80, "medium": 60, "low": 0},
  "action_suggestions": {"high": "...", "medium": "...", "low": "..."},
  "custom_weights_applied": false,
  "weight_normalization_warning": null
}
```

**Weight Merge Logic** (executed within this Phase):
1. If `custom_weights` is non-null, merge into default weights (override only specified dimensions)
2. Check if weight sum equals 1; if not, normalize and set `weight_normalization_warning: "Weight sum is X, auto-normalized. Consider reviewing weight settings."`
3. Set `custom_weights_applied: true`

**Error Handling**: If `scoring_config_name` does not exist in scoring-rules.md, error: "Rule set not found. Please confirm the name or create the rule set first." Terminate orchestration.

**Degradation**: If knowledge-rag fails to load, this Skill directly reads references/scoring-rules.md and parses the corresponding config, annotated `[Degraded: Knowledge-RAG not loaded]`.

## Phase 3 - Score Calculation (Data-Analyst)

**Mandatory load**: Call `skill` tool with `name: "data-analyst"`

**Input Contract**:
- Phase 1 extraction result
- Phase 2 rule_loading result
- Analysis mode: `"scoring"` (custom scoring analysis mode)
- Analysis instruction: score per criteria → weighted calculation → rule hit detection

**Scoring Calculation Rules**:

1. **Dimension Scoring**: Each dimension matches `raw_value` against `scoring_criteria` for a raw score (1-10). `raw_value` null → raw score = null.
2. **Weighted Calculation**: `weighted_score = raw_score × weight × 10` (null → 0). `total = Σ weighted_score` (max 100).
3. **Grade Determination**: High (≥80) | Medium (60-79) | Low (<60)
4. **Rule Hit Detection** (when `rule_adjustment=true`): iterate `special_rules`; if all conditions are true, rule is hit; execute `score_adjustment`; floor at 0.

**Output Contract** (must be structured JSON):
```json
{
  "phase": "scoring",
  "scoring_matrix": [
    {"Dimension": "Business Scale", "Weight": "20%", "Raw Value": "50M", "Raw Score": 8, "Weighted Score": 16.0, "Rule Hit": "✓ Pass"},
    ...
  ],
  "summary": {
    "raw_total": 63.5,
    "rule_adjustments": [
      {"rule": "Tier-1 Churn Alert", "conditions_check": [{"field":"level","expected":"Tier-1","actual":"Tier-1","hit":true},...], "adjustment": -20}
    ],
    "final_total": 43.5,
    "grade": "Low",
    "action_suggestion": "Urgent follow-up recommended..."
  },
  "all_dimensions_null": false
}
```

**Error Handling**:
- Rule hit causes total < 0 → set total to 0, annotate "Multiple risk rules stacked. Strong attention recommended."
- All dimension raw scores are null → error: "Target object is missing all scoring dimension data. Cannot score." Terminate orchestration.

**Degradation**: If data-analyst fails to load, this Skill manually calculates per the rules above, annotated `[Degraded: Data-Analyst not loaded]`.

## Phase 4 - Report Generation (Report-Generator)

**Mandatory load**: Call `skill` tool with `name: "report-generator"`

**Input Contract**:
- report_type: `"customer_brief"`
- Phase 3 scoring result
- output_format: user-specified format

**Report Must Include 5 Modules**:

**Module 1 - Scoring Matrix Table**

| Dimension | Weight | Raw Score | Weighted Score | Rule Hit |
|-----------|--------|-----------|----------------|----------|
| Business Scale | 20% | 8 | 16.0 | ✓ Pass |
| ... | ... | ... | ... | ... |
| **Total** | **100%** | — | **XX** | — |

Rule hit labels: ✓ Pass / ⚠️ Risk / — No rule

**Module 2 - Summary Row**: total score, grade (High/Medium/Low), recommended action

**Module 3 - Rule Config Display**: currently active scoring rule YAML snippet (shows rules are parameterized)

**Module 4 - Hit Rule Explanation**: each hit rule shows rule name, per-condition match (✓/✗), adjustment value, adjustment reason

**Module 5 - Sensitivity Note**: "Modify weights/rules and re-run to take effect. No Skill code changes needed."

**Degradation**: If report-generator fails to load, this Skill manually generates report per the 5-module format above, annotated `[Degraded: Report-Generator not loaded]`.

## Security Requirements

1. Customer names are anonymized as "Client A/B/C" during archiving
2. Scoring rules are core business assets; archive with label "Internal reference, do not distribute"
3. When total score < 50 triggers alert, report must note "This conclusion is for internal reference only and should not be the sole basis for client classification"
4. Do not display contract amounts directly in output; show only "Met/Not Met"

## Error Handling Quick Reference

| Error Scenario | Handling |
|----------------|----------|
| target_object missing dimension data | Annotate "Data missing", raw score null, weighted score 0, highlight |
| scoring_config_name not found | Error: "Rule set not found. Please confirm the name or create the rule set first." Terminate |
| Custom weight sum ≠ 1 | Auto-normalize with warning |
| Rule hit causes total < 0 | Set total to 0, annotate "Multiple risk rules stacked. Strong attention recommended." |
| All dimension raw scores null | Error: "Target object is missing all scoring dimension data. Cannot score." Terminate |
| Component load failure | Activate degradation strategy, annotate degraded mode, output format unchanged |

## Rule Library and Orchestration Protocol

- Complete scoring rule configs: [references/scoring-rules.md](references/scoring-rules.md)
- 4-Phase orchestration protocol: [references/orchestration.md](references/orchestration.md)
- Phase prompt templates and pipeline construction: [references/pipeline-phases.md](references/pipeline-phases.md)
- Generic dispatcher (independent skill): phase-orchestrator
