import requests
from typing import Dict, Optional


def fetch_treasury_yield(symbol: str, name: str) -> Optional[dict]:
    """
    使用 Yahoo Finance API 获取国债收益率。
    美债代码: ^TNX (10年期), ^FVX (5年期), ^IRX (13周)
    """
    try:
        url = f"https://query1.finance.yahoo.com/v8/finance/chart/{symbol}"
        headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"
        }
        params = {"interval": "1d", "range": "1d"}

        r = requests.get(url, headers=headers, params=params, timeout=10)
        r.raise_for_status()
        data = r.json()

        result = data.get("chart", {}).get("result", [{}])[0]
        meta = result.get("meta", {})

        # 收益率需要乘以100，Yahoo返回的是小数形式
        current_yield = meta.get("regularMarketPrice", 0)
        previous_yield = meta.get("previousClose", 0) or meta.get("chartPreviousClose", 0)

        if current_yield:
            current_yield = current_yield
        if previous_yield:
            previous_yield = previous_yield

        change = current_yield - previous_yield if current_yield and previous_yield else 0
        change_pct = (change / previous_yield * 100) if previous_yield else 0

        return {
            "name": name,
            "symbol": symbol,
            "yield": round(current_yield, 2),
            "change": round(change, 2),
            "change_pct": round(change_pct, 2),
        }
    except Exception:
        return None


def fetch_vix() -> Optional[dict]:
    """
    获取 VIX 恐慌指数 (市场波动率指数)
    """
    try:
        url = "https://query1.finance.yahoo.com/v8/finance/chart/^VIX"
        headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"
        }
        params = {"interval": "1d", "range": "1d"}

        r = requests.get(url, headers=headers, params=params, timeout=10)
        r.raise_for_status()
        data = r.json()

        result = data.get("chart", {}).get("result", [{}])[0]
        meta = result.get("meta", {})

        current_vix = meta.get("regularMarketPrice", 0)
        previous_vix = meta.get("previousClose", 0) or meta.get("chartPreviousClose", 0)

        change = current_vix - previous_vix if current_vix and previous_vix else 0
        change_pct = (change / previous_vix * 100) if previous_vix else 0

        return {
            "name": "VIX恐慌指数",
            "value": round(current_vix, 2),
            "change": round(change, 2),
            "change_pct": round(change_pct, 2),
        }
    except Exception:
        return None


def fetch_bonds_and_vix() -> Dict[str, Optional[dict]]:
    """
    获取国债收益率和VIX恐慌指数
    """
    return {
        "treasury_10y": fetch_treasury_yield("^TNX", "美债10年期"),
        "vix": fetch_vix(),
    }


def generate_bond_vix_analysis(data: Dict[str, Optional[dict]]) -> str:
    """
    生成债券市场和VIX解读
    """
    parts = []

    # 美债10年期分析
    treasury = data.get("treasury_10y")
    if treasury and treasury.get("yield"):
        yield_val = treasury["yield"]
        change = treasury.get("change", 0)

        if yield_val > 4.5:
            level_desc = "高位"
        elif yield_val > 3.5:
            level_desc = "中高"
        elif yield_val > 2.5:
            level_desc = "中等"
        else:
            level_desc = "低位"

        if abs(change) > 0.1:
            direction = "上升" if change > 0 else "下降"
            parts.append(f"📊 美债10年期收益率{direction}至{level_desc}水平({yield_val}%)，{'压制成长股估值' if change > 0 else '利好科技股'}")
        else:
            parts.append(f"📊 美债10年期收益率维持在{level_desc}水平({yield_val}%)")

    # VIX分析
    vix = data.get("vix")
    if vix and vix.get("value"):
        vix_val = vix["value"]
        vix_change = vix.get("change", 0)

        if vix_val > 30:
            sentiment = "极度恐慌"
            emoji = "😱"
        elif vix_val > 20:
            sentiment = "谨慎"
            emoji = "😰"
        elif vix_val > 15:
            sentiment = "中性"
            emoji = "😐"
        else:
            sentiment = "乐观"
            emoji = "😊"

        if abs(vix_change) > 10:
            change_desc = "大幅" + ("飙升" if vix_change > 0 else "回落")
            parts.append(f"{emoji} VIX指数{change_desc}至{vix_val}，市场{sentiment}")
        else:
            parts.append(f"{emoji} V指数{vix_val}，市场处于{sentiment}状态")

    return "｜".join(parts) if parts else "债券/VIX数据暂不可用"
