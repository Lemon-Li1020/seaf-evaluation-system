---
name: seaf-testing-guide
description: Seaf 智能体工厂测试方法与测试要点分析。用于：(1) 制定 Seaf 平台各模块（智能体/MCP/Skill/知识库/插件）的测试策略和用例设计；(2) 分析 AI Agent 平台行业通用的测试方法论；(3) 对比 Coze/Dify 等竞品的测试方案；(4) 每周一早上 8:30 自动汇总 AI 行业论坛最热话题并推送给用户。触发场景包括：用户要求分析测试方法、设计测试用例、制定测试计划、了解竞品测试方案、订阅每周 AI 热点推送等。
---

# Seaf 测试方法指南

## 测试分层架构

Seaf 平台按以下层次组织测试：

| 层次 | 测试对象 | 测试重点 |
|------|----------|----------|
| **功能测试** | 各模块基础功能 | 功能正确性、边界条件 |
| **接口测试** | 各层 API | 请求/响应契约、异常处理 |
| **集成测试** | 跨模块联动 | 构建侧↔用户侧↔管理侧 |
| **端到端测试** | 用户实际使用路径 | 完整业务流程 |
| **安全测试** | 权限/鉴权/越权 | 空间隔离、越权访问 |

## 各模块测试要点

### 1. 智能体（Agent）

详见 `references/agent-testing.md`

### 2. MCP

- **发布流程**：仅本空间（免审/非免审）/ 全部空间（必须审核）
- **下架流程**：管理侧下架 → 构建侧状态变为「未发布」
- **审核流程**：待审核 → 通过 / 拒绝 → 重新发布
- **详情页**：`publish_status=2` 时显示发布按钮

测试覆盖：`template_check_status` 各状态流转

### 3. Skill

与 MCP 审核流程完全一致，测试要点复用 MCP。

### 4. 知识库

- 上传/删除文档
- 知识库与智能体关联
- RAG 检索质量（答案相关性）

### 5. 插件

- 插件挂载/卸载
- 插件调用链路
- 插件异常处理

### 6. 日志模块

- 调用日志列表展示
- 「日志」回放功能
- 「执行链」Langfuse 链接
- 用户名称为空兜底（API调用/分享链接/用户侧）

## 测试用例设计原则

- **等价类划分**：正常/异常/边界
- **状态机覆盖**：所有 `template_check_status` 状态流转（见 agent-testing.md）
- **权限矩阵**：不同角色（开发者/用户/管理员）的功能可见性
- **依赖隔离**：三个平台测试需考虑联调依赖

## 竞品测试方案参考

详见 `references/competitor-testing.md`

## 每周 AI 热点推送

每周一 8:30 自动推送，参考 `references/ai-forums.md` 中的可访问渠道抓取。

### 推送内容格式

```
🌐 AI 行业周报 | [日期]

📄 arXiv 最新论文（cs.AI）
1. [论文标题] arXiv:XXXX.XXXXX
   摘要：[取前100词]...
   🔗 https://arxiv.org/abs/XXXXX

💻 GitHub Trending（本周 AI 类）
1. [仓库名] ⭐ XX,XXX | ⬆️ +XX,XXX this week
   [描述]
   🔗 https://github.com/xxx/xxx

📝 Towards Data Science
1. [文章标题] · X min read
   [简介]
   🔗 [链接]
```

### 抓取渠道优先级

1. arXiv cs.AI — 每日新论文，关键词：agent / llm / mcp / tool / benchmark
2. GitHub Trending — 本周 AI 类仓库
3. Towards Data Science — AI 相关文章

详见 `references/ai-forums.md`
