import requests as _requests
from bs4 import BeautifulSoup
from hotboard.sources.base import BaseFetcher
from hotboard.models import HotItem


class Pojie52Fetcher(BaseFetcher):
    platform = "pojie52"
    platform_name = "吾爱破解"
    icon = "🔓"
    group = "tech"
    source_url = "https://www.52pojie.cn/"

    def fetch(self) -> list[HotItem]:
        url = "https://www.52pojie.cn/forum.php?mod=guide&view=hot"
        headers = {
            "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) "
                          "AppleWebKit/537.36 (KHTML, like Gecko) "
                          "Chrome/120.0.0.0 Safari/537.36",
            "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
            "Accept-Language": "zh-CN,zh;q=0.9",
        }
        # 直接用 requests 避免代理干扰，52pojie 是国内站不需要代理
        r = _requests.get(url, headers=headers, timeout=15)
        r.raise_for_status()
        r.encoding = r.apparent_encoding or "gbk"
        soup = BeautifulSoup(r.text, "html.parser")

        items = []
        links = soup.select("a.xst")
        for i, a in enumerate(links[:20]):
            title = a.get_text(strip=True)
            if not title:
                continue
            href = a.get("href", "")
            if href and not href.startswith("http"):
                href = f"https://www.52pojie.cn/{href}"

            hot_value = ""
            tbody = a.find_parent("tbody")
            if tbody:
                num_td = tbody.select_one("td.num")
                if num_td:
                    parts = []
                    view_em = num_td.select_one("em")
                    reply_a = num_td.select_one("a")
                    if view_em:
                        parts.append(f"{view_em.get_text(strip=True)} 查看")
                    if reply_a:
                        parts.append(f"{reply_a.get_text(strip=True)} 回复")
                    hot_value = " · ".join(parts)

            items.append(HotItem(
                rank=i + 1,
                title=title,
                url=href,
                hot_value=hot_value,
            ))
        return items
