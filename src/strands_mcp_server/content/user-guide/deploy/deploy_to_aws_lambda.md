# Deploying Strands Agents SDK Agents to AWS Lambda

AWS Lambda is a serverless compute service that lets you run code without provisioning or managing servers. This makes it an excellent choice for deploying Strands Agents SDK agents because you only pay for the compute time you consume and don't need to manage hosts or servers.

If you're not familiar with the AWS CDK, check out the [official documentation](https://docs.aws.amazon.com/cdk/v2/guide/home.html).

This guide discusses Lambda integration at a high level - for a complete example project deploying to Lambda, check out the [`deploy_to_lambda` sample project on GitHub][project_code].

!!! note

    This Lambda deployment example does not implement response streaming as described in the [Async Iterators for Streaming](../concepts/streaming/async-iterators.md) documentation. If you need streaming capabilities, consider using the [AWS Fargate deployment](deploy_to_aws_fargate.md) approach which does implement streaming responses.

## Creating Your Agent in Python

The core of your Lambda deployment is the agent handler code. This Python script initializes your Strands Agents SDK agent and processes incoming requests. 

The Lambda handler follows these steps:

1. Receive an event object containing the input prompt
2. Create a Strands Agents SDK agent with the specified system prompt and tools
3. Process the prompt through the agent
4. Extract the text from the agent's response
5. Format and return the response back to the client

Here's an example of a weather forecasting agent handler ([`agent_handler.py`][agent_handler]):

```python
from strands import Agent
from strands_tools import http_request
from typing import Dict, Any

# Define a weather-focused system prompt
WEATHER_SYSTEM_PROMPT = """You are a weather assistant with HTTP capabilities. You can:

1. Make HTTP requests to the National Weather Service API
2. Process and display weather forecast data
3. Provide weather information for locations in the United States

When retrieving weather information:
1. First get the coordinates or grid information using https://api.weather.gov/points/{latitude},{longitude} or https://api.weather.gov/points/{zipcode}
2. Then use the returned forecast URL to get the actual forecast

When displaying responses:
- Format weather data in a human-readable way
- Highlight important information like temperature, precipitation, and alerts
- Handle errors appropriately
- Convert technical terms to user-friendly language

Always explain the weather conditions clearly and provide context for the forecast.
"""

# The handler function signature `def handler(event, context)` is what Lambda
# looks for when invoking your function.
def handler(event: Dict[str, Any], _context) -> str:
    weather_agent = Agent(
        system_prompt=WEATHER_SYSTEM_PROMPT,
        tools=[http_request],
    )

    response = weather_agent(event.get('prompt'))
    return str(response)
```

## Infrastructure

To deploy the above agent to Lambda using the TypeScript CDK, prepare your code for deployment by creating the Lambda definition and an associated Lambda layer ([`AgentLambdaStack.ts`][AgentLambdaStack]):

```typescript
const packagingDirectory = path.join(__dirname, "../packaging");
const zipDependencies = path.join(packagingDirectory, "dependencies.zip");
const zipApp = path.join(packagingDirectory, "app.zip");

// Create a lambda layer with dependencies
const dependenciesLayer = new lambda.LayerVersion(this, "DependenciesLayer", {
  code: lambda.Code.fromAsset(zipDependencies),
  compatibleRuntimes: [lambda.Runtime.PYTHON_3_12],
  description: "Dependencies needed for agent-based lambda",
});

// Define the Lambda function
const weatherFunction = new lambda.Function(this, "AgentLambda", {
  runtime: lambda.Runtime.PYTHON_3_12,
  functionName: "AgentFunction",
  handler: "agent_handler.handler",
  code: lambda.Code.fromAsset(zipApp),
  timeout: Duration.seconds(30),
  memorySize: 128,
  layers: [dependenciesLayer],
  architecture: lambda.Architecture.ARM_64,
});

// Add permissions for Bedrock apis
weatherFunction.addToRolePolicy(
  new iam.PolicyStatement({
    actions: ["bedrock:InvokeModel", "bedrock:InvokeModelWithResponseStream"],
    resources: ["*"],
  }),
);
```

The dependencies are packaged and pulled in via a Lambda layer separately from the application code. By separating your dependencies into a layer, your application code remains small and enables you to view or edit your function code directly in the Lambda console.

