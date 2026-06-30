from dataclasses import dataclass, field
from typing import Any
from enum import Enum
import hashlib


class Consistency(Enum):
    CONSISTENT = "consistent"
    CONFLICT = "conflict"
    PARTIAL = "partial"
    MISSING = "missing"


class RootCauseConfidence(Enum):
    HIGH = "high"
    MEDIUM = "medium"
    LOW = "low"
    INCONCLUSIVE = "inconclusive"


@dataclass
class EvidenceItem:
    source_id: str
    source_name: str
    source_type: str
    timestamp: str
    attributes: dict
    reliability: float = 1.0


@dataclass
class ConflictRecord:
    attribute: str
    sources_involved: list[str]
    values: dict[str, Any]
    consistency: Consistency
    severity: float
    analysis: str


@dataclass
class RootCauseHypothesis:
    hypothesis_id: str
    description: str
    supporting_evidence: list[str]
    contradicting_evidence: list[str]
    confidence: float
    confidence_level: RootCauseConfidence
    reasoning: str


@dataclass
class ChainResult:
    target_id: str
    evidence_count: int
    conflict_count: int
    consistency_score: float
    conflicts: list[ConflictRecord]
    hypotheses: list[RootCauseHypothesis]
    primary_root_cause: RootCauseHypothesis | None
    summary: str


