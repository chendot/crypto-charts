"""
X-02a 验证脚本：DeFi锁仓稳定币 / 全链稳定币总量
目的：快速验证"稳定币增量越来越留在DeFi"这个方向是否成立
运行：python validate_stablecoin_ratio.py
"""

import requests
import json
from datetime import datetime

HEADERS = {"User-Agent": "crypto-charts-research/1.0"}

def get_total_stablecoin_mcap():
    """全链稳定币总量（当前快照）"""
    url = "https://stablecoins.llama.fi/stablecoins?includePrices=true"
    r = requests.get(url, headers=HEADERS, timeout=30)
    r.raise_for_status()
    assets = r.json()["peggedAssets"]
    total = sum(s.get("circulating", {}).get("usd", 0) for s in assets)

    # 顺手打印前10币种
    top = sorted(assets, key=lambda x: -x.get("circulating", {}).get("usd", 0))[:10]
    print("\n── 全链稳定币前10 ──")
    for s in top:
        mcap = s.get("circulating", {}).get("usd", 0)
        print(f"  {s['symbol']:<12} ${mcap/1e9:.2f}b")
    return total


def get_defi_stablecoin_tvl():
    """
    各协议的 stablecoinTvl 加总
    注意：DeFiLlama 的 stablecoinTvl 字段 = 该协议合约地址持有的稳定币市值
    覆盖范围：Lending / DEX / CDP / Yield / Bridge 等所有协议类型
    """
    url = "https://api.llama.fi/protocols"
    r = requests.get(url, headers=HEADERS, timeout=60)
    r.raise_for_status()
    protocols = r.json()

    rows = []
    for p in protocols:
        sc = p.get("stablecoinTvl") or 0
        if sc > 1e6:  # 过滤掉噪音（<$1M）
            rows.append({
                "name": p["name"],
                "category": p.get("category", ""),
                "chain": p.get("chain", ""),
                "stablecoin_tvl": sc,
            })

    rows.sort(key=lambda x: -x["stablecoin_tvl"])

    # 打印前30
    print("\n── DeFi协议稳定币TVL前30 ──")
    print(f"  {'协议':<28} {'分类':<18} {'稳定币TVL':>12}")
    print("  " + "-" * 62)
    for row in rows[:30]:
        print(f"  {row['name']:<28} {row['category']:<18} ${row['stablecoin_tvl']/1e9:>9.3f}b")

    # 按分类汇总
    from collections import defaultdict
    by_cat = defaultdict(float)
    for row in rows:
        by_cat[row["category"]] += row["stablecoin_tvl"]

    print("\n── 按协议分类汇总 ──")
    for cat, val in sorted(by_cat.items(), key=lambda x: -x[1])[:12]:
        print(f"  {cat:<25} ${val/1e9:.2f}b")

    total_defi = sum(r["stablecoin_tvl"] for r in rows)
    return total_defi, rows


def main():
    print(f"查询时间: {datetime.utcnow().strftime('%Y-%m-%d %H:%M UTC')}")

    total_mcap = get_total_stablecoin_mcap()
    defi_tvl, rows = get_defi_stablecoin_tvl()

    ratio = defi_tvl / total_mcap * 100

    print("\n" + "=" * 50)
    print(f"  全链稳定币总量:         ${total_mcap/1e9:.2f}b")
    print(f"  DeFi协议稳定币TVL:      ${defi_tvl/1e9:.2f}b")
    print(f"  DeFi锁仓占比:           {ratio:.1f}%")
    print("=" * 50)

    # 初步判断
    print("\n── 初步判断 ──")
    if ratio > 40:
        print(f"  占比 {ratio:.1f}% > 40%：DeFi内循环吸纳比例显著，方向值得深入")
    elif ratio > 25:
        print(f"  占比 {ratio:.1f}%：中等水平，需要看历史趋势才能判断方向")
    else:
        print(f"  占比 {ratio:.1f}% < 25%：DeFi锁仓比例有限，主论点可能需要调整")

    print("\n  下一步：需要拉2020-至今月度历史数据，观察比值趋势")
    print("  关键问题：2021牛市顶部 vs 现在，哪个比值更高？")

    # 保存原始数据备用
    with open("stablecoin_ratio_snapshot.json", "w") as f:
        json.dump({
            "timestamp": datetime.utcnow().isoformat(),
            "total_mcap_usd": total_mcap,
            "defi_tvl_usd": defi_tvl,
            "ratio_pct": ratio,
            "top30": rows[:30],
        }, f, indent=2)
    print("\n  原始数据已保存至 stablecoin_ratio_snapshot.json")


if __name__ == "__main__":
    main()
