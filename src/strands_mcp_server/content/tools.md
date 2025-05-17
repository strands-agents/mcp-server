Tools are the primary mechanism for extending agent capabilities, enabling them to perform actions beyond simple text generation. Tools allow agents to interact with external systems, access data, and manipulate their environment.

## Adding Tools to Agents

Tools are passed to agents during initialization or at runtime, making them available for use throughout the agent's lifecycle. Once loaded, the agent can use these tools in response to user requests:

```python
from strands import Agent
from strands_tools import calculator, file_read, shell

# Add tools to our agent
agent = Agent(
    tools=[calculator, file_read, shell]
)

# Agent will automatically determine when to use the calculator tool
agent("What is 42 ^ 9")

# Agent will use the shell and file reader tool when appropriate
agent("Show me the contents of a single file in this directory")
```

## Building & Loading Tools

### 1. Python Tools

Build your own Python tools using the Strands SDK's tool interfaces.

Function decorated tools can be placed anywhere in your codebase and imported in to your agent's list of tools. Define any Python function as a tool by using the [`@tool`](../../../api-reference/tools.md#strands.tools.decorator.tool) decorator.

```python
from strands import Agent, tool

@tool
def get_user_location() -> str:
    """Get the user's location
    """

    # Implement user location lookup logic here
    return "Seattle, USA"

@tool
def weather(location: str) -> str:
    """Get weather information for a location

    Args:
        location: City or location name
    """

    # Implement weather lookup logic here
    return f"Weather for {location}: Sunny, 72°F"

agent = Agent(tools=[get_user_location, weather])

# Use the agent with the custom tools
agent("What is the weather like in my location?")
```

### 2. Model Context Protocol (MCP) Tools

The [Model Context Protocol (MCP)](https://modelcontextprotocol.io) provides a standardized way to expose and consume tools across different systems. This approach is ideal for creating reusable tool collections that can be shared across multiple agents or applications.

```python
from mcp import stdio_client, StdioServerParameters
from strands import Agent
from strands.tools.mcp import MCPClient

# Connect to an MCP server using stdio transport
stdio_mcp_client = MCPClient(lambda: stdio_client(
    StdioServerParameters(command="uvx", args=["awslabs.aws-documentation-mcp-server@latest"])
))

# Create an agent with MCP tools
with stdio_mcp_client:
    # Get the tools from the MCP server
    tools = stdio_mcp_client.list_tools_sync()

    # Create an agent with these tools
    agent = Agent(tools=tools)
```

### 3. Example Built-in Tools

Strands offers an optional example tools package `strands-agents-tools` which includes pre-built tools to get started quickly experimenting with agents and tools during development.

Install the `strands-agents-tools` package by running:

```bash
pip install strands-agents-tools
```

## Available Built-In Strands Tools

#### RAG & Memory

- `retrieve`: Semantically retrieve data from Amazon Bedrock Knowledge Bases for RAG, memory, and other purposes

#### File Operations

- `editor`: Advanced file editing operations
- `file_read`: Read and parse files
- `file_write`: Create and modify files

#### Shell & System

- `environment`: Manage environment variables
- `shell`: Execute shell commands

#### Code Interpretation

- `python_repl`: Run Python code

#### Web & Network

- `http_request`: Make API calls, fetch web data, and call local HTTP servers

#### Multi-modal

- `image_reader`: Process and analyze images
- `generate_image`: Create AI generated images with Amazon Bedrock
- `nova_reels`: Create AI generated videos with Nova Reels on Amazon Bedrock

#### AWS Services

- `use_aws`: Interact with AWS services

#### Utilities

- `calculator`: Perform mathematical operations
- `current_time`: Get the current date and time
- `load_tool`: Dynamically load more tools at runtime

#### Agents & Workflows

- `agent_graph`: Create and manage graphs of agents
- `journal`: Create structured tasks and logs for agents to manage and work from
- `swarm`: Coordinate multiple AI agents in a swarm / network of agents
- `stop`: Force stop the agent event loop
- `think`: Perform deep thinking by creating parallel branches of agentic reasoning
- `use_llm`: Run a new AI event loop with custom prompts
- `workflow`: Orchestrate sequenced workflows
