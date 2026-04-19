# 智能体评测系统 - 评测器设计

> 文档版本：V1.0  
> 日期：2026-04-19  
> 状态：待评审

---

## 一、评测器架构

### 1.1 评测器定位

评测器（Evaluator）是评测系统的核心执行单元，负责：
1. 调用被测智能体
2. 采集执行日志
3. 将结果传递给 LLM 评委打分
4. 计算性能指标（仅工作流）

### 1.2 评测器抽象设计

```python
from abc import ABC, abstractmethod
from dataclasses import dataclass
from typing import List, Dict, Any, Optional
from enum import Enum


class AgentType(str, Enum):
    REASONING = "reasoning"
    WORKFLOW = "workflow"


@dataclass
class EvaluationInput:
    """评测输入"""
    case_id: int
    query: str
    expected_tools: Optional[List[str]] = None
    expected_nodes: Optional[List[str]] = None
    max_node_latency_ms: Optional[int] = None
    max_total_latency_ms: Optional[int] = None


@dataclass
class EvaluationOutput:
    """评测输出"""
    case_id: int
    query: str
    agent_response: str
    tool_call_log: List[Dict[str, Any]]
    node_execution_log: List[Dict[str, Any]]
    latency_ms: int
    error: Optional[str] = None


@dataclass
class EvaluationResult:
    """评测结果"""
    case_id: int
    scores: Dict[str, int]
    weighted_score: int
    passed: bool
    latency_ms: int
    llm_response: Optional[Dict[str, Any]] = None


class BaseEvaluator(ABC):
    """评测器基类"""
    
    def __init__(self, agent_id: int, agent_config: Dict[str, Any]):
        self.agent_id = agent_id
        self.agent_config = agent_config
    
    @abstractmethod
    async def evaluate(self, input_data: EvaluationInput) -> EvaluationOutput:
        """执行单条评测，返回原始输出"""
        pass
    
    @abstractmethod
    def get_evaluation_dimensions(self) -> List[str]:
        """返回评测维度列表"""
        pass
    
    async def batch_evaluate(
        self, 
        inputs: List[EvaluationInput],
        progress_callback=None
    ) -> List[EvaluationOutput]:
        """批量执行评测"""
        results = []
        for i, input_data in enumerate(inputs):
            result = await self.evaluate(input_data)
            results.append(result)
            if progress_callback:
                progress_callback(i + 1, len(inputs))
        return results
```

---

## 二、推理评测器设计

### 2.1 核心逻辑