!!! info "Installing Dependencies with the Correct Architecture"
    
    When deploying to AWS Lambda, it's important to install dependencies that match the target Lambda architecture. Because the example above uses ARM64 architecture, dependencies must be installed specifically for this architecture:
    
    ```shell
    # Install Python dependencies for lambda with correct architecture
    pip install -r requirements.txt \
        --python-version 3.12 \
        --platform manylinux2014_aarch64 \
        --target ./packaging/_dependencies \
        --only-binary=:all:
    ```
    
    This ensures that all binary dependencies are compatible with the Lambda ARM64 environment regardless of the operating-system used for development.

    Failing to match the architecture can result in runtime errors when the Lambda function executes.

### Packaging Your Code

The CDK constructs above expect the Python code to be packaged before running the deployment - this can be done using a Python script that creates two ZIP files ([`package_for_lambda.py`][package_for_lambda]):

```python
def create_lambda_package():
    current_dir = Path.cwd()
    packaging_dir = current_dir / "packaging"

    app_dir = current_dir / "lambda"
    app_deployment_zip = packaging_dir / "app.zip"

    dependencies_dir = packaging_dir / "_dependencies"
    dependencies_deployment_zip = packaging_dir / "dependencies.zip"
    
    # ...
    
    with zipfile.ZipFile(dependencies_deployment_zip, 'w', zipfile.ZIP_DEFLATED) as zipf:
        for root, _, files in os.walk(dependencies_dir):
            for file in files:
                file_path = os.path.join(root, file)
                arcname = Path("python") / os.path.relpath(file_path, dependencies_dir)
                zipf.write(file_path, arcname)

    with zipfile.ZipFile(app_deployment_zip, 'w', zipfile.ZIP_DEFLATED) as zipf:
        for root, _, files in os.walk(app_dir):
            for file in files:
                file_path = os.path.join(root, file)
                arcname = os.path.relpath(file_path, app_dir)
                zipf.write(file_path, arcname)
```

This approach gives you full control over where your app code lives and how you want to package it.

## Deploying Your Agent & Testing

Assuming that Python & Node dependencies are already installed, package up the assets, run the CDK and deploy:

```bash
python ./bin/package_for_lambda.py

# Bootstrap your AWS environment (if not already done)
npx cdk bootstrap
# Deploy the stack
npx cdk deploy
```

Once fully deployed, testing can be done by hitting the lambda using the AWS CLI:

```bash
aws lambda invoke --function-name AgentFunction \
  --region us-east-1 \
  --cli-binary-format raw-in-base64-out \
  --payload '{"prompt": "What is the weather in Seattle?"}' \
  output.json

# View the formatted output
jq -r '.' ./output.json
```

## Summary

The above steps covered:

 - Creating a Python handler that Lambda invokes to trigger an agent
 - Creating the CDK infrastructure to deploy to Lambda
 - Packaging up the Lambda handler and dependencies 
 - Deploying the agent and infrastructure to an AWS account
 - Manually testing the Lambda function  

Possible follow-up tasks would be to:

  - Set up a CI/CD pipeline to automate the deployment process
  - Configure the CDK stack to use a [Lambda function URL](https://docs.aws.amazon.com/lambda/latest/dg/urls-configuration.html) or add an [API Gateway](https://docs.aws.amazon.com/apigateway/latest/developerguide/welcome.html) to invoke the HTTP Lambda on a REST request.

## Complete Example

For the complete example code, including all files and configurations, see the [`deploy_to_lambda` sample project on GitHub][project_code].

## Related Resources

- [AWS Lambda Documentation](https://docs.aws.amazon.com/lambda/latest/dg/welcome.html)
- [AWS CDK Documentation](https://docs.aws.amazon.com/cdk/latest/guide/home.html)
- [Amazon Bedrock Documentation](https://docs.aws.amazon.com/bedrock/)

[project_code]: {{ docs_repo }}/docs/examples/cdk/deploy_to_lambda
[agent_handler]: {{ docs_repo }}/docs/examples/cdk/deploy_to_lambda/lambda/agent_handler.py
[AgentLambdaStack]: {{ docs_repo }}/docs/examples/cdk/deploy_to_lambda/lib/agent-lambda-stack.ts
[package_for_lambda]: {{ docs_repo }}/docs/examples/cdk/deploy_to_lambda/bin/package_for_lambda.py