# Amazon Bedrock

Amazon Bedrock is a fully managed service that offers a choice of high-performing foundation models from leading AI companies through a unified API. Strands provides native support for Amazon Bedrock, allowing you to use these powerful models in your agents with minimal configuration.

The [`BedrockModel`](../../../api-reference/models.md#strands.models.bedrock) class in Strands enables seamless integration with Amazon Bedrock's API, supporting:

- Text generation
- Multi-Modal understanding (Image, Document, etc.)
- Tool/function calling
- Guardrail configurations
- System Prompt, Tool, and/or Message caching

## Getting Started

### Prerequisites

1. **AWS Account**: You need an AWS account with access to Amazon Bedrock
2. **Model Access**: Request access to your desired models in the Amazon Bedrock console
3. **AWS Credentials**: Configure AWS credentials with appropriate permissions

#### Required IAM Permissions

To use Amazon Bedrock with Strands, your IAM user or role needs the following permissions:

- `bedrock:InvokeModelWithResponseStream` (for streaming mode)
- `bedrock:InvokeModel` (for non-streaming mode)

Here's a sample IAM policy that grants the necessary permissions:

```json
{
    "Version": "2012-10-17",
    "Statement": [
        {
            "Effect": "Allow",
            "Action": [
                "bedrock:InvokeModelWithResponseStream",
                "bedrock:InvokeModel"
            ],
            "Resource": "*"
        }
    ]
}
```

For production environments, it's recommended to scope down the `Resource` to specific model ARNs.

#### Requesting Access to Bedrock Models

Before you can use a model in Amazon Bedrock, you need to request access to it:

1. Sign in to the AWS Management Console and open the Amazon Bedrock console
2. In the navigation pane, choose **Model access**
3. Choose **Manage model access**
4. Select the checkbox next to each model you want to access
5. Choose **Request model access**
6. Review the terms and conditions, then select **I accept these terms**
7. Choose **Request model access**

The model access request is typically processed immediately. Once approved, the model status will change to "Access granted" in the console.

For more details, see the [Amazon Bedrock documentation on modifying model access](https://docs.aws.amazon.com/bedrock/latest/userguide/model-access-modify.html).

#### Setting Up AWS Credentials

Strands uses [boto3](https://boto3.amazonaws.com/v1/documentation/api/latest/index.html) (the AWS SDK for Python) to make calls to Amazon Bedrock. Boto3 has its own credential resolution system that determines which credentials to use when making requests to AWS.

For development environments, configure credentials using one of these methods:

**Option 1: AWS CLI**

```bash
aws configure
```

**Option 2: Environment Variables**

```bash
export AWS_ACCESS_KEY_ID=your_access_key
export AWS_SECRET_ACCESS_KEY=your_secret_key
export AWS_SESSION_TOKEN=your_session_token  # If using temporary credentials
export AWS_REGION="us-west-2"  # Used if a custom Boto3 Session is not provided
```

**Option 3: Custom Boto3 Session**
You can configure a custom [boto3 Session](https://boto3.amazonaws.com/v1/documentation/api/latest/reference/core/session.html) and pass it to the [`BedrockModel`](../../../api-reference/models.md#strands.models.bedrock):

```python
import boto3
from strands.models import BedrockModel

# Create a custom boto3 session
session = boto3.Session(
    aws_access_key_id='your_access_key',
    aws_secret_access_key='your_secret_key',
    aws_session_token='your_session_token',  # If using temporary credentials
    region_name='us-west-2',
    profile_name='your-profile'  # Optional: Use a specific profile
)

# Create a Bedrock model with the custom session
bedrock_model = BedrockModel(
    model_id="anthropic.claude-sonnet-4-20250514-v1:0",
    boto_session=session
)
```

For complete details on credential configuration and resolution, see the [boto3 credentials documentation](https://boto3.amazonaws.com/v1/documentation/api/latest/guide/credentials.html#configuring-credentials).

## Basic Usage

The [`BedrockModel`](../../../api-reference/models.md#strands.models.bedrock) provider is used by default when creating a basic Agent, and uses the [Claude 4 Sonnet](https://aws.amazon.com/blogs/aws/claude-opus-4-anthropics-most-powerful-model-for-coding-is-now-in-amazon-bedrock/) model by default. This basic example creates an agent using this default setup:

```python
from strands import Agent

agent = Agent()

response = agent("Tell me about Amazon Bedrock.")
```

You can specify which Bedrock model to use by passing in the model ID string directly to the Agent constructor:

```python
from strands import Agent

# Create an agent with a specific model by passing the model ID string
agent = Agent(model="anthropic.claude-sonnet-4-20250514-v1:0")

response = agent("Tell me about Amazon Bedrock.")
```

For more control over model configuration, you can create an instance of the [`BedrockModel`](../../../api-reference/models.md#strands.models.bedrock) class:

```python
from strands import Agent
from strands.models import BedrockModel

# Create a Bedrock model instance
bedrock_model = BedrockModel(
    model_id="us.amazon.nova-premier-v1:0",
    temperature=0.3,
    top_p=0.8,
)

# Create an agent using the BedrockModel instance
agent = Agent(model=bedrock_model)

# Use the agent
response = agent("Tell me about Amazon Bedrock.")
```

## Configuration Options

The [`BedrockModel`](../../../api-reference/models.md#strands.models.bedrock) supports various [configuration parameters](../../../api-reference/models.md#strands.models.bedrock.BedrockModel.BedrockConfig):

| Parameter                                                                                                                                                                                             | Description                                                                                                    | Default                                                                                              |
| ----------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- | -------------------------------------------------------------------------------------------------------------- | ---------------------------------------------------------------------------------------------------- |
| [`model_id`](https://docs.aws.amazon.com/bedrock/latest/userguide/models-supported.html)                                                                                                              | The Bedrock model identifier                                                                                   | "anthropic.claude-sonnet-4-20250514-v1:0"                                                       |
| [`boto_session`](https://boto3.amazonaws.com/v1/documentation/api/latest/reference/core/session.html)                                                                                                 | Boto Session to use when creating the Boto3 Bedrock Client                                                     | Boto Session with region: "us-west-2"                                                                |
| [`boto_client_config`](https://botocore.amazonaws.com/v1/documentation/api/latest/reference/config.html)                                                                                              | Botocore Configuration used when creating the Boto3 Bedrock Client                                             | -                                                                                                    |
| [`region_name`](https://docs.aws.amazon.com/general/latest/gr/bedrock.html)                                                                                                                           | AWS region to use for the Bedrock service                                                                      | "us-west-2"                                                                                          |
| [`streaming`](https://docs.aws.amazon.com/bedrock/latest/userguide/api-methods.html)                                                                                                                  | Flag to enable/disable streaming mode                                                                          | True                                                                                                 |
| [`temperature`](https://docs.aws.amazon.com/bedrock/latest/APIReference/API_runtime_InferenceConfiguration.html#API_runtime_InferenceConfiguration_Contents)                                          | Controls randomness (higher = more random)                                                                     | [Model-specific default](https://docs.aws.amazon.com/bedrock/latest/userguide/model-parameters.html) |
| [`max_tokens`](https://docs.aws.amazon.com/bedrock/latest/APIReference/API_runtime_InferenceConfiguration.html#API_runtime_InferenceConfiguration_Contents)                                           | Maximum number of tokens to generate                                                                           | [Model-specific default](https://docs.aws.amazon.com/bedrock/latest/userguide/model-parameters.html) |
| [`top_p`](https://docs.aws.amazon.com/bedrock/latest/APIReference/API_runtime_InferenceConfiguration.html#API_runtime_InferenceConfiguration_Contents)                                                | Controls diversity via nucleus sampling                                                                        | [Model-specific default](https://docs.aws.amazon.com/bedrock/latest/userguide/model-parameters.html) |
| [`stop_sequences`](https://docs.aws.amazon.com/bedrock/latest/APIReference/API_runtime_InferenceConfiguration.html#API_runtime_InferenceConfiguration_Contents)                                       | List of sequences that stop generation                                                                         | -                                                                                                    |
| [`cache_prompt`](https://docs.aws.amazon.com/bedrock/latest/userguide/prompt-caching.html)                                                                                                            | Cache point type for the system prompt                                                                         | -                                                                                                    |
| [`cache_tools`](https://docs.aws.amazon.com/bedrock/latest/userguide/prompt-caching.html)                                                                                                             | Cache point type for tools                                                                                     | -                                                                                                    |
| [`guardrail_id`](https://docs.aws.amazon.com/bedrock/latest/APIReference/API_runtime_GuardrailStreamConfiguration.html)                                                                               | ID of the guardrail to apply                                                                                   | -                                                                                                    |
| [`guardrail_trace`](https://docs.aws.amazon.com/bedrock/latest/APIReference/API_runtime_GuardrailStreamConfiguration.html)                                                                            | Guardrail trace mode ("enabled", "disabled", "enabled_full")                                                   | "enabled"                                                                                            |
| [`guardrail_version`](https://docs.aws.amazon.com/bedrock/latest/APIReference/API_runtime_GuardrailStreamConfiguration.html)                                                                          | Version of the guardrail to apply                                                                              | -                                                                                                    |
| [`guardrail_stream_processing_mode`](https://docs.aws.amazon.com/bedrock/latest/APIReference/API_runtime_GuardrailStreamConfiguration.html)                                                           | The guardrail processing mode ("sync", "async")                                                                | -                                                                                                    |
| [`guardrail_redact_input`](https://docs.aws.amazon.com/bedrock/latest/APIReference/API_runtime_GuardrailStreamConfiguration.html)                                                                     | Flag to redact input if a guardrail is triggered                                                               | True                                                                                                 |
| [`guardrail_redact_input_message`](https://docs.aws.amazon.com/bedrock/latest/APIReference/API_runtime_GuardrailStreamConfiguration.html)                                                             | If a Bedrock guardrail triggers, replace the input with this message                                           | "[User input redacted.]"                                                                             |
| [`guardrail_redact_output`](https://docs.aws.amazon.com/bedrock/latest/APIReference/API_runtime_GuardrailStreamConfiguration.html)                                                                    | Flag to redact output if guardrail is triggered                                                                | False                                                                                                |
| [`guardrail_redact_output_message`](https://docs.aws.amazon.com/bedrock/latest/APIReference/API_runtime_GuardrailStreamConfiguration.html)                                                            | If a Bedrock guardrail triggers, replace output with this message                                              | "[Assistant output redacted.]"                                                                       |
| [`additional_request_fields`](https://docs.aws.amazon.com/bedrock/latest/userguide/model-parameters.html)                                                                                             | Additional inference parameters that the model supports                                                        | -                                                                                                    |
| [`additional_response_field_paths`](https://docs.aws.amazon.com/bedrock/latest/APIReference/API_runtime_ConverseStream.html#bedrock-runtime_ConverseStream-request-additionalModelResponseFieldPaths) | Additional model parameters field paths to return in the response                                              | -                                                                                                    |
| `additional_args`                                                                                                                                                                                     | Additional arguments to include in the request. This is included for forwards compatibility of new parameters. | -                                                                                                    |

### Example with Configuration

```python
from strands import Agent
from strands.models import BedrockModel
from botocore.config import Config as BotocoreConfig

# Create a boto client config with custom settings
boto_config = BotocoreConfig(
    retries={"max_attempts": 3, "mode": "standard"},
    connect_timeout=5,
    read_timeout=60
)

# Create a configured Bedrock model
bedrock_model = BedrockModel(
    model_id="anthropic.claude-sonnet-4-20250514-v1:0",
    region_name="us-east-1",  # Specify a different region than the default
    temperature=0.3,
    top_p=0.8,
    stop_sequences=["###", "END"],
    boto_client_config=boto_config,
)

# Create an agent with the configured model
agent = Agent(model=bedrock_model)

# Use the agent
response = agent("Write a short story about an AI assistant.")
```

## Advanced Features

### Streaming vs Non-Streaming Mode

Certain Amazon Bedrock models only support non-streaming tool use, so you can set the `streaming` configuration to false
in order to use these models. Both modes provide the same event structure and functionality in your agent, as the non-streaming responses are converted to the streaming format internally.

```python
# Streaming model (default)
streaming_model = BedrockModel(
    model_id="anthropic.claude-sonnet-4-20250514-v1:0",
    streaming=True,  # This is the default
)

# Non-streaming model
non_streaming_model = BedrockModel(
    model_id="us.meta.llama3-2-90b-instruct-v1:0",
    streaming=False,  # Disable streaming
)
```

See the Amazon Bedrock documentation for [Supported models and model features](https://docs.aws.amazon.com/bedrock/latest/userguide/conversation-inference-supported-models-features.html) to learn about the streaming support for different models.

### Multimodal Support

Some Bedrock models support multimodal inputs (Documents, Images, etc.). Here's how to use them:

```python
from strands import Agent
from strands.models import BedrockModel

# Create a Bedrock model that supports multimodal inputs
bedrock_model = BedrockModel(
    model_id="anthropic.claude-sonnet-4-20250514-v1:0"
)
agent = Agent(model=bedrock_model)

# Send the multimodal message to the agent
response = agent(
    [
        {
            "document": {
                "format": "txt",
                "name": "example",
                "source": {
                    "bytes": b"Once upon a time..."
                }
            }
        },
        {
            "text": "Tell me about the document."
        }
    ]
)
```

For a complete list of input types, please refer to the [API Reference](../../../api-reference/types.md#strands.types.content.ContentBlock).

### Guardrails

Amazon Bedrock supports guardrails to help ensure model outputs meet your requirements. Strands allows you to configure guardrails with your [`BedrockModel`](../../../api-reference/models.md#strands.models.bedrock):

```python
from strands import Agent
from strands.models import BedrockModel

# Using guardrails with BedrockModel
bedrock_model = BedrockModel(
    model_id="anthropic.claude-sonnet-4-20250514-v1:0",
    guardrail_id="your-guardrail-id",
    guardrail_version="DRAFT",
    guardrail_trace="enabled",  # Options: "enabled", "disabled", "enabled_full"
    guardrail_stream_processing_mode="sync",  # Options: "sync", "async"
    guardrail_redact_input=True,  # Default: True
    guardrail_redact_input_message="Blocked Input!", # Default: [User input redacted.]
    guardrail_redact_output=False,  # Default: False
    guardrail_redact_output_message="Blocked Output!" # Default: [Assistant output redacted.]
)

guardrail_agent = Agent(model=bedrock_model)

response = guardrail_agent("Can you tell me about the Strands SDK?")
```

When a guardrail is triggered:

- Input redaction (enabled by default): If a guardrail policy is triggered, the input is redacted
- Output redaction (disabled by default): If a guardrail policy is triggered, the output is redacted
- Custom redaction messages can be specified for both input and output redactions

### Caching

Strands supports caching system prompts, tools, and messages to improve performance and reduce costs. Caching allows you to reuse parts of previous requests, which can significantly reduce token usage and latency.

When you enable prompt caching, Amazon Bedrock creates a cache composed of **cache checkpoints**. These are markers that define the contiguous subsection of your prompt that you wish to cache (often referred to as a prompt prefix). These prompt prefixes should be static between requests; alterations to the prompt prefix in subsequent requests will result in a cache miss.

The cache has a five-minute Time To Live (TTL), which resets with each successful cache hit. During this period, the context in the cache is preserved. If no cache hits occur within the TTL window, your cache expires.

For detailed information about supported models, minimum token requirements, and other limitations, see the [Amazon Bedrock documentation on prompt caching](https://docs.aws.amazon.com/bedrock/latest/userguide/prompt-caching.html).

#### System Prompt Caching

System prompt caching allows you to reuse a cached system prompt across multiple requests:

```python
from strands import Agent
from strands.models import BedrockModel

# Using system prompt caching with BedrockModel
bedrock_model = BedrockModel(
    model_id="anthropic.claude-sonnet-4-20250514-v1:0",
    cache_prompt="default"
)

# Create an agent with the model
agent = Agent(
    model=bedrock_model,
    system_prompt="You are a helpful assistant that provides concise answers. " +
                 "This is a long system prompt with detailed instructions... "
                 # Add enough text to reach the minimum token requirement for your model
)

# First request will cache the system prompt
response1 = agent("Tell me about Python")

# Second request will reuse the cached system prompt
response2 = agent("Tell me about JavaScript")
```

#### Tool Caching

Tool caching allows you to reuse a cached tool definition across multiple requests:

```python
from strands import Agent, tool
from strands.models import BedrockModel
from strands_tools import calculator, current_time

# Using tool caching with BedrockModel
bedrock_model = BedrockModel(
    model_id="anthropic.claude-sonnet-4-20250514-v1:0",
    cache_tools="default"
)

# Create an agent with the model and tools
agent = Agent(
    model=bedrock_model,
    tools=[calculator, current_time]
)
# First request will cache the tools
response1 = agent("What time is it?")

# Second request will reuse the cached tools
response2 = agent("What is the square root of 1764?")
```

#### Messages Caching

Messages caching allows you to reuse a cached conversation across multiple requests. This is not enabled via a configuration in the [`BedrockModel`](../../../api-reference/models.md#strands.models.bedrock) class, but instead by including a `cachePoint` in the Agent's Messages array:

```python
from strands import Agent
from strands.models import BedrockModel

# Create a conversation, and add a messages cache point to cache the conversation up to that point
messages = [
    {
        "role": "user",
        "content": [
            {
                "document": {
                    "format": "txt",
                    "name": "example",
                    "source": {
                        "bytes": b"This is a sample document!"
                    }
                }
            },
            {
                "text": "Use this document in your response."
            },
            {
                "cachePoint": {"type": "default"}
            },
        ],
    },
    {
        "role": "assistant",
        "content": [
            {
                "text": "I will reference that document in my following responses."
            }
        ]
    }
]

# Create an agent with the model and messages
agent = Agent(
    messages=messages
)
# First request will cache the message
response1 = agent("What is in that document?")

# Second request will reuse the cached message
response2 = agent("How long is the document?")
```

> **Note**: Each model has its own minimum token requirement for creating cache checkpoints. If your system prompt or tool definitions don't meet this minimum token threshold, a cache checkpoint will not be created. For optimal caching, ensure your system prompts and tool definitions are substantial enough to meet these requirements.

### Updating Configuration at Runtime

You can update the model configuration during runtime:

```python
# Create the model with initial configuration
bedrock_model = BedrockModel(
    model_id="anthropic.claude-sonnet-4-20250514-v1:0",
    temperature=0.7
)

# Update configuration later
bedrock_model.update_config(
    temperature=0.3,
    top_p=0.2,
)
```

This is especially useful for tools that need to update the model's configuration:

```python
@tool
def update_model_id(model_id: str, agent: Agent) -> str:
    """
    Update the model id of the agent

    Args:
      model_id: Bedrock model id to use.
    """
    print(f"Updating model_id to {model_id}")
    agent.model.update_config(model_id=model_id)
    return f"Model updated to {model_id}"


@tool
def update_temperature(temperature: float, agent: Agent) -> str:
    """
    Update the temperature of the agent

    Args:
      temperature: Temperature value for the model to use.
    """
    print(f"Updating Temperature to {temperature}")
    agent.model.update_config(temperature=temperature)
    return f"Temperature updated to {temperature}"
```

### Reasoning Support

Amazon Bedrock models can provide detailed reasoning steps when generating responses. For detailed information about supported models and reasoning token configuration, see the [Amazon Bedrock documentation on inference reasoning](https://docs.aws.amazon.com/bedrock/latest/userguide/inference-reasoning.html).

Strands allows you to enable and configure reasoning capabilities with your [`BedrockModel`](../../../api-reference/models.md#strands.models.bedrock):

```python
from strands import Agent
from strands.models import BedrockModel

# Create a Bedrock model with reasoning configuration
bedrock_model = BedrockModel(
    model_id="anthropic.claude-sonnet-4-20250514-v1:0",
    additional_request_fields={
        "thinking": {
            "type": "enabled",
            "budget_tokens": 4096 # Minimum of 1,024
        }
    }
)

# Create an agent with the reasoning-enabled model
agent = Agent(model=bedrock_model)

# Ask a question that requires reasoning
response = agent("If a train travels at 120 km/h and needs to cover 450 km, how long will the journey take?")
```

> **Note**: Not all models support structured reasoning output. Check the [inference reasoning documentation](https://docs.aws.amazon.com/bedrock/latest/userguide/inference-reasoning.html) for details on supported models.

### Structured Output

Amazon Bedrock models support structured output through their tool calling capabilities. When you use [`Agent.structured_output()`](../../../api-reference/agent.md#strands.agent.agent.Agent.structured_output), the Strands SDK converts your Pydantic models to Bedrock's tool specification format.

```python
from pydantic import BaseModel, Field
from strands import Agent
from strands.models import BedrockModel
from typing import List, Optional

class ProductAnalysis(BaseModel):
    """Analyze product information from text."""
    name: str = Field(description="Product name")
    category: str = Field(description="Product category")
    price: float = Field(description="Price in USD")
    features: List[str] = Field(description="Key product features")
    rating: Optional[float] = Field(description="Customer rating 1-5", ge=1, le=5)

bedrock_model = BedrockModel()

agent = Agent(model=bedrock_model)

result = agent.structured_output(
    ProductAnalysis,
    """
    Analyze this product: The UltraBook Pro is a premium laptop computer
    priced at $1,299. It features a 15-inch 4K display, 16GB RAM, 512GB SSD,
    and 12-hour battery life. Customer reviews average 4.5 stars.
    """
)

print(f"Product: {result.name}")
print(f"Category: {result.category}")
print(f"Price: ${result.price}")
print(f"Features: {result.features}")
print(f"Rating: {result.rating}")
```

## Troubleshooting

### Model access issue

If you encounter the following error:

> You don't have access to the model with the specified model ID

This may indicate that the model is not enabled in your Amazon Bedrock account for the specified region. To resolve this issue follow the [instructions above](#requesting-access-to-bedrock-models) to request access to the model

### On-demand throughput isn’t supported

If you encounter the error:

> Invocation of model ID XXXX with on-demand throughput isn’t supported. Retry your request with the ID or ARN of an inference profile that contains this model.

This typically indicates that the model requires Cross-Region Inference, as documented in the [Amazon Bedrock documentation on inference profiles](https://docs.aws.amazon.com/bedrock/latest/userguide/inference-profiles-support.html#inference-profiles-support-system).  To resolve this issue, prefix your model ID with the appropriate regional identifier (`us.`or `eu.`) based on where your agent is running. For example:

Instead of: 

```
anthropic.claude-sonnet-4-20250514-v1:0
```

Use: 

```
us.anthropic.claude-sonnet-4-20250514-v1:0
```

## Related Resources

- [Amazon Bedrock Documentation](https://docs.aws.amazon.com/bedrock/)
- [Bedrock Model IDs Reference](https://docs.aws.amazon.com/bedrock/latest/userguide/model-ids.html)
- [Bedrock Pricing](https://aws.amazon.com/bedrock/pricing/)
