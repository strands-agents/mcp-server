# Python Tools

There are two approaches to defining python-based tools in Strands:

* **Python functions with the [`@tool`](../../../api-reference/tools.md#strands.tools.decorator.tool) decorator**: Transform regular Python functions into tools by adding a simple decorator. This approach leverages Python's docstrings and type hints to automatically generate tool specifications.

* **Python modules following a specific format**: Define tools by creating Python modules that contain a tool specification and a matching function. This approach gives you more control over the tool's definition and is useful for dependency-free implementations of tools.

## Python Tool Decorators

The [`@tool`](../../../api-reference/tools.md#strands.tools.decorator.tool) decorator provides a straightforward way to transform regular Python functions into tools that agents can use.

### Basic Example

Here's a simple example of a function decorated as a tool:

```python
from strands import tool

@tool
def weather_forecast(city: str, days: int = 3) -> str:
    """Get weather forecast for a city.

    Args:
        city: The name of the city
        days: Number of days for the forecast
    """
    return f"Weather forecast for {city} for the next {days} days..."
```

The decorator extracts information from your function's docstring to create the tool specification. The first paragraph becomes the tool's description, and the "Args" section provides parameter descriptions. These are combined with the function's type hints to create a complete tool specification.

### Loading Function-Decorated tools

To use function-based tool, simply pass the function to the agent:

```python
agent = Agent(
    tools=[weather_forecast]
)
```

### Overriding Tool Name and Description

You can also optionally override the tool name or description by providing them as arguments to the decorator:

```python
@tool(name="get_weather", description="Retrieves weather forecast for a specified location")
def weather_forecast(city: str, days: int = 3) -> str:
    """Implementation function for weather forecasting.

    Args:
        city: The name of the city
        days: Number of days for the forecast
    """
    # Implementation
    return f"Weather forecast for {city} for the next {days} days..."
```

### Dictionary Return Type

By default, your function's return value is automatically formatted as a text response. However, if you need more control over the response format, you can return a dictionary with a specific structure:

```python
@tool
def fetch_data(source_id: str) -> dict:
    """Fetch data from a specified source.

    Args:
        source_id: Identifier for the data source
    """
    try:
        data = some_other_function(source_id)
        return {
            "status": "success",
            "content": [ {
                "json": data,
            }]
        }
    except Exception as e:
        return {
            "status": "error",
             "content": [
                {"text": f"Error:{e}"}
            ]
        }
```

For more details, see the [Tool Response Format](#tool-response-format) section below.

### Async Invocation

Decorated tools may also be defined async. Strands will invoke all async tools concurrently.

```Python
import asyncio
from strands import Agent, tool


@tool
async def call_api() -> str:
    """Call API asynchronously."""

    await asyncio.sleep(5)  # simulated api call
    return "API result"


async def async_example():
    agent = Agent(tools=[call_api])
    await agent.invoke_async("Can you call my API?")


asyncio.run(async_example())
```

## Python Modules as Tools

An alternative approach is to define a tool as a Python module with a specific structure. This enables creating tools that don't depend on the SDK directly.

A Python module tool requires two key components:

1. A `TOOL_SPEC` variable that defines the tool's name, description, and input schema
2. A function with the same name as specified in the tool spec that implements the tool's functionality

### Basic Example

Here's how you would implement the same weather forecast tool as a module:

```python
# weather_forecast.py

# 1. Tool Specification
TOOL_SPEC = {
    "name": "weather_forecast",
    "description": "Get weather forecast for a city.",
    "inputSchema": {
        "json": {
            "type": "object",
            "properties": {
                "city": {
                    "type": "string",
                    "description": "The name of the city"
                },
                "days": {
                    "type": "integer",
                    "description": "Number of days for the forecast",
                    "default": 3
                }
            },
            "required": ["city"]
        }
    }
}

# 2. Tool Function
def weather_forecast(tool, **kwargs: Any):
    # Extract tool parameters
    tool_use_id = tool["toolUseId"]
    tool_input = tool["input"]

    # Get parameter values
    city = tool_input.get("city", "")
    days = tool_input.get("days", 3)

    # Tool implementation
    result = f"Weather forecast for {city} for the next {days} days..."

    # Return structured response
    return {
        "toolUseId": tool_use_id,
        "status": "success",
        "content": [{"text": result}]
    }
```

### Loading Module Tools

To use a module-based tool, import the module and pass it to the agent:

```python
from strands import Agent
import weather_forecast

agent = Agent(
    tools=[weather_forecast]
)
```

Alternatively, you can load a tool by passing in a path:

```python
from strands import Agent

agent = Agent(
    tools=["./weather_forecast.py"]
)
```

### Async Invocation

Similar to decorated tools, users may define their module tools async.

```Python
TOOL_SPEC = {
    "name": "call_api",
    "description": "Call my API asynchronously.",
    "inputSchema": {
        "json": {
            "type": "object",
            "properties": {},
            "required": []
        }
    }
}

async def call_api(tool, **kwargs):
    await asyncio.sleep(5)  # simulated api call
    result = "API result"

    return {
        "toolUseId": tool["toolUseId"],
        "status": "success",
        "content": [{"text": result}],
    }
```

### Tool Response Format

Tools can return responses in various formats using the [`ToolResult`](../../../api-reference/types.md#strands.types.tools.ToolResult) structure. This structure provides flexibility for returning different types of content while maintaining a consistent interface.

#### ToolResult Structure

The [`ToolResult`](../../../api-reference/types.md#strands.types.tools.ToolResult) dictionary has the following structure:

```python
{
    "toolUseId": str,       # The ID of the tool use request (should match the incoming request).  Optional
    "status": str,          # Either "success" or "error"
    "content": List[dict]   # A list of content items with different possible formats
}
```

#### Content Types

The `content` field is a list of dictionaries, where each dictionary can contain one of the following keys:

- `text`: A string containing text output
- `json`: Any JSON-serializable data structure
- `image`: An image object with format and source
- `document`: A document object with format, name, and source

#### Success Response Example

```python
{
    "toolUseId": "tool-123",
    "status": "success",
    "content": [
        {"text": "Operation completed successfully"},
        {"json": {"results": [1, 2, 3], "total": 3}}
    ]
}
```

#### Error Response Example

```python
{
    "toolUseId": "tool-123",
    "status": "error",
    "content": [
        {"text": "Error: Unable to process request due to invalid parameters"}
    ]
}
```

#### Automatic Conversion

When using the [`@tool`](../../../api-reference/tools.md#strands.tools.decorator.tool) decorator, your function's return value is automatically converted to a proper [`ToolResult`](../../../api-reference/types.md#strands.types.tools.ToolResult):

1. If you return a string or other simple value, it's wrapped as `{"text": str(result)}`
2. If you return a dictionary with the proper [`ToolResult`](../../../api-reference/types.md#strands.types.tools.ToolResult) structure, it's used directly
3. If an exception occurs, it's converted to an error response
