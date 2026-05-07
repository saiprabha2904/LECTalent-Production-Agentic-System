"""State management for the agent system."""
from typing import Dict, List, Any, Optional
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum


class AgentStatus(str, Enum):
    """Agent execution status."""
    IDLE = "idle"
    THINKING = "thinking"
    EXECUTING_TOOL = "executing_tool"
    ERROR = "error"
    COMPLETED = "completed"


@dataclass
class ToolCall:
    """Record of a tool call."""
    tool_name: str
    parameters: Dict[str, Any]
    result: Any
    success: bool
    error: Optional[str] = None
    timestamp: datetime = field(default_factory=datetime.now)
    latency_ms: float = 0.0
    cost: float = 0.0


@dataclass
class ConversationTurn:
    """A single turn in the conversation."""
    user_message: str
    agent_response: str
    tool_calls: List[ToolCall] = field(default_factory=list)
    timestamp: datetime = field(default_factory=datetime.now)
    total_cost: float = 0.0
    total_latency_ms: float = 0.0


class AgentState:
    """Manages the state of the agent system."""
    
    def __init__(self, max_history: int = 10):
        self.status: AgentStatus = AgentStatus.IDLE
        self.conversation_history: List[ConversationTurn] = []
        self.context: Dict[str, Any] = {}
        self.max_history = max_history
        self.total_cost: float = 0.0
        self.total_tool_calls: int = 0
        self.failed_tool_calls: int = 0
        self.current_turn: Optional[ConversationTurn] = None
    
    def start_turn(self, user_message: str):
        """Start a new conversation turn."""
        self.current_turn = ConversationTurn(
            user_message=user_message,
            agent_response=""
        )
        self.status = AgentStatus.THINKING
    
    def add_tool_call(self, tool_call: ToolCall):
        """Add a tool call to the current turn."""
        if self.current_turn:
            self.current_turn.tool_calls.append(tool_call)
            self.current_turn.total_cost += tool_call.cost
            self.current_turn.total_latency_ms += tool_call.latency_ms
            self.total_cost += tool_call.cost
            self.total_tool_calls += 1
            if not tool_call.success:
                self.failed_tool_calls += 1
    
    def complete_turn(self, agent_response: str):
        """Complete the current turn."""
        if self.current_turn:
            self.current_turn.agent_response = agent_response
            self.conversation_history.append(self.current_turn)
            
            # Trim history if needed
            if len(self.conversation_history) > self.max_history:
                self.conversation_history = self.conversation_history[-self.max_history:]
            
            self.current_turn = None
            self.status = AgentStatus.COMPLETED
    
    def set_error(self, error_message: str):
        """Set error status."""
        self.status = AgentStatus.ERROR
        if self.current_turn:
            self.current_turn.agent_response = f"Error: {error_message}"
    
    def update_context(self, key: str, value: Any):
        """Update context with a key-value pair."""
        self.context[key] = value
    
    def get_context(self, key: str, default: Any = None) -> Any:
        """Get a value from context."""
        return self.context.get(key, default)
    
    def get_recent_history(self, n: int = 3) -> List[ConversationTurn]:
        """Get the n most recent conversation turns."""
        return self.conversation_history[-n:] if self.conversation_history else []
    
    def get_statistics(self) -> Dict[str, Any]:
        """Get statistics about the agent's performance."""
        success_rate = 0.0
        if self.total_tool_calls > 0:
            success_rate = (self.total_tool_calls - self.failed_tool_calls) / self.total_tool_calls
        
        return {
            "total_turns": len(self.conversation_history),
            "total_tool_calls": self.total_tool_calls,
            "failed_tool_calls": self.failed_tool_calls,
            "success_rate": success_rate,
            "total_cost": self.total_cost,
            "average_cost_per_turn": self.total_cost / len(self.conversation_history) if self.conversation_history else 0.0,
            "status": self.status.value
        }
    
    def reset(self):
        """Reset the agent state."""
        self.status = AgentStatus.IDLE
        self.conversation_history = []
        self.context = {}
        self.total_cost = 0.0
        self.total_tool_calls = 0
        self.failed_tool_calls = 0
        self.current_turn = None

