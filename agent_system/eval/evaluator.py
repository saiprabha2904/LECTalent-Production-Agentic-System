"""Evaluation harness for testing agent performance."""
import asyncio
import json
from typing import List, Dict, Any, Optional
from datetime import datetime
from pathlib import Path
from tabulate import tabulate

from .test_cases import TestCase, get_test_cases, get_test_cases_by_difficulty
from ..core.agent import Agent
from ..tools.calculator import Calculator
from ..tools.web_search import WebSearch
from ..tools.knowledge_base import KnowledgeBase
from ..tools.document_qa import DocumentQA


class EvaluationResult:
    """Result of evaluating a single test case."""
    
    def __init__(self, test_case: TestCase):
        self.test_case = test_case
        self.response: str = ""
        self.tools_used: List[str] = []
        self.success: bool = False
        self.error: Optional[str] = None
        self.latency_ms: float = 0.0
        self.cost: float = 0.0
        self.tool_selection_correct: bool = False
        self.response_quality: str = "unknown"  # good, acceptable, poor
        
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return {
            "query": self.test_case.query,
            "category": self.test_case.category,
            "difficulty": self.test_case.difficulty,
            "expected_tools": self.test_case.expected_tools,
            "tools_used": self.tools_used,
            "tool_selection_correct": self.tool_selection_correct,
            "success": self.success,
            "error": self.error,
            "latency_ms": self.latency_ms,
            "cost": self.cost,
            "response_quality": self.response_quality,
            "response": self.response[:200] + "..." if len(self.response) > 200 else self.response
        }


