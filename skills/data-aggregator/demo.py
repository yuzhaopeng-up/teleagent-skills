from .engine import DataAggregator

SAMPLE_MONTHLY_DATA = [
    {"month": "202501", "region": "华东", "revenue": 2850, "complaints": 45, "users": 12000},
    {"month": "202502", "region": "华东", "revenue": 2680, "complaints": 52, "users": 12200},
    {"month": "202503", "region": "华东", "revenue": 3100, "complaints": 38, "users": 12500},
    {"month": "202504", "region": "华东", "revenue": 3250, "complaints": 41, "users": 12800},
    {"month": "202505", "region": "华东", "revenue": 3400, "complaints": 35, "users": 13200},
    {"month": "202506", "region": "华东", "revenue": 3580, "complaints": 30, "users": 13500},
    {"month": "202601", "region": "华东", "revenue": 3200, "complaints": 42, "users": 13800},
    {"month": "202602", "region": "华东", "revenue": 3050, "complaints": 48, "users": 14000},
    {"month": "202603", "region": "华东", "revenue": 3600, "complaints": 33, "users": 14200},
    {"month": "202604", "region": "华东", "revenue": 3780, "complaints": 29, "users": 14500},
    {"month": "202605", "region": "华东", "revenue": 3950, "complaints": 25, "users": 14800},
    {"month": "202606", "region": "华东", "revenue": 4100, "complaints": 22, "users": 15200},
    {"month": "202501", "region": "华南", "revenue": 2200, "complaints": 58, "users": 8500},
    {"month": "202502", "region": "华南", "revenue": 2050, "complaints": 62, "users": 8600},
    {"month": "202503", "region": "华南", "revenue": 2400, "complaints": 50, "users": 8800},
    {"month": "202504", "region": "华南", "revenue": 2500, "complaints": 48, "users": 9000},
    {"month": "202505", "region": "华南", "revenue": 2650, "complaints": 44, "users": 9200},
    {"month": "202506", "region": "华南", "revenue": 2700, "complaints": 42, "users": 9400},
    {"month": "202601", "region": "华南", "revenue": 2500, "complaints": 55, "users": 9500},
    {"month": "202602", "region": "华南", "revenue": 2350, "complaints": 60, "users": 9600},
    {"month": "202603", "region": "华南", "revenue": 2800, "complaints": 45, "users": 9800},
    {"month": "202604", "region": "华南", "revenue": 2900, "complaints": 40, "users": 10000},
    {"month": "202605", "region": "华南", "revenue": 3050, "complaints": 38, "users": 10200},
    {"month": "202606", "region": "华南", "revenue": 3200, "complaints": 35, "users": 10500},
]


def main():
    agg = DataAggregator()
    print("=" * 60)
    print("  TeleAgent Data Aggregator Demo")
    print("=" * 60)

    print("\n--- 按区域聚合 + 同比/环比 ---")
    result = agg.aggregate(
        data=SAMPLE_MONTHLY_DATA,
        group_by="region",
        metrics={
            "revenue": ["sum", "mean", "min", "max"],
            "complaints": ["sum", "mean", "min", "max"],
            "users": ["sum", "mean", "max"],
        },
        yoy_field="revenue",
        mom_field="revenue",
        time_field="month",
    )
    print(DataAggregator.format_report(result))


if __name__ == "__main__":
    main()
