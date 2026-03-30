# Daily Digest

每日信息聚合工具，包含两大功能模块：

1. **每日简报** — 天气、股市、新闻、GitHub Trending 等聚合推送到飞书
2. **HotBoard 热榜看板** — 全网热榜聚合，支持本地实时看板 + GitHub Pages 静态站

---

## 每日简报

定时推送综合信息简报到飞书，包含：

- 天气预报
- 股市行情（A股/港股/美股）、大宗商品、汇率、国债/VIX
- 时事/科技/开发者新闻（AI 摘要 + 翻译）
- GitHub Trending、Product Hunt
- 热点聚类、情感分析

```bash
# 完整简报
python main.py --mode daily

# 股市简报
python main.py --mode stock-morning    # A股开盘
python main.py --mode stock-afternoon  # 港股收盘
python main.py --mode stock-evening    # 美股收盘

# 股票/板块分析
python main.py --mode stock-analysis --stock-code AAPL --market US
python main.py --mode stock-analysis --sector 科技 --market US
```

## HotBoard 热榜看板

全网热榜聚合，覆盖多个平台：

| 分组 | 平台 |
|------|------|
| 🇨🇳 国内平台 | 微博热搜、知乎热榜、百度热搜、B站热门 |
| 💻 技术社区 | GitHub Trending、HackerNews、V2EX |
| 🌍 海外平台 | Reddit |

### 本地模式（实时）

```bash
pip install -r requirements.txt
python -m hotboard.app
# → http://localhost:8000
```

- 实时抓取 + 5 分钟缓存
- 自动刷新 + 手动刷新
- 定时推送热榜摘要到飞书

海外平台需代理，在 `.env` 中配置：

```
HOTBOARD_PROXY=http://127.0.0.1:7890
```

### 线上模式（GitHub Pages）

GitHub Actions 每天 3 次（08:00 / 13:00 / 19:00 北京时间）自动抓取数据，生成静态 JSON，部署到 GitHub Pages。

```bash
# 本地手动生成
python generate.py
# → docs/api/boards.json
```

**部署步骤：**

1. 推送到 GitHub
2. Settings → Pages → Source 选 `main` 分支 `/docs` 目录
3. Actions 页面手动触发一次 `Update HotBoard`

GitHub Actions 运行在国际节点，无需代理即可访问所有平台。

---

## 环境配置

```bash
# 创建虚拟环境
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt

# 复制环境变量
cp .env.example .env
# 编辑 .env 填入 FEISHU_WEBHOOK 等配置
```

## 项目结构

```
daily-digest/
├── main.py              # 每日简报入口
├── generate.py          # 热榜静态数据生成
├── sender.py            # 飞书推送
├── formatter.py         # 飞书卡片构建
├── fetchers/            # 每日简报数据源
├── ai/                  # AI 增强（摘要/翻译/聚类/情感）
├── hotboard/            # 热榜看板模块
│   ├── app.py           # FastAPI 本地看板
│   ├── sources/         # 各平台 fetcher
│   ├── static/          # 前端资源
│   └── templates/       # Jinja2 模板
├── docs/                # GitHub Pages 静态站
│   ├── index.html
│   └── api/boards.json
└── .github/workflows/   # GitHub Actions
```
