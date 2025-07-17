# State Management in Strands

State management in the Strands Agents SDK provides various mechanisms for maintaining context and information across agent interactions. Understanding these state management options is essential for building agents that can maintain context, track data, and deliver coherent multi-turn responses.

## Types of State

Strands implements three primary types of state:

### 1. Conversation History

Conversation history is the primary form of context in Strands agents, representing the sequence of messages exchanged between the user and agent:

```python
from strands import Agent

agent = Agent()

# Send a message
agent("Hello!")

# Access the conversation history
print(agent.messages)  # Shows all messages exchanged so far
```

The `agent.messages` list contains:
- User messages that initiate interactions
- Assistant messages containing responses
- Tool calls and tool results
- System messages for internal context

You can initialize an agent with existing messages:

```python
agent = Agent(messages=[
    {"role": "user", "content": [{"text": "Hello, my name is Strands!"}]},
    {"role": "assistant", "content": [{"text": "Hi there! How can I help you today?"}]}
])
```

### 2. Agent State

Agent state provides a key-value storage mechanism for information that persists outside of the conversation context. Unlike conversation history, agent state isn't passed to the model during inference but can be accessed and modified by tools and application logic:

```python
# Create an agent with initial state
agent = Agent(state={"user_preferences": {"theme": "dark"}, "session_count": 0})

# Access state values
theme = agent.state.get("user_preferences")

# Set new state values
agent.state.set("last_action", "login")
agent.state.set("session_count", 1)

# Get entire state
all_state = agent.state.get()

# Delete state values
agent.state.delete("last_action")
```

Agent state enforces JSON serialization validation to ensure data can be persisted and restored.

### 3. Request State

Request state is a dictionary that persists throughout a single agent interaction and its event loop cycles:

```python
def custom_callback_handler(**kwargs):
    # Access request state
    if "request_state" in kwargs:
        state = kwargs["request_state"]
        # Use or modify state as needed
        if "counter" not in state:
            state["counter"] = 0
        state["counter"] += 1
        print(f"Callback handler event count: {state['counter']}")

agent = Agent(callback_handler=custom_callback_handler)
result = agent("Hi there!")
print(result.state)  # Access state in the result
```

Request state:
- Is initialized at the beginning of each agent call
- Persists through recursive event loop cycles
- Can be modified by callback handlers
- Is returned in the AgentResult object

## Conversation Management

Strands uses a conversation manager to handle conversation history effectively. The default is the `SlidingWindowConversationManager`, which keeps recent messages and removes older ones when needed:

```python
from strands import Agent
from strands.agent.conversation_manager import SlidingWindowConversationManager

# Create a conversation manager with custom window size
conversation_manager = SlidingWindowConversationManager(
    window_size=10,  # Maximum number of message pairs to keep
)

# Use the conversation manager with your agent
agent = Agent(conversation_manager=conversation_manager)
```

The sliding window conversation manager:
- Keeps the most recent N message pairs
- Removes the oldest messages when the window size is exceeded
- Handles context window overflow exceptions by reducing context
- Ensures conversations don't exceed model context limits

## Using State in Tools

Agent state is particularly useful for maintaining information across tool executions:

```python
from strands import Agent
from strands.tools.decorator import tool

@tool
def track_user_action(action: str, agent: Agent):
    """Track user actions in agent state."""
    # Get current action count
    action_count = agent.state.get("action_count") or 0
    
    # Update state
    agent.state.set("action_count", action_count + 1)
    agent.state.set("last_action", action)
    
    return f"Action '{action}' recorded. Total actions: {action_count + 1}"

agent = Agent(tools=[track_user_action])
agent("Track that I logged in")
print(f"Actions taken: {agent.state.get('action_count')}")
```

## Direct Tool Calling and State

Direct tool calls are (by default) recorded in the conversation history:

```python
from strands import Agent
from strands_tools import calculator

agent = Agent(tools=[calculator])

# Direct tool call with recording (default behavior)
agent.tool.calculator(expression="123 * 456")

# Direct tool call without recording
agent.tool.calculator(expression="765 / 987", record_direct_tool_call=False)
```

The `record_direct_tool_call` parameter controls whether the tool call is added to conversation history.

## Session Management

Strands supports session management for persisting state across multiple interactions or application restarts:

```python
from strands import Agent, Session, FileSessionStorage

# Create a session storage
session_storage = FileSessionStorage(directory="sessions")

# Create or load a session
session = Session(
    session_id="user123",
    storage=session_storage
)

# Create an agent with the session
agent = Agent(session=session)

# Use the agent
response = agent("Hello")

# The session is automatically saved after each interaction
```

Session storage saves:
- Conversation history
- Agent state
- Session metadata

## Best Practices

1. **Choose the Right State Type**:
   - Use conversation history for LLM-visible context
   - Use agent state for persistent data that shouldn't be sent to the model
   - Use request state for temporary, interaction-specific data

2. **Manage Conversation Window Size**:
   - Set appropriate window sizes based on your model's context limits
   - Use smaller windows for models with limited context size
   - Consider the complexity of your tasks when configuring window size

3. **State Validation**:
   - Ensure state data is JSON-serializable
   - Handle validation errors gracefully
   - Use proper type annotations for state values

4. **Tool State Management**:
   - Pass relevant state to tools explicitly
   - Update state consistently across tools
   - Document state dependencies for tools

5. **Session Persistence**:
   - Implement proper error handling for session loading/saving
   - Consider security implications for sensitive state data
   - Use appropriate storage backends for your application's needs