```python
import httpx
import json
import time
from typing import List, Dict, Any, Optional
from .base import BaseEvaluator, EvaluationInput, EvaluationOutput, EvaluationResult
from ..llm_judge import LLMJudgeService


class ReasoningEvaluator(BaseEvaluator):
    """推理智能体评测器"""
    
    def __init__(
        self, 
        agent_id: int, 
        agent_config: Dict[str, Any],
        seaf_api_base: str,
        seaf_api_key: str,
        llm_judge: LLMJudgeService
    ):
        super().__init__(agent_id, agent_config)
        self.seaf_api_base = seaf_api_base
        self.seaf_api_key = seaf_api_key
        self.llm_judge = llm_judge
    
    def get_evaluation_dimensions(self) -> List[str]:
        return ["tool_usage", "accuracy"]
    
    async def evaluate(self, input_data: EvaluationInput) -> EvaluationOutput:
        """调用推理 Agent 并采集日志"""
        start_time = time.time()
        tool_call_log = []
        agent_response = ""
        error = None
        
        try:
            async with httpx.AsyncClient(timeout=120) as client:
                # 调用 Seaf Agent 对话接口
                response = await client.post(
                    f"{self.seaf_api_base}/seaf/api/chat/agent_ask",
                    headers={"Authorization": f"Bearer {self.seaf_api_key}"},
                    json={
                        "agent_id": self.agent_id,
                        "message": input_data.query,
                        "stream": False
                    }
                )
                response.raise_for_status()
                result = response.json()
                
                # 解析响应，提取工具调用日志和最终回答
                agent_response, tool_call_log = self._parse_response(result)
                
        except Exception as e:
            error = str(e)
            agent_response = ""
        
        latency_ms = int((time.time() - start_time) * 1000)
        
        return EvaluationOutput(
            case_id=input_data.case_id,
            query=input_data.query,
            agent_response=agent_response,
            tool_call_log=tool_call_log,
            node_execution_log=[],  # 推理 Agent 无节点日志
            latency_ms=latency_ms,
            error=error
        )
    
    def _parse_response(self, response_data: Dict) -> tuple[str, List[Dict]]:
        """解析 Seaf Agent 响应，提取工具调用和最终回答"""
        tool_call_log = []
        agent_response = ""
        
        # 遍历响应中的消息，提取工具调用和最终回答
        messages = response_data.get("messages", [])
        for msg in messages:
            msg_type = msg.get("type", "")
            content = msg.get("content", "")
            
            if msg_type == "mcp_tool_request":
                # 工具调用请求
                tool_call_log.append({
                    "tool_name": msg.get("tool_name", ""),
                    "arguments": msg.get("arguments", {}),
                    "status": "requested",
                    "latency_ms": 0
                })
            elif msg_type == "mcp_server_response":
                # 工具调用结果
                if tool_call_log:
                    tool_call_log[-1]["result"] = content
                    tool_call_log[-1]["status"] = "success"
            elif msg_type == "answer":
                # 最终回答
                agent_response = content
        
        return agent_response, tool_call_log
    
    async def judge(
        self, 
        output: EvaluationOutput, 
        expected_tools: Optional[List[str]] = None
    ) -> EvaluationResult:
        """调用 LLM 评委打分"""
        if output.error:
            return EvaluationResult(
                case_id=output.case_id,
                scores={"tool_usage": 0, "accuracy": 0},
                weighted_score=0,
                passed=False,
                latency_ms=output.latency_ms,
                llm_response={"error": output.error}
            )
        
        # 调用 LLM 评委
        llm_response = await self.llm_judge.judge_reasoning(
            user_query=output.query,
            agent_response=output.agent_response,
            tool_call_log=output.tool_call_log,
            expected_tools=expected_tools
        )
        
        scores = llm_response.get("scores", {})
        weighted_score = llm_response.get("weighted_score", 0)
        
        return EvaluationResult(
            case_id=output.case_id,
            scores=scores,
            weighted_score=weighted_score,
            passed=weighted_score >= 60,  # 通过阈值
            latency_ms=output.latency_ms,
            llm_response=llm_response
        )
```

### 2.2 工具调用准确性判定逻辑

```python
def calculate_tool_usage_score(
    tool_call_log: List[Dict],
    expected_tools: Optional[List[str]] = None
) -> int:
    """计算工具调用得分"""
    if not expected_tools:
        # 无期望工具，只评估工具调用是否有错误
        if not tool_call_log:
            return 50  # 无工具调用但未出错
        error_count = sum(1 for t in tool_call_log if t.get("status") == "failed")
        if error_count > 0:
            return max(0, 100 - error_count * 30)
        return 100
    
    # 有期望工具的情况
    called_tools = set(t.get("tool_name", "") for t in tool_call_log)
    expected_set = set(expected_tools)
    
    # 完全匹配
    if called_tools == expected_set:
        return 100
    
    # 计算匹配度
    matched = len(called_tools & expected_set)
    total = len(expected_set)
    
    # 额外调用的工具
    extra = called_tools - expected_set
    
    score = (matched / total) * 80  # 匹配度占 80 分
    if extra:
        score -= len(extra) * 10  # 每多一个工具扣 10 分
    
    return max(0, min(100, int(score)))
```

---

## 三、工作流评测器设计

### 3.1 核心逻辑

