"""
股票/板块分析模块 - 支持任意股票和板块
"""
import requests
from typing import Dict, List, Optional
from datetime import datetime, timedelta


def get_stock_symbol(code: str, market: str) -> str:
    """根据市场和代码获取完整的股票代码"""
    # 如果用户已经提供了完整的后缀，直接返回
    if any(suffix in code for suffix in ['.SS', '.SZ', '.HK', '.T']):
        return code

    # 根据市场添加后缀
    if market == "CN":
        if code.startswith('6'):
            return f"{code}.SS"
        else:
            return f"{code}.SZ"
    elif market == "HK":
        return f"{code.zfill(4)}.HK"

    return code  # US 市场不需要后缀


def fetch_stock_history(symbol: str, days: int = 30) -> List[Dict]:
    """获取股票历史价格数据"""
    try:
        url = f"https://query1.finance.yahoo.com/v8/finance/chart/{symbol}"
        headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"
        }
        params = {
            "interval": "1d",
            "range": f"{days}d"
        }

        r = requests.get(url, headers=headers, params=params, timeout=10)
        r.raise_for_status()
        data = r.json()

        result = data.get("chart", {}).get("result", [{}])[0]
        timestamps = result.get("timestamp", [])
        prices = result.get("indicators", {}).get("quote", [{}])[0]

        history = []
        for i, ts in enumerate(timestamps):
            if prices.get("close") and i < len(prices["close"]):
                history.append({
                    "date": datetime.fromtimestamp(ts).strftime("%Y-%m-%d"),
                    "close": round(prices["close"][i], 2),
                    "volume": prices.get("volume", [0]*len(timestamps))[i],
                })

        return history
    except Exception as e:
        print(f"获取历史数据失败: {e}")
        return []


def calculate_technical_indicators(history: List[Dict]) -> Dict:
    """计算技术指标"""
    if not history or len(history) < 20:
        return {}

    closes = [h["close"] for h in history]

    # 最新价格
    current_price = closes[-1]

    # 5日、10日、20日均线
    ma5 = sum(closes[-5:]) / 5
    ma10 = sum(closes[-10:]) / 10
    ma20 = sum(closes[-20:]) / 20

    # 计算波动率
    price_changes = [(closes[i] - closes[i-1]) / closes[i-1] for i in range(1, len(closes))]
    volatility = (sum([x**2 for x in price_changes]) / len(price_changes)) ** 0.5 * 100

    # 近期涨跌
    change_5d = (closes[-1] - closes[-6]) / closes[-6] * 100 if len(closes) >= 6 else 0
    change_20d = (closes[-1] - closes[-21]) / closes[-21] * 100 if len(closes) >= 21 else 0

    # 判断趋势
    trend = "上涨"
    if ma5 < ma10 < ma20:
        trend = "下跌"
    elif ma5 > ma10 and ma10 < ma20:
        trend = "震荡"

    return {
        "current_price": round(current_price, 2),
        "ma5": round(ma5, 2),
        "ma10": round(ma10, 2),
        "ma20": round(ma20, 2),
        "volatility": round(volatility, 2),
        "change_5d": round(change_5d, 2),
        "change_20d": round(change_20d, 2),
        "trend": trend,
        "above_ma20": current_price > ma20,
    }


def fetch_stock_fundamentals(symbol: str) -> Dict:
    """获取基本面数据"""
    try:
        url = f"https://query1.finance.yahoo.com/v10/finance/quoteSummary/{symbol}"
        headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"
        }
        params = {
            "modules": "summaryDetail,defaultKeyStatistics,financialData"
        }

        r = requests.get(url, headers=headers, params=params, timeout=10)
        data = r.json()

        result = data.get("quoteSummary", {}).get("result", [{}])[0]

        summary = result.get("summaryDetail", {})
        stats = result.get("defaultKeyStatistics", {})
        financial = result.get("financialData", {})

        return {
            "pe_ratio": summary.get("trailingPE", {}).get("raw", 0),
            "pb_ratio": summary.get("priceToBook", {}).get("raw", 0),
            "market_cap": summary.get("marketCap", {}).get("raw", 0),
            "dividend_yield": summary.get("dividendYield", {}).get("raw", 0),
            "52w_high": summary.get("fiftyTwoWeekHigh", {}).get("raw", 0),
            "52w_low": summary.get("fiftyTwoWeekLow", {}).get("raw", 0),
            "revenue_growth": financial.get("revenueGrowth", {}).get("raw", 0),
            "profit_margin": financial.get("profitMargins", {}).get("raw", 0),
        }
    except Exception as e:
        print(f"获取基本面数据失败: {e}")
        return {}


def analyze_stock(stock_code: str, market: str, report_type: str = "full") -> Dict:
    """分析单只股票 - 支持任意股票代码"""
    from fetchers.stocks import fetch_stock_quote

    symbol = get_stock_symbol(stock_code, market)

    # 获取实时报价
    quote = fetch_stock_quote(symbol, stock_code)
    if not quote:
        return {"error": f"无法获取 {stock_code} 的数据，请检查代码是否正确"}

    result = {
        "stock_code": stock_code,
        "symbol": symbol,
        "market": market,
        "quote": quote,
        "report_type": report_type,
    }

    # 技术分析
    if report_type in ["full", "technical"]:
        history = fetch_stock_history(symbol, days=30)
        if history:
            result["technical"] = calculate_technical_indicators(history)
            result["history"] = history[-5:]  # 最近5天

    # 基本面分析
    if report_type in ["full", "fundamental"]:
        result["fundamentals"] = fetch_stock_fundamentals(symbol)

    return result


