"""Prompt generation system for Strands development.

This module combines Agent SOPs with dynamically fetched Strands documentation
to create comprehensive prompts for various development tasks.

Architecture:
    - Agent SOPs (from strands-agents-sops): Provide structured workflows,
      constraints, and best practices for development tasks
    - Dynamic Content (from strandsagents.com): Up-to-date documentation
      specific to each development area
    - Jinja2 Templates: Format the dynamic documentation content

Pattern: sop_with_input(dynamic_documentation)
"""

import re
from pathlib import Path

import jinja2
from strands_agents_sops import code_assist_with_input

from .utils import cache

# Initialize Jinja2 environment for formatting dynamic content
template_dir = Path(__file__).parent / "prompts"
jinja_env = jinja2.Environment(
    loader=jinja2.FileSystemLoader(template_dir), trim_blocks=True, lstrip_blocks=True, autoescape=False
)


def regex_replace_filter(text: str, pattern: str, replacement: str = "") -> str:
    """Custom Jinja2 filter for regex replacement.

    Args:
        text: The text to process
        pattern: The regex pattern to match
        replacement: The replacement string (default: empty string)

    Returns:
        Text with pattern replaced
    """
    if not text:
        return text
    return re.sub(pattern, replacement, text, flags=re.DOTALL)


# Add custom filters to Jinja environment
jinja_env.filters["regex_replace"] = regex_replace_filter


def fetch_content(url: str) -> str:
    """Fetch content from documentation URL using cache.

    Args:
        url: URL to fetch content from

    Returns:
        Content string or empty string if fetch fails
    """
    cache.ensure_ready()
    page = cache.ensure_page(url)
    if page and page.content:
        return page.content
    return ""


# ============================================================================
# PROMPT GENERATORS - SOP + Dynamic Documentation Pattern
# ============================================================================


def generate_tool_prompt(request: str, tool_use_examples: str = "", preferred_libraries: str = "") -> str:
    """Generate a design-first tool development prompt with dynamic documentation.

    Combines the code-assist SOP workflow with Strands-specific tool documentation.

    Args:
        request: Description of the tool functionality needed
        tool_use_examples: Examples of how the tool will be used (optional)
        preferred_libraries: Specific libraries or APIs to use (optional)

    Returns:
        Generated prompt combining SOP instructions with Strands documentation
    """
    cache.ensure_ready()

    # Fetch documentation
    llms_txt_url = "https://strandsagents.com/llms.txt"
    llms_txt_content = fetch_content(llms_txt_url)

    python_tools_url = (
        "https://strandsagents.com/latest/documentation/docs/user-guide/concepts/tools/python-tools/index.md"
    )
    python_tools_content = fetch_content(python_tools_url)

    # Load and render template for dynamic content
    template = jinja_env.get_template("tool_development.jinja2")
    dynamic_content = template.render(
        request=request,
        tool_use_examples=tool_use_examples,
        preferred_libraries=preferred_libraries,
        llms_txt_content=llms_txt_content,
        python_tools_content=python_tools_content,
    )

    # Combine SOP with dynamic content
    return code_assist_with_input(dynamic_content)


def generate_session_prompt(request: str, include_examples: bool = True) -> str:
    """Generate a session management implementation prompt with documentation.

    Combines the code-assist SOP workflow with Strands session management documentation.

    Args:
        request: Description of the session management needs
        include_examples: Include usage examples (default: True)

    Returns:
        Generated prompt combining SOP instructions with session documentation
    """
    cache.ensure_ready()

    # Fetch documentation
    llms_txt_url = "https://strandsagents.com/llms.txt"
    llms_txt_content = fetch_content(llms_txt_url)

    session_management_url = (
        "https://strandsagents.com/latest/documentation/docs/user-guide/concepts/agents/session-management/index.md"
    )
    session_management_content = fetch_content(session_management_url)

    session_api_url = "https://strandsagents.com/latest/documentation/docs/api-reference/session/index.md"
    session_api_content = fetch_content(session_api_url)

    # Load and render template for dynamic content
    template = jinja_env.get_template("session_management.jinja2")
    dynamic_content = template.render(
        request=request,
        include_examples=include_examples,
        llms_txt_content=llms_txt_content,
        session_management_content=session_management_content,
        session_api_content=session_api_content,
    )

    # Combine SOP with dynamic content
    return code_assist_with_input(dynamic_content)


