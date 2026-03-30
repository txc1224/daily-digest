import abc
import requests
from datetime import datetime
from hotboard.models import HotBoard, HotItem
from hotboard.config import PROXY_URL, PROXY_PLATFORMS


class BaseFetcher(abc.ABC):
    """所有热榜 fetcher 的抽象基类"""

    platform: str = ""
    platform_name: str = ""
    icon: str = ""
    group: str = ""
    source_url: str = ""

    @abc.abstractmethod
    def fetch(self) -> list[HotItem]:
        """抓取热榜数据，返回 HotItem 列表"""
        ...

    def get_board(self) -> HotBoard:
        items = self.fetch()
        return HotBoard(
            platform=self.platform,
            platform_name=self.platform_name,
            icon=self.icon,
            group=self.group,
            items=items,
            updated_at=datetime.now().isoformat(timespec="seconds"),
            source_url=self.source_url,
        )

    @property
    def needs_proxy(self) -> bool:
        return self.platform in PROXY_PLATFORMS

    @property
    def proxies(self) -> dict | None:
        if self.needs_proxy and PROXY_URL:
            return {"http": PROXY_URL, "https": PROXY_URL}
        return None

    def http_get(self, url: str, **kwargs) -> requests.Response:
        """统一的 HTTP GET 方法，自动处理代理"""
        kwargs.setdefault("timeout", 10)
        proxies = self.proxies
        if proxies:
            kwargs["proxies"] = proxies
        return requests.get(url, **kwargs)
