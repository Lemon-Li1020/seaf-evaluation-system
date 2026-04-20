"""
LLM Judge prompts for evaluation.
"""

# Dimension weights for each agent type
DIMENSION_WEIGHTS = {
    "reasoning": {
        "correctness": 0.35,
        "tool_usage": 0.25,
        "efficiency": 0.20,
        "relevance": 0.20,
    },
    "workflow": {
        "flow_completeness": 0.30,
        "node_performance": 0.25,
        "end_to_end_correctness": 0.25,
        "latency": 0.20,
    },
    "orchestration": {
        "orchestration_reasonableness": 0.25,
        "sub_agent_effectiveness": 0.25,
        "result_aggregation": 0.25,
        "end_to_end_effectiveness": 0.25,
    },
}

REASONING_JUDGE_PROMPT = """You are an expert judge evaluating an AI agent's reasoning capabilities.

## User Query
{user_query}

## Agent Response
{agent_response}

## Tool Call Log
{tool_call_log}

## Expected Tools
{expected_tools}

## Your Task
Evaluate the agent's performance on the following dimensions:

1. **Correctness** (0-100): Did the agent correctly understand and address the user's query?
2. **Tool Usage** (0-100): Did the agent use the appropriate tools effectively?
3. **Efficiency** (0-100): Was the agent's approach efficient without unnecessary steps?
4. **Relevance** (0-100): Was the response relevant and helpful to the user's needs?

## Evaluation Criteria
- Check if the agent used the expected tools
- Evaluate the logical flow of the reasoning
- Consider the completeness and accuracy of the response
- Assess whether the tool calls were necessary and appropriate

## Output Format
Please respond with a JSON object containing:
{{
  "scores": {{
    "correctness": <0-100>,
    "tool_usage": <0-100>,
    "efficiency": <0-100>,
    "relevance": <0-100>
  }},
  "weighted_score": <0-100>,
  "confidence": "high|medium|low",
  "needs_human_review": <true|false>,
  "key_findings": ["<finding1>", "<finding2>", ...],
  "main_issues": ["<issue1>", "<issue2>", ...]
}}

## Confidence Level Guidelines
- **high**: Clear pass/fail, all expected tools used correctly, no ambiguity
- **medium**: Some ambiguity, minor issues, most criteria met
- **low**: Significant ambiguity, conflicting signals, needs human judgment

If confidence is "low", set needs_human_review to true.
"""

WORKFLOW_JUDGE_PROMPT = """You are an expert judge evaluating an AI agent's workflow execution.

## User Query
{user_query}

## Agent Response
{agent_response}

## Node Execution Log
{node_execution_log}

## Expected Nodes
{expected_nodes}

## Expected Order
{expected_order}

## Your Task
Evaluate the agent's workflow execution on the following dimensions:

1. **Flow Completeness** (0-100): Did the workflow execute all expected nodes/steps?
2. **Node Performance** (0-100): Did each node perform correctly and produce expected outputs?
3. **End-to-End Correctness** (0-100): Did the overall workflow achieve the intended goal?
4. **Latency** (0-100): Did the workflow complete within acceptable time limits?

## Evaluation Criteria
- Check if all expected nodes were executed
- Verify the correct order of node execution
- Evaluate the output quality at each node
- Assess total workflow latency against expectations

## Output Format
Please respond with a JSON object containing:
{{
  "scores": {{
    "flow_completeness": <0-100>,
    "node_performance": <0-100>,
    "end_to_end_correctness": <0-100>,
    "latency": <0-100>
  }},
  "weighted_score": <0-100>,
  "confidence": "high|medium|low",
  "needs_human_review": <true|false>,
  "key_findings": ["<finding1>", "<finding2>", ...],
  "main_issues": ["<issue1>", "<issue2>", ...]
}}

## Confidence Level Guidelines
- **high**: All nodes executed in correct order with good performance
- **medium**: Minor issues with node execution or ordering
- **low**: Significant workflow issues or execution failures

If confidence is "low", set needs_human_review to true.
"""

ORCHESTRATION_JUDGE_PROMPT = """You are an expert judge evaluating an AI agent's orchestration capabilities.

## User Query
{user_query}

## Agent Response
{agent_response}

## Sub-Agent Call Chain
{sub_agent_call_log}

## Expected Sub-Agents
{expected_sub_agents}

## Expected Order
{expected_order}

## Your Task
Evaluate the agent's orchestration capabilities on the following dimensions:

1. **Orchestration Reasonableness** (0-100): Did the agent appropriately decompose the task and delegate to sub-agents?
2. **Sub-Agent Effectiveness** (0-100): Did the sub-agents perform their assigned tasks effectively?
3. **Result Aggregation** (0-100): Did the agent properly combine sub-agent results into a coherent response?
4. **End-to-End Effectiveness** (0-100): Did the overall orchestration achieve the user's goal?

## Evaluation Criteria
- Check if appropriate sub-agents were invoked
- Verify sub-agents executed in a logical order
- Evaluate the quality of result aggregation
- Look for signs of dead loops or redundant calls
- Assess whether max_sub_agent_calls was respected

## Dead Loop Detection
If you detect the same sub-agent being called in a repeating pattern without progress, this is a critical issue.

## Output Format
Please respond with a JSON object containing:
{{
  "scores": {{
    "orchestration_reasonableness": <0-100>,
    "sub_agent_effectiveness": <0-100>,
    "result_aggregation": <0-100>,
    "end_to_end_effectiveness": <0-100>
  }},
  "weighted_score": <0-100>,
  "confidence": "high|medium|low",
  "needs_human_review": <true|false>,
  "key_findings": ["<finding1>", "<finding2>", ...],
  "main_issues": ["<issue1>", "<issue2>", ...]
}}

## Confidence Level Guidelines
- **high**: Clean orchestration with appropriate sub-agent delegation
- **medium**: Some issues with delegation or aggregation
- **low**: Significant orchestration problems including potential dead loops

If confidence is "low", set needs_human_review to true.
"""

# Simplified prompts for fallback
SIMPLIFIED_REASONING_PROMPT = """Evaluate the following agent response:

Query: {user_query}
Response: {agent_response}
Tools Used: {tool_call_log}

Score correctness, tool_usage, efficiency, relevance (0-100 each).
Return JSON: {{"scores": {{"correctness":X,"tool_usage":Y,"efficiency":Z,"relevance":W}}, "weighted_score": <avg>, "confidence": "medium", "needs_human_review": false, "key_findings": [], "main_issues": []}}
"""

SIMPLIFIED_WORKFLOW_PROMPT = """Evaluate workflow execution:

Query: {user_query}
Nodes: {node_execution_log}

Score flow_completeness, node_performance, end_to_end_correctness, latency (0-100 each).
Return JSON: {{"scores": {{"flow_completeness":X,"node_performance":Y,"end_to_end_correctness":Z,"latency":W}}, "weighted_score": <avg>, "confidence": "medium", "needs_human_review": false, "key_findings": [], "main_issues": []}}
"""

SIMPLIFIED_ORCHESTRATION_PROMPT = """Evaluate orchestration:

Query: {user_query}
Sub-agents: {sub_agent_call_log}

Score orchestration_reasonableness, sub_agent_effectiveness, result_aggregation, end_to_end_effectiveness (0-100 each).
Return JSON: {{"scores": {{"orchestration_reasonableness":X,"sub_agent_effectiveness":Y,"result_aggregation":Z,"end_to_end_effectiveness":W}}, "weighted_score": <avg>, "confidence": "medium", "needs_human_review": false, "key_findings": [], "main_issues": []}}
"""
