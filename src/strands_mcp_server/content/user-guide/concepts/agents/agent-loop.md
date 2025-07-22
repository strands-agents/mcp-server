# Agent Loop

The agent loop is a core concept in the Strands Agents SDK that enables intelligent, autonomous behavior through a cycle of reasoning, tool use, and response generation. This document explains how the agent loop works, its components, and how to effectively use it in your applications.

## What is the Agent Loop?

The agent loop is the process by which a Strands agent processes user input, makes decisions, executes tools, and generates responses. It's designed to support complex, multi-step reasoning and actions with seamless integration of tools and language models.

```mermaid
flowchart LR
    A[Input & Context] --> Loop

    subgraph Loop[" "]
        direction TB
        B["Reasoning (LLM)"] --> C["Tool Selection"]
        C --> D["Tool Execution"]
        D --> B
    end

    Loop --> E[Response]
```

At its core, the agent loop follows these steps:

1. **Receives user input** and contextual information
2. **Processes the input** using a language model (LLM)
3. **Decides** whether to use tools to gather information or perform actions
4. **Executes tools** and receives results
5. **Continues reasoning** with the new information
6. **Produces a final response** or iterates again through the loop

This cycle may repeat multiple times within a single user interaction, allowing the agent to perform complex, multi-step reasoning and autonomous behavior.

## Core Components

The agent loop consists of several key components working together to create a seamless experience:

### Event Loop Cycle

The event loop cycle is the central mechanism that orchestrates the flow of information. It's implemented in the [`event_loop_cycle`](../../../api-reference/event-loop.md#strands.event_loop.event_loop.event_loop_cycle) function, which:

- Processes messages with the language model
- Handles tool execution requests
- Manages conversation state
- Handles errors and retries with exponential backoff
- Collects metrics and traces for observability

```python
def event_loop_cycle(
    model: Model,
    system_prompt: Optional[str],
    messages: Messages,
    tool_config: Optional[ToolConfig],
    **kwargs: Any,
) -> Tuple[StopReason, Message, EventLoopMetrics, Any]:
    # ... implementation details ...
```

The event loop cycle maintains a recursive structure, allowing for multiple iterations when tools are used, while preserving state across the conversation.

### Message Processing

Messages flow through the agent loop in a structured format:

1. **User messages**: Input that initiates the loop
2. **Assistant messages**: Responses from the model that may include tool requests
3. **Tool result messages**: Results from tool executions fed back to the model

The SDK automatically formats these messages into the appropriate structure for model inputs and [session state](state.md).

### Tool Execution

The agent loop includes a tool execution system that:

1. Validates tool requests from the model
2. Looks up tools in the registry
3. Executes tools concurrently with proper error handling
4. Captures and formats results
5. Feeds results back to the model

## Detailed Flow

Let's dive into the detailed flow of the agent loop:

### 1. Initialization

When an agent is created, it sets up the necessary components:

```python
from strands import Agent
from strands_tools import calculator

# Initialize the agent with tools, model, and configuration
agent = Agent(
    tools=[calculator],
    system_prompt="You are a helpful assistant."
)
```

This initialization:

- Creates a tool registry and registers tools
- Sets up the conversation manager
- Initializes metrics collection

### 2. User Input Processing

The agent is called with a user input:

```python
# Process user input
result = agent("Calculate 25 * 48")
```

Calling the agent adds the message to the conversation history and applies conversation management strategies before initializing a new event loop cycle.

### 3. Model Processing

The model receives:

- System prompt (if provided)
- Complete conversation history
- Configuration for available tools

The model then generates a response that can be a combination of a text response to the user and requests to use one or more tools if tools are available to the agent.

### 4. Response Analysis & Tool Execution

If the model returns a tool use request:

```json
{
  "role": "assistant",
  "content": [
    {
      "toolUse": {
        "toolUseId": "tool_123",
        "name": "calculator",
        "input": {
          "expression": "25 * 48"
        }
      }
    }
  ]
}
```

The event loop:

- Extracts and validates the tool request
- Looks up the tool in the registry
- Executes the tool
- Captures the result and formats it

### 5. Tool Result Processing

The tool result is formatted as:

```json
{
  "role": "user",
  "content": [
    {
      "toolResult": {
        "toolUseId": "tool_123",
        "status": "success",
        "content": [
          {"text": "1200"}
        ]
      }
    }
  ]
}
```

This result is added to the conversation history, and the model is invoked again for it to reason about the tool results.

### 6. Recursive Processing

The agent loop can recursively continue if the model requests more tool executions, further clarification is needed, or multi-step reasoning is required.

This recursive nature allows for complex workflows like:

1. User asks a question
2. Agent uses a search tool to find information
3. Agent uses a calculator to process the information
4. Agent synthesizes a final response

### 7. Completion

The loop completes when the model generates a final text response or an exception occurs that cannot be handled. At completion, metrics and traces are collected, conversation state is updated, and the final response is returned to the caller.
