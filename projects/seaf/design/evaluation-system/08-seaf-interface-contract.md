# 智能体评测系统 - Seaf 外部接口契约

> 文档版本：V1.0  
> 日期：2026-04-20  
> 状态：待确认（需 Seaf 侧确认接口可用性）

---

## 一、概述

### 1.1 目的

本文档定义评测系统依赖的 Seaf 平台外部接口契约。包括：

1. **推理智能体对话接口** — 调用推理智能体，获取响应和工具调用日志
2. **工作流执行接口** — 触发工作流，获取执行结果和节点日志
3. **编排智能体接口** — 调用编排智能体，获取完整调用链日志
4. **智能体信息查询接口** — 获取智能体配置信息

### 1.2 接口依赖矩阵

| 接口 | 用途 | 依赖方 | 优先级 |
|------|------|--------|--------|
| `POST /seaf/api/chat/agent_ask` | 推理智能体对话 | 推理评测器 | P0 |
| `POST /seaf/api/workflow/execute` | 工作流触发 | 工作流评测器 | P0 |
| `GET /seaf/api/workflow/execution/{id}` | 工作流状态/结果查询 | 工作流评测器 | P0 |
| `POST /seaf/api/chat/orchestration_ask` | 编排智能体对话+调用链 | 编排评测器 | P0 |
| `GET /seaf/api/agents/{id}` | 查询智能体信息 | 评测执行器 | P1 |

### 1.3 通用说明

| 项目 | 说明 |
|------|------|
| **基础 URL** | Seaf 平台部署地址，由配置注入 |
| **认证方式** | `Authorization: Bearer <token>` |
| **Content-Type** | `application/json` |
| **字符编码** | UTF-8 |
| **错误处理** | HTTP 4xx/5xx 均视为调用失败，记录 error_message |

---

## 二、推理智能体对话接口

### 2.1 接口定义

**请求**
```
POST /seaf/api/chat/agent_ask
```

**请求头**

| 字段 | 值 | 说明 |
|------|-----|------|
| Authorization | Bearer {token} | Seaf 平台认证 Token |
| Content-Type | application/json | 请求体格式 |

**请求 Body**

| 字段 | 类型 | 必填 | 说明 |
|------|------|------|------|
| agent_id | int | 是 | 智能体 ID |
| message | string | 是 | 用户问题 |
| stream | bool | 否 | 是否流式返回，默认 false。评测系统必须使用 false |
| session_id | string | 否 | 会话 ID（多轮对话场景） |
| context | array | 否 | 历史消息上下文 |

**最小请求示例**
```json
{
  "agent_id": 1001,
  "message": "请问你们的退换货政策是什么？",
  "stream": false
}
```

**完整请求示例（多轮）**
```json
{
  "agent_id": 1001,
  "message": "那退货需要带什么材料？",
  "stream": false,
  "session_id": "sess-xxx-001",
  "context": [
    {"role": "user", "content": "请问你们的退换货政策是什么？"},
    {"role": "assistant", "content": "我们支持7天无理由退货..."}
  ]
}
```

**响应（200 OK）**

| 字段 | 类型 | 说明 |
|------|------|------|
| code | int | 状态码，0=成功，非0=失败 |
| message | string | 错误信息 |
| data | object | 响应数据 |

**data 字段结构**

| 字段 | 类型 | 说明 |
|------|------|------|
| session_id | string | 会话 ID |
| response | string | 最终回答文本 |
| messages | array | 消息列表（见下方消息结构） |
| latency_ms | int | 总耗时（毫秒） |

**消息列表（messages）结构**

评测系统通过解析 `messages` 提取工具调用日志。消息类型如下：

| type 值 | 说明 | 关键字段 |
|---------|------|----------|
| `user` | 用户消息 | content |
| `assistant` | LLM 回答片段 | content, tool_calls（如果有） |
| `mcp_tool_request` | 工具调用请求 | tool_name, arguments, request_id |
| `mcp_tool_response` | 工具调用结果 | request_id, result, status, latency_ms |
| `mcp_tool_error` | 工具调用错误 | request_id, error, error_code |
| `answer` | 最终回答（部分场景） | content |

