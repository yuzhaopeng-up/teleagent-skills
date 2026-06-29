---
name: nl2-query
description: >
  Natural Language to Query — converts natural language queries into structured query objects.
  Includes: intent recognition, entity extraction, query construction, confidence scoring, query optimization.
  Depends on: Info-Extractor, Data-Analyst, Security-Guard. Orchestrated via Phase-Orchestrator.
  Triggers: natural language query, NL2SQL, text-to-SQL, ask data, smart query.
name_cn: NL2Query 自然语言转查询
description_cn: 将自然语言查询转换为结构化查询对象，含意图识别、实体提取、查询构建与安全验证
version: "1.0.0"
author: "yuzhaopeng"
license: "Apache-2.0"
---

# NL2Query — Natural Language to Query

Core component. Converts user natural language queries into structured query JSON for downstream data executors.

## Parameters

| Parameter | Type | Required | Default | Description |
|-----------|------|----------|---------|-------------|
| natural_language | Text | Yes | - | User's natural language query |
| context | JSON | No | {} | Context (historical queries, user preferences, permission token) |
| confidence_threshold | Number | No | 0.7 | Below this confidence, return candidate parses for user confirmation |
| dialect | Option | No | mysql | Target SQL dialect: mysql/postgresql/clickhouse |

## Domain References

Phase 1 and Phase 2 load domain knowledge: [references/domain_knowledge.md](references/domain_knowledge.md)

Phase 2 loads dialect adaptation rules when generating SQL preview: [references/dialect.md](references/dialect.md)

## 4-Phase Forced Orchestration Protocol

Orchestrated via Phase-Orchestrator. Each Phase launches a general-type sub-Agent via task tool. Phases pass data via structured JSON.

### Phase 1: Intent Recognition and Entity Extraction (Info-Extractor)

**Load component**: `skill(name="info-extractor")`

**Execution**: task tool launches general-type sub-Agent, prompt:

```
You are the Phase 1 executor of NL2Query. Extract intent and entities from the natural language query.

Load info-extractor skill: skill(name="info-extractor")

Read domain knowledge: read references/domain_knowledge.md

Input: natural_language = "<user query>"

Extraction rules:

Intent recognition: determine query_type (simple|comparison|trend|ranking|aggregate)
Entity extraction:
- Time entity: normalize to {"type":"month|quarter|year","value":"YYYY-MM|YYYY-QN|YYYY","relative":true|false}
- Region entity: normalize to {"type":"region","value":"<region_code>","name":"<display_name>"}
- Metric entity: normalize to {"metric":"<field>","aggregation":"count|sum|avg|max|min","direction":"asc|desc"}
- Dimension entity: normalize to {"dimension":"<field>","name":"<display_name>"}
- Object entity: normalize to {"field":"<field>","operator":"=|LIKE|IN","value":"<value>"}
Confidence scoring: assign 0-1 confidence score for each entity

Output JSON:
{
  "intent": { "query_type": "simple|comparison|trend|ranking|aggregate", "confidence": 0.0-1.0 },
  "entities": {
    "time": {"value": "2026-05", "type": "month", "confidence": 0.95, "raw": "last month"},
    "region": {"value": "Region_North", "name": "North", "confidence": 0.92, "raw": "North"},
    "metric": {"metric": "ticket_count", "aggregation": "count", "confidence": 0.88, "raw": "most tickets"},
    "dimension": {"dimension": "plan_type", "name": "plan", "confidence": 0.90, "raw": "plan"},
    "filter": null
  },
  "ambiguous_entities": [],
  "missing_entities": [],
  "overall_confidence": 0.0-1.0,
  "phase_status": "success|low_confidence"
}
```

### Phase 2: Query Construction (Data-Analyst)

**Load component**: `skill(name="data-analyst")`

**Input**: Phase 1 output `{ "intent": {...}, "entities": {...}, "overall_confidence": 0.xx }`

**Execution**: task tool launches general-type sub-Agent, prompt:

```
You are the Phase 2 executor of NL2Query. Construct a structured query based on Phase 1 intent and entities.

Load data-analyst skill: skill(name="data-analyst")

Read domain knowledge: read references/domain_knowledge.md
Read dialect rules: read references/dialect.md

Construction rules:

1. Determine target table (based on metric and dimension mapping):
   - ticket_count -> support_ticket table
   - amount/payment -> transaction table
   - customer related -> customer table
   - incident related -> incident table
   - Cross-table -> use integrated data source, requires JOIN

2. Construct structured_query:
{
  "table": "<table_name>",
  "dimensions": ["<from entities.dimension>"],
  "metrics": [{"name": "<metric_field>", "aggregation": "<aggregation_method>"}],
  "filters": [
    {"field": "region", "operator": "=", "value": "<region_code>"},
    {"field": "month", "operator": "=", "value": "<time_value>"},
    {"field": "<filter_field>", "operator": "<operator>", "value": "<filter_value>"}
  ],
  "sort": [{"field": "<sort_field>", "order": "<sort_direction>"}],
  "limit": <row_limit, default 100>
}

3. Inject implicit conditions:
   - ranking query -> auto-add ORDER BY + LIMIT
   - trend query -> auto-add GROUP BY month + ORDER BY month
   - comparison query -> auto-add GROUP BY dimension
   - No time condition -> default to current month
   - No region condition -> use region_filter from permission token

4. Complexity assessment: low(single table + WHERE + LIMIT) | medium(single table + GROUP BY + aggregate) | high(multi-table JOIN or subquery)

Output JSON:
{
  "structured_query": { ... },
  "query_type": "simple|comparison|trend|ranking|aggregate",
  "target_table": "<table_name>",
  "estimated_complexity": "low|medium|high",
  "implicit_conditions": ["<list of auto-added implicit conditions>"],
  "sql_preview": "<generated SQL preview (display only, not executable)>",
  "phase_status": "success|error"
}
```

