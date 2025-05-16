Strands Agents supports many different model providers. By default, agents use the Amazon Bedrock model provider with the Claude 3.7 model.

You can specify a different model in two ways:

1. By passing a string model ID directly to the Agent constructor
2. By creating a model provider instance with specific configurations

### Using a String Model ID

The simplest way to specify a model is to pass the model ID string directly:

```python
from strands import Agent

# Create an agent with a specific model by passing the model ID string
agent = Agent(model="us.anthropic.claude-3-7-sonnet-20250219-v1:0")
```

Models passed as string IDs will use the Bedrock model provider.

### Amazon Bedrock (Default)

For more control over model configuration, you can create a model provider instance:

```python
import boto3
from strands import Agent
from strands.models import BedrockModel

# Create a BedrockModel
bedrock_model = BedrockModel(
    model_id="us.anthropic.claude-3-7-sonnet-20250219-v1:0",
    region_name='us-west-2',
    temperature=0.3,
)

agent = Agent(model=bedrock_model)
```

You will also need to enable model access in Amazon Bedrock for the models that you choose to use with your agents, following the [AWS documentation](https://docs.aws.amazon.com/bedrock/latest/userguide/model-access-modify.html) to enable access.

### Anthropic

First install the `anthropic` python client:

```bash
pip install strands-agents[anthropic]
```

Next, import and initialize the `AnthropicModel` provider:

```python
from strands import Agent
from strands.models.anthropic import AnthropicModel

anthropic_model = AnthropicModel(
    client_args={
        "api_key": "<KEY>",
    },
    max_tokens=1028,
    model_id="claude-3-7-sonnet-20250219",
    params={
        "temperature": 0.7,
    }
)

agent = Agent(model=anthropic_model)
```

### LiteLLM

LiteLLM is a unified interface for various LLM providers that allows you to interact with models from OpenAI and many others.

First install the `litellm` python client:

```bash
pip install strands-agents[litellm]
```

Next, import and initialize the `LiteLLMModel` provider:

```python
from strands import Agent
from strands.models.litellm import LiteLLMModel

litellm_model = LiteLLMModel(
    client_args={
        "api_key": "<KEY>",
    },
    model_id="gpt-4o"
)

agent = Agent(model=litellm_model)
```

### Llama API

Llama API is a Meta-hosted API service that helps you integrate Llama models into your applications quickly and efficiently.

First install the `llamaapi` python client:
```bash
pip install strands-agents[llamaapi]
```

Next, import and initialize the `LlamaAPIModel` provider:

```python
from strands import Agent
from strands.models.llamaapi import LLamaAPIModel

model = LlamaAPIModel(
    client_args={
        "api_key": "<KEY>",
    },
    # **model_config
    model_id="Llama-4-Maverick-17B-128E-Instruct-FP8",
)

agent = Agent(models=LLamaAPIModel)
```

### Ollama (Local Models)

First install the `ollama` python client:

```bash
pip install strands-agents[ollama]
```

Next, import and initialize the `OllamaModel` provider:

```python
from strands import Agent
from strands.models.ollama import OllamaModel

ollama_model = OllamaModel(
    host="http://localhost:11434"  # Ollama server address
    model_id="llama3",  # Specify which model to use
    temperature=0.3,
)

agent = Agent(model=ollama_model)
```

### Custom Model Providers

We can even connect our agents to custom model providers to use any model from anywhere!

```python
from strands import Agent
from your_company.models.custom_model import CustomModel

custom_model = CustomModel(
    model_id="your-model-id
    temperature=0.3,
)

agent = Agent(model=custom_model)
```
