"""Example usage of the agent system."""
import asyncio
import os
from agent_system.core.agent import Agent
from agent_system.tools.calculator import Calculator
from agent_system.tools.web_search import WebSearch
from agent_system.tools.knowledge_base import KnowledgeBase
from agent_system.tools.document_qa import DocumentQA


async def main():
    """Run example queries."""
    
    # Set up API key (or use environment variable)
    # os.environ["OPENAI_API_KEY"] = "your-key-here"
    
    # Create tools
    tools = [
        Calculator(),
        WebSearch(),
        KnowledgeBase(),
        DocumentQA()
    ]
    
    # Create agent
    agent = Agent(
        tools=tools,
        model="gpt-4o-mini",
        max_iterations=5,
        enable_fallback=True
    )
    
    # Example queries
    queries = [
        "What is 15% of 250?",
        "What is machine learning?",
        "Calculate the square root of 144 and tell me about Python",
        "What are the key features in the agent systems guide?",
    ]
    
    print("=" * 80)
    print("AGENT SYSTEM DEMO")
    print("=" * 80)
    
    for i, query in enumerate(queries, 1):
        print(f"\n[Query {i}] {query}")
        print("-" * 80)
        
        try:
            response = await agent.run(query)
            print(f"Response: {response}")
            
            # Show tools used
            if agent.state.conversation_history:
                last_turn = agent.state.conversation_history[-1]
                if last_turn.tool_calls:
                    tools_used = [tc.tool_name for tc in last_turn.tool_calls]
                    print(f"Tools used: {', '.join(tools_used)}")
                    print(f"Cost: ${last_turn.total_cost:.4f}")
                    print(f"Latency: {last_turn.total_latency_ms:.0f}ms")
        
        except Exception as e:
            print(f"Error: {e}")
    
    # Print overall statistics
    print("\n" + "=" * 80)
    print("OVERALL STATISTICS")
    print("=" * 80)
    
    stats = agent.get_state_statistics()
    print(f"Total turns: {stats['total_turns']}")
    print(f"Total tool calls: {stats['total_tool_calls']}")
    print(f"Success rate: {stats['success_rate']:.1%}")
    print(f"Total cost: ${stats['total_cost']:.4f}")
    
    metrics = agent.get_metrics_summary()
    print(f"\nLLM calls: {metrics['llm_calls']['count']}")
    print(f"Total tokens: {metrics['llm_calls']['total_tokens']}")
    print(f"Tool usage: {metrics['tool_calls']['by_tool']}")
    
    # Save metrics
    agent.save_metrics()
    print("\nMetrics saved to agent_system/data/metrics.jsonl")


if __name__ == "__main__":
    asyncio.run(main())


