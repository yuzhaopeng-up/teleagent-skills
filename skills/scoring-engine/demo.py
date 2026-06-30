from .engine import ScoringEngine

SAMPLE_TARGETS = [
    {
        "id": "CUST-001 华瑞集团",
        "annual_revenue": 35000,
        "revenue_growth_pct": 12.5,
        "it_budget_level": "high",
        "years_cooperated": 6,
        "active_contracts": 4,
        "dm_access_level": "senior",
        "digital_maturity": "defined",
        "five_g_readiness": "piloting",
        "pipeline_projects": 7,
        "payment_credit_grade": "a",
        "churn_risk": "low",
        "compliance_status": "compliant",
    },
    {
        "id": "CUST-002 明远科技",
        "annual_revenue": 800,
        "revenue_growth_pct": -5,
        "it_budget_level": "low",
        "years_cooperated": 2,
        "active_contracts": 1,
        "dm_access_level": "middle",
        "digital_maturity": "initial",
        "five_g_readiness": "exploring",
        "pipeline_projects": 2,
        "payment_credit_grade": "b",
        "churn_risk": "medium",
        "compliance_status": "warning",
    },
    {
        "id": "CUST-003 鼎盛金控",
        "annual_revenue": 150000,
        "revenue_growth_pct": 22,
        "it_budget_level": "premium",
        "years_cooperated": 12,
        "active_contracts": 15,
        "dm_access_level": "c_level",
        "digital_maturity": "optimizing",
        "five_g_readiness": "deploying",
        "pipeline_projects": 12,
        "payment_credit_grade": "aa",
        "churn_risk": "none",
        "compliance_status": "excellent",
    },
]


def main():
    engine = ScoringEngine()
    print("=" * 60)
    print("  TeleAgent Scoring Engine Demo")
    print("  规则系统: 政企客户商机评分 v1.0")
    print("=" * 60)
    for target in SAMPLE_TARGETS:
        result = engine.score(target)
        print(ScoringEngine.format_report(result))
        print()


if __name__ == "__main__":
    main()
