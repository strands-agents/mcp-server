from typing import Any, Dict, List

from mcp.server.fastmcp import FastMCP

from .prompts import (
    generate_agent_prompt,
    generate_model_prompt,
    generate_multiagent_prompt,
    generate_session_prompt,
    generate_tool_prompt,
)
from .utils import cache, text_processor

APP_NAME = "strands-agents-mcp-server"
mcp = FastMCP(APP_NAME)


@mcp.tool()
def search_docs(query: str, k: int = 5) -> List[Dict[str, Any]]:
    """Search curated documentation and return ranked results with snippets.

    This tool provides access to the complete Strands Agents documentation including:

    **User Guide Topics:**
    - Agent concepts (agent loop, conversation management, hooks, prompts, state)
    - Model providers (Amazon Bedrock, Anthropic, Cohere, LiteLLM, LlamaAPI,
            MistralAI, Ollama, OpenAI, SageMaker, Writer, Gemini)
    - Multi-agent patterns (Agent2Agent, Agents as Tools, Graph, Swarm, Workflow)
    - Tools (Python tools, MCP tools, community tools, executors)
    - Deployment guides (EC2, EKS, Fargate, Lambda, Bedrock AgentCore)
    - Observability & evaluation (logs, metrics, traces, evaluation)
    - Safety & security (guardrails, PII redaction, responsible AI)

    **API Reference:**
    - Complete API documentation for Agent, Models, Tools, Handlers, etc.

    **Examples:**
    - Code samples and implementation examples

    Use this to find relevant Strands Agents documentation for any development question.

    Args:
        query: Search query string (e.g., "bedrock model", "tell me about a2a", "how to use MCP tools")
        k: Maximum number of results to return (default: 5)

    Returns:
        List of dictionaries containing:
        - url: Document URL
        - title: Display title
        - score: Relevance score (0-1, higher is better)
        - snippet: Contextual content preview

    """
    cache.ensure_ready()
    index = cache.get_index()
    results = index.search(query, k=k) if index else []
    url_cache = cache.get_url_cache()

    # Collect top-k URLs that need hydration (no content yet)
    # Simplified: Direct hydration in one pass
    top = results[: min(len(results), cache.SNIPPET_HYDRATE_MAX)]
    for _, doc in top:
        cached = url_cache.get(doc.uri)
        if cached is None or not cached.content:
            cache.ensure_page(doc.uri)

    # Build response with real content snippets when available
    return_docs: List[Dict[str, Any]] = []
    for score, doc in results:
        page = url_cache.get(doc.uri)
        snippet = text_processor.make_snippet(page, doc.display_title)
        return_docs.append(
            {
                "url": doc.uri,
                "title": doc.display_title,
                "score": round(score, 3),
                "snippet": snippet,
            }
        )
    return return_docs


@mcp.prompt()
def strands_tool_development(request: str, tool_use_examples: str = "", preferred_libraries: str = "") -> str:
    """Generate a design-first prompt for developing Strands tools.

    This prompt guides the development process through:
    1. Understanding the user's requirements
    2. Designing the tool interface first
    3. Getting user approval on the design
    4. Implementing the full tool code

    The workflow ensures clear communication and agreement before implementation.

    Args:
        request: Description of the tool functionality needed
        tool_use_examples: Examples of how the tool will be used (optional)
        preferred_libraries: Specific libraries or APIs to use (optional)

    Returns:
        A structured prompt for design-first tool development
    """
    return generate_tool_prompt(request, tool_use_examples, preferred_libraries)


@mcp.prompt()
def strands_agent_development(
    use_case: str, examples: str = "", agent_guidelines: str = "", tools_required: str = "", model_preferences: str = ""
) -> str:
    """Generate a design-first prompt for developing Strands agents with comprehensive guidelines.

    This prompt guides agent development through:
    1. Understanding the requirements
    2. Designing the agent architecture first (system prompt, tools, model)
    3. Getting user approval on the design
    4. Implementing the full agent code

    The workflow ensures proper agent design with:
    - Effective system prompt development
    - Strategic tool selection
    - Appropriate model provider choice
    - Session and state management planning

    Args:
        use_case: Description of what the agent should do (e.g., "research assistant for academic papers")
        examples: Optional examples of expected agent behavior or interactions
        agent_guidelines: Optional specific behavioral guidelines or constraints for the agent
        tools_required: Optional list of specific tools or capabilities the agent must have
        model_preferences: Optional preferences for model provider or specific models

    Returns:
        A structured prompt for design-first agent development
    """
    return generate_agent_prompt(
        use_case=use_case,
        examples=examples,
        agent_guidelines=agent_guidelines,
        tools_required=tools_required,
        model_preferences=model_preferences,
        include_examples=bool(examples),
        verbosity="normal",
    )


@mcp.prompt()
def strands_session_management(request: str, include_examples: bool = True) -> str:
    """Generate a design-first prompt for implementing Strands session management.

    This prompt guides the implementation of session management through:
    1. Understanding the session requirements
    2. Designing the session architecture first
    3. Getting user approval on the design
    4. Implementing the full session management code

    Session management enables:
    - Stateful conversations with memory
    - Multi-turn interactions with context
    - Persistent conversation history
    - Session lifecycle management
    - Custom storage backends

    Args:
        request: Description of the session management needs
        include_examples: Include usage examples (default: True)

    Returns:
        A structured prompt for design-first session implementation
    """
    return generate_session_prompt(request, include_examples)


