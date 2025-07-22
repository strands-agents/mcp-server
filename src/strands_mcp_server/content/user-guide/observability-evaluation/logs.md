# Logging

Strands SDK uses Python's standard [`logging`](https://docs.python.org/3/library/logging.html) module to provide visibility into its operations. This document explains how logging is implemented in the SDK and how you can configure it for your needs.

The Strands Agents SDK implements a straightforward logging approach:

1. **Module-level Loggers**: Each module in the SDK creates its own logger using `logging.getLogger(__name__)`, following Python best practices for hierarchical logging.

2. **Root Logger**: All loggers in the SDK are children of the "strands" root logger, making it easy to configure logging for the entire SDK.

3. **Default Behavior**: By default, the SDK doesn't configure any handlers or log levels, allowing you to integrate it with your application's logging configuration.

## Configuring Logging

To enable logging for the Strands Agents SDK, you can configure the "strands" logger:

```python
import logging

# Configure the root strands logger
logging.getLogger("strands").setLevel(logging.DEBUG)

# Add a handler to see the logs
logging.basicConfig(
    format="%(levelname)s | %(name)s | %(message)s", 
    handlers=[logging.StreamHandler()]
)
```

### Log Levels

The Strands Agents SDK uses standard Python log levels, with specific usage patterns:

- **DEBUG**: Extensively used throughout the SDK for detailed operational information, particularly for tool registration, discovery, configuration, and execution flows. This level provides visibility into the internal workings of the SDK, including tool registry operations, event loop processing, and model interactions.

- **INFO**: Not currently used in the Strands Agents SDK. The SDK jumps from DEBUG (for detailed operational information) directly to WARNING (for potential issues).

- **WARNING**: Commonly used to indicate potential issues that don't prevent operation, such as tool validation failures, specification validation errors, and context window overflow conditions. These logs highlight situations that might require attention but don't cause immediate failures.

- **ERROR**: Used to report significant problems that prevent specific operations from completing successfully, such as tool execution failures, event loop cycle exceptions, and handler errors. These logs indicate functionality that couldn't be performed as expected.

- **CRITICAL**: Not currently used in the Strands Agents SDK. This level is reserved for catastrophic failures that might prevent the application from running, but the SDK currently handles such situations at the ERROR level.

## Key Logging Areas

The Strands Agents SDK logs information in several key areas. Let's look at what kinds of logs you might see when using the following example agent with a calculator tool:

```python
from strands import Agent
from strands.tools.calculator import calculator

# Create an agent with the calculator tool
agent = Agent(tools=[calculator])
result = agent("What is 125 * 37?")
```

When running this code with logging enabled, you'll see logs from different components of the SDK as the agent processes the request, calls the calculator tool, and generates a response. The following sections show examples of these logs:

### Tool Registry and Execution

Logs related to tool discovery, registration, and execution:

```
# Tool registration
DEBUG | strands.tools.registry | tool_name=<calculator> | registering tool
DEBUG | strands.tools.registry | tool_name=<calculator>, tool_type=<function>, is_dynamic=<False> | registering tool
DEBUG | strands.tools.registry | tool_name=<calculator> | loaded tool config
DEBUG | strands.tools.registry | tool_count=<1> | tools configured

# Tool discovery
DEBUG | strands.tools.registry | tools_dir=</path/to/tools> | found tools directory
DEBUG | strands.tools.registry | tools_dir=</path/to/tools> | scanning
DEBUG | strands.tools.registry | tool_modules=<['calculator', 'weather']> | discovered

# Tool validation
WARNING | strands.tools.registry | tool_name=<invalid_tool> | spec validation failed | Missing required fields in tool spec: description
DEBUG | strands.tools.registry | tool_name=<calculator> | loaded dynamic tool config

# Tool execution
DEBUG | strands.event_loop.event_loop | tool_use=<calculator_tool_use_id> | streaming

# Tool hot reloading
DEBUG | strands.tools.registry | tool_name=<calculator> | searching directories for tool
DEBUG | strands.tools.registry | tool_name=<calculator> | reloading tool
DEBUG | strands.tools.registry | tool_name=<calculator> | successfully reloaded tool
```

### Event Loop

Logs related to the event loop processing:

```
ERROR | strands.event_loop.error_handler | an exception occurred in event_loop_cycle | ContextWindowOverflowException
DEBUG | strands.event_loop.error_handler | message_index=<5> | found message with tool results at index
```

### Model Interactions

Logs related to interactions with foundation models:

```
DEBUG | strands.models.bedrock | config=<{'model_id': 'us.anthropic.claude-4-sonnet-20250219-v1:0'}> | initializing
WARNING | strands.models.bedrock | bedrock threw context window overflow error
DEBUG | strands.models.bedrock | Found blocked output guardrail. Redacting output.
```

## Advanced Configuration

### Filtering Specific Modules

You can configure logging for specific modules within the SDK:

```python
import logging

# Enable DEBUG logs for the tool registry only
logging.getLogger("strands.tools.registry").setLevel(logging.DEBUG)

# Set WARNING level for model interactions
logging.getLogger("strands.models").setLevel(logging.WARNING)
```

### Custom Handlers

You can add custom handlers to process logs in different ways:

```python
import logging
import json

class JsonFormatter(logging.Formatter):
    def format(self, record):
        log_data = {
            "timestamp": self.formatTime(record),
            "level": record.levelname,
            "name": record.name,
            "message": record.getMessage()
        }
        return json.dumps(log_data)

# Create a file handler with JSON formatting
file_handler = logging.FileHandler("strands_agents_sdk.log")
file_handler.setFormatter(JsonFormatter())

# Add the handler to the strands logger
logging.getLogger("strands").addHandler(file_handler)
```

## Callback System vs. Logging

In addition to standard logging, Strands Agents SDK provides a callback system for streaming events:

- **Logging**: Internal operations, debugging, errors (not typically visible to end users)
- **Callbacks**: User-facing output, streaming responses, tool execution notifications

The callback system is configured through the `callback_handler` parameter when creating an Agent:

```python
from strands.handlers.callback_handler import PrintingCallbackHandler

agent = Agent(
    model="anthropic.claude-3-sonnet-20240229-v1:0",
    callback_handler=PrintingCallbackHandler()
)
```

You can create custom callback handlers to process streaming events according to your application's needs.

## Best Practices

1. **Configure Early**: Set up logging configuration before initializing the Agent
2. **Appropriate Levels**: Use INFO for normal operation and DEBUG for troubleshooting
3. **Structured Log Format**: Use the structured log format shown in examples for better parsing
4. **Performance**: Be mindful of logging overhead in production environments
5. **Integration**: Integrate Strands Agents SDK logging with your application's logging system
