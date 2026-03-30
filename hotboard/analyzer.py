"""
热点分析模块 — 跨平台话题聚类 + AI 摘要
"""
import sys
import os

sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))

from ai.clustering import cluster_news, extract_keywords
from ai.summarizer import has_groq_key, call_groq, extract_key_info


def analyze_cross_platform(boards: dict) -> dict:
    """
    跨平台热点分析：找出同时出现在多个平台的话题

    Args:
        boards: {platform: board_dict} 格式的数据

    Returns:
        analysis dict with cross_platform_topics
    """
    # 1. 收集所有平台的 items，附带平台来源
    all_items = []
    for platform, board in boards.items():
        for item in board.get("items", []):
            all_items.append({
                "title": item.get("title", ""),
                "url": item.get("url", ""),
                "platform": platform,
                "platform_name": board.get("platform_name", platform),
                "rank": item.get("rank", 0),
                "hot_value": item.get("hot_value", ""),
            })

    if not all_items:
        return {"cross_platform_topics": []}

    # 2. 关键词聚类
    clusters = cluster_news(all_items, min_cluster_size=2)

    # 3. 筛选跨平台话题（出现在 2+ 个不同平台）
    cross_platform_topics = []
    for cluster in clusters:
        related = cluster.get("related_news", [])
        platforms = list(set(item.get("platform", "") for item in related))

        if len(platforms) < 2:
            continue

        # 计算热度分（出现平台数 * 30 + 相关条目数 * 10，上限100）
        heat_score = min(len(platforms) * 30 + len(related) * 10, 100)

        # 取各平台中排名最高的条目作为代表
        best_items = []
        seen_platforms = set()
        for item in sorted(related, key=lambda x: x.get("rank", 99)):
            p = item.get("platform", "")
            if p not in seen_platforms:
                seen_platforms.add(p)
                best_items.append({
                    "title": item["title"],
                    "url": item.get("url", ""),
                    "platform": p,
                    "platform_name": item.get("platform_name", p),
                    "rank": item.get("rank", 0),
                })

        cross_platform_topics.append({
            "topic": cluster["topic"],
            "summary": "",  # 后续 AI 填充
            "platforms": platforms,
            "platform_count": len(platforms),
            "heat_score": heat_score,
            "related_items": best_items[:5],
        })

    # 按热度排序
    cross_platform_topics.sort(key=lambda x: x["heat_score"], reverse=True)
    cross_platform_topics = cross_platform_topics[:10]

    # 4. AI 摘要生成（可选）
    if cross_platform_topics:
        cross_platform_topics = _generate_summaries(cross_platform_topics)

    return {"cross_platform_topics": cross_platform_topics}


def _generate_summaries(topics: list) -> list:
    """为跨平台热点生成 AI 摘要"""
    if not has_groq_key():
        # 无 API Key：用第一条相关新闻标题作为摘要
        for topic in topics:
            items = topic.get("related_items", [])
            if items:
                topic["summary"] = items[0]["title"]
            else:
                topic["summary"] = topic["topic"]
        return topics

    try:
        # 批量生成摘要
        topics_text = "\n".join([
            f"[{i+1}] 话题关键词: {t['topic']}，出现在 {', '.join(t['platforms'])}，"
            f"相关标题: {'; '.join(item['title'][:30] for item in t['related_items'][:3])}"
            for i, t in enumerate(topics[:5])
        ])

        prompt = f"""以下是今天的跨平台热点话题，请为每个话题生成一句简短的中文总结（不超过30字）：

{topics_text}

格式：
[1] 总结内容
[2] 总结内容
...

只返回总结，不要解释。"""

        text = call_groq(prompt, max_tokens=300)

        # 解析响应
        import re
        for i, topic in enumerate(topics[:5]):
            pattern = rf'\[{i+1}\]\s*(.*?)(?:\n|$)'
            match = re.search(pattern, text)
            if match:
                topic["summary"] = match.group(1).strip().lstrip(':：')
            elif not topic["summary"]:
                items = topic.get("related_items", [])
                topic["summary"] = items[0]["title"] if items else topic["topic"]

    except Exception as e:
        print(f"  [WARN] AI 摘要生成失败: {e}", file=sys.stderr)
        for topic in topics:
            if not topic["summary"]:
                items = topic.get("related_items", [])
                topic["summary"] = items[0]["title"] if items else topic["topic"]

    return topics
