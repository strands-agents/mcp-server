# Callback Handlers

Callback handlers are a powerful feature of the Strands Agents SDK that allow you to intercept and process events as they happen during agent execution. This enables real-time monitoring, custom output formatting, and integration with external systems.

Callback handlers receive events in real-time as they occur during an agent's lifecycle:

- Text generation from the model
- Tool selection and execution
- Reasoning process
- Errors and completions

> **Note:** For asynchronous applications such as web servers, Strands Agents also provides [async iterators](./async-iterators.md) as an alternative to callback-based callback handlers.

## Basic Usage

The simplest way to use a callback handler is to pass a callback function to your agent:

```python
from strands import Agent
from strands_tools import calculator

def custom_callback_handler(**kwargs):
    # Process stream data
    if "data" in kwargs:
        print(f"MODEL OUTPUT: {kwargs['data']}")
    elif "current_tool_use" in kwargs and kwargs["current_tool_use"].get("name"):
        print(f"\nUSING TOOL: {kwargs['current_tool_use']['name']}")

# Create an agent with custom callback handler
agent = Agent(
    tools=[calculator],
    callback_handler=custom_callback_handler
)

agent("Calculate 2+2")
```

## Callback Handler Events

Callback handlers receive the same event types as [async iterators](./async-iterators.md#event-types), as keyword arguments:

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

## Default Callback Handler

Strands Agents provides a default callback handler that formats output to the console:

```python
from strands import Agent
from strands.handlers.callback_handler import PrintingCallbackHandler

# The default callback handler prints text and shows tool usage
agent = Agent(callback_handler=PrintingCallbackHandler())
```

If you want to disable all output, specify `None` for the callback handler:

```python
from strands import Agent

# No output will be displayed
agent = Agent(callback_handler=None)
```

## Custom Callback Handlers

Custom callback handlers enable you to have fine-grained control over what is streamed from your agents.

### Example - Print all events in the stream sequence

Custom callback handlers can be useful to debug sequences of events in the agent loop:

```python
from strands import Agent
from strands_tools import calculator

def debugger_callback_handler(**kwargs):
    # Print the values in kwargs so that we can see everything
    print(kwargs)

agent = Agent(
    tools=[calculator],
    callback_handler=debugger_callback_handler
)

agent("What is 922 + 5321")
```

This handler prints all calls to the callback handler including full event details.

### Example - Buffering Output Per Message

This handler demonstrates how to buffer text and only show it when a complete message is generated. This pattern is useful for chat interfaces where you want to show polished, complete responses:

```python
import json
from strands import Agent
from strands_tools import calculator

def message_buffer_handler(**kwargs):
    # When a new message is created from the assistant, print its content
    if "message" in kwargs and kwargs["message"].get("role") == "assistant":
        print(json.dumps(kwargs["message"], indent=2))

# Usage with an agent
agent = Agent(
    tools=[calculator],
    callback_handler=message_buffer_handler
)

agent("What is 2+2 and tell me about AWS Lambda")
```

This handler leverages the `message` event which is triggered when a complete message is created. By using this approach, we can buffer the incrementally streamed text and only display complete, coherent messages rather than partial fragments. This is particularly useful in conversational interfaces or when responses benefit from being processed as complete units.

### Example - Event Loop Lifecycle Tracking

This callback handler illustrates the event loop lifecycle events and how they relate to each other. It's useful for understanding the flow of execution in the Strands agent:

```python
from strands import Agent
from strands_tools import calculator

def event_loop_tracker(**kwargs):
    # Track event loop lifecycle
    if kwargs.get("init_event_loop", False):
        print("🔄 Event loop initialized")
    elif kwargs.get("start_event_loop", False):
        print("▶️ Event loop cycle starting")
    elif kwargs.get("start", False):
        print("📝 New cycle started")
    elif "message" in kwargs:
        print(f"📬 New message created: {kwargs['message']['role']}")
    elif kwargs.get("complete", False):
        print("✅ Cycle completed")
    elif kwargs.get("force_stop", False):
        print(f"🛑 Event loop force-stopped: {kwargs.get('force_stop_reason', 'unknown reason')}")
        
    # Track tool usage
    if "current_tool_use" in kwargs and kwargs["current_tool_use"].get("name"):
        tool_name = kwargs["current_tool_use"]["name"]
        print(f"🔧 Using tool: {tool_name}")
    
    # Show only a snippet of text to keep output clean
    if "data" in kwargs:
        # Only show first 20 chars of each chunk for demo purposes
        data_snippet = kwargs["data"][:20] + ("..." if len(kwargs["data"]) > 20 else "")
        print(f"📟 Text: {data_snippet}")

# Create agent with event loop tracker
agent = Agent(
    tools=[calculator],
    callback_handler=event_loop_tracker
)

# This will show the full event lifecycle in the console
agent("What is the capital of France and what is 42+7?")
```

The output will show the sequence of events:

1. First the event loop initializes (`init_event_loop`)
2. Then the cycle begins (`start_event_loop`)
3. New cycles may start multiple times during execution (`start`)
4. Text generation and tool usage events occur during the cycle
5. Finally, the cycle completes (`complete`) or may be force-stopped

## Best Practices

When implementing callback handlers:

1. **Keep Them Fast**: Callback handlers run in the critical path of agent execution
2. **Handle All Event Types**: Be prepared for different event types
3. **Graceful Errors**: Handle exceptions within your handler
4. **State Management**: Store accumulated state in the `request_state`