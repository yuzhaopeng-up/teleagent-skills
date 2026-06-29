# Scoring Rule Library

This file contains YAML configurations for all scoring rule sets. At runtime the Skill loads the corresponding rule set based on the `scoring_config_name` parameter.

---

## Customer Opportunity Scoring v2

```yaml
scoring_config:
  name: "Customer Opportunity Scoring v2"
  version: "2.0"
  description: "Opportunity value scoring for B2B customers. 6 dimensions with weighted scoring + special rule hit detection."
  target_audience: "Account Managers, Business Development"

dimensions:
  - name: "Business Scale"
    weight: 0.20
    source_field: "revenue"
    scoring_criteria:
      - condition: "Annual revenue >= 100M"
        score: 9
      - condition: "Annual revenue 50M-100M"
        score: 8
      - condition: "Annual revenue 10M-50M"
        score: 6
      - condition: "Annual revenue 5M-10M"
        score: 4
      - condition: "Annual revenue < 5M"
        score: 2

  - name: "Technology Adoption"
    weight: 0.20
    source_field: "existing_products"
    scoring_criteria:
      - condition: "3+ existing products (Product A + Solution X + Solution Y etc.)"
        score: 9
      - condition: "2 existing products"
        score: 7
      - condition: "1 existing product"
        score: 5
      - condition: "No product but has technology roadmap"
        score: 3
      - condition: "No product and no roadmap"
        score: 1

  - name: "Solution Fit"
    weight: 0.25
    source_field: "match_products"
    scoring_criteria:
      - condition: "High fit: 3+ solution needs can be met"
        score: 9
      - condition: "Good fit: 2-3 solution needs can be met"
        score: 7
      - condition: "Moderate fit: 1-2 solution needs can be met"
        score: 5
      - condition: "Low fit: needs diverge from available solutions"
        score: 3
      - condition: "No fit"
        score: 1

  - name: "Partnership History"
    weight: 0.15
    source_field: "cooperation_years"
    scoring_criteria:
      - condition: "5+ years, multiple ongoing contracts"
        score: 9
      - condition: "3-5 years"
        score: 7
      - condition: "1-3 years"
        score: 6
      - condition: "Less than 1 year"
        score: 4
      - condition: "No history but has intent"
        score: 2

  - name: "Service Risk"
    weight: 0.10
    source_field: "recent_complaints"
    scoring_criteria:
      - condition: "0 complaints in last 3 months"
        score: 10
      - condition: "1 complaint in last 3 months"
        score: 4
      - condition: "2 complaints in last 3 months"
        score: 2
      - condition: "3+ complaints in last 3 months"
        score: 1

  - name: "Competitive Landscape"
    weight: 0.10
    source_field: "competitor_contact"
    scoring_criteria:
      - condition: "No competitor contact"
        score: 10
      - condition: "Competitor initial contact"
        score: 3
      - condition: "Competitor in active negotiation"
        score: 1
      - condition: "Competitor has won partial business"
        score: 0

special_rules:
  - name: "Tier-1 Account Churn Alert"
    priority: 1
    conditions:
      - field: "level"
        operator: "=="
        value: "Tier-1"
        description: "Account level = Tier-1"
      - field: "recent_complaints"
        operator: ">="
        value: 1
        description: "1+ complaints in last 3 months"
      - field: "competitor_contact"
        operator: "=="
        value: true
        description: "Competitor has made contact"
    score_adjustment: -20
    reason: "Tier-1 account showing complaints + competitor contact is a high churn risk signal"
    suggestion: "Recommend urgent follow-up, assign dedicated account manager, provide differentiated proposal"

  - name: "High-Fit Fast Track"
    priority: 2
    conditions:
      - field: "revenue"
        operator: ">="
        value: "50M"
        description: "Annual revenue >= 50M"
      - field: "existing_products"
        operator: "count>="
        value: 2
        description: "2+ existing products"
      - field: "competitor_contact"
        operator: "=="
        value: false
        description: "No competitor contact"
    score_adjustment: +10
    reason: "High-value, high-fit, no competitive pressure — accelerate deal closure"
    suggestion: "Recommend priority engagement, prepare full-solution proposal, pursue annual framework agreement"

grade_thresholds:
  high: 80
  medium: 60
  low: 0

action_suggestions:
  high: "Priority follow-up, assign dedicated solution, pursue deal closure"
  medium: "Maintain engagement, develop improvement plan, advance gradually"
  low: "Evaluate ROI, develop recovery or exit strategy"
```

---

## Customer Churn Risk v1