**响应示例**
```json
{
  "code": 0,
  "message": "success",
  "data": {
    "session_id": "sess-xxx-001",
    "response": "我们的退换货政策是支持7天无理由退货，运费由买家承担。",
    "messages": [
      {
        "type": "user",
        "content": "请问你们的退换货政策是什么？"
      },
      {
        "type": "mcp_tool_request",
        "tool_name": "knowledge_retrieval",
        "arguments": {"query": "退换货政策"},
        "request_id": "req-001",
        "timestamp": "2026-04-20T10:00:00+08:00"
      },
      {
        "type": "mcp_tool_response",
        "request_id": "req-001",
        "result": "退换货政策：支持7天无理由退货...",
        "status": "success",
        "latency_ms": 150
      },
      {
        "type": "assistant",
        "content": "我们的退换货政策是支持7天无理由退货，运费由买家承担。"
      }
    ],
    "latency_ms": 1250
  }
}
```

**错误响应**
```json
{
  "code": 3002,
  "message": "Agent execution failed: timeout",
  "data": null
}
```

### 2.2 工具调用日志提取规则

评测系统从 `messages` 中提取工具调用日志的规则：

```
1. 遍历 messages
2. 找到 type=mcp_tool_request 的消息 → 记录 tool_name + arguments
3. 找到对应的 type=mcp_tool_response（按 request_id 匹配） → 记录 result + status + latency_ms
4. 若 request_id 不匹配，则以 mcp_tool_request 为准，status 标记为 unknown
5. 遍历 assistant 消息，若有 tool_calls 字段，记录工具调用意图
```

---

## 三、工作流执行接口

### 3.1 触发工作流执行

**请求**
```
POST /seaf/api/workflow/execute
```

**请求 Body**

| 字段 | 类型 | 必填 | 说明 |
|------|------|------|------|
| workflow_id | int | 是 | 工作流 ID（从 agent_config 中获取） |
| input | string | 是 | 用户输入/触发条件 |
| sync | bool | 否 | 是否同步执行。默认 false（异步），评测系统必须使用 false |

**请求示例**
```json
{
  "workflow_id": 2001,
  "input": "帮我处理订单20240618001的退款",
  "sync": false
}
```

**响应（200 OK）**

| 字段 | 类型 | 说明 |
|------|------|------|
| code | int | 状态码 |
| message | string | 错误信息 |
| data.execution_id | string | 执行 ID（用于后续轮询） |
| data.status | string | 初始状态（pending / running） |

**响应示例**
```json
{
  "code": 0,
  "message": "success",
  "data": {
    "execution_id": "exec-xxx-001",
    "status": "pending"
  }
}
```

### 3.2 查询工作流执行状态和结果

**请求**
```
GET /seaf/api/workflow/execution/{execution_id}
```

**路径参数**

| 字段 | 类型 | 说明 |
|------|------|------|
| execution_id | string | 执行 ID（由触发接口返回） |

**响应（200 OK）**

| 字段 | 类型 | 说明 |
|------|------|------|
| code | int | 状态码 |
| data.execution_id | string | 执行 ID |
| data.status | string | 执行状态 |
| data.node_log | array | 节点执行日志 |
| data.output | string | 工作流最终输出 |
| data.started_at | string | 开始时间（ISO 8601） |
| data.completed_at | string | 完成时间（ISO 8601） |
| data.total_latency_ms | int | 端到端总耗时（毫秒） |

**status 枚举值**

| 值 | 说明 |
|-----|------|
| `pending` | 等待执行 |
| `running` | 执行中 |
| `completed` | 执行完成 |
| `failed` | 执行失败 |
| `cancelled` | 已取消 |
| `timeout` | 执行超时 |

**node_log 节点日志结构**

| 字段 | 类型 | 说明 |
|------|------|------|
| node | string | 节点名称 |
| node_id | string | 节点 ID |
| status | string | 节点状态（success / failed / skipped / running） |
| latency_ms | int | 节点耗时（毫秒） |
| output | string | 节点输出（可选） |
| error | string | 错误信息（仅失败时） |
| started_at | string | 开始时间 |
| completed_at | string | 完成时间 |

**响应示例（执行中）**
```json
{
  "code": 0,
  "message": "success",
  "data": {
    "execution_id": "exec-xxx-001",
    "status": "running",
    "node_log": [
      {"node": "订单查询", "node_id": "node-001", "status": "completed", "latency_ms": 1200},
      {"node": "退款计算", "node_id": "node-002", "status": "running", "latency_ms": 0}
    ],
    "output": null,
    "started_at": "2026-04-20T10:00:00+08:00",
    "completed_at": null,
    "total_latency_ms": 1200
  }
}
```