### Phase 3: Query Validation and Optimization (Data-Analyst + Security-Guard)

**Input**: Phase 2 output `{ "structured_query": {...}, "query_type": "...", "estimated_complexity": "..." }`

**Execution**: task tool launches general-type sub-Agent, prompt:

```
You are the Phase 3 executor of NL2Query. Validate and optimize the structured query.

Step 1: Legality validation
- Check table field is in whitelist: customer, transaction, support_ticket, incident
- Check all field names are in corresponding table's field whitelist
- Check operator is legal: =, !=, >, <, >=, <=, IN, LIKE, BETWEEN
- Check value is reasonable (no SQL injection risk)

Step 2: Security check
Load security-guard skill: skill(name="security-guard")
- Detect SQL injection patterns: single-quote closure, UNION injection, OR 1=1, comment markers --
- Detect dangerous operations: DELETE, UPDATE, DROP, INSERT, ALTER
- Verify query is read-only

Step 3: Query optimization
- No LIMIT specified -> add LIMIT 100
- No sort specified -> sort by primary key or time descending
- Time range exceeds 1 year -> suggest narrowing range
- JOINs exceed 3 -> suggest simplifying query

Output JSON:
{
  "validated_query": { ... },
  "optimizations_applied": ["Added LIMIT 100", "Added ORDER BY month DESC"],
  "warnings": ["Query time range is large, suggest narrowing to within 3 months"],
  "security_check": "passed|blocked",
  "security_risks": [],
  "phase_status": "success|blocked|warning"
}
```

### Phase 4: Confidence Report and Candidate Generation

**Input**: Phase 3 output `{ "validated_query": {...}, "optimizations_applied": [...], "security_check": "..." }`

**Execution**: task tool launches general-type sub-Agent, prompt:

```
You are the Phase 4 executor of NL2Query. Generate final output and confidence report.

Step 1: Composite confidence calculation
- Intent recognition confidence x 0.3
- Entity extraction average confidence x 0.4
- Query validation pass rate x 0.3
- Total confidence < confidence_threshold (default 0.7) -> generate candidate parses

Step 2: Candidate parse generation (only when total confidence < 0.7)
- Generate 2-3 alternative parses for low-confidence entities
- Example: user says "last month" -> candidate 1: 2026-05, candidate 2: 2026-04
- Let user select the parse that best matches their intent

Step 3: Assemble final output

Output JSON:
{
  "status": "success|low_confidence|error",
  "structured_query": { ... },
  "entities": { ... },
  "confidence": {
    "overall": 0.0-1.0,
    "intent": 0.0-1.0,
    "entities_avg": 0.0-1.0,
    "validation": 0.0-1.0
  },
  "candidates": [],
  "sql_preview": "<final SQL preview>",
  "suggestions": ["You might also want to query: <related query suggestions>"],
  "phase_status": "success"
}
```

## Phase Data Passing

| Path | Data Format |
|------|-------------|
| Phase 1 -> 2 | `{ "intent": {...}, "entities": {...}, "overall_confidence": 0.xx }` |
| Phase 2 -> 3 | `{ "structured_query": {...}, "query_type": "...", "estimated_complexity": "..." }` |
| Phase 3 -> 4 | `{ "validated_query": {...}, "optimizations_applied": [...], "security_check": "..." }` |

## Degradation Strategy

| Condition | Handling |
|-----------|----------|
| Phase 1 confidence < 0.5 | Return raw input + prompt user to rephrase |
| Phase 2 construction fails | Attempt simplified query (remove least certain entities) |
| Phase 3 blocked by security | Return error directly, no degradation |
| Phase 4 confidence < 0.7 | Return candidate parses for user selection |

## Usage Example

Input: `natural_language: "which plan had the most support tickets in the North region last month"`, `context: { "permission_token": { "role": "manager", "region_scope": "all" } }`

Phase 4 final output:

```json
{
  "status": "success",
  "structured_query": {
    "table": "support_ticket",
    "dimensions": ["plan_type"],
    "metrics": [{"name": "ticket_count", "aggregation": "count"}],
    "filters": [
      {"field": "region", "operator": "=", "value": "Region_North"},
      {"field": "month", "operator": "=", "value": "2026-05"}
    ],
    "sort": [{"field": "ticket_count", "order": "desc"}],
    "limit": 10
  },
  "confidence": {"overall": 0.91, "intent": 0.93, "entities_avg": 0.91, "validation": 0.88},
  "sql_preview": "SELECT plan_type, COUNT(*) AS ticket_count FROM support_ticket WHERE region = 'Region_North' AND month = '2026-05' GROUP BY plan_type ORDER BY ticket_count DESC LIMIT 10"
}
```
