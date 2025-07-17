# Strands Agent Tools

Tools are the primary mechanism for extending agent capabilities in the Strands Agents SDK, enabling them to perform actions beyond simple text generation. They allow agents to interact with external systems, access data, and manipulate their environment.

## Tool Implementation Approaches

### 1. Python Function Decorator Approach

The simplest way to create a tool is using the `@tool` decorator on Python functions:

```python
from strands import Agent, tool

@tool
def weather(location: str) -> str:
    """Get weather information for a location.

    Args:
        location: City or location name
    """
    # Implement weather lookup logic
    return f"Weather for {location}: Sunny, 72°F"

agent = Agent(tools=[weather])
```

The decorator extracts information from your function's docstring for the tool description and parameters, combined with type hints to create a complete specification.

### 2. Python Modules as Tools

You can create a tool as a Python module with two key components:
- A `TOOL_SPEC` variable defining name, description, and input schema
- A function with the same name implementing the tool's functionality

```python
# weather.py
TOOL_SPEC = {
    "name": "weather",
    "description": "Get weather information for a location",
    "inputSchema": {
        "json": {
            "type": "object",
            "properties": {
                "location": {
                    "type": "string",
                    "description": "City or location name"
                }
            },
            "required": ["location"]
        }
    }
}

def weather(tool, **kwargs):
    location = tool["input"]["location"]
    return {
        "toolUseId": tool["toolUseId"],
        "status": "success",
        "content": [{"text": f"Weather for {location}: Sunny, 72°F"}]
    }
```

### 3. Model Context Protocol (MCP) Tools

The Model Context Protocol (MCP) provides a standardized way to expose and consume tools across different systems:

```python
from mcp.client.sse import sse_client
from strands import Agent
from strands.tools.mcp import MCPClient

# Connect to an MCP server using SSE transport
mcp_client = MCPClient(lambda: sse_client("http://localhost:8000/sse"))

with mcp_client:
    tools = mcp_client.list_tools_sync()
    agent = Agent(tools=tools)
    agent("Calculate the square root of 144")
```

## Adding Tools to Agents

Tools can be added to agents in several ways:

```python
# As imported functions or modules
agent = Agent(tools=[calculator, file_read, weather_module])

# As file paths
agent = Agent(tools=["/path/to/my_tool.py"])

# Auto-loading from directory
agent = Agent(load_tools_from_directory=True)  # Loads from ./tools/
```

## Invoking Tools

Tools can be invoked in two ways:

1. **Natural Language Invocation**: The agent determines when to use tools based on the request.
   ```python
   agent("Please read the file at /path/to/file.txt")
   ```

2. **Direct Method Calls**: Every tool is accessible as a method on the agent object.
   ```python
   result = agent.tool.file_read(path="/path/to/file.txt", mode="view")
   ```

## Tool Response Format

Tools can return responses using the `ToolResult` structure:

```python
{
    "toolUseId": str,     # The ID of the tool use request (optional)
    "status": str,        # Either "success" or "error"
    "content": [          # List of content items with different formats
        {"text": "Operation completed successfully"},
        {"json": {"results": [1, 2, 3]}},
        {"image": {"format": "png", "source": {"bytes": binary_data}}},
        {"document": {"format": "pdf", "name": "report.pdf", "source": {...}}}
    ]
}
```

## Built-in Community Example Tools

Strands offers a community package `strands-agents-tools` with pre-built tools for:
- 
- RAG & Memory: `retrieve`, `memory`, `mem0_memory`
- File Operations: `editor`, `file_read`, `file_write`
- Shell & System: `environment`, `shell`, `cron`
- Code Interpretation: `python_repl`
- Web & Network: `http_request`, `slack`
- Multi-modal: `generate_image`, `image_reader`, `speak`
- AWS Services: `use_aws`
- Utilities: `calculator`, `current_time`, `load_tool`
- Agents & Workflows: `agent_graph`, `journal`, `swarm`, `handoff_to_user`

## Tool Design Best Practices

1. **Clear Descriptions**: Explain purpose, usage scenarios, and limitations
2. **Detailed Parameter Documentation**: Specify types, formats, and examples
3. **Appropriate Error Handling**: Return informative error responses
4. **Security Considerations**: Validate inputs and handle sensitive operations safely
5. **Performance Optimization**: Minimize latency for frequently used tools