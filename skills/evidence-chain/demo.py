from .engine import EvidenceChainAnalyzer, EvidenceItem

SAMPLE_EVIDENCE_A = [
    EvidenceItem(
        source_id="SYS-LOG-001",
        source_name="核心网运维日志",
        source_type="system_log",
        timestamp="2026-06-28T14:30:00",
        attributes={
            "device_id": "NE-HW-01",
            "status": "fault",
            "cpu_usage": 95.2,
            "error_count": 127,
            "link_status": "down",
        },
        reliability=1.0,
    ),
    EvidenceItem(
        source_id="ALERT-045",
        source_name="告警监控系统",
        source_type="alert",
        timestamp="2026-06-28T14:31:15",
        attributes={
            "device_id": "NE-HW-01",
            "status": "fault",
            "cpu_usage": 93.8,
            "error_count": 120,
            "link_status": "degraded",
        },
        reliability=0.85,
    ),
    EvidenceItem(
        source_id="SLA-REC-022",
        source_name="SLA监测平台",
        source_type="sla_record",
        timestamp="2026-06-28T14:28:00",
        attributes={
            "device_id": "NE-HW-01",
            "status": "normal",
            "cpu_usage": 45.0,
            "error_count": 3,
            "link_status": "up",
        },
        reliability=0.95,
    ),
    EvidenceItem(
        source_id="COMP-089",
        source_name="客户投诉记录",
        source_type="complaint",
        timestamp="2026-06-28T14:45:00",
        attributes={
            "device_id": "NE-HW-01",
            "status": "fault",
            "cpu_usage": None,
            "error_count": None,
            "link_status": "down",
        },
        reliability=0.70,
    ),
]

SAMPLE_EVIDENCE_B = [
    EvidenceItem(
        source_id="SENSOR-A01",
        source_name="机房温控传感器",
        source_type="sensor",
        timestamp="2026-06-28T14:00:00",
        attributes={
            "device_id": "NE-HW-02",
            "status": "normal",
            "temperature": 42.5,
            "humidity": 65,
        },
        reliability=0.90,
    ),
    EvidenceItem(
        source_id="SYS-LOG-012",
        source_name="边缘节点日志",
        source_type="system_log",
        timestamp="2026-06-28T14:05:00",
        attributes={
            "device_id": "NE-HW-02",
            "status": "normal",
            "temperature": 41.8,
            "humidity": 64,
        },
        reliability=1.0,
    ),
    EvidenceItem(
        source_id="ALERT-099",
        source_name="告警系统",
        source_type="alert",
        timestamp="2026-06-28T14:05:30",
        attributes={
            "device_id": "NE-HW-02",
            "status": "normal",
            "temperature": 42.3,
            "humidity": 65,
        },
        reliability=0.85,
    ),
]


def main():
    analyzer = EvidenceChainAnalyzer()
    print("=" * 60)
    print("  TeleAgent Evidence Chain Demo")
    print("=" * 60)

    print("\n--- 场景A: 核心网故障 (存在冲突) ---")
    result_a = analyzer.analyze("NE-HW-01", SAMPLE_EVIDENCE_A)
    print(EvidenceChainAnalyzer.format_report(result_a))

    print("\n--- 场景B: 边缘节点 (数据一致) ---")
    result_b = analyzer.analyze("NE-HW-02", SAMPLE_EVIDENCE_B)
    print(EvidenceChainAnalyzer.format_report(result_b))


if __name__ == "__main__":
    main()
