# Conversation Management

In the Strands Agents SDK, context refers to the information provided to the agent for understanding and reasoning. This includes:

- User messages
- Agent responses
- Tool usage and results
- System prompts

As conversations grow, managing this context becomes increasingly important for several reasons:

1. **Token Limits**: Language models have fixed context windows (maximum tokens they can process)
2. **Performance**: Larger contexts require more processing time and resources
3. **Relevance**: Older messages may become less relevant to the current conversation
4. **Coherence**: Maintaining logical flow and preserving important information

## Conversation Managers

The SDK provides a flexible system for context management through the [`ConversationManager`](../../../api-reference/agent.md#strands.agent.conversation_manager.conversation_manager.ConversationManager) interface. This allows you to implement different strategies for managing conversation history. There are three key elements to implement:

1. [`apply_management`](../../../api-reference/agent.md#strands.agent.conversation_manager.conversation_manager.ConversationManager.apply_management): This method is called after each event loop cycle completes to manage the conversation history. It's responsible for applying your management strategy to the messages array, which may have been modified with tool results and assistant responses. The agent runs this method automatically after processing each user input and generating a response.

2. [`reduce_context`](../../../api-reference/agent.md#strands.agent.conversation_manager.conversation_manager.ConversationManager.reduce_context): This method is called when the model's context window is exceeded (typically due to token limits). It implements the specific strategy for reducing the window size when necessary. The agent calls this method when it encounters a context window overflow exception, giving your implementation a chance to trim the conversation history before retrying.

3. `removed_messages_count` This attribute is tracked by conversation managers, and utilized by [Session Management](./session-management.md) to efficiently load messages from the session storage. The count represent messages provided by the user or LLM that have been removed from the agent's messages, but not messages included by the conversation manager through something like summarization.

To manage conversations, you can either leverage one of Strands's provided managers or build your own manager that matches your requirements.

#### NullConversationManager

The [`NullConversationManager`](../../../api-reference/agent.md#strands.agent.conversation_manager.null_conversation_manager.NullConversationManager) is a simple implementation that does not modify the conversation history. It's useful for:

- Short conversations that won't exceed context limits
- Debugging purposes
- Cases where you want to manage context manually

```python
from strands import Agent
from strands.agent.conversation_manager import NullConversationManager

agent = Agent(
    conversation_manager=NullConversationManager()
)
```

#### SlidingWindowConversationManager

The [`SlidingWindowConversationManager`](../../../api-reference/agent.md#strands.agent.conversation_manager.sliding_window_conversation_manager.SlidingWindowConversationManager) implements a sliding window strategy that maintains a fixed number of recent messages. This is the default conversation manager used by the Agent class.

```python
from strands import Agent
from strands.agent.conversation_manager import SlidingWindowConversationManager

# Create a conversation manager with custom window size
conversation_manager = SlidingWindowConversationManager(
    window_size=20,  # Maximum number of messages to keep
    should_truncate_results=True, # Enable truncating the tool result when a message is too large for the model's context window 
)

agent = Agent(
    conversation_manager=conversation_manager
)
```

Key features of the `SlidingWindowConversationManager`:

- **Maintains Window Size**: Automatically removes messages from the window if the number of messages exceeds the limit.
- **Dangling Message Cleanup**: Removes incomplete message sequences to maintain valid conversation state.
- **Overflow Trimming**: In the case of a context window overflow, it will trim the oldest messages from history until the request fits in the models context window.
- **Configurable Tool Result Truncation**: Enable / disable truncation of tool results when the message exceeds context window limits. When `should_truncate_results=True` (default), large results are truncated with a placeholder message. When `False`, full results are preserved but more historical messages may be removed.

#### SummarizingConversationManager

The [`SummarizingConversationManager`](../../../api-reference/agent.md#strands.agent.conversation_manager.summarizing_conversation_manager.SummarizingConversationManager) implements intelligent conversation context management by summarizing older messages instead of simply discarding them. This approach preserves important information while staying within context limits.

Configuration parameters:

- **`summary_ratio`** (float, default: 0.3): Percentage of messages to summarize when reducing context (clamped between 0.1 and 0.8)
- **`preserve_recent_messages`** (int, default: 10): Minimum number of recent messages to always keep
- **`summarization_agent`** (Agent, optional): Custom agent for generating summaries. If not provided, uses the main agent instance. Cannot be used together with `summarization_system_prompt`.
- **`summarization_system_prompt`** (str, optional): Custom system prompt for summarization. If not provided, uses a default prompt that creates structured bullet-point summaries focusing on key topics, tools used, and technical information in third-person format. Cannot be used together with `summarization_agent`.

**Basic Usage:**

By default, the `SummarizingConversationManager` leverages the same model and configuration as your main agent to perform summarization.

```python
from strands import Agent
from strands.agent.conversation_manager import SummarizingConversationManager

agent = Agent(
    conversation_manager=SummarizingConversationManager()
)
```

You can also customize the behavior by adjusting parameters like summary ratio and number of preserved messages:

```python
from strands import Agent
from strands.agent.conversation_manager import SummarizingConversationManager

# Create the summarizing conversation manager with default settings
conversation_manager = SummarizingConversationManager(
    summary_ratio=0.3,  # Summarize 30% of messages when context reduction is needed
    preserve_recent_messages=10,  # Always keep 10 most recent messages
)

agent = Agent(
    conversation_manager=conversation_manager
)
```

**Custom System Prompt for Domain-Specific Summarization:**

You can customize the summarization behavior by providing a custom system prompt that tailors the summarization to your domain or use case.

```python
from strands import Agent
from strands.agent.conversation_manager import SummarizingConversationManager

# Custom system prompt for technical conversations
custom_system_prompt = """
You are summarizing a technical conversation. Create a concise bullet-point summary that:
- Focuses on code changes, architectural decisions, and technical solutions
- Preserves specific function names, file paths, and configuration details
- Omits conversational elements and focuses on actionable information
- Uses technical terminology appropriate for software development

Format as bullet points without conversational language.
"""

conversation_manager = SummarizingConversationManager(
    summarization_system_prompt=custom_system_prompt
)

agent = Agent(
    conversation_manager=conversation_manager
)
```

**Advanced Configuration with Custom Summarization Agent:**

For advanced use cases, you can provide a custom `summarization_agent` to handle the summarization process. This enables using a different model (such as a faster or a more cost-effective one), incorporating tools during summarization, or implementing specialized summarization logic tailored to your domain. The custom agent can leverage its own system prompt, tools, and model configuration to generate summaries that best preserve the essential context for your specific use case.

```python
from strands import Agent
from strands.agent.conversation_manager import SummarizingConversationManager
from strands.models import AnthropicModel

# Create a cheaper, faster model for summarization tasks
summarization_model = AnthropicModel(
    model_id="claude-haiku-4-20250514",  # More cost-effective for summarization
    max_tokens=1000,
    params={"temperature": 0.1}  # Low temperature for consistent summaries
)
custom_summarization_agent = Agent(model=summarization_model)

conversation_manager = SummarizingConversationManager(
    summary_ratio=0.4,
    preserve_recent_messages=8,
    summarization_agent=custom_summarization_agent
)

agent = Agent(
    conversation_manager=conversation_manager
)
```

Key features of the `SummarizingConversationManager`:

- **Context Window Management**: Automatically reduces context when token limits are exceeded
- **Intelligent Summarization**: Uses structured bullet-point summaries to capture key information
- **Tool Pair Preservation**: Ensures tool use and result message pairs aren't broken during summarization
- **Flexible Configuration**: Customize summarization behavior through various parameters
- **Fallback Safety**: Handles summarization failures gracefully
