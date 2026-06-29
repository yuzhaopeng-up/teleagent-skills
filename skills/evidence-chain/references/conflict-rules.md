# Conflict Detection Rules

## Conflict Types

| Type | Description | Example |
|------|-------------|---------|
| Value Conflict | Different sources report inconsistent numeric values for the same metric | Client claims 3 outages, system records 2 |
| Time Conflict | The same event has inconsistent timestamps across sources | Client reports issue at 09:00, system alert at 09:15 |
| Status Conflict | Different sources describe different states at the same point in time | Client reports complete outage, system shows only elevated packet loss |
| Scope Conflict | Different descriptions of the affected scope | Client says entire site is down, alerts show only a single link affected |

## Sensitivity Levels

### high
- Flag time inconsistencies ≤ 1 minute
- Flag numeric deviations ≥ 10%
- Flag any status description differences
- Use for: compliance audits, SLA dispute resolution

### medium (default)
- Flag time inconsistencies ≤ 15 minutes
- Flag numeric deviations ≥ 30%
- Flag obvious status contradictions
- Use for: routine fault diagnosis

### low
- Only flag time differences > 30 minutes or complete contradictions
- Only flag numeric deviations ≥ 50%
- Only flag completely opposite status descriptions
- Use for: quick screening

## Conflict Determination Flow

1. From Step 1's same-event evidence pairs, compare item by item per conflict type
2. Judge whether a conflict exists per `conflict_sensitivity` level
3. Conflict confirmed → generate conflict record, annotate involved sources and difference analysis
4. No conflict → treat as mutual validation, increase cross-validation score

## Difference Analysis Template

Each conflict record contains:
- **Conflict ID**: C-sequence (e.g., C-01)
- **Conflict Type**: value / time / status / scope
- **Conflict Description**: one-sentence summary of the contradiction
- **Source A**: source name + specific description
- **Source B**: source name + specific description
- **Difference Value**: quantifiable difference (e.g., "delta=1 occurrence", "time delta=15 minutes")
- **Possible Reason**: plausible explanation for the difference (e.g., "Client may have counted a device reboot as an outage")