class Evaluator:
    """Evaluation harness for testing agent performance."""
    
    def __init__(
        self,
        agent: Optional[Agent] = None,
        output_dir: str = "agent_system/data/eval_results"
    ):
        self.agent = agent or self._create_default_agent()
        self.output_dir = Path(output_dir)
        self.output_dir.mkdir(parents=True, exist_ok=True)
        self.results: List[EvaluationResult] = []
    
    def _create_default_agent(self) -> Agent:
        """Create a default agent for evaluation."""
        tools = [
            Calculator(),
            WebSearch(),
            KnowledgeBase(),
            DocumentQA()
        ]
        return Agent(tools=tools, max_iterations=5, enable_fallback=True)
    
    async def evaluate_test_case(self, test_case: TestCase) -> EvaluationResult:
        """Evaluate a single test case."""
        result = EvaluationResult(test_case)
        
        try:
            # Reset agent state
            self.agent.reset()
            
            # Run the agent
            start_time = asyncio.get_event_loop().time()
            response = await self.agent.run(test_case.query)
            end_time = asyncio.get_event_loop().time()
            
            result.response = response
            result.latency_ms = (end_time - start_time) * 1000
            result.success = True
            
            # Get tools used from state
            if self.agent.state.conversation_history:
                last_turn = self.agent.state.conversation_history[-1]
                result.tools_used = [tc.tool_name for tc in last_turn.tool_calls]
                result.cost = last_turn.total_cost
            
            # Check tool selection correctness
            result.tool_selection_correct = self._check_tool_selection(
                test_case.expected_tools,
                result.tools_used
            )
            
            # Assess response quality (simple heuristic)
            result.response_quality = self._assess_response_quality(
                test_case,
                response,
                result.tools_used
            )
            
        except Exception as e:
            result.success = False
            result.error = str(e)
            result.response_quality = "poor"
        
        return result
    
    def _check_tool_selection(
        self,
        expected_tools: List[str],
        actual_tools: List[str]
    ) -> bool:
        """Check if tool selection was correct."""
        if not expected_tools:
            # If no tools expected, correct if no tools used
            return len(actual_tools) == 0
        
        # Check if all expected tools were used
        expected_set = set(expected_tools)
        actual_set = set(actual_tools)
        
        # Correct if expected tools are subset of actual tools
        return expected_set.issubset(actual_set)
    
    def _assess_response_quality(
        self,
        test_case: TestCase,
        response: str,
        tools_used: List[str]
    ) -> str:
        """Assess response quality using heuristics."""
        response_lower = response.lower()
        
        # Poor quality indicators
        if "error" in response_lower and "apologize" in response_lower:
            return "poor"
        if len(response) < 20:
            return "poor"
        if "maximum number of steps" in response_lower:
            return "poor"
        
        # Good quality indicators
        if test_case.expected_tools and tools_used:
            if self._check_tool_selection(test_case.expected_tools, tools_used):
                return "good"
        
        # For queries that shouldn't use tools
        if not test_case.expected_tools and not tools_used:
            if len(response) > 50:
                return "good"
        
        return "acceptable"
    
    async def run_evaluation(
        self,
        test_cases: Optional[List[TestCase]] = None,
        difficulties: Optional[List[str]] = None
    ) -> Dict[str, Any]:
        """Run evaluation on test cases."""
        if test_cases is None:
            if difficulties:
                test_cases = []
                for difficulty in difficulties:
                    test_cases.extend(get_test_cases_by_difficulty(difficulty))
            else:
                test_cases = get_test_cases()
        
        print(f"\n{'='*80}")
        print(f"Running evaluation on {len(test_cases)} test cases...")
        print(f"{'='*80}\n")
        
        self.results = []
        for i, test_case in enumerate(test_cases, 1):
            print(f"[{i}/{len(test_cases)}] Testing: {test_case.query[:60]}...")
            result = await self.evaluate_test_case(test_case)
            self.results.append(result)
            
            status = "✓" if result.success and result.tool_selection_correct else "✗"
            print(f"  {status} Tools: {result.tools_used}, Quality: {result.response_quality}")
        
        # Generate summary
        summary = self._generate_summary()
        
        # Save results
        self._save_results(summary)
        
        # Print summary
        self._print_summary(summary)
        
        return summary
    
    def _generate_summary(self) -> Dict[str, Any]:
        """Generate evaluation summary."""
        total = len(self.results)
        if total == 0:
            return {}
        
        successful = sum(1 for r in self.results if r.success)
        tool_selection_correct = sum(1 for r in self.results if r.tool_selection_correct)
        
        quality_counts = {
            "good": sum(1 for r in self.results if r.response_quality == "good"),
            "acceptable": sum(1 for r in self.results if r.response_quality == "acceptable"),
            "poor": sum(1 for r in self.results if r.response_quality == "poor")
        }
        
        # By difficulty
        by_difficulty = {}
        for difficulty in ["easy", "medium", "hard", "adversarial"]:
            diff_results = [r for r in self.results if r.test_case.difficulty == difficulty]
            if diff_results:
                by_difficulty[difficulty] = {
                    "total": len(diff_results),
                    "success_rate": sum(1 for r in diff_results if r.success) / len(diff_results),
                    "tool_selection_accuracy": sum(1 for r in diff_results if r.tool_selection_correct) / len(diff_results),
                    "avg_latency_ms": sum(r.latency_ms for r in diff_results) / len(diff_results),
                    "avg_cost": sum(r.cost for r in diff_results) / len(diff_results)
                }
        
        # By category
        by_category = {}
        categories = set(r.test_case.category for r in self.results)
        for category in categories:
            cat_results = [r for r in self.results if r.test_case.category == category]
            if cat_results:
                by_category[category] = {
                    "total": len(cat_results),
                    "success_rate": sum(1 for r in cat_results if r.success) / len(cat_results),
                    "tool_selection_accuracy": sum(1 for r in cat_results if r.tool_selection_correct) / len(cat_results)
                }
        
        return {
            "timestamp": datetime.now().isoformat(),
            "total_tests": total,
            "success_rate": successful / total,
            "tool_selection_accuracy": tool_selection_correct / total,
            "response_quality": quality_counts,
            "total_cost": sum(r.cost for r in self.results),
            "avg_latency_ms": sum(r.latency_ms for r in self.results) / total,
            "by_difficulty": by_difficulty,
            "by_category": by_category,
            "failed_tests": [
                {
                    "query": r.test_case.query,
                    "error": r.error,
                    "tools_used": r.tools_used,
                    "expected_tools": r.test_case.expected_tools
                }
                for r in self.results if not r.success or not r.tool_selection_correct
            ]
        }
    
    def _save_results(self, summary: Dict[str, Any]):
        """Save evaluation results to file."""
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        
        # Save detailed results
        results_file = self.output_dir / f"eval_results_{timestamp}.json"
        with open(results_file, 'w') as f:
            json.dump({
                "summary": summary,
                "detailed_results": [r.to_dict() for r in self.results]
            }, f, indent=2)
        
        print(f"\nResults saved to: {results_file}")
    
    def _print_summary(self, summary: Dict[str, Any]):
        """Print evaluation summary."""
        print(f"\n{'='*80}")
        print("EVALUATION SUMMARY")
        print(f"{'='*80}")
        
        print(f"\nOverall Performance:")
        print(f"  Total Tests: {summary['total_tests']}")
        print(f"  Success Rate: {summary['success_rate']:.1%}")
        print(f"  Tool Selection Accuracy: {summary['tool_selection_accuracy']:.1%}")
        print(f"  Total Cost: ${summary['total_cost']:.4f}")
        print(f"  Avg Latency: {summary['avg_latency_ms']:.0f}ms")
        
        print(f"\nResponse Quality:")
        for quality, count in summary['response_quality'].items():
            print(f"  {quality.capitalize()}: {count}")
        
        print(f"\nPerformance by Difficulty:")
        table_data = []
        for difficulty, stats in summary['by_difficulty'].items():
            table_data.append([
                difficulty.capitalize(),
                stats['total'],
                f"{stats['success_rate']:.1%}",
                f"{stats['tool_selection_accuracy']:.1%}",
                f"{stats['avg_latency_ms']:.0f}ms",
                f"${stats['avg_cost']:.4f}"
            ])
        print(tabulate(
            table_data,
            headers=["Difficulty", "Tests", "Success", "Tool Accuracy", "Latency", "Cost"],
            tablefmt="grid"
        ))
        
        if summary['failed_tests']:
            print(f"\nFailed/Incorrect Tests ({len(summary['failed_tests'])}):")
            for i, failed in enumerate(summary['failed_tests'][:5], 1):
                print(f"  {i}. {failed['query'][:60]}...")
                print(f"     Expected: {failed['expected_tools']}, Used: {failed['tools_used']}")
                if failed['error']:
                    print(f"     Error: {failed['error']}")


async def run_quick_eval():
    """Run a quick evaluation with easy and medium cases."""
    evaluator = Evaluator()
    await evaluator.run_evaluation(difficulties=["easy", "medium"])


async def run_full_eval():
    """Run full evaluation including adversarial cases."""
    evaluator = Evaluator()
    await evaluator.run_evaluation()


if __name__ == "__main__":
    # Run evaluation
    asyncio.run(run_full_eval())

