# 智能体评测系统 - 编排智能体评测器设计

> 文档版本：V1.0  
> 日期：2026-04-20  
> 状态：初稿，待评审

---

## 一、编排智能体概述

### 1.1 什么是编排智能体

编排智能体（Orchestration Agent）是在推理智能体基础上增加了多 Agent 协作调度能力的智能体类型。其本质是：**一个"编排层"负责协调多个子 Agent（推理智能体）协作完成任务**。

典型结构：

```
用户问题
    ↓
编排层（Orchestrator）
    ↓
┌─────────┐  ┌─────────┐  ┌─────────┐
│子Agent A │→ │子Agent B │→ │子Agent C │
│文档解析  │  │数据分析  │  │报告生成  │
└─────────┘  └─────────┘  └─────────┘
    ↓
编排层汇总结果 → 最终回答
```

### 1.2 编排智能体 vs 推理智能体

| 维度 | 推理智能体 | 编排智能体 |
|------|----------|----------|
| Agent 层级 | 单层 | 双层（编排层 + 子 Agent） |
| 工具调用 | 调用 MCP/Skill 等外部工具 | 调用子 Agent（本质也是一种"工具"） |
| 日志采集 | 工具调用日志 | 子 Agent 调用链日志 |
| 评测重点 | 单 Agent 的意图识别 + 工具调用 | 编排合理性 + 结果聚合质量 + 调用链稳定性 |
| LLM 依赖 | LLM 评判答案质量 | LLM 评判编排逻辑 + 结果质量 |

### 1.3 编排智能体评测定位

在评测体系中的位置：

```
推理智能体评测器 (ReasoningEvaluator)
    → 评测单 Agent 的工具调用和回答质量
          ↓
编排智能体评测器 (OrchestrationEvaluator)  ← 新增
    → 评测编排层对子 Agent 的调度能力
    → 同时复用 ReasoningEvaluator 评测各子 Agent
          ↓
工作流智能体评测器 (WorkflowEvaluator)
    → 评测 DAG 节点串联执行
```

---

## 二、编排智能体评测维度

### 2.1 评测维度定义

| 维度 | 权重 | 评测方式 | 说明 |
|------|------|----------|------|
| **编排合理性** | 30% | LLM 评委 | 是否调用了正确的子 Agent，顺序是否合理 |
| **结果聚合质量** | 25% | LLM 评委 | 是否正确合并多 Agent 输出，无冲突/遗漏 |
| **死循环检测** | 15% | 系统自动 | 是否存在异常重复调用 |
| **端到端效果** | 20% | LLM 评委 | 最终回答是否解决了用户问题 |
| **子 Agent 工具调用** | 10% | 系统 + LLM | 各子 Agent 的工具调用是否正确 |

### 2.2 各维度详细说明

#### 编排合理性（30%）

评判编排层是否"聪明地"调度了子 Agent：

| 情况 | 评分 | 说明 |
|------|------|------|
| 调用了所有必要的子 Agent，且顺序合理 | 90-100 | 正确理解任务并合理分解 |
| 调用了必要的子 Agent，但顺序欠佳 | 70-89 | 结果正确但效率低 |
| 遗漏了必要的子 Agent | 40-69 | 任务分解不完整 |
| 调用了错误的子 Agent 或完全跑偏 | 0-39 | 意图理解错误 |
| 调用了完全不相关的子 Agent | 0 | 完全错误 |

#### 结果聚合质量（25%）

评判编排层是否正确合并了多个子 Agent 的输出：

| 情况 | 评分 | 说明 |
|------|------|------|
| 各子 Agent 结果正确合并，无冲突无遗漏 | 90-100 | 聚合完美 |
| 有轻微遗漏或重复，但不影响最终效果 | 70-89 | 基本正确 |
| 存在关键信息丢失 | 40-69 | 聚合有缺陷 |
| 各子 Agent 结果直接拼接，未做聚合 | 0-39 | 无聚合 |
| 输出相互矛盾的结论 | 0 | 冲突未处理 |

