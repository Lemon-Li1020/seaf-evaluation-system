# 智能体评测系统 - 数据库设计

> 文档版本：V1.0  
> 日期：2026-04-19  
> 状态：待评审

---

## 一、ER 图

```
┌─────────────────┐     ┌─────────────────┐     ┌─────────────────┐
│    team         │     │    agent        │     │   test_set      │
│    团队表        │     │    智能体表      │     │    评测集表     │
├─────────────────┤     ├─────────────────┤     ├─────────────────┤
│ id (PK)         │◄────│ team_id (FK)    │     │ id (PK)         │
│ name             │     │ id (PK)         │◄────│ agent_id (FK)   │
│ created_at       │     │ name             │     │ name            │
│ updated_at       │     │ agent_type       │     │ agent_type      │
└─────────────────┘     │ created_at       │     │ description     │
                        │ updated_at       │     │ total_cases     │
                        └─────────────────┘     │ created_at      │
                                                │ updated_at      │
                                                └────────┬────────┘
                                                         │
                                                         │ 1:N
                                                         ▼
                                                ┌─────────────────┐
                                                │  test_case      │
                                                │   评测数据项表   │
                                                ├─────────────────┤
                                                │ id (PK)         │
                                                │ test_set_id(FK) │
                                                │ name            │
                                                │ query           │
                                                │ expected_tools  │
                                                │ expected_nodes  │
                                                │ max_node_latency│
                                                │ max_total_latency│
                                                │ tags            │
                                                │ difficulty      │
                                                │ created_at      │
                                                │ updated_at      │
                                                └─────────────────┘

┌─────────────────┐     ┌─────────────────┐     ┌─────────────────┐
│  evaluation_task│     │ test_case_result│     │   evaluation_   │
│   评测任务表      │     │  评测结果明细表  │     │    report       │
├─────────────────┤     ├─────────────────┤     │   评测报告表     │
│ id (PK)         │────►│ id (PK)         │     ├─────────────────┤
│ test_set_id(FK) │ 1:N │ task_id (FK)    │◄─── │ id (PK)         │
│ agent_id (FK)   │     │ test_case_id(FK)│     │ task_id (FK)    │
│ agent_type      │     │ scores (JSONB)  │     │ summary (JSONB) │
│ agent_version   │     │ weighted_score  │     │ by_dimension    │
│ trigger         │     │ passed          │     │ (JSONB)         │
│ status          │     │ latency_ms      │     │ grade           │
│ started_at      │     │ tool_call_log   │     │ created_at      │
│ completed_at    │     │ llm_response    │     └─────────────────┘
│ duration_ms     │     │ node_log        │
│ created_by      │     │ error_message   │
│ created_at      │     │ created_at      │
└─────────────────┘     └─────────────────┘
```

---

## 二、表结构设计

### 2.1 team - 团队表

| 字段 | 类型 | 约束 | 说明 |
|------|------|------|------|
| id | BIGSERIAL | PRIMARY KEY | 团队 ID |
| name | VARCHAR(100) | NOT NULL | 团队名称 |
| description | TEXT | | 团队描述 |
| created_at | TIMESTAMP | DEFAULT NOW() | 创建时间 |
| updated_at | TIMESTAMP | DEFAULT NOW() | 更新时间 |

```sql
CREATE TABLE team (
    id BIGSERIAL PRIMARY KEY,
    name VARCHAR(100) NOT NULL,
    description TEXT,
    created_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP DEFAULT NOW()
);

CREATE INDEX idx_team_name ON team(name);
```

---

### 2.2 agent - 智能体表（可选复用现有表）

> ⚠️ 本表为评测系统所需的最小字段，完整智能体信息应复用 Seaf 平台现有 agent 表。

| 字段 | 类型 | 约束 | 说明 |
|------|------|------|------|
| id | BIGSERIAL | PRIMARY KEY | 智能体 ID |
| team_id | BIGINT | FOREIGN KEY (team.id) | 团队 ID |
| name | VARCHAR(200) | NOT NULL | 智能体名称 |
| agent_type | VARCHAR(20) | NOT NULL | 类型：reasoning / workflow |
| description | TEXT | | 智能体描述 |
| config | JSONB | | 智能体配置 |
| created_at | TIMESTAMP | DEFAULT NOW() | 创建时间 |
| updated_at | TIMESTAMP | DEFAULT NOW() | 更新时间 |

