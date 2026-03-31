from dataclasses import dataclass, field
from typing import Dict, List, Optional

from ai.clustering import cluster_news
from ai.sentiment import analyze_finance_sentiment
from ai.summarizer import batch_summarize_efficient
from ai.translator import translate_news_batch
from fetchers.bonds import fetch_bonds_and_vix, generate_bond_vix_analysis
from fetchers.finance import fetch_finance
from fetchers.forex import fetch_all_forex_rates, generate_forex_analysis
from fetchers.github_trending import fetch_github_trending
from fetchers.news import fetch_all_news
from fetchers.product_hunt import fetch_product_hunt_fallback, fetch_product_hunt_trending
from fetchers.stocks import fetch_commodities, fetch_major_indices
from fetchers.weather import fetch_weather
from formatter import build_card
from sender import send_to_feishu


@dataclass
class DailyDigestData:
    weather: dict = field(default_factory=dict)
    all_news: dict = field(default_factory=dict)
    finance_news: list = field(default_factory=list)
    stocks: List[dict] = field(default_factory=list)
    commodities: List[dict] = field(default_factory=list)
    forex_rates: Dict = field(default_factory=dict)
    bonds_vix: Dict = field(default_factory=dict)
    forex_analysis: str = ""
    bond_vix_analysis: str = ""
    github_trending: List[dict] = field(default_factory=list)
    product_hunt: List[dict] = field(default_factory=list)
    hot_topics: List[dict] = field(default_factory=list)
    sentiment_result: Optional[Dict] = None


def _log_market_items(items: List[dict]) -> None:
    for item in items:
        emoji = "📈" if item["change"] >= 0 else "📉"
        print(f"  {emoji} {item['name']}: {item['price']} ({item['change_pct']}%)")


def _fetch_weather() -> dict:
    print("📡 正在获取天气...")
    try:
        weather = fetch_weather()
        print(f"  ✅ {weather['text']} {weather['temp']}°C")
        return weather
    except Exception as exc:
        print(f"  ⚠️  天气获取失败: {exc}")
        return {
            "text": "获取失败",
            "temp": "--",
            "feelsLike": "--",
            "windDir": "--",
            "windScale": "--",
            "humidity": "--",
        }


def _fetch_market_snapshot() -> tuple[List[dict], List[dict], Dict, Dict, str, str]:
    print("📡 正在获取股市行情...")
    try:
        stocks = fetch_major_indices()
        _log_market_items(stocks)
    except Exception as exc:
        print(f"  ⚠️  股市获取失败: {exc}")
        stocks = []

    print("📡 正在获取大宗商品...")
    try:
        commodities = fetch_commodities()
        _log_market_items(commodities)
    except Exception as exc:
        print(f"  ⚠️  大宗商品获取失败: {exc}")
        commodities = []

    print("📡 正在获取汇率...")
    try:
        forex_rates = fetch_all_forex_rates()
        valid_rates = {k: v for k, v in forex_rates.items() if v}
        print(f"  ✅ 汇率: {len(valid_rates)} 组")
        for pair, rate in valid_rates.items():
            emoji = "📈" if rate.get("change", 0) >= 0 else "📉"
            print(f"    {emoji} {pair}: {rate['rate']}")
    except Exception as exc:
        print(f"  ⚠️  汇率获取失败: {exc}")
        forex_rates = {}

    print("📡 正在获取国债收益率与VIX...")
    try:
        bonds_vix = fetch_bonds_and_vix()
        valid_bonds = {k: v for k, v in bonds_vix.items() if v}
        print(f"  ✅ 债券/VIX: {len(valid_bonds)} 项")
    except Exception as exc:
        print(f"  ⚠️  债券/VIX获取失败: {exc}")
        bonds_vix = {}

    forex_analysis = generate_forex_analysis(forex_rates)
    bond_vix_analysis = generate_bond_vix_analysis(bonds_vix)
    return stocks, commodities, forex_rates, bonds_vix, forex_analysis, bond_vix_analysis


def _fetch_news_snapshot() -> tuple[dict, list]:
    print("📡 正在获取新闻...")
    try:
        all_news = fetch_all_news()
        for category, items in all_news.items():
            print(f"  ✅ {category}: {len(items)} 条")
    except Exception as exc:
        print(f"  ⚠️  新闻获取失败: {exc}")
        all_news = {}

    print("📡 正在获取财经资讯...")
    try:
        finance_news = fetch_finance()
        print(f"  ✅ 财经: {len(finance_news)} 条")
    except Exception as exc:
        print(f"  ⚠️  财经获取失败: {exc}")
        finance_news = []

    return all_news, finance_news