#### 死循环检测（15%）

通过子 Agent 调用次数判定：

| 情况 | 评分 | 说明 |
|------|------|------|
| 任一子 Agent 调用次数 ≤ max_calls | 100 | 无异常 |
| 任一子 Agent 调用次数 > max_calls 但 ≤ max_calls×2 | 60-99 | 效率低 |
| 任一子 Agent 调用次数 > max_calls×2 | 0-59 | 可能死循环 |
| 检测到明确的死循环（返回相同结果循环3次+） | 0 | 死循环 |

#### 端到端效果（20%）

评判最终回答是否解决了用户原始问题：

- 复用推理智能体的答案准确性评判标准
- 由 LLM 评委独立打分

#### 子 Agent 工具调用（10%）

评判各子 Agent 内部的工具调用质量：

- 复用推理智能体的工具调用评判逻辑
- 由系统自动判定（每个子 Agent 跑一遍推理评测逻辑）

---

## 三、编排调用链日志格式

### 3.1 日志结构

编排智能体的执行日志需要记录完整的调用链：

```json
{
  "orchestration_id": "orch-xxx",
  "user_query": "帮我分析这份竞品报告并给出建议",
  "sub_agent_calls": [
    {
      "call_id": 1,
      "sub_agent_id": "doc-parser",
      "sub_agent_name": "文档解析Agent",
      "input": "用户上传的竞品报告PDF",
      "output": "解析后的文本内容...",
      "status": "success",
      "latency_ms": 1200,
      "tool_calls": [
        {
          "tool_name": "pdf_parser",
          "arguments": {"file_path": "/tmp/report.pdf"},
          "status": "success",
          "latency_ms": 800
        }
      ]
    },
    {
      "call_id": 2,
      "sub_agent_id": "data-analyst",
      "sub_agent_name": "数据分析Agent",
      "input": "竞品报告文本内容",
      "output": "SWOT分析结果...",
      "status": "success",
      "latency_ms": 3500,
      "tool_calls": [
        {
          "tool_name": "knowledge_retrieval",
          "arguments": {"query": "竞品分析方法论"},
          "status": "success",
          "latency_ms": 200
        }
      ]
    },
    {
      "call_id": 3,
      "sub_agent_id": "report-generator",
      "sub_agent_name": "报告生成Agent",
      "input": "SWOT分析结果",
      "output": "最终报告全文...",
      "status": "success",
      "latency_ms": 2000,
      "tool_calls": []
    }
  ],
  "final_response": "综合分析报告...",
  "total_latency_ms": 6700,
  "orchestration_pattern": "sequential"
}
```

### 3.2 编排模式识别

| 模式 | 说明 | 示例 |
|------|------|------|
| `sequential` | 顺序执行 | A → B → C |
| `parallel` | 并行执行 | A ‖ B ‖ C |
| `conditional` | 条件分支 | if X then A else B |
| `loop` | 循环执行 | A → B → A → B... |
| `mixed` | 混合模式 | (A ‖ B) → C |

---

## 四、编排评测器核心实现

### 4.1 类设计

