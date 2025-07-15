# Model Context Protocol (MCP) in Strands

The Model Context Protocol (MCP) is an open protocol that standardizes how applications provide context to Large Language Models (LLMs). Strands integrates with MCP to enable agents to access external tools and services through a standardized interface.

## What is MCP?

MCP establishes a common protocol for communication between LLM-powered applications and context providers. In Strands, MCP enables agents to:

1. Connect to external MCP servers
2. Discover available tools
3. Call these tools when needed
4. Process the results returned by tools

MCP allows for modular, extensible agent architectures by separating tool implementation from the agent core, enabling tools to be deployed and scaled independently.

## MCP Server Connection Options

Strands provides several ways to connect to MCP servers:

### 1. Standard I/O (stdio)

For command-line tools and local processes that implement the MCP protocol:

```python
from mcp import stdio_client, StdioServerParameters
from strands import Agent
from strands.tools.mcp import MCPClient

# Connect to an MCP server using stdio transport
stdio_mcp_client = MCPClient(lambda: stdio_client(
    StdioServerParameters(
        command="uvx", 
        args=["awslabs.aws-documentation-mcp-server@latest"]
    )
))

# Create an agent with MCP tools
with stdio_mcp_client:
    tools = stdio_mcp_client.list_tools_sync()
    agent = Agent(tools=tools)
```

### 2. Server-Sent Events (SSE)

For HTTP-based MCP servers that use Server-Sent Events transport:

```python
from mcp.client.sse import sse_client
from strands import Agent
from strands.tools.mcp import MCPClient

# Connect to an MCP server using SSE transport
sse_mcp_client = MCPClient(lambda: sse_client("http://localhost:8000/sse"))

# Create an agent with MCP tools
with sse_mcp_client:
    tools = sse_mcp_client.list_tools_sync()
    agent = Agent(tools=tools)
```

### 3. Streamable HTTP

For HTTP-based MCP servers that use Streamable-HTTP Events transport:

```python
from mcp.client.streamable_http import streamablehttp_client
from strands import Agent
from strands.tools.mcp.mcp_client import MCPClient

streamable_http_mcp_client = MCPClient(lambda: streamablehttp_client("http://localhost:8000/mcp"))

# Create an agent with MCP tools
with streamable_http_mcp_client:
    tools = streamable_http_mcp_client.list_tools_sync()
    agent = Agent(tools=tools)
```

## Context Manager Requirement

When working with MCP tools in Strands, all agent operations must be performed within the MCP client's context manager (using a `with` statement). This requirement ensures that the MCP session remains active and connected while the agent is using the tools.

```python
# Correct usage:
with mcp_client:
    agent = Agent(tools=mcp_client.list_tools_sync())
    response = agent("Your prompt")  # Works correctly

# Incorrect usage:
with mcp_client:
    agent = Agent(tools=mcp_client.list_tools_sync())
response = agent("Your prompt")  # Will fail with MCPClientInitializationError
```

## Using Multiple MCP Servers

You can connect to multiple MCP servers simultaneously and combine their tools:

```python
from mcp import stdio_client, StdioServerParameters
from mcp.client.sse import sse_client
from strands import Agent
from strands.tools.mcp import MCPClient

# Connect to multiple MCP servers
sse_mcp_client = MCPClient(lambda: sse_client("http://localhost:8000/sse"))
stdio_mcp_client = MCPClient(lambda: stdio_client(StdioServerParameters(command="python", args=["path/to/mcp_server.py"])))

# Use both servers together
with sse_mcp_client, stdio_mcp_client:
    # Combine tools from both servers
    tools = sse_mcp_client.list_tools_sync() + stdio_mcp_client.list_tools_sync()
    
    # Create an agent with all tools
    agent = Agent(tools=tools)
```

## MCP Tool Response Format

MCP tools can return responses in two primary content formats:

1. **Text Content**: Simple text responses
2. **Image Content**: Binary image data with associated MIME type

Strands automatically maps these MCP content types to the appropriate `ToolResultContent` format used by the agent framework.

The tool result structure follows this format:

```python
{
    "status": str,          # "success" or "error" based on the MCP call result
    "toolUseId": str,       # The ID of the tool use request
    "content": List[dict]   # A list of content items (text or image)
}
```

## Implementing an MCP Server

You can create your own MCP server to extend agent capabilities:

```python
from mcp.server import FastMCP

# Create an MCP server
mcp = FastMCP("Calculator Server")

# Define a tool
@mcp.tool(description="Calculator tool which performs calculations")
def calculator(x: int, y: int) -> int:
    return x + y

# Run the server with SSE transport
mcp.run(transport="sse")
```

## Direct Tool Invocation

While tools are typically invoked by the agent based on user requests, you can also call MCP tools directly:

```python
# Directly invoke an MCP tool
result = mcp_client.call_tool_sync(
    tool_use_id="tool-123",
    name="calculator",
    arguments={"x": 10, "y": 20}
)

# Process the result
print(f"Calculation result: {result['content'][0]['text']}")
```

## Troubleshooting Common MCP Issues

### Connection Failures

If you're experiencing connection problems:
- Ensure the MCP server is running and accessible
- Verify network connectivity and firewall settings
- Check that the URL or command is correct and properly formatted

### Tool Discovery Issues

When tools aren't being discovered:
- Confirm the MCP server has properly implemented the list_tools method
- Verify that tools are correctly registered with the server

### Tool Execution Errors

For errors during tool execution:
- Verify that all tool arguments match the expected schema
- Check server logs for detailed error information
- Ensure the MCP client is within a valid context manager block

## Best Practices

1. **Tool Descriptions**: Provide clear descriptions for your tools to help the agent understand when and how to use them

2. **Parameter Types**: Use appropriate parameter types and descriptions to ensure correct tool usage

3. **Error Handling**: Return informative error messages when tools fail to execute properly

4. **Security Considerations**: Consider security implications when exposing tools via MCP, especially for network-accessible servers

5. **Connection Management**: Always use context managers (`with` statements) to ensure proper cleanup of MCP connections

6. **Timeouts**: Set appropriate timeouts for tool calls to prevent hanging on long-running operations

7. **Content Types**: Use the appropriate content type for tool responses (text or image) based on the tool's purpose

8. **Tool Organization**: Group related tools on the same MCP server for better organization and performance