```sql
CREATE TABLE agent (
    id BIGSERIAL PRIMARY KEY,
    team_id BIGINT REFERENCES team(id),
    name VARCHAR(200) NOT NULL,
    agent_type VARCHAR(20) NOT NULL CHECK (agent_type IN ('reasoning', 'workflow')),
    description TEXT,
    config JSONB DEFAULT '{}',
    created_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP DEFAULT NOW()
);

CREATE INDEX idx_agent_team_id ON agent(team_id);
CREATE INDEX idx_agent_type ON agent(agent_type);
```

---

### 2.3 test_set - 评测集表

| 字段 | 类型 | 约束 | 说明 |
|------|------|------|------|
| id | BIGSERIAL | PRIMARY KEY | 评测集 ID |
| team_id | BIGINT | FOREIGN KEY (team.id) | 团队 ID |
| agent_id | BIGINT | FOREIGN KEY (agent.id) | 关联智能体 ID |
| name | VARCHAR(200) | NOT NULL | 评测集名称 |
| agent_type | VARCHAR(20) | NOT NULL | 智能体类型 |
| description | TEXT | | 评测集描述 |
| total_cases | INTEGER | DEFAULT 0 | 评测项总数 |
| version | VARCHAR(20) | DEFAULT 'v1.0' | 版本号 |
| created_by | BIGINT | | 创建人 ID |
| created_at | TIMESTAMP | DEFAULT NOW() | 创建时间 |
| updated_at | TIMESTAMP | DEFAULT NOW() | 更新时间 |

```sql
CREATE TABLE test_set (
    id BIGSERIAL PRIMARY KEY,
    team_id BIGINT REFERENCES team(id) NOT NULL,
    agent_id BIGINT REFERENCES agent(id),
    name VARCHAR(200) NOT NULL,
    agent_type VARCHAR(20) NOT NULL CHECK (agent_type IN ('reasoning', 'workflow')),
    description TEXT,
    total_cases INTEGER DEFAULT 0,
    version VARCHAR(20) DEFAULT 'v1.0',
    created_by BIGINT,
    created_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP DEFAULT NOW()
);

CREATE INDEX idx_test_set_team_id ON test_set(team_id);
CREATE INDEX idx_test_set_agent_id ON test_set(agent_id);
CREATE INDEX idx_test_set_type ON test_set(agent_type);
```

---

### 2.4 test_case - 评测数据项表

| 字段 | 类型 | 约束 | 说明 |
|------|------|------|------|
| id | BIGSERIAL | PRIMARY KEY | 评测项 ID |
| test_set_id | BIGINT | FOREIGN KEY (test_set.id) | 所属评测集 ID |
| name | VARCHAR(200) | NOT NULL | 评测项名称 |
| query | TEXT | NOT NULL | 用户问题/触发条件 |
| expected_tools | TEXT | | 期望调用的工具列表（JSON 数组字符串） |
| expected_answer_keywords | TEXT | | 期望答案关键词（JSON 数组字符串） |
| expected_nodes | TEXT | | 期望执行的工作流节点（JSON 数组，仅工作流类型） |
| max_node_latency_ms | INTEGER | | 单节点最大耗时（毫秒） |
| max_total_latency_ms | INTEGER | | 端到端最大耗时（毫秒） |
| tags | TEXT | | 标签列表（JSON 数组字符串） |
| difficulty | VARCHAR(10) | DEFAULT 'medium' | 难度：easy / medium / hard |
| sort_order | INTEGER | DEFAULT 0 | 排序顺序 |
| created_at | TIMESTAMP | DEFAULT NOW() | 创建时间 |
| updated_at | TIMESTAMP | DEFAULT NOW() | 更新时间 |

```sql
CREATE TABLE test_case (
    id BIGSERIAL PRIMARY KEY,
    test_set_id BIGINT REFERENCES test_set(id) ON DELETE CASCADE,
    name VARCHAR(200) NOT NULL,
    query TEXT NOT NULL,
    expected_tools TEXT,
    expected_answer_keywords TEXT,
    expected_nodes TEXT,
    max_node_latency_ms INTEGER,
    max_total_latency_ms INTEGER,
    tags TEXT DEFAULT '[]',
    difficulty VARCHAR(10) DEFAULT 'medium' CHECK (difficulty IN ('easy', 'medium', 'hard')),
    sort_order INTEGER DEFAULT 0,
    created_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP DEFAULT NOW()
);

CREATE INDEX idx_test_case_test_set_id ON test_case(test_set_id);
CREATE INDEX idx_test_case_difficulty ON test_case(difficulty);
```

