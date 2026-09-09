"""
Dynamic tool registration and execution dispatcher.

Leverages LangChain's `StructuredTool` to automatically infer JSON schemas 
from Python type hints and docstrings. This eliminates boilerplate schema 
definitions and ensures our LLM bindings are always perfectly synced with 
the underlying Python signatures.
"""

from __future__ import annotations

import logging
from typing import Any, Callable

from langchain_core.tools import StructuredTool

logger = logging.getLogger(__name__)


class ToolRegistry:
    """
    Central registry for all agent tools.

    Usage:
        registry = ToolRegistry()
        registry.register("search_flights", search_flights)
        result = registry.execute("search_flights", {"origin": "Ahmedabad", ...})
    """

    def __init__(self) -> None:
        self._tools: dict[str, Callable] = {}
        self._lc_tools: dict[str, StructuredTool] = {}

    def register(self, name: str, func: Callable) -> None:
        """Register a tool — schema is auto-generated from type hints & docstring."""
        self._tools[name] = func
        self._lc_tools[name] = StructuredTool.from_function(func=func, name=name)
        logger.info("Registered tool: %s", name)

    @property
    def tool_names(self) -> list[str]:
        return list(self._tools.keys())

    def get_langchain_tools(self) -> list[StructuredTool]:
        """Return LangChain StructuredTool objects for binding to an LLM."""
        return list(self._lc_tools.values())

    def execute(self, name: str, arguments: dict[str, Any]) -> dict[str, Any]:
        """Execute a registered tool. Returns result dict or error dict."""
        if name not in self._tools:
            logger.error("Unknown tool called: %s", name)
            return {"error": f"Unknown tool: {name}", "available_tools": self.tool_names}

        try:
            result = self._tools[name](**arguments)
            logger.info("Tool %s executed successfully", name)
            return result
        except Exception as e:
            logger.exception("Tool %s execution failed", name)
            return {"error": f"Tool execution failed: {str(e)}", "tool": name}
