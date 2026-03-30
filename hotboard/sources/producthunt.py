import sys
import os

# 允许导入项目根目录的 fetchers 模块
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(__file__))))

from hotboard.sources.base import BaseFetcher
from hotboard.models import HotItem
from fetchers.product_hunt import fetch_product_hunt_trending


class ProductHuntFetcher(BaseFetcher):
    platform = "producthunt"
    platform_name = "Product Hunt"
    icon = "🚀"
    group = "tech"
    source_url = "https://www.producthunt.com"

    def fetch(self) -> list[HotItem]:
        products = fetch_product_hunt_trending(limit=20)
        items = []
        for i, product in enumerate(products):
            name = product.get("name", "")
            tagline = product.get("tagline", "")
            votes = product.get("votes", 0)
            url = product.get("url", "")
            topics = product.get("topics", [])

            hot_value = f"▲ {votes}" if votes > 0 else ""
            category = " · ".join(topics) if topics else ""

            items.append(HotItem(
                rank=i + 1,
                title=name,
                url=url,
                hot_value=hot_value,
                category=f"{category} · {tagline}" if category else tagline,
            ))
        return items