@mcp.prompt()
def strands_model_development(
    use_case: str,
    model_details: str = "",
    api_documentation: str = "",
    auth_requirements: str = "",
    special_features: str = "",
) -> str:
    """Generate a design-first prompt for developing custom Strands model providers.

    This prompt guides the development of custom model providers through:
    1. Understanding the model integration requirements
    2. Designing the provider architecture first (auth, API format, features)
    3. Getting user approval on the design
    4. Implementing the full model provider code

    Custom model providers enable:
    - Integration with proprietary LLM services
    - Custom inference endpoints
    - Specialized model configurations
    - Organization-specific authentication
    - Advanced features (streaming, function calling, embeddings)

    Args:
        use_case: Description of the model provider's purpose (e.g., "integrate our company's custom LLM API")
        model_details: Optional details about the models to support (versions, capabilities, endpoints)
        api_documentation: Optional reference to API documentation or endpoint specifications
        auth_requirements: Optional authentication/authorization requirements (API keys, OAuth, custom)
        special_features: Optional special capabilities needed (streaming, function calling, embeddings)

    Returns:
        A structured prompt for design-first model provider development
    """
    return generate_model_prompt(
        use_case=use_case,
        model_details=model_details,
        api_documentation=api_documentation,
        auth_requirements=auth_requirements,
        special_features=special_features,
        include_examples=True,
    )


@mcp.prompt()
def strands_multiagent_development(
    use_case: str,
    pattern: str = "",
    agent_roles: str = "",
    interaction_requirements: str = "",
    scale_requirements: str = "",
) -> str:
    """Generate a design-first prompt for developing multi-agent systems with Strands.

    This prompt guides the development of multi-agent systems through:
    1. Understanding why multi-agent is needed for the use case
    2. Choosing between Graph (structured) vs Swarm (autonomous) patterns
    3. Designing the agent architecture and interactions first
    4. Getting user approval on the design
    5. Implementing the full multi-agent system

    Multi-agent systems enable:
    - **Cognitive Load Distribution**: Break complex tasks into specialized sub-tasks
    - **Parallel Processing**: Execute independent tasks simultaneously
    - **Specialized Expertise**: Agents with different prompts, tools, and models
    - **Fault Tolerance**: Isolated failure domains with graceful degradation
    - **Emergent Intelligence**: Collective problem-solving beyond individual capabilities

    Pattern Selection Guide:
    - **Graph**: Use for structured workflows, ETL pipelines, approval chains
    - **Swarm**: Use for creative problem-solving, research, collaborative analysis
    - **Hybrid**: Combine Graph structure with Swarm nodes for complex sub-tasks

    Args:
        use_case: Description of what the multi-agent system should accomplish
        pattern: Preferred pattern - "graph", "swarm", or "hybrid" (optional, will guide selection if not specified)
        agent_roles: Description of the different agent roles and specializations needed (optional)
        interaction_requirements: How agents should interact and collaborate (optional)
        scale_requirements: Performance, reliability, and scalability requirements (optional)

    Returns:
        A structured prompt for design-first multi-agent system development
    """
    return generate_multiagent_prompt(
        use_case=use_case,
        pattern=pattern,
        agent_roles=agent_roles,
        interaction_requirements=interaction_requirements,
        scale_requirements=scale_requirements,
        include_examples=True,
    )


@mcp.tool()
def fetch_doc(uri: str = "") -> Dict[str, Any]:
    """Fetch full document content by URL.

    Retrieves complete Strands Agents documentation content from URLs found via search_docs
    or provided directly. Use this to get full documentation pages including:

    - Complete user guides with code examples
    - Detailed API reference documentation
    - Step-by-step tutorials and implementation guides
    - Full deployment and configuration instructions
    - Comprehensive multi-agent pattern examples
    - Complete model provider setup guides

    This provides the full content when search snippets aren't sufficient for
    understanding or implementing Strands Agents features.

    Args:
        uri: Document URI (supports http/https URLs). If empty, returns all available URLs.

    Returns:
        Dictionary containing:
        - url: Canonical document URL
        - title: Document title
        - content: Full document text content
        - error: Error message (if fetch failed)

        Or when uri is empty:
        - urls: List of all available document URLs with titles

    """
    cache.ensure_ready()

    # If no URI provided, return all available URLs (llms.txt catalog)
    if not uri:
        url_titles = cache.get_url_titles()
        return {"urls": [{"url": url, "title": title} for url, title in url_titles.items()]}
    # Only accept https://strandsagents.com URLs
    if not uri.startswith("https://strandsagents.com"):
        return {"error": "only https://strandsagents.com URLs allowed", "url": uri}

    url = uri

    page = cache.ensure_page(url)
    if page is None:
        return {"error": "fetch failed", "url": url}

    return {
        "url": url,
        "title": page.title,
        "content": page.content,
    }


def main() -> None:
    """Main entry point for the MCP server.

    Initializes the document cache and starts the FastMCP server.
    The cache is loaded with document titles only for fast startup,
    with full content fetched on-demand.
    """
    cache.ensure_ready()
    mcp.run()