```python
import httpx
import json
import time
from typing import List, Dict, Any, Optional
from .base import BaseEvaluator, EvaluationInput, EvaluationOutput, EvaluationResult
from ..llm_judge import LLMJudgeService


class WorkflowEvaluator(BaseEvaluator):
    """工作流智能体评测器"""
    
    def __init__(
        self, 
        agent_id: int, 
        agent_config: Dict[str, Any],
        seaf_api_base: str,
        seaf_api_key: str,
        llm_judge: LLMJudgeService
    ):
        super().__init__(agent_id, agent_config)
        self.seaf_api_base = seaf_api_base
        self.seaf_api_key = seaf_api_key
        self.llm_judge = llm_judge
    
    def get_evaluation_dimensions(self) -> List[str]:
        return ["flow_completeness", "node_performance", "end_to_end_latency", "result_quality"]
    
    async def evaluate(self, input_data: EvaluationInput) -> EvaluationOutput:
        """触发工作流并采集节点执行日志"""
        start_time = time.time()
        node_execution_log = []
        workflow_output = ""
        error = None
        
        try:
            async with httpx.AsyncClient(timeout=300) as client:
                # 触发工作流执行
                response = await client.post(
                    f"{self.seaf_api_base}/seaf/api/workflow/execute",
                    headers={"Authorization": f"Bearer {self.seaf_api_key}"},
                    json={
                        "workflow_id": self.agent_config.get("workflow_id"),
                        "input": input_data.query,
                        "sync": False  # 异步执行，轮询获取结果
                    }
                )
                response.raise_for_status()
                execution_result = response.json()
                
                execution_id = execution_result.get("execution_id")
                
                # 轮询获取执行结果和节点日志
                max_polls = 60  # 最多轮询 60 次（5 分钟）
                for _ in range(max_polls):
                    status_response = await client.get(
                        f"{self.seaf_api_base}/seaf/api/workflow/execution/{execution_id}",
                        headers={"Authorization": f"Bearer {self.seaf_api_key}"}
                    )
                    status_data = status_response.json()
                    
                    if status_data.get("status") in ("completed", "failed"):
                        node_execution_log = status_data.get("node_log", [])
                        workflow_output = status_data.get("output", "")
                        break
                    
                    await asyncio.sleep(5)  # 每 5 秒轮询一次
                
                if not node_execution_log:
                    error = "工作流执行超时"
                    
        except Exception as e:
            error = str(e)
        
        latency_ms = int((time.time() - start_time) * 1000)
        
        return EvaluationOutput(
            case_id=input_data.case_id,
            query=input_data.query,
            agent_response=workflow_output,
            tool_call_log=[],  # 工作流无工具调用日志
            node_execution_log=node_execution_log,
            latency_ms=latency_ms,
            error=error
        )
    
    async def judge(
        self, 
        output: EvaluationOutput,
        expected_nodes: Optional[List[str]] = None,
        max_node_latency_ms: Optional[int] = None,
        max_total_latency_ms: Optional[int] = None
    ) -> EvaluationResult:
        """评判工作流评测结果"""
        scores = {}
        
        if output.error:
            scores = {
                "flow_completeness": 0,
                "node_performance": 0,
                "end_to_end_latency": 0,
                "result_quality": 0
            }
            weighted_score = 0
        else:
            # 1. 流程完整性判定
            scores["flow_completeness"] = self._judge_flow_completeness(
                output.node_execution_log, expected_nodes
            )
            
            # 2. 节点性能判定
            scores["node_performance"] = self._judge_node_performance(
                output.node_execution_log, max_node_latency_ms
            )
            
            # 3. 端到端耗时判定
            scores["end_to_end_latency"] = self._judge_end_to_end_latency(
                output.latency_ms, max_total_latency_ms
            )
            
            # 4. 结果质量 LLM 评判
            llm_response = await self.llm_judge.judge_workflow(
                user_query=output.query,
                workflow_output=output.agent_response,
                node_execution_log=output.node_execution_log
            )
            scores["result_quality"] = llm_response.get("scores", {}).get("result_quality", 0)
            
            # 计算加权总分
            weighted_score = self._calculate_weighted_score(scores)
        
        return EvaluationResult(
            case_id=output.case_id,
            scores=scores,
            weighted_score=weighted_score,
            passed=weighted_score >= 60,
            latency_ms=output.latency_ms,
            llm_response=llm_response if "llm_response" in dir() else None
        )
    
    def _judge_flow_completeness(
        self,
        node_log: List[Dict],
        expected_nodes: Optional[List[str]] = None
    ) -> int:
        """判定流程完整性"""
        if not expected_nodes:
            # 无期望节点，检查是否全部成功执行
            failed_count = sum(1 for n in node_log if n.get("status") != "success")
            if failed_count == 0:
                return 100
            return max(0, 100 - failed_count * 30)
        
        executed_nodes = set(n.get("node", "") for n in node_log)
        expected_set = set(expected_nodes)
        
        # 核心节点是否都执行了
        matched = len(executed_nodes & expected_set)
        total = len(expected_set)
        
        if matched == total:
            return 100
        
        # 每跳过一个核心节点扣 30 分
        skipped = total - matched
        return max(0, 100 - skipped * 30)
    
    def _judge_node_performance(
        self,
        node_log: List[Dict],
        max_latency_ms: Optional[int] = None
    ) -> int:
        """判定节点性能"""
        if not max_latency_ms:
            return 100  # 无阈值要求
        
        slow_count = 0
        for node in node_log:
            latency = node.get("latency_ms", 0)
            if latency > max_latency_ms:
                slow_count += 1
        
        if slow_count == 0:
            return 100
        
        # 每超时一个节点扣 20 分
        return max(0, 100 - slow_count * 20)
    
    def _judge_end_to_end_latency(
        self,
        total_latency_ms: int,
        max_latency_ms: Optional[int] = None
    ) -> int:
        """判定端到端耗时"""
        if not max_latency_ms:
            return 100  # 无阈值要求
        
        if total_latency_ms <= max_latency_ms:
            return 100
        
        # 超时直接扣 50 分
        return 50
    
    def _calculate_weighted_score(self, scores: Dict[str, int]) -> int:
        """计算加权总分"""
        weights = {
            "flow_completeness": 0.3,
            "node_performance": 0.3,
            "end_to_end_latency": 0.2,
            "result_quality": 0.2
        }
        
        total = sum(scores.get(dim, 0) * weight for dim, weight in weights.items())
        return int(total)
```

