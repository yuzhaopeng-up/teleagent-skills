from dataclasses import dataclass, field
from typing import Any
import math


@dataclass
class AggregationResult:
    group_key: str | None
    metrics: dict
    yoy: dict | None = None
    mom: dict | None = None
    annotations: list[str] = field(default_factory=list)


@dataclass
class AggregatorOutput:
    source_row_count: int
    groups: list[AggregationResult]
    global_stats: dict
    anomalies: list[dict]
    summary: str


class DataAggregator:
    def __init__(self, config: dict | None = None):
        self.config = config or self._default_config()

    @staticmethod
    def _default_config() -> dict:
        return {
            "anomaly_z_threshold": 2.0,
            "yoy_alert_threshold": 0.30,
            "mom_alert_threshold": 0.20,
            "default_numeric_ops": ["sum", "mean", "min", "max", "count"],
        }

    def aggregate(
        self,
        data: list[dict],
        group_by: str | list[str] | None = None,
        metrics: dict[str, list[str]] | None = None,
        yoy_field: str | None = None,
        mom_field: str | None = None,
        time_field: str = "month",
    ) -> AggregatorOutput:
        if not data:
            return AggregatorOutput(0, [], {}, [], "空数据集")
        group_keys = self._normalize_group_by(group_by)
        if metrics is None:
            metrics = self._infer_metrics(data)
        grouped = self._group_data(data, group_keys)
        agg_results = []
        for key, rows in grouped.items():
            agg = self._compute_metrics(rows, metrics)
            annotations = []
            yoy_data = None
            mom_data = None
            if yoy_field:
                yoy_data = self._compute_yoy(rows, yoy_field, time_field)
                annotations += self._check_yoy_alerts(yoy_data)
            if mom_field:
                mom_data = self._compute_mom(rows, mom_field, time_field)
                annotations += self._check_mom_alerts(mom_data)
            agg_results.append(
                AggregationResult(
                    group_key=key,
                    metrics=agg,
                    yoy=yoy_data,
                    mom=mom_data,
                    annotations=annotations,
                )
            )
        global_stats = self._compute_global_stats(data, metrics)
        anomalies = self._detect_anomalies(data)
        summary = self._build_summary(agg_results, anomalies)
        return AggregatorOutput(
            source_row_count=len(data),
            groups=agg_results,
            global_stats=global_stats,
            anomalies=anomalies,
            summary=summary,
        )

    def _normalize_group_by(self, group_by) -> list[str]:
        if group_by is None:
            return []
        if isinstance(group_by, str):
            return [group_by]
        return list(group_by)

    def _infer_metrics(self, data: list[dict]) -> dict[str, list[str]]:
        metrics = {}
        sample = data[0]
        for k, v in sample.items():
            if isinstance(v, (int, float)):
                metrics[k] = list(self.config["default_numeric_ops"])
        return metrics

    def _group_data(self, data: list[dict], group_keys: list[str]) -> dict:
        if not group_keys:
            return {"__all__": data}
        groups: dict[tuple, list] = {}
        for row in data:
            key = tuple(row.get(k) for k in group_keys)
            groups.setdefault(key, []).append(row)
        return groups

    def _compute_metrics(self, rows: list[dict], metrics: dict[str, list[str]]) -> dict:
        result = {}
        for field_name, ops in metrics.items():
            values = [r.get(field_name) for r in rows if r.get(field_name) is not None]
            nums = []
            for v in values:
                try:
                    nums.append(float(v))
                except (TypeError, ValueError):
                    pass
            field_result = {"count": len(values), "valid_count": len(nums)}
            if nums:
                if "sum" in ops:
                    field_result["sum"] = round(sum(nums), 4)
                if "mean" in ops:
                    field_result["mean"] = round(sum(nums) / len(nums), 4)
                if "min" in ops:
                    field_result["min"] = round(min(nums), 4)
                if "max" in ops:
                    field_result["max"] = round(max(nums), 4)
                if "std" in ops:
                    mean = sum(nums) / len(nums)
                    var = sum((x - mean) ** 2 for x in nums) / len(nums)
                    field_result["std"] = round(math.sqrt(var), 4)
                if "median" in ops:
                    sorted_n = sorted(nums)
                    mid = len(sorted_n) // 2
                    if len(sorted_n) % 2 == 0:
                        field_result["median"] = round(
                            (sorted_n[mid - 1] + sorted_n[mid]) / 2, 4
                        )
                    else:
                        field_result["median"] = round(sorted_n[mid], 4)
            result[field_name] = field_result
        return result

    def _compute_yoy(self, rows: list[dict], value_field: str, time_field: str) -> dict:
        time_values: dict[str, list[float]] = {}
        for row in rows:
            t = row.get(time_field, "")
            v = row.get(value_field)
            if v is not None and t:
                try:
                    time_values.setdefault(t, []).append(float(v))
                except (TypeError, ValueError):
                    pass
        yoy = {}
        sorted_periods = sorted(time_values.keys())
        for i, period in enumerate(sorted_periods):
            current = sum(time_values[period]) / len(time_values[period])
            year_ago_idx = None
            for j in range(i):
                if self._is_yoy_pair(sorted_periods[j], period):
                    year_ago_idx = j
                    break
            entry = {"period": period, "value": round(current, 2)}
            if year_ago_idx is not None:
                prev_period = sorted_periods[year_ago_idx]
                prev = sum(time_values[prev_period]) / len(time_values[prev_period])
                entry["compare_period"] = prev_period
                entry["compare_value"] = round(prev, 2)
                if prev != 0:
                    entry["yoy_change"] = round((current - prev) / abs(prev), 4)
                else:
                    entry["yoy_change"] = None
            yoy[period] = entry
        return yoy

    def _compute_mom(self, rows: list[dict], value_field: str, time_field: str) -> dict:
        time_values: dict[str, list[float]] = {}
        for row in rows:
            t = row.get(time_field, "")
            v = row.get(value_field)
            if v is not None and t:
                try:
                    time_values.setdefault(t, []).append(float(v))
                except (TypeError, ValueError):
                    pass
        mom = {}
        sorted_periods = sorted(time_values.keys())
        for i, period in enumerate(sorted_periods):
            current = sum(time_values[period]) / len(time_values[period])
            entry = {"period": period, "value": round(current, 2)}
            if i > 0:
                prev_period = sorted_periods[i - 1]
                prev = sum(time_values[prev_period]) / len(time_values[prev_period])
                entry["compare_period"] = prev_period
                entry["compare_value"] = round(prev, 2)
                if prev != 0:
                    entry["mom_change"] = round((current - prev) / abs(prev), 4)
                else:
                    entry["mom_change"] = None
            mom[period] = entry
        return mom

    def _is_yoy_pair(self, earlier: str, later: str) -> bool:
        parts_e = earlier.replace("-", "").replace("/", "")
        parts_l = later.replace("-", "").replace("/", "")
        if len(parts_e) >= 6 and len(parts_l) >= 6:
            me, ye = parts_e[4:6], parts_e[:4]
            ml, yl = parts_l[4:6], parts_l[:4]
            try:
                return me == ml and int(yl) - int(ye) == 1
            except ValueError:
                return False
        return False

    def _check_yoy_alerts(self, yoy_data: dict) -> list[str]:
        alerts = []
        threshold = self.config["yoy_alert_threshold"]
        for period, entry in yoy_data.items():
            change = entry.get("yoy_change")
            if change is not None and abs(change) > threshold:
                direction = "增长" if change > 0 else "下降"
                alerts.append(
                    f"{period} 同比{direction}{abs(change):.1%}，"
                    f"超过{threshold:.0%}阈值"
                )
        return alerts

    def _check_mom_alerts(self, mom_data: dict) -> list[str]:
        alerts = []
        threshold = self.config["mom_alert_threshold"]
        for period, entry in mom_data.items():
            change = entry.get("mom_change")
            if change is not None and abs(change) > threshold:
                direction = "增长" if change > 0 else "下降"
                alerts.append(
                    f"{period} 环比{direction}{abs(change):.1%}，"
                    f"超过{threshold:.0%}阈值"
                )
        return alerts

    def _compute_global_stats(self, data: list[dict], metrics: dict) -> dict:
        stats = {"total_rows": len(data)}
        for field_name in metrics:
            values = []
            for row in data:
                v = row.get(field_name)
                if v is not None:
                    try:
                        values.append(float(v))
                    except (TypeError, ValueError):
                        pass
            if values:
                stats[field_name] = {
                    "total": round(sum(values), 2),
                    "avg": round(sum(values) / len(values), 2),
                    "min": round(min(values), 2),
                    "max": round(max(values), 2),
                }
        return stats

    def _detect_anomalies(self, data: list[dict]) -> list[dict]:
        anomalies = []
        numeric_cols = []
        sample = data[0]
        for k, v in sample.items():
            if isinstance(v, (int, float)):
                numeric_cols.append(k)
        for col in numeric_cols:
            values = []
            for row in data:
                v = row.get(col)
                if v is not None:
                    try:
                        values.append(float(v))
                    except (TypeError, ValueError):
                        pass
            if len(values) < 3:
                continue
            mean = sum(values) / len(values)
            var = sum((x - mean) ** 2 for x in values) / len(values)
            std = math.sqrt(var)
            if std == 0:
                continue
            z_thresh = self.config["anomaly_z_threshold"]
            for i, v in enumerate(values):
                z = abs(v - mean) / std
                if z > z_thresh:
                    anomalies.append(
                        {
                            "field": col,
                            "row_index": i,
                            "value": v,
                            "z_score": round(z, 2),
                            "direction": "high" if v > mean else "low",
                        }
                    )
        return anomalies

    def _build_summary(self, groups: list, anomalies: list) -> str:
        parts = [f"聚合{len(groups)}组数据"]
        if anomalies:
            parts.append(f"检测到{len(anomalies)}个异常点")
        all_annotations = []
        for g in groups:
            all_annotations.extend(g.annotations)
        if all_annotations:
            parts.append(f"{len(all_annotations)}条预警")
        return "，".join(parts)

    @staticmethod
    def format_report(result: AggregatorOutput) -> str:
        lines = [
            "=" * 60,
            f"  数据聚合报告 (源数据{result.source_row_count}行)",
            f"  {result.summary}",
            "=" * 60,
        ]
        for g in result.groups:
            key = g.group_key if g.group_key != "__all__" else "全部"
            lines.append(f"\n▶ 分组: {key}")
            for field_name, stats in g.metrics.items():
                parts = [f"{op}={val}" for op, val in stats.items()]
                lines.append(f"  {field_name}: {', '.join(parts)}")
            if g.yoy:
                lines.append(f"  同比分析:")
                for period, entry in g.yoy.items():
                    change = entry.get("yoy_change")
                    if change is not None:
                        arrow = "↑" if change > 0 else "↓"
                        lines.append(
                            f"    {period}: {entry['value']} vs "
                            f"{entry.get('compare_value', '?')} "
                            f"{arrow} {abs(change):.1%}"
                        )
            if g.mom:
                lines.append(f"  环比分析:")
                for period, entry in g.mom.items():
                    change = entry.get("mom_change")
                    if change is not None:
                        arrow = "↑" if change > 0 else "↓"
                        lines.append(
                            f"    {period}: {entry['value']} vs "
                            f"{entry.get('compare_value', '?')} "
                            f"{arrow} {abs(change):.1%}"
                        )
            if g.annotations:
                lines.append(f"  预警:")
                for a in g.annotations:
                    lines.append(f"    ⚠ {a}")
        if result.anomalies:
            lines.append(f"\n▶ 异常点 (Z>{2.0}):")
            for a in result.anomalies:
                lines.append(
                    f"  [{a['field']}] 行{a['row_index']} "
                    f"值={a['value']} Z={a['z_score']} ({a['direction']})"
                )
        lines.append("\n" + "=" * 60)
        return "\n".join(lines)
