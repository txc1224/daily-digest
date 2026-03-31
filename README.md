# Daily Digest

每日信息聚合工具，当前以 HotBoard 驱动的摘要推送和热榜看板为主，包含两大模块：

1. **HotBoard Brief** — 基于全网热榜聚合结果生成飞书日摘要
2. **HotBoard 热榜看板** — 全网热榜聚合，支持本地实时看板 + GitHub Pages 静态站

旧版完整日报仍然保留为手动可用的 `full-daily` 模式，适合作为补充而不是主推送链路。

---

## HotBoard Brief

默认定时推送的是基于 HotBoard 的飞书日摘要，强调快速扫读而不是大而全汇总，主要包含：

- 跨平台热点
- 技术社区精选
- 国内平台精选
- 海外平台精选
- 抓取异常和平台健康状态

```bash
# HotBoard 日摘要
python main.py --mode hotboard-brief

# 完整简报
python main.py --mode full-daily

# GitHub Actions 手动触发
# daily.yml 可选 hotboard-brief 或 full-daily
# hotboard-brief 是默认定时模式
# full-daily 会执行旧版完整日报
# 兼容旧命令：
# python main.py --mode daily
# python main.py --mode hotboard-daily
```

## Full Daily

旧版完整日报仍可手动执行，包含：

- 天气预报
- 股市行情（A股/港股/美股）、大宗商品、汇率、国债/VIX
- 时事/科技/开发者新闻（AI 摘要 + 翻译）
- GitHub Trending、Product Hunt
- 热点聚类、情感分析

```bash
python main.py --mode full-daily
```

## 其他模式

```bash

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

## GitHub Actions

- `Daily Brief`：每天 08:00 发送 `hotboard-brief`，手动触发时可切换为 `full-daily`
- `Update HotBoard`：每天 3 次更新 `docs/api/boards.json` 和历史快照
- `Tests`：在 `push` / `pull_request` 时运行 `pytest tests`
- `Stock Market - A股开盘 / 港股收盘 / 美股收盘`：已暂停自动调度，仅保留手动触发
- `股票/板块分析报告`：手动分析指定股票或板块

---

## 环境配置

```bash
# 创建虚拟环境
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt

# 安装开发/测试依赖
pip install -r requirements-dev.txt

# 复制环境变量
cp .env.example .env
# 编辑 .env 填入 FEISHU_WEBHOOK 等配置
```

## 测试

```bash
source .venv/bin/activate
pytest tests
```

## 项目结构

```
daily-digest/
├── main.py              # CLI 入口（hotboard-brief / full-daily / stock-*）
├── generate.py          # HotBoard 静态数据生成
├── daily_digest_pipeline.py  # 旧版完整日报 pipeline
├── sender.py            # 飞书推送
├── formatter.py         # 完整日报/股市卡片构建
├── fetchers/            # 数据源抓取
├── ai/                  # AI 增强（摘要/翻译/聚类/情感）
├── hotboard/            # 热榜看板模块
│   ├── app.py           # FastAPI 本地看板
│   ├── status.py        # 平台抓取状态记录
│   ├── sources/         # 各平台 fetcher
│   ├── static/          # 前端资源
│   └── templates/       # Jinja2 模板
├── docs/                # GitHub Pages 静态站
│   ├── index.html
│   └── api/boards.json
└── .github/workflows/   # GitHub Actions
```
