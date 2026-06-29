---
name: evidence-chain
description: >
  Multi-source evidence chain analysis. Extracts evidence from multiple independent sources,
  cross-validates, detects conflicts, evaluates confidence, and outputs analysis reports with
  root cause judgments. Use when: (1) analyzing client complaints against system records to
  find truth, (2) cross-validating data from 2+ sources (complaints, alerts, SLA agreements,
  operation logs), (3) detecting contradictions between sources, (4) producing confidence-scored
  root cause judgments.
  Triggers: evidence chain, cross-validation, multi-source analysis, conflict detection,
  confidence assessment, root cause inference, fault diagnosis analysis, complaint verification,
  alert correlation, evidence chain analysis.
name_cn: 多源证据链分析组件
description_cn: 从多个独立来源提取证据，交叉验证、识别冲突、评估置信度，输出带根因判断的分析报告
version: "1.0.0"
author: "yuzhaopeng"
license: "Apache-2.0"
---

# Evidence-Chain

Core philosophy: **Not single-source RAG answering from a knowledge base, but multi-source evidence chain — ordinary RAG answers from a knowledge base; advanced Skills cross-validate from multiple sources, detect conflicts, and evaluate confidence.**

## Component Orchestration

This Skill chains 4 components that **must execute in strict sequence**; each stage's output is the next stage's input:

```
Info-Extractor ──→ Data-Analyst ──→ Report-Generator ──→ Archive-Manager
    Phase 1            Phase 2            Phase 3              Phase 4
  Evidence        Cross-validation      Report             Archiving
  extraction      + inference          generation         & audit trail
```

**Execution Rules**:
- Each component must be loaded via the `skill` tool before execution; skipping or merging is prohibited
- Components pass intermediate results as structured JSON objects (see output contracts per Phase below)
- If any component fails to load, execute degradation strategy (see "Error Handling")

Detailed orchestration protocol: [references/orchestration.md](references/orchestration.md).

## Input Parameters

### Required

| Parameter | Type | Description |
|-----------|------|-------------|
| `evidence_sources` | JSON array | Each element contains `source_name`, `source_type`, `content` |
| `analysis_question` | string | Core question, e.g. "Is there a persistent service quality issue with the network service?" |

`source_type` enum: `complaint_report` / `system_alert` / `contract_term` / `operation_log` / `other`

### Optional

| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `conflict_sensitivity` | enum | `medium` | `high` / `medium` / `low` |
| `confidence_threshold` | 0-1 | `0.7` | Below this value, root cause is annotated "⚠️ Needs further verification" |
| `output_format` | enum | `markdown` | `markdown` / `json` / `table` |

## Phase 1 — Info-Extractor: Evidence Extraction

**Invocation**: Load `info-extractor` skill via `skill` tool, execute extraction for each source

**Input**: Each element in `evidence_sources`

**Processing**:
1. Iterate `evidence_sources`, call Info-Extractor for each source
2. Extract structured fields: time, event, values, objects, location, etc.
3. Annotate each piece of evidence with source type and initial confidence

| Source Type | Initial Confidence | Attribute |
|-------------|-------------------|-----------|
| complaint_report | ⭐⭐ (0.4) | Subjective statement |
| system_alert | ⭐⭐⭐⭐ (0.8) | Objective data |
| contract_term | ⭐⭐⭐ (0.6) | Authoritative reference |
| operation_log | ⭐⭐⭐⭐ (0.8) | Objective data |
| other | ⭐⭐⭐ (0.6) | Pending assessment |

**Phase 1 Output Contract** (passed to Phase 2):

```json
{
  "extracted_evidences": [
    {
      "evidence_id": "E-01",
      "source_name": "Source Name",
      "source_type": "complaint_report",
      "extracted_fields": { "time": "...", "event": "...", "value": "..." },
      "initial_confidence": 0.4,
      "raw_summary": "One-line summary"
    }
  ]
}
```

## Phase 2 — Data-Analyst: Cross-Validation and Inference

**Invocation**: Load `data-analyst` skill via `skill` tool, use Phase 1 output as analysis input, execute cross-validation and inference per the sub-steps below

**Input**: Phase 1 `output_phase1` object

**Sub-steps**:

### 2a - Timeline Alignment
- Sort `extracted_evidences` chronologically
- Identify multi-source records of the same event, annotate time deltas
- Output: `timeline_events` array

### 2b - Conflict Detection
- Compare descriptions of the same event from different sources
- Adjust detection granularity per `conflict_sensitivity`
- Each conflict annotated: conflict ID, type, description, involved sources, difference analysis
- Conflict detection rules: [references/conflict-rules.md](references/conflict-rules.md)

### 2c - Confidence Assessment
- Formula: `composite_confidence = source_confidence × cross_validation_score × time_decay`
  - Cross-validation score: proportion of independent sources confirming the same fact (0-1)
  - Time decay: evidence older than 30 days decays by 0.95^months

### 2d - Root Cause Inference
- Three dimensions: **Earliest Occurrence** / **Downstream Dependency** / **High Frequency**
- Output: suspected root cause + confidence level (High/Medium/Low) + numeric value + basis
- Below `confidence_threshold` → annotate "⚠️ Needs further verification"

