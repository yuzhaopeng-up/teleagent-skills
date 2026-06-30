import os
from .engine import VisualizationRenderer

SAMPLE_REVENUE_DATA = [
    {"month": "2026-01", "region": "华东", "revenue": 3200, "complaints": 42},
    {"month": "2026-02", "region": "华东", "revenue": 3050, "complaints": 48},
    {"month": "2026-03", "region": "华东", "revenue": 3600, "complaints": 33},
    {"month": "2026-04", "region": "华东", "revenue": 3780, "complaints": 29},
    {"month": "2026-05", "region": "华东", "revenue": 3950, "complaints": 25},
    {"month": "2026-06", "region": "华东", "revenue": 4100, "complaints": 22},
]

SAMPLE_MARKET_SHARE = [
    {"product": "5G专网", "share": 35},
    {"product": "云网融合", "share": 25},
    {"product": "物联网", "share": 20},
    {"product": "安全服务", "share": 12},
    {"product": "其他", "share": 8},
]

SAMPLE_SCATTER_DATA = [
    {"customer": f"CUST-{i:03d}", "revenue": 500 + i * 120, "satisfaction": 60 + (i % 5) * 8}
    for i in range(1, 21)
]


def main():
    output_dir = os.path.join(os.path.dirname(__file__), "output")
    renderer = VisualizationRenderer(output_dir=output_dir)

    print("=" * 60)
    print("  TeleAgent Visualization Renderer Demo")
    print("=" * 60)

    print("\n--- 折线图: 月度营收趋势 (自动推荐) ---")
    r1 = renderer.render(
        SAMPLE_REVENUE_DATA,
        title="华东区月度营收与投诉趋势",
        category_field="month",
        value_fields=["revenue", "complaints"],
    )
    print(VisualizationRenderer.format_report(r1))

    print("\n--- 饼图: 市场份额 (自动推荐) ---")
    r2 = renderer.render(
        SAMPLE_MARKET_SHARE,
        title="政企产品市场份额",
        category_field="product",
        value_fields=["share"],
    )
    print(VisualizationRenderer.format_report(r2))

    print("\n--- 散点图: 客户营收与满意度 (指定) ---")
    r3 = renderer.render(
        SAMPLE_SCATTER_DATA,
        title="客户营收与满意度相关性",
        category_field="customer",
        value_fields=["revenue", "satisfaction"],
        preferred_type="scatter",
    )
    print(VisualizationRenderer.format_report(r3))

    print(f"\n3个HTML文件已生成到: {output_dir}")


if __name__ == "__main__":
    main()