**响应示例（已完成）**
```json
{
  "code": 0,
  "message": "success",
  "data": {
    "execution_id": "exec-xxx-001",
    "status": "completed",
    "node_log": [
      {
        "node": "订单查询",
        "node_id": "node-001",
        "status": "completed",
        "latency_ms": 1200,
        "output": "订单存在，当前状态：已发货"
      },
      {
        "node": "退款计算",
        "node_id": "node-002",
        "status": "completed",
        "latency_ms": 3500,
        "output": "退款金额：199元"
      },
      {
        "node": "退款执行",
        "node_id": "node-003",
        "status": "completed",
        "latency_ms": 2000,
        "output": "退款成功，退款单号：refund-xxx"
      },
      {
        "node": "通知用户",
        "node_id": "node-004",
        "status": "failed",
        "latency_ms": 500,
        "error": "短信网关超时"
      }
    ],
    "output": "订单退款处理完成，退款金额199元，已通知用户（短信发送失败）",
    "started_at": "2026-04-20T10:00:00+08:00",
    "completed_at": "2026-04-20T10:01:05+08:00",
    "total_latency_ms": 7200
  }
}
```

**响应示例（执行失败）**
```json
{
  "code": 3002,
  "message": "Workflow execution failed",
  "data": {
    "execution_id": "exec-xxx-001",
    "status": "failed",
    "error": "工作流执行失败: 退款接口返回错误码 E5001",
    "node_log": [
      {"node": "订单查询", "status": "completed", "latency_ms": 1200},
      {"node": "退款计算", "status": "failed", "latency_ms": 3500, "error": "余额不足"}
    ],
    "total_latency_ms": 4700
  }
}
```

### 3.3 工作流轮询策略

评测系统的工作流轮询策略：

```
触发工作流
    ↓
轮询 GET /workflow/execution/{execution_id}（间隔 5 秒）
    ↓
若 status in (completed, failed, cancelled, timeout) → 停止轮询
若 status = running → 继续轮询
若轮询次数 > 60（5 分钟）→ 停止轮询，标记为 timeout
```

---

## 四、编排智能体对话接口

### 4.1 接口定义

**请求**
```
POST /seaf/api/chat/orchestration_ask
```

**请求 Body**

| 字段 | 类型 | 必填 | 说明 |
|------|------|------|------|
| agent_id | int | 是 | 编排智能体 ID |
| message | string | 是 | 用户问题 |
| stream | bool | 否 | 是否流式，默认 false。评测系统必须使用 false |
| include_call_chain | bool | 是 | **必须为 true**，要求返回完整调用链 |
| session_id | string | 否 | 会话 ID |

**请求示例**
```json
{
  "agent_id": 3001,
  "message": "帮我分析这份竞品报告并给出建议",
  "stream": false,
  "include_call_chain": true
}
```

**响应（200 OK）**

| 字段 | 类型 | 说明 |
|------|------|------|
| code | int | 状态码 |
| message | string | 错误信息 |
| data.orchestration_id | string | 编排执行 ID |
| data.query | string | 用户原始问题 |
| data.pattern | string | 编排模式（sequential / parallel / conditional / loop / mixed） |
| data.sub_agent_calls | array | 子 Agent 调用列表 |
| data.final_response | string | 编排层最终回答 |
| data.total_latency_ms | int | 端到端总耗时 |

**sub_agent_calls 子 Agent 调用结构**

| 字段 | 类型 | 必填 | 说明 |
|------|------|------|------|
| call_id | int | ✅ | 调用序号（从 1 开始） |
| sub_agent_id | string | ✅ | 子 Agent 标识 |
| sub_agent_name | string | ✅ | 子 Agent 名称（人类可读） |
| input | string | ✅ | 传递给子 Agent 的输入 |
| output | string | ✅ | 子 Agent 的文本输出 |
| status | string | ✅ | success / failed / timeout |
| latency_ms | int | ✅ | 耗时（毫秒） |
| tool_calls | array | ⚠️ | 子 Agent 内部的工具调用日志（可选） |

**tool_calls 子 Agent 内部工具调用结构**

| 字段 | 类型 | 说明 |
|------|------|------|
| tool_name | string | 工具名称 |
| arguments | object | 工具参数 |
| status | string | success / failed |
| latency_ms | int | 耗时（毫秒） |

