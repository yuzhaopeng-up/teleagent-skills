---
name: data-aggregator
description: >
  Data Aggregator — performs secondary processing on raw data from a data executor:
  validation, cleaning, aggregation, year-over-year/month-over-month comparison, statistical enhancement and annotation.
  4-Phase forced orchestration via Phase-Orchestrator. Depends on Data-Analyst component.
  Triggers: aggregation, statistics, grouping, YoY/MoM, TOP ranking, data summarization.
name_cn: 数据聚合器
description_cn: 对查询结果进行聚合统计、同比环比计算和智能标注的数据加工组件
version: "1.0.0"
author: "yuzhaopeng"
license: "Apache-2.0"
---

# Data Aggregator

Core data aggregation component. Depends on Data-Analyst, orchestrated via Phase-Orchestrator.

## Parameters

| Parameter | Type | Required | Default | Description |
|-----------|------|----------|---------|-------------|
| raw_data | JSON array | Yes | - | Raw data from data executor |
| aggregation_config | JSON | Yes | - | Aggregation configuration (operation types and parameters) |
| comparison_config | JSON | No | null | YoY/MoM comparison configuration |
| null_strategy | Option | No | ignore | Null strategy: ignore/fill_zero/mark |

## Supported Aggregation Operations

| Operation | Description | Input Requirement | Output |
|-----------|-------------|-------------------|--------|
| count | Count | Any field | Number |
| sum | Sum | Numeric field | Number |
| avg | Average | Numeric field | Number |
| max | Maximum | Numeric/Date field | Number/Date |
| min | Minimum | Numeric/Date field | Number/Date |
| percentile | Percentile | Numeric field + p value | Number |
| group_by | Group by | Any field + aggregate function | Grouped results |
| top_n | Top N | Sort field + N value | Sorted results |
| compare | YoY/MoM | Numeric field + time dimension | Comparison results |
| derive | Derived calc | Existing fields + formula | New field |

## 4-Phase Forced Orchestration Protocol

Orchestrated via Phase-Orchestrator. Each Phase loads components via skill tool and launches a general-type sub-Agent via task tool.

### Phase 1: Data Validation and Cleaning

**Load component**: skill -> `data-analyst`

**Execution**: task tool launches general-type sub-Agent, prompt:

```
You are the Phase 1 executor of the Data Aggregator. Validate and clean the raw data.

Input: raw_data (JSON array), null_strategy (ignore/fill_zero/mark)

Step 1: Format validation
- Check raw_data is a valid JSON array
- Check each record has consistent structure (same field names)
- Check numeric fields are number type (not string)

Step 2: Null handling (based on null_strategy)
- ignore -> skip records with null values
- fill_zero -> replace null values with 0
- mark -> keep null values but flag as "data_missing"

Step 3: Outlier detection
- Numeric fields: detect values beyond 3-sigma range
- Date fields: detect future dates or very old dates
- Enum fields: detect values not in known enum list
- Flag but do not remove outliers

Step 4: Data summary
- Total rows, field count
- Each field's type, null rate, unique count
- Numeric fields' min/max/avg/median

Output JSON:
{
  "validated_data": [...],
  "data_quality": {
    "total_rows": 0, "total_fields": 0,
    "null_count": 0, "null_rate": 0.0,
    "outlier_count": 0, "outlier_fields": []
  },
  "field_summary": {
    "<field_name>": {"type": "number|string|date", "null_rate": 0.0, "unique_count": 0, "min": null, "max": null, "avg": null}
  },
  "cleaning_actions": ["Replaced null with 0 (3 records)", "Flagged 2 outliers"],
  "phase_status": "success|warning"
}
```

### Phase 2: Aggregation Calculation

**Load component**: skill -> `data-analyst`

**Execution**: task tool launches general-type sub-Agent, prompt:

```
You are the Phase 2 executor of the Data Aggregator. Execute aggregation calculations.

Input: Phase 1 output validated_data, aggregation_config

Execute based on aggregation_config:

group_by: group by specified field, apply aggregate function per group
top_n: sort by specified field, take top N, add rank and percentile columns
percentile: calculate specified percentile values (supports 25th/50th/75th/90th/95th/99th)
derive (derived calculation): calculate new fields from existing ones
  - ratio: ratio
  - difference: difference
  - growth_rate: growth_rate = (current - previous) / previous * 100

Output JSON:
{
  "aggregated_data": [...],
  "aggregation_meta": {
    "operations_performed": ["group_by:plan_type", "count", "avg:amount"],
    "groups_count": 0,
    "result_rows": 0
  },
  "phase_status": "success"
}
```

### Phase 3: Comparison Calculation (YoY/MoM)

**Conditional execution**: Only when comparison_config is not null; otherwise skip and pass Phase 2 output directly to Phase 4.

**Execution**: task tool launches general-type sub-Agent, prompt:

