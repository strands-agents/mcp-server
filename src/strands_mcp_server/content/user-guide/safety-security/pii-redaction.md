# PII Redaction 
PII redaction is a critical aspect of protecting personal information. This document provides clear instructions and recommended practices for safely handling PII, including guidance on integrating third-party redaction solutions with Strands SDK.

## What is PII Redaction
Personally Identifiable Information (PII) is defined as: Information that can be used to distinguish or trace an individual’s identity, either alone or when combined with other information that is linked or linkable to a specific individual.

PII Redaction is the process of identifying, removing, or obscuring sensitive information from telemetry data before storage or transmission to prevent potential privacy violations and to ensure regulatory compliance.

## Why do you need PII redaction?
Integrating PII redaction is crucial for:

* **Privacy Compliance**: Protecting users' sensitive information and ensuring compliance with global data privacy regulations.

* **Security: Reducing**: the risk of data breaches and unauthorized exposure of personal information.

* **Operational Safety**: Maintaining safe data handling practices within applications and observability platforms.

## How to implement PII Redaction

Strands SDK does not natively perform PII redaction within its core telemetry generation but recommends two effective ways to achieve PII masking:
### Option 1: Using Third-Party Specialized Libraries [Recommended]
Leverage specialized external libraries like Langfuse, LLM Guard, Presidio, or AWS Comprehend for high-quality PII detection and redaction:
#### Step-by-Step Integration Guide
##### Step 1: Install your chosen PII Redaction Library.
Example with [LLM Guard](https://protectai.com/llm-guard):
````
pip install llm-guard
````
##### Step2: Import necessary modules and initialize the Vault and Anonymize scanner.
````
from llm_guard.vault import Vault
from llm_guard.input_scanners import Anonymize
from llm_guard.input_scanners.anonymize_helpers import BERT_LARGE_NER_CONF

vault = Vault()

# Create anonymize scanner
def create_anonymize_scanner():
    scanner = Anonymize(
        vault,
        recognizer_conf=BERT_LARGE_NER_CONF,
        language="en"
    )
    return scanner
````
##### Step3: Define a masking function using the anonymize scanner.
````
def masking_function(data, **kwargs):
    if isinstance(data, str):
        scanner = create_anonymize_scanner()
        sanitized_data, is_valid, risk_score = scanner.scan(data)
        return sanitized_data
    return data
````
##### Step4: Configure the masking function in Observability platform, eg., Langfuse.
````
from langfuse import Langfuse, observe

langfuse = Langfuse(mask=masking_function)
````
##### Step5: Create a sample function with PII.
````
@observe()
def generate_report():
    report = "John Doe met with Jane Smith to discuss the project."
    return report

result = generate_report()
print(result)
# Output: [REDACTED_PERSON] met with [REDACTED_PERSON] to discuss the project.

langfuse.flush()
````


### Option 2: Using OpenTelemetry Collector Configuration [Collector-level Masking]
Implement PII masking directly at the collector level, which is ideal for centralized control.
#### Example code:
1. Edit your collector configuration (eg., otel-collector-config.yaml):
````
processors:
  attributes/pii:
    actions:
      - key: user.email
        action: delete
      - key: http.url
        regex: '(\?|&)(token|password)=([^&]+)'
        action: update
        value: '[REDACTED]'

service:
  pipelines:
    traces:
      processors: [attributes/pii]
````
2. Deploy or restart your OTEL collector with the updated configuration.
#### Example:
##### Before:
````
{
"user.email": "user@example.com",
"http.url": "https://example.com?token=abc123"
}
````
#### After:
````
{
  "http.url": "https://example.com?token=[REDACTED]"
}
````

## Additional Resources
* [PII definition](https://www.dol.gov/general/ppii)
* [OpenTelemetry official docs](https://opentelemetry.io/docs/collector/transforming-telemetry/)
* [LLM Guard](https://protectai.com/llm-guard)