### 3.2 慢节点定位

```python
from dataclasses import dataclass
from typing import List, Dict, Any


@dataclass
class SlowNode:
    node: str
    avg_latency_ms: int
    threshold_ms: int
    exceed_ratio: float


def identify_slow_nodes(
    node_log: List[Dict],
    threshold_ms: int = 3000
) -> List[SlowNode]:
    """识别慢节点"""
    node_latencies: Dict[str, List[int]] = {}
    
    for entry in node_log:
        node = entry.get("node", "unknown")
        latency = entry.get("latency_ms", 0)
        
        if node not in node_latencies:
            node_latencies[node] = []
        node_latencies[node].append(latency)
    
    slow_nodes = []
    for node, latencies in node_latencies.items():
        avg_latency = sum(latencies) // len(latencies)
        if avg_latency > threshold_ms:
            exceed_ratio = (avg_latency - threshold_ms) / threshold_ms
            slow_nodes.append(SlowNode(
                node=node,
                avg_latency_ms=avg_latency,
                threshold_ms=threshold_ms,
                exceed_ratio=exceed_ratio
            ))
    
    # 按超出比例排序
    slow_nodes.sort(key=lambda x: x.exceed_ratio, reverse=True)
    return slow_nodes
```

---

## 四、评测执行器设计

### 4.1 评测执行器