```yaml
scoring_config:
  name: "Customer Churn Risk v1"
  version: "1.0"
  description: "Assess customer churn risk. Focuses on complaints, competition, renewal intent, and contract trends."
  target_audience: "Customer Success Managers, Retention Teams"

dimensions:
  - name: "Renewal Intent"
    weight: 0.30
    source_field: "renewal_intention"
    scoring_criteria:
      - condition: "Explicitly confirmed renewal"
        score: 9
      - condition: "Positive attitude but not confirmed"
        score: 6
      - condition: "Ambiguous /观望 attitude"
        score: 3
      - condition: "Explicitly stated no renewal"
        score: 0

  - name: "Service Risk"
    weight: 0.25
    source_field: "recent_complaints"
    scoring_criteria:
      - condition: "0 complaints in last 3 months"
        score: 10
      - condition: "1 complaint in last 3 months"
        score: 4
      - condition: "2 complaints in last 3 months"
        score: 2
      - condition: "3+ complaints in last 3 months"
        score: 1

  - name: "Competitive Landscape"
    weight: 0.25
    source_field: "competitor_contact"
    scoring_criteria:
      - condition: "No competitor contact"
        score: 10
      - condition: "Competitor initial contact"
        score: 3
      - condition: "Competitor in active negotiation"
        score: 1
      - condition: "Competitor has won partial business"
        score: 0

  - name: "Contract Trend"
    weight: 0.20
    source_field: "contract_change"
    scoring_criteria:
      - condition: "Contract value growing"
        score: 9
      - condition: "Contract value stable"
        score: 6
      - condition: "Contract value declining"
        score: 3
      - condition: "Contract expired without renewal"
        score: 1

special_rules:
  - name: "Urgent Churn Alert"
    priority: 1
    conditions:
      - field: "renewal_intention"
        operator: "=="
        value: "no_renewal"
        description: "Explicitly stated no renewal"
      - field: "competitor_contact"
        operator: "=="
        value: true
        description: "Competitor has made contact"
    score_adjustment: -25
    reason: "Explicit no-renewal with competitor contact — extremely high churn risk"
    suggestion: "Recommend immediate executive escalation, provide dedicated retention proposal"

grade_thresholds:
  high: 75
  medium: 50
  low: 0

action_suggestions:
  high: "Account relationship stable, maintain current service level"
  medium: "Churn risk present, proactive engagement and value-add needed"
  low: "Extreme churn risk, activate escalation response process"
```

---

## Demo Data

### Input Parameters

```json
{
  "target_object": {
    "name": "Acme Manufacturing Corp",
    "level": "Tier-1",
    "revenue": "50M",
    "existing_products": ["Product A", "Product B"],
    "cooperation_years": 2,
    "recent_complaints": 1,
    "competitor_contact": true,
    "match_products": ["Solution X", "Solution Y"]
  },
  "scoring_config_name": "Customer Opportunity Scoring v2"
}
```

### Expected Scoring Process

| Dimension | Raw Value | Weight | Raw Score | Weighted Score | Rule Hit |
|-----------|-----------|--------|-----------|----------------|----------|
| Business Scale | Annual revenue 50M | 20% | 8 | 16.0 | ✓ Pass |
| Technology Adoption | Product A + Product B (2 products) | 20% | 7 | 14.0 | ✓ Pass |
| Solution Fit | Solution X + Solution Y (2 needs met) | 25% | 7 | 17.5 | ✓ Pass |
| Partnership History | 2 years partnership | 15% | 6 | 9.0 | — |
| Service Risk | 1 complaint in last 3 months | 10% | 4 | 4.0 | ⚠️ Risk |
| Competitive Landscape | Competitor contact confirmed | 10% | 3 | 3.0 | ⚠️ Risk |
| **Total** | | **100%** | — | **63.5** | |

### Rule Hit Detection

**Tier-1 Account Churn Alert** — ✗ Not fully hit initially (all 3 conditions must be met)
- ✓ Account level = Tier-1
- ✓ 1+ complaints in last 3 months
- ✓ Competitor has made contact

→ Hit! Adjustment -20 points

### Final Result

- Pre-adjustment total: 63.5 (Medium grade, 60-79)
- After Tier-1 Account Churn Alert hit: 63.5 - 20 = **43.5**
- Grade: Low (<60)
- Recommended action: Evaluate ROI, urgent follow-up recommended, assign dedicated account manager

> Calculation: 8×0.20×10 + 7×0.20×10 + 7×0.25×10 + 6×0.15×10 + 4×0.10×10 + 3×0.10×10 = 16+14+17.5+9+4+3 = 63.5 → hit -20 → **43.5**

### Sensitivity Demo: Weight Modification

If Competitive Landscape weight is raised to 30% (from 10%), Service Risk lowered to 5%:

```
custom_weights: {"Competitive Landscape": 0.30, "Service Risk": 0.05}
After normalization: Business Scale 19.0%, Technology Adoption 19.0%, Solution Fit 23.8%, Partnership History 14.3%, Service Risk 4.8%, Competitive Landscape 28.6%
```

Observation: Raising Competitive Landscape weight amplifies the impact of the low-scoring competitor-contact item, further reducing the total — demonstrating the "change config, not code" parameterization capability.
