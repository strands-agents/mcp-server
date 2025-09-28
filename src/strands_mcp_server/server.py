from typing import Any, Dict, List

from mcp.server.fastmcp import FastMCP

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


@mcp.tool()
def fetch_doc(uri: str) -> Dict[str, Any]:
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
        uri: Document URI (supports http/https URLs)

    Returns:
        Dictionary containing:
        - url: Canonical document URL
        - title: Document title
        - content: Full document text content
        - error: Error message (if fetch failed)

    """
    cache.ensure_ready()

    # Accept HTTP/HTTPS URLs
    if uri.startswith("http://") or uri.startswith("https://"):
        url = uri
    else:
        return {"error": "unsupported uri", "url": uri}

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