---

### 2.5 evaluation_task - 评测任务表

| 字段 | 类型 | 约束 | 说明 |
|------|------|------|------|
| id | BIGSERIAL | PRIMARY KEY | 任务 ID |
| task_uuid | VARCHAR(36) | UNIQUE, NOT NULL | 任务 UUID（用于 Celery） |
| team_id | BIGINT | FOREIGN KEY (team.id) | 团队 ID |
| test_set_id | BIGINT | FOREIGN KEY (test_set.id) | 评测集 ID |
| agent_id | BIGINT | FOREIGN KEY (agent.id) | 智能体 ID |
| agent_type | VARCHAR(20) | NOT NULL | 智能体类型 |
| agent_version | VARCHAR(50) | | 智能体版本 |
| trigger | VARCHAR(20) | DEFAULT 'manual' | 触发方式：manual / scheduled / pre_release |
| status | VARCHAR(20) | DEFAULT 'pending' | 状态：pending / running / completed / failed |
| total_cases | INTEGER | DEFAULT 0 | 总评测项数 |
| completed_cases | INTEGER | DEFAULT 0 | 已完成数 |
| progress | INTEGER | DEFAULT 0 | 进度百分比 |
| error_message | TEXT | | 错误信息 |
| started_at | TIMESTAMP | | 开始时间 |
| completed_at | TIMESTAMP | | 完成时间 |
| duration_ms | BIGINT | | 总耗时（毫秒） |
| created_by | BIGINT | | 创建人 ID |
| created_at | TIMESTAMP | DEFAULT NOW() | 创建时间 |

```sql
CREATE TABLE evaluation_task (
    id BIGSERIAL PRIMARY KEY,
    task_uuid VARCHAR(36) UNIQUE NOT NULL,
    team_id BIGINT REFERENCES team(id) NOT NULL,
    test_set_id BIGINT REFERENCES test_set(id) NOT NULL,
    agent_id BIGINT REFERENCES agent(id) NOT NULL,
    agent_type VARCHAR(20) NOT NULL CHECK (agent_type IN ('reasoning', 'workflow')),
    agent_version VARCHAR(50),
    trigger VARCHAR(20) DEFAULT 'manual' CHECK (trigger IN ('manual', 'scheduled', 'pre_release', 'api')),
    status VARCHAR(20) DEFAULT 'pending' CHECK (status IN ('pending', 'running', 'completed', 'failed')),
    total_cases INTEGER DEFAULT 0,
    completed_cases INTEGER DEFAULT 0,
    progress INTEGER DEFAULT 0,
    error_message TEXT,
    started_at TIMESTAMP,
    completed_at TIMESTAMP,
    duration_ms BIGINT,
    created_by BIGINT,
    created_at TIMESTAMP DEFAULT NOW()
);

CREATE INDEX idx_task_team_id ON evaluation_task(team_id);
CREATE INDEX idx_task_test_set_id ON evaluation_task(test_set_id);
CREATE INDEX idx_task_agent_id ON evaluation_task(agent_id);
CREATE INDEX idx_task_status ON evaluation_task(status);
CREATE INDEX idx_task_created_at ON evaluation_task(created_at);
CREATE INDEX idx_task_trigger ON evaluation_task(trigger);
```

---

### 2.6 test_case_result - 评测结果明细表

| 字段 | 类型 | 约束 | 说明 |
|------|------|------|------|
| id | BIGSERIAL | PRIMARY KEY | 结果 ID |
| task_id | BIGINT | FOREIGN KEY (evaluation_task.id) | 任务 ID |
| test_case_id | BIGINT | FOREIGN KEY (test_case.id) | 评测项 ID |
| query | TEXT | | 用户问题 |
| agent_response | TEXT | | Agent 响应 |
| tool_call_log | JSONB | | 工具调用日志 |
| node_execution_log | JSONB | | 工作流节点执行日志（仅工作流类型） |
| scores | JSONB | | 各维度得分 |
| weighted_score | INTEGER | | 加权总分 |
| passed | BOOLEAN | | 是否通过 |
| latency_ms | BIGINT | | 响应耗时（毫秒） |
| llm_response | JSONB | | LLM 评委原始响应 |
| error_message | TEXT | | 错误信息 |
| created_at | TIMESTAMP | DEFAULT NOW() | 创建时间 |

