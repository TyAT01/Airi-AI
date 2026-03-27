import logging
from typing import List, Dict, Any, Optional, Callable, Awaitable
from pydantic import BaseModel

logger = logging.getLogger(__name__)

class McpToolDescriptor(BaseModel):
    server_name: str
    name: str
    tool_name: str
    description: Optional[str] = None
    input_schema: Dict[str, Any]

class McpCallToolPayload(BaseModel):
    name: str
    arguments: Optional[Dict[str, Any]] = None

class McpCallToolResult(BaseModel):
    content: Optional[List[Dict[str, Any]]] = None
    structured_content: Optional[Dict[str, Any]] = None
    tool_result: Optional[Any] = None
    is_error: bool = False

class McpToolBridge:
    def __init__(self):
        self._list_tools_handler: Optional[Callable[[], Awaitable[List[McpToolDescriptor]]]] = None
        self._call_tool_handler: Optional[Callable[[McpCallToolPayload], Awaitable[McpCallToolResult]]] = None

    def set_handlers(self, list_tools: Callable[[], Awaitable[List[McpToolDescriptor]]], call_tool: Callable[[McpCallToolPayload], Awaitable[McpCallToolResult]]):
        self._list_tools_handler = list_tools
        self._call_tool_handler = call_tool

    async def list_tools(self) -> List[McpToolDescriptor]:
        if not self._list_tools_handler:
            raise RuntimeError("MCP list_tools handler not set")
        return await self._list_tools_handler()

    async def call_tool(self, payload: McpCallToolPayload) -> McpCallToolResult:
        if not self._call_tool_handler:
            raise RuntimeError("MCP call_tool handler not set")
        return await self._call_tool_handler(payload)

_bridge: Optional[McpToolBridge] = None

def get_mcp_tool_bridge() -> McpToolBridge:
    global _bridge
    if _bridge is None:
        _bridge = McpToolBridge()
    return _bridge
