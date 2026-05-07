"""Prompt ablation experiments."""
import asyncio
import json
from typing import List, Dict, Any, Optional
from datetime import datetime
from pathlib import Path
from tabulate import tabulate

from .test_cases import get_test_cases_by_difficulty
from .evaluator import Evaluator, EvaluationResult
from ..core.agent import Agent
from ..tools.calculator import Calculator
from ..tools.web_search import WebSearch
from ..tools.knowledge_base import KnowledgeBase
from ..tools.document_qa import DocumentQA
from ..prompts.prompt_variants import get_prompt_variants


class AblationStudy:
    """Run ablation studies on prompt variants."""
    
    def __init__(self, output_dir: str = "agent_system/data/ablation_results"):
        self.output_dir = Path(output_dir)
        self.output_dir.mkdir(parents=True, exist_ok=True)
        self.results: Dict[str, Dict[str, Any]] = {}
    
    async def run_ablation(
        self,
        difficulties: Optional[List[str]] = None,
        variants: Optional[List[str]] = None
    ) -> Dict[str, Any]:
        if difficulties is None:
            difficulties = ["easy", "medium"]
        """Run ablation study comparing prompt variants."""
        
        # Get test cases
        test_cases = []
        for difficulty in difficulties:
            test_cases.extend(get_test_cases_by_difficulty(difficulty))
        
        print(f"\n{'='*80}")
        print(f"PROMPT ABLATION STUDY")
        print(f"{'='*80}")
        print(f"Test cases: {len(test_cases)} ({', '.join(difficulties)} difficulty)")
        print(f"{'='*80}\n")
        
        # Get prompt variants
        all_variants = get_prompt_variants()
        if variants:
            all_variants = [v for v in all_variants if v.name in variants]
        
        # Test each variant
        for variant in all_variants:
            print(f"\nTesting variant: {variant.name}")
            print(f"Description: {variant.description}")
            print("-" * 80)
            
            # Create agent with this prompt variant
            tools = [Calculator(), WebSearch(), KnowledgeBase(), DocumentQA()]
            agent = Agent(tools=tools, max_iterations=5, enable_fallback=True)
            
            # Override system prompt
            agent.system_prompt = variant.build(agent.tools)
            
            # Run evaluation
            evaluator = Evaluator(agent=agent)
            results = []
            
            for i, test_case in enumerate(test_cases, 1):
                print(f"  [{i}/{len(test_cases)}] {test_case.query[:50]}...")
                result = await evaluator.evaluate_test_case(test_case)
                results.append(result)
            
            # Store results
            self.results[variant.name] = {
                "variant": variant.name,
                "description": variant.description,
                "results": results,
                "summary": self._compute_variant_summary(results)
            }
        
        # Generate comparison
        comparison = self._generate_comparison()
        
        # Save results
        self._save_results(comparison)
        
        # Print comparison
        self._print_comparison(comparison)
        
        return comparison
    
    def _compute_variant_summary(self, results: List[EvaluationResult]) -> Dict[str, Any]:
        """Compute summary statistics for a variant."""
        total = len(results)
        if total == 0:
            return {}
        
        return {
            "total_tests": total,
            "success_rate": sum(1 for r in results if r.success) / total,
            "tool_selection_accuracy": sum(1 for r in results if r.tool_selection_correct) / total,
            "avg_latency_ms": sum(r.latency_ms for r in results) / total,
            "total_cost": sum(r.cost for r in results),
            "avg_cost": sum(r.cost for r in results) / total,
            "quality_good": sum(1 for r in results if r.response_quality == "good") / total,
            "quality_acceptable": sum(1 for r in results if r.response_quality == "acceptable") / total,
            "quality_poor": sum(1 for r in results if r.response_quality == "poor") / total
        }
    
    def _generate_comparison(self) -> Dict[str, Any]:
        """Generate comparison across all variants."""
        comparison = {
            "timestamp": datetime.now().isoformat(),
            "variants_tested": len(self.results),
            "variants": {}
        }
        
        for variant_name, variant_data in self.results.items():
            comparison["variants"][variant_name] = {
                "description": variant_data["description"],
                "summary": variant_data["summary"]
            }
        
        # Find best variant for each metric
        if self.results:
            comparison["best_variants"] = {
                "success_rate": max(self.results.items(), key=lambda x: x[1]["summary"]["success_rate"])[0],
                "tool_accuracy": max(self.results.items(), key=lambda x: x[1]["summary"]["tool_selection_accuracy"])[0],
                "quality": max(self.results.items(), key=lambda x: x[1]["summary"]["quality_good"])[0],
                "speed": min(self.results.items(), key=lambda x: x[1]["summary"]["avg_latency_ms"])[0],
                "cost": min(self.results.items(), key=lambda x: x[1]["summary"]["avg_cost"])[0]
            }
        
        return comparison
    
    def _save_results(self, comparison: Dict[str, Any]):
        """Save ablation results."""
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        
        # Save comparison
        comparison_file = self.output_dir / f"ablation_comparison_{timestamp}.json"
        with open(comparison_file, 'w') as f:
            json.dump(comparison, f, indent=2)
        
        # Save detailed results for each variant
        for variant_name, variant_data in self.results.items():
            variant_file = self.output_dir / f"ablation_{variant_name}_{timestamp}.json"
            with open(variant_file, 'w') as f:
                json.dump({
                    "variant": variant_name,
                    "description": variant_data["description"],
                    "summary": variant_data["summary"],
                    "detailed_results": [r.to_dict() for r in variant_data["results"]]
                }, f, indent=2)
        
        print(f"\nAblation results saved to: {self.output_dir}")
    
    def _print_comparison(self, comparison: Dict[str, Any]):
        """Print ablation comparison."""
        print(f"\n{'='*80}")
        print("ABLATION STUDY RESULTS")
        print(f"{'='*80}\n")
        
        # Comparison table
        table_data = []
        for variant_name, variant_info in comparison["variants"].items():
            summary = variant_info["summary"]
            table_data.append([
                variant_name,
                f"{summary['success_rate']:.1%}",
                f"{summary['tool_selection_accuracy']:.1%}",
                f"{summary['quality_good']:.1%}",
                f"{summary['avg_latency_ms']:.0f}ms",
                f"${summary['avg_cost']:.4f}"
            ])
        
        print(tabulate(
            table_data,
            headers=["Variant", "Success", "Tool Acc", "Quality", "Latency", "Cost"],
            tablefmt="grid"
        ))
        
        # Best variants
        if "best_variants" in comparison:
            print(f"\nBest Variants by Metric:")
            for metric, variant in comparison["best_variants"].items():
                print(f"  {metric.replace('_', ' ').title()}: {variant}")
        
        # Key findings
        print(f"\nKey Findings:")
        variants = comparison["variants"]
        
        # Compare baseline to minimal
        if "baseline" in variants and "minimal" in variants:
            baseline = variants["baseline"]["summary"]
            minimal = variants["minimal"]["summary"]
            
            success_diff = (baseline["success_rate"] - minimal["success_rate"]) * 100
            tool_diff = (baseline["tool_selection_accuracy"] - minimal["tool_selection_accuracy"]) * 100
            
            print(f"  • Baseline vs Minimal:")
            print(f"    - Success rate difference: {success_diff:+.1f}%")
            print(f"    - Tool accuracy difference: {tool_diff:+.1f}%")
        
        # Compare with/without examples
        if "baseline" in variants and "no_examples" in variants:
            baseline = variants["baseline"]["summary"]
            no_examples = variants["no_examples"]["summary"]
            
            quality_diff = (baseline["quality_good"] - no_examples["quality_good"]) * 100
            print(f"  • Impact of Examples:")
            print(f"    - Quality improvement: {quality_diff:+.1f}%")
        
        # Compare with/without guidelines
        if "baseline" in variants and "no_guidelines" in variants:
            baseline = variants["baseline"]["summary"]
            no_guidelines = variants["no_guidelines"]["summary"]
            
            tool_diff = (baseline["tool_selection_accuracy"] - no_guidelines["tool_selection_accuracy"]) * 100
            print(f"  • Impact of Guidelines:")
            print(f"    - Tool accuracy improvement: {tool_diff:+.1f}%")


async def run_quick_ablation():
    """Run quick ablation with easy cases only."""
    study = AblationStudy()
    await study.run_ablation(difficulties=["easy"])


async def run_full_ablation():
    """Run full ablation study."""
    study = AblationStudy()
    await study.run_ablation(difficulties=["easy", "medium", "hard"])


if __name__ == "__main__":
    asyncio.run(run_full_ablation())