```sql
CREATE TABLE test_case_result (
    id BIGSERIAL PRIMARY KEY,
    task_id BIGINT REFERENCES evaluation_task(id) ON DELETE CASCADE,
    test_case_id BIGINT REFERENCES test_case(id),
    query TEXT,
    agent_response TEXT,
    tool_call_log JSONB DEFAULT '[]',
    node_execution_log JSONB DEFAULT '[]',
    scores JSONB DEFAULT '{}',
    weighted_score INTEGER,
    passed BOOLEAN,
    latency_ms BIGINT,
    llm_response JSONB,
    error_message TEXT,
    created_at TIMESTAMP DEFAULT NOW()
);

CREATE INDEX idx_result_task_id ON test_case_result(task_id);
CREATE INDEX idx_result_case_id ON test_case_result(test_case_id);
CREATE INDEX idx_result_passed ON test_case_result(passed);
```

---

### 2.7 evaluation_report - 评测报告表

| 字段 | 类型 | 约束 | 说明 |
|------|------|------|------|
| id | BIGSERIAL | PRIMARY KEY | 报告 ID |
| task_id | BIGINT | FOREIGN KEY (evaluation_task.id) | 任务 ID |
| team_id | BIGINT | FOREIGN KEY (team.id) | 团队 ID |
| agent_id | BIGINT | FOREIGN KEY (agent.id) | 智能体 ID |
| test_set_id | BIGINT | FOREIGN KEY (test_set.id) | 评测集 ID |
| summary | JSONB | | 汇总信息 |
| by_dimension | JSONB | | 分维度得分 |
| regression | JSONB | | 回归检测结果 |
| created_at | TIMESTAMP | DEFAULT NOW() | 创建时间 |

```sql
CREATE TABLE evaluation_report (
    id BIGSERIAL PRIMARY KEY,
    task_id BIGINT REFERENCES evaluation_task(id) UNIQUE NOT NULL,
    team_id BIGINT REFERENCES team(id) NOT NULL,
    agent_id BIGINT REFERENCES agent(id) NOT NULL,
    test_set_id BIGINT REFERENCES test_set(id) NOT NULL,
    summary JSONB NOT NULL,
    by_dimension JSONB NOT NULL,
    regression JSONB DEFAULT '{}',
    created_at TIMESTAMP DEFAULT NOW()
);

CREATE INDEX idx_report_team_id ON evaluation_report(team_id);
CREATE INDEX idx_report_agent_id ON evaluation_report(agent_id);
CREATE INDEX idx_report_created_at ON evaluation_report(created_at);
```

---

### 2.8 notification_config - 通知配置表

| 字段 | 类型 | 约束 | 说明 |
|------|------|------|------|
| id | BIGSERIAL | PRIMARY KEY | 配置 ID |
| team_id | BIGINT | FOREIGN KEY (team.id) | 团队 ID |
| channel | VARCHAR(20) | NOT NULL | 通知渠道：email / webhook |
| config | JSONB | NOT NULL | 渠道配置 |
| enabled | BOOLEAN | DEFAULT TRUE | 是否启用 |
| created_at | TIMESTAMP | DEFAULT NOW() | 创建时间 |
| updated_at | TIMESTAMP | DEFAULT NOW() | 更新时间 |

```sql
CREATE TABLE notification_config (
    id BIGSERIAL PRIMARY KEY,
    team_id BIGINT REFERENCES team(id) NOT NULL,
    channel VARCHAR(20) NOT NULL CHECK (channel IN ('email', 'webhook', 'in_app')),
    config JSONB NOT NULL,
    enabled BOOLEAN DEFAULT TRUE,
    created_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP DEFAULT NOW()
);

CREATE INDEX idx_notification_team_id ON notification_config(team_id);
```

---

### 2.9 evaluation_config - 评测配置表

