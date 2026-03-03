"""
情感分析模块 - 分析股市/财经新闻的情绪倾向
"""
import re
from typing import Dict, List, Tuple


# 情感词典（简化版，用于快速判断）
POSITIVE_WORDS = {
    '涨', '上涨', '反弹', '回升', '走强', '增长', '增长', '利好', '积极',
    '突破', '创新高', '激增', '暴涨', '飙升', '看好', '乐观', '强劲',
    '买入', '增持', '上调', '超出预期', '超预期', '亮眼', '优秀', '良好',
    'rise', 'rising', 'gain', 'gains', 'surge', 'surging', 'rally',
    'bull', 'bullish', 'up', 'upward', 'strong', 'growth', 'positive',
    'outperform', 'beat', 'beats', 'exceed', 'exceeds', 'soar', 'jump'
}

NEGATIVE_WORDS = {
    '跌', '下跌', '回调', '回落', '走弱', '下跌', '下跌', '利空', '消极',
    '跌破', '创新低', '暴跌', '暴跌', '崩盘', '看空', '悲观', '疲软',
    '卖出', '减持', '下调', '低于预期', '不及预期', '惨淡', '糟糕', '恶化',
    'fall', 'falling', 'drop', 'drops', 'decline', 'declining', 'plunge',
    'bear', 'bearish', 'down', 'downward', 'weak', 'weakness', 'negative',
    'underperform', 'miss', 'misses', 'crash', 'tumble', 'slump'
}

NEUTRAL_WORDS = {
    '持平', '盘整', '震荡', '稳定', '平稳', '观望', '谨慎', '中性',
    'flat', 'steady', 'stable', 'unchanged', 'neutral', 'cautious'
}


def analyze_sentiment_text(text: str) -> Tuple[str, float]:
    """
    分析单条文本的情感倾向

    Returns:
        (情感标签, 置信度分数)
        情感标签: 'positive', 'negative', 'neutral'
        置信度: 0-1 之间的分数
    """
    if not text:
        return ('neutral', 0.0)

    text_lower = text.lower()

    # 分词（简化处理）
    words = set(re.findall(r'\b\w+\b', text_lower))
    # 也包含中文（按字符分）
    words.update(text_lower)

    pos_count = len(words & POSITIVE_WORDS)
    neg_count = len(words & NEGATIVE_WORDS)
    neu_count = len(words & NEUTRAL_WORDS)

    total = pos_count + neg_count + neu_count
    if total == 0:
        return ('neutral', 0.5)

    # 计算情感倾向
    pos_score = pos_count / total
    neg_score = neg_count / total
    neu_score = neu_count / total

    # 判断情感标签
    if pos_score > neg_score and pos_score > neu_score:
        confidence = min(pos_score + 0.5, 1.0)
        return ('positive', confidence)
    elif neg_score > pos_score and neg_score > neu_score:
        confidence = min(neg_score + 0.5, 1.0)
        return ('negative', confidence)
    else:
        return ('neutral', 0.5 + neu_score * 0.5)


def analyze_news_sentiment(news_items: List[Dict]) -> List[Dict]:
    """
    批量分析新闻情感

    Args:
        news_items: 新闻列表

    Returns:
        添加了 sentiment 和 sentiment_score 的新闻列表
    """
    results = []

    for item in news_items:
        title = item.get('title', '')
        sentiment, confidence = analyze_sentiment_text(title)

        results.append({
            **item,
            'sentiment': sentiment,
            'sentiment_score': confidence,
            'sentiment_emoji': get_sentiment_emoji(sentiment)
        })

    return results


def get_sentiment_emoji(sentiment: str) -> str:
    """获取情感对应的 emoji"""
    return {
        'positive': '🟢',
        'negative': '🔴',
        'neutral': '⚪'
    }.get(sentiment, '⚪')


def get_sentiment_label(sentiment: str) -> str:
    """获取情感的中文标签"""
    return {
        'positive': '正面',
        'negative': '负面',
        'neutral': '中性'
    }.get(sentiment, '中性')


def analyze_finance_sentiment(news_items: List[Dict]) -> Dict:
    """
    分析财经新闻的整体情感倾向

    Returns:
        {
            'overall': 'positive' | 'negative' | 'neutral',
            'positive_count': int,
            'negative_count': int,
            'neutral_count': int,
            'positive_ratio': float,
            'summary': str
        }
    """
    analyzed = analyze_news_sentiment(news_items)

    positive = [n for n in analyzed if n['sentiment'] == 'positive']
    negative = [n for n in analyzed if n['sentiment'] == 'negative']
    neutral = [n for n in analyzed if n['sentiment'] == 'neutral']

    total = len(analyzed)
    if total == 0:
        return {
            'overall': 'neutral',
            'positive_count': 0,
            'negative_count': 0,
            'neutral_count': 0,
            'positive_ratio': 0.5,
            'summary': '暂无数据'
        }

    pos_ratio = len(positive) / total
    neg_ratio = len(negative) / total

    # 判断整体情感
    if pos_ratio > neg_ratio + 0.2:
        overall = 'positive'
        summary = f"市场情绪偏乐观 📈，{len(positive)}/{total} 条新闻为正面"
    elif neg_ratio > pos_ratio + 0.2:
        overall = 'negative'
        summary = f"市场情绪偏悲观 📉，{len(negative)}/{total} 条新闻为负面"
    else:
        overall = 'neutral'
        summary = f"市场情绪中性 ⚖️，正负面新闻分布均衡"

    # 添加极端情绪提示
    high_confidence_negative = [n for n in negative if n.get('sentiment_score', 0) > 0.8]
    if high_confidence_negative:
        summary += "，⚠️ 存在高风险信号"

    return {
        'overall': overall,
        'positive_count': len(positive),
        'negative_count': len(negative),
        'neutral_count': len(neutral),
        'positive_ratio': pos_ratio,
        'summary': summary
    }


def filter_by_sentiment(news_items: List[Dict], sentiment_type: str = 'positive') -> List[Dict]:
    """
    按情感过滤新闻

    Args:
        news_items: 新闻列表
        sentiment_type: 'positive' | 'negative' | 'neutral' | 'all'

    Returns:
        过滤后的新闻列表
    """
    if sentiment_type == 'all':
        return news_items

    analyzed = analyze_news_sentiment(news_items)
    return [item for item in analyzed if item['sentiment'] == sentiment_type]
