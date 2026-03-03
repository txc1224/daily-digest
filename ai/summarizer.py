"""
新闻摘要生成器 - 使用 Claude API 或本地规则为新闻生成一句话摘要
"""
import os
import re
from typing import List, Dict


# 尝试导入 anthropic，如果失败则使用备用方案
try:
    from anthropic import Anthropic
    ANTHROPIC_AVAILABLE = True
except ImportError:
    ANTHROPIC_AVAILABLE = False


def has_anthropic_key() -> bool:
    """检查是否有 Anthropic API Key"""
    return ANTHROPIC_AVAILABLE and bool(os.environ.get("ANTHROPIC_API_KEY", ""))


def create_summarizer_client():
    """创建 Anthropic 客户端"""
    api_key = os.environ.get("ANTHROPIC_API_KEY", "")
    if not api_key:
        raise ValueError("ANTHROPIC_API_KEY 环境变量未设置")
    return Anthropic(api_key=api_key)


def extract_key_info(title: str) -> str:
    """
    无 API Key 时的备用摘要方案：从标题提取关键信息
    基于规则的简单摘要生成
    """
    # 移除常见的语气词和冗余词
    stop_phrases = [
        r'据悉，?', r'据报道，?', r'消息称，?', r'据了解，?',
        r'业内人士指出，?', r'专家表示，?', r'分析认为，?',
        r'独家：?', r'重磅：?', r'突发：?', r'快讯：?',
        r'刚刚[，：]', r'最新[：，]', r'注意[：，]',
    ]

    summary = title
    for phrase in stop_phrases:
        summary = re.sub(phrase, '', summary)

    # 提取核心实体和动作
    # 尝试匹配 "某公司/人 + 动作 + 对象" 的模式
    patterns = [
        r'([^，。；]+)(?:宣布|发布|推出|推出|完成|获得|收购|投资|上涨|下跌|增长|下降)([^，。；]+)',
        r'([^，。；]+)(?:与|和)([^，。；]+)(?:合作|合并|竞争)',
    ]

    for pattern in patterns:
        match = re.search(pattern, summary)
        if match:
            # 提取匹配的核心内容
            parts = [p.strip() for p in match.groups() if p.strip()]
            if parts:
                return '，'.join(parts[:2])  # 最多两个部分

    # 如果以上都失败，返回清理后的标题（截断）
    summary = summary.strip('：:，,。. ')
    if len(summary) > 35:
        # 尝试在逗号或句号处截断
        for punct in ['，', '。', '；', ',', '.', ';']:
            idx = summary.find(punct, 15, 35)
            if idx > 0:
                return summary[:idx]
        return summary[:32] + "..."

    return summary


def summarize_news(title: str, description: str = "") -> str:
    """
    为单条新闻生成一句话摘要
    优先使用 Claude API，无 Key 时使用本地规则
    """
    # 如果没有 API Key，使用备用方案
    if not has_anthropic_key():
        return extract_key_info(title)

    try:
        client = create_summarizer_client()

        content = title
        if description:
            content = f"{title}\n{description}"

        prompt = f"""请为以下新闻生成一句简短的中文摘要（不超过30字）：

{content}

要求：
1. 一句话概括核心内容
2. 不超过30个汉字
3. 只返回摘要内容，不要任何解释"""

        response = client.messages.create(
            model="claude-3-haiku-20240307",
            max_tokens=100,
            temperature=0.3,
            messages=[{"role": "user", "content": prompt}]
        )

        summary = response.content[0].text.strip()
        # 移除可能的引号和多余空格
        summary = summary.strip('""').strip("'").strip()

        # 限制长度
        if len(summary) > 35:
            summary = summary[:32] + "..."

        return summary

    except Exception as e:
        print(f"Claude API 失败，使用备用方案: {e}")
        return extract_key_info(title)


def batch_summarize_efficient(news_items: List[Dict], max_items: int = 10) -> List[Dict]:
    """
    批量为新闻生成摘要
    优先使用 Claude API，无 Key 时使用本地规则
    """
    if not news_items:
        return news_items

    # 如果没有 API Key，直接使用本地规则处理
    if not has_anthropic_key():
        print("  ℹ️  未检测到 ANTHROPIC_API_KEY，使用本地规则生成摘要")
        return [{**item, "summary": extract_key_info(item.get("title", ""))}
                for item in news_items[:max_items]]

    try:
        client = create_summarizer_client()

        # 构建批量请求
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

        response = client.messages.create(
            model="claude-3-haiku-20240307",
            max_tokens=500,
            temperature=0.3,
            messages=[{"role": "user", "content": prompt}]
        )

        # 解析响应
        summaries = parse_batch_response(response.content[0].text.strip(), len(news_items[:max_items]))

        # 合并结果
        results = []
        for i, item in enumerate(news_items[:max_items]):
            summary = summaries.get(i + 1, "")
            # 如果 API 返回空，使用备用方案
            if not summary:
                summary = extract_key_info(item.get("title", ""))
            results.append({**item, "summary": summary})

        return results

    except Exception as e:
        print(f"Claude API 批量摘要失败，使用备用方案: {e}")
        # 降级：使用本地规则
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

        # 查找 [数字] 格式
        for i in range(1, expected_count + 1):
            prefix = f"[{i}]"
            if line.startswith(prefix):
                summary = line[len(prefix):].strip()
                # 清理可能的额外标记
                summary = summary.lstrip(':：').strip()
                summaries[i] = summary
                break

    return summaries