| 字段 | 类型 | 约束 | 说明 |
|------|------|------|------|
| id | BIGSERIAL | PRIMARY KEY | 配置 ID |
| agent_type | VARCHAR(20) | NOT NULL | 智能体类型 |
| dimensions | JSONB | NOT NULL | 评测维度配置 |
| grade_rules | JSONB | NOT NULL | Grade 计算规则 |
| regression_threshold | DECIMAL(5,2) | DEFAULT 10.00 | 回归检测阈值 |
| created_at | TIMESTAMP | DEFAULT NOW() | 创建时间 |
| updated_at | TIMESTAMP | DEFAULT NOW() | 更新时间 |

```sql
CREATE TABLE evaluation_config (
    id BIGSERIAL PRIMARY KEY,
    agent_type VARCHAR(20) NOT NULL UNIQUE CHECK (agent_type IN ('reasoning', 'workflow')),
    dimensions JSONB NOT NULL,
    grade_rules JSONB NOT NULL,
    regression_threshold DECIMAL(5,2) DEFAULT 10.00,
    created_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP DEFAULT NOW()
);

-- 初始化默认配置
INSERT INTO evaluation_config (agent_type, dimensions, grade_rules, regression_threshold) VALUES
('reasoning', 
 '{"tool_usage": {"weight": 0.6, "description": "工具调用准确性"}, "accuracy": {"weight": 0.4, "description": "答案准确性"}}',
 '{"A": [90, 100], "B": [80, 89], "C": [70, 79], "D": [60, 69], "F": [0, 59], "dimension_constraint": {"threshold": 60, "max_grade": "C"}}',
 10.00
),
('workflow',
 '{"flow_completeness": {"weight": 0.3, "description": "流程完整性"}, "node_performance": {"weight": 0.3, "description": "节点性能"}, "end_to_end_latency": {"weight": 0.2, "description": "端到端耗时"}, "result_quality": {"weight": 0.2, "description": "结果质量"}}',
 '{"A": [90, 100], "B": [80, 89], "C": [70, 79], "D": [60, 69], "F": [0, 59], "dimension_constraint": {"threshold": 60, "max_grade": "C"}}',
 10.00
);
```

---

## 三、JSONB 字段结构

### 3.1 scores - 各维度得分

```json
{
  "tool_usage": 85,
  "accuracy": 90
}
```

### 3.2 summary - 汇总信息

```json
{
  "total_cases": 20,
  "passed": 18,
  "failed": 2,
  "pass_rate": "90%",
  "weighted_score": 87,
  "grade": "B",
  "avg_latency_ms": 2340
}
```

### 3.3 by_dimension - 分维度得分

```json
{
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
}
```

### 3.4 regression - 回归检测结果

```json
{
  "detected": false,
  "previous_task_id": 123,
  "previous_score": 84,
  "current_score": 87,
  "change": "+3%",
  "threshold": "10%"
}
```

### 3.5 tool_call_log - 工具调用日志

```json
[
  {
    "tool_name": "knowledge_retrieval",
    "arguments": {"query": "退换货政策"},
    "result": "...",
    "status": "success",
    "latency_ms": 150
  },
  {
    "tool_name": "mcp_weather",
    "arguments": {"city": "北京"},
    "result": "...",
    "status": "success",
    "latency_ms": 200
  }
]
```

### 3.6 node_execution_log - 工作流节点执行日志

```json
[
  {
    "node": "节点A",
    "latency_ms": 1200,
    "status": "success"
  },
  {
    "node": "节点B",
    "latency_ms": 3500,
    "status": "success"
  },
  {
    "node": "节点C",
    "latency_ms": 800,
    "status": "failed",
    "error": "timeout"
  }
]
```

---

## 四、索引优化

### 4.1 常用查询索引

```sql
-- 按团队查询评测集
CREATE INDEX idx_test_set_team_agent ON test_set(team_id, agent_id);

-- 按智能体查询历史评测任务
CREATE INDEX idx_task_agent_time ON evaluation_task(agent_id, created_at DESC);

-- 按状态查询待处理任务（Celery 轮询）
CREATE INDEX idx_task_pending ON evaluation_task(status, created_at) WHERE status = 'pending';

-- 按团队查询最新报告
CREATE INDEX idx_report_agent_time ON evaluation_report(agent_id, created_at DESC);
```

