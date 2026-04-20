"""
Seaf API mock data and utilities.
"""

from typing import Dict, Any, List, Optional


class SeafAPIMock:
    """Mock responses for Seaf API endpoints."""
    
    @staticmethod
    def chat_agent_ask_response(
        query: str = "What is the weather?",
        messages: Optional[List[Dict[str, Any]]] = None,
        session_id: str = "",
    ) -> Dict[str, Any]:
        """Mock response for POST /api/v1/agents/chat"""
        if messages is None:
            messages = [
                {
                    "role": "assistant",
                    "content": f"Let me check the weather for you. Query: {query}",
                    "tool_calls": [
                        {
                            "id": "call_001",
                            "name": "get_weather",
                            "arguments": {"location": "Beijing"},
                        }
                    ],
                },
                {
                    "role": "tool",
                    "tool_call_id": "call_001",
                    "name": "get_weather",
                    "content": '{"temperature": 22, "condition": "Sunny", "humidity": 45}',
                },
                {
                    "role": "assistant",
                    "content": "The weather in Beijing is sunny with a temperature of 22°C.",
                },
            ]
        
        return {
            "session_id": session_id or "sess_test_001",
            "messages": messages,
        }
    
    @staticmethod
    def workflow_execute_response(
        query: str = "Process the order",
        execution_id: str = "exec_001",
    ) -> Dict[str, Any]:
        """Mock response for POST /api/v1/agents/workflow/execute"""
        return {
            "execution_id": execution_id,
            "status": "running",
            "query": query,
        }
    
    @staticmethod
    def workflow_execution_response(
        execution_id: str = "exec_001",
        status: str = "completed",
        nodes: Optional[List[Dict[str, Any]]] = None,
    ) -> Dict[str, Any]:
        """Mock response for GET /api/v1/agents/workflow/execution/{id}"""
        if nodes is None:
            nodes = [
                {
                    "id": "node_1",
                    "name": "validate_order",
                    "status": "completed",
                    "output": "Order validated successfully",
                    "latency_ms": 150,
                },
                {
                    "id": "node_2",
                    "name": "process_payment",
                    "status": "completed",
                    "output": "Payment processed: $100",
                    "latency_ms": 500,
                },
                {
                    "id": "node_3",
                    "name": "send_confirmation",
                    "status": "completed",
                    "output": "Confirmation email sent",
                    "latency_ms": 200,
                },
            ]
        
        return {
            "execution_id": execution_id,
            "status": status,
            "nodes": nodes,
            "output": "Order processed successfully. Confirmation email sent to customer.",
        }
    
    @staticmethod
    def orchestration_ask_response(
        query: str = "Analyze sales data and generate report",
        call_chain: Optional[List[Dict[str, Any]]] = None,
    ) -> Dict[str, Any]:
        """Mock response for POST /api/v1/agents/orchestration/ask"""
        if call_chain is None:
            call_chain = [
                {
                    "sub_agent_id": "agent_001",
                    "sub_agent_name": "data_collector",
                    "query": f"Collect sales data for {query}",
                    "result": "Collected 1000 sales records",
                    "calls": [
                        {
                            "sub_agent_id": "agent_003",
                            "sub_agent_name": "sql_query",
                            "query": "Execute SQL query",
                            "result": "Query executed",
                            "calls": [],
                        },
                    ],
                },
                {
                    "sub_agent_id": "agent_002",
                    "sub_agent_name": "report_generator",
                    "query": "Generate sales report",
                    "result": "Report generated: 10 pages, PDF format",
                    "calls": [],
                },
            ]
        
        return {
            "response": f"Analysis complete. I've analyzed the sales data and generated a comprehensive report. {query}",
            "call_chain": call_chain,
        }
    
    @staticmethod
    def dead_loop_response() -> Dict[str, Any]:
        """Mock response with dead loop pattern (same sub-agent called repeatedly)."""
        call_chain = [
            {
                "sub_agent_id": "agent_001",
                "sub_agent_name": "search_agent",
                "query": "Search for product A",
                "result": "Found 10 results",
                "calls": [],
            },
            {
                "sub_agent_id": "agent_001",
                "sub_agent_name": "search_agent",
                "query": "Search for product A",
                "result": "Found 10 results",
                "calls": [],
            },
            {
                "sub_agent_id": "agent_001",
                "sub_agent_name": "search_agent",
                "query": "Search for product A",
                "result": "Found 10 results",
                "calls": [],
            },
            {
                "sub_agent_id": "agent_001",
                "sub_agent_name": "search_agent",
                "query": "Search for product A",
                "result": "Found 10 results",
                "calls": [],
            },
        ]
        return SeafAPIMock.orchestration_ask_response(call_chain=call_chain)
    
    @staticmethod
    def make_chat_response(
        tools_used: Optional[List[str]] = None,
        final_response: str = "Done.",
    ) -> Dict[str, Any]:
        """Create a chat response with specific tools."""
        tools_used = tools_used or ["get_weather", "get_location"]
        tool_calls = [
            {"id": f"call_{i:03d}", "name": tool, "arguments": {}}
            for i, tool in enumerate(tools_used)
        ]
        
        return SeafAPIMock.chat_agent_ask_response(
            messages=[
                {
                    "role": "assistant",
                    "content": "Let me help with that.",
                    "tool_calls": tool_calls,
                },
                {
                    "role": "assistant",
                    "content": final_response,
                },
            ]
        )
    
    @staticmethod
    def make_workflow_response(
        nodes: Optional[List[Dict[str, Any]]] = None,
        status: str = "completed",
        output: str = "Workflow completed successfully.",
    ) -> Dict[str, Any]:
        """Create a workflow response with specific nodes."""
        return SeafAPIMock.workflow_execution_response(
            nodes=nodes,
            status=status,
        )
