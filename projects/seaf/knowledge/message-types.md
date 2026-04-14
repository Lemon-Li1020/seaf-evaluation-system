# Seaf 引擎消息类型说明

> 来源：问答接口消息字段说明
> 最后更新：2026-04-14

---

## 消息类型对照表

| 消息类型 | 引擎类型 | 说明 |
|----------|----------|------|
| `answer` | `result` | 问答结果（最终） |
| `answer_chunk` | `result_chunk` | 流式问答结果 |
| `deep_thinking` | `thinking` | 模型思考过程（最终） |
| `deep_thinking_chunk` | `thinking_chunk` | 流式模型思考过程 |
| `reasoning` | `text` | 正文，引擎的推理过程（最终） |
| `reasoning_chunk` | `text_chunk` | 流式正文 |
| `file` | `file` | 最后的文件产物 |
| `file_chunk` | `file_chunk` | 流式文件内容 |
| `mcp_call` | `mcp_tool_request` | MCP 请求 |
| `mcp_response` | `mcp_server_response` | MCP 响应结果 |
| `error` | `status[error]` | 引擎执行状态说明 - 错误 |
| `error` | `status[aborted]` | 引擎执行状态说明 - 取消 |

---

## Tool 类型消息

| 消息类型 | 引擎类型 | 说明 |
|----------|----------|------|
| `todolist` | `tool[updateTodoList]` | 方案确认 |
| `call_agent` | `tool[callAgent]` | agent 调用 |
| `followup` | `followup` | 需求确认 |
| `todolist_start` | `todolist_start` | 待办列表开始 |
| `followup_start` | `followup_start` | 跟进开始 |
| `tool_complete` | `tool_complete` | 工具完成 |
| `l4_state` | `l4_state` | L4 引擎状态 |

---

## GUI 弹窗类型

| 消息类型 | 引擎类型 | 说明 |
|----------|----------|------|
| `gui_popup` | `gui_popup` | 必弹卡片 |
| `gui_popup` | `gui_unpopup` | 非必弹卡片 |

---

## 任务重试类型

| 消息类型 | 引擎类型 | 说明 |
|----------|----------|------|
| `task_retry_start` | `task_retry_start` | 任务开始重试 |

---

## Error 错误类型

| 引擎类型 | 说明 |
|----------|------|
| `model_error` | 模型异常 |
| `engine_error` | 引擎异常 |
| `model_content_exceed_limit` | 模型超出上下文限制 |
| `api_req_failed` | API 请求失败 |

---

## 知识库类型消息

| 消息类型 | 引擎类型 | 说明 |
|----------|----------|------|
| `function_call` | `function_call` | 知识库调用请求 |
| `tool_response` | `tool_response` | 知识库响应结果 |

---

## 消息结构

### 答案消息

```json
{
  "session_id": "str",
  "message": {
    "type": "str",           // 消息类型：answer/error/mcp_call/mcp_response 等
    "content": "str",        // 内容
    "reasoning_content": "str",  // 推理过程内容（可选）
    "reply_id": "str",       // 回复ID
    "extra_info": {
      "log_id": "str",
      "tool_name": "str",
      "tool_type": "str",
      "time_cost": "str",
      "mcp": "str",
      "input_tokens": "int",
      "output_tokens": "int",
      "total_tokens": "int"
    }
  },
  "is_finish": "bool",
  "seq_id": "int"
}
```

---

*最后更新：2026-04-14*