```python
from dataclasses import dataclass, field
from typing import List, Dict, Any, Optional, Literal
from enum import Enum
from .base import BaseEvaluator, EvaluationInput, EvaluationOutput, EvaluationResult


class OrchestrationPattern(str, Enum):
    SEQUENTIAL = "sequential"
    PARALLEL = "parallel"
    CONDITIONAL = "conditional"
    LOOP = "loop"
    MIXED = "mixed"


@dataclass
class SubAgentCall:
    """子 Agent 调用记录"""
    call_id: int
    sub_agent_id: str
    sub_agent_name: str
    input: str
    output: str
    status: str  # success / failed / timeout
    latency_ms: int
    tool_calls: List[Dict[str, Any]] = field(default_factory=list)


@dataclass
class OrchestrationCallChain:
    """编排调用链"""
    orchestration_id: str
    user_query: str
    sub_agent_calls: List[SubAgentCall] = field(default_factory=list)
    final_response: str = ""
    total_latency_ms: int = 0
    orchestration_pattern: OrchestrationPattern = OrchestrationPattern.SEQUENTIAL
    error: Optional[str] = None


@dataclass
class OrchestrationEvaluationInput(EvaluationInput):
    """编排评测输入"""
    expected_sub_agents: Optional[List[str]] = None      # 期望调用的子 Agent
    expected_order: Optional[List[str]] = None          # 期望的调用顺序
    max_sub_agent_calls: Optional[int] = None           # 单子 Agent 最大调用次数
    conflict_scenario: bool = False                     # 是否为冲突场景测试


class OrchestrationEvaluator(BaseEvaluator):
    """编排智能体评测器"""

    def __init__(
        self,
        agent_id: int,
        agent_config: Dict[str, Any],
        seaf_api_base: str,
        seaf_api_key: str,
        llm_judge: Any,
        reasoning_evaluator: Optional[BaseEvaluator] = None
    ):
        super().__init__(agent_id, agent_config)
        self.seaf_api_base = seaf_api_base
        self.seaf_api_key = seaf_api_key
        self.llm_judge = llm_judge
        self.reasoning_evaluator = reasoning_evaluator  # 复用推理评测器评分子Agent

    def get_evaluation_dimensions(self) -> List[str]:
        return [
            "orchestration_reasonableness",
            "result_aggregation",
            "dead_loop_detection",
            "end_to_end_effect",
            "sub_agent_tool_usage"
        ]

    async def evaluate(self, input_data: OrchestrationEvaluationInput) -> EvaluationOutput:
        """执行编排智能体评测"""
        start_time = time.time()
        call_chain = OrchestrationCallChain(
            orchestration_id=f"orch-{input_data.case_id}",
            user_query=input_data.query
        )
        error = None

        try:
            # 调用编排智能体，采集完整调用链
            call_chain = await self._call_orchestration_agent(input_data.query)
        except Exception as e:
            error = str(e)

        latency_ms = int((time.time() - start_time) * 1000)
        call_chain.total_latency_ms = latency_ms

        return EvaluationOutput(
            case_id=input_data.case_id,
            query=input_data.query,
            agent_response=call_chain.final_response,
            tool_call_log=[],  # 编排智能体不直接调用工具
            node_execution_log=self._serialize_call_chain(call_chain),
            latency_ms=latency_ms,
            error=error
        )

    async def _call_orchestration_agent(self, query: str) -> OrchestrationCallChain:
        """调用编排智能体并解析调用链"""
        import httpx
        import json

        async with httpx.AsyncClient(timeout=300) as client:
            response = await client.post(
                f"{self.seaf_api_base}/seaf/api/chat/orchestration_ask",
                headers={"Authorization": f"Bearer {self.seaf_api_key}"},
                json={
                    "agent_id": self.agent_id,
                    "message": query,
                    "stream": False,
                    "include_call_chain": True  # 要求返回完整调用链
                }
            )
            response.raise_for_status()
            result = response.json()

            return self._parse_orchestration_response(result)

    def _parse_orchestration_response(self, response_data: Dict) -> OrchestrationCallChain:
        """解析编排智能体响应，提取调用链"""
        chain = OrchestrationCallChain(
            orchestration_id=response_data.get("orchestration_id", ""),
            user_query=response_data.get("query", "")
        )

        # 解析子 Agent 调用记录
        raw_calls = response_data.get("sub_agent_calls", [])
        for raw in raw_calls:
            sub_call = SubAgentCall(
                call_id=raw.get("call_id", 0),
                sub_agent_id=raw.get("sub_agent_id", ""),
                sub_agent_name=raw.get("sub_agent_name", ""),
                input=raw.get("input", ""),
                output=raw.get("output", ""),
                status=raw.get("status", "unknown"),
                latency_ms=raw.get("latency_ms", 0),
                tool_calls=raw.get("tool_calls", [])
            )
            chain.sub_agent_calls.append(sub_call)

        chain.final_response = response_data.get("final_response", "")
        chain.orchestration_pattern = OrchestrationPattern(
            response_data.get("pattern", "sequential")
        )

        return chain

    def _serialize_call_chain(self, chain: OrchestrationCallChain) -> List[Dict]:
        """将调用链序列化为 List[Dict]，存入 node_execution_log"""
        return [
            {
                "call_id": c.call_id,
                "sub_agent_id": c.sub_agent_id,
                "sub_agent_name": c.sub_agent_name,
                "status": c.status,
                "latency_ms": c.latency_ms,
                "pattern": chain.orchestration_pattern.value
            }
            for c in chain.sub_agent_calls
        ]

    async def judge(
        self,
        output: EvaluationOutput,
        input_data: OrchestrationEvaluationInput
    ) -> EvaluationResult:
        """编排智能体评判"""
        if output.error:
            return EvaluationResult(
                case_id=output.case_id,
                scores={dim: 0 for dim in self.get_evaluation_dimensions()},
                weighted_score=0,
                passed=False,
                latency_ms=output.latency_ms,
                llm_response={"error": output.error}
            )

        call_chain_dict = output.node_execution_log  # List[Dict]
        scores = {}

        # 1. 编排合理性（LLM 评委）
        scores["orchestration_reasonableness"] = await self._judge_orchestration_reasonableness(
            output.query, output.agent_response, call_chain_dict, input_data
        )

        # 2. 结果聚合质量（LLM 评委）
        scores["result_aggregation"] = await self._judge_result_aggregation(
            output.query, call_chain_dict, output.agent_response
        )

        # 3. 死循环检测（系统自动）
        scores["dead_loop_detection"] = self._judge_dead_loop(
            call_chain_dict, input_data.max_sub_agent_calls
        )

        # 4. 端到端效果（LLM 评委）
        scores["end_to_end_effect"] = await self._judge_end_to_end_effect(
            output.query, output.agent_response
        )

        # 5. 子 Agent 工具调用（系统 + LLM）
        scores["sub_agent_tool_usage"] = await self._judge_sub_agent_tool_usage(call_chain_dict)

        # 计算加权总分
        weighted_score = self._calculate_weighted_score(scores)

        return EvaluationResult(
            case_id=output.case_id,
            scores=scores,
            weighted_score=weighted_score,
            passed=weighted_score >= 60,
            latency_ms=output.latency_ms
        )

    def _judge_dead_loop(
        self,
        call_chain: List[Dict],
        max_calls: Optional[int] = None
    ) -> int:
        """判定死循环——系统自动"""
        if not call_chain:
            return 100  # 无子 Agent 调用，但未出错

        # 统计每个子 Agent 的调用次数
        call_counts: Dict[str, int] = {}
        for call in call_chain:
            sub_id = call.get("sub_agent_id", "")
            call_counts[sub_id] = call_counts.get(sub_id, 0) + 1

        max_allowed = max_calls or 3  # 默认单子Agent最多调用3次

        # 检查是否超过阈值
        max_actual = max(call_counts.values())
        if max_actual <= max_allowed:
            return 100
        elif max_actual <= max_allowed * 2:
            # 效率低，但未死循环
            return int(100 - (max_actual - max_allowed) * 20)
        else:
            # 可能死循环
            return max(0, 60 - (max_actual - max_allowed * 2) * 20)

    async def _judge_orchestration_reasonableness(
        self,
        query: str,
        final_response: str,
        call_chain: List[Dict],
        input_data: OrchestrationEvaluationInput
    ) -> int:
        """评判编排合理性——LLM评委"""
        sub_agents_called = [c.get("sub_agent_name", "") for c in call_chain]
        expected = input_data.expected_sub_agents or []
        expected_order = input_data.expected_order or []

        sub_agents_str = ", ".join(sub_agents_called) if sub_agents_called else "无"
        expected_str = ", ".join(expected) if expected else "未指定期望"

        prompt = f"""【角色】
你是一个专业的 AI 编排评测专家。请评判编排层是否合理地调度了子 Agent。

【输入信息】
用户问题：{query}
实际调用的子 Agent：{sub_agents_str}
期望调用的子 Agent（如有）：{expected_str}
最终回答：{final_response[:500]}

【评判标准】

请根据以下规则打分（0-100）：

1. 调用了所有必要的子 Agent，且顺序合理 → 90-100 分
2. 调用了必要的子 Agent，但顺序欠佳 → 70-89 分
3. 遗漏了必要的子 Agent → 40-69 分
4. 调用了错误的子 Agent 或完全跑偏 → 0-39 分
5. 调用了完全不相关的子 Agent → 0 分

【输出格式】（严格 JSON）
{{
  "score": <分数(0-100)>,
  "reasoning": "<评分理由>"
}}
"""
        raw = await self.llm_judge._call_llm(prompt)
        try:
            data = json.loads(raw)
            return int(data.get("score", 0))
        except Exception:
            return 0

    async def _judge_result_aggregation(
        self,
        query: str,
        call_chain: List[Dict],
        final_response: str
    ) -> int:
        """评判结果聚合质量——LLM评委"""
        sub_outputs = []
        for c in call_chain:
            sub_outputs.append(
                f"[{c.get('sub_agent_name','')}]: {c.get('output','')[:200]}"
            )
        sub_outputs_str = "\n".join(sub_outputs)

        prompt = f"""【角色】
你是一个专业的 AI 编排评测专家。请评判编排层是否正确合并了多个子 Agent 的输出。

【输入信息】
用户问题：{query}
各子 Agent 输出摘要：
{sub_outputs_str}

最终聚合回答：{final_response[:500]}

【评判标准】

1. 各子 Agent 结果正确合并，无冲突无遗漏 → 90-100 分
2. 有轻微遗漏或重复，但不影响最终效果 → 70-89 分
3. 存在关键信息丢失 → 40-69 分
4. 各子 Agent 结果直接拼接，未做聚合 → 0-39 分
5. 输出相互矛盾的结论 → 0 分

【输出格式】（严格 JSON）
{{
  "score": <分数(0-100)>,
  "reasoning": "<评分理由>"
}}
"""
        raw = await self.llm_judge._call_llm(prompt)
        try:
            data = json.loads(raw)
            return int(data.get("score", 0))
        except Exception:
            return 0

    async def _judge_end_to_end_effect(
        self,
        query: str,
        final_response: str
    ) -> int:
        """评判端到端效果——LLM评委"""
        prompt = f"""【角色】
你是一个专业的 AI 评测专家。请评判最终回答是否解决了用户的原始问题。

【输入信息】
用户问题：{query}
最终回答：{final_response}

【评判标准】

1. 完全正确解决了用户问题 → 90-100 分
2. 基本解决了问题，但有瑕疵 → 70-89 分
3. 部分解决了问题，有明显遗漏 → 40-69 分
4. 完全未解决用户问题 → 0-39 分

【输出格式】（严格 JSON）
{{
  "score": <分数(0-100)>,
  "reasoning": "<评分理由>"
}}
"""
        raw = await self.llm_judge._call_llm(prompt)
        try:
            data = json.loads(raw)
            return int(data.get("score", 0))
        except Exception:
            return 0

    async def _judge_sub_agent_tool_usage(self, call_chain: List[Dict]) -> int:
        """评判子 Agent 工具调用——系统+LLM"""
        if not call_chain:
            return 100  # 无子 Agent 调用

        tool_usage_scores = []
        for call in call_chain:
            tool_calls = call.get("tool_calls", [])
            if not tool_calls:
                tool_usage_scores.append(100)
                continue

            # 系统自动判定工具调用是否有错误
            error_count = sum(
                1 for t in tool_calls if t.get("status") != "success"
            )
            score = max(0, 100 - error_count * 30)
            tool_usage_scores.append(score)

        return int(sum(tool_usage_scores) / len(tool_usage_scores))

    def _calculate_weighted_score(self, scores: Dict[str, int]) -> int:
        """计算编排智能体加权总分"""
        weights = {
            "orchestration_reasonableness": 0.30,
            "result_aggregation": 0.25,
            "dead_loop_detection": 0.15,
            "end_to_end_effect": 0.20,
            "sub_agent_tool_usage": 0.10
        }
        total = sum(scores.get(dim, 0) * w for dim, w in weights.items())
        return int(total)
```

