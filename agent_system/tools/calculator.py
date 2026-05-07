"""Calculator tool for mathematical computations."""
import ast
import operator
import math
from typing import Any, Dict
from .base import BaseTool, ToolSchema, ToolResult, ToolCategory


class Calculator(BaseTool):
    """Safe calculator for mathematical expressions."""
    
    # Allowed operators and functions
    OPERATORS = {
        ast.Add: operator.add,
        ast.Sub: operator.sub,
        ast.Mult: operator.mul,
        ast.Div: operator.truediv,
        ast.Pow: operator.pow,
        ast.USub: operator.neg,
        ast.UAdd: operator.pos,
        ast.Mod: operator.mod,
    }
    
    FUNCTIONS = {
        'sqrt': math.sqrt,
        'sin': math.sin,
        'cos': math.cos,
        'tan': math.tan,
        'log': math.log,
        'log10': math.log10,
        'exp': math.exp,
        'abs': abs,
        'round': round,
        'floor': math.floor,
        'ceil': math.ceil,
    }
    
    CONSTANTS = {
        'pi': math.pi,
        'e': math.e,
    }
    
    def _create_schema(self) -> ToolSchema:
        return ToolSchema(
            name="calculator",
            description="Evaluate mathematical expressions safely. Supports basic arithmetic, powers, modulo, and common math functions (sqrt, sin, cos, tan, log, exp, etc.). Use for any numerical computation.",
            category=ToolCategory.COMPUTATION,
            parameters={
                "type": "object",
                "properties": {
                    "expression": {
                        "type": "string",
                        "description": "Mathematical expression to evaluate (e.g., '2 + 2', 'sqrt(16)', 'sin(pi/2)')"
                    }
                },
                "required": ["expression"]
            },
            examples=[
                "Calculate 15% tip on $45.50",
                "What is the square root of 144?",
                "Compute 2^10",
                "What is sin(pi/4)?",
            ]
        )
    
    def _eval_node(self, node: ast.AST) -> float:
        """Recursively evaluate AST node."""
        if isinstance(node, ast.Constant):
            # Modern Python uses ast.Constant for all literals
            if isinstance(node.value, (int, float)):
                return float(node.value)
            raise ValueError(f"Unsupported constant type: {type(node.value)}")
        elif isinstance(node, ast.Num):
            # Legacy support for older Python versions
            return float(node.n)  # type: ignore
        elif isinstance(node, ast.Name):
            if node.id in self.CONSTANTS:
                return self.CONSTANTS[node.id]
            raise ValueError(f"Unknown constant: {node.id}")
        elif isinstance(node, ast.BinOp):
            op_type = type(node.op)
            if op_type not in self.OPERATORS:
                raise ValueError(f"Unsupported operator: {op_type.__name__}")
            left = self._eval_node(node.left)
            right = self._eval_node(node.right)
            return self.OPERATORS[op_type](left, right)
        elif isinstance(node, ast.UnaryOp):
            op_type = type(node.op)
            if op_type not in self.OPERATORS:
                raise ValueError(f"Unsupported unary operator: {op_type.__name__}")
            operand = self._eval_node(node.operand)
            return self.OPERATORS[op_type](operand)
        elif isinstance(node, ast.Call):
            if not isinstance(node.func, ast.Name):
                raise ValueError("Only simple function calls are supported")
            func_name = node.func.id
            if func_name not in self.FUNCTIONS:
                raise ValueError(f"Unknown function: {func_name}")
            args = [self._eval_node(arg) for arg in node.args]
            return self.FUNCTIONS[func_name](*args)
        else:
            raise ValueError(f"Unsupported expression type: {type(node).__name__}")
    
    async def execute(self, **kwargs) -> ToolResult:
        """Execute calculator with given expression."""
        expression = kwargs.get("expression", "")
        if not expression:
            return ToolResult(
                success=False,
                error="Missing required parameter: expression"
            )
        try:
            # Parse the expression
            expression = expression.strip()
            tree = ast.parse(expression, mode='eval')
            
            # Evaluate safely
            result = self._eval_node(tree.body)
            
            return ToolResult(
                success=True,
                data=result,
                metadata={
                    "expression": expression,
                    "result_type": type(result).__name__
                }
            )
        except ZeroDivisionError:
            return ToolResult(
                success=False,
                error="Division by zero",
                metadata={"expression": expression}
            )
        except ValueError as e:
            return ToolResult(
                success=False,
                error=f"Invalid expression: {str(e)}",
                metadata={"expression": expression}
            )
        except Exception as e:
            return ToolResult(
                success=False,
                error=f"Calculation error: {str(e)}",
                metadata={"expression": expression}
            )

