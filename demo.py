"""
Master Demo: TeleAgent Skills — 5 Core Business Skills

Runs all 5 skills end-to-end with sample data:
1. Scoring Engine — Rate a business opportunity
2. Evidence Chain — Cross-validate 3 sources
3. Data Aggregator — Compute YoY/MoM metrics
4. Visualization Renderer — Generate ECharts HTML
5. NL2Query — Convert natural language to SQL
"""

import json
import os

from skills.scoring_engine import ScoringEngine
from skills.evidence_chain import EvidenceChainEngine
from skills.data_aggregator import DataAggregator
from skills.visualization_renderer import VisualizationRenderer
from skills.nl2_query import NL2QueryEngine


def demo_scoring():
    print("\n" + "=" * 60)
    print("1. Scoring Engine")
    print("=" * 60)
    engine = ScoringEngine()
    target = {
        "name": "Acme Corp",
        "tier": "Tier-1",
        "revenue": "50M",
        "existing_products": ["Product A", "Product B"],
        "cooperation_years": 2,
        "recent_complaints": 1,
        "competitor_contact": True,
    }
    result = engine.score(target, config_name="Customer Opportunity Scoring v2")
    print(f"Total Score: {result['total_score']}")
    print(f"Rating: {result['rating']}")
    for dim in result["dimensions"]:
        print(f"  - {dim['name']}: {dim['score']} (weight {dim['weight']})")


def demo_evidence():
    print("\n" + "=" * 60)
    print("2. Evidence Chain")
    print("=" * 60)
    engine = EvidenceChainEngine()
    sources = [
        {
            "source_name": "Client Report",
            "source_type": "complaint_report",
            "content": "Customer reports 2-hour service outage on June 20.",
        },
        {
            "source_name": "System Alert",
            "source_type": "system_alert",
            "content": "Database connection pool exhausted at 14:00 on June 20.",
        },
        {
            "source_name": "SLA Agreement",
            "source_type": "contract_term",
            "content": "SLA guarantees 99.9% uptime; outage exceeded allowed threshold.",
        },
    ]
    result = engine.analyze(
        evidence_sources=sources,
        question="Is there a genuine service quality issue?",
    )
    print(f"Confidence: {result['confidence']}")
    print(f"Conclusion: {result['conclusion']}")
    print(f"Root Cause: {result['root_cause']}")


def demo_aggregator():
    print("\n" + "=" * 60)
    print("3. Data Aggregator")
    print("=" * 60)
    engine = DataAggregator()
    data = [
        {"month": "2025-06", "region": "North", "revenue": 100, "cost": 60},
        {"month": "2026-05", "region": "North", "revenue": 120, "cost": 70},
        {"month": "2026-06", "region": "North", "revenue": 135, "cost": 75},
        {"month": "2025-06", "region": "South", "revenue": 80, "cost": 50},
        {"month": "2026-05", "region": "South", "revenue": 95, "cost": 55},
        {"month": "2026-06", "region": "South", "revenue": 110, "cost": 60},
    ]
    result = engine.aggregate(data, group_by=["region"], metrics=["revenue", "cost"])
    print(json.dumps(result, indent=2, ensure_ascii=False))


def demo_visualization():
    print("\n" + "=" * 60)
    print("4. Visualization Renderer")
    print("=" * 60)
    renderer = VisualizationRenderer()
    data = [
        {"month": "2026-01", "revenue": 100},
        {"month": "2026-02", "revenue": 120},
        {"month": "2026-03", "revenue": 115},
        {"month": "2026-04", "revenue": 140},
        {"month": "2026-05", "revenue": 160},
        {"month": "2026-06", "revenue": 175},
    ]
    output_path = "demo_chart.html"
    renderer.render(data, x="month", y="revenue", chart_type="line", output_path=output_path)
    print(f"Chart saved to: {os.path.abspath(output_path)}")


def demo_nl2query():
    print("\n" + "=" * 60)
    print("5. NL2Query")
    print("=" * 60)
    engine = NL2QueryEngine()
    schema = {
        "support_ticket": {
            "columns": ["id", "plan", "created_at", "status"],
            "description": "Customer support tickets",
        }
    }
    result = engine.convert(
        query="Which subscription plan had the most support tickets last month?",
        schema=schema,
    )
    print(f"SQL: {result['sql']}")
    print(f"Confidence: {result['confidence']}")


def main():
    print("\nTeleAgent Skills — Master Demo")
    demo_scoring()
    demo_evidence()
    demo_aggregator()
    demo_visualization()
    demo_nl2query()
    print("\n" + "=" * 60)
    print("All 5 skills executed successfully.")
    print("=" * 60)


if __name__ == "__main__":
    main()
