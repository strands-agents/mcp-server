# Strands Agents SDK

[Strands Agents]({{ sdk_repo_home }}) is a simple-to-use, code-first framework for building agents.

First, install the Strands Agents SDK:

```bash
pip install strands-agents
```

Then create your first agent as a Python file, for this example we'll use `agent.py`.

```python
from strands import Agent

# Create an agent with default settings
agent = Agent()

# Ask the agent a question
agent("Tell me about agentic AI")
```

Now run the agent with:

```bash
python -u agent.py
```

That's it!

> **Note**: To run this example hello world agent you will need to set up credentials for our model provider and enable model access. The default model provider is [Amazon Bedrock](user-guide/concepts/model-providers/amazon-bedrock.md) and the default model is Claude 4 Sonnet in the US Oregon (us-west-2) region.

> For the default Amazon Bedrock model provider, see the [Boto3 documentation](https://boto3.amazonaws.com/v1/documentation/api/latest/guide/credentials.html) for setting up AWS credentials. Typically for development, AWS credentials are defined in `AWS_` prefixed environment variables or configured with `aws configure`. You will also need to enable Claude 4 Sonnet model access in Amazon Bedrock, following the [AWS documentation](https://docs.aws.amazon.com/bedrock/latest/userguide/model-access-modify.html) to enable access.

> Different model providers can be configured for agents by following the [quickstart guide](user-guide/quickstart.md#model-providers).

## Features

Strands Agents is lightweight and production-ready, supporting many model providers and deployment targets. 

Key features include:

* **Lightweight and gets out of your way**: A simple agent loop that just works and is fully customizable.
* **Production ready**: Full observability, tracing, and deployment options for running agents at scale.
* **Model, provider, and deployment agnostic**: Strands supports many different models from many different providers.
* **Powerful built-in tools**: Get started quickly with tools for a broad set of capabilities.
* **Multi-agent and autonomous agents**: Apply advanced techniques to your AI systems like agent teams and agents that improve themselves over time.
* **Conversational, non-conversational, streaming, and non-streaming**: Supports all types of agents for various workloads.
* **Safety and security as a priority**: Run agents responsibly while protecting data.

## Next Steps

Ready to learn more? Check out these resources:

- [Quickstart](user-guide/quickstart.md) - A more detailed introduction to Strands Agents
- [Examples](examples/README.md) - Examples for many use cases, types of agents, multi-agent systems, autonomous agents, and more
- [Example Built-in Tools](user-guide/concepts/tools/example-tools-package.md) - The {{ link_strands_tools }} package provides many powerful example tools for your agents to use during development
- [Strands Agent Builder]({{ agent_builder_repo_home }}) - Use the accompanying {{ link_strands_builder }} agent builder to harness the power of LLMs to generate your own tools and agents

!!! tip "Join Our Community"

    [Learn how to contribute]({{ sdk_repo }}/CONTRIBUTING.md) or join our community discussions to shape the future of Strands Agents ❤️.