### 4.2 分区表建议（数据量大时）

```sql
-- 按月分区（评测任务表）
CREATE TABLE evaluation_task_partitioned (
    LIKE evaluation_task INCLUDING ALL
) PARTITION BY RANGE (created_at);

CREATE TABLE evaluation_task_2026_04 PARTITION OF evaluation_task_partitioned
    FOR VALUES FROM ('2026-04-01') TO ('2026-05-01');
```

---

## 五、迁移脚本

```sql
-- V1.0 初始化脚本
-- 包含所有表的创建和默认数据初始化

BEGIN;

-- 1. 团队表
CREATE TABLE IF NOT EXISTS team (
    id BIGSERIAL PRIMARY KEY,
    name VARCHAR(100) NOT NULL,
    description TEXT,
    created_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP DEFAULT NOW()
);

-- 2. 智能体表（评测系统专用）
CREATE TABLE IF NOT EXISTS agent (
    id BIGSERIAL PRIMARY KEY,
    team_id BIGINT REFERENCES team(id),
    name VARCHAR(200) NOT NULL,
    agent_type VARCHAR(20) NOT NULL CHECK (agent_type IN ('reasoning', 'workflow')),
    description TEXT,
    config JSONB DEFAULT '{}',
    created_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP DEFAULT NOW()
);

-- 3. 评测集表
CREATE TABLE IF NOT EXISTS test_set (
    id BIGSERIAL PRIMARY KEY,
    team_id BIGINT REFERENCES team(id) NOT NULL,
    agent_id BIGINT REFERENCES agent(id),
    name VARCHAR(200) NOT NULL,
    agent_type VARCHAR(20) NOT NULL CHECK (agent_type IN ('reasoning', 'workflow')),
    description TEXT,
    total_cases INTEGER DEFAULT 0,
    version VARCHAR(20) DEFAULT 'v1.0',
    created_by BIGINT,
    created_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP DEFAULT NOW()
);

-- 4. 评测数据项表
CREATE TABLE IF NOT EXISTS test_case (
    id BIGSERIAL PRIMARY KEY,
    test_set_id BIGINT REFERENCES test_set(id) ON DELETE CASCADE,
    name VARCHAR(200) NOT NULL,
    query TEXT NOT NULL,
    expected_tools TEXT,
    expected_answer_keywords TEXT,
    expected_nodes TEXT,
    max_node_latency_ms INTEGER,
    max_total_latency_ms INTEGER,
    tags TEXT DEFAULT '[]',
    difficulty VARCHAR(10) DEFAULT 'medium' CHECK (difficulty IN ('easy', 'medium', 'hard')),
    sort_order INTEGER DEFAULT 0,
    created_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP DEFAULT NOW()
);

-- 5. 评测任务表
CREATE TABLE IF NOT EXISTS evaluation_task (
    id BIGSERIAL PRIMARY KEY,
    task_uuid VARCHAR(36) UNIQUE NOT NULL,
    team_id BIGINT REFERENCES team(id) NOT NULL,
    test_set_id BIGINT REFERENCES test_set(id) NOT NULL,
    agent_id BIGINT REFERENCES agent(id) NOT NULL,
    agent_type VARCHAR(20) NOT NULL CHECK (agent_type IN ('reasoning', 'workflow')),
    agent_version VARCHAR(50),
    trigger VARCHAR(20) DEFAULT 'manual' CHECK (trigger IN ('manual', 'scheduled', 'pre_release', 'api')),
    status VARCHAR(20) DEFAULT 'pending' CHECK (status IN ('pending', 'running', 'completed', 'failed')),
    total_cases INTEGER DEFAULT 0,
    completed_cases INTEGER DEFAULT 0,
    progress INTEGER DEFAULT 0,
    error_message TEXT,
    started_at TIMESTAMP,
    completed_at TIMESTAMP,
    duration_ms BIGINT,
    created_by BIGINT,
    created_at TIMESTAMP DEFAULT NOW()
);

-- 6. 评测结果明细表
CREATE TABLE IF NOT EXISTS test_case_result (
    id BIGSERIAL PRIMARY KEY,
    task_id BIGINT REFERENCES evaluation_task(id) ON DELETE CASCADE,
    test_case_id BIGINT REFERENCES test_case(id),
    query TEXT,
    agent_response TEXT,
    tool_call_log JSONB DEFAULT '[]',
    node_execution_log JSONB DEFAULT '[]',
    scores JSONB DEFAULT '{}',
    weighted_score INTEGER,
    passed BOOLEAN,
    latency_ms BIGINT,
    llm_response JSONB,
    error_message TEXT,
    created_at TIMESTAMP DEFAULT NOW()
);

-- 7. 评测报告表
CREATE TABLE IF NOT EXISTS evaluation_report (
    id BIGSERIAL PRIMARY KEY,
    task_id BIGINT REFERENCES evaluation_task(id) UNIQUE NOT NULL,
    team_id BIGINT REFERENCES team(id) NOT NULL,
    agent_id BIGINT REFERENCES agent(id) NOT NULL,
    test_set_id BIGINT REFERENCES test_set(id) NOT NULL,
    summary JSONB NOT NULL,
    by_dimension JSONB NOT NULL,
    regression JSONB DEFAULT '{}',
    created_at TIMESTAMP DEFAULT NOW()
);

-- 8. 通知配置表
CREATE TABLE IF NOT EXISTS notification_config (
    id BIGSERIAL PRIMARY KEY,
    team_id BIGINT REFERENCES team(id) NOT NULL,
    channel VARCHAR(20) NOT NULL CHECK (channel IN ('email', 'webhook', 'in_app')),
    config JSONB NOT NULL,
    enabled BOOLEAN DEFAULT TRUE,
    created_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP DEFAULT NOW()
);

-- 9. 评测配置表
CREATE TABLE IF NOT EXISTS evaluation_config (
    id BIGSERIAL PRIMARY KEY,
    agent_type VARCHAR(20) NOT NULL UNIQUE CHECK (agent_type IN ('reasoning', 'workflow')),
    dimensions JSONB NOT NULL,
    grade_rules JSONB NOT NULL,
    regression_threshold DECIMAL(5,2) DEFAULT 10.00,
    created_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP DEFAULT NOW()
);

-- 10. 创建索引
CREATE INDEX IF NOT EXISTS idx_agent_team_id ON agent(team_id);
CREATE INDEX IF NOT EXISTS idx_test_set_team_id ON test_set(team_id);
CREATE INDEX IF NOT EXISTS idx_test_set_agent_id ON test_set(agent_id);
CREATE INDEX IF NOT EXISTS idx_test_case_test_set_id ON test_case(test_set_id);
CREATE INDEX IF NOT EXISTS idx_task_team_id ON evaluation_task(team_id);
CREATE INDEX IF NOT EXISTS idx_task_test_set_id ON evaluation_task(test_set_id);
CREATE INDEX IF NOT EXISTS idx_task_agent_id ON evaluation_task(agent_id);
CREATE INDEX IF NOT EXISTS idx_task_status ON evaluation_task(status);
CREATE INDEX IF NOT EXISTS idx_result_task_id ON test_case_result(task_id);
CREATE INDEX IF NOT EXISTS idx_report_agent_id ON evaluation_report(agent_id);

-- 11. 初始化评测配置
INSERT INTO evaluation_config (agent_type, dimensions, grade_rules, regression_threshold) VALUES
('reasoning', 
 '{"tool_usage": {"weight": 0.6, "description": "工具调用准确性"}, "accuracy": {"weight": 0.4, "description": "答案准确性"}}',
 '{"A": [90, 100], "B": [80, 89], "C": [70, 79], "D": [60, 69], "F": [0, 59], "dimension_constraint": {"threshold": 60, "max_grade": "C"}}',
 10.00
),
('workflow',
 '{"flow_completeness": {"weight": 0.3, "description": "流程完整性"}, "node_performance": {"weight": 0.3, "description": "节点性能"}, "end_to_end_latency": {"weight": 0.2, "description": "端到端耗时"}, "result_quality": {"weight": 0.2, "description": "结果质量"}}',
 '{"A": [90, 100], "B": [80, 89], "C": [70, 79], "D": [60, 69], "F": [0, 59], "dimension_constraint": {"threshold": 60, "max_grade": "C"}}',
 10.00
) ON CONFLICT (agent_type) DO NOTHING;

COMMIT;
```

---

*文档状态：待评审*
