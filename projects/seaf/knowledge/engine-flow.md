# Seaf 引擎调用层处理流程

> 来源：长文本消息 2026-04-14 18:40:24
> 最后更新：2026-04-14

---

## 1. 整体流程概览

### 1.1 入口：SeafChatService.chat_agent_ask

**处理步骤：**

1. **记录开始时间**，设置初始序列 ID
2. **会话验证** → 调用 `check_session` 验证会话和用户有效性
3. **获取智能体信息** → 调用 `get_agent_detail_info`
4. **用户信息处理** → 针对 API 调用方式，处理用户信息和源信息
5. **保存用户问题** → 调用 `create_question`
6. **发送确认消息** → 返回 `confirmed` 类型的消息
7. **检查终止信号** → 调用 `update_chat_final_status`
8. **检查是否首次问答** → 调用 `is_first_ask_for_new_agent`
9. **获取知识库工具** → 调用 `fetch_knowledge_tools`
10. **获取 MCP 服务** → 调用 `batch_get_mcp_authorization`
11. **知识库召回处理** → 处理知识库召回（如果存在）
12. **长期记忆处理** → 调用 `memory_search_prepare` 和 `memory_search`（**⚠️ 当前系统默认关闭长期记忆，agent 表中 memory_status 都是 3**）
13. **核心对话处理** → 调用 `sse_create_message_mcp`
14. **状态更新** → 更新会话和智能体状态
15. **异常处理** → 捕获异常并更新失败状态
16. **记忆添加** → 调用 `memory_add`（**现在系统默认关闭长期记忆**）
17. **推荐问题生成** → 调用 `_generate_suggestion`
18. **结束流** → 发送 `"done"` 信号

---

## 2. 关键方法

### 2.1 create_question — 保存用户问题

```python
async def create_question(self, item: ChatReq, session_detail):
    # 重新生成回答场景
    if item.regenerate_answer and item.question_id:
        return item.question_id, {...}
    # 新建问题
    question_message = Message(
        role="user",
        type="question",
        content=item.message,
        content_type=item.content_type,
        extra_info=ExtraInfo(log_id=GLOBAL_CONTENT.request_id)
    )
    data = ChatResponseData(...)
    question_id = str(await self.chat_dao.save_stream_chat_message(data=question_data))
    return question_id, {...}
```

### 2.2 is_first_ask_for_new_agent — 判断是否首次问答

```python
async def is_first_ask_for_new_agent(self, session_id):
    """
    判断依据：有回答或者 MCP 调用了，即使消息删除也算
    """
    find = await self.chat_dao.get_one_chat_sse_message_by_type(
        session_id, ["mcp_response", "mcp_call", "answer"], True
    )
    return bool(find)
```

### 2.3 sse_create_message_mcp — 核心对话处理

**参数：**
- `item`: 用户请求参数，包含 message 和 session_id
- `agent_detail`: 智能体基本配置
- `question_id`: 用户问题 ID
- `mcp_dict`: 可用 MCP 服务配置信息，格式：
  ```python
  {mcp_version_id}: {
      "mcp_version_id": int,
      "mcp_id": int,
      "mcp_name": str,
      "mcp_url": str,
      "mcp_detail": str,
      "mcp_header": dict,
      "mcp_type": int  # 1-SSE, 3-streamhttp
  }
  ```
- `knowledge_content`: 知识库检索结果

**响应类型处理：**

| chunk_type | 含义 | 关键字段 |
|------------|------|----------|
| `result` | 问答结果（最终） | `input_tokens`, `output_tokens` |
| `result_chunk` | 流式问答结果 | 流式拼接 `final_content` |
| `thinking` / `text` | 思考过程最终文本 | |
| `thinking_chunk` / `text_chunk` | 思考过程流式返回 | |
| `file` | 最终文件产物 | `totalFiles`, `files[]` |
| `file_chunk` | 文件内容流式返回 | `file_name`, `file_content` |
| `mcp_tool_request` | MCP 工具调用请求 | `serverName`, `toolName`, `arguments` |
| `mcp_server_response` | MCP 工具调用结果 | 格式化 JSON 响应 |
| `status` | 任务状态 | `taskStatus`: aborted / error / completed |

