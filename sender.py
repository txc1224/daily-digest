import os
import requests


def send_to_feishu(card: dict) -> None:
    """
    将飞书卡片 JSON POST 到自定义机器人 Webhook。
    card 为 build_card() 返回的字典。
    """
    webhook = os.environ["FEISHU_WEBHOOK"]
    payload = {
        "msg_type": "interactive",
        "card": card,
    }
    r = requests.post(webhook, json=payload, timeout=10)
    r.raise_for_status()

    # 飞书 Webhook 即使 HTTP 200 也可能在 body 里返回业务错误
    body = r.json()
    if body.get("code", 0) != 0:
        raise RuntimeError(f"飞书推送失败: {body}")