---

## 五、死循环检测详细逻辑

### 5.1 检测算法

```python
from typing import List, Dict, Tuple


def detect_dead_loop(call_chain: List[Dict]) -> Tuple[int, List[str]]:
    """
    检测死循环

    返回: (score, warnings)
        - score: 死循环检测得分 (0-100)
        - warnings: 警告信息列表
    """
    if not call_chain:
        return 100, []

    warnings = []

    # 1. 统计各子 Agent 调用次数
    call_counts: Dict[str, int] = {}
    for call in call_chain:
        sub_id = call.get("sub_agent_id", "unknown")
        call_counts[sub_id] = call_counts.get(sub_id, 0) + 1

    # 2. 检测重复调用模式（连续调用同一子Agent）
    consecutive_calls = 0
    max_consecutive = 0
    prev_id = None
    for call in call_chain:
        curr_id = call.get("sub_agent_id")
        if curr_id == prev_id:
            consecutive_calls += 1
            max_consecutive = max(max_consecutive, consecutive_calls)
        else:
            consecutive_calls = 1
        prev_id = curr_id

    if max_consecutive >= 3:
        warnings.append(f"检测到连续调用同一子Agent {max_consecutive} 次，可能存在死循环")

    # 3. 检测结果重复（相同输出循环）
    outputs = [call.get("output", "") for call in call_chain]
    repeat_count = count_consecutive_repeats(outputs)
    if repeat_count >= 3:
        warnings.append(f"检测到相同输出连续重复 {repeat_count} 次，明确死循环")
        return 0, warnings

    # 4. 计算得分
    max_calls = max(call_counts.values())
    if max_calls <= 3:
        score = 100
    elif max_calls <= 6:
        score = int(100 - (max_calls - 3) * 15)
    else:
        score = max(0, 60 - (max_calls - 6) * 20)
        warnings.append(f"子Agent调用次数过多（{max_calls}次），可能存在死循环")

    return max(0, score), warnings


def count_consecutive_repeats(items: List[str]) -> int:
    """统计连续重复项的最大次数"""
    if not items:
        return 0

    max_count = 1
    current_count = 1
    prev = items[0]

    for item in items[1:]:
        if item == prev:
            current_count += 1
            max_count = max(max_count, current_count)
        else:
            current_count = 1
        prev = item

    return max_count
```

