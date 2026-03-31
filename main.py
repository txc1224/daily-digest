import argparse


MODE_ALIASES = {
    "daily": "full-daily",
    "full-daily": "full-daily",
    "hotboard-brief": "hotboard-brief",
    "hotboard-daily": "hotboard-brief",
    "stock-morning": "stock-morning",
    "stock-afternoon": "stock-afternoon",
    "stock-evening": "stock-evening",
    "stock-analysis": "stock-analysis",
}


def run_stock_morning():
    """A股开盘推送：上证指数 + 隔夜美股收盘"""
    from formatter import build_stock_card
    from sender import send_to_feishu
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
    from formatter import build_stock_card
    from sender import send_to_feishu
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
    from fetchers.forex import fetch_all_forex_rates
    from fetchers.stocks import fetch_commodities, fetch_major_indices
    from formatter import build_stock_card
    from sender import send_to_feishu
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
    from fetchers.stock_analyzer import analyze_stock, analyze_sector, generate_analysis_summary
    from formatter import build_analysis_card
    from sender import send_to_feishu
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


def run_hotboard_daily_brief():
    """基于 HotBoard 的精简日摘要"""
    from hotboard.feishu_push import push_hotboard_daily_brief_to_feishu
    push_hotboard_daily_brief_to_feishu()


def main():
    parser = argparse.ArgumentParser(description='每日简报推送')
    parser.add_argument('--mode', type=str, default='full-daily',
                        help='运行模式：full-daily(完整简报), hotboard-brief(热榜日摘要), stock-morning(A股开盘), stock-afternoon(港股收盘), stock-evening(美股收盘), stock-analysis(股票分析)。兼容别名：daily -> full-daily, hotboard-daily -> hotboard-brief')
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
    mode = MODE_ALIASES.get(args.mode)

    if not mode:
        parser.error(
            "无效的 --mode，支持: full-daily, hotboard-brief, stock-morning, "
            "stock-afternoon, stock-evening, stock-analysis。兼容别名: daily, hotboard-daily"
        )

    if mode == 'full-daily':
        from daily_digest_pipeline import run_daily_digest
        run_daily_digest()
    elif mode == 'hotboard-brief':
        run_hotboard_daily_brief()
    elif mode == 'stock-morning':
        run_stock_morning()
    elif mode == 'stock-afternoon':
        run_stock_afternoon()
    elif mode == 'stock-evening':
        run_stock_evening()
    elif mode == 'stock-analysis':
        run_stock_analysis(args)


if __name__ == "__main__":
    main()
