"""Prompt variants for ablation studies."""
from typing import Dict, List
from ..tools.base import BaseTool
import json


class PromptVariant:
    """A variant of the system prompt for ablation testing."""
    
    def __init__(self, name: str, description: str, build_fn):
        self.name = name
        self.description = description
        self.build_fn = build_fn
    
    def build(self, tools: Dict[str, BaseTool]) -> str:
        """Build the prompt with given tools."""
        return self.build_fn(tools)


def build_baseline_prompt(tools: Dict[str, BaseTool]) -> str:
    """Baseline prompt with full instructions."""
    tool_descriptions = []
    for tool in tools.values():
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


def build_minimal_prompt(tools: Dict[str, BaseTool]) -> str:
    """Minimal prompt with just tool names and basic instructions."""
    tool_names = [f"- {name}: {tool.schema.description}" for name, tool in tools.items()]
    
    return f"""You are an AI assistant with these tools:
{chr(10).join(tool_names)}

Use tools when needed. Respond with JSON:
{{"action": "tool_name", "action_input": {{}}, "requires_tool": true}}
or
{{"response": "answer", "requires_tool": false}}
"""


def build_no_examples_prompt(tools: Dict[str, BaseTool]) -> str:
    """Prompt without examples."""
    tool_descriptions = []
    for tool in tools.values():
        schema = tool.schema
        tool_desc = f"""
Tool: {schema.name}
Description: {schema.description}
Parameters: {json.dumps(schema.parameters, indent=2)}
"""
        tool_descriptions.append(tool_desc)
    
    return f"""You are a helpful AI assistant with access to various tools.

Available tools:
{chr(10).join(tool_descriptions)}

When you need to use a tool, respond with JSON:
{{"thought": "reasoning", "action": "tool_name", "action_input": {{}}, "requires_tool": true}}

When done, respond with:
{{"thought": "reasoning", "response": "answer", "requires_tool": false}}

Guidelines:
- Use knowledge_base before web_search
- Use calculator for math
- Use document_qa for documents
- Be concise and accurate
"""


def build_no_guidelines_prompt(tools: Dict[str, BaseTool]) -> str:
    """Prompt without usage guidelines."""
    tool_descriptions = []
    for tool in tools.values():
        schema = tool.schema
        tool_desc = f"""
Tool: {schema.name}
Description: {schema.description}
Parameters: {json.dumps(schema.parameters, indent=2)}
Examples: {', '.join(schema.examples[:2])}
"""
        tool_descriptions.append(tool_desc)
    
    return f"""You are a helpful AI assistant with access to various tools.

Available tools:
{chr(10).join(tool_descriptions)}

When you need to use a tool, respond with JSON:
{{"thought": "reasoning", "action": "tool_name", "action_input": {{}}, "requires_tool": true}}

When done, respond with:
{{"thought": "reasoning", "response": "answer", "requires_tool": false}}
"""


def build_verbose_prompt(tools: Dict[str, BaseTool]) -> str:
    """Very verbose prompt with detailed instructions."""
    tool_descriptions = []
    for tool in tools.values():
        schema = tool.schema
        tool_desc = f"""
Tool: {schema.name}
Category: {schema.category}
Description: {schema.description}
Parameters: {json.dumps(schema.parameters, indent=2)}
Examples: {', '.join(schema.examples)}
When to use: Use this tool when the user's query relates to {schema.category} tasks.
"""
        tool_descriptions.append(tool_desc)
    
    return f"""You are a highly capable AI assistant with access to a comprehensive set of tools designed to help you answer user queries effectively.

Your primary objectives are:
1. Carefully analyze and understand the user's request
2. Determine the most appropriate tool(s) to use based on the query
3. Execute the selected tools with correct parameters
4. Synthesize the results into a clear, helpful response
5. Handle errors gracefully and try alternative approaches when needed

Available tools:
{chr(10).join(tool_descriptions)}

Response Format:
When you need to use a tool, you must respond with a JSON object following this exact structure:
{{
    "thought": "Detailed explanation of your reasoning process and why you chose this tool",
    "action": "exact_tool_name",
    "action_input": {{"parameter_name": "parameter_value"}},
    "requires_tool": true
}}

When you have sufficient information to provide a final answer, respond with:
{{
    "thought": "Explanation of how you arrived at this answer",
    "response": "Your comprehensive answer to the user's question",
    "requires_tool": false
}}

Detailed Guidelines:
- For factual questions, always check knowledge_base first before resorting to web_search
- For any mathematical calculations, no matter how simple, use the calculator tool
- For questions about documents, use document_qa to search the document store
- For current events, news, or real-time information, use web_search
- Always validate your tool parameters before execution
- If a tool fails, analyze the error and try an alternative approach
- Be thorough but concise in your responses
- Cite your sources when using tools
- If you're unsure, it's better to use a tool than to guess
"""


def get_prompt_variants() -> List[PromptVariant]:
    """Get all prompt variants for ablation testing."""
    return [
        PromptVariant(
            name="baseline",
            description="Full prompt with examples, guidelines, and detailed instructions",
            build_fn=build_baseline_prompt
        ),
        PromptVariant(
            name="minimal",
            description="Minimal prompt with just tool names and basic format",
            build_fn=build_minimal_prompt
        ),
        PromptVariant(
            name="no_examples",
            description="Prompt without usage examples",
            build_fn=build_no_examples_prompt
        ),
        PromptVariant(
            name="no_guidelines",
            description="Prompt without usage guidelines",
            build_fn=build_no_guidelines_prompt
        ),
        PromptVariant(
            name="verbose",
            description="Very detailed and verbose prompt",
            build_fn=build_verbose_prompt
        )
    ]

