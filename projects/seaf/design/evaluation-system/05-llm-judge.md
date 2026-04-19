# 智能体评测系统 - LLM 评委服务设计

> 文档版本：V1.0  
> 日期：2026-04-19  
> 状态：待评审

---

## 一、服务概述

### 1.1 定位

LLM 评委服务（LLM Judge Service）是评测系统的核心组件，负责：
1. 接收评测输入（用户问题 + Agent 响应 + 工具调用日志）
2. 调用 LLM 生成评分
3. 解析 LLM 返回的结构化评分结果
4. 处理异常和降级

### 1.2 支持的智能体类型

| 智能体类型 | 评测维度 | LLM 评分 |
|------------|----------|----------|
| 推理智能体 | 工具调用准确性、答案准确性 | 全部维度 |
| 工作流智能体 | 结果质量 | 仅结果质量维度 |
| 编排智能体 | 编排合理性、结果聚合质量、端到端效果 | 编排合理性 + 结果聚合 + 端到端效果（死循环和子Agent工具调用由系统判定） |

> ⚠️ 工作流智能体的流程完整性、节点性能、端到端耗时由系统自动判定，不需要 LLM 打分。

---

## 二、服务架构

### 2.1 整体架构

```
┌─────────────────────────────────────────────────────────────────┐
│                      LLM Judge Service                          │
│                                                                 │
│  ┌─────────────┐                                               │
│  │   Router    │ ← 接收请求，根据类型路由到不同处理逻辑          │
│  └──────┬──────┘                                               │
│         │                                                        │
│         ├──→ reasoning_judge()  → 推理智能体评判                  │
│         │                                                        │
│         └──→ workflow_judge()   → 工作流智能体评判                │
│                                                                 │
│  ┌─────────────────────────────────────────────────────────┐   │
│  │                    Prompt Manager                         │   │
│  │  - 模板加载                                              │   │
│  │  - 变量替换                                              │   │
│  │  - 格式校验                                              │   │
│  └─────────────────────────────────────────────────────────┘   │
│                                                                 │
│  ┌─────────────────────────────────────────────────────────┐   │
│  │                    LLM Client                            │   │
│  │  - API 调用                                              │   │
│  │  - 重试逻辑                                              │   │
│  │  - 响应解析                                              │   │
│  │  - 降级处理                                              │   │
│  └─────────────────────────────────────────────────────────┘   │
│                                                                 │
└─────────────────────────────────────────────────────────────────┘
```

### 2.2 类图

