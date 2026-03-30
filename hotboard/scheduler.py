from apscheduler.schedulers.background import BackgroundScheduler
from hotboard.config import REFRESH_INTERVAL_MINUTES, FEISHU_PUSH_HOUR, FEISHU_PUSH_MINUTE
from hotboard.cache import clear_cache
from hotboard.app import fetch_all_boards


def _scheduled_refresh():
    """定时清除缓存并重新抓取"""
    clear_cache()
    fetch_all_boards()
    print(f"⏰ 定时刷新完成")


def _scheduled_feishu_push():
    """每日飞书推送"""
    from hotboard.feishu_push import push_hotboard_to_feishu
    push_hotboard_to_feishu()


def start_scheduler():
    """启动定时任务"""
    scheduler = BackgroundScheduler()

    # 每 N 分钟刷新热榜
    scheduler.add_job(
        _scheduled_refresh,
        "interval",
        minutes=REFRESH_INTERVAL_MINUTES,
        id="hotboard_refresh",
    )

    # 每天指定时间推送飞书
    scheduler.add_job(
        _scheduled_feishu_push,
        "cron",
        hour=FEISHU_PUSH_HOUR,
        minute=FEISHU_PUSH_MINUTE,
        id="hotboard_feishu_push",
    )

    scheduler.start()
    print(f"⏰ 定时任务已启动: 每 {REFRESH_INTERVAL_MINUTES} 分钟刷新, 每天 {FEISHU_PUSH_HOUR}:{FEISHU_PUSH_MINUTE:02d} 推送飞书")
    return scheduler