### 2.4 LLMClientMcp.ainvoke — LLM 调用

调用链：`ainvoke` → `achat_generate_stream`

**超时配置：**
```python
AGENTRUNNER_TIMEOUT = httpx.Timeout(
    timeout=5.0,      # 整体超时
    connect=5.0,     # 连接超时
    read=1200        # 读取超时（20分钟）
)
```

---

## 3. 异常处理机制

### 3.1 层级分布

| 层级 | 处理方式 |
|------|----------|
| 入口层 | 不直接处理，异常向上传递 |
| 会话管理层 | `try/except` 记录日志并抛出 |
| 智能体对话层 | 捕获异常、更新失败状态、返回错误消息 |
| MCP 引擎层 | `status=error/aborted` 判断、抛异常 |
| HTTP 层 | `httpx.TimeoutException` 特殊处理 |

### 3.2 超时处理流程

```
httpx.TimeoutException
  ↓
yield {"taskStatus": "error", "type": "status", "data": "服务端异常:超时..."}
  ↓
上层 except 捕获，包装为 Exception
  ↓
返回 "系统错误[{str(e)}]，请稍后再试！"
```

---

## 4. 数据结构

### 4.1 会话数据结构

```json
{
  "agent_id": "int",
  "conv_name": "str",
  "session_id": "str",
  "conv_uc": "int",
  "uid": "int",
  "last_msg": "str",
  "last_msg_time": "int",
  "is_deleted": "int",
  "created_at": "int",
  "updated_at": "int"
}
```

### 4.2 问题数据结构

```json
{
  "session_id": "str",
  "message": {
    "role": "user",
    "type": "question",
    "content": "str",
    "content_type": "str",
    "extra_info": { "log_id": "str" }
  },
  "is_finish": true,
  "agent_id": "int",
  "user_id": "int",
  "external_user": "str",
  "channel": "str",
  "status": "int",
  "time_cost": "int",
  "stop_position": "int"
}
```

### 4.3 答案数据结构（变体）

根据 `message.type` 不同有多种变体：
- `answer` — 普通回答
- `error` — 错误响应
- `mcp_call` — MCP 调用请求
- `mcp_response` — MCP 调用结果
- `reasoning` / `deep_thinking` — 思考过程

---

## 5. 测试点建议

### 5.1 正常流程测试

- [ ] 基础参数验证
- [ ] 会话管理（新会话创建、已有会话更新）
- [ ] 知识库功能（获取、触发词处理、召回）
- [ ] MCP 工具调用（获取服务、调用、结果处理）
- [ ] 文件操作（文件块处理、完整文件消息）
- [ ] 响应流处理（多种响应类型、流式数据合并）
- [ ] 推荐问题生成

### 5.2 异常流程测试

- [ ] 参数验证失败（无效 session_id、user_id）
- [ ] 会话验证失败（不存在、不匹配）
- [ ] 智能体信息获取失败
- [ ] 知识库处理异常
- [ ] MCP 引擎异常（HTTP 错误、任务取消、执行失败）
- [ ] 超时异常（连接超时、读取超时）
- [ ] 状态更新失败

### 5.3 边界条件测试

- [ ] 大量并发请求
- [ ] 超长用户消息
- [ ] 超长知识库召回结果
- [ ] 多种类型混合响应
- [ ] Token 计算逻辑
- [ ] 超长错误消息

---

## 6. 关键注意事项

> ⚠️ **长期记忆功能当前默认关闭**
>
> - `agent` 表中 `memory_status` 字段值均为 `3`
> - 记忆搜索和添加方法仍然存在，但在正常流程中不会被触发
> - 测试时注意确认是否涉及记忆相关逻辑

> ⚠️ **MCP 资源类型映射**
>
> - MCP 调用统计时，`mcp_category` 转换：
>   - `0`（工具 MCP）→ `2`（知识库）
>   - `1`（工作流 MCP）→ `1`

---

*最后更新：2026-04-14*
