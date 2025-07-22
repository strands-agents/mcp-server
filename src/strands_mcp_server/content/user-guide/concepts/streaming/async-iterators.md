# Async Iterators for Streaming

Strands Agents SDK provides support for asynchronous iterators through the [`stream_async`](../../../api-reference/agent.md#strands.agent.agent.Agent.stream_async) method, enabling real-time streaming of agent responses in asynchronous environments like web servers, APIs, and other async applications.

> **Note**: If you want to use callbacks instead of async iterators, take a look at the [callback handlers](./callback-handlers.md) documentation. Async iterators are ideal for asynchronous frameworks like FastAPI, aiohttp, or Django Channels. For these environments, Strands Agents SDK offers the `stream_async` method which returns an asynchronous iterator.

## Basic Usage

```python
import asyncio
from strands import Agent
from strands_tools import calculator

# Initialize our agent without a callback handler
agent = Agent(
    tools=[calculator],
    callback_handler=None
)

# Async function that iterators over streamed agent events
async def process_streaming_response():
    agent_stream = agent.stream_async("Calculate 2+2")
    async for event in agent_stream:
        print(event)

# Run the agent
asyncio.run(process_streaming_response())
```

> Note, Strands also offers an [`invoke_async`](../../../api-reference/agent.md#strands.agent.agent.Agent.invoke_async) method for non-iterative async invocations.

## Event Types

The async iterator yields the same event types as [callback handlers](callback-handlers.md#callback-handler-events), including:

### Text Generation Events

- `data`: Text chunk from the model's output
- `delta`: Raw delta content from the model

### Tool Events

- `current_tool_use`: Information about the current tool being used, including:
    - `toolUseId`: Unique ID for this tool use
    - `name`: Name of the tool
    - `input`: Tool input parameters (accumulated as streaming occurs)

### Lifecycle Events

- `init_event_loop`: True when the event loop is initializing
- `start_event_loop`: True when the event loop is starting
- `start`: True when a new cycle starts
- `message`: Present when a new message is created
- `event`: Raw event from the model stream
- `force_stop`: True if the event loop was forced to stop
- `force_stop_reason`: Reason for forced stop
- `result`: The final [`AgentResult`](../../../api-reference/agent.md#strands.agent.agent_result.AgentResult)

### Reasoning Events

- `reasoning`: True for reasoning events
- `reasoningText`: Text from reasoning process
- `reasoning_signature`: Signature from reasoning process

## FastAPI Example

Here's how to integrate `stream_async` with FastAPI to create a streaming endpoint:

```python
from fastapi import FastAPI, HTTPException
from fastapi.responses import StreamingResponse
from pydantic import BaseModel
from strands import Agent
from strands_tools import calculator, http_request

app = FastAPI()

class PromptRequest(BaseModel):
    prompt: str

@app.post("/stream")
async def stream_response(request: PromptRequest):
    async def generate():
        agent = Agent(
            tools=[calculator, http_request],
            callback_handler=None
        )

        try:
            async for event in agent.stream_async(request.prompt):
                if "data" in event:
                    # Only stream text chunks to the client
                    yield event["data"]
        except Exception as e:
            yield f"Error: {str(e)}"

    return StreamingResponse(
        generate(),
        media_type="text/plain"
    )
```
