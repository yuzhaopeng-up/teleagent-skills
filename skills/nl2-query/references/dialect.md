# NL2Query Dialect Adaptation Rules

Phase 2 generates SQL preview, adapting syntax differences across SQL dialects based on the `dialect` parameter.

## Dialect Comparison

| Feature | MySQL | PostgreSQL | ClickHouse |
|---------|-------|------------|------------|
| Date formatting | DATE_FORMAT(col, '%Y-%m') | TO_CHAR(col, 'YYYY-MM') | formatDateTime(col, '%Y-%m') |
| LIMIT | LIMIT n | LIMIT n | LIMIT n |
| String quotes | Single quote | Single quote | Single quote |
| Distinct count | COUNT(DISTINCT col) | COUNT(DISTINCT col) | uniqExact(col) |
| IF function | IF(cond, a, b) | CASE WHEN cond THEN a ELSE b END | if(cond, a, b) |
| Type cast | CAST(col AS type) | col::type | CAST(col AS type) |
| Year/month extract | YEAR(col), MONTH(col) | EXTRACT(YEAR FROM col) | toYear(col), toMonth(col) |

## MySQL Dialect (default)

```sql
-- Time filter
WHERE month = '2026-05'

-- Date formatting
DATE_FORMAT(month, '%Y-%m')

-- Aggregate statistics
SELECT plan_type, COUNT(*) AS ticket_count
FROM support_ticket
WHERE region = 'Region_North' AND month = '2026-05'
GROUP BY plan_type
ORDER BY ticket_count DESC
LIMIT 10
```

## PostgreSQL Dialect

```sql
-- Time filter
WHERE month = '2026-05'

-- Date formatting
TO_CHAR(month, 'YYYY-MM')

-- Aggregate statistics
SELECT plan_type, COUNT(*) AS ticket_count
FROM support_ticket
WHERE region = 'Region_North' AND month = '2026-05'
GROUP BY plan_type
ORDER BY ticket_count DESC
LIMIT 10
```

## ClickHouse Dialect

```sql
-- Time filter
WHERE month = '2026-05'

-- Date formatting
formatDateTime(month, '%Y-%m')

-- Aggregate statistics
SELECT plan_type, count() AS ticket_count
FROM support_ticket
WHERE region = 'Region_North' AND month = '2026-05'
GROUP BY plan_type
ORDER BY ticket_count DESC
LIMIT 10

-- Distinct count uses uniqExact
SELECT region, uniqExact(customer_id) AS unique_customers
FROM support_ticket
GROUP BY region
```

## Notes

- SQL preview is for display only, not directly executable (must go through data executor)
- All queries are read-only (SELECT), no DML/DDL statements generated
- Field names and table names are not quoted (for cross-dialect compatibility), unless the dialect requires it (e.g., PostgreSQL uppercase fields need double quotes)
