"""Knowledge base tool for structured information retrieval."""
import json
from typing import Dict, List, Any, Optional
from pathlib import Path
from .base import BaseTool, ToolSchema, ToolResult, ToolCategory


class KnowledgeBase(BaseTool):
    """Query a structured knowledge base."""
    
    def __init__(self, kb_path: Optional[str] = None):
        self.kb_path = kb_path or "agent_system/data/knowledge_base.json"
        self._kb_data: Dict[str, Any] = {}
        self._load_knowledge_base()
        super().__init__()
    
    def _create_schema(self) -> ToolSchema:
        return ToolSchema(
            name="knowledge_base",
            description="Query the internal knowledge base for structured information about topics, entities, or concepts. The knowledge base contains curated, verified information organized by categories. Use this for factual lookups about known topics before searching the web.",
            category=ToolCategory.KNOWLEDGE,
            parameters={
                "type": "object",
                "properties": {
                    "query": {
                        "type": "string",
                        "description": "Query to search in the knowledge base"
                    },
                    "category": {
                        "type": "string",
                        "description": "Optional category to narrow search (e.g., 'science', 'history', 'technology')",
                        "default": None
                    }
                },
                "required": ["query"]
            },
            examples=[
                "What is machine learning?",
                "Tell me about Python programming language",
                "Information about quantum computing",
                "History of the internet",
            ]
        )
    
    def _load_knowledge_base(self):
        """Load knowledge base from file."""
        kb_file = Path(self.kb_path)
        if kb_file.exists():
            try:
                with open(kb_file, 'r', encoding='utf-8') as f:
                    self._kb_data = json.load(f)
            except Exception as e:
                print(f"Warning: Failed to load knowledge base: {e}")
                self._kb_data = self._get_default_kb()
        else:
            # Create default knowledge base
            self._kb_data = self._get_default_kb()
            self._save_knowledge_base()
    
    def _get_default_kb(self) -> Dict[str, Any]:
        """Get default knowledge base content."""
        return {
            "technology": {
                "python": {
                    "name": "Python",
                    "description": "Python is a high-level, interpreted programming language known for its simplicity and readability. Created by Guido van Rossum in 1991.",
                    "key_features": ["Dynamic typing", "Extensive standard library", "Multiple paradigms", "Large ecosystem"],
                    "use_cases": ["Web development", "Data science", "Machine learning", "Automation"]
                },
                "machine_learning": {
                    "name": "Machine Learning",
                    "description": "Machine learning is a subset of artificial intelligence that enables systems to learn and improve from experience without being explicitly programmed.",
                    "types": ["Supervised learning", "Unsupervised learning", "Reinforcement learning"],
                    "applications": ["Image recognition", "Natural language processing", "Recommendation systems", "Predictive analytics"]
                },
                "llm": {
                    "name": "Large Language Models",
                    "description": "Large Language Models (LLMs) are AI models trained on vast amounts of text data to understand and generate human-like text.",
                    "examples": ["GPT-4", "Claude", "LLaMA", "PaLM"],
                    "capabilities": ["Text generation", "Question answering", "Code generation", "Translation"]
                }
            },
            "science": {
                "quantum_computing": {
                    "name": "Quantum Computing",
                    "description": "Quantum computing uses quantum mechanical phenomena like superposition and entanglement to perform computations.",
                    "key_concepts": ["Qubits", "Superposition", "Entanglement", "Quantum gates"],
                    "potential_applications": ["Cryptography", "Drug discovery", "Optimization problems", "Financial modeling"]
                }
            },
            "history": {
                "internet": {
                    "name": "History of the Internet",
                    "description": "The internet evolved from ARPANET in the 1960s to become a global network connecting billions of devices.",
                    "milestones": [
                        "1969: ARPANET created",
                        "1983: TCP/IP adopted",
                        "1989: World Wide Web invented by Tim Berners-Lee",
                        "1990s: Commercial internet expansion"
                    ]
                }
            }
        }
    
    def _save_knowledge_base(self):
        """Save knowledge base to file."""
        kb_file = Path(self.kb_path)
        kb_file.parent.mkdir(parents=True, exist_ok=True)
        try:
            with open(kb_file, 'w', encoding='utf-8') as f:
                json.dump(self._kb_data, f, indent=2)
        except Exception as e:
            print(f"Warning: Failed to save knowledge base: {e}")
    
    def _search_kb(self, query: str, category: Optional[str] = None) -> List[Dict[str, Any]]:
        """Search knowledge base for matching entries."""
        query_lower = query.lower()
        results = []
        
        # Determine which categories to search
        categories_to_search = [category] if category and category in self._kb_data else self._kb_data.keys()
        
        for cat in categories_to_search:
            if cat not in self._kb_data:
                continue
                
            for key, value in self._kb_data[cat].items():
                # Check if query matches key or content
                if (query_lower in key.lower() or 
                    query_lower in str(value).lower()):
                    results.append({
                        "category": cat,
                        "key": key,
                        "data": value,
                        "relevance": self._calculate_relevance(query_lower, key, value)
                    })
        
        # Sort by relevance
        results.sort(key=lambda x: x["relevance"], reverse=True)
        return results
    
    def _calculate_relevance(self, query: str, key: str, value: Any) -> float:
        """Calculate relevance score for a result."""
        score = 0.0
        
        # Exact key match
        if query == key.lower():
            score += 10.0
        # Key contains query
        elif query in key.lower():
            score += 5.0
        
        # Check in name/description
        if isinstance(value, dict):
            name = value.get("name", "").lower()
            desc = value.get("description", "").lower()
            
            if query in name:
                score += 3.0
            if query in desc:
                score += 2.0
        
        return score
    
    async def execute(self, **kwargs) -> ToolResult:
        """Execute knowledge base query."""
        query = kwargs.get("query", "")
        category = kwargs.get("category")
        
        if not query:
            return ToolResult(
                success=False,
                error="Missing required parameter: query"
            )
        
        try:
            results = self._search_kb(query, category)
            
            if not results:
                return ToolResult(
                    success=True,
                    data=[],
                    metadata={
                        "query": query,
                        "category": category,
                        "message": "No matching entries found in knowledge base"
                    }
                )
            
            # Return top 3 results
            top_results = results[:3]
            
            return ToolResult(
                success=True,
                data=top_results,
                metadata={
                    "query": query,
                    "category": category,
                    "total_matches": len(results),
                    "returned": len(top_results)
                }
            )
            
        except Exception as e:
            return ToolResult(
                success=False,
                error=f"Knowledge base query failed: {str(e)}",
                metadata={"query": query, "category": category}
            )


