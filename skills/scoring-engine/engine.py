import yaml
import math
from dataclasses import dataclass, field
from typing import Any


DEFAULT_RULES_YAML = """
scoring_system:
  name: "政企客户商机评分"
  version: "1.0"
  dimensions:
    - id: financial
      name: "财务健康度"
      weight: 0.30
      rules:
        - id: revenue_scale
          name: "营收规模"
          weight: 0.40
          type: range
          field: annual_revenue
          ranges:
            - [0, 1000, 20]
            - [1000, 5000, 40]
            - [5000, 20000, 60]
            - [20000, 100000, 80]
            - [100000, 999999999, 100]
        - id: revenue_growth
          name: "营收增长率"
          weight: 0.30
          type: range
          field: revenue_growth_pct
          ranges:
            - [-999, -10, 10]
            - [-10, 0, 30]
            - [0, 5, 50]
            - [5, 15, 70]
            - [15, 999, 100]
        - id: budget_level
          name: "IT预算水平"
          weight: 0.30
          type: categorical
          field: it_budget_level
          mapping:
            low: 25
            medium: 55
            high: 85
            premium: 100
    - id: relational
      name: "关系紧密度"
      weight: 0.25
      rules:
        - id: cooperation_years
          name: "合作年限"
          weight: 0.35
          type: range
          field: years_cooperated
          ranges:
            - [0, 1, 20]
            - [1, 3, 45]
            - [3, 5, 65]
            - [5, 10, 85]
            - [10, 999, 100]
        - id: contract_count
          name: "合同数量"
          weight: 0.35
          type: range
          field: active_contracts
          ranges:
            - [0, 1, 15]
            - [1, 3, 40]
            - [3, 5, 65]
            - [5, 10, 85]
            - [10, 999, 100]
        - id: decision_maker_access
          name: "决策层触达"
          weight: 0.30
          type: categorical
          field: dm_access_level
          mapping:
            none: 10
            middle: 40
            senior: 70
            c_level: 100
    - id: opportunity
      name: "商机潜力"
      weight: 0.25
      rules:
        - id: digital_maturity
          name: "数字化成熟度"
          weight: 0.40
          type: categorical
          field: digital_maturity
          mapping:
            initial: 20
            developing: 45
            defined: 70
            managed: 90
            optimizing: 100
        - id: 5g_readiness
          name: "5G就绪度"
          weight: 0.30
          type: categorical
          field: five_g_readiness
          mapping:
            none: 10
            exploring: 35
            planning: 60
            piloting: 80
            deploying: 100
        - id: project_pipeline
          name: "项目管线"
          weight: 0.30
          type: range
          field: pipeline_projects
          ranges:
            - [0, 1, 20]
            - [1, 3, 45]
            - [3, 5, 65]
            - [5, 10, 85]
            - [10, 999, 100]
    - id: risk
      name: "风险控制"
      weight: 0.20
      rules:
        - id: payment_credit
          name: "付款信用"
          weight: 0.40
          type: categorical
          field: payment_credit_grade
          mapping:
            d: 15
            c: 35
            b: 60
            a: 85
            aa: 100
        - id: churn_signal
          name: "流失预警"
          weight: 0.35
          type: categorical
          field: churn_risk
          mapping:
            high: 15
            medium: 45
            low: 75
            none: 100
        - id: compliance
          name: "合规达标"
          weight: 0.25
          type: categorical
          field: compliance_status
          mapping:
            violation: 10
            warning: 40
            compliant: 80
            excellent: 100
  grade_thresholds:
    A: 85
    B: 70
    C: 55
    D: 40
    F: 0
"""


@dataclass
class RuleResult:
    rule_id: str
    rule_name: str
    score: float
    weight: float
    weighted_score: float
    raw_value: Any
    score_reason: str


@dataclass
class DimensionResult:
    dimension_id: str
    dimension_name: str
    weight: float
    rule_results: list
    weighted_score: float
    raw_score: float


@dataclass
class ScoringResult:
    target_id: str
    total_score: float
    grade: str
    dimension_results: list
    score_breakdown: dict = field(default_factory=dict)
    recommendations: list = field(default_factory=list)