class EvidenceChainAnalyzer:
    def __init__(self, cross_validation_rules: dict | None = None):
        self.rules = cross_validation_rules or self._default_rules()

    @staticmethod
    def _default_rules() -> dict:
        return {
            "numeric_tolerance": 0.05,
            "timestamp_gap_threshold_minutes": 30,
            "reliability_weights": {
                "system_log": 1.0,
                "alert": 0.85,
                "sla_record": 0.95,
                "complaint": 0.70,
                "manual_report": 0.60,
                "sensor": 0.90,
            },
            "conflict_severity": {
                "status_mismatch": 0.9,
                "value_out_of_range": 0.7,
                "timestamp_anomaly": 0.5,
                "attribute_missing": 0.3,
            },
        }

    def analyze(self, target_id: str, evidence_list: list[EvidenceItem]) -> ChainResult:
        conflicts = self._cross_validate(evidence_list)
        hypotheses = self._infer_root_causes(evidence_list, conflicts)
        consistency_score = self._compute_consistency(evidence_list, conflicts)
        primary = self._select_primary(hypotheses)
        summary = self._generate_summary(
            target_id, evidence_list, conflicts, hypotheses, consistency_score
        )
        return ChainResult(
            target_id=target_id,
            evidence_count=len(evidence_list),
            conflict_count=len(conflicts),
            consistency_score=consistency_score,
            conflicts=conflicts,
            hypotheses=hypotheses,
            primary_root_cause=primary,
            summary=summary,
        )

    def _cross_validate(self, evidence_list: list[EvidenceItem]) -> list[ConflictRecord]:
        conflicts = []
        all_attrs = set()
        for ev in evidence_list:
            all_attrs.update(ev.attributes.keys())
        for attr in all_attrs:
            source_values = {}
            for ev in evidence_list:
                if attr in ev.attributes:
                    source_values[ev.source_id] = ev.attributes[attr]
            if len(source_values) < 2:
                continue
            consistency = self._check_consistency(attr, source_values)
            if consistency != Consistency.CONSISTENT:
                severity = self._assess_severity(attr, consistency)
                analysis = self._analyze_conflict(attr, source_values, consistency)
                conflicts.append(
                    ConflictRecord(
                        attribute=attr,
                        sources_involved=list(source_values.keys()),
                        values=source_values,
                        consistency=consistency,
                        severity=severity,
                        analysis=analysis,
                    )
                )
        return conflicts

    def _check_consistency(self, attr: str, source_values: dict) -> Consistency:
        values = list(source_values.values())
        if all(v is None for v in values):
            return Consistency.MISSING
        non_none = [v for v in values if v is not None]
        if len(non_none) < len(values):
            return Consistency.PARTIAL
        if all(isinstance(v, (int, float)) for v in non_none):
            tol = self.rules["numeric_tolerance"]
            max_v, min_v = max(non_none), min(non_none)
            avg = (max_v + min_v) / 2 if max_v + min_v != 0 else 1
            if abs(max_v - min_v) / abs(avg) <= tol:
                return Consistency.CONSISTENT
            return Consistency.CONFLICT
        if all(v == non_none[0] for v in non_none):
            return Consistency.CONSISTENT
        status_groups = {}
        for v in non_none:
            status_groups.setdefault(str(v), []).append(v)
        if len(status_groups) == 1:
            return Consistency.CONSISTENT
        if len(status_groups) == 2:
            return Consistency.PARTIAL
        return Consistency.CONFLICT

    def _assess_severity(self, attr: str, consistency: Consistency) -> float:
        base = self.rules["conflict_severity"].get("status_mismatch", 0.7)
        if "status" in attr.lower() or "state" in attr.lower():
            base = self.rules["conflict_severity"]["status_mismatch"]
        elif "value" in attr.lower() or "count" in attr.lower():
            base = self.rules["conflict_severity"]["value_out_of_range"]
        elif "time" in attr.lower():
            base = self.rules["conflict_severity"]["timestamp_anomaly"]
        if consistency == Consistency.PARTIAL:
            base *= 0.6
        elif consistency == Consistency.MISSING:
            base = self.rules["conflict_severity"]["attribute_missing"]
        return round(base, 2)

    def _analyze_conflict(self, attr: str, source_values: dict, consistency: Consistency) -> str:
        parts = []
        for sid, val in source_values.items():
            parts.append(f"{sid}={val}")
        val_str = ", ".join(parts)
        if consistency == Consistency.CONFLICT:
            return f"属性'{attr}'存在冲突: {val_str}，需进一步排查数据源可靠性"
        if consistency == Consistency.PARTIAL:
            return f"属性'{attr}'部分源缺失: {val_str}，可能存在数据采集不完整"
        return f"属性'{attr}'数据异常: {val_str}"

    def _infer_root_causes(
        self, evidence_list: list[EvidenceItem], conflicts: list[ConflictRecord]
    ) -> list[RootCauseHypothesis]:
        hypotheses = []
        high_conflicts = [c for c in conflicts if c.severity >= 0.7]
        if high_conflicts:
            earliest = self._find_earliest_anomaly(evidence_list, high_conflicts)
            if earliest:
                hyp = self._build_hypothesis(
                    "H1",
                    f"最早异常源: {earliest.source_name}，"
                    f"时间{earliest.timestamp}，可能为根因触发点",
                    evidence_list,
                    high_conflicts,
                    earliest,
                )
                hypotheses.append(hyp)
        status_conflicts = [c for c in conflicts if "status" in c.attribute.lower()]
        if status_conflicts:
            hyp = self._build_status_hypothesis(status_conflicts, evidence_list)
            hypotheses.append(hyp)
        if not conflicts:
            hypotheses.append(
                RootCauseHypothesis(
                    hypothesis_id="H0",
                    description="所有证据源数据一致，未检测到冲突",
                    supporting_evidence=[e.source_id for e in evidence_list],
                    contradicting_evidence=[],
                    confidence=0.95,
                    confidence_level=RootCauseConfidence.HIGH,
                    reasoning="交叉验证通过，数据一致性良好",
                )
            )
        elif not high_conflicts:
            hypotheses.append(
                RootCauseHypothesis(
                    hypothesis_id="H99",
                    description="仅存在低严重度冲突，可能为数据采集延迟或精度差异",
                    supporting_evidence=[],
                    contradicting_evidence=[],
                    confidence=0.40,
                    confidence_level=RootCauseConfidence.LOW,
                    reasoning="无高严重度冲突，根因不确定",
                )
            )
        return hypotheses

    def _find_earliest_anomaly(
        self, evidence_list: list[EvidenceItem], conflicts: list[ConflictRecord]
    ) -> EvidenceItem | None:
        involved_sources = set()
        for c in conflicts:
            involved_sources.update(c.sources_involved)
        candidates = [e for e in evidence_list if e.source_id in involved_sources]
        if not candidates:
            return None
        candidates.sort(key=lambda e: e.timestamp)
        return candidates[0]

    def _build_hypothesis(
        self, hid, desc, evidence_list, conflicts, earliest
    ) -> RootCauseHypothesis:
        supporting = [earliest.source_id]
        contradicting = []
        rw = self.rules["reliability_weights"]
        for e in evidence_list:
            if e.source_id != earliest.source_id:
                rel = rw.get(e.source_type, 0.5)
                (supporting if rel >= 0.8 else contradicting).append(e.source_id)
        avg_sev = sum(c.severity for c in conflicts) / len(conflicts)
        rel = rw.get(earliest.source_type, 0.5)
        confidence = round(min(0.95, avg_sev * rel), 2)
        if confidence >= 0.7:
            level = RootCauseConfidence.HIGH
        elif confidence >= 0.5:
            level = RootCauseConfidence.MEDIUM
        else:
            level = RootCauseConfidence.LOW
        return RootCauseHypothesis(
            hypothesis_id=hid,
            description=desc,
            supporting_evidence=supporting,
            contradicting_evidence=contradicting,
            confidence=confidence,
            confidence_level=level,
            reasoning=f"基于时序优先原则，最早异常源{earliest.source_id}最可能为根因",
        )

    def _build_status_hypothesis(self, status_conflicts, evidence_list):
        attr = status_conflicts[0].attribute
        sources = set()
        for c in status_conflicts:
            sources.update(c.sources_involved)
        rw = self.rules["reliability_weights"]
        supporting = []
        contradicting = []
        for s in sources:
            ev = next((e for e in evidence_list if e.source_id == s), None)
            if ev and rw.get(ev.source_type, 0.5) >= 0.85:
                supporting.append(s)
            elif ev:
                contradicting.append(s)
        conf = round(0.5 + 0.1 * len(supporting) - 0.05 * len(contradicting), 2)
        conf = min(0.90, max(0.2, conf))
        return RootCauseHypothesis(
            hypothesis_id="H2",
            description=f"状态属性'{attr}'源间不一致，"
            f"疑似系统状态同步故障或监控盲区",
            supporting_evidence=supporting,
            contradicting_evidence=contradicting,
            confidence=conf,
            confidence_level=RootCauseConfidence.MEDIUM
            if conf >= 0.5
            else RootCauseConfidence.LOW,
            reasoning="状态类属性冲突通常指向组件间同步问题",
        )

    def _compute_consistency(self, evidence_list, conflicts) -> float:
        n = len(evidence_list)
        if n < 2:
            return 1.0
        total_attrs = set()
        for e in evidence_list:
            total_attrs.update(e.attributes.keys())
        if not total_attrs:
            return 1.0
        conflict_attrs = len(set(c.attribute for c in conflicts))
        raw = 1.0 - (conflict_attrs / len(total_attrs))
        severity_penalty = sum(c.severity * 0.1 for c in conflicts)
        return round(max(0.0, min(1.0, raw - severity_penalty)), 3)

    def _select_primary(self, hypotheses) -> RootCauseHypothesis | None:
        if not hypotheses:
            return None
        return max(hypotheses, key=lambda h: h.confidence)

    def _generate_summary(self, target_id, evidence_list, conflicts, hypotheses, consistency) -> str:
        lines = [f"目标 {target_id} 证据链分析:"]
        lines.append(f"  证据源: {len(evidence_list)}个, 冲突: {len(conflicts)}个")
        lines.append(f"  一致性评分: {consistency:.1%}")
        if conflicts:
            high = [c for c in conflicts if c.severity >= 0.7]
            lines.append(f"  高严重度冲突: {len(high)}个")
        if hypotheses:
            best = max(hypotheses, key=lambda h: h.confidence)
            lines.append(f"  首要根因: {best.description}")
            lines.append(f"  置信度: {best.confidence:.0%} ({best.confidence_level.value})")
        return "\n".join(lines)

    @staticmethod
    def format_report(result: ChainResult) -> str:
        lines = [
            "=" * 60,
            f"  证据链分析报告: {result.target_id}",
            f"  一致性评分: {result.consistency_score:.1%}",
            "=" * 60,
            f"\n  证据源: {result.evidence_count}  冲突: {result.conflict_count}",
        ]
        if result.conflicts:
            lines.append(f"\n  ▶ 冲突详情:")
            for c in result.conflicts:
                lines.append(f"    [{c.consistency.value}] {c.attribute}")
                lines.append(f"      严重度: {c.severity}  涉及: {', '.join(c.sources_involved)}")
                for sid, val in c.values.items():
                    lines.append(f"        {sid} → {val}")
                lines.append(f"      分析: {c.analysis}")
        lines.append(f"\n  ▶ 根因假设:")
        for h in result.hypotheses:
            marker = "★" if h == result.primary_root_cause else " "
            lines.append(
                f"  {marker} {h.hypothesis_id}: {h.description}"
            )
            lines.append(f"      置信度: {h.confidence:.0%} ({h.confidence_level.value})")
            lines.append(f"      支持: {h.supporting_evidence}")
            if h.contradicting_evidence:
                lines.append(f"      矛盾: {h.contradicting_evidence}")
            lines.append(f"      推理: {h.reasoning}")
        lines.append(f"\n{'─' * 60}")
        lines.append(f"  {result.summary}")
        lines.append("=" * 60)
        return "\n".join(lines)
