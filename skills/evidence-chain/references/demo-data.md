# Demo Data: 3-Source Evidence Chain Example

## Scenario

A client reports frequent service interruptions on their network service. We need to determine whether a genuine service quality issue exists.

## Input Parameters

```json
{
  "evidence_sources": [
    {
      "source_name": "Client Complaint Report",
      "source_type": "complaint_report",
      "content": "Client A (Manufacturing) (account ID MFG-0012) called on 2026-06-12 at 09:00, reporting that the network service had 3 outages in the past week. The most recent occurred around 2026-06-12 08:50, each outage lasting 5-15 minutes, severely impacting production systems. Client requests emergency handling and a written explanation. Contact: Manager Zhang, tel 139****5678."
    },
    {
      "source_name": "System Alert Log",
      "source_type": "system_alert",
      "content": "[Alert 1] 2026-06-12 09:01:23 | Device: SW-DIST-01 | Port: GE0/0/1 | Alert: link packet loss exceeds threshold | Current: 8.5% | Threshold: 5% | Duration: 12 minutes\n[Alert 2] 2026-06-12 14:30:05 | Device: SW-DIST-01 | Port: GE0/0/1 | Alert: optical module anomaly | Detail: low optical power (-18.5dBm), alert threshold -15dBm | Duration: ongoing, not recovered\n[Historical Alert] 2026-06-05 10:22:11 | Same device and port | Link packet loss 8.2% | Duration: 8 minutes"
    },
    {
      "source_name": "SLA Agreement",
      "source_type": "contract_term",
      "content": "Contract ID: SLA-2026-MFG-0045 | Client: Client A (Manufacturing) | Service: Network Service 100M | Monthly availability commitment: >=99.5% | Fault response: <=30 min | Fault resolution: <=4 hours | Penalty: for every 0.1% below committed availability, 5% monthly rent reduction | Last 3 months actual availability: March 99.1% / April 99.7% / May 99.3%"
    }
  ],
  "analysis_question": "Is there a persistent service quality issue with the network service?",
  "conflict_sensitivity": "medium",
  "confidence_threshold": 0.7
}
```

## Expected Output Summary

### Evidence List (partial)

| # | Source | Source Type | Time | Key Content | Confidence |
|---|--------|------------|------|-------------|------------|
| 1 | Client Complaint Report | complaint_report | 6/12 09:00 | 3 outages in past week, production impacted | ⭐⭐ |
| 2 | System Alert Log | system_alert | 6/5 10:22 | Link packet loss 8.2%, 8 min | ⭐⭐⭐⭐ |
| 3 | System Alert Log | system_alert | 6/12 09:01 | Link packet loss 8.5%, 12 min | ⭐⭐⭐⭐ |
| 4 | System Alert Log | system_alert | 6/12 14:30 | Optical module anomaly, low power | ⭐⭐⭐⭐ |
| 5 | SLA Agreement | contract_term | - | Monthly availability commitment 99.5% | ⭐⭐⭐ |
| 6 | SLA Agreement | contract_term | - | March actual 99.1%, May actual 99.3% | ⭐⭐⭐ |

### Conflict Detection

**C-01 Value Conflict**: Client claims 3 outages; system records only 2 significant link anomalies (6/5 and 6/12)
- Difference: delta=1 occurrence
- Possible reason: The 3rd outage may have been a client-side device issue that did not trigger network-layer alerts, or the client counted a brief slowdown as an outage

**C-02 Status Conflict**: Client describes "outage"; system records "elevated packet loss"
- Difference: Complete outage vs. partial degradation
- Possible reason: 8.5% packet loss may have limited impact on general traffic, but the client's production system may be packet-loss sensitive

### Root Cause Judgment

- **Suspected Root Cause**: Optical module anomaly on Link A (SW-DIST-01 GE0/0/1)
- **Confidence**: 0.85 (High)
- **Basis**:
  - Earliest occurrence: Packet loss anomaly appeared on 6/5, before client complaint
  - Downstream dependency: Both 6/12 alerts involve the same port
  - High frequency: Same port repeatedly shows packet loss, with consistently low optical power
- **SLA Impact**: March and May availability both below committed 99.5%, penalty clause triggered

### Recommended Actions

| Priority | Recommended Action | Linked Evidence |
|----------|-------------------|-----------------|
| 🔴 Urgent | Replace optical module on SW-DIST-01 GE0/0/1 | Evidence #4 |
| 🟡 Concurrent | Provide client with written fault analysis and SLA compensation plan | Evidence #1,#5,#6 |
| 🟡 Concurrent | Check client-side device logs for possible 3rd outage record | Evidence #1,#2,#3 |
| 🟢 Deferred | Evaluate whether client link needs redundancy backup | Evidence #5,#6 |

### Metadata

- Analysis time: 2026-06-20
- Evidence count: 6
- Conflict count: 2
- Max confidence: 0.85
