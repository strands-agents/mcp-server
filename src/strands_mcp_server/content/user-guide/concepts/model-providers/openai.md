# OpenAI

[OpenAI](https://platform.openai.com/docs/overview) is an AI research and deployment company that provides a suite of powerful language models. The Strands Agents SDK implements an OpenAI provider, allowing you to run agents against any OpenAI or OpenAI-compatible model.

## Installation

OpenAI is configured as an optional dependency in Strands Agents. To install, run:

```bash
pip install 'strands-agents[openai]'
```

## Usage

After installing `openai`, you can import and initialize the Strands Agents' OpenAI provider as follows:

```python
from strands import Agent
from strands.models.openai import OpenAIModel
from strands_tools import calculator

model = OpenAIModel(
    client_args={
        "api_key": "<KEY>",
    },
    # **model_config
    model_id="gpt-4o",
    params={
        "max_tokens": 1000,
        "temperature": 0.7,
    }
)

agent = Agent(model=model, tools=[calculator])
response = agent("What is 2+2")
print(response)
```

To connect to a custom OpenAI-compatible server, you will pass in its `base_url` into the `client_args`:

```python
model = OpenAIModel(
    client_args={
      "api_key": "<KEY>",
      "base_url": "<URL>",
    },
    ...
)
```

## Configuration

### Client Configuration

The `client_args` configure the underlying OpenAI client. For a complete list of available arguments, please refer to the OpenAI [source](https://github.com/openai/openai-python).

### Model Configuration

The `model_config` configures the underlying model selected for inference. The supported configurations are:

|  Parameter | Description | Example | Options |
|------------|-------------|---------|---------|
| `model_id` | ID of a model to use | `gpt-4o` | [reference](https://platform.openai.com/docs/models)
| `params` | Model specific parameters | `{"max_tokens": 1000, "temperature": 0.7}` | [reference](https://platform.openai.com/docs/api-reference/chat/create)

## Troubleshooting

### Module Not Found

If you encounter the error `ModuleNotFoundError: No module named 'openai'`, this means you haven't installed the `openai` dependency in your environment. To fix, run `pip install 'strands-agents[openai]'`.

## Advanced Features

### Structured Output

OpenAI models support structured output through their native tool calling capabilities. When you use [`Agent.structured_output()`](../../../api-reference/agent.md#strands.agent.agent.Agent.structured_output), the Strands SDK automatically converts your Pydantic models to OpenAI's function calling format.

```python
from pydantic import BaseModel, Field
from strands import Agent
from strands.models.openai import OpenAIModel

class PersonInfo(BaseModel):
    """Extract person information from text."""
    name: str = Field(description="Full name of the person")
    age: int = Field(description="Age in years")
    occupation: str = Field(description="Job or profession")

model = OpenAIModel(
    client_args={"api_key": "<KEY>"},
    model_id="gpt-4o",
)

agent = Agent(model=model)

result = agent.structured_output(
    PersonInfo,
    "John Smith is a 30-year-old software engineer working at a tech startup."
)

print(f"Name: {result.name}")      # "John Smith"
print(f"Age: {result.age}")        # 30
print(f"Job: {result.occupation}") # "software engineer"
```

## References

- [API](../../../api-reference/models.md)
- [OpenAI](https://platform.openai.com/docs/overview)