### 5.2 死循环配置

```yaml
# 死循环检测配置
dead_loop_detection:
  # 单子 Agent 最大调用次数（默认）
  default_max_calls: 3

  # 连续重复输出阈值（检测死循环）
  max_consecutive_repeats: 3

  # 子 Agent 专属配置
  agent_overrides:
    "data-analyst":
      max_calls: 5  # 数据分析可能需要多次调用
    "search-agent":
      max_calls: 10  # 搜索可能需要多次调用
```

---

## 六、编排调用链的 Seaf 接口要求

编排评测依赖编排智能体返回完整调用链日志。Seaf 编排智能体需要提供以下能力：

### 6.1 接口要求

**请求**
```
POST /seaf/api/chat/orchestration_ask
```

**请求参数**

| 参数 | 类型 | 必填 | 说明 |
|------|------|------|------|
| agent_id | int | 是 | 编排智能体 ID |
| message | string | 是 | 用户问题 |
| stream | bool | 否 | 是否流式返回，默认 false |
| include_call_chain | bool | 是 | **必须为 true**，要求返回完整调用链 |

**响应（含调用链）**

```json
{
  "orchestration_id": "orch-xxx",
  "query": "帮我分析竞品报告并给出建议",
  "pattern": "sequential",
  "sub_agent_calls": [
    {
      "call_id": 1,
      "sub_agent_id": "doc-parser",
      "sub_agent_name": "文档解析Agent",
      "input": "用户上传的PDF",
      "output": "解析后的文本...",
      "status": "success",
      "latency_ms": 1200,
      "tool_calls": [
        {"tool_name": "pdf_parser", "arguments": {}, "status": "success", "latency_ms": 800}
      ]
    }
  ],
  "final_response": "综合分析报告...",
  "total_latency_ms": 6700
}
```