class ScoringEngine:
    def __init__(self, rules_yaml: str | None = None):
        src = rules_yaml or DEFAULT_RULES_YAML
        self.config = yaml.safe_load(src)
        self.system = self.config["scoring_system"]
        self._validate_config()

    def _validate_config(self):
        dims = self.system.get("dimensions", [])
        total_w = sum(d["weight"] for d in dims)
        if not math.isclose(total_w, 1.0, rel_tol=1e-3):
            raise ValueError(f"Dimension weights sum to {total_w}, expected 1.0")
        for dim in dims:
            rules = dim.get("rules", [])
            rw = sum(r["weight"] for r in rules)
            if not math.isclose(rw, 1.0, rel_tol=1e-3):
                raise ValueError(
                    f"Dimension '{dim['id']}' rule weights sum to {rw}, expected 1.0"
                )

    def score(self, target: dict) -> ScoringResult:
        target_id = target.get("id", target.get("name", "unknown"))
        dim_results = []
        for dim_cfg in self.system["dimensions"]:
            dr = self._score_dimension(dim_cfg, target)
            dim_results.append(dr)
        total = sum(dr.weighted_score for dr in dim_results)
        grade = self._compute_grade(total)
        breakdown = {}
        for dr in dim_results:
            breakdown[dr.dimension_id] = {
                "name": dr.dimension_name,
                "weight": dr.weight,
                "raw_score": round(dr.raw_score, 2),
                "weighted_score": round(dr.weighted_score, 2),
                "rules": {
                    rr.rule_id: {
                        "name": rr.rule_name,
                        "score": rr.score,
                        "raw_value": rr.raw_value,
                        "reason": rr.score_reason,
                    }
                    for rr in dr.rule_results
                },
            }
        recs = self._generate_recommendations(dim_results)
        return ScoringResult(
            target_id=target_id,
            total_score=round(total, 2),
            grade=grade,
            dimension_results=dim_results,
            score_breakdown=breakdown,
            recommendations=recs,
        )

    def _score_dimension(self, dim_cfg: dict, target: dict) -> DimensionResult:
        rule_results = []
        for rule_cfg in dim_cfg["rules"]:
            rr = self._apply_rule(rule_cfg, target)
            rule_results.append(rr)
        raw = sum(r.weighted_score for r in rule_results)
        return DimensionResult(
            dimension_id=dim_cfg["id"],
            dimension_name=dim_cfg["name"],
            weight=dim_cfg["weight"],
            rule_results=rule_results,
            weighted_score=round(raw * dim_cfg["weight"], 4),
            raw_score=round(raw, 4),
        )

    def _apply_rule(self, rule_cfg: dict, target: dict) -> RuleResult:
        field_name = rule_cfg["field"]
        raw_value = target.get(field_name)
        rule_type = rule_cfg["type"]
        if raw_value is None:
            return RuleResult(
                rule_id=rule_cfg["id"],
                rule_name=rule_cfg["name"],
                score=0,
                weight=rule_cfg["weight"],
                weighted_score=0,
                raw_value=None,
                score_reason="字段缺失，默认0分",
            )
        if rule_type == "range":
            score, reason = self._eval_range(rule_cfg, raw_value)
        elif rule_type == "categorical":
            score, reason = self._eval_categorical(rule_cfg, raw_value)
        else:
            score, reason = 0, f"未知规则类型: {rule_type}"
        ws = score * rule_cfg["weight"]
        return RuleResult(
            rule_id=rule_cfg["id"],
            rule_name=rule_cfg["name"],
            score=score,
            weight=rule_cfg["weight"],
            weighted_score=round(ws, 4),
            raw_value=raw_value,
            score_reason=reason,
        )

    def _eval_range(self, rule_cfg: dict, value) -> tuple[float, str]:
        ranges = rule_cfg["ranges"]
        try:
            num = float(value)
        except (TypeError, ValueError):
            return 0, f"无法将值 '{value}' 转为数值"
        for low, high, score in ranges:
            if low <= num < high:
                return float(score), f"值{num}落在[{low},{high})区间，得分{score}"
        last = ranges[-1]
        if num >= last[1]:
            return float(last[2]), f"值{num}超过上限{last[1]}，取最高分{last[2]}"
        return 0, f"值{num}低于下限{ranges[0][0]}，得分0"

    def _eval_categorical(self, rule_cfg: dict, value) -> tuple[float, str]:
        mapping = rule_cfg.get("mapping", {})
        key = str(value).lower().replace(" ", "_")
        if key in mapping:
            return float(mapping[key]), f"类别'{value}'→得分{mapping[key]}"
        return 0, f"类别'{value}'未在映射表中找到，默认0分"

    def _compute_grade(self, score: float) -> str:
        thresholds = self.system.get("grade_thresholds", {})
        for grade, threshold in sorted(thresholds.items(), key=lambda x: -x[1]):
            if score >= threshold:
                return grade
        return "F"

    def _generate_recommendations(self, dim_results: list) -> list[str]:
        recs = []
        for dr in dim_results:
            weak_rules = [rr for rr in dr.rule_results if rr.score < 50]
            if weak_rules:
                names = ", ".join(rr.rule_name for rr in weak_rules)
                recs.append(
                    f"[{dr.dimension_name}] 弱项指标: {names}，建议重点提升"
                )
        return recs

    @staticmethod
    def format_report(result: ScoringResult) -> str:
        lines = [
            "=" * 60,
            f"  评分报告: {result.target_id}",
            f"  总分: {result.total_score}  等级: {result.grade}",
            "=" * 60,
        ]
        for dr in result.dimension_results:
            lines.append(f"\n▶ {dr.dimension_name} (权重{dr.weight:.0%})")
            lines.append(f"  原始分: {dr.raw_score:.2f}  加权分: {dr.weighted_score:.2f}")
            for rr in dr.rule_results:
                bar_len = int(rr.score / 5)
                bar = "█" * bar_len + "░" * (20 - bar_len)
                lines.append(f"    - {rr.rule_name}: [{bar}] {rr.score:.0f}/100")
                lines.append(f"      {rr.score_reason}")
        lines.append(f"\n{'─' * 60}")
        lines.append(f"  推荐行动:")
        for r in result.recommendations:
            lines.append(f"  • {r}")
        lines.append("=" * 60)
        return "\n".join(lines)
