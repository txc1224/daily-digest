import requests
import os


# 常用城市坐标表（避免频繁调用 geocoding API）
CITY_COORDS = {
    "beijing":   (39.9042, 116.4074),
    "shanghai":  (31.2304, 121.4737),
    "guangzhou": (23.1291, 113.2644),
    "shenzhen":  (22.5431, 114.0579),
    "chengdu":   (30.5728, 104.0668),
    "hangzhou":  (30.2741, 120.1551),
    "wuhan":     (30.5928, 114.3055),
    "nanjing":   (32.0603, 118.7969),
    "xian":      (34.3416, 108.9398),
    "chongqing": (29.5630, 106.5516),
}

WMO_CODE = {
    0: "晴", 1: "多云转晴", 2: "局部多云", 3: "阴",
    45: "雾", 48: "冻雾",
    51: "小毛毛雨", 53: "中毛毛雨", 55: "大毛毛雨",
    61: "小雨", 63: "中雨", 65: "大雨",
    71: "小雪", 73: "中雪", 75: "大雪",
    80: "阵雨", 81: "中阵雨", 82: "强阵雨",
    95: "雷阵雨", 96: "雷阵雨夹冰雹", 99: "强雷阵雨夹冰雹",
}


def _get_coords(city: str):
    """先查本地表，找不到再调 geocoding API"""
    key = city.lower().replace(" ", "")
    if key in CITY_COORDS:
        return CITY_COORDS[key]

    url = "https://geocoding-api.open-meteo.com/v1/search"
    r = requests.get(url, params={"name": city, "count": 1, "format": "json"}, timeout=10)
    r.raise_for_status()
    results = r.json().get("results", [])
    if not results:
        raise RuntimeError(f"找不到城市: {city}")
    return results[0]["latitude"], results[0]["longitude"]


def fetch_weather() -> dict:
    """
    使用 Open-Meteo API 获取当前天气（完全免费，无需 API Key，不限制云端 IP）。
    城市通过 WEATHER_CITY 环境变量配置（英文名），默认 Beijing。
    """
    city = os.environ.get("WEATHER_CITY", "").strip() or "Beijing"
    lat, lon = _get_coords(city)

    url = "https://api.open-meteo.com/v1/forecast"
    params = {
        "latitude": lat,
        "longitude": lon,
        "current": "temperature_2m,apparent_temperature,relative_humidity_2m,weather_code,wind_speed_10m,wind_direction_10m",
        "timezone": "Asia/Shanghai",
        "forecast_days": 1,
    }
    r = requests.get(url, params=params, timeout=15)
    r.raise_for_status()
    data = r.json()["current"]

    wmo = data["weather_code"]
    wind_deg = data["wind_direction_10m"]
    # 16 方位风向
    dirs = ["北", "北北东", "北东", "东北东", "东", "东南东", "南东", "南南东",
            "南", "南南西", "南西", "西南西", "西", "西北西", "北西", "北北西"]
    wind_dir = dirs[round(wind_deg / 22.5) % 16]

    return {
        "city": city,
        "text": WMO_CODE.get(wmo, f"天气码{wmo}"),
        "temp": str(round(data["temperature_2m"])),
        "feelsLike": str(round(data["apparent_temperature"])),
        "windDir": wind_dir,
        "windScale": f"{round(data['wind_speed_10m'])} km/h",
        "humidity": str(data["relative_humidity_2m"]),
    }
