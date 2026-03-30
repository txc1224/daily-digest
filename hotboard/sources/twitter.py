from bs4 import BeautifulSoup
from hotboard.sources.base import BaseFetcher
from hotboard.models import HotItem


class TwitterFetcher(BaseFetcher):
    platform = "twitter"
    platform_name = "Twitter/X"
    icon = "🐦"
    group = "overseas"
    source_url = "https://twitter.com/explore/tabs/trending"

    def fetch(self) -> list[HotItem]:
        # 通过 trends24.in 抓取 Twitter/X 热门趋势
        url = "https://trends24.in/united-states/"
        headers = {
            "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) "
                          "AppleWebKit/537.36 (KHTML, like Gecko) "
                          "Chrome/120.0.0.0 Safari/537.36",
            "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
        }

        try:
            r = self.http_get(url, headers=headers)
            r.raise_for_status()
            return self._parse_trends24(r.text)
        except Exception as e:
            print(f"Twitter trends24 抓取失败: {e}")
            return []

    def _parse_trends24(self, html: str) -> list[HotItem]:
        """解析 trends24.in 页面，提取热门趋势"""
        soup = BeautifulSoup(html, "html.parser")
        items = []
        seen = set()

        # trends24.in 的趋势列在 trend-card 区块中
        trend_cards = soup.select("ol.trend-card__list")
        for card in trend_cards:
            links = card.select("li a")
            for link in links:
                name = link.get_text(strip=True)
                if not name or name in seen:
                    continue
                seen.add(name)

                # 提取推文量（如果有）
                tweet_count = ""
                count_span = link.find_next_sibling("span")
                if count_span:
                    tweet_count = count_span.get_text(strip=True)

                # 构建 Twitter 搜索链接
                search_query = name.replace("#", "%23").replace(" ", "%20")
                tweet_url = f"https://twitter.com/search?q={search_query}"

                items.append(HotItem(
                    rank=len(items) + 1,
                    title=name,
                    url=tweet_url,
                    hot_value=tweet_count,
                ))

                if len(items) >= 20:
                    break
            if len(items) >= 20:
                break

        return items
