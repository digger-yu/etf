#!/usr/bin/env python3
"""
ETF 份额历史数据回填脚本
从上海证券交易所和深圳证券交易所获取历史 ETF 份额数据，
按标的汇总，建立初始数据文件。
"""

import json
import os
import sys
import datetime
import time
import traceback

import akshare as ak
import pandas as pd

# 导入 fetch_data 的核心逻辑
import importlib.util
spec = importlib.util.spec_from_file_location(
    "fetch_data",
    os.path.join(os.path.dirname(os.path.abspath(__file__)), "fetch_data.py")
)
fetch_data_mod = importlib.util.module_from_spec(spec)
spec.loader.exec_module(fetch_data_mod)

match_target = fetch_data_mod.match_target
aggregate_by_target = fetch_data_mod.aggregate_by_target
shares_to_yi = fetch_data_mod.shares_to_yi
fetch_sse_data = fetch_data_mod.fetch_sse_data
fetch_szse_data = fetch_data_mod.fetch_szse_data
load_data = fetch_data_mod.load_data
save_data = fetch_data_mod.save_data
fetch_target_nav = fetch_data_mod.fetch_target_nav
TARGET_KEYWORDS = fetch_data_mod.TARGET_KEYWORDS
EXCLUDE_KEYWORDS = fetch_data_mod.EXCLUDE_KEYWORDS


def backfill_szse(start_date: str, end_date: str) -> dict[str, dict[str, float]]:
    """
    回填深交所历史数据。
    start_date/end_date: YYYYMMDD 格式
    深交所API限制每次查询不超过6个月，需要分段查询。
    返回: {date_key(YYYY-MM-DD): {target: shares_yi}}
    """
    result = {}

    start = datetime.datetime.strptime(start_date, "%Y%m%d")
    end = datetime.datetime.strptime(end_date, "%Y%m%d")

    chunk_start = start
    while chunk_start <= end:
        chunk_end = min(chunk_start + datetime.timedelta(days=180), end)
        chunk_start_str = chunk_start.strftime("%Y%m%d")
        chunk_end_str = chunk_end.strftime("%Y%m%d")

        print(f"正在回填深交所数据: {chunk_start_str} ~ {chunk_end_str}")

        try:
            df = ak.fund_scale_daily_szse(
                start_date=chunk_start_str,
                end_date=chunk_end_str,
                symbol="ETF"
            )
            if df is not None and len(df) > 0:
                for date_val, group in df.groupby("日期"):
                    date_key = pd.Timestamp(date_val).strftime("%Y-%m-%d")
                    aggregated = aggregate_by_target(group)
                    yi_data = {t: shares_to_yi(s) for t, s in aggregated.items()}
                    if yi_data:
                        result[date_key] = yi_data
                print(f"  获取到 {len(df)} 条数据，覆盖 {len(result)} 个日期")
            else:
                print("  未获取到数据")
        except Exception as e:
            print(f"  回填失败: {e}")

        chunk_start = chunk_end + datetime.timedelta(days=1)
        time.sleep(1)

    return result


def backfill_sse(start_date: str, end_date: str) -> dict[str, dict[str, float]]:
    """
    回填上交所历史数据。
    上交所API只支持单日查询，需要逐日循环。
    start_date/end_date: YYYYMMDD 格式
    返回: {date_key(YYYY-MM-DD): {target: shares_yi}}
    """
    result = {}

    start = datetime.datetime.strptime(start_date, "%Y%m%d")
    end = datetime.datetime.strptime(end_date, "%Y%m%d")

    current = start
    total_days = (end - start).days + 1
    processed = 0

    while current <= end:
        processed += 1
        # 跳过周末
        if current.weekday() >= 5:
            current += datetime.timedelta(days=1)
            continue

        date_api = current.strftime("%Y%m%d")
        date_key = current.strftime("%Y-%m-%d")

        if processed % 10 == 0:
            print(f"  [{processed}/{total_days}] 正在回填上交所数据: {date_api}")

        try:
            df = fetch_sse_data(date_api)
            if len(df) > 0:
                aggregated = aggregate_by_target(df)
                yi_data = {t: shares_to_yi(s) for t, s in aggregated.items()}
                if yi_data:
                    result[date_key] = yi_data
        except Exception as e:
            pass

        current += datetime.timedelta(days=1)
        time.sleep(0.3)

    return result