```python
from abc import ABC, abstractmethod
from dataclasses import dataclass
from typing import List, Dict, Any, Optional
import json


@dataclass
class JudgeRequest:
    """评委请求"""
    user_query: str
    agent_response: str
    tool_call_log: List[Dict[str, Any]] = None
    node_execution_log: List[Dict[str, Any]] = None
    expected_tools: List[str] = None
    expected_nodes: List[str] = None


@dataclass
class JudgeResponse:
    """评委响应"""
    scores: Dict[str, int]
    weighted_score: int
    confidence: str = "high"  # high / medium / low
    needs_human_review: bool = False
    key_findings: str = ""
    main_issues: List[str] = None
    suggestions: List[str] = None
    raw_response: str = ""


class BaseJudgeStrategy(ABC):
    """评判策略基类"""
    
    @abstractmethod
    def get_prompt_template(self) -> str:
        """返回 Prompt 模板"""
        pass
    
    @abstractmethod
    def parse_response(self, raw_text: str) -> JudgeResponse:
        """解析 LLM 原始响应"""
        pass
    
    def build_prompt(self, request: JudgeRequest) -> str:
        """构建 Prompt"""
        template = self.get_prompt_template()
        # 变量替换逻辑
        ...


class ReasoningJudgeStrategy(BaseJudgeStrategy):
    """推理智能体评判策略"""
    
    def get_prompt_template(self) -> str:
        return REASONING_PROMPT_TEMPLATE
    
    def parse_response(self, raw_text: str) -> JudgeResponse:
        # JSON 解析逻辑
        ...


class WorkflowJudgeStrategy(BaseJudgeStrategy):
    """工作流智能体评判策略"""
    
    def get_prompt_template(self) -> str:
        return WORKFLOW_PROMPT_TEMPLATE
    
    def parse_response(self, raw_text: str) -> JudgeResponse:
        # JSON 解析逻辑
        ...


class LLMJudgeService:
    """LLM 评委服务"""
    
    def __init__(
        self,
        api_key: str,
        base_url: str = "https://api.deepseek.com",
        model: str = "deepseek-chat",
        timeout: int = 30,
        max_retries: int = 3
    ):
        self.api_key = api_key
        self.base_url = base_url
        self.model = model
        self.timeout = timeout
        self.max_retries = max_retries
        
        # 注册评判策略
        self.strategies = {
            "reasoning": ReasoningJudgeStrategy(),
            "workflow": WorkflowJudgeStrategy()
        }
    
    async def judge_reasoning(self, request: JudgeRequest) -> JudgeResponse:
        """评判推理智能体"""
        strategy = self.strategies["reasoning"]
        return await self._do_judge(strategy, request)
    
    async def judge_workflow(self, request: JudgeRequest) -> JudgeResponse:
        """评判工作流智能体"""
        strategy = self.strategies["workflow"]
        return await self._do_judge(strategy, request)
    
    async def judge(self, agent_type: str, request: JudgeRequest) -> JudgeResponse:
        """通用评判入口"""
        strategy = self.strategies.get(agent_type)
        if not strategy:
            raise ValueError(f"不支持的智能体类型: {agent_type}")
        return await self._do_judge(strategy, request)
    
    async def _do_judge(self, strategy: BaseJudgeStrategy, request: JudgeRequest) -> JudgeResponse:
        """执行评判"""
        # 1. 构建 Prompt
        prompt = strategy.build_prompt(request)
        
        # 2. 调用 LLM
        raw_response = await self._call_llm(prompt)
        
        # 3. 解析响应
        return strategy.parse_response(raw_response)
    
    async def _call_llm(self, prompt: str) -> str:
        """调用 LLM API"""
        for attempt in range(self.max_retries):
            try:
                async with httpx.AsyncClient(timeout=self.timeout) as client:
                    response = await client.post(
                        f"{self.base_url}/chat/completions",
                        headers={
                            "Authorization": f"Bearer {self.api_key}",
                            "Content-Type": "application/json"
                        },
                        json={
                            "model": self.model,
                            "messages": [
                                {"role": "user", "content": prompt}
                            ],
                            "temperature": 0.1,  # 低温度，保证稳定性
                            "response_format": {"type": "json_object"}
                        }
                    )
                    response.raise_for_status()
                    result = response.json()
                    return result["choices"][0]["message"]["content"]
                    
            except Exception as e:
                if attempt == self.max_retries - 1:
                    raise
                await asyncio.sleep(2 ** attempt)  # 指数退避
```

---

## 三、Prompt 模板

### 3.1 推理智能体 Prompt

```python
REASONING_PROMPT_TEMPLATE = """【角色】
你是一个专业的 AI 评测专家。请对以下 Agent 的回答进行公正、严格的评分。

【输入信息】
用户问题：{user_query}
Agent 回答：{agent_response}
期望调用的工具：{expected_tools}
工具调用记录：{tool_call_log}

【评分维度】

1. 工具调用准确性（权重 60%）
   - 是否选择了正确的工具
   - 传入工具的参数是否正确完整
   - 0分：工具调用完全错误或遗漏关键工具
   - 50分：调用了部分正确工具
   - 100分：工具调用完全准确

2. 答案准确性（权重 40%）
   - 回答内容是否正确解决了用户问题
   - 0分：完全错误或误导用户
   - 50分：部分正确，有明显错误
   - 100分：完全正确

【置信度判断】
请对本次评分结果进行置信度自评：
- 高置信（>90%）：评分依据充分，无歧义
- 中置信（70-90%）：评分依据基本充分，但存在一定模糊性
- 低置信（<70%）：评分依据不足或存在较大歧义，建议人工复核

【输出格式】（严格 JSON，不包含任何额外文本）
{{
  "scores": {{
    "tool_usage": <工具调用得分(0-100)>,
    "accuracy": <答案准确性得分(0-100)>
  }},
  "weighted_score": <加权总分>,
  "confidence": "<high | medium | low>",
  "needs_human_review": <false | true>,
  "key_findings": "<核心发现说明>",
  "main_issues": ["<问题1>", "<问题2>"]
}}

【注意事项】
- 必须严格按 JSON 格式输出，不包含任何额外文本
- 分数为整数（0-100）
- weighted_score = tool_usage * 0.6 + accuracy * 0.4
- confidence 为 high/medium/low
- needs_human_review 在 confidence 为 low 时必须为 true
"""
```

