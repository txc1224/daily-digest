import requests
from typing import Dict, Optional


def fetch_exchange_rate(from_currency: str, to_currency: str) -> Optional[dict]:
    """
    使用 Yahoo Finance API 获取汇率。
    货币代码: CNY(人民币), USD(美元), EUR(欧元), JPY(日元)
    """
    try:
        # Yahoo Finance 汇率格式: CNYUSD=X (从CNY到USD)
        symbol = f"{from_currency}{to_currency}=X"
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

        current_rate = meta.get("regularMarketPrice", 0)
        previous_rate = meta.get("previousClose", 0) or meta.get("chartPreviousClose", 0)

        if current_rate and previous_rate:
            change = current_rate - previous_rate
            change_pct = (change / previous_rate) * 100
        else:
            change = 0
            change_pct = 0

        return {
            "from": from_currency,
            "to": to_currency,
            "rate": round(current_rate, 4),
            "change": round(change, 4),
            "change_pct": round(change_pct, 2),
        }
    except Exception:
        return None


def fetch_all_forex_rates() -> Dict[str, Optional[dict]]:
    """
    获取主要汇率: 美元兑人民币、欧元、日元
    """
    rates = {
        "USD/CNY": fetch_exchange_rate("USD", "CNY"),
        "USD/EUR": fetch_exchange_rate("USD", "EUR"),
        "USD/JPY": fetch_exchange_rate("USD", "JPY"),
    }
    return rates


def generate_forex_analysis(rates: Dict[str, Optional[dict]]) -> str:
    """
    生成汇率市场解读
    """
    if not rates or not any(rates.values()):
        return "汇率数据暂不可用"

    parts = []

    # 美元兑人民币分析
    if rates.get("USD/CNY"):
        usd_cny = rates["USD/CNY"]
        change = usd_cny.get("change_pct", 0)
        if change > 0.5:
            parts.append(f"💵 美元兑人民币走强(+{change}%)，人民币承压，利好出口企业")
        elif change < -0.5:
            parts.append(f"💵 美元兑人民币走弱({change}%)，人民币升值，利好进口")
        else:
            parts.append(f"💵 美元兑人民币汇率稳定({usd_cny.get('rate')})")

    # 美元指数综合判断
    eur_rate = rates.get("USD/EUR")
    jpy_rate = rates.get("USD/JPY")

    if eur_rate and jpy_rate:
        eur_change = eur_rate.get("change_pct", 0)
        jpy_change = jpy_rate.get("change_pct", 0)

        if eur_change > 0 and jpy_change > 0:
            parts.append("🌍 美元指数强势，美元相对欧元、日元均走强")
        elif eur_change < 0 and jpy_change < 0:
            parts.append("🌍 美元指数疲软，美元相对主要货币贬值")
        else:
            parts.append("🌍 美元走势分化，需关注各币种具体动向")

    return "｜".join(parts) if parts else "汇率市场暂无显著波动"
