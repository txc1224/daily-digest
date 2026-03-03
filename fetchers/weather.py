import requests
import os


def fetch_weather() -> dict:
    """
    使用 wttr.in 获取天气（完全免费，无需 API Key，不限制云端 IP）。
    城市通过 QWEATHER_LOCATION 环境变量配置（城市英文名或中文拼音）。
    例如: Beijing, Shanghai, Shenzhen
    """
    city = os.environ.get("WEATHER_CITY", "Beijing")
    url = f"https://wttr.in/{city}?format=j1"

    r = requests.get(url, timeout=10, headers={"User-Agent": "daily-digest/1.0"})
    r.raise_for_status()
    data = r.json()

    current = data["current_condition"][0]
    # 取中文天气描述（如有），否则取英文
    lang_zh = next(
        (d["value"] for d in current.get("lang_zh", []) if d.get("value")),
        current.get("weatherDesc", [{}])[0].get("value", "未知"),
    )

    return {
        "text": lang_zh,
        "temp": current["temp_C"],
        "feelsLike": current["FeelsLikeC"],
        "windDir": current["winddir16Point"],
        "windScale": current["windspeedKmph"] + " km/h",
        "humidity": current["humidity"],
    }
