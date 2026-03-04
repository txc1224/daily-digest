"""
新闻摘要生成器 - 使用 Groq API 或本地规则为新闻生成一句话摘要
"""
import os
import re
import requests
from typing import List, Dict


GROQ_API_URL = "https://api.groq.com/openai/v1/chat/completions"
GROQ_MODEL = "llama-3.1-8b-instant"  # 免费，速度快，中文理解好


def has_groq_key() -> bool:
    """检查是否有 Groq API Key"""
    return bool(os.environ.get("GROQ_API_KEY", "").strip())


def call_groq(prompt: str, max_tokens: int = 200) -> str:
    """调用 Groq API，返回文本结果"""
    api_key = os.environ.get("GROQ_API_KEY", "").strip()
    headers = {
        "Authorization": f"Bearer {api_key}",
        "Content-Type": "application/json",
    }
    payload = {
        "model": GROQ_MODEL,
        "messages": [{"role": "user", "content": prompt}],
        "max_tokens": max_tokens,
        "temperature": 0.3,
    }
    resp = requests.post(GROQ_API_URL, json=payload, headers=headers, timeout=15)
    resp.raise_for_status()
    return resp.json()["choices"][0]["message"]["content"].strip()


def extract_key_info(title: str) -> str:
    """
    无 API Key 时的备用摘要方案：从标题提取关键信息
    基于规则的简单摘要生成
    """
    stop_phrases = [
        r'据悉，?', r'据报道，?', r'消息称，?', r'据了解，?',
        r'业内人士指出，?', r'专家表示，?', r'分析认为，?',
        r'独家：?', r'重磅：?', r'突发：?', r'快讯：?',
        r'刚刚[，：]', r'最新[：，]', r'注意[：，]',
    ]

    summary = title
    for phrase in stop_phrases:
        summary = re.sub(phrase, '', summary)

    patterns = [
        r'([^，。；]+)(?:宣布|发布|推出|完成|获得|收购|投资|上涨|下跌|增长|下降)([^，。；]+)',
        r'([^，。；]+)(?:与|和)([^，。；]+)(?:合作|合并|竞争)',
    ]

    for pattern in patterns:
        match = re.search(pattern, summary)
        if match:
            parts = [p.strip() for p in match.groups() if p.strip()]
            if parts:
                return '，'.join(parts[:2])

    summary = summary.strip('：:，,。. ')
    if len(summary) > 35:
        for punct in ['，', '。', '；', ',', '.', ';']:
            idx = summary.find(punct, 15, 35)
            if idx > 0:
                return summary[:idx]
        return summary[:32] + "..."

    return summary


def summarize_news(title: str, description: str = "") -> str:
    """
    为单条新闻生成一句话摘要
    优先使用 Groq API，无 Key 时使用本地规则
    """
    if not has_groq_key():
        return extract_key_info(title)

    try:
        content = title
        if description:
            content = f"{title}\n{description}"

        prompt = f"""请为以下新闻生成一句简短的中文摘要（不超过30字）：

{content}

要求：
1. 一句话概括核心内容
2. 不超过30个汉字
3. 只返回摘要内容，不要任何解释"""

        summary = call_groq(prompt, max_tokens=100)
        summary = summary.strip('""\'"\'').strip()
        if len(summary) > 35:
            summary = summary[:32] + "..."
        return summary

    except Exception as e:
        print(f"Groq API 失败，使用备用方案: {e}")
        return extract_key_info(title)


def batch_summarize_efficient(news_items: List[Dict], max_items: int = 10) -> List[Dict]:
    """
    批量为新闻生成摘要
    优先使用 Groq API，无 Key 时使用本地规则
    """
    if not news_items:
        return news_items

    if not has_groq_key():
        print("  ℹ️  未检测到 GROQ_API_KEY，使用本地规则生成摘要")
        return [{**item, "summary": extract_key_info(item.get("title", ""))}
                for item in news_items[:max_items]]

    try:
        items_text = "\n\n".join([
            f"[{i+1}] {item.get('title', '')}"
            for i, item in enumerate(news_items[:max_items])
        ])

        prompt = f"""请为以下 {len(news_items[:max_items])} 条新闻分别生成一句话中文摘要。
每条摘要不超过25字。

{items_text}

请按以下格式返回：
[1] 摘要内容
[2] 摘要内容
...

只返回摘要，不要其他解释。"""

        text = call_groq(prompt, max_tokens=500)
        summaries = parse_batch_response(text, len(news_items[:max_items]))

        results = []
        for i, item in enumerate(news_items[:max_items]):
            summary = summaries.get(i + 1, "")
            if not summary:
                summary = extract_key_info(item.get("title", ""))
            results.append({**item, "summary": summary})

        return results

    except Exception as e:
        print(f"Groq API 批量摘要失败，使用备用方案: {e}")
        return [{**item, "summary": extract_key_info(item.get("title", ""))}
                for item in news_items[:max_items]]


def parse_batch_response(text: str, expected_count: int) -> Dict[int, str]:
    """解析批量摘要响应"""
    summaries = {}

    lines = text.strip().split('\n')
    for line in lines:
        line = line.strip()
        if not line:
            continue

        for i in range(1, expected_count + 1):
            prefix = f"[{i}]"
            if line.startswith(prefix):
                summary = line[len(prefix):].strip()
                summary = summary.lstrip(':：').strip()
                summaries[i] = summary
                break

    return summaries