### 6.2 最低返回字段要求

| 字段 | 必填 | 说明 |
|------|------|------|
| `sub_agent_calls` | ✅ | 子 Agent 调用列表 |
| `sub_agent_calls[].sub_agent_id` | ✅ | 子 Agent 标识 |
| `sub_agent_calls[].sub_agent_name` | ✅ | 子 Agent 名称（人类可读） |
| `sub_agent_calls[].status` | ✅ | success / failed / timeout |
| `sub_agent_calls[].output` | ✅ | 子 Agent 文本输出 |
| `sub_agent_calls[].latency_ms` | ✅ | 耗时（毫秒） |
| `final_response` | ✅ | 编排层最终回答 |
| `pattern` | ⚠️ | 编排模式，不提供则默认 sequential |

> ⚠️ **重要**：Seaf 编排智能体必须支持 `include_call_chain=true` 参数，否则编排评测器无法采集调用链日志。如当前版本不支持，需在 Seaf 侧补充开发此能力。

---

## 七、编排评测集数据结构

### 7.1 评测数据项结构

```json
{
  "id": "orch-001",
  "name": "竞品分析场景",
  "agent_type": "orchestration",
  "query": "帮我分析这份竞品报告并给出建议",
  "expected_sub_agents": ["文档解析Agent", "数据分析Agent", "报告生成Agent"],
  "expected_order": ["文档解析Agent", "数据分析Agent", "报告生成Agent"],
  "max_sub_agent_calls": 3,
  "conflict_scenario": false,
  "expected_answer_keywords": ["优势", "劣势", "机会", "威胁", "建议"],
  "tags": ["竞品分析", "多Agent协作"],
  "difficulty": "hard"
}
```

