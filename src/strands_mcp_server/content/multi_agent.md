# Multi-Agent Systems in Strands

Multi-agent systems in Strands enable coordinated collaboration between multiple AI agents to solve complex tasks that would be difficult for a single agent. Strands provides several patterns for implementing multi-agent systems, each with its own strengths and use cases.

## Multi-Agent Patterns

Strands offers four main patterns for multi-agent orchestration:

### 1. Agents as Tools

The "Agents as Tools" pattern creates a hierarchy where specialized agents are wrapped as callable tools for other agents:

```python
from strands import Agent, tool

@tool
def research_assistant(query: str) -> str:
    """Process and respond to research-related queries."""
    research_agent = Agent(
        system_prompt="You are a specialized research assistant...",
        tools=[retrieve, http_request]
    )
    return str(research_agent(query))

# Orchestrator agent uses specialized agents as tools
orchestrator = Agent(
    system_prompt="Route queries to the appropriate specialized agent...",
    tools=[research_assistant, product_recommendation_assistant]
)
```

**Key benefits:**
- Clear separation of concerns with focused specialist agents
- Hierarchical delegation through an orchestrator agent
- Modular architecture for easy system expansion
- Optimized performance through specialized system prompts

### 2. Graph Pattern

Graphs provide deterministic execution of agent workflows using a Directed Acyclic Graph (DAG):

```python
from strands import Agent
from strands.multiagent import GraphBuilder

# Create specialized agents
researcher = Agent(name="researcher", system_prompt="You are a research specialist...")
analyst = Agent(name="analyst", system_prompt="You are a data analysis specialist...")
report_writer = Agent(name="report_writer", system_prompt="You are a report specialist...")

# Build the graph
builder = GraphBuilder()
builder.add_node(researcher, "research")
builder.add_node(analyst, "analysis")
builder.add_node(report_writer, "report")

# Add edges (dependencies)
builder.add_edge("research", "analysis")
builder.add_edge("analysis", "report")

# Build and execute the graph
graph = builder.build()
result = graph("Research the impact of AI on healthcare")
```

**Key features:**
- Deterministic execution order based on dependencies
- Clear propagation of outputs along edges
- Support for conditional edge traversal
- Ability to nest other multi-agent patterns within nodes

### 3. Swarm Pattern

Swarms enable autonomous, self-organizing agent teams with shared working memory:

```python
from strands import Agent
from strands.multiagent import Swarm

# Create specialized agents
researcher = Agent(name="researcher", system_prompt="You are a research specialist...")
coder = Agent(name="coder", system_prompt="You are a coding specialist...")
reviewer = Agent(name="reviewer", system_prompt="You are a code review specialist...")

# Create and execute a swarm
swarm = Swarm(
    [researcher, coder, reviewer],
    max_handoffs=20,
    execution_timeout=900.0  # 15 minutes
)
result = swarm("Design and implement a simple REST API")
```

**Key features:**
- Autonomous agent coordination through handoffs
- Shared context and working memory
- Dynamic task distribution based on agent expertise
- Built-in safety mechanisms to prevent infinite loops

### 4. Workflow Pattern

Workflows provide structured coordination of tasks across agents with explicit dependency management:

```python
from strands import Agent
from strands_tools import workflow

# Create an agent with workflow capability
agent = Agent(tools=[workflow])

# Create a multi-agent workflow
agent.tool.workflow(
    action="create",
    workflow_id="data_analysis",
    tasks=[
        {
            "task_id": "data_extraction",
            "description": "Extract key financial data",
            "system_prompt": "You extract financial data from reports."
        },
        {
            "task_id": "trend_analysis",
            "description": "Analyze trends in the data",
            "dependencies": ["data_extraction"],
            "system_prompt": "You identify trends in financial time series."
        },
        {
            "task_id": "report_generation",
            "description": "Generate an analysis report",
            "dependencies": ["trend_analysis"],
            "system_prompt": "You create financial analysis reports."
        }
    ]
)

# Execute workflow
agent.tool.workflow(action="start", workflow_id="data_analysis")
```

**Key features:**
- Structured task definition and distribution
- Explicit dependency management
- Parallel execution of independent tasks
- State management and context preservation

## Agent-to-Agent (A2A) Protocol Integration

Strands supports the Agent-to-Agent (A2A) protocol, enabling interoperability with external agent systems:

```python
from strands import Agent
from strands.multiagent.a2a import A2AServer
from strands_tools.calculator import calculator

# Create a Strands agent
agent = Agent(
    name="Calculator Agent",
    description="A calculator agent for arithmetic operations.",
    tools=[calculator]
)

# Create and start A2A server
a2a_server = A2AServer(agent=agent)
a2a_server.serve()  # Runs on port 9000 by default
```

A2A protocol enables:
- Cross-platform agent communication
- Agent discovery and collaboration
- Distributed AI systems
- Streaming responses between agents

## Choosing the Right Multi-Agent Pattern

| Pattern | Best For | Structure | Control Flow |
|---------|----------|-----------|-------------|
| **Agents as Tools** | Hierarchical delegation with a clear orchestrator | Wrapper functions | Top-down |
| **Graph** | Processes with explicit dependencies | Directed Acyclic Graph | Deterministic |
| **Swarm** | Collaborative problem-solving with dynamic handoffs | Network | Self-organizing |
| **Workflow** | Multi-step processes with clear sequences | Task definitions | Structured |

## Advanced Features

### Multi-Modal Support

All multi-agent patterns support multi-modal inputs like text and images:

```python
from strands.types.content import ContentBlock

content_blocks = [
    ContentBlock(text="Analyze this image:"),
    ContentBlock(image={"format": "png", "source": {"bytes": image_bytes}}),
]

result = multi_agent_system(content_blocks)
```

### Conditional Logic

Graphs support conditional edge traversal for dynamic workflows:

```python
def only_if_research_successful(state):
    research_node = state.results.get("research")
    result_text = str(research_node.result)
    return "successful" in result_text.lower()

builder.add_edge("research", "analysis", condition=only_if_research_successful)
```

### Asynchronous Execution

All multi-agent patterns support asynchronous execution:

```python
import asyncio

async def run_async():
    result = await multi_agent_system.invoke_async("Process this complex task")
    return result

result = asyncio.run(run_async())
```

### Tool Integration

You can use multi-agent patterns as tools in other agents:

```python
from strands_tools import agent_graph, swarm

agent = Agent(tools=[agent_graph, swarm])
agent("Design a system using multiple specialized agents")
```

## Best Practices

1. **Clear Agent Specialization**: Define clear roles and responsibilities for each agent
2. **Appropriate Pattern Selection**: Choose the pattern that best matches your problem structure
3. **Effective System Prompts**: Craft specialized prompts for each agent's role
4. **Error Handling**: Implement proper error handling and safety mechanisms
5. **Context Management**: Ensure proper context passing between agents
6. **Performance Optimization**: Configure timeouts and resource limits appropriately
7. **Testing and Evaluation**: Validate multi-agent systems against simpler approaches