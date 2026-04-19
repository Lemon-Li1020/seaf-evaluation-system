# Seaf 项目跟进

## 当前迭代

| 项目 | 信息 |
|------|------|
| 版本号 | 3.0.6.510 |
| 阶段 | 开发联调阶段 |
| 本期交付节点 | **5.10 交付本期需求** |

## 平台进度 & 交付规则

| 平台 | 状态 | 备注 |
|------|------|------|
| 开发平台（构建侧） | 开发联调中 | **先完成** |
| 用户平台 | 开发联调中 | 有依赖 |
| 管理平台 | 开发联调中 | 有依赖 |

**交付标准**：三个平台**必须都完成**才算本期交付，三个平台**互相有依赖**

**依赖关系**：构建侧（开发平台）先完成 → 用户平台/管理平台依赖 → 联调 → 交付

## 文档归档（2026-04-19）

已整理以下文档：

| 文件 | 内容 |
|------|------|
| `docs/test-environment.md` | 测试环境说明（环境地址/账户/中间件/日志） |
| `docs/suggestion-logic.md` | 推荐问题逻辑（is_suggestion 字段） |
| `docs/website-embed-test.md` | 网站嵌入 SDK 测试方法 |
| `docs/changelog.md` | 各版本提测变更总览（0815～V3.0.6.0510，共 11 个版本） |
| `docs/deployment-license.md` | agents-license 部署流程 |
| `docs/qpaas-scripts.md` | QPaaS GUI 侧部署脚本（6 个 feat） |
| `docs/mcp-process.md` | MCP / Skill 发布/下架/审核流程、前后端 API 交互逻辑 |
| `docs/agent-detail-tabs.md` | 智能体详情页 4 个 Tab 功能说明（日志模块完整，编排/发布/运营待补充） |
| `docs/ai-forums.md` | AI 行业论坛订阅清单 + 抓取策略（已验证可访问渠道） |
| `docs/agent-evaluation-system-requirements.md` | 通用智能体评测系统需求规格说明书（完整版） |
| `docs/agent-evaluation-system-requirements-mvp.md` | 通用智能体评测系统需求规格说明书（MVP 版：推理+工作流） |
| `design/evaluation-system/` | 智能体评测系统研发设计文档（6 个子文档） |

**评测系统设计文档（design/evaluation-system/）：**

| 文件 | 内容 |
|------|------|
| `README.md` | 文档索引 |
| `01-architecture.md` | 总体技术方案（架构图、技术选型、部署方案） |
| `02-database.md` | 数据库设计（表结构、ER图、索引、迁移脚本） |
| `03-api.md` | API 接口设计（评测集/任务/报告/配置 API） |
| `04-evaluator.md` | 评测器设计（推理/工作流评测器、执行器、代码示例） |
| `05-llm-judge.md` | LLM 评委服务设计（Prompt模板、响应解析、降级策略） |
| `06-celery-tasks.md` | 异步任务设计（Celery配置、任务定义、Docker/K8s部署） |

**Skills：**

| 文件 | 内容 |
|------|------|
| `skills/seaf-testing-guide/` | Seaf 测试方法指南 skill（含竞品测试方案、行业测试方法论、每周 AI 热点抓取逻辑） |
| `skills/seaf-competitive-analysis/` | Seaf 竞品分析 skill（含 Coze/Dify/Diffy/FastGPT 等平台信息） |

---

## 团队

| 角色 | 人数 |
|------|------|
| 产品经理 | 3 人 |
| 开发人员 | ~20 人 |
| 测试人员 | 5 人 |

**迭代周期**：每月一次

**当前状态**：开发联调阶段，测试文档正在收集整理

---

*最后更新：2026-04-19*