### 7.2 字段说明

| 字段 | 类型 | 必填 | 说明 |
|------|------|------|------|
| `expected_sub_agents` | string[] | 否 | 期望调用的子 Agent 名称列表 |
| `expected_order` | string[] | 否 | 期望的调用顺序 |
| `max_sub_agent_calls` | int | 否 | 单子 Agent 最大调用次数，默认 3 |
| `conflict_scenario` | bool | 否 | 是否为冲突场景测试（多个子 Agent 结论矛盾） |

---

## 八、与推理评测器的集成

编排评测器在内部复用推理评测器来评测各个子 Agent 的工具调用质量：

```python
class OrchestrationEvaluator:
    def __init__(self, ..., reasoning_evaluator: BaseEvaluator):
        self.reasoning_evaluator = reasoning_evaluator

    async def _judge_sub_agent_tool_usage(self, call_chain: List[Dict]) -> int:
        """复用推理评测器评分子 Agent"""
        scores = []
        for call in call_chain:
            tool_calls = call.get("tool_calls", [])
            if not tool_calls:
                scores.append(100)
                continue

            # 构造推理评测输入
            input_data = EvaluationInput(
                case_id=call["call_id"],
                query=call.get("input", ""),
                expected_tools=None
            )
            output = EvaluationOutput(
                case_id=call["call_id"],
                query=call.get("input", ""),
                agent_response=call.get("output", ""),
                tool_call_log=tool_calls,
                node_execution_log=[],
                latency_ms=call.get("latency_ms", 0)
            )

            # 调用推理评测器的 judge 方法
            result = await self.reasoning_evaluator.judge(output)
            tool_score = result.scores.get("tool_usage", 100)
            scores.append(tool_score)

        return int(sum(scores) / len(scores)) if scores else 100
```

