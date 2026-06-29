# TeleAgent Skills

[![License: Apache 2.0](https://img.shields.io/badge/License-Apache%202.0-blue.svg)](LICENSE)
[![Skills](https://img.shields.io/badge/Skills-5-green.svg)]()
[![Compatible](https://img.shields.io/badge/Compatible-TeleAgent%20%7C%20Claude%20Code%20%7C%20Cursor%20%7C%20OpenClaw-orange)]()

> **Production-ready Agent Skills for AI-powered business workflows** — Drop-in components with 4-Phase orchestration, configurable rules, multi-source evidence analysis, NL2SQL, and interactive visualization.

## Why TeleAgent Skills?

Most AI agent skills hard-code business rules in prompts. Ours don't. Every skill follows three principles:

1. **Rules are parameterized** — Business changes? Update the YAML config, not the Skill code
2. **Components are composable** — 4-Phase orchestration with standardized JSON contracts between phases
3. **Every skill has degradation** — If a sub-component fails, the skill degrades gracefully, not crashes

## Quick Start

```bash
# Clone the repository
git clone https://github.com/yuzhaopeng-up/teleagent-skills.git

# Copy a skill to your agent's skills directory
cp -r teleagent-skills/skills/scoring-engine ~/.config/TeleAgent/skills/
```

## Skills Overview

| Skill | Description | Use Case |
|-------|-------------|----------|
| [Scoring Engine](skills/scoring-engine/) | Multi-dimensional weighted scoring with configurable rules | Customer scoring, risk assessment, supplier evaluation |
| [Evidence Chain](skills/evidence-chain/) | Multi-source cross-validation and root cause analysis | Fault diagnosis, complaint investigation, audit verification |
| [Data Aggregator](skills/data-aggregator/) | Statistical aggregation with YoY/MoM comparison | Business reporting, trend analysis, KPI dashboards |
| [Visualization Renderer](skills/visualization-renderer/) | Auto chart recommendation + interactive ECharts HTML | Data dashboards, report visualization, presentation |
| [NL2Query](skills/nl2-query/) | Natural language to structured query with confidence scoring | Self-service data query, business intelligence |

> Looking for multi-agent communication skills? See [agent-cluster-comm](https://github.com/yuzhaopeng-up/agent-cluster-comm) — Redis message bus, encrypted P2P, group chat bots, async handoff, and cluster health monitoring.

## Architecture

Every skill follows the 4-Phase component orchestration pattern:

```
┌─ Phase 1: Extract (Info-Extractor) ────┐
│  Parse input → structured JSON           │
└──────────────────┬──────────────────────┘
                   ▼
┌─ Phase 2: Analyze (Data-Analyst) ──────┐
│  Compute scores / validate / aggregate   │
└──────────────────┬──────────────────────┘
                   ▼
┌─ Phase 3: Generate (Report-Generator) ─┐
│  Format output with 5-module template    │
└──────────────────┬──────────────────────┘
                   ▼
┌─ Phase 4: Archive (Archive-Manager) ───┐
│  Desensitize + persist + audit trail     │
└─────────────────────────────────────────┘
```

**Key design decisions:**
- JSON contracts between phases — no free-text passing
- Each phase can be executed by independent sub-Agents
- Graceful degradation: if any component fails, the skill runs in degraded mode with clear labeling

## Quick Examples

### Scoring Engine — Rate a business opportunity
```json
{
  "target_object": {
    "name": "Acme Corp",
    "tier": "Tier-1",
    "revenue": "50M",
    "existing_products": ["Product A", "Product B"],
    "cooperation_years": 2,
    "recent_complaints": 1,
    "competitor_contact": true
  },
  "scoring_config_name": "Customer Opportunity Scoring v2"
}
```

### Evidence Chain — Cross-validate 3 sources
```json
{
  "evidence_sources": [
    {"source_name": "Client Report", "source_type": "complaint_report", "content": "..."},
    {"source_name": "System Alert", "source_type": "system_alert", "content": "..."},
    {"source_name": "SLA Agreement", "source_type": "contract_term", "content": "..."}
  ],
  "analysis_question": "Is there a genuine service quality issue?"
}
```

### NL2Query — Natural language to SQL
```
Input:  "Which subscription plan had the most support tickets last month?"
Output: SELECT plan, COUNT(*) AS ticket_count FROM support_ticket 
        WHERE month='2026-05' GROUP BY plan ORDER BY ticket_count DESC LIMIT 10
```

## Industry Use Cases

| Industry | Scoring Engine | Evidence Chain | Data Aggregator | Visualization | NL2Query |
|----------|----------------|----------------|-----------------|---------------|----------|
| Financial Services | Credit scoring, risk rating | Fraud investigation, claim verification | Portfolio analytics | Risk dashboards | "Show me high-risk accounts" |
| Manufacturing | Supplier evaluation | Equipment failure diagnosis | Production statistics | Quality dashboards | "Which line had most defects?" |
| Retail | Store scoring | Customer complaint analysis | Sales analytics | Performance boards | "Top 10 stores by revenue" |
| Healthcare | Patient risk assessment | Adverse event investigation | Clinical statistics | Outcome dashboards | "Readmission rate by department" |

## Contributing

See [CONTRIBUTING.md](CONTRIBUTING.md) for guidelines. We welcome:
- New skills following the 4-Phase pattern
- Industry-specific rule configs
- Bug fixes and improvements
- Documentation translations

## Security

- All example data is fully anonymized
- No real customer information in any file
- See [SECURITY.md](SECURITY.md) for our security policy

## License

Apache License 2.0 — Free for commercial and personal use.

---

If you find these skills useful, please consider giving this repo a star! It helps others discover it.
