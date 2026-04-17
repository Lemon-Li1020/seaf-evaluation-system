# Seaf 竞品周报

> 整理时间：2026-04-17（第 1 期）

---

## 【ToC 智能体助手】

### 📌 豆包（字节跳动）
近一周在抖音生态内持续发力，AI 对话能力与短视频场景深度融合，卡片式交互进一步优化，语音交互响应速度提升。

### 📌 Kimi（月之暗面）
持续强化长上下文能力，128K 上下文窗口稳固其技术护城河，近期在学术文献分析场景获得大量用户好评。

### 📌 DeepSeek
开源模型 DeepSeek-V3 / R1 热度持续，吸引大量开发者基于其 API 构建应用，价格优势明显，在中小企业中快速渗透。

### 📌 ChatGPT / Claude
ChatGPT 本周开放了 GPT-4o 图像生成功能的 API 调用；Claude 持续在代码生成和长文档分析上迭代强化，Anthropic 发布 Claude 3.7 Sonnet 更新。

### 📌 通义千问（阿里）
千问 3.0 在阿里云全面上线，Agent 工具调用能力显著增强，与阿里云函数计算深度集成，企业级 API 能力持续补强。

---

## 【ToB 智能体工厂】

### 📌 Dify — v1.13.3（3月27日）

本周稳定维护更新，核心改进：
- **新功能**：LLM / Question Classifier / Variable Extractor 节点支持变量引用参数配置，工作流编排灵活性大幅提升
- **Bug 修复**：流式输出稳定性、循环/迭代节点粘贴行为、HTTP Request 执行重试逻辑
- **RAG**：引用元数据保留、切片预览恢复、检索命中计数过滤修复

🔗 https://github.com/langgenius/dify/releases

### 📌 FastGPT — v4.14.10.2（4月10日）

本周重点更新：
- **Agent Sandbox**：新增 Agent 沙箱配置，支持代码节点隔离执行，安全性提升
- **Skill 开发**：正式合入 Skill 测试代码，FastGPT 开始支持 Agent Skill 能力
- **Bug 修复**：Chat Agent 模型被重置问题、aiproxy 地址协议
- **运维优化**：Docker Compose 配置规范化、命名一致性改进

🔗 https://github.com/labring/fastgpt/releases

### 📌 LangFlow

本周新增支持将 Flow 导出为 MCP Server，成为 LangChain 生态内 MCP 化的重要里程碑。

---

## 【GitHub Trending 本周 AI 类热点】

### 💻 NousResearch / hermes-agent ⭐ 95,050 | ⬆️ +51,025 ⬆️
「The agent that grows with you」—— 可持续学习进化的 Agent 框架，本周暴涨，继续领跑 AI Agent 类仓库。

### 💻 multica-ai / multica ⭐ 14,946 | ⬆️ +10,588 ⬆️
「开源托管 Agent 平台」—— 把编码 Agent 变成真正的团队成员，支持任务分配与技能积累。

### 💻 microsoft / markitdown ⭐ 110,763 | ⬆️ +14,539 ⬆️
微软出品，文件转 Markdown 利器，支持 Office 全家桶，开发神器。

### 💻 addyosmani / agent-skills ⭐ 高关注
Google 前工程师出品，「生产级 Agent Skills」合集。

---

## 【Seaf 机会点】

### 💡 1. Skill 能力追上 FastGPT
FastGPT 本周已合入 Skill 开发代码，Seaf 的 Skill 审核流程需尽快完善并上线，这是直接对标点。

### 💡 2. Agent 沙箱安全性
FastGPT 引入 Agent Sandbox 隔离执行，Seaf 如有多步执行场景，应关注代码执行安全问题。

### 💡 3. 可进化 Agent 是大趋势
hermes-agent 的「Agent 持续学习」+ multica 的「Agent 团队协作」代表今年 Agent 核心方向，Seaf 智能体编排 Tab 需要在规划阶段考虑这类能力。

### 💡 4. MCP 生态已成标配
LangFlow 已支持 Flow → MCP Server 导出，Dify/FastGPT 也在跟进，Seaf 的 MCP 发布审核体系是差异化资产，需持续强化 MCP 生态建设。

---

*数据来源：GitHub Releases / Trending / 公开报道 | 2026-04-17*
