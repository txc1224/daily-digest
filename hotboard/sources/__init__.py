from hotboard.sources.weibo import WeiboFetcher
from hotboard.sources.zhihu import ZhihuFetcher
from hotboard.sources.baidu import BaiduFetcher
from hotboard.sources.bilibili import BilibiliFetcher
from hotboard.sources.hackernews import HackerNewsFetcher
from hotboard.sources.github import GitHubFetcher
from hotboard.sources.v2ex import V2exFetcher
from hotboard.sources.reddit import RedditFetcher

ALL_FETCHERS = {
    "weibo": WeiboFetcher,
    "zhihu": ZhihuFetcher,
    "baidu": BaiduFetcher,
    "bilibili": BilibiliFetcher,
    "hackernews": HackerNewsFetcher,
    "github": GitHubFetcher,
    "v2ex": V2exFetcher,
    "reddit": RedditFetcher,
}
