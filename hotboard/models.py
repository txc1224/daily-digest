from dataclasses import dataclass, field, asdict
from datetime import datetime


@dataclass
class HotItem:
    rank: int
    title: str
    url: str = ""
    hot_value: str = ""
    category: str = ""
    cover_img: str = ""

    def to_dict(self):
        return asdict(self)


@dataclass
class HotBoard:
    platform: str
    platform_name: str
    icon: str
    group: str  # domestic / tech / overseas / seo
    items: list = field(default_factory=list)
    updated_at: str = ""
    source_url: str = ""

    def to_dict(self):
        return {
            "platform": self.platform,
            "platform_name": self.platform_name,
            "icon": self.icon,
            "group": self.group,
            "items": [item.to_dict() if isinstance(item, HotItem) else item for item in self.items],
            "updated_at": self.updated_at,
            "source_url": self.source_url,
        }