def analyze_sector(sector: str, market: str, stock_codes: str = "") -> Dict:
    """分析板块 - 支持任意板块名称和自定义成分股

    Args:
        sector: 板块名称（任意字符串）
        market: 市场（US/HK/CN）
        stock_codes: 可选，逗号分隔的股票代码列表，如 "AAPL,MSFT,GOOGL"
    """
    from fetchers.stocks import fetch_stock_quote

    # 如果用户提供了成分股代码，使用用户的
    if stock_codes:
        codes = [code.strip() for code in stock_codes.split(",") if code.strip()]
    else:
        # 否则尝试从Yahoo Finance搜索该板块的热门股票
        # 这里使用一些常见股票作为示例
        codes = get_default_sector_stocks(sector, market)

    if not codes:
        return {"error": f"无法获取 {sector} 板块的成分股，请通过 stock_codes 参数手动提供，如：00700.HK,09988.HK"}

    results = []
    gainers = []
    losers = []

    for code in codes[:10]:  # 最多分析10只
        quote = fetch_stock_quote(code, code)
        if quote:
            results.append(quote)
            if quote["change_pct"] > 0:
                gainers.append(quote)
            else:
                losers.append(quote)

    if not results:
        return {"error": f"无法获取 {sector} 板块任何股票的数据，请检查股票代码是否正确"}

    # 计算板块平均涨跌幅
    avg_change = sum([r["change_pct"] for r in results]) / len(results)

    # 排序
    gainers.sort(key=lambda x: x["change_pct"], reverse=True)
    losers.sort(key=lambda x: x["change_pct"])

    return {
        "sector": sector,
        "market": market,
        "stocks": results,
        "avg_change": round(avg_change, 2),
        "top_gainers": gainers[:3],
        "top_losers": losers[:3],
    }


def get_default_sector_stocks(sector: str, market: str) -> List[str]:
    """获取默认的板块成分股 - 如果用户没提供，尝试匹配一些常见股票"""

    # 一些常见板块的默认股票
    defaults = {
        "科技": {
            "US": ["AAPL", "MSFT", "GOOGL", "NVDA", "META"],
            "HK": ["0700.HK", "3690.HK", "9988.HK", "9618.HK", "1024.HK"],
            "CN": ["002415.SZ", "000938.SZ", "600570.SS", "002230.SZ"],
        },
        "金融": {
            "US": ["JPM", "BAC", "WFC", "GS", "MS"],
            "HK": ["1299.HK", "2318.HK", "0005.HK", "1398.HK"],
            "CN": ["600036.SS", "601398.SS", "601288.SS", "601988.SS"],
        },
        "医药": {
            "US": ["JNJ", "PFE", "UNH", "ABBV", "MRK"],
            "HK": ["1093.HK", "2269.HK", "6185.HK", "2359.HK"],
            "CN": ["600276.SS", "300760.SZ", "603259.SS", "000661.SZ"],
        },
        "新能源": {
            "US": ["TSLA", "ENPH", "SEDG", "FSLR"],
            "HK": ["9866.HK", "1211.HK", "9868.HK", "2015.HK"],
            "CN": ["300750.SZ", "002594.SZ", "601012.SS", "300014.SZ"],
        },
        "消费": {
            "US": ["AMZN", "WMT", "HD", "COST", "NKE"],
            "HK": ["2319.HK", "0291.HK", "2020.HK", "1876.HK"],
            "CN": ["600519.SS", "000858.SZ", "002714.SZ", "603288.SS"],
        },
    }

    # 尝试匹配
    for key, stocks in defaults.items():
        if key in sector or sector in key:
            return stocks.get(market, [])

    # 如果都不匹配，返回空列表
    return []


def generate_analysis_summary(analysis: Dict) -> str:
    """生成分析总结"""
    if "error" in analysis:
        return analysis["error"]

    if "sector" in analysis:
        # 板块分析
        sector = analysis["sector"]
        avg_change = analysis["avg_change"]
        trend = "上涨" if avg_change > 0 else "下跌"
        emoji = "📈" if avg_change > 0 else "📉"

        summary = f"{emoji} {sector}板块整体{trend} {abs(avg_change)}%"

        if analysis.get("top_gainers"):
            top = analysis["top_gainers"][0]
            summary += f"，领涨: {top['name']} (+{top['change_pct']:.1f}%)"

        return summary

    # 个股分析
    stock_code = analysis["stock_code"]
    quote = analysis["quote"]

    emoji = "📈" if quote["change"] >= 0 else "📉"
    summary = f"{emoji} {stock_code}: {quote['price']:.2f} ({quote['change_pct']:.2f}%)"

    if "technical" in analysis:
        tech = analysis["technical"]
        summary += f"，趋势: {tech['trend']}, 5日: {tech['change_5d']:.1f}%"

    return summary