def backfill_all(start_date: str, end_date: str, filepath: str = None):
    """
    回填所有历史数据，合并深交所和上交所。
    """
    if filepath is None:
        filepath = os.path.join(
            os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
            "docs", "data", "etf_shares.json"
        )

    print(f"开始回填历史数据: {start_date} ~ {end_date}")
    print("=" * 50)

    # 先回填深交所
    print("\n[1/2] 回填深交所数据...")
    szse_data = backfill_szse(start_date, end_date)
    print(f"深交所回填完成，获取 {len(szse_data)} 个日期的数据")

    # 再回填上交所
    print("\n[2/2] 回填上交所数据...")
    sse_data = backfill_sse(start_date, end_date)
    print(f"上交所回填完成，获取 {len(sse_data)} 个日期的数据")

    # 合并数据
    print("\n合并数据...")
    data = load_data(filepath)

    # 深交所数据先写入
    for date_key, target_data in szse_data.items():
        if date_key not in data["records"]:
            data["records"][date_key] = {}
        for target, shares in target_data.items():
            if target not in data["records"][date_key]:
                data["records"][date_key][target] = {"shares": shares, "nav": None, "aum": None}

    # 上交所数据写入
    for date_key, target_data in sse_data.items():
        if date_key not in data["records"]:
            data["records"][date_key] = {}
        for target, shares in target_data.items():
            if target in data["records"][date_key]:
                # 同一标的已有数据，求和
                existing_shares = data["records"][date_key][target].get("shares", 0)
                data["records"][date_key][target]["shares"] = existing_shares + shares
            else:
                data["records"][date_key][target] = {"shares": shares, "nav": None, "aum": None}

    # 收集所有标的
    all_targets = set()
    for date_data in data["records"].values():
        all_targets.update(date_data.keys())

    # 回填每个标的的净值（从最近一天开始，向前填充）
    # 注：akshare 的 fund_etf_fund_info_em 只能获取最新净值，无法获取历史净值
    # 所以这里用最新净值回填所有历史日期（注意：这会有偏差，但仍是合理估算）
    print(f"\n回填 {len(all_targets)} 个标的的单位净值...")
    target_navs = {}
    for target in sorted(all_targets):
        nav = fetch_target_nav(target)
        if nav is not None:
            target_navs[target] = round(nav, 4)
            print(f"  {target}: {round(nav, 4)}")

    for date_key, date_data in data["records"].items():
        for target, rec in date_data.items():
            if target in target_navs and rec.get("nav") is None:
                rec["nav"] = target_navs[target]
                if rec.get("shares") is not None:
                    rec["aum"] = round(rec["shares"] * target_navs[target], 2)

    # 按日期排序
    sorted_records = dict(sorted(data["records"].items()))
    data["records"] = sorted_records
    data["last_update"] = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")

    total_dates = len(data["records"])

    print(f"\n回填完成！")
    print(f"  总日期数: {total_dates}")
    print(f"  覆盖标的: {sorted(all_targets)}")

    save_data(filepath, data)
    print(f"数据已保存到 {filepath}")


if __name__ == "__main__":
    if len(sys.argv) >= 3:
        start = sys.argv[1]
        end = sys.argv[2]
    elif len(sys.argv) == 2:
        start = sys.argv[1]
        end = datetime.datetime.now().strftime("%Y%m%d")
    else:
        end = datetime.datetime.now().strftime("%Y%m%d")
        start_dt = datetime.datetime.now() - datetime.timedelta(days=90)
        start = start_dt.strftime("%Y%m%d")
        print(f"未指定日期范围，默认回填最近3个月: {start} ~ {end}")

    backfill_all(start, end)
