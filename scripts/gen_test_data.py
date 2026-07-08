#!/usr/bin/env python3
"""
生成测试数据，用于验证前端展示页面。
生成最近90天的模拟ETF份额数据 + 净值数据。
"""

import json
import os
import datetime
import random

TARGETS = [
    "上证50", "沪深300", "中证500", "中证1000", "中证A500",
    "科创50", "科创100", "科创半导体", "科创芯片", "双创50",
    "创业板指", "深证100", "国证2000",
    "黄金", "白银",
    "创新药", "有色金属", "光伏", "半导体", "芯片",
]

# 各标的的初始份额（亿份）
INITIAL_SHARES = {
    "上证50": 180, "沪深300": 400, "中证500": 80, "中证1000": 60,
    "中证A500": 120, "科创50": 50, "科创100": 25, "科创半导体": 30,
    "科创芯片": 20, "双创50": 15, "创业板指": 100, "深证100": 40,
    "国证2000": 30, "黄金": 80, "白银": 5, "创新药": 40,
    "有色金属": 35, "光伏": 25, "半导体": 20, "芯片": 15,
}

# 各标的的初始单位净值
INITIAL_NAV = {
    "上证50": 2.85, "沪深300": 3.95, "中证500": 5.65, "中证1000": 2.42,
    "中证A500": 1.02, "科创50": 0.95, "科创100": 1.05, "科创半导体": 1.15,
    "科创芯片": 1.25, "双创50": 0.88, "创业板指": 2.15, "深证100": 3.45,
    "国证2000": 1.05, "黄金": 5.65, "白银": 0.85, "创新药": 0.92,
    "有色金属": 1.45, "光伏": 0.88, "半导体": 1.25, "芯片": 1.18,
}

DAILY_VOLATILITY = {
    "上证50": 2, "沪深300": 5, "中证500": 1.5, "中证1000": 1,
    "中证A500": 2, "科创50": 1, "科创100": 0.5, "科创半导体": 0.5,
    "科创芯片": 0.3, "双创50": 0.3, "创业板指": 2, "深证100": 0.8,
    "国证2000": 0.5, "黄金": 1.5, "白银": 0.2, "创新药": 0.8,
    "有色金属": 0.5, "光伏": 0.3, "半导体": 0.3, "芯片": 0.2,
}

# 各标的的净值日波动率（百分比）
NAV_DAILY_VOLATILITY = {
    "上证50": 0.8, "沪深300": 0.7, "中证500": 1.0, "中证1000": 1.1,
    "中证A500": 0.9, "科创50": 1.5, "科创100": 1.6, "科创半导体": 2.0,
    "科创芯片": 2.2, "双创50": 1.8, "创业板指": 1.2, "深证100": 0.9,
    "国证2000": 1.1, "黄金": 0.6, "白银": 1.4, "创新药": 1.5,
    "有色金属": 1.3, "光伏": 1.8, "半导体": 2.0, "芯片": 2.2,
}


def generate_test_data():
    filepath = os.path.join(
        os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
        "docs", "data", "etf_shares.json"
    )

    records = {}
    end_date = datetime.datetime.now()
    start_date = end_date - datetime.timedelta(days=90)

    current = start_date
    while current <= end_date:
        # 跳过周末
        if current.weekday() >= 5:
            current += datetime.timedelta(days=1)
            continue

        date_key = current.strftime("%Y-%m-%d")
        day_data = {}

        # 找最近一个有数据的日期
        prev_dates = sorted([d for d in records.keys() if d < date_key])

        for target in TARGETS:
            if not prev_dates:
                # 第一个交易日
                shares = INITIAL_SHARES[target]
                nav = INITIAL_NAV[target]
            else:
                prev_date = prev_dates[-1]
                prev_info = records[prev_date][target]
                prev_shares = prev_info["shares"]
                prev_nav = prev_info["nav"]

                # 份额随机波动
                shares_vol = DAILY_VOLATILITY[target]
                shares_change = random.gauss(0, shares_vol) + shares_vol * 0.05
                shares = round(prev_shares + shares_change, 4)

                # 净值随机波动
                nav_vol = NAV_DAILY_VOLATILITY[target] / 100
                nav_change = random.gauss(0, nav_vol) + 0.0005
                nav = round(prev_nav * (1 + nav_change), 4)

            aum = round(shares * nav, 2)  # 资产规模（亿元）
            day_data[target] = {
                "shares": shares,
                "nav": nav,
                "aum": aum,
            }

        records[date_key] = day_data
        current += datetime.timedelta(days=1)

    data = {
        "last_update": end_date.strftime("%Y-%m-%d %H:%M:%S"),
        "records": dict(sorted(records.items())),
    }

    os.makedirs(os.path.dirname(filepath), exist_ok=True)
    with open(filepath, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)

    print(f"测试数据已生成到 {filepath}")
    print(f"  日期范围: {sorted(records.keys())[0]} ~ {sorted(records.keys())[-1]}")
    print(f"  交易日数: {len(records)}")
    print(f"  标的数量: {len(TARGETS)}")


if __name__ == "__main__":
    generate_test_data()
