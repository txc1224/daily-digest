import requests
from typing import Dict, List, Optional


def fetch_stock_quote(symbol: str, display_name: str) -> Optional[dict]:
    """
    使用 Yahoo Finance API 获取股票/指数实时行情。
    完全免费，无需 API Key。
    """
    try:
        # Yahoo Finance API endpoint
        url = f"https://query1.finance.yahoo.com/v8/finance/chart/{symbol}"
        headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"
        }
        params = {
            "interval": "1d",
            "range": "1d"
        }

        r = requests.get(url, headers=headers, params=params, timeout=10)
        r.raise_for_status()
        data = r.json()

        result = data.get("chart", {}).get("result", [{}])[0]
        meta = result.get("meta", {})

        # 获取最新价格
        regular_price = meta.get("regularMarketPrice", 0)
        previous_close = meta.get("previousClose", 0) or meta.get("chartPreviousClose", 0)

        if regular_price and previous_close:
            change = regular_price - previous_close
            change_pct = (change / previous_close) * 100
        else:
            change = 0
            change_pct = 0

        return {
            "symbol": symbol,
            "name": display_name,
            "price": round(regular_price, 2),
            "change": round(change, 2),
            "change_pct": round(change_pct, 2),
            "currency": meta.get("currency", "USD"),
        }
    except Exception:
        return None


def fetch_major_indices() -> List[dict]:
    """
    获取全球主要股市指数行情。
    包括：标普500、纳斯达克、道琼斯、恒生指数、上证指数。
    """
    indices = [
        ("^GSPC", "标普500"),       # S&P 500
        ("^IXIC", "纳斯达克"),      # NASDAQ
        ("^DJI", "道琼斯"),         # Dow Jones
        ("^HSI", "恒生指数"),       # Hang Seng
        ("000001.SS", "上证指数"),  # Shanghai Composite
    ]

    results = []
    for symbol, name in indices:
        quote = fetch_stock_quote(symbol, name)
        if quote:
            results.append(quote)

    return results


def format_stock_line(stock: dict) -> str:
    """格式化单只股票为易读字符串"""
    name = stock["name"]
    price = stock["price"]
    change = stock["change"]
    change_pct = stock["change_pct"]

    emoji = "📈" if change >= 0 else "📉"
    sign = "+" if change >= 0 else ""

    return f"{emoji} **{name}**: {price} ({sign}{change}, {sign}{change_pct}%)"


def fetch_commodities() -> List[dict]:
    """
    获取大宗商品行情。
    包括：WTI原油、黄金、白银。
    """
    commodities = [
        ("CL=F", "WTI原油", "USD"),   # WTI Crude Oil
        ("GC=F", "黄金", "USD"),       # Gold
        ("SI=F", "白银", "USD"),       # Silver
    ]

    results = []
    for symbol, name, currency in commodities:
        quote = fetch_stock_quote(symbol, name)
        if quote:
            quote["currency"] = currency
            results.append(quote)

    return results
