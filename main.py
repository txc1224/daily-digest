import sys
from fetchers.weather import fetch_weather
from fetchers.news import fetch_all_news
from fetchers.finance import fetch_finance
from fetchers.stocks import fetch_major_indices, fetch_commodities
from fetchers.forex import fetch_all_forex_rates, generate_forex_analysis
from fetchers.bonds import fetch_bonds_and_vix, generate_bond_vix_analysis
from fetchers.github_trending import fetch_github_trending
from fetchers.product_hunt import fetch_product_hunt_trending, fetch_product_hunt_fallback
from ai.summarizer import batch_summarize_efficient
from ai.clustering import cluster_news, generate_hot_topics_summary
from ai.sentiment import analyze_finance_sentiment, analyze_news_sentiment
from ai.translator import translate_news_batch
from formatter import build_card
from sender import send_to_feishu


def main() -> None:
    # ============ 基础数据 ============
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

    # ============ 扩展金融数据 ============
    print("📡 正在获取汇率...")
    try:
        forex_rates = fetch_all_forex_rates()
        valid_rates = {k: v for k, v in forex_rates.items() if v}
        print(f"  ✅ 汇率: {len(valid_rates)} 组")
        for pair, rate in valid_rates.items():
            if rate:
                change_emoji = "📈" if rate.get('change', 0) >= 0 else "📉"
                print(f"    {change_emoji} {pair}: {rate['rate']}")
    except Exception as e:
        print(f"  ⚠️  汇率获取失败: {e}", file=sys.stderr)
        forex_rates = {}

    print("📡 正在获取国债收益率与VIX...")
    try:
        bonds_vix = fetch_bonds_and_vix()
        valid_bonds = {k: v for k, v in bonds_vix.items() if v}
        print(f"  ✅ 债券/VIX: {len(valid_bonds)} 项")
    except Exception as e:
        print(f"  ⚠️  债券/VIX获取失败: {e}", file=sys.stderr)
        bonds_vix = {}

    # 生成金融数据解读
    forex_analysis = generate_forex_analysis(forex_rates)
    bond_vix_analysis = generate_bond_vix_analysis(bonds_vix)

    # ============ 新闻数据 ============
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

    # ============ 开发者与产品新闻 ============
    print("📡 正在获取 GitHub Trending...")
    try:
        github_trending = fetch_github_trending(limit=10)
        print(f"  ✅ GitHub: {len(github_trending)} 条")
    except Exception as e:
        print(f"  ⚠️  GitHub获取失败: {e}", file=sys.stderr)
        github_trending = []

    print("📡 正在获取 Product Hunt...")
    try:
        product_hunt = fetch_product_hunt_trending(limit=10)
        if not product_hunt:
            # 尝试备用方案
            product_hunt = fetch_product_hunt_fallback(limit=10)
        print(f"  ✅ Product Hunt: {len(product_hunt)} 条")
    except Exception as e:
        print(f"  ⚠️  Product Hunt获取失败: {e}", file=sys.stderr)
        product_hunt = []

    # ============ AI 增强功能 ============
    # 1. 翻译英文新闻标题
    print("🤖 正在翻译新闻标题...")
    try:
        # 翻译时事和科技新闻（如果是英文）
        if "时事" in all_news and all_news["时事"]:
            all_news["时事"] = translate_news_batch(all_news["时事"], max_items=10)
            print(f"  ✅ 时事新闻翻译完成")

        if "科技/AI" in all_news and all_news["科技/AI"]:
            all_news["科技/AI"] = translate_news_batch(all_news["科技/AI"], max_items=10)
            print(f"  ✅ 科技新闻翻译完成")

        # 翻译开发者新闻
        if "开发者" in all_news and all_news["开发者"]:
            all_news["开发者"] = translate_news_batch(all_news["开发者"], max_items=10)
            print(f"  ✅ 开发者新闻翻译完成")

        # 翻译财经新闻
        if finance_news:
            finance_news = translate_news_batch(finance_news, max_items=5)
            print(f"  ✅ 财经新闻翻译完成")
    except Exception as e:
        print(f"  ⚠️  新闻翻译失败: {e}", file=sys.stderr)

    # 2. 新闻摘要
    print("🤖 正在生成新闻摘要...")
    try:
        # 为时事和科技新闻生成摘要
        if "时事" in all_news and all_news["时事"]:
            all_news["时事"] = batch_summarize_efficient(all_news["时事"], max_items=10)
            print(f"  ✅ 时事新闻摘要生成完成")

        if "科技/AI" in all_news and all_news["科技/AI"]:
            all_news["科技/AI"] = batch_summarize_efficient(all_news["科技/AI"], max_items=10)
            print(f"  ✅ 科技新闻摘要生成完成")

        # 为财经新闻生成摘要
        if finance_news:
            finance_news = batch_summarize_efficient(finance_news, max_items=10)
            print(f"  ✅ 财经新闻摘要生成完成")
    except Exception as e:
        print(f"  ⚠️  新闻摘要生成失败: {e}", file=sys.stderr)

    # 2. 热点聚类
    print("🤖 正在进行热点聚类...")
    hot_topics = []
    try:
        # 合并所有新闻进行聚类
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
            print(f"  ℹ️  暂无热点话题")
    except Exception as e:
        print(f"  ⚠️  热点聚类失败: {e}", file=sys.stderr)

    # 3. 情感分析
    print("🤖 正在进行情感分析...")
    sentiment_result = None
    try:
        # 分析财经新闻情感
        sentiment_result = analyze_finance_sentiment(finance_news)
        print(f"  ✅ 情感分析: {sentiment_result['summary']}")
    except Exception as e:
        print(f"  ⚠️  情感分析失败: {e}", file=sys.stderr)

    # ============ 推送 ============
    print("📨 正在推送到飞书...")
    card = build_card(
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
        sentiment_result=sentiment_result
    )
    send_to_feishu(card)
    print("推送成功 ✅")


if __name__ == "__main__":
    main()