```python
import asyncio
from typing import List, Dict, Any, Callable, Optional
from dataclasses import dataclass
import logging

from .base import EvaluationInput, EvaluationOutput, EvaluationResult, AgentType
from .reasoning_evaluator import ReasoningEvaluator
from .workflow_evaluator import WorkflowEvaluator
from ..llm_judge import LLMJudgeService
from ..models import EvaluationTask, TestCase, EvaluationReport
from ..database import Database


logger = logging.getLogger(__name__)


@dataclass
class ExecutionProgress:
    task_id: int
    total: int
    completed: int
    current_case_id: int
    estimated_remaining_seconds: int


class EvaluationExecutor:
    """评测执行器 - 负责调度整个评测流程"""
    
    def __init__(
        self,
        seaf_api_base: str,
        seaf_api_key: str,
        llm_judge: LLMJudgeService,
        db: Database
    ):
        self.seaf_api_base = seaf_api_base
        self.seaf_api_key = seaf_api_key
        self.llm_judge = llm_judge
        self.db = db
    
    async def execute_task(
        self,
        task_id: int,
        progress_callback: Optional[Callable[[ExecutionProgress], None]] = None
    ) -> EvaluationReport:
        """执行评测任务"""
        # 1. 加载任务和评测集信息
        task = await self.db.get_task(task_id)
        test_cases = await self.db.get_test_cases(task.test_set_id)
        agent_config = await self.db.get_agent_config(task.agent_id)
        
        # 2. 创建评测器
        evaluator = self._create_evaluator(task.agent_type, task.agent_id, agent_config)
        
        # 3. 更新任务状态
        await self.db.update_task_status(task_id, "running", started_at=datetime.now())
        
        # 4. 逐条执行评测
        results: List[EvaluationResult] = []
        for i, case in enumerate(test_cases):
            try:
                # 4.1 调用 Agent
                input_data = self._build_evaluation_input(case, task.agent_type)
                output = await evaluator.evaluate(input_data)
                
                # 4.2 LLM 评判
                result = await evaluator.judge(
                    output,
                    expected_tools=case.get("expected_tools"),
                    expected_nodes=case.get("expected_nodes"),
                    max_node_latency_ms=case.get("max_node_latency_ms"),
                    max_total_latency_ms=case.get("max_total_latency_ms")
                )
                results.append(result)
                
                # 4.3 保存结果
                await self._save_case_result(task_id, output, result)
                
                # 4.4 更新进度
                await self.db.update_task_progress(
                    task_id, 
                    completed_cases=i + 1,
                    progress=int((i + 1) / len(test_cases) * 100)
                )
                
                # 4.5 回调进度
                if progress_callback:
                    progress_callback(ExecutionProgress(
                        task_id=task_id,
                        total=len(test_cases),
                        completed=i + 1,
                        current_case_id=case.id,
                        estimated_remaining_seconds=0
                    ))
                    
            except Exception as e:
                logger.error(f"评测 case {case.id} 失败: {e}")
                # 记录失败结果
                await self._save_case_result(
                    task_id, 
                    EvaluationOutput(
                        case_id=case.id,
                        query=case.query,
                        agent_response="",
                        tool_call_log=[],
                        node_execution_log=[],
                        latency_ms=0,
                        error=str(e)
                    ),
                    EvaluationResult(
                        case_id=case.id,
                        scores={},
                        weighted_score=0,
                        passed=False,
                        latency_ms=0
                    )
                )
        
        # 5. 生成报告
        report = await self._generate_report(task_id, results)
        
        # 6. 更新任务完成状态
        await self.db.update_task_status(
            task_id, 
            "completed",
            completed_at=datetime.now()
        )
        
        return report
    
    def _create_evaluator(
        self,
        agent_type: str,
        agent_id: int,
        agent_config: Dict[str, Any]
    ):
        """根据类型创建评测器"""
        if agent_type == AgentType.REASONING:
            return ReasoningEvaluator(
                agent_id=agent_id,
                agent_config=agent_config,
                seaf_api_base=self.seaf_api_base,
                seaf_api_key=self.seaf_api_key,
                llm_judge=self.llm_judge
            )
        elif agent_type == AgentType.WORKFLOW:
            return WorkflowEvaluator(
                agent_id=agent_id,
                agent_config=agent_config,
                seaf_api_base=self.seaf_api_base,
                seaf_api_key=self.seaf_api_key,
                llm_judge=self.llm_judge
            )
        else:
            raise ValueError(f"不支持的智能体类型: {agent_type}")
    
    def _build_evaluation_input(self, case: Dict, agent_type: str) -> EvaluationInput:
        """构建评测输入"""
        return EvaluationInput(
            case_id=case["id"],
            query=case["query"],
            expected_tools=json.loads(case.get("expected_tools", "[]")) if case.get("expected_tools") else None,
            expected_nodes=json.loads(case.get("expected_nodes", "[]")) if case.get("expected_nodes") else None,
            max_node_latency_ms=case.get("max_node_latency_ms"),
            max_total_latency_ms=case.get("max_total_latency_ms")
        )
    
    async def _save_case_result(
        self,
        task_id: int,
        output: EvaluationOutput,
        result: EvaluationResult
    ):
        """保存单条评测结果"""
        await self.db.save_case_result(
            task_id=task_id,
            case_id=output.case_id,
            query=output.query,
            agent_response=output.agent_response,
            tool_call_log=output.tool_call_log,
            node_execution_log=output.node_execution_log,
            scores=result.scores,
            weighted_score=result.weighted_score,
            passed=result.passed,
            latency_ms=output.latency_ms,
            llm_response=result.llm_response
        )
    
    async def _generate_report(
        self,
        task_id: int,
        results: List[EvaluationResult]
    ) -> EvaluationReport:
        """生成评测报告"""
        # 汇总数据
        total = len(results)
        passed = sum(1 for r in results if r.passed)
        avg_latency = sum(r.latency_ms for r in results) // total if total > 0 else 0
        
        # 收集各维度得分
        dimension_scores: Dict[str, List[int]] = {}
        for r in results:
            for dim, score in r.scores.items():
                if dim not in dimension_scores:
                    dimension_scores[dim] = []
                dimension_scores[dim].append(score)
        
        by_dimension = {}
        for dim, scores in dimension_scores.items():
            avg_score = sum(scores) // len(scores)
            passed_dim = sum(1 for s in scores if s >= 60)
            by_dimension[dim] = {
                "score": avg_score,
                "weight": self._get_dimension_weight(dim),
                "passed": passed_dim,
                "failed": len(scores) - passed_dim
            }
        
        # 计算加权总分
        weighted_score = sum(
            by_dimension.get(dim, {}).get("score", 0) * by_dimension.get(dim, {}).get("weight", 0)
            for dim in by_dimension
        )
        
        # 计算 Grade
        grade = self._calculate_grade(weighted_score, by_dimension)
        
        # 回归检测
        regression = await self._check_regression(task_id, weighted_score)
        
        # 生成报告
        report = await self.db.save_report(
            task_id=task_id,
            summary={
                "total_cases": total,
                "passed": passed,
                "failed": total - passed,
                "pass_rate": f"{passed * 100 // total}%",
                "weighted_score": int(weighted_score),
                "grade": grade,
                "avg_latency_ms": avg_latency
            },
            by_dimension=by_dimension,
            regression=regression
        )
        
        # 触发告警
        if regression.get("detected"):
            await self._send_regression_alert(task_id, regression)
        
        return report
    
    def _get_dimension_weight(self, dim: str) -> float:
        """获取维度权重"""
        weights = {
            "tool_usage": 0.6,
            "accuracy": 0.4,
            "flow_completeness": 0.3,
            "node_performance": 0.3,
            "end_to_end_latency": 0.2,
            "result_quality": 0.2
        }
        return weights.get(dim, 0.0)
    
    def _calculate_grade(self, score: float, by_dimension: Dict) -> str:
        """计算 Grade"""
        # 检查维度约束
        for dim, data in by_dimension.items():
            if data.get("score", 0) < 60:
                return "D"  # 任一维度 < 60，Grade 不高于 C
        
        # 按分数区间定级
        if score >= 90:
            return "A"
        elif score >= 80:
            return "B"
        elif score >= 70:
            return "C"
        elif score >= 60:
            return "D"
        else:
            return "F"
    
    async def _check_regression(self, task_id: int, current_score: float) -> Dict:
        """回归检测"""
        # 获取同一智能体的上一次评测结果
        previous = await self.db.get_latest_report(task_id)
        if not previous:
            return {"detected": False}
        
        previous_score = previous.summary.get("weighted_score", 0)
        change = ((current_score - previous_score) / previous_score * 100) if previous_score > 0 else 0
        change_str = f"+{int(change)}%" if change >= 0 else f"{int(change)}%"
        
        # 检查是否超过阈值
        threshold = 10.0
        detected = change < -threshold
        
        return {
            "detected": detected,
            "previous_score": previous_score,
            "current_score": current_score,
            "change": change_str,
            "threshold": threshold
        }
    
    async def _send_regression_alert(self, task_id: int, regression: Dict):
        """发送回归告警"""
        # 获取通知配置
        task = await self.db.get_task(task_id)
        notifications = await self.db.get_notification_configs(task.team_id)
        
        for notification in notifications:
            if not notification.enabled:
                continue
            
            if notification.channel == "email":
                await self._send_email_alert(task, regression, notification.config)
            elif notification.channel == "webhook":
                await self._send_webhook_alert(task, regression, notification.config)
            elif notification.channel == "in_app":
                await self._send_in_app_alert(task, regression)
    
    async def _send_webhook_alert(self, task, regression, config):
        """发送 Webhook 告警"""
        import httpx
        async with httpx.AsyncClient() as client:
            await client.post(
                config.get("url"),
                json={
                    "event": "evaluation.regression",
                    "task_id": task.id,
                    "agent_id": task.agent_id,
                    "regression": regression
                }
            )
```

