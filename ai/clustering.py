"""
热点聚类模块 - 通过关键词提取识别今日最热话题
"""
import re
from typing import List, Dict, Tuple, Counter as CounterType
from collections import Counter


def extract_keywords(text: str) -> List[str]:
    """
    从文本中提取关键词（简单的基于词频的方法）
    """
    # 清理文本
    text = text.lower()
    # 移除标点
    text = re.sub(r'[^\w\s]', ' ', text)

    # 停用词列表（简化版）
    stop_words = {
        'the', 'a', 'an', 'is', 'are', 'was', 'were', 'be', 'been',
        'and', 'or', 'but', 'in', 'on', 'at', 'to', 'for', 'of',
        'with', 'by', 'from', 'as', 'it', 'its', 'this', 'that',
        '的', '了', '在', '是', '我', '有', '和', '就', '不', '人',
        '都', '一', '一个', '上', '也', '很', '到', '说', '要', '去',
        '你', '会', '着', '没有', '看', '好', '自己', '这', '那',
        'report', 'says', 'new', 'year', 'years', 'million', 'billion',
        'company', 'companies', 'said', 'say', 'saying'
    }

    words = [w for w in text.split() if len(w) > 2 and w not in stop_words]
    return words


def cluster_news(news_items: List[Dict], min_cluster_size: int = 2) -> List[Dict]:
    """
    对新闻进行聚类，识别热点话题

    Args:
        news_items: 新闻列表，每项包含 title
        min_cluster_size: 最小聚类大小（话题至少包含几条新闻）

    Returns:
        热点话题列表，每项包含 topic 和 related_news
    """
    if not news_items:
        return []

    # 1. 提取所有标题的关键词
    all_keywords: List[str] = []
    item_keywords: List[List[str]] = []

    for item in news_items:
        title = item.get('title', '')
        keywords = extract_keywords(title)
        all_keywords.extend(keywords)
        item_keywords.append(keywords)

    # 2. 统计词频，找出热门关键词
    word_counts = Counter(all_keywords)
    top_keywords = word_counts.most_common(30)

    # 3. 构建话题聚类
    topic_clusters: Dict[str, List[Dict]] = {}

    for keyword, count in top_keywords:
        if count < min_cluster_size:
            continue

        # 找到包含该关键词的新闻
        related_items = []
        for i, item in enumerate(news_items):
            if keyword in item_keywords[i]:
                related_items.append(item)

        if len(related_items) >= min_cluster_size:
            topic_clusters[keyword] = related_items

    # 4. 去重：如果两个话题高度重合，保留更大的那个
    topics = list(topic_clusters.keys())
    to_remove = set()

    for i, topic1 in enumerate(topics):
        if topic1 in to_remove:
            continue
        items1 = set(id(item) for item in topic_clusters[topic1])

        for topic2 in topics[i+1:]:
            if topic2 in to_remove:
                continue
            items2 = set(id(item) for item in topic_clusters[topic2])

            # 计算重合度
            intersection = len(items1 & items2)
            if intersection > 0:
                # 保留更大的话题
                if len(items1) >= len(items2):
                    to_remove.add(topic2)
                else:
                    to_remove.add(topic1)
                    break

    # 5. 构建结果
    results = []
    for topic, items in topic_clusters.items():
        if topic not in to_remove:
            results.append({
                'topic': topic.capitalize() if topic.islower() else topic,
                'count': len(items),
                'related_news': items[:5]  # 最多5条相关新闻
            })

    # 按热度排序
    results.sort(key=lambda x: x['count'], reverse=True)

    return results[:5]  # 返回前5个热点话题


def generate_hot_topics_summary(clusters: List[Dict]) -> str:
    """
    生成热点话题的文字总结
    """
    if not clusters:
        return "暂无热点话题"

    lines = []
    for i, cluster in enumerate(clusters[:3], 1):
        topic = cluster['topic']
        count = cluster['count']
        news_titles = [item.get('title', '')[:30] + '...' for item in cluster['related_news'][:2]]

        line = f"🔥 {topic}({count}篇)"
        if news_titles:
            line += f" - {', '.join(news_titles)}"
        lines.append(line)

    return '\n'.join(lines)


def find_related_keywords(news_items: List[Dict], target_word: str) -> List[str]:
    """
    找到与目标词经常一起出现的关键词
    """
    co_occurrence: CounterType[str] = Counter()

    for item in news_items:
        title = item.get('title', '').lower()
        keywords = extract_keywords(title)

        if target_word.lower() in keywords:
            for kw in keywords:
                if kw != target_word.lower():
                    co_occurrence[kw] += 1

    return [word for word, count in co_occurrence.most_common(3)]