def generate_agent_prompt(
    use_case: str,
    examples: str = "",
    agent_guidelines: str = "",
    tools_required: str = "",
    model_preferences: str = "",
    include_examples: bool = True,
    verbosity: str = "normal",
) -> str:
    """Generate a design-first agent development prompt with dynamic documentation.

    Combines the code-assist SOP workflow with Strands agent documentation.

    Args:
        use_case: Description of what the agent should do
        examples: Optional examples of expected agent behavior
        agent_guidelines: Optional specific behavioral guidelines
        tools_required: Optional list of required tools/capabilities
        model_preferences: Optional model provider preferences
        include_examples: Whether to include code examples
        verbosity: Level of detail (minimal, normal, detailed)

    Returns:
        Generated prompt combining SOP instructions with agent documentation
    """
    cache.ensure_ready()

    # Fetch documentation
    llms_txt_url = "https://strandsagents.com/llms.txt"
    llms_txt_content = fetch_content(llms_txt_url)

    agent_loop_url = (
        "https://strandsagents.com/latest/documentation/docs/user-guide/concepts/agents/agent-loop/index.md"
    )
    agent_loop_content = fetch_content(agent_loop_url)

    agent_api_url = "https://strandsagents.com/latest/documentation/docs/api-reference/agent/index.md"
    agent_api_content = fetch_content(agent_api_url)

    community_tools_url = (
        "https://strandsagents.com/latest/documentation/docs/user-guide/concepts/tools/community-tools-package/index.md"
    )
    community_tools_content = fetch_content(community_tools_url)

    # Load and render template for dynamic content
    template = jinja_env.get_template("agent_development.jinja2")
    dynamic_content = template.render(
        use_case=use_case,
        examples=examples,
        agent_guidelines=agent_guidelines,
        tools_required=tools_required,
        model_preferences=model_preferences,
        llms_txt_content=llms_txt_content,
        agent_loop_content=agent_loop_content,
        agent_api_content=agent_api_content,
        community_tools_content=community_tools_content,
        include_examples=include_examples,
        verbosity=verbosity,
    )

    # Combine SOP with dynamic content
    return code_assist_with_input(dynamic_content)


def generate_model_prompt(
    use_case: str,
    model_details: str = "",
    api_documentation: str = "",
    auth_requirements: str = "",
    special_features: str = "",
    include_examples: bool = True,
) -> str:
    """Generate a design-first custom model provider development prompt.

    Combines the code-assist SOP workflow with Strands model provider documentation.

    Args:
        use_case: Description of the model provider's purpose
        model_details: Details about the models to support
        api_documentation: Reference to API docs or endpoints
        auth_requirements: Authentication/authorization details
        special_features: Special capabilities needed (streaming, function calling, etc.)
        include_examples: Whether to include code examples

    Returns:
        Generated prompt combining SOP instructions with model provider documentation
    """
    cache.ensure_ready()

    # Fetch documentation
    custom_model_url = "https://strandsagents.com/latest/documentation/docs/user-guide/concepts/model-providers/custom_model_provider/index.md"
    custom_model_content = fetch_content(custom_model_url)

    models_api_url = "https://strandsagents.com/latest/documentation/docs/api-reference/models/index.md"
    models_api_content = fetch_content(models_api_url)

    # Load and render template for dynamic content
    template = jinja_env.get_template("model_development.jinja2")
    dynamic_content = template.render(
        use_case=use_case,
        model_details=model_details,
        api_documentation=api_documentation,
        auth_requirements=auth_requirements,
        special_features=special_features,
        custom_model_content=custom_model_content,
        models_api_content=models_api_content,
        include_examples=include_examples,
    )

    # Combine SOP with dynamic content
    return code_assist_with_input(dynamic_content)


def generate_multiagent_prompt(
    use_case: str,
    pattern: str = "",
    agent_roles: str = "",
    interaction_requirements: str = "",
    scale_requirements: str = "",
    include_examples: bool = True,
) -> str:
    """Generate a multi-agent systems development prompt.

    Combines the code-assist SOP workflow with Strands multi-agent documentation.

    Args:
        use_case: Description of what the multi-agent system should accomplish
        pattern: Preferred pattern (graph/swarm/hybrid) or let the prompt guide selection
        agent_roles: Description of the different agent roles and specializations needed
        interaction_requirements: How agents should interact and collaborate
        scale_requirements: Performance, reliability, and scalability requirements
        include_examples: Whether to include code examples

    Returns:
        Generated prompt combining SOP instructions with multi-agent documentation
    """
    cache.ensure_ready()

    # Fetch multi-agent documentation
    graph_url = "https://strandsagents.com/latest/documentation/docs/user-guide/concepts/multi-agent/graph/index.md"
    swarm_url = "https://strandsagents.com/latest/documentation/docs/user-guide/concepts/multi-agent/swarm/index.md"
    multiagent_api_url = "https://strandsagents.com/latest/documentation/docs/api-reference/multiagent/index.md"

    graph_content = fetch_content(graph_url)
    swarm_content = fetch_content(swarm_url)
    multiagent_api_content = fetch_content(multiagent_api_url)

    # Load the template for dynamic content
    template = jinja_env.get_template("multiagent_development.jinja2")
    dynamic_content = template.render(
        use_case=use_case,
        pattern=pattern,
        agent_roles=agent_roles,
        interaction_requirements=interaction_requirements,
        scale_requirements=scale_requirements,
        graph_content=graph_content,
        swarm_content=swarm_content,
        multiagent_api_content=multiagent_api_content,
        include_examples=include_examples,
    )

    # Combine SOP with dynamic content
    return code_assist_with_input(dynamic_content)