---

## 五、目录结构

```
evaluation_system/
├── __init__.py
├── main.py                    # FastAPI 应用入口
├── config.py                  # 配置管理
├── database.py                # 数据库操作
├── models.py                  # 数据模型
│
├── api/                       # API 层
│   ├── __init__.py
│   ├── router.py              # 路由注册
│   ├── test_sets.py           # 评测集 API
│   ├── tasks.py               # 任务 API
│   ├── reports.py             # 报告 API
│   └── config.py              # 配置 API
│
├── service/                   # 业务逻辑层
│   ├── __init__.py
│   ├── test_set_service.py    # 评测集服务
│   ├── task_service.py        # 任务服务
│   └── report_service.py      # 报告服务
│
├── evaluator/                 # 评测器
│   ├── __init__.py
│   ├── base.py                # 评测器基类
│   ├── reasoning_evaluator.py # 推理评测器
│   ├── workflow_evaluator.py   # 工作流评测器
│   └── executor.py             # 评测执行器
│
├── llm_judge/                 # LLM 评委
│   ├── __init__.py
│   ├── service.py             # LLM 评委服务
│   └── prompts.py             # Prompt 模板
│
├── worker/                    # Celery Worker
│   ├── __init__.py
│   ├── celery_app.py          # Celery 配置
│   └── tasks.py               # 异步任务
│
└── utils/                     # 工具函数
    ├── __init__.py
    ├── grade.py               # Grade 计算
    └── notification.py        # 通知工具
```

---

## 六、关键设计决策

### 6.1 为什么使用抽象基类设计评测器？

**好处：**
- 统一接口，方便后续扩展编排评测器
- 便于写单元测试（可以 Mock Evaluator）
- 评测器之间逻辑隔离，易维护

### 6.2 为什么用轮询方式获取工作流结果？

**原因：**
- Seaf 工作流接口暂不支持 WebSocket 推送
- 轮询间隔 5 秒，60 次（5 分钟）足够覆盖大多数场景
- 简单可靠，适合 MVP 阶段

**后续可优化：**
- 接入 WebSocket 实时推送
- 支持长时工作流的超时配置

### 6.3 为什么 LLM 评判单独调用？

**原因：**
- 评测输出和 LLM 打分可以独立失败和重试
- 性能指标判定不需要 LLM（系统直接算）
- 便于后续扩展多评委聚合

---

*文档状态：待评审*
