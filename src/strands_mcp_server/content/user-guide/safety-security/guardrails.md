# Guardrails

Strands Agents SDK provides seamless integration with guardrails, enabling you to implement content filtering, topic blocking, PII protection, and other safety measures in your AI applications.

## What Are Guardrails?

Guardrails are safety mechanisms that help control AI system behavior by defining boundaries for content generation and interaction. They act as protective layers that:

1. **Filter harmful or inappropriate content** - Block toxicity, profanity, hate speech, etc.
2. **Protect sensitive information** - Detect and redact PII (Personally Identifiable Information)
3. **Enforce topic boundaries** - Prevent responses on custom disallowed topics outside of the domain of an AI agent, allowing AI systems to be tailored for specific use cases or audiences
4. **Ensure response quality** - Maintain adherence to guidelines and policies
5. **Enable compliance** - Help meet regulatory requirements for AI systems
6. **Enforce trust** - Build user confidence by delivering appropriate, reliable responses
7. **Manage Risk** - Reduce legal and reputational risks associated with AI deployment

## Guardrails in Different Model Providers

Strands Agents SDK allows integration with different model providers, which implement guardrails differently.

### Amazon Bedrock

Amazon Bedrock provides a [built-in guardrails framework](https://docs.aws.amazon.com/bedrock/latest/userguide/guardrails.html) that integrates directly with Strands Agents SDK. If a guardrail is triggered, the Strands Agents SDK will automatically overwrite the user's input in the conversation history. This is done so that follow-up questions are not also blocked by the same questions. This can be configured with the `guardrail_redact_input` boolean, and the `guardrail_redact_input_message` string to change the overwrite message. Additionally, the same functionality is built for the model's output, but this is disabled by default. You can enable this with the `guardrail_redact_output` boolean, and change the overwrite message with the `guardrail_redact_output_message` string. Below is an example of how to leverage Bedrock guardrails in your code:

```python
import json
from strands import Agent
from strands.models import BedrockModel

# Create a Bedrock model with guardrail configuration
bedrock_model = BedrockModel(
    model_id="anthropic.claude-3-5-sonnet-20241022-v2:0",
    guardrail_id="your-guardrail-id",         # Your Bedrock guardrail ID
    guardrail_version="1",                    # Guardrail version
    guardrail_trace="enabled",                # Enable trace info for debugging
)

# Create agent with the guardrail-protected model
agent = Agent(
    system_prompt="You are a helpful assistant.",
    model=bedrock_model,
)

# Use the protected agent for conversations
response = agent("Tell me about financial planning.")

# Handle potential guardrail interventions
if response.stop_reason == "guardrail_intervened":
    print("Content was blocked by guardrails, conversation context overwritten!")

print(f"Conversation: {json.dumps(agent.messages, indent=4)}")
```

### Ollama

Ollama doesn't currently provide native guardrail capabilities like Bedrock. Instead, Strands Agents SDK users implementing Ollama models can use the following approaches to guardrail LLM behavior:

- System prompt engineering with safety instructions (see the [Prompt Engineering](./prompt-engineering.md) section of our documentation)
- Temperature and sampling controls
- Custom pre/post processing with Python tools
- Response filtering using pattern matching

## Additional Resources

* [Amazon Bedrock Guardrails Documentation](https://docs.aws.amazon.com/bedrock/latest/userguide/guardrails.html)
* [Allen Institute for AI: Guardrails Project](https://www.guardrailsai.com/docs)