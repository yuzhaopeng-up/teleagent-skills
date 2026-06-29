# NL2Query Domain Knowledge

## Table Whitelist

Only the following 4 tables are allowed for queries. Any table not in the whitelist should be rejected.

| Table | Display Name | Key Fields | Description |
|-------|-------------|------------|-------------|
| customer | Customer | customer_id, name, phone, region, plan_type, status | Customer profile |
| transaction | Transaction | transaction_id, customer_id, amount, plan_type, month, payment_status | Billing/payment data |
| support_ticket | Support Ticket | ticket_id, customer_id, type, region, month, plan_type, status | Support ticket records |
| incident | Incident | incident_id, region, type, month, duration_hours, status | Incident work orders |

### Field Details

**customer table**: customer_id(VARCHAR PK), name(VARCHAR), phone(VARCHAR), region(VARCHAR), plan_type(VARCHAR), status(VARCHAR)

**transaction table**: transaction_id(VARCHAR PK), customer_id(VARCHAR FK->customer), amount(DECIMAL), plan_type(VARCHAR), month(VARCHAR YYYY-MM), payment_status(VARCHAR)

**support_ticket table**: ticket_id(VARCHAR PK), customer_id(VARCHAR FK->customer), type(VARCHAR), region(VARCHAR), month(VARCHAR YYYY-MM), plan_type(VARCHAR), status(VARCHAR)

**incident table**: incident_id(VARCHAR PK), region(VARCHAR), type(VARCHAR), month(VARCHAR YYYY-MM), duration_hours(DECIMAL), status(VARCHAR)

## Entity Recognition Rules

### Time Entity

| Pattern | Normalization Rule | Example |
|---------|-------------------|---------|
| "last month" | Current month - 1, format YYYY-MM | "last month" -> `{"type":"month","value":"2026-05","relative":true}` |
| "this month" | Current month | "this month" -> `{"type":"month","value":"2026-06","relative":true}` |
| "this year" | Current year | "this year" -> `{"type":"year","value":"2026","relative":true}` |
| "month N" | Year-month N | "March" -> `{"type":"month","value":"2026-03","relative":false}` |
| "quarter N" | Year-quarter N | "Q1" -> `{"type":"quarter","value":"2026-Q1","relative":false}` |
| "last N months" | Current month minus N months | "last 3 months" -> `{"type":"range","start":"2026-04","end":"2026-06","relative":true}` |

### Region Entity

| Pattern | Normalization Rule | Example |
|---------|-------------------|---------|
| "North" | Region code | "North" -> `{"type":"region","value":"Region_North","name":"North"}` |
| "South" | Region code | "South" -> `{"type":"region","value":"Region_South","name":"South"}` |
| "East" | Region code | "East" -> `{"type":"region","value":"Region_East","name":"East"}` |
| "West" | Region code | "West" -> `{"type":"region","value":"Region_West","name":"West"}` |
| "all regions" | All-region code | "all regions" -> `{"type":"region","value":"Region_All","name":"All"}` |

### Metric Entity

| Pattern | Normalization Rule | Example |
|---------|-------------------|---------|
| "most tickets / fewest tickets" | metric + aggregation + direction | "most tickets" -> `{"metric":"ticket_count","aggregation":"count","direction":"desc"}` |
| "highest spend / lowest spend" | metric + aggregation + direction | "highest spend" -> `{"metric":"amount","aggregation":"sum","direction":"desc"}` |
| "fewest incidents" | metric + aggregation + direction | "fewest incidents" -> `{"metric":"incident_count","aggregation":"count","direction":"asc"}` |
| "average duration" | metric + aggregation | "average duration" -> `{"metric":"duration_hours","aggregation":"avg","direction":null}` |

### Dimension Entity

| Pattern | Normalization Rule | Example |
|---------|-------------------|---------|
| "by plan / by product" | dimension mapping | "by plan" -> `{"dimension":"plan_type","name":"plan"}` |
| "by region / by area" | dimension mapping | "by region" -> `{"dimension":"region","name":"region"}` |
| "by month" | dimension mapping | "by month" -> `{"dimension":"month","name":"month"}` |
| "by status" | dimension mapping | "by status" -> `{"dimension":"status","name":"status"}` |
| "by type" | dimension mapping | "by type" -> `{"dimension":"type","name":"type"}` |

### Object Entity (Filter Conditions)

| Pattern | Normalization Rule | Example |
|---------|-------------------|---------|
| "standard" | LIKE fuzzy match | "standard" -> `{"field":"plan_type","op":"LIKE","value":"%Standard%"}` |
| "premium" | LIKE fuzzy match | "premium" -> `{"field":"plan_type","op":"LIKE","value":"%Premium%"}` |
| "basic plan" | LIKE fuzzy match | "basic plan" -> `{"field":"plan_type","op":"LIKE","value":"%Basic%"}` |
| "unpaid / paid" | Exact match | "unpaid" -> `{"field":"payment_status","op":"=","value":"unpaid"}` |

## Intent Classification

| Intent | Trigger Words | Query Pattern | Output query_type |
|--------|--------------|---------------|-------------------|
| Query | "query/view/how many" | SELECT + WHERE | simple |
| Compare | "compare/rank/versus" | SELECT + GROUP BY + ORDER BY | comparison |
| Trend | "trend/change/growth" | SELECT + GROUP BY month + ORDER BY month | trend |
| Ranking | "most/highest/TOP" | SELECT + GROUP BY + ORDER BY DESC + LIMIT | ranking |
| Aggregate | "summarize/statistics/total" | SELECT + aggregate function | aggregate |

## Table-Metric-Dimension Mapping Reference

| User-mentioned Metric | Mapped Table | Mapped Field | Default Aggregation |
|----------------------|-------------|-------------|---------------------|
| ticket count / tickets | support_ticket | ticket_id | COUNT |
| spend / amount / revenue | transaction | amount | SUM |
| customer count / user count | customer | customer_id | COUNT |
| incident count / work orders | incident | incident_id | COUNT |
| duration / time taken | incident | duration_hours | AVG |
