#!/usr/bin/env python3
"""
ETF 份额数据获取脚本
从上海证券交易所和深圳证券交易所获取每日 ETF 份额数据，
按标的汇总（忽略不同基金公司），存储为 JSON 文件供前端展示。
同时获取单位净值数据，用于计算资产规模。
"""

import json
import os
import sys
import datetime
import traceback
import re

import akshare as ak
import pandas as pd


# ============================================================
# 标的映射配置：标的名称 → 匹配关键词列表
# 匹配顺序：更具体的关键词优先，避免子串冲突
# ============================================================
TARGET_KEYWORDS = [
    # 科创系列（更具体的先匹配）
    ("科创半导体", ["科创半导体"]),
    ("科创芯片", ["科创芯片"]),
    ("科创100", ["科创100"]),
    ("科创50", ["科创50"]),
    # 双创
    ("双创50", ["双创50", "双创"]),
    # A500 vs 500 冲突处理
    ("中证A500", ["中证A500", "A500"]),
    # 1000 vs 500 冲突处理
    ("中证1000", ["中证1000"]),
    ("中证500", ["中证500"]),
    ("沪深300", ["沪深300"]),
    ("上证50", ["上证50"]),
    # 创业板
    ("创业板指", ["创业板指", "创业板"]),
    # 深证100
    ("深证100", ["深证100"]),
    # 国证2000
    ("国证2000", ["国证2000"]),
    # 商品 ETF
    ("黄金", ["黄金"]),
    ("白银", ["白银"]),
    # 行业/主题 ETF
    ("创新药", ["创新药", "医药创新"]),
    ("有色金属", ["有色金属"]),
    ("光伏", ["光伏"]),
    ("半导体", ["半导体"]),  # 注意：不含"科创"的半导体ETF
    ("芯片", ["芯片"]),      # 注意：不含"科创"的芯片ETF
]

# 排除关键词：这些基金不是直接的ETF
EXCLUDE_KEYWORDS = ["联接", "LOF", "增强"]


def match_target(name: str) -> str | None:
    """
    根据ETF名称匹配所属标的。
    按优先级顺序匹配，返回第一个匹配的标的名称。
    排除联接基金等。
    """
    # 先检查排除条件
    for kw in EXCLUDE_KEYWORDS:
        if kw in name:
            return None

    # 按优先级顺序匹配
    for target, keywords in TARGET_KEYWORDS:
        for kw in keywords:
            if kw in name:
                return target
    return None


def fetch_sse_data(date_str: str) -> pd.DataFrame:
    """
    获取上海证券交易所 ETF 份额日报数据。
    date_str: YYYYMMDD 格式
    返回 DataFrame: 基金代码, 基金简称, 基金份额
    """
    try:
        df = ak.fund_etf_scale_sse(date=date_str)
        if df is not None and len(df) > 0:
            return df[["基金代码", "基金简称", "基金份额"]].copy()
    except Exception as e:
        print(f"获取上交所数据失败: {e}")
    return pd.DataFrame(columns=["基金代码", "基金简称", "基金份额"])


def fetch_szse_data(date_str: str) -> pd.DataFrame:
    """
    获取深圳证券交易所 ETF 份额日报数据。
    date_str: YYYYMMDD 格式
    返回 DataFrame: 基金代码, 基金简称, 基金份额
    """
    try:
        df = ak.fund_scale_daily_szse(
            start_date=date_str, end_date=date_str, symbol="ETF"
        )
        if df is not None and len(df) > 0:
            return df[["基金代码", "基金简称", "基金份额"]].copy()
    except Exception as e:
        print(f"获取深交所数据失败: {e}")
    return pd.DataFrame(columns=["基金代码", "基金简称", "基金份额"])


def fetch_em_spot_data() -> pd.DataFrame:
    """
    使用东方财富实时ETF数据作为备选数据源（包含最新份额和最新净值）。
    返回 DataFrame: 代码, 名称, 最新份额
    """
    try:
        df = ak.fund_etf_spot_em()
        if df is not None and len(df) > 0:
            result = df[["代码", "名称", "最新份额"]].copy()
            result.columns = ["基金代码", "基金简称", "基金份额"]
            return result
    except Exception as e:
        print(f"获取东方财富ETF数据失败: {e}")
    return pd.DataFrame(columns=["基金代码", "基金简称", "基金份额"])


def aggregate_by_target(df: pd.DataFrame) -> dict[str, float]:
    """
    将 ETF 数据按标的汇总，同一标的所有不同基金公司的ETF份额求和。
    返回 dict: {标的名称: 总份额(份)}
    """
    result = {}
    for _, row in df.iterrows():
        name = str(row["基金简称"])
        shares = row["基金份额"]

        # 跳过空值
        if pd.isna(shares) or shares == 0:
            continue

        target = match_target(name)
        if target is None:
            continue

        # 求和
        if target in result:
            result[target] += float(shares)
        else:
            result[target] = float(shares)

    return result


