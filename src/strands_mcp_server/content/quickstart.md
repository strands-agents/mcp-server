This quickstart guide describes the core concepts of Strands Agents and shows you how to create your first AI agent with Strands Agents.

The full documentation can be found at https://strandsagents.com.

## Concepts

Strands Agents is a Python SDK for building AI agents. It may also be referred to as simply 'Strands'.

- Agent: Agents are defined using the Strands SDK. They are primarily defined by specifying 1) a model, 2) tools, and 3) prompts.
- Model: Agents can use any model that supports reasoning and tool use, including models in Amazon Bedrock, Anthropic, and many more through LiteLLM.
  The default model in Strands is Anthropic Claude Sonnet 3.7 in Amazon Bedrock in region us-west-2.
- Tools: Tools are the primary mechanism for extending agent capabilities, enabling them to perform actions beyond simple text generation.
  Tools allow agents to interact with external systems, access data, and manipulate their environment.
  The agent automatically determines when to use tools based on the input query and context.
  Strands provides some example tools, supports Model Context Protocol (MCP) servers, and can use any Python function decorated with @tool.
- Prompts: A system prompt and user messages are the primary way to communicate with AI models in an agent using Strands.

## Main Python Packages

The main Strands Agents SDK Python package is `strands-agents`. The SDK package provides the `strands` Python module.

The Strands Agents SDK additionally offers the `strands-agents-tools` package with many example tools.
The tools package provides the `strands-tools` Python module.

Your requirements.txt file may look like:

```
strands-agents>=0.1.0
strands-agents-tools>=0.1.0
```

## Example Agent

We'll create an example agent Python project, with this directory structure:

```
my_agent/
├── __init__.py
├── agent.py
└── requirements.txt
```

The `my_agent/__init__.py` file contains:

```python
from . import agent
```

The `agent.py` file contains:

```python
from strands import Agent, tool
from strands_tools import calculator, current_time, python_repl

# Define a custom tool for the agent as a Python function using the @tool decorator
@tool
def letter_counter(word: str, letter: str) -> int:
    """
    Count occurrences of a specific letter in a word.

    Args:
        word (str): The input word to search in
        letter (str): The specific letter to count

    Returns:
        int: The number of occurrences of the letter in the word
    """
    if not isinstance(word, str) or not isinstance(letter, str):
        return 0

    if len(letter) != 1:
        raise ValueError("The 'letter' parameter must be a single character")

    return word.lower().count(letter.lower())

# Define the agent
agent = Agent(
    # If you provide the model ID as a string, Bedrock is the
    # default model provider.
    # Remember to ensure you have model access in Bedrock or request it:
    # https://docs.aws.amazon.com/bedrock/latest/userguide/model-access-modify.html
    model="us.anthropic.claude-3-7-sonnet-20250219-v1:0",
    # Use tools from the strands-tools example tools package
    # as well as our custom letter_counter tool
    tools=[calculator, current_time, python_repl, letter_counter],
    # System prompt for the agent
    system_prompt="You are a helpful assistant"
)

# Ask the agent a question that uses the available tools
message = """
I have 4 requests:

1. What is the time right now?
2. Calculate 3111696 / 74088
3. Tell me how many letter R's are in the word "strawberry" 🍓
4. Output a script that does what we just spoke about!
   Use your python tools to confirm that the script works before outputting it
"""
agent(message)
```

## Running Agents

Our agent is just Python, so we can run it using any mechanism for running Python!

To test our agent we can simply run:

```bash
python -u my_agent/agent.py
```

And that's it! We now have a running agent with powerful tools and abilities in just a few lines of code 🥳.

## Debug Logs

To enable debug logs in our agent, configure the `strands` logger:

```python
import logging
from strands import Agent

# Enables Strands Agents debug log level
logging.getLogger("strands").setLevel(logging.DEBUG)

# Sets the logging format and streams logs to stderr
logging.basicConfig(
    format="%(levelname)s | %(name)s | %(message)s",
    handlers=[logging.StreamHandler()]
)

agent = Agent()

agent("Hello!")
```

## Capturing Streamed Data & Events

Strands Agents provides two main approaches to capture streaming events from an agent: async iterators and callback functions.

### Async Iterators

For asynchronous applications (like web servers or APIs), Strands Agents provides an async iterator approach using `stream_async()`. This is particularly useful with async frameworks like FastAPI or Django Channels.

```python
import asyncio
from strands import Agent
from strands_tools import calculator

# Initialize our agent without a callback handler
agent = Agent(
    tools=[calculator],
    callback_handler=None  # Disable default callback handler
)

# Async function that iterates over streamed agent events
async def process_streaming_response():
    query = "What is 25 * 48 and explain the calculation"

    # Get an async iterator for the agent's response stream
    agent_stream = agent.stream_async(query)

    # Process events as they arrive
    async for event in agent_stream:
        if "data" in event:
            # Print text chunks as they're generated
            print(event["data"], end="", flush=True)
        elif "current_tool_use" in event and event["current_tool_use"].get("name"):
            # Print tool usage information
            print(f"\n[Tool use delta for: {event['current_tool_use']['name']}]")

# Run the agent with the async event processing
asyncio.run(process_streaming_response())
```

The async iterator yields the same event types as the callback handler callbacks, including text generation events, tool events, and lifecycle events. This approach is ideal for integrating Strands Agents agents with async web frameworks.

See the [Async Iterators](concepts/streaming/async-iterators.md) documentation for full details.

### Callback Handlers (Callbacks)

We can create a custom callback function (named a [callback handler](concepts/streaming/callback-handlers.md)) that is invoked at various points throughout an agent's lifecycle.

Here is an example that captures streamed data from the agent and logs it instead of printing:

```python
import logging
from strands import Agent
from strands_tools import shell

logger = logging.getLogger("my_agent")

# Define a simple callback handler that logs instead of printing
tool_use_ids = []
def callback_handler(**kwargs):
    if "data" in kwargs:
        # Log the streamed data chunks
        logger.info(kwargs["data"], end="")
    elif "current_tool_use" in kwargs:
        tool = kwargs["current_tool_use"]
        if tool["toolUseId"] not in tool_use_ids:
            # Log the tool use
            logger.info(f"\n[Using tool: {tool.get('name')}]")
            tool_use_ids.append(tool["toolUseId"])

# Create an agent with the callback handler
agent = Agent(
    tools=[shell],
    callback_handler=callback_handler
)

# Ask the agent a question
result = agent("What operating system am I using?")

# Print only the last response
print(result.message)
```

The callback handler is called in real-time as the agent thinks, uses tools, and responds.

See the [Callback Handlers](concepts/streaming/callback-handlers.md) documentation for full details.
