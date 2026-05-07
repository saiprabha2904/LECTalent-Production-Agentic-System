"""Document Q&A tool for querying document content."""
import json
from typing import Dict, List, Any, Optional
from pathlib import Path
from .base import BaseTool, ToolSchema, ToolResult, ToolCategory


class DocumentQA(BaseTool):
    """Answer questions about documents in the document store."""
    
    def __init__(self, docs_path: Optional[str] = None):
        self.docs_path = docs_path or "agent_system/data/documents"
        self._documents: Dict[str, Dict[str, Any]] = {}
        self._load_documents()
        super().__init__()
    
    def _create_schema(self) -> ToolSchema:
        return ToolSchema(
            name="document_qa",
            description="Query and retrieve information from stored documents. Can search across multiple documents and extract relevant passages. Use when you need to find specific information in documents or answer questions based on document content.",
            category=ToolCategory.DOCUMENT,
            parameters={
                "type": "object",
                "properties": {
                    "question": {
                        "type": "string",
                        "description": "Question to answer from the documents"
                    },
                    "document_id": {
                        "type": "string",
                        "description": "Optional specific document ID to search in",
                        "default": None
                    }
                },
                "required": ["question"]
            },
            examples=[
                "What are the key features mentioned in the product documentation?",
                "Summarize the main points from the research paper",
                "Find information about API authentication in the docs",
                "What does the contract say about payment terms?",
            ]
        )
    
    def _load_documents(self):
        """Load documents from the document store."""
        docs_dir = Path(self.docs_path)
        if docs_dir.exists():
            for doc_file in docs_dir.glob("*.json"):
                try:
                    with open(doc_file, 'r', encoding='utf-8') as f:
                        doc_data = json.load(f)
                        doc_id = doc_file.stem
                        self._documents[doc_id] = doc_data
                except Exception as e:
                    print(f"Warning: Failed to load document {doc_file}: {e}")
        else:
            # Create sample documents
            self._documents = self._get_sample_documents()
            self._save_documents()
    
    def _get_sample_documents(self) -> Dict[str, Dict[str, Any]]:
        """Get sample documents for demonstration."""
        return {
            "agent_systems_guide": {
                "title": "Guide to Building Agent Systems",
                "content": """
                Agent systems are autonomous software entities that can perceive their environment,
                make decisions, and take actions to achieve specific goals. Key components include:
                
                1. Perception: Gathering information from the environment through sensors or APIs
                2. Decision Making: Using reasoning and planning to determine actions
                3. Action: Executing decisions through actuators or tool calls
                4. Learning: Improving performance over time through experience
                
                Best practices for agent systems:
                - Clear tool schemas with well-defined inputs and outputs
                - Robust error handling and fallback mechanisms
                - State management to track conversation and context
                - Observability for monitoring performance and costs
                - Evaluation harnesses to test agent behavior
                
                Common challenges:
                - Tool selection: Choosing the right tool for each task
                - Error recovery: Handling failures gracefully
                - Context management: Maintaining relevant information
                - Cost optimization: Balancing performance and expenses
                """,
                "metadata": {
                    "author": "AI Research Team",
                    "date": "2024-01-15",
                    "category": "technical_guide"
                }
            },
            "llm_best_practices": {
                "title": "LLM Integration Best Practices",
                "content": """
                When integrating Large Language Models into applications:
                
                Prompt Engineering:
                - Be specific and clear in instructions
                - Provide examples when possible
                - Use structured output formats (JSON, XML)
                - Include relevant context
                
                Error Handling:
                - Implement retry logic with exponential backoff
                - Validate LLM outputs before using them
                - Have fallback strategies for failures
                - Log errors for debugging
                
                Cost Management:
                - Cache responses when appropriate
                - Use smaller models for simple tasks
                - Implement rate limiting
                - Monitor token usage
                
                Security:
                - Sanitize user inputs
                - Validate outputs before execution
                - Implement content filtering
                - Use API keys securely
                
                Testing:
                - Create comprehensive test suites
                - Include edge cases and adversarial inputs
                - Test with different prompt variations
                - Monitor performance metrics
                """,
                "metadata": {
                    "author": "Engineering Team",
                    "date": "2024-02-20",
                    "category": "best_practices"
                }
            },
            "api_documentation": {
                "title": "Agent System API Documentation",
                "content": """
                API Endpoints:
                
                POST /agent/query
                - Execute an agent query
                - Request body: {"query": "string", "context": {}}
                - Response: {"result": "string", "tools_used": [], "cost": float}
                
                GET /agent/tools
                - List available tools
                - Response: [{"name": "string", "description": "string", "schema": {}}]
                
                POST /agent/tool/execute
                - Execute a specific tool
                - Request body: {"tool_name": "string", "parameters": {}}
                - Response: {"success": bool, "data": any, "error": "string"}
                
                GET /agent/state
                - Get current agent state
                - Response: {"conversation_history": [], "context": {}}
                
                Authentication:
                - Use Bearer token in Authorization header
                - Token format: "Bearer <your_api_key>"
                
                Rate Limits:
                - 100 requests per minute per API key
                - 1000 requests per hour per API key
                """,
                "metadata": {
                    "version": "1.0.0",
                    "date": "2024-03-01",
                    "category": "api_docs"
                }
            }
        }
    
    def _save_documents(self):
        """Save documents to the document store."""
        docs_dir = Path(self.docs_path)
        docs_dir.mkdir(parents=True, exist_ok=True)
        
        for doc_id, doc_data in self._documents.items():
            doc_file = docs_dir / f"{doc_id}.json"
            try:
                with open(doc_file, 'w', encoding='utf-8') as f:
                    json.dump(doc_data, f, indent=2)
            except Exception as e:
                print(f"Warning: Failed to save document {doc_id}: {e}")
    
    def _search_documents(self, question: str, document_id: Optional[str] = None) -> List[Dict[str, Any]]:
        """Search documents for relevant information."""
        question_lower = question.lower()
        results = []
        
        # Determine which documents to search
        docs_to_search = {document_id: self._documents[document_id]} if document_id and document_id in self._documents else self._documents
        
        for doc_id, doc_data in docs_to_search.items():
            content = doc_data.get("content", "")
            title = doc_data.get("title", "")
            
            # Simple keyword matching and relevance scoring
            relevance = 0.0
            
            # Check title
            if any(word in title.lower() for word in question_lower.split()):
                relevance += 2.0
            
            # Check content - find relevant paragraphs
            paragraphs = [p.strip() for p in content.split('\n\n') if p.strip()]
            relevant_paragraphs = []
            
            for para in paragraphs:
                para_lower = para.lower()
                # Count matching words
                matches = sum(1 for word in question_lower.split() if len(word) > 3 and word in para_lower)
                if matches > 0:
                    relevance += matches
                    relevant_paragraphs.append(para)
            
            if relevance > 0:
                results.append({
                    "document_id": doc_id,
                    "title": title,
                    "relevant_content": relevant_paragraphs[:3],  # Top 3 paragraphs
                    "metadata": doc_data.get("metadata", {}),
                    "relevance": relevance
                })
        
        # Sort by relevance
        results.sort(key=lambda x: x["relevance"], reverse=True)
        return results
    
    async def execute(self, **kwargs) -> ToolResult:
        """Execute document Q&A."""
        question = kwargs.get("question", "")
        document_id = kwargs.get("document_id")
        
        if not question:
            return ToolResult(
                success=False,
                error="Missing required parameter: question"
            )
        
        try:
            if not self._documents:
                return ToolResult(
                    success=True,
                    data=[],
                    metadata={
                        "question": question,
                        "message": "No documents available in the document store"
                    }
                )
            
            results = self._search_documents(question, document_id)
            
            if not results:
                return ToolResult(
                    success=True,
                    data=[],
                    metadata={
                        "question": question,
                        "document_id": document_id,
                        "message": "No relevant information found in documents"
                    }
                )
            
            # Return top 2 results
            top_results = results[:2]
            
            return ToolResult(
                success=True,
                data=top_results,
                metadata={
                    "question": question,
                    "document_id": document_id,
                    "total_matches": len(results),
                    "returned": len(top_results)
                }
            )
            
        except Exception as e:
            return ToolResult(
                success=False,
                error=f"Document Q&A failed: {str(e)}",
                metadata={"question": question, "document_id": document_id}
            )


