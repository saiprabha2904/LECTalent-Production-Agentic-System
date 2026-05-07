"""Core agent loop with LLM-driven tool selection."""
import json
import os
from typing import Dict, List, Any, Optional
from openai import AsyncOpenAI
from .state import AgentState, AgentStatus, ToolCall
from .observability import MetricsCollector, LatencyTracker
from ..tools.base import BaseTool, ToolResult


class Agent:
    """Main agent with LLM-driven tool selection and execution."""
    
    def __init__(
        self,
        tools: List[BaseTool],
        model: str = "gpt-4o-mini",
        api_key: Optional[str] = None,
        max_iterations: int = 5,
        enable_fallback: bool = True
    ):
        self.tools = {tool.schema.name: tool for tool in tools}
        self.model = model
        self.client = AsyncOpenAI(api_key=api_key or os.getenv("OPENAI_API_KEY"))
        self.max_iterations = max_iterations
        self.enable_fallback = enable_fallback
        
        self.state = AgentState()
        self.metrics = MetricsCollector()
        
        # System prompt for tool selection
        self.system_prompt = self._build_system_prompt()
    
    def _build_system_prompt(self) -> str:
        """Build the system prompt with tool descriptions."""
        tool_descriptions = []
        for tool in self.tools.values():
            schema = tool.schema
            tool_desc = f"""
Tool: {schema.name}
Category: {schema.category}
Description: {schema.description}
Parameters: {json.dumps(schema.parameters, indent=2)}
Examples: {', '.join(schema.examples[:2])}
"""
            tool_descriptions.append(tool_desc)
        
        return f"""You are a helpful AI assistant with access to various tools. Your job is to:
1. Understand the user's request
2. Determine which tool(s) to use (if any)
3. Execute tools with appropriate parameters
4. Synthesize results into a helpful response

Available tools:
{chr(10).join(tool_descriptions)}

When you need to use a tool, respond with a JSON object in this format:
{{
    "thought": "Your reasoning about what to do",
    "action": "tool_name",
    "action_input": {{"param1": "value1", "param2": "value2"}},
    "requires_tool": true
}}

When you have enough information to answer without tools, or after using tools, respond with:
{{
    "thought": "Your reasoning",
    "response": "Your final answer to the user",
    "requires_tool": false
}}

Guidelines:
- Use knowledge_base first for factual information before web_search
- Use calculator for any mathematical computations
- Use document_qa for questions about stored documents
- Use web_search for current events or information not in knowledge base
- Be concise and accurate
- If a tool fails, try an alternative approach or explain the limitation
"""
    
    async def run(self, user_message: str) -> str:
        """Run the agent loop for a user message."""
        self.state.start_turn(user_message)
        
        conversation = [
            {"role": "system", "content": self.system_prompt},
            {"role": "user", "content": user_message}
        ]
        
        iteration = 0
        final_response = ""
        
        try:
            while iteration < self.max_iterations:
                iteration += 1
                self.state.status = AgentStatus.THINKING
                
                # Get LLM response
                with LatencyTracker() as tracker:
                    llm_response = await self._call_llm(conversation)
                
                # Track LLM call
                cost = self.metrics.track_llm_call(
                    model=self.model,
                    input_tokens=llm_response.get("input_tokens", 0),
                    output_tokens=llm_response.get("output_tokens", 0),
                    latency_ms=tracker.latency_ms,
                    success=True
                )
                
                response_text = llm_response.get("content", "")
                
                # Parse response
                try:
                    parsed = self._parse_llm_response(response_text)
                except json.JSONDecodeError:
                    # Fallback: treat as final response
                    final_response = response_text
                    break
                
                # Add to conversation
                conversation.append({"role": "assistant", "content": response_text})
                
                # Check if tool is required
                if not parsed.get("requires_tool", False):
                    final_response = parsed.get("response", response_text)
                    break
                
                # Execute tool
                tool_name = parsed.get("action")
                tool_input = parsed.get("action_input", {})
                
                if tool_name not in self.tools:
                    error_msg = f"Unknown tool: {tool_name}"
                    conversation.append({"role": "user", "content": f"Error: {error_msg}. Please try a different approach."})
                    if not self.enable_fallback:
                        final_response = f"Error: {error_msg}"
                        break
                    continue
                
                # Execute tool with error handling
                self.state.status = AgentStatus.EXECUTING_TOOL
                tool_result = await self._execute_tool_with_retry(tool_name, tool_input)
                
                # Add tool result to conversation
                result_message = self._format_tool_result(tool_name, tool_result)
                conversation.append({"role": "user", "content": result_message})
                
                # If tool failed and no fallback, break
                if not tool_result.success and not self.enable_fallback:
                    final_response = f"Tool execution failed: {tool_result.error}"
                    break
            
            # If we hit max iterations without a final response
            if not final_response:
                final_response = "I apologize, but I've reached the maximum number of steps. Please try rephrasing your question."
            
            self.state.complete_turn(final_response)
            
            # Track agent turn
            self.metrics.track_agent_turn(
                turn_number=len(self.state.conversation_history),
                total_latency_ms=sum(tc.latency_ms for tc in self.state.current_turn.tool_calls) if self.state.current_turn else 0,
                total_cost=self.state.current_turn.total_cost if self.state.current_turn else 0,
                tool_calls=len(self.state.current_turn.tool_calls) if self.state.current_turn else 0,
                success=True
            )
            
            return final_response
            
        except Exception as e:
            error_msg = f"Agent error: {str(e)}"
            self.state.set_error(error_msg)
            self.metrics.track_agent_turn(
                turn_number=len(self.state.conversation_history),
                total_latency_ms=0,
                total_cost=0,
                tool_calls=0,
                success=False
            )
            return error_msg
    
    async def _call_llm(self, messages: List[Dict[str, str]]) -> Dict[str, Any]:
        """Call the LLM API."""
        response = await self.client.chat.completions.create(
            model=self.model,
            messages=messages,  # type: ignore
            temperature=0.7,
            max_tokens=1000
        )
        
        return {
            "content": response.choices[0].message.content,
            "input_tokens": response.usage.prompt_tokens if response.usage else 0,
            "output_tokens": response.usage.completion_tokens if response.usage else 0
        }
    
    def _parse_llm_response(self, response: str) -> Dict[str, Any]:
        """Parse LLM response as JSON."""
        # Try to extract JSON from markdown code blocks
        if "```json" in response:
            start = response.find("```json") + 7
            end = response.find("```", start)
            response = response[start:end].strip()
        elif "```" in response:
            start = response.find("```") + 3
            end = response.find("```", start)
            response = response[start:end].strip()
        
        return json.loads(response)
    
    async def _execute_tool_with_retry(
        self,
        tool_name: str,
        parameters: Dict[str, Any],
        max_retries: int = 2
    ) -> ToolResult:
        """Execute a tool with retry logic."""
        tool = self.tools[tool_name]
        last_error = None
        
        for attempt in range(max_retries):
            try:
                with LatencyTracker() as tracker:
                    result = await tool.execute(**parameters)
                
                # Track tool call
                tool_call = ToolCall(
                    tool_name=tool_name,
                    parameters=parameters,
                    result=result.data,
                    success=result.success,
                    error=result.error,
                    latency_ms=tracker.latency_ms,
                    cost=0.0  # Tools don't have direct cost
                )
                self.state.add_tool_call(tool_call)
                
                self.metrics.track_tool_call(
                    tool_name=tool_name,
                    latency_ms=tracker.latency_ms,
                    success=result.success,
                    error=result.error
                )
                
                if result.success or attempt == max_retries - 1:
                    return result
                
                last_error = result.error
                
            except Exception as e:
                last_error = str(e)
                if attempt == max_retries - 1:
                    return ToolResult(
                        success=False,
                        error=f"Tool execution failed after {max_retries} attempts: {last_error}"
                    )
        
        return ToolResult(
            success=False,
            error=f"Tool execution failed: {last_error}"
        )
    
    def _format_tool_result(self, tool_name: str, result: ToolResult) -> str:
        """Format tool result for LLM consumption."""
        if result.success:
            return f"Tool '{tool_name}' executed successfully. Result: {json.dumps(result.data, indent=2)}"
        else:
            return f"Tool '{tool_name}' failed with error: {result.error}"
    
    def get_metrics_summary(self) -> Dict[str, Any]:
        """Get metrics summary."""
        return self.metrics.get_summary()
    
    def get_state_statistics(self) -> Dict[str, Any]:
        """Get state statistics."""
        return self.state.get_statistics()
    
    def save_metrics(self):
        """Save metrics to file."""
        self.metrics.save_to_file()
    
    def reset(self):
        """Reset agent state and metrics."""
        self.state.reset()
        self.metrics.reset()