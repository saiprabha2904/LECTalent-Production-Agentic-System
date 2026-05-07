"""Web search tool using DuckDuckGo."""
import asyncio
from typing import Dict, List
from .base import BaseTool, ToolSchema, ToolResult, ToolCategory


class WebSearch(BaseTool):
    """Search the web using DuckDuckGo."""
    
    def __init__(self):
        super().__init__()
        self._ddg = None
    
    def _create_schema(self) -> ToolSchema:
        return ToolSchema(
            name="web_search",
            description="Search the web for current information, news, facts, or any topic not in the knowledge base. Returns relevant search results with titles, snippets, and URLs. Use when you need up-to-date information or facts you don't know.",
            category=ToolCategory.SEARCH,
            parameters={
                "type": "object",
                "properties": {
                    "query": {
                        "type": "string",
                        "description": "Search query to find information on the web"
                    },
                    "max_results": {
                        "type": "integer",
                        "description": "Maximum number of results to return (default: 5)",
                        "default": 5
                    }
                },
                "required": ["query"]
            },
            examples=[
                "What is the current weather in Tokyo?",
                "Latest news about artificial intelligence",
                "Who won the 2024 Nobel Prize in Physics?",
                "Python 3.12 new features",
            ]
        )
    
    async def execute(self, **kwargs) -> ToolResult:
        """Execute web search."""
        query = kwargs.get("query", "")
        max_results = kwargs.get("max_results", 5)
        
        if not query:
            return ToolResult(
                success=False,
                error="Missing required parameter: query"
            )
        
        try:
            # Import here to avoid issues if not installed
            from duckduckgo_search import DDGS
            
            # Run search in executor to avoid blocking
            loop = asyncio.get_event_loop()
            results = await loop.run_in_executor(
                None,
                lambda: self._search_sync(query, max_results)
            )
            
            if not results:
                return ToolResult(
                    success=True,
                    data=[],
                    metadata={
                        "query": query,
                        "message": "No results found"
                    }
                )
            
            return ToolResult(
                success=True,
                data=results,
                metadata={
                    "query": query,
                    "result_count": len(results)
                }
            )
            
        except ImportError:
            return ToolResult(
                success=False,
                error="duckduckgo-search package not installed. Install with: pip install duckduckgo-search",
                metadata={"query": query}
            )
        except Exception as e:
            return ToolResult(
                success=False,
                error=f"Search failed: {str(e)}",
                metadata={"query": query}
            )
    
    def _search_sync(self, query: str, max_results: int) -> List[Dict]:
        """Synchronous search helper."""
        from duckduckgo_search import DDGS
        
        results = []
        with DDGS() as ddgs:
            for i, result in enumerate(ddgs.text(query, max_results=max_results)):
                if i >= max_results:
                    break
                results.append({
                    "title": result.get("title", ""),
                    "snippet": result.get("body", ""),
                    "url": result.get("href", "")
                })
        return results


