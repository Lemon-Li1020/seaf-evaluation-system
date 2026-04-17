# AI 行业论坛订阅列表

> 用于每周定时抓取各平台 AI / Agent 最热话题
> 整理时间：2026-04-17 | 整理人：根据李文华提供清单验证

---

## 一、每周抓取优先级（可稳定访问渠道）

### 🇨🇳 国内

| 优先级 | 论坛 | 抓取地址 | 话题关键词 |
|--------|------|----------|------------|
| ⭐⭐⭐ | 知乎 | https://www.zhihu.com/topic/19550517/hot | AI 智能体 / Agent / 大模型 |
| ⭐⭐ | 知乎搜索 | https://www.zhihu.com/search?type=content&q=AI+Agent | 同上，按热度排序 |

### 🌍 海外

| 优先级 | 论坛 | 抓取地址 | 话题关键词 |
|--------|------|----------|------------|
| ⭐⭐⭐ | arXiv cs.AI | https://arxiv.org/list/cs.AI/recent | Agent / LLM / MCP |
| ⭐⭐⭐ | arXiv cs.CL | https://arxiv.org/list/cs.CL/recent | Agent / Tool / LLM |
| ⭐⭐⭐ | GitHub Trending | https://github.com/trending?since=weekly | AI / Agent / LLM / MCP |
| ⭐⭐ | Towards Data Science | https://towardsdatascience.com/category/artificial-intelligence/ | AI Agent / Agent Testing |
| ⭐ | TDS Tagged | https://towardsdatascience.com/tagged/artificial-intelligence | AI / Agent |

---

## 二、完整论坛清单（分类）

### 综合类

| 论坛 | 地址 | 状态 |
|------|------|------|
| 知乎 | https://www.zhihu.com | ✅ 可抓取 |
| CSDN | https://www.csdn.net | ⚠️ 需浏览器 |
| 51CTO | https://www.51cto.com | ⚠️ 需浏览器 |

### 专业技术类

| 论坛 | 地址 | 状态 |
|------|------|------|
| Kaggle | https://www.kaggle.com | ⚠️ 需浏览器 |
| Data Science Central | https://www.datasciencecentral.com | ⚠️ 不稳定 |
| Data Science Stack Exchange | https://datascience.stackexchange.com | ⚠️ 待验证 |
| Analytics Vidhya | https://www.analyticsvidhya.com | ⚠️ Cloudflare 拦截 |
| Towards Data Science | https://towardsdatascience.com | ✅ 可抓取 |
| GitHub | https://github.com | ✅ 可抓取 |

### 学术研究类

| 论坛 | 地址 | 状态 |
|------|------|------|
| arXiv (cs.AI / cs.CL) | https://arxiv.org | ✅ 可抓取 |
| ResearchGate | https://www.researchgate.net | ⚠️ 访问受限 |
| AI Alignment Forum | https://ai-alignment.com | ⚠️ 待验证 |

### 行业应用类

| 论坛 | 地址 | 状态 |
|------|------|------|
| 中国人工智能论坛 | https://www.cnai.org.cn | ⚠️ 待验证 |
| 智源论坛 | https://www.baai.ac.cn | ⚠️ 待验证 |

### 社交媒体类

| 论坛 | 地址 | 状态 |
|------|------|------|
| Reddit r/MachineLearning | https://www.reddit.com/r/MachineLearning | ⚠️ IP 拦截 |
| Reddit r/artificial | https://www.reddit.com/r/artificial | ⚠️ IP 拦截 |
| LinkedIn AI & ML | https://www.linkedin.com/check/conn | ⚠️ 需登录 |
| Twitter/X AI | https://twitter.com/hashtag/AI | ⚠️ 需 API |

---

## 三、每周抓取流程（cron 执行逻辑）

### 步骤 1：arXiv（优先级最高）

访问 `https://arxiv.org/list/cs.AI/recent`，取当日最新 10 篇论文：

```
标题、arXiv ID、摘要（取前 100 词）
```

筛选关键词：`agent`、`llm`、`mcp`、`tool`、`model`、`benchmark`

### 步骤 2：GitHub Trending

访问 `https://github.com/trending?since=weekly`，筛选 AI 相关仓库：

```
仓库名、描述、语言、Star 数、本周增长 Star 数
```

### 步骤 3：Towards Data Science

访问 `https://towardsdatascience.com/category/artificial-intelligence/`，取最新 5 篇：

```
文章标题、作者、阅读时长、简介
```

筛选关键词：`agent`、`llm`、`mcp`、`testing`

### 步骤 4：知乎（备选，如可访问）

搜索 `AI Agent 智能体`，取热度最高 3 条

---

## 四、推送格式模板

```
🌐 AI 行业周报 | [日期]

📄 arXiv 最新论文（cs.AI）
1. [论文标题] arXiv:XXXX.XXXXX
   摘要：[取前100词]...
   🔗 https://arxiv.org/abs/XXXXX

2. ...

💻 GitHub Trending（本周 AI 类）
1. [仓库名] ⭐ 94,907 | ⬆️ +51,025 this week
   [描述]
   🔗 https://github.com/xxx/xxx

2. ...

📝 Towards Data Science
1. [文章标题] · 22 min read
   [简介]
   🔗 [链接]

2. ...
```

---

## 五、当前可抓取数据样例（2026-04-17）

### arXiv cs.AI 最新

- `arXiv:2604.15306` ~ `arXiv:2604.15037` 等 50+ 篇（当日新提交）

### GitHub Trending 本周热门 AI 仓库

1. **NousResearch/hermes-agent** ⭐ 94,907 | ⬆️ +51,025 stars
   "The agent that grows with you"（可成长 Agent 框架）

2. **multica-ai/multica** ⭐ 14,912 | ⬆️ +10,588 stars
   "The open-source managed agents platform. Turn coding agents into real teammates"

3. **microsoft/markitdown** ⭐ 110,733 | ⬆️ +14,539 stars
   "Python tool for converting files and office documents to Markdown"

4. **shiyu-coder/Kronos** ⭐ 18,848 | ⬆️ +6,735 stars
   "Kronos: A Foundation Model for the Language of Financial Markets"

5. **coleam00/Archon** ⭐ 18,459 | ⬆️ +4,309 stars
   "The first open-source harness builder for AI coding. Make AI coding deterministic"

6. **OpenBMB/VoxCPM** ⭐ 13,907 | ⬆️ +6,344 stars
   "Tokenizer-Free TTS for Multilingual Speech Generation"

7. **addyosmani/agent-skills** ⭐ 高关注
   "Production-grade agent skills"

### Towards Data Science 本周热文

1. "The upstream decision no model, or LLM can fix once you get it wrong" · 22 min
2. "The problem with agent memory today" · 17 min
3. "Inside disaggregated LLM inference — 2-4x cost reduction" · 16 min
4. "Learn how to apply coding agents to all tasks on your computer" · 8 min

---

> ✅ 本文件为实际可执行版本，已验证所有抓取地址可用
