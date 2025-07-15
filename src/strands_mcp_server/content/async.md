# Asynchronous Programming in Strands

Strands Agents SDK provides comprehensive support for asynchronous programming using Python's `asyncio` framework. This allows you to build non-blocking agent applications that can handle multiple concurrent operations efficiently.

## Asynchronous Agent Operations

The Strands Agents SDK provides async versions of all major agent operations:

### Basic Agent Invocation

The most common async operation is invoking an agent:

```python
import asyncio
from strands import Agent

async def main():
    agent = Agent()
    
    # Async agent invocation
    response = await agent.invoke_async("What's the capital of France?")
    print(response)

# Run the async function
asyncio.run(main())
```

### Streaming Responses

For applications that need to process agent responses incrementally as they arrive:

```python
import asyncio
from strands import Agent

async def main():
    agent = Agent()
    
    # Process streaming responses
    async for chunk in agent.stream_async("Write a short story about a robot"):
        if "contentBlockDelta" in chunk and "text" in chunk["contentBlockDelta"]["delta"]:
            text = chunk["contentBlockDelta"]["delta"]["text"]
            print(text, end="", flush=True)

asyncio.run(main())
```

### Structured Output

Get type-safe, validated responses asynchronously:

```python
import asyncio
from pydantic import BaseModel
from strands import Agent

class PersonInfo(BaseModel):
    name: str
    age: int
    occupation: str

async def main():
    agent = Agent()
    
    # Get structured output asynchronously
    person = await agent.structured_output_async(
        PersonInfo,
        "Extract info: John Smith is a 30-year-old software engineer"
    )
    
    print(f"Name: {person.name}")
    print(f"Age: {person.age}")
    print(f"Occupation: {person.occupation}")

asyncio.run(main())
```

## Async Tools

Strands also supports asynchronous tools, which are executed concurrently when called:

### Async Function Tools

Create asynchronous tools using the `@tool` decorator:

```python
import asyncio
from strands import Agent, tool

@tool
async def fetch_weather(city: str) -> str:
    """Get current weather for a city.
    
    Args:
        city: Name of the city
    """
    # Simulate API call with delay
    await asyncio.sleep(2)
    return f"Weather in {city}: Sunny, 72°F"

async def main():
    agent = Agent(tools=[fetch_weather])
    response = await agent.invoke_async("What's the weather in Seattle?")
    print(response)

asyncio.run(main())
```

### Async Module Tools

Module-based tools can also be implemented asynchronously:

```python
# weather.py
import asyncio

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

async def weather(tool, **kwargs):
    """Async implementation of the weather tool."""
    location = tool["input"]["location"]
    
    # Simulate API call
    await asyncio.sleep(1)
    weather_info = f"Weather for {location}: Sunny, 72°F"
    
    return {
        "toolUseId": tool["toolUseId"],
        "status": "success",
        "content": [{"text": weather_info}]
    }
```

## Concurrent Tool Execution

When multiple async tools are invoked within the same model turn, Strands executes them concurrently:

```python
import asyncio
from strands import Agent, tool

@tool
async def fetch_weather(city: str) -> str:
    """Get weather for a city."""
    await asyncio.sleep(2)  # 2 second delay
    return f"Weather in {city}: Sunny, 72°F"

@tool
async def fetch_news(topic: str) -> str:
    """Get latest news about a topic."""
    await asyncio.sleep(3)  # 3 second delay
    return f"Latest {topic} news: New developments announced"

async def main():
    agent = Agent(tools=[fetch_weather, fetch_news])
    
    # This will execute both tools concurrently
    response = await agent.invoke_async(
        "Get me the weather in Seattle and the latest tech news"
    )
    print(response)

asyncio.run(main())
```

In this example, both tools will execute in parallel rather than sequentially, reducing the total wait time to about 3 seconds instead of 5 seconds.

## Multi-Agent Async Operations

Asynchronous programming is particularly valuable for multi-agent patterns:

### Async Graph Execution

```python
import asyncio
from strands import Agent
from strands.multiagent import GraphBuilder

async def main():
    # Create agents
    researcher = Agent(name="researcher")
    analyst = Agent(name="analyst")
    
    # Build graph
    builder = GraphBuilder()
    builder.add_node(researcher, "research")
    builder.add_node(analyst, "analysis")
    builder.add_edge("research", "analysis")
    
    graph = builder.build()
    
    # Execute graph asynchronously
    result = await graph.invoke_async("Research AI advancements")
    print(result)

asyncio.run(main())
```

### Async Swarm Execution

```python
import asyncio
from strands import Agent
from strands.multiagent import Swarm

async def main():
    # Create specialized agents
    researcher = Agent(name="researcher")
    analyst = Agent(name="analyst")
    writer = Agent(name="writer")
    
    # Create swarm
    swarm = Swarm([researcher, analyst, writer])
    
    # Execute swarm asynchronously
    result = await swarm.invoke_async("Research and write about quantum computing")
    print(result)

asyncio.run(main())
```
