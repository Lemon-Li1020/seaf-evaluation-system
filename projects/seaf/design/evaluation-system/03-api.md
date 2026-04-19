# 智能体评测系统 - API 接口设计

> 文档版本：V1.0  
> 日期：2026-04-19  
> 状态：待评审

---

## 一、接口规范

### 1.1 通用说明

| 项目 | 说明 |
|------|------|
| **基础 URL** | `/api/v1/evaluation` |
| **认证方式** | `Authorization: Bearer <token>` |
| **Content-Type** | `application/json` |
| **字符编码** | UTF-8 |

### 1.2 通用响应格式

```json
{
  "code": 0,
  "message": "success",
  "data": {}
}
```

| 字段 | 类型 | 说明 |
|------|------|------|
| code | int | 状态码，0=成功，非0=失败 |
| message | string | 错误信息 |
| data | object | 响应数据 |

### 1.3 错误码定义

| 错误码 | 说明 |
|--------|------|
| 0 | 成功 |
| 1001 | 参数错误 |
| 1002 | 认证失败 |
| 2001 | 资源不存在 |
| 2002 | 资源已存在 |
| 3001 | 任务执行中 |
| 3002 | 任务执行失败 |
| 4001 | 评测配置错误 |
| 5001 | 内部错误 |

---

## 二、评测集管理 API

### 2.1 创建评测集

**请求**
```
POST /api/v1/evaluation/test-sets
```

**请求 Body**

```json
{
  "team_id": 1,
  "agent_id": 100,
  "name": "推理智能体评测集-客服场景",
  "agent_type": "reasoning",
  "description": "用于测试客服场景下的智能体表现"
}
```

| 字段 | 类型 | 必填 | 说明 |
|------|------|------|------|
| team_id | int | 是 | 团队 ID |
| agent_id | int | 是 | 关联智能体 ID |
| name | string | 是 | 评测集名称 |
| agent_type | string | 是 | 智能体类型：reasoning / workflow / orchestration |
| description | string | 否 | 评测集描述 |

**响应**

```json
{
  "code": 0,
  "message": "success",
  "data": {
    "id": 1,
    "team_id": 1,
    "agent_id": 100,
    "name": "推理智能体评测集-客服场景",
    "agent_type": "reasoning",
    "description": "用于测试客服场景下的智能体表现",
    "total_cases": 0,
    "version": "v1.0",
    "created_at": "2026-04-19T12:00:00Z"
  }
}
```

---

### 2.2 查询评测集列表

**请求**
```
GET /api/v1/evaluation/test-sets
```

**Query 参数**

| 参数 | 类型 | 必填 | 说明 |
|------|------|------|------|
| team_id | int | 是 | 团队 ID |
| agent_id | int | 否 | 智能体 ID |
| agent_type | string | 否 | 智能体类型 |
| page | int | 否 | 页码，默认 1 |
| page_size | int | 否 | 每页数量，默认 20 |

**响应**

```json
{
  "code": 0,
  "message": "success",
  "data": {
    "items": [
      {
        "id": 1,
        "team_id": 1,
        "agent_id": 100,
        "name": "推理智能体评测集-客服场景",
        "agent_type": "reasoning",
        "description": "用于测试客服场景下的智能体表现",
        "total_cases": 20,
        "version": "v1.0",
        "created_at": "2026-04-19T12:00:00Z"
      }
    ],
    "total": 1,
    "page": 1,
    "page_size": 20
  }
}
```

---

### 2.3 查询评测集详情

**请求**
```
GET /api/v1/evaluation/test-sets/{test_set_id}
```

**路径参数**

| 参数 | 类型 | 说明 |
|------|------|------|
| test_set_id | int | 评测集 ID |

**响应**

```json
{
  "code": 0,
  "message": "success",
  "data": {
    "id": 1,
    "team_id": 1,
    "agent_id": 100,
    "name": "推理智能体评测集-客服场景",
    "agent_type": "reasoning",
    "description": "用于测试客服场景下的智能体表现",
    "total_cases": 20,
    "version": "v1.0",
    "created_at": "2026-04-19T12:00:00Z",
    "updated_at": "2026-04-19T12:00:00Z"
  }
}
```