---

## 九、目录结构更新

```
evaluation_system/
├── evaluator/
│   ├── __init__.py
│   ├── base.py                  # 评测器基类
│   ├── reasoning_evaluator.py   # 推理评测器 ✅
│   ├── workflow_evaluator.py    # 工作流评测器 ✅
│   ├── orchestration_evaluator.py # 编排评测器 ✅ (新增)
│   └── executor.py              # 评测执行器
```

---

## 十、测试用例设计

### 10.1 编排合理性测试

```python
import pytest


class TestOrchestrationReasonableness:
    """编排合理性评判测试"""

    @pytest.fixture
    def evaluator(self):
        return OrchestrationEvaluator(...)

    @pytest.mark.asyncio
    async def test_correct_sub_agents_sequential(self, evaluator):
        """正确调用子Agent，顺序合理 → 高分"""
        call_chain = [
            {"sub_agent_name": "文档解析", "status": "success", "latency_ms": 1000},
            {"sub_agent_name": "数据分析", "status": "success", "latency_ms": 3000},
            {"sub_agent_name": "报告生成", "status": "success", "latency_ms": 2000},
        ]
        score = await evaluator._judge_orchestration_reasonableness(
            query="分析报告并给出建议",
            final_response="综合分析报告...",
            call_chain=call_chain,
            input_data=OrchestrationEvaluationInput(
                case_id=1,
                query="分析报告并给出建议",
                expected_sub_agents=["文档解析", "数据分析", "报告生成"],
                expected_order=["文档解析", "数据分析", "报告生成"]
            )
        )
        assert score >= 70

    @pytest.mark.asyncio
    async def test_wrong_order_penalized(self, evaluator):
        """顺序不合理 → 扣分"""
        call_chain = [
            {"sub_agent_name": "报告生成", "status": "success", "latency_ms": 2000},
            {"sub_agent_name": "数据分析", "status": "success", "latency_ms": 3000},
            {"sub_agent_name": "文档解析", "status": "success", "latency_ms": 1000},
        ]
        score = await evaluator._judge_orchestration_reasonableness(
            query="分析报告并给出建议",
            final_response="综合分析报告...",
            call_chain=call_chain,
            input_data=OrchestrationEvaluationInput(
                case_id=1,
                query="分析报告并给出建议",
                expected_order=["文档解析", "数据分析", "报告生成"]
            )
        )
        assert score < 90  # 顺序错了，应该扣分


class TestDeadLoopDetection:
    """死循环检测测试"""

    def test_no_loop(self):
        """正常调用 → 满分"""
        call_chain = [
            {"sub_agent_id": "A"}, {"sub_agent_id": "B"}, {"sub_agent_id": "C"}
        ]
        score, warnings = detect_dead_loop(call_chain)
        assert score == 100
        assert len(warnings) == 0

    def test_excessive_calls(self):
        """同一子Agent调用10次 → 低分"""
        call_chain = [{"sub_agent_id": "A"}] * 10
        score, warnings = detect_dead_loop(call_chain)
        assert score < 20
        assert len(warnings) > 0

    def test_consecutive_repeats(self):
        """连续相同输出 → 死循环"""
        call_chain = [
            {"sub_agent_id": "A", "output": "结果X"},
            {"sub_agent_id": "A", "output": "结果X"},
            {"sub_agent_id": "A", "output": "结果X"},
        ]
        score, warnings = detect_dead_loop(call_chain)
        assert score == 0
        assert any("死循环" in w for w in warnings)
```

---

*文档状态：待评审*

*如有问题或建议，请联系负责人。*