def _fetch_developer_snapshot() -> tuple[list, list]:
    print("📡 正在获取 GitHub Trending...")
    try:
        github_trending = fetch_github_trending(limit=10)
        print(f"  ✅ GitHub: {len(github_trending)} 条")
    except Exception as exc:
        print(f"  ⚠️  GitHub获取失败: {exc}")
        github_trending = []

    print("📡 正在获取 Product Hunt...")
    try:
        product_hunt = fetch_product_hunt_trending(limit=10)
        if not product_hunt:
            product_hunt = fetch_product_hunt_fallback(limit=10)
        print(f"  ✅ Product Hunt: {len(product_hunt)} 条")
    except Exception as exc:
        print(f"  ⚠️  Product Hunt获取失败: {exc}")
        product_hunt = []

    return github_trending, product_hunt


def _enrich_news(all_news: dict, finance_news: list) -> tuple[dict, list]:
    print("🤖 正在翻译新闻标题...")
    try:
        for category in ("时事", "科技/AI", "开发者"):
            items = all_news.get(category, [])
            if items:
                all_news[category] = translate_news_batch(items, max_items=10)
                print(f"  ✅ {category}新闻翻译完成")

        if finance_news:
            finance_news = translate_news_batch(finance_news, max_items=5)
            print("  ✅ 财经新闻翻译完成")
    except Exception as exc:
        print(f"  ⚠️  新闻翻译失败: {exc}")

    print("🤖 正在生成新闻摘要...")
    try:
        for category in ("时事", "科技/AI"):
            items = all_news.get(category, [])
            if items:
                all_news[category] = batch_summarize_efficient(items, max_items=10)
                print(f"  ✅ {category}新闻摘要生成完成")

        if finance_news:
            finance_news = batch_summarize_efficient(finance_news, max_items=10)
            print("  ✅ 财经新闻摘要生成完成")
    except Exception as exc:
        print(f"  ⚠️  新闻摘要生成失败: {exc}")

    return all_news, finance_news


def _analyze_news(all_news: dict, finance_news: list) -> tuple[list, Optional[Dict]]:
    print("🤖 正在进行热点聚类...")
    hot_topics = []
    try:
        all_items = []
        for items in all_news.values():
            all_items.extend(items)
        all_items.extend(finance_news)

        hot_topics = cluster_news(all_items, min_cluster_size=2)
        if hot_topics:
            print(f"  ✅ 识别到 {len(hot_topics)} 个热点话题")
            for topic in hot_topics[:3]:
                print(f"    🔥 {topic['topic']} ({topic['count']}篇)")
        else:
            print("  ℹ️  暂无热点话题")
    except Exception as exc:
        print(f"  ⚠️  热点聚类失败: {exc}")

    print("🤖 正在进行情感分析...")
    sentiment_result = None
    try:
        sentiment_result = analyze_finance_sentiment(finance_news)
        print(f"  ✅ 情感分析: {sentiment_result['summary']}")
    except Exception as exc:
        print(f"  ⚠️  情感分析失败: {exc}")

    return hot_topics, sentiment_result


def collect_daily_digest_data() -> DailyDigestData:
    weather = _fetch_weather()
    (
        stocks,
        commodities,
        forex_rates,
        bonds_vix,
        forex_analysis,
        bond_vix_analysis,
    ) = _fetch_market_snapshot()
    all_news, finance_news = _fetch_news_snapshot()
    github_trending, product_hunt = _fetch_developer_snapshot()
    all_news, finance_news = _enrich_news(all_news, finance_news)
    hot_topics, sentiment_result = _analyze_news(all_news, finance_news)

    return DailyDigestData(
        weather=weather,
        all_news=all_news,
        finance_news=finance_news,
        stocks=stocks,
        commodities=commodities,
        forex_rates=forex_rates,
        bonds_vix=bonds_vix,
        forex_analysis=forex_analysis,
        bond_vix_analysis=bond_vix_analysis,
        github_trending=github_trending,
        product_hunt=product_hunt,
        hot_topics=hot_topics,
        sentiment_result=sentiment_result,
    )


def run_daily_digest() -> None:
    data = collect_daily_digest_data()

    print("📨 正在推送到飞书...")
    card = build_card(
        weather=data.weather,
        all_news=data.all_news,
        finance_news=data.finance_news,
        stocks=data.stocks,
        commodities=data.commodities,
        forex_rates=data.forex_rates,
        bonds_vix=data.bonds_vix,
        forex_analysis=data.forex_analysis,
        bond_vix_analysis=data.bond_vix_analysis,
        github_trending=data.github_trending,
        product_hunt=data.product_hunt,
        hot_topics=data.hot_topics,
        sentiment_result=data.sentiment_result,
    )
    send_to_feishu(card)
    print("推送成功 ✅")
