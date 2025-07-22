# LiteLLM

[LiteLLM](https://docs.litellm.ai/docs/) is a unified interface for various LLM providers that allows you to interact with models from Amazon, Anthropic, OpenAI, and many others through a single API. The Strands Agents SDK implements a LiteLLM provider, allowing you to run agents against any model LiteLLM supports.

## Installation

LiteLLM is configured as an optional dependency in Strands Agents. To install, run:

```bash
pip install 'strands-agents[litellm]'
```

## Usage

After installing `litellm`, you can import and initialize Strands Agents' LiteLLM provider as follows:

```python
from strands import Agent
from strands.models.litellm import LiteLLMModel
from strands_tools import calculator

model = LiteLLMModel(
    client_args={
        "api_key": "<KEY>",
    },
    # **model_config
    model_id="anthropic/claude-3-7-sonnet-20250219",
    params={
        "max_tokens": 1000,
        "temperature": 0.7,
    }
)

agent = Agent(model=model, tools=[calculator])
response = agent("What is 2+2")
print(response)
```

## Configuration

### Client Configuration

The `client_args` configure the underlying LiteLLM `completion` API. For a complete list of available arguments, please refer to the LiteLLM [docs](https://docs.litellm.ai/docs/completion/input).

### Model Configuration

The `model_config` configures the underlying model selected for inference. The supported configurations are:

|  Parameter | Description | Example | Options |
|------------|-------------|---------|---------|
| `model_id` | ID of a model to use | `anthropic/claude-3-7-sonnet-20250219` | [reference](https://docs.litellm.ai/docs/providers)
| `params` | Model specific parameters | `{"max_tokens": 1000, "temperature": 0.7}` | [reference](https://docs.litellm.ai/docs/completion/input)

## Troubleshooting

### Module Not Found

If you encounter the error `ModuleNotFoundError: No module named 'litellm'`, this means you haven't installed the `litellm` dependency in your environment. To fix, run `pip install 'strands-agents[litellm]'`.

## Advanced Features

### Structured Output

LiteLLM supports structured output by proxying requests to underlying model providers that support tool calling. The availability of structured output depends on the specific model and provider you're using through LiteLLM.

```python
from pydantic import BaseModel, Field
from strands import Agent
from strands.models.litellm import LiteLLMModel

class BookAnalysis(BaseModel):
    """Analyze a book's key information."""
    title: str = Field(description="The book's title")
    author: str = Field(description="The book's author")
    genre: str = Field(description="Primary genre or category")
    summary: str = Field(description="Brief summary of the book")
    rating: int = Field(description="Rating from 1-10", ge=1, le=10)

model = LiteLLMModel(
    model_id="bedrock/us.anthropic.claude-3-7-sonnet-20250219-v1:0"
)

agent = Agent(model=model)

result = agent.structured_output(
    BookAnalysis,
    """
    Analyze this book: "The Hitchhiker's Guide to the Galaxy" by Douglas Adams.
    It's a science fiction comedy about Arthur Dent's adventures through space
    after Earth is destroyed. It's widely considered a classic of humorous sci-fi.
    """
)

print(f"Title: {result.title}")
print(f"Author: {result.author}")
print(f"Genre: {result.genre}")
print(f"Rating: {result.rating}")
```

## References

- [API](../../../api-reference/models.md)
- [LiteLLM](https://docs.litellm.ai/docs/)
