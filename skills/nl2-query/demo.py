from .engine import NL2QueryEngine

TEST_QUERIES = [
    "华东区有多少政企客户？",
    "各行业的合同总金额对比",
    "金融行业年营收5000万以上的客户详情",
    "最近一年的投诉趋势",
    "客户信用等级分布",
    "TOP 10合同金额最大的客户",
    "华南区活跃客户的平均IT预算",
    "合作年限5年以上的流失客户有哪些",
]


def main():
    engine = NL2QueryEngine()
    print("=" * 60)
    print("  TeleAgent NL2Query Engine Demo")
    print(f"  表: {engine.schema.table_name} ({engine.schema.comment})")
    print("=" * 60)

    print("\n--- 表结构 ---")
    for col in engine.schema.columns:
        pk = " [PK]" if col.get("pk") else ""
        print(f"  {col['name']:20s} {col['type']:16s} {col['comment']}{pk}")

    print(f"\n--- 8条NL测试查询 ---\n")
    results = engine.translate_batch(TEST_QUERIES)
    for r in results:
        print(NL2QueryEngine.format_report(r))
        print()


if __name__ == "__main__":
    main()