**Phase 2 Output Contract** (passed to Phase 3):

```json
{
  "timeline_events": [...],
  "conflicts": [
    {
      "conflict_id": "C-01",
      "type": "value_conflict",
      "description": "...",
      "sources_involved": ["E-01", "E-03"],
      "difference": "delta=1 occurrence",
      "possible_reason": "..."
    }
  ],
  "confidence_scores": [
    { "evidence_id": "E-01", "source_confidence": 0.4, "cross_validation": 0.7, "time_decay": 1.0, "final_confidence": 0.28 }
  ],
  "root_cause": {
    "suspected": "...",
    "confidence_level": "High",
    "confidence_value": 0.85,
    "basis": ["Earliest occurrence", "Downstream dependency", "High frequency"],
    "needs_further_verification": false
  },
  "recommended_actions": [
    { "priority": "🔴 Urgent", "action": "...", "linked_evidence": ["E-04"] },
    { "priority": "🟡 Concurrent", "action": "...", "linked_evidence": ["E-01","E-05"] }
  ]
}
```

## Phase 3 — Report-Generator: Generate Report

**Invocation**: Load `report-generator` skill via `skill` tool, generate report from Phase 2 analysis results per template

**Input**: Phase 2 `output_phase2` object + Phase 1 `output_phase1` object

**Output Format**: Selected per `output_format` parameter

### Module 1: Evidence List Table
| # | Source | Source Type | Time | Key Content | Confidence |
|---|--------|------------|------|-------------|------------|

### Module 2: Conflict Detection Section
Each conflict: conflict ID + type + description + involved sources + difference analysis

### Module 3: Root Cause Judgment
Suspected root cause + confidence (High/Medium/Low) + numeric value + basis + ⚠️ marker (if applicable)

### Module 4: Recommended Actions
| Priority | Recommended Action | Linked Evidence |
|----------|-------------------|-----------------|
| 🔴 Urgent | ... | Evidence #n |
| 🟡 Concurrent | ... | Evidence #n |
| 🟢 Deferred | ... | Evidence #n |

### Module 5: Metadata
Analysis time / Evidence count / Conflict count / Max confidence

**Phase 3 Output Contract** (passed to Phase 4):

```json
{
  "report_content": "Full report text (markdown/json/table)",
  "report_metadata": {
    "analysis_time": "2026-06-20T...",
    "evidence_count": 7,
    "conflict_count": 2,
    "max_confidence": 0.85
  }
}
```

## Phase 4 — Archive-Manager: Archiving

**Invocation**: Load `archive-manager` skill via `skill` tool for archiving

**Input**: Phase 3 `output_phase3` object

**Archive Contents**:
- Analysis process: Phase 1 extraction results + Phase 2 analysis results
- Analysis conclusion: Phase 3 full report
- Archive metadata: Analyst, analysis time, evidence source list

**Pre-Archive Anonymization Required**:
- Client name → "Client A"
- Contract IDs retained but financial details hidden

## Component Load Failure Degradation Strategy

| Component | Fallback when load fails |
|-----------|-------------------------|
| Info-Extractor | Manually extract structured fields per source type, annotate initial confidence |
| Data-Analyst | Manually execute Phase 2 sub-steps (timeline alignment / conflict detection / confidence assessment / root cause inference) per SKILL.md rules |
| Report-Generator | Manually generate report per Phase 3's 5-module template in SKILL.md |
| Archive-Manager | Save archive contents as local `.md` file, filename includes timestamp and analysis question |

**Degraded reports must annotate in metadata**: `"degraded": true, "degraded_components": ["info-extractor"]`

## Error Handling

| Condition | Behavior |
|-----------|----------|
| Source count = 0 | Error: "At least 2 evidence sources are required for cross-validation" |
| Source count = 1 | Degrade to single-source analysis + warning: "Only 1 source available; cross-validation not possible; conclusion confidence is limited" |
| All evidence missing time info | Skip Phase 2a + report annotation "Missing time dimension; chronological analysis not possible" |
| sensitivity=high but no conflicts | Output "No conflicts detected; all source descriptions are consistent" |
| Root cause confidence < threshold | Annotate "⚠️ Needs further verification" + list evidence that needs supplementation |

## Security Requirements

- Client complaint content **must not** be archived to public knowledge bases before anonymization
- SLA contract terms are confidential; **must be anonymized** during archiving
- Root cause judgments **must include confidence level**; low-confidence conclusions must not be used as sole basis for actions
- All archive records **must include**: analyst, analysis time, evidence source list

## Demo Data

Full 3-source evidence chain example: [references/demo-data.md](references/demo-data.md).

## Self-Check Checklist

- [ ] Can correctly extract structured fields from 3 different source types
- [ ] Can detect conflicts between client statements and system records
- [ ] Can produce confidence-scored root cause judgments
- [ ] Can distinguish 🔴 Urgent / 🟡 Concurrent / 🟢 Deferred action priorities
- [ ] Anonymized data correctly hides client names
- [ ] Archive records include complete evidence source list
