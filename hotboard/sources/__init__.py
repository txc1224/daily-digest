from hotboard.sources.weibo import WeiboFetcher
from hotboard.sources.zhihu import ZhihuFetcher
from hotboard.sources.baidu import BaiduFetcher
from hotboard.sources.bilibili import BilibiliFetcher
from hotboard.sources.hackernews import HackerNewsFetcher
from hotboard.sources.github import GitHubFetcher
from hotboard.sources.v2ex import V2exFetcher
from hotboard.sources.reddit import RedditFetcher
from hotboard.sources.douyin import DouyinFetcher
from hotboard.sources.toutiao import ToutiaoFetcher
from hotboard.sources.kr36 import Kr36Fetcher
from hotboard.sources.weixin import WeixinFetcher
from hotboard.sources.producthunt import ProductHuntFetcher
from hotboard.sources.twitter import TwitterFetcher
from hotboard.sources.sspai import SspaieFetcher
from hotboard.sources.pojie52 import Pojie52Fetcher
from hotboard.sources.juejin import JuejinFetcher

ALL_FETCHERS = {
    "weibo": WeiboFetcher,
    "zhihu": ZhihuFetcher,
    "baidu": BaiduFetcher,
    "bilibili": BilibiliFetcher,
    "hackernews": HackerNewsFetcher,
    "github": GitHubFetcher,
    "v2ex": V2exFetcher,
    "reddit": RedditFetcher,
    "douyin": DouyinFetcher,
    "toutiao": ToutiaoFetcher,
    "kr36": Kr36Fetcher,
    "weixin": WeixinFetcher,
    "producthunt": ProductHuntFetcher,
    "twitter": TwitterFetcher,
    "sspai": SspaieFetcher,
    "pojie52": Pojie52Fetcher,
    "juejin": JuejinFetcher,
}