---

### 2.4 更新评测集

**请求**
```
PUT /api/v1/evaluation/test-sets/{test_set_id}
```

**请求 Body**

```json
{
  "name": "推理智能体评测集-客服场景-v2",
  "description": "更新后的描述"
}
```

**响应**

```json
{
  "code": 0,
  "message": "success",
  "data": {
    "id": 1,
    "name": "推理智能体评测集-客服场景-v2",
    "updated_at": "2026-04-19T13:00:00Z"
  }
}
```

---

### 2.5 删除评测集

**请求**
```
DELETE /api/v1/evaluation/test-sets/{test_set_id}
```

**响应**

```json
{
  "code": 0,
  "message": "success",
  "data": {}
}
```

---

### 2.6 批量添加评测数据项

**请求**
```
POST /api/v1/evaluation/test-sets/{test_set_id}/cases/batch
```

**请求 Body（推理智能体）**

```json
{
  "cases": [
    {
      "name": "退换货政策咨询",
      "query": "请问你们的退换货政策是什么？",
      "expected_tools": ["knowledge_retrieval"],
      "expected_answer_keywords": ["7天", "无理由", "退货"],
      "tags": ["客服", "政策咨询"],
      "difficulty": "easy"
    },
    {
      "name": "订单状态查询",
      "query": "我有一笔订单，订单号是20240618001，请问发货了吗？",
      "expected_tools": ["order_query"],
      "tags": ["客服", "订单查询"],
      "difficulty": "medium"
    }
  ]
}
```

**请求 Body（工作流智能体）**

