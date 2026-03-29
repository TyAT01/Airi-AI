import logging
from typing import List, Dict, Any, Optional, Callable, Awaitable
from pydantic import BaseModel, Field

logger = logging.getLogger(__name__)

class McpToolDescriptor(BaseModel):
    server_name: str = Field(..., alias="serverName")
    name: str
    tool_name: str = Field(..., alias="toolName")
    description: Optional[str] = None
    input_schema: Dict[str, Any] = Field(..., alias="inputSchema")

    class Config:
        populate_by_name = True

class McpCallToolPayload(BaseModel):
    name: str
    arguments: Optional[Dict[str, Any]] = None

class McpCallToolResult(BaseModel):
    content: Optional[List[Dict[str, Any]]] = None
    structured_content: Optional[Dict[str, Any]] = Field(None, alias="structuredContent")
    tool_result: Optional[Any] = Field(None, alias="toolResult")
    is_error: bool = Field(False, alias="isError")

    class Config:
        populate_by_name = True

class McpToolBridge:
    """
    Bridge for MCP tool interactions.
    Mirror of packages/stage-ui/src/stores/mcp-tool-bridge.ts.
    """
    def __init__(self):
        self._list_tools_handler: Optional[Callable[[], Awaitable[List[McpToolDescriptor]]]] = None
        self._call_tool_handler: Optional[Callable[[McpCallToolPayload], Awaitable[McpCallToolResult]]] = None

    def set_handlers(
        self,
        list_tools: Callable[[], Awaitable[List[McpToolDescriptor]]],
        call_tool: Callable[[McpCallToolPayload], Awaitable[McpCallToolResult]]
    ):
        self._list_tools_handler = list_tools
        self._call_tool_handler = call_tool

    async def list_tools(self) -> List[McpToolDescriptor]:
        if not self._list_tools_handler:
            raise RuntimeError("MCP tool bridge is not available in this runtime (list_tools handler not set)")
        return await self._list_tools_handler()

    async def call_tool(self, payload: McpCallToolPayload) -> McpCallToolResult:
        if not self._call_tool_handler:
            raise RuntimeError("MCP tool bridge is not available in this runtime (call_tool handler not set)")
        return await self._call_tool_handler(payload)

_bridge: Optional[McpToolBridge] = None

def get_mcp_tool_bridge() -> McpToolBridge:
    """
    Singleton accessor for the MCP tool bridge.
    """
    global _bridge
    if _bridge is None:
        _bridge = McpToolBridge()
    return _bridge

def set_mcp_tool_bridge(next_bridge: McpToolBridge):
    """
    Sets the MCP tool bridge instance.
    """
    global _bridge
    _bridge = next_bridge

def clear_mcp_tool_bridge():
    """
    Clears the MCP tool bridge instance.
    """
    global _bridge
    _bridge = None