```
You are the Phase 3 executor of the Data Aggregator. Calculate year-over-year and month-over-month comparisons.

Input: Phase 2 output aggregated_data, comparison_config

YoY calculation: same dimension, current period vs same period last year
  YoY = (current - last_year) / last_year * 100%
  Annotation: up / down / flat

MoM calculation: same dimension, current period vs previous period
  MoM = (current - last_month) / last_month * 100%
  Annotation: up / down / flat

Notes:
- Same period last year not available -> annotate "no_comparable_data"
- Base is 0 -> annotate "base_zero_cannot_calculate"
- Change exceeds 100% -> annotate "large_fluctuation"

Output JSON:
{
  "comparison_data": [
    {
      "dimension": "Premium Plan", "current": 47, "previous": 35, "last_year": 28,
      "mom_change": 34.3, "mom_direction": "up",
      "yoy_change": 67.9, "yoy_direction": "up"
    }
  ],
  "comparison_meta": {
    "current_period": "2026-05", "previous_period": "2026-04",
    "yoy_period": "2025-05", "data_completeness": "full|partial"
  },
  "phase_status": "success|partial"
}
```

### Phase 4: Statistical Enhancement and Annotation

**Execution**: task tool launches general-type sub-Agent, prompt:

```
You are the Phase 4 executor of the Data Aggregator. Add statistical enhancement and smart annotations to aggregation results.

Input: Phase 3 output comparison_data (or Phase 2 aggregated_data if Phase 3 skipped)

Step 1: Derived metrics
- Proportion: each dimension value / total * 100%
- Cumulative: cumulative value and cumulative percentage by sort order
- Z-Score: deviation of each dimension from the mean

Step 2: Smart annotation
- YoY/MoM change exceeds 20% -> focus_attention
- Z-Score > 2 -> anomaly
- Rank change exceeds 3 positions -> rank_change annotation
- CR3 proportion > 70% -> high_concentration

Step 3: Summary generation
- One-sentence summary of data characteristics
- List TOP3 attention items
- Flag anomalies requiring special attention

Output JSON:
{
  "enhanced_data": [...],
  "annotations": [
    {"dimension": "Premium Plan", "type": "significant_increase", "detail": "MoM growth 34.3%, well above average"}
  ],
  "derived_metrics": {
    "concentration_cr3": 0.72,
    "gini_coefficient": 0.38,
    "total": 140,
    "average": 28
  },
  "summary": {
    "one_liner": "Support tickets concentrated on Premium Plan (33.6%) and Standard Plan (27.1%)",
    "top3_attention": ["Premium Plan: MoM growth 34.3%", "Standard Plan: proportion 27.1%", "Basic Plan: YoY decline 12%"],
    "anomalies": ["Enterprise Plan ticket volume significantly below average"]
  },
  "phase_status": "success"
}
```

## Phase Data Passing

- Phase 1 -> Phase 2: `{ "validated_data": [...], "data_quality": {...}, "field_summary": {...} }`
- Phase 2 -> Phase 3: `{ "aggregated_data": [...], "aggregation_meta": {...} }`
- Phase 3 -> Phase 4: `{ "comparison_data": [...], "comparison_meta": {...}, "aggregated_data": [...] }`

## Degradation Strategy

| Condition | Degradation Behavior |
|-----------|---------------------|
| Phase 1 data quality poor (null rate > 30%) | Degrade to descriptive statistics only |
| Phase 2 aggregation fails | Return raw data + error explanation |
| Phase 3 no historical data | Skip comparison, proceed directly to Phase 4 |
| Phase 4 annotation fails | Return aggregated data only, without annotations |

## Usage Example

Input:
```json
{
  "raw_data": [
    {"plan_type": "Premium Plan", "ticket_count": 47},
    {"plan_type": "Standard Plan", "ticket_count": 38},
    {"plan_type": "Basic Plan", "ticket_count": 25},
    {"plan_type": "Lite Plan", "ticket_count": 18},
    {"plan_type": "Enterprise Plan", "ticket_count": 12}
  ],
  "aggregation_config": {
    "operations": ["group_by", "top_n", "derive"],
    "group_by": {"field": "plan_type"},
    "top_n": {"field": "ticket_count", "n": 5, "order": "desc"},
    "derive": [{"name": "percentage", "formula": "value / total * 100"}]
  },
  "comparison_config": {
    "current_period": "2026-05",
    "previous_period": "2026-04",
    "yoy_period": "2025-05",
    "metric": "ticket_count"
  }
}
```

Final output:
```json
{
  "enhanced_data": [
    {"plan_type": "Premium Plan", "ticket_count": 47, "percentage": 33.6, "rank": 1, "mom": "up 34.3%", "yoy": "up 67.9%"},
    {"plan_type": "Standard Plan", "ticket_count": 38, "percentage": 27.1, "rank": 2, "mom": "up 5.6%", "yoy": "up 18.8%"},
    {"plan_type": "Basic Plan", "ticket_count": 25, "percentage": 17.9, "rank": 3, "mom": "down 12.0%", "yoy": "flat"},
    {"plan_type": "Lite Plan", "ticket_count": 18, "percentage": 12.9, "rank": 4, "mom": "up 10.0%", "yoy": "up 28.6%"},
    {"plan_type": "Enterprise Plan", "ticket_count": 12, "percentage": 8.6, "rank": 5, "mom": "flat", "yoy": "down 7.7%"}
  ],
  "annotations": [
    {"dimension": "Premium Plan", "type": "significant_increase", "detail": "MoM growth 34.3%, YoY surge 67.9%"}
  ],
  "summary": {
    "one_liner": "Support tickets concentrated on Premium Plan (33.6%) and Standard Plan (27.1%)",
    "top3_attention": ["Premium Plan MoM +34%", "Standard Plan proportion 27%", "Basic Plan YoY decline 12%"]
  }
}
```