### 3.2 工作流智能体 Prompt

```python
WORKFLOW_PROMPT_TEMPLATE = """【角色】
你是一个专业的 AI 评测专家。请对以下工作流智能体的输出结果进行公正、严格的评分。

【输入信息】
用户问题：{user_query}
工作流最终输出：{workflow_output}
工作流节点执行记录：{node_execution_log}

【评分维度】

结果质量（权重 100%）
   - 最终输出是否正确解决了用户问题
   - 输出内容是否完整、专业
   - 0分：完全错误或无输出
   - 50分：部分正确，有明显缺陷
   - 100分：完全正确

【置信度判断】
请对本次评分结果进行置信度自评：
- 高置信（>90%）：评分依据充分，无歧义
- 中置信（70-90%）：评分依据基本充分，但存在一定模糊性
- 低置信（<70%）：评分依据不足，建议人工复核

【输出格式】（严格 JSON，不包含任何额外文本）
{{
  "scores": {{
    "result_quality": <结果质量得分(0-100)>
  }},
  "weighted_score": <加权总分>,
  "confidence": "<high | medium | low>",
  "needs_human_review": <false | true>,
  "key_findings": "<核心发现说明>",
  "main_issues": ["<问题1>"]
}}

【注意事项】
- 必须严格按 JSON 格式输出，不包含任何额外文本
- 分数为整数（0-100）
- confidence 为 high/medium/low
- needs_human_review 在 confidence 为 low 时必须为 true
"""
```

---


### 3.3 编排智能体 Prompt

编排智能体评测调用 LLM 评委评判编排合理性、结果聚合质量和端到端效果。死循环检测和子 Agent 工具调用由系统自动判定后填入最终分数。

Prompt 模板与编排评测器设计中保持一致，核心要点：

- **编排合理性**（30%）：评判子 Agent 调用是否正确、顺序是否合理
- **结果聚合质量**（25%）：评判多 Agent 输出是否正确合并
- **端到端效果**（20%）：评判最终回答是否解决问题
- **置信度**：高/中/低三档，confidence=low 时 needs_human_review=true

