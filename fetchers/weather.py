import requests
import os


def fetch_weather() -> dict:
    """调用和风天气 API 获取当前天气信息"""
    key = os.environ["QWEATHER_KEY"]
    location = os.environ.get("QWEATHER_LOCATION", "101010100")  # 默认北京
    url = f"https://devapi.qweather.com/v7/weather/now?location={location}&key={key}"

    r = requests.get(url, timeout=10)
    r.raise_for_status()
    data = r.json()

    if data.get("code") != "200":
        raise RuntimeError(f"和风天气 API 错误: code={data.get('code')}")

    now = data["now"]
    return {
        "text": now["text"],          # 天气描述，如"晴"
        "temp": now["temp"],          # 当前温度（摄氏度）
        "feelsLike": now["feelsLike"],  # 体感温度
        "windDir": now["windDir"],    # 风向
        "windScale": now["windScale"],  # 风力等级
        "humidity": now["humidity"],  # 相对湿度
    }
