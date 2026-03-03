import sys
from fetchers.weather import fetch_weather
from fetchers.news import fetch_all_news
from fetchers.finance import fetch_finance
from fetchers.stocks import fetch_major_indices, fetch_commodities
from formatter import build_card
from sender import send_to_feishu


def main() -> None:
    print("📡 正在获取天气...")
    try:
        weather = fetch_weather()
        print(f"  ✅ {weather['text']} {weather['temp']}°C")
    except Exception as e:
        print(f"  ⚠️  天气获取失败: {e}", file=sys.stderr)
        weather = {"text": "获取失败", "temp": "--", "feelsLike": "--",
                   "windDir": "--", "windScale": "--", "humidity": "--"}

    print("📡 正在获取股市行情...")
    try:
        stocks = fetch_major_indices()
        for s in stocks:
            emoji = "📈" if s["change"] >= 0 else "📉"
            print(f"  {emoji} {s['name']}: {s['price']} ({s['change_pct']}%)")
    except Exception as e:
        print(f"  ⚠️  股市获取失败: {e}", file=sys.stderr)
        stocks = []

    print("📡 正在获取大宗商品...")
    try:
        commodities = fetch_commodities()
        for c in commodities:
            emoji = "📈" if c["change"] >= 0 else "📉"
            print(f"  {emoji} {c['name']}: {c['price']} ({c['change_pct']}%)")
    except Exception as e:
        print(f"  ⚠️  大宗商品获取失败: {e}", file=sys.stderr)
        commodities = []

    print("📡 正在获取新闻...")
    try:
        all_news = fetch_all_news()
        for cat, items in all_news.items():
            print(f"  ✅ {cat}: {len(items)} 条")
    except Exception as e:
        print(f"  ⚠️  新闻获取失败: {e}", file=sys.stderr)
        all_news = {}

    print("📡 正在获取财经资讯...")
    try:
        finance_news = fetch_finance()
        print(f"  ✅ 财经: {len(finance_news)} 条")
    except Exception as e:
        print(f"  ⚠️  财经获取失败: {e}", file=sys.stderr)
        finance_news = []

    print("📨 正在推送到飞书...")
    card = build_card(weather, all_news, finance_news, stocks, commodities)
    send_to_feishu(card)
    print("推送成功 ✅")


if __name__ == "__main__":
    main()
