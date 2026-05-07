"""Test cases for agent evaluation including adversarial queries."""
from typing import List, Dict, Any
from dataclasses import dataclass


@dataclass
class TestCase:
    """A single test case for evaluation."""
    query: str
    category: str
    expected_tools: List[str]
    difficulty: str  # easy, medium, hard, adversarial
    description: str
    expected_behavior: str


def get_test_cases() -> List[TestCase]:
    """Get comprehensive test cases including adversarial queries."""
    return [
        # Easy cases - single tool, clear intent
        TestCase(
            query="What is 15% of 250?",
            category="calculation",
            expected_tools=["calculator"],
            difficulty="easy",
            description="Simple percentage calculation",
            expected_behavior="Should use calculator and return 37.5"
        ),
        TestCase(
            query="What is machine learning?",
            category="knowledge",
            expected_tools=["knowledge_base"],
            difficulty="easy",
            description="Knowledge base lookup",
            expected_behavior="Should query knowledge base and return definition"
        ),
        TestCase(
            query="What are the key features in the agent systems guide?",
            category="document",
            expected_tools=["document_qa"],
            difficulty="easy",
            description="Document Q&A",
            expected_behavior="Should search documents and extract key features"
        ),
        
        # Medium cases - multiple tools or ambiguous
        TestCase(
            query="Calculate the square root of 144 and tell me about Python",
            category="multi_tool",
            expected_tools=["calculator", "knowledge_base"],
            difficulty="medium",
            description="Multiple independent tasks",
            expected_behavior="Should use calculator for sqrt(144)=12, then knowledge_base for Python info"
        ),
        TestCase(
            query="What's the latest news about AI?",
            category="search",
            expected_tools=["web_search"],
            difficulty="medium",
            description="Current events requiring web search",
            expected_behavior="Should use web_search for current information"
        ),
        TestCase(
            query="How do I authenticate with the API according to the documentation?",
            category="document",
            expected_tools=["document_qa"],
            difficulty="medium",
            description="Specific document query",
            expected_behavior="Should search API documentation for authentication info"
        ),
        
        # Hard cases - complex reasoning, tool chaining
        TestCase(
            query="If I have $1000 and invest it at 5% annual interest, how much will I have after 3 years? Also, what does the knowledge base say about financial modeling?",
            category="complex",
            expected_tools=["calculator", "knowledge_base"],
            difficulty="hard",
            description="Compound calculation plus knowledge lookup",
            expected_behavior="Should calculate compound interest (1000 * 1.05^3 = 1157.625) and query knowledge base"
        ),
        TestCase(
            query="Compare what the documents say about LLM best practices with current web information",
            category="complex",
            expected_tools=["document_qa", "web_search"],
            difficulty="hard",
            description="Multi-source comparison",
            expected_behavior="Should query documents first, then web search, and synthesize comparison"
        ),
        
        # Adversarial cases - edge cases, ambiguous, misleading
        TestCase(
            query="Calculate the meaning of life",
            category="adversarial",
            expected_tools=[],
            difficulty="adversarial",
            description="Philosophical question disguised as calculation",
            expected_behavior="Should recognize this isn't a calculation and respond appropriately without tools"
        ),
        TestCase(
            query="Search for information about a topic that definitely doesn't exist: xyzabc123nonsense",
            category="adversarial",
            expected_tools=["knowledge_base", "web_search"],
            difficulty="adversarial",
            description="Non-existent topic",
            expected_behavior="Should try knowledge_base, then web_search, and gracefully handle no results"
        ),
        TestCase(
            query="What is 10 divided by 0?",
            category="adversarial",
            expected_tools=["calculator"],
            difficulty="adversarial",
            description="Division by zero",
            expected_behavior="Should attempt calculation and handle division by zero error gracefully"
        ),
        TestCase(
            query="",
            category="adversarial",
            expected_tools=[],
            difficulty="adversarial",
            description="Empty query",
            expected_behavior="Should handle empty input gracefully without crashing"
        ),
        TestCase(
            query="Use the calculator to search the web for documents about knowledge",
            category="adversarial",
            expected_tools=[],
            difficulty="adversarial",
            description="Confused tool instructions",
            expected_behavior="Should ignore confused instructions and determine appropriate action"
        ),
        TestCase(
            query="What is 2+2? What is 3+3? What is 4+4? What is 5+5? What is 6+6?",
            category="adversarial",
            expected_tools=["calculator"],
            difficulty="adversarial",
            description="Multiple similar requests",
            expected_behavior="Should handle multiple calculations efficiently"
        ),
        TestCase(
            query="Tell me everything about everything",
            category="adversarial",
            expected_tools=[],
            difficulty="adversarial",
            description="Overly broad request",
            expected_behavior="Should ask for clarification or provide a reasonable scoped response"
        ),
        TestCase(
            query="Calculate sin(pi/2) + cos(0) * sqrt(16)",
            category="calculation",
            expected_tools=["calculator"],
            difficulty="hard",
            description="Complex mathematical expression",
            expected_behavior="Should calculate: sin(pi/2)=1, cos(0)=1, sqrt(16)=4, result=1+1*4=5"
        ),
        TestCase(
            query="What does the document say about topics that aren't in any document?",
            category="adversarial",
            expected_tools=["document_qa"],
            difficulty="adversarial",
            description="Document query for non-existent content",
            expected_behavior="Should search documents and report no relevant information found"
        ),
        TestCase(
            query="Search for Python but only in the history category",
            category="knowledge",
            expected_tools=["knowledge_base"],
            difficulty="medium",
            description="Constrained knowledge base search",
            expected_behavior="Should search knowledge_base with category filter"
        ),
    ]


def get_test_cases_by_difficulty(difficulty: str) -> List[TestCase]:
    """Get test cases filtered by difficulty."""
    return [tc for tc in get_test_cases() if tc.difficulty == difficulty]


def get_test_cases_by_category(category: str) -> List[TestCase]:
    """Get test cases filtered by category."""
    return [tc for tc in get_test_cases() if tc.category == category]