**响应示例**
```json
{
  "code": 0,
  "message": "success",
  "data": {
    "orchestration_id": "orch-xxx-001",
    "query": "帮我分析这份竞品报告并给出建议",
    "pattern": "sequential",
    "sub_agent_calls": [
      {
        "call_id": 1,
        "sub_agent_id": "doc-parser",
        "sub_agent_name": "文档解析Agent",
        "input": "用户上传的竞品报告PDF",
        "output": "解析后的文本内容，共5页，介绍了竞品A/B/C的市场策略...",
        "status": "success",
        "latency_ms": 1200,
        "tool_calls": [
          {"tool_name": "pdf_parser", "arguments": {"file_path": "/tmp/report.pdf"}, "status": "success", "latency_ms": 800}
        ]
      },
      {
        "call_id": 2,
        "sub_agent_id": "data-analyst",
        "sub_agent_name": "数据分析Agent",
        "input": "竞品报告文本内容",
        "output": "SWOT分析：竞品A优势在价格，劣势在功能...",
        "status": "success",
        "latency_ms": 3500,
        "tool_calls": [
          {"tool_name": "knowledge_retrieval", "arguments": {"query": "竞品分析方法论"}, "status": "success", "latency_ms": 200}
        ]
      },
      {
        "call_id": 3,
        "sub_agent_id": "report-generator",
        "sub_agent_name": "报告生成Agent",
        "input": "SWOT分析结果",
        "output": "综合分析报告...",
        "status": "success",
        "latency_ms": 2000,
        "tool_calls": []
      }
    ],
    "final_response": "【竞品分析报告】...\n【建议】...",
    "total_latency_ms": 6700
  }
}
```

### 4.2 错误响应
```json
{
  "code": 3002,
  "message": "Orchestration execution failed: 子Agent数据分析师调用超时",
  "data": {
    "orchestration_id": "orch-xxx-001",
    "sub_agent_calls": [
      {"call_id": 1, "status": "success"},
      {"call_id": 2, "status": "timeout"}
    ],
    "final_response": "抱歉，分析过程中遇到问题...",
    "total_latency_ms": 30000
  }
}
```

---

## 五、智能体信息查询接口

### 5.1 查询智能体详情

**请求**
```
GET /seaf/api/agents/{agent_id}
```

**响应**
```json
{
  "code": 0,
  "message": "success",
  "data": {
    "id": 1001,
    "name": "客服智能体",
    "agent_type": "reasoning",
    "description": "用于处理用户咨询的智能客服",
    "config": {
      "model": "deepseek-chat",
      "prompt_template": "你是一个专业的客服...",
      "tools": ["knowledge_retrieval", "order_query"],
      "workflow_id": null,
      "orchestration_config": null
    },
    "version": "v1.2.3",
    "status": "online",
    "created_at": "2026-03-01T10:00:00+08:00"
  }
}
```

---

## 六、接口可用性检查清单

| 接口 | 检查项 | 状态 |
|------|--------|------|
| `POST /seaf/api/chat/agent_ask` | 是否支持 `stream=false` 并返回完整 messages 列表 | ⬜ 待确认 |
| `POST /seaf/api/chat/agent_ask` | messages 中是否包含 `mcp_tool_request` / `mcp_tool_response` 类型 | ⬜ 待确认 |
| `POST /seaf/api/workflow/execute` | `sync=false` 是否返回 execution_id | ⬜ 待确认 |
| `GET /seaf/api/workflow/execution/{id}` | 是否返回 node_log（节点耗时 + 状态） | ⬜ 待确认 |
| `POST /seaf/api/chat/orchestration_ask` | Seaf 编排智能体是否支持 `include_call_chain=true` | ⬜ **重要：需补充开发** |
| `GET /seaf/api/agents/{id}` | 是否返回 config（包含 tools、workflow_id 等） | ⬜ 待确认 |

---

## 七、接口降级策略

当 Seaf 接口不可用时，评测系统的降级策略：

| 场景 | 降级策略 |
|------|----------|
| 单次调用超时 | 重试 3 次，间隔 2s/4s/8s（指数退避） |
| 连续调用失败（>50%） | 标记该智能体评测任务为"环境异常"，暂停后续评测 |
| 接口格式不匹配 | 记录原始响应，降级为"人工复核"模式 |

---

*文档状态：待 Seaf 侧确认接口可用性*

*关键待确认项：编排智能体的 `include_call_chain=true` 参数需要 Seaf 侧补充开发。*
