from dataclasses import dataclass, field
from typing import Any
import re


@dataclass
class TableSchema:
    table_name: str
    columns: list[dict]
    comment: str = ""


@dataclass
class Intent:
    intent_type: str
    description: str
    confidence: float


@dataclass
class Entity:
    entity_type: str
    value: str
    column: str | None
    alias: str | None = None


@dataclass
class NL2QueryResult:
    original_query: str
    intent: Intent
    entities: list[Entity]
    sql: str
    confidence: float
    confidence_breakdown: dict
    alternatives: list[str] = field(default_factory=list)
    warnings: list[str] = field(default_factory=list)


class NL2QueryEngine:
    INTENT_PATTERNS = {
        "aggregate": [
            (r"(多少|数量|总计|合计|总|平均|均值|最大|最小|统计|排名|top)", 0.85),
            (r"(count|sum|avg|max|min|total|average)", 0.90),
            (r"(几|几个|多少个)", 0.80),
        ],
        "trend": [
            (r"(趋势|变化|增长|下降|同比|环比|走势|波动)", 0.90),
            (r"(trend|growth|decline|yoy|mom)", 0.85),
            (r"(比上|较上|相比去年|对比去年)", 0.85),
        ],
        "comparison": [
            (r"(对比|比较|vs|versus|差异|区别|哪个多|哪个高)", 0.85),
            (r"(compare|comparison|difference|versus)", 0.90),
            (r"(各|每个|分别|不同)", 0.65),
        ],
        "detail": [
            (r"(详情|详细|具体|信息|记录|明细)", 0.85),
            (r"(detail|specific|info|record)", 0.90),
            (r"(什么|哪些|什么情况|怎么样)", 0.60),
        ],
        "distribution": [
            (r"(分布|占比|比例|百分比|构成|结构)", 0.90),
            (r"(distribution|proportion|percentage|ratio)", 0.90),
        ],
    }

    AGGREGATE_MAP = {
        "多少": "COUNT",
        "数量": "COUNT",
        "总计": "SUM",
        "合计": "SUM",
        "总": "SUM",
        "平均": "AVG",
        "均值": "AVG",
        "最大": "MAX",
        "最高": "MAX",
        "最小": "MIN",
        "最低": "MIN",
        "count": "COUNT",
        "sum": "SUM",
        "avg": "AVG",
        "max": "MAX",
        "min": "MIN",
        "top": "TOP",
        "排名": "TOP",
    }

    TIME_KEYWORDS = {
        "今年": "YEAR(CURRENT_DATE)",
        "去年": "YEAR(CURRENT_DATE) - 1",
        "本月": "MONTH(CURRENT_DATE) AND YEAR(CURRENT_DATE) = YEAR(CURRENT_DATE)",
        "上月": "MONTH(CURRENT_DATE - INTERVAL 1 MONTH)",
        "上季度": "QUARTER(CURRENT_DATE - INTERVAL 3 MONTH)",
        "近三个月": "3 MONTH",
        "近半年": "6 MONTH",
        "近一年": "12 MONTH",
    }

    def __init__(self, schema: TableSchema | None = None):
        self.schema = schema or self._default_schema()
        self._col_index = self._build_column_index()

    @staticmethod
    def _default_schema() -> TableSchema:
        return TableSchema(
            table_name="enterprise_customer",
            comment="政企客户信息表",
            columns=[
                {"name": "customer_id", "type": "VARCHAR(32)", "comment": "客户ID", "pk": True},
                {"name": "customer_name", "type": "VARCHAR(128)", "comment": "客户名称"},
                {"name": "industry", "type": "VARCHAR(64)", "comment": "行业"},
                {"name": "region", "type": "VARCHAR(32)", "comment": "区域"},
                {"name": "annual_revenue", "type": "DECIMAL(15,2)", "comment": "年营收(万元)"},
                {"name": "contract_count", "type": "INT", "comment": "合同数量"},
                {"name": "total_amount", "type": "DECIMAL(15,2)", "comment": "合同总金额(万元)"},
                {"name": "it_budget", "type": "DECIMAL(12,2)", "comment": "IT预算(万元)"},
                {"name": "cooperation_years", "type": "INT", "comment": "合作年限"},
                {"name": "status", "type": "VARCHAR(16)", "comment": "客户状态(active/churned/potential)"},
                {"name": "credit_grade", "type": "VARCHAR(4)", "comment": "信用等级(AA/A/B/C/D)"},
                {"name": "last_order_date", "type": "DATE", "comment": "最近下单日期"},
                {"name": "complaint_count", "type": "INT", "comment": "投诉次数"},
                {"name": "is_5g_customer", "type": "TINYINT", "comment": "是否5G客户(0/1)"},
            ],
        )

    def _build_column_index(self) -> dict:
        idx = {}
        for col in self.schema.columns:
            idx[col["name"].lower()] = col
            for word in col["comment"].split("(万元)")[0].split():
                idx.setdefault(word, col)
            clean_comment = re.sub(r"[()（）万元元个次年]", "", col["comment"])
            for token in clean_comment:
                if token not in idx and len(token) > 0:
                    idx.setdefault(token, col)
        return idx

    def translate(self, query: str) -> NL2QueryResult:
        intent = self._detect_intent(query)
        entities = self._extract_entities(query)
        sql = self._generate_sql(intent, entities, query)
        confidence, breakdown = self._compute_confidence(intent, entities, sql)
        alternatives = self._generate_alternatives(intent, entities, query)
        warnings = self._check_warnings(sql, entities)
        return NL2QueryResult(
            original_query=query,
            intent=intent,
            entities=entities,
            sql=sql,
            confidence=confidence,
            confidence_breakdown=breakdown,
            alternatives=alternatives,
            warnings=warnings,
        )

    def _detect_intent(self, query: str) -> Intent:
        q = query.lower().strip()
        best_type = "detail"
        best_conf = 0.30
        for intent_type, patterns in self.INTENT_PATTERNS.items():
            for pattern, base_conf in patterns:
                if re.search(pattern, q):
                    if base_conf > best_conf:
                        best_type = intent_type
                        best_conf = base_conf
        return Intent(
            intent_type=best_type,
            description=self._intent_description(best_type),
            confidence=round(best_conf, 2),
        )

    def _intent_description(self, intent_type: str) -> str:
        return {
            "aggregate": "聚合统计查询",
            "trend": "趋势变化查询",
            "comparison": "对比分析查询",
            "detail": "明细详情查询",
            "distribution": "分布占比查询",
        }.get(intent_type, "未知意图")

    def _extract_entities(self, query: str) -> list[Entity]:
        entities = []
        q = query
        for col in self.schema.columns:
            cn = col["comment"]
            name = col["name"]
            if cn and cn in q:
                entities.append(Entity("column_ref", cn, name))
            if name in q.lower():
                entities.append(Entity("column_ref", name, name))
        industry_vals = ["金融", "制造", "医疗", "教育", "零售", "政府", "能源", "交通", "互联网"]
        for iv in industry_vals:
            if iv in q:
                entities.append(Entity("value", iv, "industry"))
        region_vals = ["华东", "华南", "华北", "西南", "西北", "华中", "东北"]
        for rv in region_vals:
            if rv in q:
                entities.append(Entity("value", rv, "region"))
        status_map = {"活跃": "active", "流失": "churned", "潜在": "potential"}
        for label, val in status_map.items():
            if label in q:
                entities.append(Entity("value", val, "status", alias=label))
        grade_vals = ["AA", "A", "B", "C", "D"]
        for gv in grade_vals:
            if gv in q.upper() and gv in q.upper().split():
                entities.append(Entity("value", gv, "credit_grade"))
        for tk, expr in self.TIME_KEYWORDS.items():
            if tk in q:
                entities.append(Entity("time_range", tk, "last_order_date", alias=expr))
        num_match = re.findall(r"(\d+)(万|个|次|年|家|亿)", q)
        for val, unit in num_match:
            col_hint = {"万": "annual_revenue", "个": "contract_count",
                        "次": "complaint_count", "年": "cooperation_years",
                        "家": "customer_id", "亿": "annual_revenue"}.get(unit)
            entities.append(Entity("numeric", f"{val}{unit}", col_hint))
        top_match = re.search(r"top\s*(\d+)|前\s*(\d+)", q, re.IGNORECASE)
        if top_match:
            n = top_match.group(1) or top_match.group(2)
            entities.append(Entity("limit", n, None))
        return entities

    def _generate_sql(self, intent: Intent, entities: list[Entity], query: str) -> str:
        tbl = self.schema.table_name
        col_refs = {e.column for e in entities if e.entity_type == "column_ref" and e.column}
        val_entities = [e for e in entities if e.entity_type == "value"]
        num_entities = [e for e in entities if e.entity_type == "numeric"]
        time_entities = [e for e in entities if e.entity_type == "time_range"]
        limit_entity = next((e for e in entities if e.entity_type == "limit"), None)
        select_parts = self._build_select(intent, col_refs, entities)
        where_parts = self._build_where(val_entities, num_entities, time_entities)
        group_parts = self._build_group(intent, val_entities)
        order_parts = self._build_order(intent, entities)
        limit_part = self._build_limit(intent, limit_entity, order_parts)
        sql = f"SELECT {select_parts}\nFROM {tbl}"
        if where_parts:
            sql += f"\nWHERE {' AND '.join(where_parts)}"
        if group_parts:
            sql += f"\nGROUP BY {', '.join(group_parts)}"
        if order_parts:
            sql += f"\nORDER BY {', '.join(order_parts)}"
        if limit_part:
            sql += f"\n{limit_part}"
        return sql

    def _build_select(self, intent, col_refs, entities) -> str:
        tbl = self.schema.table_name
        if intent.intent_type == "aggregate":
            agg_col = None
            for e in entities:
                if e.entity_type == "column_ref" and e.column in (
                    "annual_revenue", "total_amount", "it_budget", "contract_count"
                ):
                    agg_col = e.column
                    break
            agg_op = "COUNT"
            for e in entities:
                if e.entity_type == "column_ref":
                    for kw, op in self.AGGREGATE_MAP.items():
                        if kw in (e.alias or ""):
                            agg_op = op
                            break
            q_orig = self._get_original(entities)
            for kw, op in self.AGGREGATE_MAP.items():
                if kw in q_orig:
                    agg_op = op
                    break
            if agg_op == "TOP":
                top_col = agg_col or "total_amount"
                return f"{top_col}, COUNT(*) AS cnt"
            if agg_op in ("COUNT",) and not agg_col:
                return "COUNT(*) AS total_count"
            if agg_col:
                return f"{agg_op}({agg_col}) AS {agg_op.lower()}_value"
            return "COUNT(*) AS total_count"
        if intent.intent_type == "distribution":
            dist_col = None
            for e in entities:
                if e.entity_type == "value" and e.column:
                    dist_col = e.column
                    break
            if not dist_col and col_refs:
                text_cols = [c for c in col_refs
                             if any(col["name"] == c and "VARCHAR" in col["type"]
                                    for col in self.schema.columns)]
                dist_col = text_cols[0] if text_cols else list(col_refs)[0]
            if dist_col:
                return f"{dist_col}, COUNT(*) AS count, ROUND(COUNT(*) * 100.0 / (SELECT COUNT(*) FROM {self.schema.table_name}), 2) AS percentage"
            return "COUNT(*) AS total_count"
        if intent.intent_type == "trend":
            time_col = "last_order_date"
            for e in entities:
                if e.entity_type == "time_range" and e.column:
                    time_col = e.column
                    break
            metric_col = "total_amount"
            for e in entities:
                if e.entity_type == "column_ref" and e.column in (
                    "annual_revenue", "total_amount", "it_budget"
                ):
                    metric_col = e.column
                    break
            return (f"DATE_FORMAT({time_col}, '%Y-%m') AS period, "
                    f"SUM({metric_col}) AS total_{metric_col}, "
                    f"COUNT(*) AS order_count")
        if intent.intent_type == "comparison":
            group_col = None
            for e in entities:
                if e.entity_type == "value" and e.column:
                    group_col = e.column
                    break
            if not group_col and col_refs:
                text_cols = [c for c in col_refs
                             if any(col["name"] == c and "VARCHAR" in col["type"]
                                    for col in self.schema.columns)]
                group_col = text_cols[0] if text_cols else None
            if group_col:
                return (f"{group_col}, "
                        f"COUNT(*) AS customer_count, "
                        f"SUM(total_amount) AS total_amount, "
                        f"AVG(annual_revenue) AS avg_revenue")
            return "*"
        return "*"

    def _get_original(self, entities) -> str:
        return getattr(self, "_current_query", "")

    def _build_where(self, val_entities, num_entities, time_entities) -> list[str]:
        parts = []
        for e in val_entities:
            if e.column:
                val = e.value if e.value.isascii() else f"'{e.value}'"
                parts.append(f"{e.column} = {val}")
        for e in num_entities:
            if e.column and e.value:
                num_match = re.match(r"(\d+)", e.value)
                if num_match:
                    n = num_match.group(1)
                    if "万" in e.value:
                        parts.append(f"{e.column} >= {n}")
                    elif "以上" in str(getattr(e, 'alias', '')):
                        parts.append(f"{e.column} >= {n}")
                    else:
                        parts.append(f"{e.column} >= {n}")
        for e in time_entities:
            if e.column:
                if "INTERVAL" in str(e.alias):
                    parts.append(f"{e.column} >= DATE_SUB(CURRENT_DATE, INTERVAL {e.alias})")
                elif "YEAR" in str(e.alias):
                    parts.append(f"YEAR({e.column}) = {e.alias}")
        return parts

    def _build_group(self, intent, val_entities) -> list[str]:
        if intent.intent_type in ("distribution", "comparison", "trend"):
            for e in val_entities:
                if e.column:
                    return [e.column]
        if intent.intent_type == "aggregate":
            for e in val_entities:
                if e.column:
                    return [e.column]
        return []

    def _build_order(self, intent, entities) -> list[str]:
        if intent.intent_type == "trend":
            return ["period ASC"]
        if intent.intent_type == "aggregate":
            for e in entities:
                if e.entity_type == "column_ref":
                    for kw in ("排名", "top", "最大", "最高"):
                        if kw in (e.alias or ""):
                            return ["total_amount DESC"]
            q = getattr(self, "_current_query", "")
            if any(kw in q for kw in ("top", "排名", "最高", "最多", "最大")):
                return ["total_amount DESC"]
        return []

    def _build_limit(self, intent, limit_entity, order_parts) -> str | None:
        if limit_entity:
            return f"LIMIT {limit_entity.value}"
        if order_parts:
            return "LIMIT 10"
        return None

    def _compute_confidence(self, intent, entities, sql) -> tuple[float, dict]:
        breakdown = {}
        intent_score = intent.confidence
        breakdown["intent_detection"] = round(intent_score, 2)
        col_match_count = sum(1 for e in entities if e.entity_type == "column_ref")
        col_total = len([c for c in self.schema.columns if c["comment"]])
        col_score = min(1.0, col_match_count / max(1, col_total) * 3) if col_match_count > 0 else 0.3
        breakdown["column_matching"] = round(col_score, 2)
        val_match_count = sum(1 for e in entities if e.entity_type in ("value", "numeric", "time_range"))
        val_score = min(1.0, val_match_count * 0.3) if val_match_count > 0 else 0.5
        breakdown["value_extraction"] = round(val_score, 2)
        sql_valid = 1.0 if "SELECT" in sql and "FROM" in sql else 0.3
        breakdown["sql_validity"] = sql_valid
        weights = {"intent_detection": 0.30, "column_matching": 0.25, "value_extraction": 0.25, "sql_validity": 0.20}
        total = sum(breakdown[k] * weights[k] for k in weights)
        total = round(min(0.99, max(0.1, total)), 2)
        return total, breakdown

    def _generate_alternatives(self, intent, entities, query) -> list[str]:
        alts = []
        val_entities = [e for e in entities if e.entity_type == "value" and e.column]
        if not val_entities and intent.intent_type == "aggregate":
            alts.append("SELECT industry, COUNT(*) AS cnt FROM enterprise_customer GROUP BY industry")
            alts.append("SELECT region, SUM(total_amount) AS total FROM enterprise_customer GROUP BY region")
        if intent.intent_type == "detail" and val_entities:
            filt_col = val_entities[0].column
            filt_val = val_entities[0].value
            v = filt_val if filt_val.isascii() else f"'{filt_val}'"
            alts.append(f"SELECT COUNT(*) FROM enterprise_customer WHERE {filt_col} = {v}")
        return alts[:3]

    def _check_warnings(self, sql, entities) -> list[str]:
        warnings = []
        if "SELECT *" in sql and not any(e.entity_type == "limit" for e in entities):
            warnings.append("查询未限制返回行数，生产环境建议加 LIMIT")
        if "DELETE" in sql.upper() or "UPDATE" in sql.upper() or "DROP" in sql.upper():
            warnings.append("检测到写操作语句，本引擎仅支持只读查询")
        if not any(e.entity_type == "time_range" for e in entities) and "last_order_date" in sql:
            warnings.append("时间字段未指定范围，可能返回大量数据")
        return warnings

    def translate_batch(self, queries: list[str]) -> list[NL2QueryResult]:
        results = []
        for q in queries:
            self._current_query = q
            results.append(self.translate(q))
        self._current_query = ""
        return results

    @staticmethod
    def format_report(result: NL2QueryResult) -> str:
        lines = [
            "=" * 60,
            f"  查询: {result.original_query}",
            f"  意图: {result.intent.description} (置信度{result.intent.confidence:.0%})",
            "=" * 60,
            f"\n  生成SQL:",
        ]
        for sql_line in result.sql.split("\n"):
            lines.append(f"    {sql_line}")
        lines.append(f"\n  总置信度: {result.confidence:.0%}")
        lines.append(f"  置信度分解:")
        for k, v in result.confidence_breakdown.items():
            lines.append(f"    {k}: {v:.0%}")
        if result.entities:
            lines.append(f"  提取实体:")
            for e in result.entities:
                lines.append(f"    [{e.entity_type}] {e.value} → {e.column or 'N/A'}")
        if result.alternatives:
            lines.append(f"  备选SQL:")
            for alt in result.alternatives:
                lines.append(f"    {alt}")
        if result.warnings:
            lines.append(f"  警告:")
            for w in result.warnings:
                lines.append(f"    ⚠ {w}")
        lines.append("=" * 60)
        return "\n".join(lines)
