# Model Context Protocol (MCP) Tools

The [Model Context Protocol (MCP)](https://modelcontextprotocol.io) is an open protocol that standardizes how applications provide context to Large Language Models (LLMs). Strands Agents integrates with MCP to extend agent capabilities through external tools and services.

MCP enables communication between agents and MCP servers that provide additional tools. Strands includes built-in support for connecting to MCP servers and using their tools.

When working with MCP tools in Strands, all agent operations must be performed within the MCP client's context manager (using a with statement). 
This requirement ensures that the MCP session remains active and connected while the agent is using the tools. 
If you attempt to use an agent or its MCP tools outside of this context, you'll encounter errors because the MCP session will have closed.


## MCP Server Connection Options

Strands provides several ways to connect to MCP servers:

### 1. Standard I/O (stdio)

For command-line tools and local processes that implement the MCP protocol:

```python
from mcp import stdio_client, StdioServerParameters
from strands import Agent
from strands.tools.mcp import MCPClient

# Connect to an MCP server using stdio transport
# Note: uvx command syntax differs by platform

# For macOS/Linux:
stdio_mcp_client = MCPClient(lambda: stdio_client(
    StdioServerParameters(
        command="uvx", 
        args=["awslabs.aws-documentation-mcp-server@latest"]
    )
))

# For Windows:
stdio_mcp_client = MCPClient(lambda: stdio_client(
    StdioServerParameters(
        command="uvx", 
        args=[
            "--from", 
            "awslabs.aws-documentation-mcp-server@latest", 
            "awslabs.aws-documentation-mcp-server.exe"
        ]
    )
))

# Create an agent with MCP tools
with stdio_mcp_client:
    # Get the tools from the MCP server
    tools = stdio_mcp_client.list_tools_sync()
    
    # Create an agent with these tools
    agent = Agent(tools=tools)
    agent("What is AWS Lambda?")
```

### 2. Streamable HTTP

For HTTP-based MCP servers that use Streamable-HTTP Events transport:

```python
from mcp.client.streamable_http import streamablehttp_client
from strands import Agent
from strands.tools.mcp.mcp_client import MCPClient

streamable_http_mcp_client = MCPClient(lambda: streamablehttp_client("http://localhost:8000/mcp"))

# Create an agent with MCP tools
with streamable_http_mcp_client:
    # Get the tools from the MCP server
    tools = streamable_http_mcp_client.list_tools_sync()
    
    # Create an agent with these tools
    agent = Agent(tools=tools)
```

### 3. Server-Sent Events (SSE)

For HTTP-based MCP servers that use Server-Sent Events transport:

```python
from mcp.client.sse import sse_client
from strands import Agent
from strands.tools.mcp import MCPClient

# Connect to an MCP server using SSE transport
sse_mcp_client = MCPClient(lambda: sse_client("http://localhost:8000/sse"))

# Create an agent with MCP tools
with sse_mcp_client:
    # Get the tools from the MCP server
    tools = sse_mcp_client.list_tools_sync()
    
    # Create an agent with these tools
    agent = Agent(tools=tools)
```

### 4. Custom Transport with MCPClient

For advanced use cases, you can implement a custom transport mechanism by using the underlying `MCPClient` class directly. This requires implementing the `MCPTransport` protocol, which is a tuple of read and write streams:

```python
from typing import Callable
from strands import Agent
from strands.tools.mcp.mcp_client import MCPClient
from strands.tools.mcp.mcp_types import MCPTransport

# Define a function that returns your custom transport
def custom_transport_factory() -> MCPTransport:
    # Implement your custom transport mechanism
    # Must return a tuple of (read_stream, write_stream)
    # Both must implement the AsyncIterable and AsyncIterator protocols
    ...
    return read_stream, write_stream

# Create an MCPClient with your custom transport
custom_mcp_client = MCPClient(transport_callable=custom_transport_factory)

# Use the server with context manager
with custom_mcp_client:
    # Get the tools from the MCP server
    tools = custom_mcp_client.list_tools_sync()
    
    # Create an agent with these tools
    agent = Agent(tools=tools)
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

Strands automatically maps these MCP content types to the appropriate `ToolResultContent` format used by the agent framework:

```python
def _map_mcp_content_to_tool_result_content(content):
    if isinstance(content, MCPTextContent):
        return {"text": content.text}
    elif isinstance(content, MCPImageContent):
        return {
            "image": {
                "format": map_mime_type_to_image_format(content.mimeType),
                "source": {"bytes": base64.b64decode(content.data)},
            }
        }
    else:
        # Unsupported content type
        return None
```

### Tool Result Structure

When an MCP tool is called, the result is converted to a `ToolResult` with the following structure:

```python
{
    "status": str,          # "success" or "error" based on the MCP call result
    "toolUseId": str,       # The ID of the tool use request
    "content": List[dict]   # A list of content items (text or image)
}
```

## Implementing an MCP Server

You can create your own MCP server to extend agent capabilities. Here's a simple example of a calculator MCP server:

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

### MCP Server Implementation Details

The MCP server connection in Strands is managed by the `MCPClient` class, which:

1. Establishes a connection to the MCP server using the provided transport
2. Initializes the MCP session
3. Discovers available tools
4. Handles tool invocation and result conversion
5. Manages the connection lifecycle

The connection runs in a background thread to avoid blocking the main application thread while maintaining communication with the MCP service.

## Advanced Usage

### Direct Tool Invocation

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

## Best Practices

- **Tool Descriptions**: Provide clear descriptions for your tools to help the agent understand when and how to use them
- **Parameter Types**: Use appropriate parameter types and descriptions to ensure correct tool usage
- **Error Handling**: Return informative error messages when tools fail to execute properly
- **Security**: Consider security implications when exposing tools via MCP, especially for network-accessible servers
- **Connection Management**: Always use context managers (`with` statements) to ensure proper cleanup of MCP connections
- **Timeouts**: Set appropriate timeouts for tool calls to prevent hanging on long-running operations

## Troubleshooting

### **MCPClientInitializationError**

AgentTools relying on an MCP connection must always be used within a context manager. When you create or use an agent outside a with statement, operations will fail because the MCP session is automatically closed once you exit the context manager block. The MCP connection must remain active throughout the agent's operations to maintain access to the tools and services it provides.

Correct usage:
```python
with mcp_client:
    agent = Agent(tools=mcp_client.list_tools_sync())
    response = agent("Your prompt")  # Works
```

Incorrect usage:
```python
with mcp_client:
    agent = Agent(tools=mcp_client.list_tools_sync())
response = agent("Your prompt")  # Will fail with MCPClientInitializationError
```
### **Connection Failures**
   Connection failures occur when there are problems establishing a connection with the MCP server. To resolve these issues, first ensure that the MCP server is running and accessible from your network environment. You should also verify your network connectivity and check if any firewall settings are blocking the connection. Additionally, make sure that the URL or command you're using to connect to the server is correct and properly formatted.

### **Tool Discovery Issues**
   When encountering tool discovery problems, first confirm that the MCP server has properly implemented the list_tools method as this is essential for tool discovery to function. It's also important to verify that all tools have been correctly registered with the server.

### **Tool Execution Errors**
   Tool execution errors can arise during the actual operation of MCP tools. To resolve these errors, verify that all tool arguments being passed match the expected schema for that particular tool. When errors occur, consulting the server logs can provide detailed information about what went wrong during the execution process.