"""
免费翻译模块 - 使用 LibreTranslate 或 MyMemory API
将英文新闻描述翻译为中文
"""
import requests
import re
from typing import Optional


# 缓存，避免重复翻译
translation_cache = {}


def translate_libretranslate(text: str, target_lang: str = "zh") -> Optional[str]:
    """
    使用 LibreTranslate API（免费开源）
    公共实例：https://libretranslate.de 或 https://translate.argosopentech.com
    """
    if not text or len(text.strip()) < 3:
        return text

    try:
        # 使用多个公共实例，失败时自动切换
        instances = [
            "https://libretranslate.de",
            "https://translate.argosopentech.com",
            "https://libretranslate.pussthecat.org",
        ]

        for base_url in instances:
            try:
                url = f"{base_url}/translate"
                params = {
                    "q": text,
                    "source": "en",
                    "target": target_lang,
                    "format": "text"
                }

                r = requests.post(url, data=params, timeout=10)
                if r.status_code == 200:
                    data = r.json()
                    return data.get("translatedText", text)
            except Exception:
                continue

        return None
    except Exception:
        return None


def translate_mymemory(text: str, target_lang: str = "zh-CN") -> Optional[str]:
    """
    使用 MyMemory API（免费，每天 5000 字符）
    https://api.mymemory.translated.net
    """
    if not text or len(text.strip()) < 3:
        return text

    try:
        # 截断文本，避免超出限制
        text_to_translate = text[:500] if len(text) > 500 else text

        url = "https://api.mymemory.translated.net/get"
        params = {
            "q": text_to_translate,
            "langpair": f"en|{target_lang}"
        }

        r = requests.get(url, params=params, timeout=10)
        if r.status_code == 200:
            data = r.json()
            response_data = data.get("responseData", {})
            translated = response_data.get("translatedText", "")

            # 检查是否超出配额
            if "INVALID LANGUAGE PAIR" in translated or "MYMEMORY" in translated.upper():
                return None

            return translated if translated and translated != text_to_translate else None

        return None
    except Exception:
        return None


def translate_text(text: str) -> str:
    """
    翻译英文文本为中文
    优先使用缓存，然后尝试多个免费 API
    """
    if not text:
        return ""

    # 检查是否已经是中文为主
    chinese_chars = len([c for c in text if '\u4e00' <= c <= '\u9fff'])
    if chinese_chars > len(text) * 0.3:
        return text

    # 检查缓存
    cache_key = text.strip().lower()[:100]
    if cache_key in translation_cache:
        return translation_cache[cache_key]

    # 尝试翻译
    translated = None

    # 1. 尝试 MyMemory
    translated = translate_mymemory(text)

    # 2. 如果失败，尝试 LibreTranslate
    if not translated:
        translated = translate_libretranslate(text)

    # 3. 如果都失败，返回原文（截断）
    if not translated:
        if len(text) > 50:
            return text[:47] + "..."
        return text

    # 存入缓存
    translation_cache[cache_key] = translated
    return translated


def translate_news_item(item: dict) -> dict:
    """翻译单条新闻的标题（如果是英文）"""
    title = item.get("title", "")

    # 检查是否主要是英文
    if title and len(re.findall(r'[a-zA-Z]', title)) > len(title) * 0.5:
        translated_title = translate_text(title)
        if translated_title and translated_title != title:
            return {**item, "title": translated_title, "original_title": title}

    return item


def translate_news_batch(news_items: list, max_items: int = 10) -> list:
    """批量翻译新闻标题"""
    results = []
    for item in news_items[:max_items]:
        translated_item = translate_news_item(item)
        results.append(translated_item)
    return results