```json
{
  "cases": [
    {
      "name": "订单处理流程",
      "query": "帮我处理订单20240618001的退款",
      "expected_nodes": ["订单查询", "退款计算", "退款执行", "通知用户"],
      "max_node_latency_ms": 3000,
      "max_total_latency_ms": 15000,
      "tags": ["工作流", "订单处理"],
      "difficulty": "medium"
    }
  ]
}

**请求 Body（编排智能体）**

```json
{
  "cases": [
    {
      "name": "竞品分析场景",
      "query": "帮我分析这份竞品报告并给出建议",
      "expected_sub_agents": ["文档解析Agent", "数据分析Agent", "报告生成Agent"],
      "expected_order": ["文档解析Agent", "数据分析Agent", "报告生成Agent"],
      "max_sub_agent_calls": 3,
      "conflict_scenario": false,
      "expected_answer_keywords": ["优势", "劣势", "机会", "威胁"],
      "tags": ["编排", "竞品分析"],
      "difficulty": "hard"
    }
  ]
}
```

**响应**

```json
{
  "code": 0,
  "message": "success",
  "data": {
    "added_count": 2,
    "test_set_id": 1,
    "total_cases": 22
  }
}
```

---

### 2.7 查询评测数据项列表

**请求**
```
GET /api/v1/evaluation/test-sets/{test_set_id}/cases
```

**Query 参数**

| 参数 | 类型 | 必填 | 说明 |
|------|------|------|------|
| page | int | 否 | 页码，默认 1 |
| page_size | int | 否 | 每页数量，默认 50 |
| difficulty | string | 否 | 难度筛选 |
| tags | string | 否 | 标签筛选（逗号分隔） |

**响应**

```json
{
  "code": 0,
  "message": "success",
  "data": {
    "items": [
      {
        "id": 1,
        "test_set_id": 1,
        "name": "退换货政策咨询",
        "query": "请问你们的退换货政策是什么？",
        "expected_tools": ["knowledge_retrieval"],
        "expected_answer_keywords": ["7天", "无理由", "退货"],
        "tags": ["客服", "政策咨询"],
        "difficulty": "easy",
        "sort_order": 1,
        "created_at": "2026-04-19T12:00:00Z"
      }
    ],
    "total": 20,
    "page": 1,
    "page_size": 50
  }
}
```

---

### 2.8 更新评测数据项

**请求**
```
PUT /api/v1/evaluation/test-sets/{test_set_id}/cases/{case_id}
```

**请求 Body**

```json
{
  "name": "退换货政策咨询-更新",
  "query": "请问你们的退换货政策是什么？支持无理由退货吗？",
  "expected_tools": ["knowledge_retrieval"],
  "difficulty": "medium"
}
```

**响应**

```json
{
  "code": 0,
  "message": "success",
  "data": {
    "id": 1,
    "updated_at": "2026-04-19T14:00:00Z"
  }
}
```

---

### 2.9 删除评测数据项

**请求**
```
DELETE /api/v1/evaluation/test-sets/{test_set_id}/cases/{case_id}
```

**响应**

```json
{
  "code": 0,
  "message": "success",
  "data": {}
}
```

---

## 三、评测任务 API

### 3.1 创建评测任务

**请求**
```
POST /api/v1/evaluation/tasks
```

**请求 Body**

```json
{
  "test_set_id": 1,
  "agent_id": 100,
  "agent_type": "reasoning",
  "agent_version": "v1.2.3",
  "trigger": "manual"
}
```

| 字段 | 类型 | 必填 | 说明 |
|------|------|------|------|
| test_set_id | int | 是 | 评测集 ID |
| agent_id | int | 是 | 智能体 ID |
| agent_type | string | 是 | 智能体类型：reasoning / workflow / orchestration |
| agent_version | string | 否 | 智能体版本 |
| trigger | string | 否 | 触发方式：manual / scheduled / pre_release，默认 manual |

**响应**

```json
{
  "code": 0,
  "message": "success",
  "data": {
    "task_id": 1,
    "task_uuid": "550e8400-e29b-41d4-a716-446655440000",
    "status": "pending",
    "total_cases": 20,
    "created_at": "2026-04-19T12:00:00Z"
  }
}
```

---

### 3.2 查询评测任务列表

**请求**
```
GET /api/v1/evaluation/tasks
```

**Query 参数**

| 参数 | 类型 | 必填 | 说明 |
|------|------|------|------|
| team_id | int | 是 | 团队 ID |
| agent_id | int | 否 | 智能体 ID |
| status | string | 否 | 状态筛选 |
| trigger | string | 否 | 触发方式筛选 |
| page | int | 否 | 页码，默认 1 |
| page_size | int | 否 | 每页数量，默认 20 |

**响应**

```json
{
  "code": 0,
  "message": "success",
  "data": {
    "items": [
      {
        "task_id": 1,
        "task_uuid": "550e8400-e29b-41d4-a716-446655440000",
        "test_set_id": 1,
        "test_set_name": "推理智能体评测集-客服场景",
        "agent_id": 100,
        "agent_type": "reasoning",
        "agent_version": "v1.2.3",
        "trigger": "manual",
        "status": "completed",
        "total_cases": 20,
        "completed_cases": 20,
        "progress": 100,
        "duration_ms": 45000,
        "created_at": "2026-04-19T12:00:00Z",
        "completed_at": "2026-04-19T12:00:45Z"
      }
    ],
    "total": 1,
    "page": 1,
    "page_size": 20
  }
}
```

---

### 3.3 查询评测任务详情

**请求**
```
GET /api/v1/evaluation/tasks/{task_id}
```

**响应**

```json
{
  "code": 0,
  "message": "success",
  "data": {
    "task_id": 1,
    "task_uuid": "550e8400-e29b-41d4-a716-446655440000",
    "test_set_id": 1,
    "agent_id": 100,
    "agent_type": "reasoning",
    "agent_version": "v1.2.3",
    "trigger": "manual",
    "status": "completed",
    "total_cases": 20,
    "completed_cases": 20,
    "progress": 100,
    "duration_ms": 45000,
    "started_at": "2026-04-19T12:00:00Z",
    "completed_at": "2026-04-19T12:00:45Z",
    "created_at": "2026-04-19T12:00:00Z",
    "created_by": 1001
  }
}
```

---

### 3.4 查询评测任务进度

**请求**
```
GET /api/v1/evaluation/tasks/{task_id}/progress
```

**响应（任务进行中）**

```json
{
  "code": 0,
  "message": "success",
  "data": {
    "task_id": 1,
    "status": "running",
    "total_cases": 20,
    "completed_cases": 8,
    "progress": 40,
    "current_case_id": 9,
    "started_at": "2026-04-19T12:00:00Z",
    "estimated_remaining_seconds": 30
  }
}
```

---

### 3.5 查询评测结果明细

**请求**
```
GET /api/v1/evaluation/tasks/{task_id}/results
```

**Query 参数**

| 参数 | 类型 | 必填 | 说明 |
|------|------|------|------|
| page | int | 否 | 页码，默认 1 |
| page_size | int | 否 | 每页数量，默认 50 |
| passed | boolean | 否 | 是否通过筛选 |

**响应**

```json
{
  "code": 0,
  "message": "success",
  "data": {
    "items": [
      {
        "result_id": 1,
        "case_id": 1,
        "case_name": "退换货政策咨询",
        "query": "请问你们的退换货政策是什么？",
        "agent_response": "我们的退换货政策是支持7天无理由退货...",
        "tool_call_log": [
          {"tool_name": "knowledge_retrieval", "status": "success", "latency_ms": 150}
        ],
        "scores": {
          "tool_usage": 85,
          "accuracy": 90
        },
        "weighted_score": 87,
        "passed": true,
        "latency_ms": 2340
      }
    ],
    "total": 20,
    "page": 1,
    "page_size": 50
  }
}
```

---

### 3.6 取消评测任务

**请求**
```
POST /api/v1/evaluation/tasks/{task_id}/cancel
```

**响应**

```json
{
  "code": 0,
  "message": "success",
  "data": {
    "task_id": 1,
    "status": "cancelled"
  }
}
```

---

## 四、报告 API

### 4.1 获取评测报告

**请求**
```
GET /api/v1/evaluation/tasks/{task_id}/report
```

**响应（推理智能体）**

```json
{
  "code": 0,
  "message": "success",
  "data": {
    "report_id": 1,
    "task_id": 1,
    "agent_id": 100,
    "agent_type": "reasoning",
    "test_set_id": 1,
    "summary": {
      "total_cases": 20,
      "passed": 18,
      "failed": 2,
      "pass_rate": "90%",
      "weighted_score": 87,
      "grade": "B",
      "avg_latency_ms": 2340
    },
    "by_dimension": {
      "tool_usage": {
        "score": 85,
        "weight": 0.6,
        "passed": 18,
        "failed": 2
      },
      "accuracy": {
        "score": 90,
        "weight": 0.4,
        "passed": 19,
        "failed": 1
      }
    },
    "regression": {
      "detected": false,
      "previous_score": 84,
      "change": "+3%",
      "threshold": "10%"
    },
    "created_at": "2026-04-19T12:00:45Z"
  }
}
```

**响应（工作流智能体）**

```json
{
  "code": 0,
  "message": "success",
  "data": {
    "report_id": 2,
    "task_id": 2,
    "agent_id": 101,
    "agent_type": "workflow",
    "test_set_id": 2,
    "summary": {
      "total_cases": 15,
      "passed": 13,
      "failed": 2,
      "pass_rate": "87%",
      "weighted_score": 83,
      "grade": "B",
      "avg_latency_ms": 8500
    },
    "by_dimension": {
      "flow_completeness": {
        "score": 100,
        "weight": 0.3,
        "passed": 15,
        "failed": 0
      },
      "node_performance": {
        "score": 75,
        "weight": 0.3,
        "passed": 12,
        "failed": 3,
        "slow_nodes": [
          {"node": "退款计算", "avg_latency_ms": 3500, "threshold_ms": 3000}
        ]
      },
      "end_to_end_latency": {
        "score": 80,
        "weight": 0.2,
        "passed": 13,
        "failed": 2
      },
      "result_quality": {
        "score": 80,
        "weight": 0.2,
        "passed": 12,
        "failed": 3
      }
    },
    "regression": {
      "detected": false,
      "previous_score": 81,
      "change": "+2%",
      "threshold": "10%"
    },
    "created_at": "2026-04-19T12:05:00Z"
  }
}
```

---

### 4.2 版本对比

**请求**
```
GET /api/v1/evaluation/compare
```

**Query 参数**

| 参数 | 类型 | 必填 | 说明 |
|------|------|------|------|
| agent_id | int | 是 | 智能体 ID |
| task_id_1 | int | 是 | 任务 ID（新版） |
| task_id_2 | int | 是 | 任务 ID（旧版） |

**响应**

```json
{
  "code": 0,
  "message": "success",
  "data": {
    "agent_id": 100,
    "agent_type": "reasoning",
    "new_version": {
      "task_id": 2,
      "task_uuid": "660e8400-e29b-41d4-a716-446655440001",
      "timestamp": "2026-04-19T14:00:00Z",
      "weighted_score": 87,
      "grade": "B",
      "scores": {
        "tool_usage": 85,
        "accuracy": 90
      }
    },
    "old_version": {
      "task_id": 1,
      "task_uuid": "550e8400-e29b-41d4-a716-446655440000",
      "timestamp": "2026-04-19T12:00:00Z",
      "weighted_score": 84,
      "grade": "B",
      "scores": {
        "tool_usage": 82,
        "accuracy": 87
      }
    },
    "diff": {
      "weighted_score_change": "+3%",
      "grade_change": null,
      "scores": {
        "tool_usage": {"old": 82, "new": 85, "change": "+3%"},
        "accuracy": {"old": 87, "new": 90, "change": "+3%"}
      }
    }
  }
}
```

---

### 4.3 历史评测记录

**请求**
```
GET /api/v1/evaluation/reports
```

**Query 参数**

| 参数 | 类型 | 必填 | 说明 |
|------|------|------|------|
| team_id | int | 是 | 团队 ID |
| agent_id | int | 否 | 智能体 ID |
| page | int | 否 | 页码，默认 1 |
| page_size | int | 否 | 每页数量，默认 20 |

**响应**

```json
{
  "code": 0,
  "message": "success",
  "data": {
    "items": [
      {
        "report_id": 1,
        "task_id": 1,
        "agent_id": 100,
        "agent_name": "客服智能体",
        "agent_type": "reasoning",
        "test_set_name": "客服场景评测集",
        "summary": {
          "weighted_score": 87,
          "grade": "B",
          "pass_rate": "90%"
        },
        "regression": {
          "detected": false,
          "change": "+3%"
        },
        "created_at": "2026-04-19T12:00:45Z"
      }
    ],
    "total": 10,
    "page": 1,
    "page_size": 20
  }
}
```

---

## 五、配置 API

### 5.1 查询评测配置

**请求**
```
GET /api/v1/evaluation/config/{agent_type}
```

**路径参数**

| 参数 | 类型 | 说明 |
|------|------|------|
| agent_type | string | 智能体类型：reasoning / workflow / orchestration |

**响应**

```json
{
  "code": 0,
  "message": "success",
  "data": {
    "agent_type": "reasoning",
    "dimensions": {
      "tool_usage": {
        "weight": 0.6,
        "description": "工具调用准确性"
      },
      "accuracy": {
        "weight": 0.4,
        "description": "答案准确性"
      }
    },
    "grade_rules": {
      "A": [90, 100],
      "B": [80, 89],
      "C": [70, 79],
      "D": [60, 69],
      "F": [0, 59],
      "dimension_constraint": {
        "threshold": 60,
        "max_grade": "C"
      }
    },
    "regression_threshold": 10.0
  }
}
```

---

### 5.2 更新评测配置

**请求**
```
PUT /api/v1/evaluation/config/{agent_type}
```

**请求 Body**

```json
{
  "dimensions": {
    "tool_usage": {
      "weight": 0.5,
      "description": "工具调用准确性"
    },
    "accuracy": {
      "weight": 0.5,
      "description": "答案准确性"
    }
  },
  "regression_threshold": 15.0
}
```

**响应**

```json
{
  "code": 0,
  "message": "success",
  "data": {}
}
```

---

### 5.3 查询通知配置

**请求**
```
GET /api/v1/evaluation/notification-config
```

**Query 参数**

| 参数 | 类型 | 必填 | 说明 |
|------|------|------|------|
| team_id | int | 是 | 团队 ID |

**响应**

```json
{
  "code": 0,
  "message": "success",
  "data": {
    "items": [
      {
        "id": 1,
        "team_id": 1,
        "channel": "email",
        "config": {
          "recipients": ["liwenhua6@360.cn"]
        },
        "enabled": true
      },
      {
        "id": 2,
        "team_id": 1,
        "channel": "webhook",
        "config": {
          "url": "https://example.com/webhook"
        },
        "enabled": true
      }
    ]
  }
}
```

---

### 5.4 保存通知配置

**请求**
```
POST /api/v1/evaluation/notification-config
```

**请求 Body**

```json
{
  "team_id": 1,
  "channel": "email",
  "config": {
    "recipients": ["liwenhua6@360.cn", "test@example.com"]
  },
  "enabled": true
}
```

**响应**

```json
{
  "code": 0,
  "message": "success",
  "data": {
    "id": 1,
    "team_id": 1,
    "channel": "email"
  }
}
```

---

## 六、Webhook 回调 API

### 6.1 评测完成回调

当评测任务完成（成功或失败）时，系统会回调配置的 Webhook URL。

**POST** `{配置的 Webhook URL}`

**请求 Body**

```json
{
  "event": "evaluation.completed",
  "timestamp": "2026-04-19T12:00:45Z",
  "data": {
    "task_id": 1,
    "agent_id": 100,
    "agent_type": "reasoning",
    "status": "completed",
    "summary": {
      "weighted_score": 87,
      "grade": "B",
      "pass_rate": "90%"
    },
    "regression": {
      "detected": true,
      "change": "-12%"
    }
  }
}
```

---

## 七、导入导出 API

### 7.1 导出评测集

**请求**
```
GET /api/v1/evaluation/test-sets/{test_set_id}/export
```

**响应**

```json
{
  "code": 0,
  "message": "success",
  "data": {
    "test_set": {
      "name": "推理智能体评测集-客服场景",
      "agent_type": "reasoning",
      "description": "用于测试客服场景下的智能体表现"
    },
    "cases": [
      {
        "name": "退换货政策咨询",
        "query": "请问你们的退换货政策是什么？",
        "expected_tools": ["knowledge_retrieval"],
        "expected_answer_keywords": ["7天", "无理由", "退货"],
        "tags": ["客服", "政策咨询"],
        "difficulty": "easy"
      }
    ],
    "exported_at": "2026-04-19T12:00:00Z"
  }
}
```

> ⚠️ 注意：导出接口返回 JSON 数据，前端需自行处理文件下载。

---

### 7.2 导入评测集

**请求**
```
POST /api/v1/evaluation/test-sets/import
Content-Type: multipart/form-data
```

**Form 参数**

| 参数 | 类型 | 必填 | 说明 |
|------|------|------|------|
| team_id | int | 是 | 团队 ID |
| agent_id | int | 是 | 关联智能体 ID |
| file | file | 是 | 导入文件（JSON 格式） |

**响应**

```json
{
  "code": 0,
  "message": "success",
  "data": {
    "test_set_id": 2,
    "name": "推理智能体评测集-客服场景",
    "imported_count": 18,
    "skipped_count": 2,
    "skipped_reasons": [
      "case_id=5: query 为空，跳过"
    ]
  }
}
```

---

*文档状态：待评审*
