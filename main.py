import sys
import argparse
from fetchers.weather import fetch_weather
from fetchers.news import fetch_all_news
from fetchers.finance import fetch_finance
from fetchers.stocks import fetch_major_indices, fetch_commodities
from fetchers.forex import fetch_all_forex_rates, generate_forex_analysis
from fetchers.bonds import fetch_bonds_and_vix, generate_bond_vix_analysis
from fetchers.github_trending import fetch_github_trending
from fetchers.product_hunt import fetch_product_hunt_trending, fetch_product_hunt_fallback
from fetchers.stock_analyzer import analyze_stock, analyze_sector, generate_analysis_summary
from ai.summarizer import batch_summarize_efficient
from ai.clustering import cluster_news, generate_hot_topics_summary
from ai.sentiment import analyze_finance_sentiment, analyze_news_sentiment
from ai.translator import translate_news_batch
from formatter import build_card, build_stock_card, build_analysis_card
from sender import send_to_feishu


def run_daily_digest():
    """运行完整的每日简报"""
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
            product_hunt = fetch_product_hunt_fallback(limit=10)
        print(f"  ✅ Product Hunt: {len(product_hunt)} 条")
    except Exception as e:
        print(f"  ⚠️  Product Hunt获取失败: {e}", file=sys.stderr)
        product_hunt = []

    # ============ AI 增强功能 ============
    print("🤖 正在翻译新闻标题...")
    try:
        if "时事" in all_news and all_news["时事"]:
            all_news["时事"] = translate_news_batch(all_news["时事"], max_items=10)
            print(f"  ✅ 时事新闻翻译完成")

        if "科技/AI" in all_news and all_news["科技/AI"]:
            all_news["科技/AI"] = translate_news_batch(all_news["科技/AI"], max_items=10)
            print(f"  ✅ 科技新闻翻译完成")

        if "开发者" in all_news and all_news["开发者"]:
            all_news["开发者"] = translate_news_batch(all_news["开发者"], max_items=10)
            print(f"  ✅ 开发者新闻翻译完成")

        if finance_news:
            finance_news = translate_news_batch(finance_news, max_items=5)
            print(f"  ✅ 财经新闻翻译完成")
    except Exception as e:
        print(f"  ⚠️  新闻翻译失败: {e}", file=sys.stderr)

    print("🤖 正在生成新闻摘要...")
    try:
        if "时事" in all_news and all_news["时事"]:
            all_news["时事"] = batch_summarize_efficient(all_news["时事"], max_items=10)
            print(f"  ✅ 时事新闻摘要生成完成")

        if "科技/AI" in all_news and all_news["科技/AI"]:
            all_news["科技/AI"] = batch_summarize_efficient(all_news["科技/AI"], max_items=10)
            print(f"  ✅ 科技新闻摘要生成完成")

        if finance_news:
            finance_news = batch_summarize_efficient(finance_news, max_items=10)
            print(f"  ✅ 财经新闻摘要生成完成")
    except Exception as e:
        print(f"  ⚠️  新闻摘要生成失败: {e}", file=sys.stderr)

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
            print(f"  ℹ️  暂无热点话题")
    except Exception as e:
        print(f"  ⚠️  热点聚类失败: {e}", file=sys.stderr)

    print("🤖 正在进行情感分析...")
    sentiment_result = None
    try:
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


def run_stock_morning():
    """A股开盘推送：上证指数 + 隔夜美股收盘"""
    print("📈 A股开盘简报")

    # 获取上证指数
    from fetchers.stocks import fetch_stock_quote
    sh_index = fetch_stock_quote("000001.SS", "上证指数")

    # 获取隔夜美股
    sp500 = fetch_stock_quote("^GSPC", "标普500")
    nasdaq = fetch_stock_quote("^IXIC", "纳斯达克")
    dow = fetch_stock_quote("^DJI", "道琼斯")

    us_stocks = [s for s in [sp500, nasdaq, dow] if s]

    card = build_stock_card(
        title="📈 A股开盘简报",
        focus_stock=sh_index,
        us_stocks=us_stocks,
        time_desc="09:30"
    )
    send_to_feishu(card)
    print("推送成功 ✅")