详见 [编排评测器设计](./07-orchestration-evaluator.md#四编排评测器核心实现) 中的 LLM 评委调用逻辑。

## 四、响应解析

### 4.1 解析逻辑

```python
import json
import re
from typing import Dict, Any


class ResponseParser:
    """LLM 响应解析器"""
    
    @staticmethod
    def parse_reasoning(raw_text: str) -> JudgeResponse:
        """解析推理智能体评判结果"""
        try:
            # 尝试直接 JSON 解析
            data = json.loads(raw_text)
        except json.JSONDecodeError:
            # 尝试提取 JSON 部分
            data = ResponseParser._extract_json(raw_text)
        
        if not data:
            raise ValueError(f"无法解析 LLM 响应: {raw_text[:200]}")
        
        scores = data.get("scores", {})
        
        # 计算加权总分
        weighted_score = int(
            scores.get("tool_usage", 0) * 0.6 + 
            scores.get("accuracy", 0) * 0.4
        )
        
        # 解析置信度
        confidence = data.get("confidence", "high")
        needs_human_review = data.get("needs_human_review", confidence == "low")

        return JudgeResponse(
            scores={
                "tool_usage": int(scores.get("tool_usage", 0)),
                "accuracy": int(scores.get("accuracy", 0))
            },
            weighted_score=weighted_score,
            confidence=confidence,
            needs_human_review=needs_human_review,
            key_findings=data.get("key_findings", ""),
            main_issues=data.get("main_issues", []),
            raw_response=raw_text
        )
    
    @staticmethod
    def parse_workflow(raw_text: str) -> JudgeResponse:
        """解析工作流智能体评判结果"""
        try:
            data = json.loads(raw_text)
        except json.JSONDecodeError:
            data = ResponseParser._extract_json(raw_text)
        
        if not data:
            raise ValueError(f"无法解析 LLM 响应: {raw_text[:200]}")
        
        scores = data.get("scores", {})
        weighted_score = int(scores.get("result_quality", 0))
        
        # 解析置信度
        confidence = data.get("confidence", "high")
        needs_human_review = data.get("needs_human_review", confidence == "low")

        return JudgeResponse(
            scores={
                "result_quality": int(scores.get("result_quality", 0))
            },
            weighted_score=weighted_score,
            confidence=confidence,
            needs_human_review=needs_human_review,
            key_findings=data.get("key_findings", ""),
            main_issues=data.get("main_issues", []),
            raw_response=raw_text
        )
    
    @staticmethod
    def _extract_json(text: str) -> Dict[str, Any]:
        """从文本中提取 JSON"""
        # 尝试多种提取方式
        patterns = [
            r'\{[^{}]*"scores"[^{}]*\}',  # 最外层 {}
            r'\{[^{}]*\}',  # 第一个 {}
        ]
        
        for pattern in patterns:
            matches = re.findall(pattern, text, re.DOTALL)
            for match in matches:
                try:
                    return json.loads(match)
                except json.JSONDecodeError:
                    continue
        
        return None
```

### 4.2 解析失败降级处理

```python
async def _call_llm_with_fallback(self, prompt: str) -> str:
    """带降级处理的 LLM 调用"""
    try:
        return await self._call_llm(prompt)
    except Exception as e:
        # 降级：使用简化 Prompt
        simplified_prompt = self._simplify_prompt(prompt)
        try:
            return await self._call_llm(simplified_prompt)
        except Exception:
            # 最终降级：返回默认评分
            raise LLMJudgeError(f"LLM 调用失败: {e}")


def _simplify_prompt(self, prompt: str) -> str:
    """简化 Prompt，减少 Token 消耗"""
    # 移除示例、详细说明，只保留核心要求
    simplified = prompt
    # ... 简化逻辑
    return simplified
```

---

## 五、变量替换规则

### 5.1 推理智能体变量

```python
def build_reasoning_prompt(request: JudgeRequest) -> str:
    """构建推理智能体 Prompt"""
    
    # 期望工具
    expected_tools = ", ".join(request.expected_tools) if request.expected_tools else "无"
    
    # 工具调用日志格式化
    tool_call_log = self._format_tool_call_log(request.tool_call_log)
    
    # Agent 响应（截断过长内容）
    agent_response = self._truncate(request.agent_response, max_length=2000)
    
    # 替换变量
    prompt = REASONING_PROMPT_TEMPLATE.format(
        user_query=request.user_query,
        agent_response=agent_response,
        expected_tools=expected_tools,
        tool_call_log=tool_call_log
    )
    
    return prompt


def _format_tool_call_log(self, tool_call_log: List[Dict]) -> str:
    """格式化工具调用日志"""
    if not tool_call_log:
        return "无工具调用"
    
    lines = []
    for i, log in enumerate(tool_call_log, 1):
        tool_name = log.get("tool_name", "unknown")
        arguments = log.get("arguments", {})
        status = log.get("status", "unknown")
        latency = log.get("latency_ms", 0)
        
        lines.append(
            f"[{i}] 工具: {tool_name}, "
            f"参数: {json.dumps(arguments, ensure_ascii=False)}, "
            f"状态: {status}, "
            f"耗时: {latency}ms"
        )
    
    return "\n".join(lines)


def _truncate(self, text: str, max_length: int = 2000) -> str:
    """截断过长文本"""
    if len(text) <= max_length:
        return text
    return text[:max_length] + f"\n... (已截断，共 {len(text)} 字符)"
```

### 5.2 工作流智能体变量

```python
def build_workflow_prompt(request: JudgeRequest) -> str:
    """构建工作流智能体 Prompt"""
    
    # 节点执行日志格式化
    node_execution_log = self._format_node_execution_log(request.node_execution_log)
    
    # 工作流输出（截断过长内容）
    workflow_output = self._truncate(request.agent_response, max_length=2000)
    
    prompt = WORKFLOW_PROMPT_TEMPLATE.format(
        user_query=request.user_query,
        workflow_output=workflow_output,
        node_execution_log=node_execution_log
    )
    
    return prompt


def _format_node_execution_log(self, node_log: List[Dict]) -> str:
    """格式化节点执行日志"""
    if not node_log:
        return "无节点执行记录"
    
    lines = []
    for i, node in enumerate(node_log, 1):
        node_name = node.get("node", "unknown")
        latency = node.get("latency_ms", 0)
        status = node.get("status", "unknown")
        error = node.get("error", "")
        
        line = f"[{i}] 节点: {node_name}, 耗时: {latency}ms, 状态: {status}"
        if error:
            line += f", 错误: {error}"
        lines.append(line)
    
    return "\n".join(lines)
```

---

## 六、异常处理

### 6.1 异常类型

```python
class LLMJudgeError(Exception):
    """LLM 评委服务异常"""
    pass


class LLMParsingError(LLMJudgeError):
    """响应解析异常"""
    pass


class LLMAPIError(LLMJudgeError):
    """API 调用异常"""
    pass


class LLMTimeoutError(LLMJudgeError):
    """API 超时异常"""
    pass
```

### 6.2 降级策略

```python
async def _do_judge_with_fallback(self, strategy, request: JudgeRequest) -> JudgeResponse:
    """带降级的评判执行"""
    
    # 1. 正常调用
    try:
        return await self._do_judge(strategy, request)
    except LLMJudgeError as e:
        logger.warning(f"LLM 评委调用失败: {e}，尝试降级")
    
    # 2. 简化 Prompt 降级
    try:
        simplified_request = self._simplify_request(request)
        return await self._do_judge(strategy, simplified_request)
    except Exception as e:
        logger.warning(f"简化 Prompt 降级失败: {e}，返回默认评分")
    
    # 3. 返回默认评分（兜底）
    return JudgeResponse(
        scores={"error": 0},
        weighted_score=0,
        confidence="low",
        needs_human_review=True,
        key_findings="LLM 评委调用失败",
        main_issues=["LLM API 调用异常"],
        suggestions=["请人工复核此评测结果"]
    )


def _simplify_request(self, request: JudgeRequest) -> JudgeRequest:
    """简化请求，减少 Token"""
    return JudgeRequest(
        user_query=self._truncate(request.user_query, 500),
        agent_response=self._truncate(request.agent_response, 1000),
        tool_call_log=request.tool_call_log[:5] if request.tool_call_log else [],  # 只保留前5条
        node_execution_log=request.node_execution_log[:5] if request.node_execution_log else [],
        expected_tools=request.expected_tools,
        expected_nodes=request.expected_nodes
    )
```

---

## 七、配置管理

### 7.1 配置文件

```yaml
# llm_judge.yaml
llm:
  provider: "deepseek"  # deepseek / openai / anthropic
  model: "deepseek-chat"
  api_key: "${LLM_API_KEY}"
  base_url: "https://api.deepseek.com"
  timeout: 30
  max_retries: 3
  temperature: 0.1  # 低温度保证稳定性

prompt:
  reasoning_template: "prompts/reasoning_judge.md"
  workflow_template: "prompts/workflow_judge.md"

fallback:
  enabled: true
  max_tokens: 4000  # 降级时限制 Token 数
```

### 7.2 多模型支持

```python
class LLMJudgeService:
    """支持多模型切换"""
    
    MODELS = {
        "deepseek-chat": {
            "provider": "deepseek",
            "base_url": "https://api.deepseek.com"
        },
        "gpt-4o": {
            "provider": "openai",
            "base_url": "https://api.openai.com/v1"
        },
        "claude-3-5-sonnet": {
            "provider": "anthropic",
            "base_url": "https://api.anthropic.com"
        }
    }
    
    def switch_model(self, model_name: str):
        """切换模型"""
        if model_name not in self.MODELS:
            raise ValueError(f"不支持的模型: {model_name}")
        
        config = self.MODELS[model_name]
        self.model = model_name
        self.base_url = config["base_url"]
        self.provider = config["provider"]
```

---

## 八、监控指标

### 8.1 关键指标

| 指标 | 说明 | 告警阈值 |
|------|------|----------|
| `llm_judge_calls_total` | LLM 调用总次数 | - |
| `llm_judge_calls_success` | 成功次数 | - |
| `llm_judge_calls_failed` | 失败次数 | - |
| `llm_judge_latency_seconds` | 调用延迟 | > 30s |
| `llm_judge_parsing_errors` | 解析错误次数 | > 5% |
| `llm_judge_fallback_used` | 降级调用次数 | > 10% |

### 8.2 日志规范

```python
import structlog
logger = structlog.get_logger()

async def _call_llm(self, prompt: str) -> str:
    """带监控的 LLM 调用"""
    start_time = time.time()
    
    logger.info(
        "llm_judge_call_start",
        model=self.model,
        prompt_length=len(prompt)
    )
    
    try:
        response = await self._do_api_call(prompt)
        
        logger.info(
            "llm_judge_call_success",
            model=self.model,
            latency=time.time() - start_time,
            response_length=len(response)
        )
        
        return response
        
    except Exception as e:
        logger.error(
            "llm_judge_call_failed",
            model=self.model,
            latency=time.time() - start_time,
            error=str(e)
        )
        raise
```

---

## 九、单元测试示例

```python
import pytest
from unittest.mock import AsyncMock, patch


class TestReasoningJudge:
    """推理智能体评判测试"""
    
    @pytest.fixture
    def service(self):
        return LLMJudgeService(
            api_key="test_key",
            model="deepseek-chat"
        )
    
    @pytest.fixture
    def sample_request(self):
        return JudgeRequest(
            user_query="请问你们的退换货政策是什么？",
            agent_response="我们的退换货政策是支持7天无理由退货...",
            expected_tools=["knowledge_retrieval"],
            tool_call_log=[
                {
                    "tool_name": "knowledge_retrieval",
                    "arguments": {"query": "退换货政策"},
                    "status": "success",
                    "latency_ms": 150
                }
            ]
        )
    
    @pytest.mark.asyncio
    async def test_judge_success(self, service, sample_request):
        """正常评判"""
        mock_response = json.dumps({
            "scores": {
                "tool_usage": 85,
                "accuracy": 90
            },
            "weighted_score": 87,
            "key_findings": "工具调用正确",
            "main_issues": []
        })
        
        with patch.object(service, '_call_llm', new_callable=AsyncMock, return_value=mock_response):
            result = await service.judge_reasoning(sample_request)
            
            assert result.scores["tool_usage"] == 85
            assert result.scores["accuracy"] == 90
            assert result.weighted_score == 87
    
    @pytest.mark.asyncio
    async def test_judge_parsing_error(self, service, sample_request):
        """解析失败降级"""
        with patch.object(service, '_call_llm', side_effect=Exception("API Error")):
            with patch.object(service, '_call_llm', new_callable=AsyncMock, side_effect=Exception("Again")):
                result = await service._do_judge_with_fallback(
                    service.strategies["reasoning"],
                    sample_request
                )
                
                # 应该返回默认评分
                assert result.weighted_score == 0
                assert result.needs_human_review is True


class TestResponseParser:
    """响应解析测试"""
    
    def test_parse_valid_json(self):
        """解析有效 JSON"""
        raw = '{"scores": {"tool_usage": 85}, "weighted_score": 85}'
        result = ResponseParser.parse_reasoning(raw)
        assert result.scores["tool_usage"] == 85
    
    def test_parse_with_extra_text(self):
        """解析带额外文本的响应"""
        raw = '以下是评分结果：\n{"scores": {"tool_usage": 85}, "weighted_score": 85}\n请确认。'
        result = ResponseParser.parse_reasoning(raw)
        assert result.scores["tool_usage"] == 85
    
    def test_parse_invalid_json(self):
        """解析无效 JSON"""
        raw = '这是一段无法解析的文本'
        with pytest.raises(ValueError):
            ResponseParser.parse_reasoning(raw)
```

---

*文档状态：待评审*
