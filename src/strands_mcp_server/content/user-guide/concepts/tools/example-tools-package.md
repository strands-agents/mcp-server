# Example Built-in Tools

Strands offers an optional example tools package [`strands-agents-tools`]({{ tools_pypi }}) which includes pre-built tools to get started quickly experimenting with agents and tools during development. The package is also open source and available on [GitHub]({{ tools_repo_home }}).

Install the `strands-agents-tools` package by running:

```bash
pip install strands-agents-tools
```

If using `mem0_memory`, install the additional required dependencies by running:

```python
pip install strands-agents-tools[mem0_memory]
```

## Available Tools

#### RAG & Memory
- [`retrieve`]({{ tools_repo }}/src/strands_tools/retrieve.py): Semantically retrieve data from Amazon Bedrock Knowledge Bases for RAG, memory, and other purposes
- [`memory`]({{ tools_repo }}/src/strands_tools/memory.py): Agent memory persistence in Amazon Bedrock Knowledge Bases
- [`mem0_memory`]({{ tools_repo }}/src/strands_tools/mem0_memory.py): Agent memory and personalization built on top of [Mem0](https://mem0.ai)

#### File Operations
- [`editor`]({{ tools_repo }}/src/strands_tools/editor.py): File editing operations like line edits, search, and undo
- [`file_read`]({{ tools_repo }}/src/strands_tools/file_read.py): Read and parse files
- [`file_write`]({{ tools_repo }}/src/strands_tools/file_write.py): Create and modify files

#### Shell & System
- [`environment`]({{ tools_repo }}/src/strands_tools/environment.py): Manage environment variables
- [`shell`]({{ tools_repo }}/src/strands_tools/shell.py): Execute shell commands
- [`cron`]({{ tools_repo }}/src/strands_tools/cron.py): Task scheduling with cron jobs

#### Code Interpretation
- [`python_repl`]({{ tools_repo }}/src/strands_tools/python_repl.py): Run Python code

#### Web & Network
- [`http_request`]({{ tools_repo }}/src/strands_tools/http_request.py): Make API calls, fetch web data, and call local HTTP servers
- [`slack`]({{ tools_repo }}/src/strands_tools/slack.py): Slack integration with real-time events, API access, and message sending

#### Multi-modal
- [`generate_image_stability`]({{ tools_repo }}/src/strands_tools/generate_image_stability.py): Create images with Stability AI
- [`image_reader`]({{ tools_repo }}/src/strands_tools/image_reader.py): Process and analyze images
- [`generate_image`]({{ tools_repo }}/src/strands_tools/generate_image.py): Create AI generated images with Amazon Bedrock
- [`nova_reels`]({{ tools_repo }}/src/strands_tools/nova_reels.py): Create AI generated videos with Nova Reels on Amazon Bedrock
- [`speak`]({{ tools_repo }}/src/strands_tools/speak.py): Generate speech from text using macOS say command or Amazon Polly

#### AWS Services
- [`use_aws`]({{ tools_repo }}/src/strands_tools/use_aws.py): Interact with AWS services

#### Utilities
- [`calculator`]({{ tools_repo }}/src/strands_tools/calculator.py): Perform mathematical operations
- [`current_time`]({{ tools_repo }}/src/strands_tools/current_time.py): Get the current date and time
- [`load_tool`]({{ tools_repo }}/src/strands_tools/load_tool.py): Dynamically load more tools at runtime

#### Agents & Workflows
- [`agent_graph`]({{ tools_repo }}/src/strands_tools/agent_graph.py): Create and manage graphs of agents
- [`journal`]({{ tools_repo }}/src/strands_tools/journal.py): Create structured tasks and logs for agents to manage and work from
- [`swarm`]({{ tools_repo }}/src/strands_tools/swarm.py): Coordinate multiple AI agents in a swarm / network of agents
- [`stop`]({{ tools_repo }}/src/strands_tools/stop.py): Force stop the agent event loop
- [`handoff_to_user`]({{ tools_repo }}/src/strands_tools/handoff_to_user.py): Enable human-in-the-loop workflows by pausing agent execution for user input or transferring control entirely to the user
- [`think`]({{ tools_repo }}/src/strands_tools/think.py): Perform deep thinking by creating parallel branches of agentic reasoning
- [`use_llm`]({{ tools_repo }}/src/strands_tools/use_llm.py): Run a new AI event loop with custom prompts
- [`workflow`]({{ tools_repo }}/src/strands_tools/workflow.py): Orchestrate sequenced workflows
- [`batch`]({{ tools_repo }}/src/strands_tools/batch.py): Call multiple tools from a single model request

## Tool Consent and Bypassing

By default, certain tools that perform potentially sensitive operations (like file modifications, shell commands, or code execution) will prompt for user confirmation before executing. This safety feature ensures users maintain control over actions that could modify their system.

To bypass these confirmation prompts, you can set the `BYPASS_TOOL_CONSENT` environment variable:

```bash
# Set this environment variable to bypass tool confirmation prompts
export BYPASS_TOOL_CONSENT=true
```

Setting the environment variable within Python:

```python
import os

os.environ["BYPASS_TOOL_CONSENT"] = "true"
```

When this variable is set to `true`, tools will execute without asking for confirmation. This is particularly useful for:

- Automated workflows where user interaction isn't possible
- Development and testing environments
- CI/CD pipelines
- Situations where you've already validated the safety of operations

**Note:** Use this feature with caution in production environments, as it removes an important safety check.

## Human-in-the-Loop with handoff_to_user

The `handoff_to_user` tool enables human-in-the-loop workflows by allowing agents to pause execution for user input or transfer control entirely to a human operator. It offers two modes: Interactive Mode (`breakout_of_loop=False`) which collects input and continues, and Complete Handoff Mode (`breakout_of_loop=True`) which stops the event loop and transfers control to the user.

```python
from strands import Agent
from strands_tools import handoff_to_user

agent = Agent(tools=[handoff_to_user])

# Request user input and continue
response = agent.tool.handoff_to_user(
    message="I need your approval to proceed. Type 'yes' to confirm.",
    breakout_of_loop=False
)

# Complete handoff to user (stops agent execution)
agent.tool.handoff_to_user(
    message="Task completed. Please review the results.",
    breakout_of_loop=True
)
```

This tool is designed for terminal environments as an example implementation. For production applications, you may want to implement custom handoff mechanisms tailored to your specific UI/UX requirements, such as web interfaces or messaging platforms.
