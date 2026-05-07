"""Observability and metrics tracking."""
import time
from typing import Dict, List, Any, Optional
from dataclasses import dataclass, field
from datetime import datetime
import json
from pathlib import Path


@dataclass
class MetricEvent:
    """A single metric event."""
    event_type: str
    timestamp: datetime
    data: Dict[str, Any]
    tags: Dict[str, str] = field(default_factory=dict)


class MetricsCollector:
    """Collects and tracks metrics for observability."""
    
    def __init__(self, log_path: Optional[str] = None):
        self.log_path = log_path or "agent_system/data/metrics.jsonl"
        self.events: List[MetricEvent] = []
        self.session_start = datetime.now()
        
        # Cost tracking (tokens to cost conversion)
        self.cost_per_1k_input_tokens = 0.01  # Example: $0.01 per 1K input tokens
        self.cost_per_1k_output_tokens = 0.03  # Example: $0.03 per 1K output tokens
    
    def track_llm_call(
        self,
        model: str,
        input_tokens: int,
        output_tokens: int,
        latency_ms: float,
        success: bool,
        error: Optional[str] = None
    ):
        """Track an LLM API call."""
        cost = (
            (input_tokens / 1000) * self.cost_per_1k_input_tokens +
            (output_tokens / 1000) * self.cost_per_1k_output_tokens
        )
        
        event = MetricEvent(
            event_type="llm_call",
            timestamp=datetime.now(),
            data={
                "model": model,
                "input_tokens": input_tokens,
                "output_tokens": output_tokens,
                "total_tokens": input_tokens + output_tokens,
                "latency_ms": latency_ms,
                "cost": cost,
                "success": success,
                "error": error
            },
            tags={"model": model, "success": str(success)}
        )
        self.events.append(event)
        return cost
    
    def track_tool_call(
        self,
        tool_name: str,
        latency_ms: float,
        success: bool,
        error: Optional[str] = None
    ):
        """Track a tool execution."""
        event = MetricEvent(
            event_type="tool_call",
            timestamp=datetime.now(),
            data={
                "tool_name": tool_name,
                "latency_ms": latency_ms,
                "success": success,
                "error": error
            },
            tags={"tool": tool_name, "success": str(success)}
        )
        self.events.append(event)
    
    def track_agent_turn(
        self,
        turn_number: int,
        total_latency_ms: float,
        total_cost: float,
        tool_calls: int,
        success: bool
    ):
        """Track a complete agent turn."""
        event = MetricEvent(
            event_type="agent_turn",
            timestamp=datetime.now(),
            data={
                "turn_number": turn_number,
                "total_latency_ms": total_latency_ms,
                "total_cost": total_cost,
                "tool_calls": tool_calls,
                "success": success
            },
            tags={"success": str(success)}
        )
        self.events.append(event)
    
    def get_summary(self) -> Dict[str, Any]:
        """Get a summary of all metrics."""
        llm_calls = [e for e in self.events if e.event_type == "llm_call"]
        tool_calls = [e for e in self.events if e.event_type == "tool_call"]
        agent_turns = [e for e in self.events if e.event_type == "agent_turn"]
        
        total_cost = sum(e.data.get("cost", 0) for e in llm_calls)
        total_tokens = sum(e.data.get("total_tokens", 0) for e in llm_calls)
        
        llm_success_rate = 0.0
        if llm_calls:
            llm_success_rate = sum(1 for e in llm_calls if e.data.get("success")) / len(llm_calls)
        
        tool_success_rate = 0.0
        if tool_calls:
            tool_success_rate = sum(1 for e in tool_calls if e.data.get("success")) / len(tool_calls)
        
        avg_latency = 0.0
        if agent_turns:
            avg_latency = sum(e.data.get("total_latency_ms", 0) for e in agent_turns) / len(agent_turns)
        
        return {
            "session_duration_seconds": (datetime.now() - self.session_start).total_seconds(),
            "total_events": len(self.events),
            "llm_calls": {
                "count": len(llm_calls),
                "success_rate": llm_success_rate,
                "total_tokens": total_tokens,
                "total_cost": total_cost
            },
            "tool_calls": {
                "count": len(tool_calls),
                "success_rate": tool_success_rate,
                "by_tool": self._count_by_tool(tool_calls)
            },
            "agent_turns": {
                "count": len(agent_turns),
                "average_latency_ms": avg_latency,
                "average_cost": total_cost / len(agent_turns) if agent_turns else 0.0
            }
        }
    
    def _count_by_tool(self, tool_calls: List[MetricEvent]) -> Dict[str, int]:
        """Count tool calls by tool name."""
        counts: Dict[str, int] = {}
        for event in tool_calls:
            tool_name = event.data.get("tool_name", "unknown")
            counts[tool_name] = counts.get(tool_name, 0) + 1
        return counts
    
    def save_to_file(self):
        """Save metrics to a JSONL file."""
        log_file = Path(self.log_path)
        log_file.parent.mkdir(parents=True, exist_ok=True)
        
        try:
            with open(log_file, 'a', encoding='utf-8') as f:
                for event in self.events:
                    event_dict = {
                        "event_type": event.event_type,
                        "timestamp": event.timestamp.isoformat(),
                        "data": event.data,
                        "tags": event.tags
                    }
                    f.write(json.dumps(event_dict) + '\n')
            self.events = []  # Clear events after saving
        except Exception as e:
            print(f"Warning: Failed to save metrics: {e}")
    
    def reset(self):
        """Reset metrics collector."""
        self.events = []
        self.session_start = datetime.now()


class LatencyTracker:
    """Context manager for tracking latency."""
    
    def __init__(self):
        self.start_time: Optional[float] = None
        self.end_time: Optional[float] = None
    
    def __enter__(self):
        self.start_time = time.time()
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        self.end_time = time.time()
    
    @property
    def latency_ms(self) -> float:
        """Get latency in milliseconds."""
        if self.start_time and self.end_time:
            return (self.end_time - self.start_time) * 1000
        return 0.0

