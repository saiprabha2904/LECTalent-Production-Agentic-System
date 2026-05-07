"""Base tool interface and schema definitions."""
from abc import ABC, abstractmethod
from typing import Any, Dict, Optional
from pydantic import BaseModel, Field
from enum import Enum


class ToolCategory(str, Enum):
    """Categories for organizing tools."""
    SEARCH = "search"
    COMPUTATION = "computation"
    KNOWLEDGE = "knowledge"
    DOCUMENT = "document"


class ToolSchema(BaseModel):
    """Schema definition for a tool."""
    name: str = Field(..., description="Unique tool identifier")
    description: str = Field(..., description="What the tool does")
    category: ToolCategory = Field(..., description="Tool category")
    parameters: Dict[str, Any] = Field(default_factory=dict, description="Parameter schema")
    examples: list[str] = Field(default_factory=list, description="Usage examples")
    
    class Config:
        use_enum_values = True


class ToolResult(BaseModel):
    """Result from tool execution."""
    success: bool
    data: Any = None
    error: Optional[str] = None
    metadata: Dict[str, Any] = Field(default_factory=dict)
    
    def __str__(self) -> str:
        if self.success:
            return f"Success: {self.data}"
        return f"Error: {self.error}"


class BaseTool(ABC):
    """Abstract base class for all tools."""
    
    def __init__(self):
        self._schema = self._create_schema()
    
    @abstractmethod
    def _create_schema(self) -> ToolSchema:
        """Create the tool schema."""
        pass
    
    @abstractmethod
    async def execute(self, **kwargs) -> ToolResult:
        """Execute the tool with given parameters."""
        pass
    
    @property
    def schema(self) -> ToolSchema:
        """Get the tool schema."""
        return self._schema
    
    def validate_params(self, params: Dict[str, Any]) -> tuple[bool, Optional[str]]:
        """Validate parameters against schema."""
        required_params = self._schema.parameters.get("required", [])
        for param in required_params:
            if param not in params:
                return False, f"Missing required parameter: {param}"
        return True, None