def get_representative_etf_code(target: str) -> str | None:
    """
    获取指定标的的代表ETF代码（用于获取净值等详细信息）。
    返回基金代码字符串。
    """
    # 常见ETF代码映射（用代表性ETF）
    target_to_code = {
        "上证50": "510050",     # 华夏上证50ETF
        "沪深300": "510300",    # 华泰柏瑞沪深300ETF
        "中证500": "510500",    # 南方中证500ETF
        "中证1000": "512100",   # 南方中证1000ETF
        "中证A500": "159353",   # 首批中证A500ETF
        "科创50": "588000",     # 华夏科创50ETF
        "科创100": "588200",    # 科创100ETF
        "科创半导体": "588210", # 科创半导体ETF
        "科创芯片": "588200",   # 备用
        "双创50": "159780",     # 首批双创50ETF
        "创业板指": "159915",   # 易方达创业板ETF
        "深证100": "159901",    # 易方达深证100ETF
        "国证2000": "159565",   # 国证2000ETF
        "黄金": "518880",       # 华安黄金ETF
        "白银": "161226",       # 国泰白银基金
        "创新药": "159992",     # 银华中证创新药产业ETF
        "有色金属": "512400",   # 南方中证申万有色金属ETF
        "光伏": "515790",       # 华泰柏瑞中证光伏产业ETF
        "半导体": "512480",     # 国联安中证全指半导体ETF
        "芯片": "159995",       # 华夏国证半导体芯片ETF
    }
    return target_to_code.get(target)


def fetch_target_nav(target: str) -> float | None:
    """
    获取指定标的代表ETF的最新单位净值。
    返回单位净值（元），失败返回 None。
    """
    code = get_representative_etf_code(target)
    if not code:
        return None
    try:
        df = ak.fund_etf_fund_info_em(fund=code)
        if df is not None and len(df) > 0 and "单位净值" in df.columns:
            return float(df["单位净值"].iloc[-1])
    except Exception as e:
        print(f"获取 {target} 净值失败: {e}")
    return None


def load_data(filepath: str) -> dict:
    """加载已有的 JSON 数据文件"""
    if os.path.exists(filepath):
        with open(filepath, "r", encoding="utf-8") as f:
            return json.load(f)
    return {"last_update": "", "records": {}}


def save_data(filepath: str, data: dict):
    """保存 JSON 数据文件"""
    os.makedirs(os.path.dirname(filepath), exist_ok=True)
    with open(filepath, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)


def shares_to_yi(shares: float) -> float:
    """将份额从份转换为亿份"""
    return round(shares / 1e8, 4)


def fetch_daily_data(date_str: str = None) -> dict:
    """
    获取指定日期的ETF份额数据，按标的汇总，并附加单位净值。
    优先使用交易所官方数据，备选东方财富实时数据。
    date_str: YYYYMMDD 格式，默认为今天
    返回 dict: {标的名称: {"shares": 份额(亿份), "nav": 单位净值, "aum": 资产规模(亿元)}}
    """
    if date_str is None:
        date_str = datetime.datetime.now().strftime("%Y%m%d")

    print(f"正在获取 {date_str} 的 ETF 份额数据...")

    # 优先从交易所官方获取
    sse_df = fetch_sse_data(date_str)
    szse_df = fetch_szse_data(date_str)

    # 合并上交所和深交所数据
    combined_df = pd.concat([sse_df, szse_df], ignore_index=True)

    if len(combined_df) == 0:
        # 如果交易所数据获取失败，尝试东方财富实时数据
        print("交易所数据获取失败，尝试使用东方财富实时数据...")
        em_df = fetch_em_spot_data()
        if len(em_df) == 0:
            print("所有数据源获取失败！")
            return {}
        combined_df = em_df

    print(f"共获取 {len(combined_df)} 条 ETF 数据")

    # 按标的汇总份额
    aggregated = aggregate_by_target(combined_df)

    # 转换为亿份并附加净值
    result = {}
    for target, shares in aggregated.items():
        shares_yi = shares_to_yi(shares)
        # 获取该标的代表ETF的单位净值
        nav = fetch_target_nav(target)
        result[target] = {
            "shares": shares_yi,
            "nav": round(nav, 4) if nav is not None else None,
            "aum": round(shares_yi * nav, 2) if nav is not None else None,  # 资产规模（亿元）
        }

    print(f"汇总后得到 {len(result)} 个标的:")
    for target, info in sorted(result.items(), key=lambda x: x[1]["shares"], reverse=True):
        nav_str = f"净值:{info['nav']:.4f}" if info['nav'] else "净值:--"
        print(f"  {target}: {info['shares']:.4f} 亿份 | {nav_str}")

    return result


def update_data_file(filepath: str = None, date_str: str = None):
    """
    获取当日数据并更新 JSON 数据文件。
    如果当日数据已存在则更新，否则追加新记录。
    """
    if filepath is None:
        filepath = os.path.join(
            os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
            "docs", "data", "etf_shares.json"
        )

    data = load_data(filepath)

    # 获取日期
    if date_str is None:
        today = datetime.datetime.now()
        date_key = today.strftime("%Y-%m-%d")
        date_api = today.strftime("%Y%m%d")
    else:
        # date_str 可能是 YYYY-MM-DD 或 YYYYMMDD
        if "-" in date_str:
            date_key = date_str
            date_api = date_str.replace("-", "")
        else:
            date_api = date_str
            date_key = f"{date_str[:4]}-{date_str[4:6]}-{date_str[6:8]}"

    # 获取数据
    daily_data = fetch_daily_data(date_api)

    if not daily_data:
        print(f"未能获取 {date_key} 的数据，不更新文件")
        return

    # 更新数据
    data["records"][date_key] = daily_data
    data["last_update"] = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")

    # 按日期排序（确保有序）
    sorted_records = dict(sorted(data["records"].items()))
    data["records"] = sorted_records

    # 保存
    save_data(filepath, data)
    print(f"数据已更新并保存到 {filepath}")


if __name__ == "__main__":
    # 从命令行参数获取日期
    date_arg = sys.argv[1] if len(sys.argv) > 1 else None
    update_data_file(date_str=date_arg)