def run_stock_afternoon():
    """港股收盘推送：恒生指数 + 实时美股"""
    print("📈 港股收盘简报")

    # 获取恒生指数
    from fetchers.stocks import fetch_stock_quote
    hsi = fetch_stock_quote("^HSI", "恒生指数")

    # 获取美股实时（盘中）
    sp500 = fetch_stock_quote("^GSPC", "标普500")
    nasdaq = fetch_stock_quote("^IXIC", "纳斯达克")
    dow = fetch_stock_quote("^DJI", "道琼斯")

    us_stocks = [s for s in [sp500, nasdaq, dow] if s]

    card = build_stock_card(
        title="📈 港股收盘简报",
        focus_stock=hsi,
        us_stocks=us_stocks,
        time_desc="16:00"
    )
    send_to_feishu(card)
    print("推送成功 ✅")


def run_stock_evening():
    """美股收盘推送：美股指数 + 大宗商品 + 汇率"""
    print("📈 美股收盘简报")

    # 获取美股收盘
    stocks = fetch_major_indices()

    # 获取大宗商品
    commodities = fetch_commodities()

    # 获取汇率
    forex_rates = fetch_all_forex_rates()
    valid_rates = {k: v for k, v in forex_rates.items() if v}

    card = build_stock_card(
        title="📈 美股收盘简报",
        stocks=stocks,
        commodities=commodities,
        forex_rates=valid_rates,
        time_desc="04:00+1"
    )
    send_to_feishu(card)
    print("推送成功 ✅")


def run_stock_analysis(args):
    """股票/板块分析报告"""
    stock_code = args.stock_code
    sector = args.sector
    market = args.market
    report_type = args.report_type
    stock_codes = args.stock_codes

    if stock_code:
        # 分析单只股票 - 支持任意代码
        print(f"📊 正在分析股票: {stock_code} ({market})...")
        analysis = analyze_stock(stock_code, market, report_type)
        if "error" in analysis:
            print(f"  ⚠️  {analysis['error']}")
            return

        print(f"  ✅ 分析完成: {generate_analysis_summary(analysis)}")

        card = build_analysis_card(
            analysis_type="stock",
            analysis=analysis,
            report_type=report_type
        )
        send_to_feishu(card)
        print("推送成功 ✅")

    elif sector:
        # 分析板块 - 支持任意板块名称和自定义成分股
        print(f"📊 正在分析板块: {sector} ({market})...")
        analysis = analyze_sector(sector, market, stock_codes)
        if "error" in analysis:
            print(f"  ⚠️  {analysis['error']}")
            return

        print(f"  ✅ 分析完成: {generate_analysis_summary(analysis)}")

        card = build_analysis_card(
            analysis_type="sector",
            analysis=analysis,
            report_type=report_type
        )
        send_to_feishu(card)
        print("推送成功 ✅")
    else:
        print("  ⚠️  请提供股票代码或板块名称")


def main():
    parser = argparse.ArgumentParser(description='每日简报推送')
    parser.add_argument('--mode', type=str, default='daily',
                        choices=['daily', 'stock-morning', 'stock-afternoon', 'stock-evening', 'stock-analysis'],
                        help='运行模式：daily(完整简报), stock-morning(A股开盘), stock-afternoon(港股收盘), stock-evening(美股收盘), stock-analysis(股票分析)')
    parser.add_argument('--stock-code', type=str, default='',
                        help='股票代码（如 AAPL, 00700.HK）')
    parser.add_argument('--sector', type=str, default='',
                        help='板块名称（如 科技、金融、医药、新能源）')
    parser.add_argument('--market', type=str, default='US',
                        choices=['US', 'HK', 'CN'],
                        help='市场：US(美股)、HK(港股)、CN(A股)')
    parser.add_argument('--report-type', type=str, default='full',
                        choices=['full', 'technical', 'fundamental', 'news'],
                        help='报告类型：full(完整)、technical(技术)、fundamental(基本面)')
    parser.add_argument('--stock-codes', type=str, default='',
                        help='板块成分股代码（逗号分隔，如：AAPL,MSFT,GOOGL）')
    args = parser.parse_args()

    if args.mode == 'daily':
        run_daily_digest()
    elif args.mode == 'stock-morning':
        run_stock_morning()
    elif args.mode == 'stock-afternoon':
        run_stock_afternoon()
    elif args.mode == 'stock-evening':
        run_stock_evening()
    elif args.mode == 'stock-analysis':
        run_stock_analysis(args)


if __name__ == "__main__":
    main()
