"""Tests for Strands MCP Server prompt endpoints."""

import sys
from pathlib import Path
from unittest.mock import Mock, patch

import pytest

# Add src to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from strands_mcp_server.server import (
    fetch_doc,
    search_docs,
    strands_agent_development,
    strands_model_development,
    strands_multiagent_development,
    strands_session_management,
    strands_tool_development,
)


class TestMCPPromptEndpoints:
    """Test MCP server prompt endpoints."""

    def test_strands_tool_development_endpoint(self):
        """Test the tool development prompt endpoint."""
        result = strands_tool_development(
            request="Create a weather API tool",
            tool_use_examples="agent.tool.get_weather('London')",
            preferred_libraries="requests",
        )

        assert isinstance(result, str)
        assert "Create a weather API tool" in result
        assert "tool" in result.lower()
        assert "@tool" in result

    def test_strands_agent_development_endpoint(self):
        """Test the agent development prompt endpoint."""
        result = strands_agent_development(
            use_case="Customer support chatbot",
            examples="User: Help with order\nAgent: I can help...",
            agent_guidelines="Be polite and helpful",
            tools_required="database_query, send_email",
            model_preferences="Fast response model",
        )

        assert isinstance(result, str)
        assert "Customer support chatbot" in result
        assert "agent" in result.lower()
        assert "system" in result.lower()

    def test_strands_session_management_endpoint(self):
        """Test the session management prompt endpoint."""
        result = strands_session_management(request="Add Redis-based session storage", include_examples=True)

        assert isinstance(result, str)
        assert "Redis-based session storage" in result
        assert "session" in result.lower()

    def test_strands_model_development_endpoint(self):
        """Test the model development prompt endpoint."""
        result = strands_model_development(
            use_case="Integrate Hugging Face models",
            model_details="Support for text generation models",
            api_documentation="https://huggingface.co/docs",
            auth_requirements="API token",
            special_features="Streaming and batching",
        )

        assert isinstance(result, str)
        assert "Integrate Hugging Face models" in result
        assert "model" in result.lower()
        assert "provider" in result.lower()

    def test_strands_multiagent_development_endpoint(self):
        """Test the multi-agent development prompt endpoint."""
        result = strands_multiagent_development(
            use_case="Research and analysis pipeline",
            pattern="graph",
            agent_roles="Researcher, Analyst, Writer",
            interaction_requirements="Pass context between agents",
            scale_requirements="Process 100 documents per hour",
        )

        assert isinstance(result, str)
        assert "Research and analysis pipeline" in result
        assert "multi-agent" in result.lower() or "multiagent" in result.lower()
        assert "graph" in result.lower() or "swarm" in result.lower()

    def test_minimal_parameters(self):
        """Test endpoints with minimal parameters."""
        # Tool development
        tool_result = strands_tool_development(request="Simple tool")
        assert "Simple tool" in tool_result

        # Agent development
        agent_result = strands_agent_development(use_case="Simple agent")
        assert "Simple agent" in agent_result

        # Session management
        session_result = strands_session_management(request="Simple session")
        assert "Simple session" in session_result

        # Model development
        model_result = strands_model_development(use_case="Simple model")
        assert "Simple model" in model_result

        # Multi-agent development
        multiagent_result = strands_multiagent_development(use_case="Simple system")
        assert "Simple system" in multiagent_result


class TestSearchDocsIntegration:
    """Test search_docs function integration."""

    @patch("strands_mcp_server.server.cache")
    def test_search_docs_basic(self, mock_cache):
        """Test basic document search."""
        # Mock the index and search results
        mock_doc = Mock()
        mock_doc.uri = "https://example.com/doc1"
        mock_doc.display_title = "Test Document"

        mock_index = Mock()
        mock_index.search.return_value = [(0.9, mock_doc)]

        mock_cache.get_index.return_value = mock_index
        mock_cache.get_url_cache.return_value = {}
        mock_cache.SNIPPET_HYDRATE_MAX = 10  # Add this attribute

        result = search_docs("test query", k=5)

        assert isinstance(result, list)
        assert len(result) <= 5
        mock_cache.ensure_ready.assert_called_once()

    @patch("strands_mcp_server.server.cache")
    def test_search_docs_no_results(self, mock_cache):
        """Test search with no results."""
        mock_index = Mock()
        mock_index.search.return_value = []

        mock_cache.get_index.return_value = mock_index
        mock_cache.get_url_cache.return_value = {}
        mock_cache.SNIPPET_HYDRATE_MAX = 10  # Add this attribute

        result = search_docs("nonexistent", k=5)

        assert result == []


class TestFetchDocIntegration:
    """Test fetch_doc function integration."""

    @patch("strands_mcp_server.server.cache")
    def test_fetch_doc_success(self, mock_cache):
        """Test successful document fetching."""
        mock_page = Mock()
        mock_page.title = "Test Title"
        mock_page.content = "Test content"

        mock_cache.ensure_page.return_value = mock_page

        # Use a valid strandsagents.com URL
        result = fetch_doc("https://strandsagents.com/doc")

        assert result["url"] == "https://strandsagents.com/doc"
        assert result["title"] == "Test Title"
        assert result["content"] == "Test content"

    @patch("strands_mcp_server.server.cache")
    def test_fetch_doc_failure(self, mock_cache):
        """Test document fetch failure."""
        mock_cache.ensure_page.return_value = None

        # Use a valid strandsagents.com URL
        result = fetch_doc("https://strandsagents.com/missing")

        assert result["error"] == "fetch failed"
        assert result["url"] == "https://strandsagents.com/missing"

    def test_fetch_doc_invalid_uri(self):
        """Test with invalid URI (non-strandsagents.com)."""
        result = fetch_doc("https://example.com/doc")

        assert result["error"] == "only https://strandsagents.com URLs allowed"
        assert result["url"] == "https://example.com/doc"

    def test_fetch_doc_empty_returns_all_urls(self):
        """Test that empty URI returns all available URLs."""
        with patch("strands_mcp_server.server.cache") as mock_cache:
            mock_cache.get_url_titles.return_value = {
                "https://strandsagents.com/doc1": "Doc 1",
                "https://strandsagents.com/doc2": "Doc 2",
            }

            result = fetch_doc("")

            assert "urls" in result
            assert len(result["urls"]) == 2


class TestMCPServerRegistration:
    """Test that all prompt functions are properly registered with MCP."""

    def test_prompt_functions_registered(self):
        """Verify all prompt functions are registered as MCP prompts."""
        # These should be registered via @mcp.prompt() decorator
        expected_prompts = [
            "strands_tool_development",
            "strands_agent_development",
            "strands_session_management",
            "strands_model_development",
            "strands_multiagent_development",
        ]

        # Check that functions exist and are callable
        from strands_mcp_server import server

        for prompt_name in expected_prompts:
            assert hasattr(server, prompt_name)
            assert callable(getattr(server, prompt_name))

    def test_tool_functions_registered(self):
        """Verify tool functions are registered."""
        expected_tools = ["search_docs", "fetch_doc"]

        from strands_mcp_server import server

        for tool_name in expected_tools:
            assert hasattr(server, tool_name)
            assert callable(getattr(server, tool_name))


# Test for template file existence
class TestTemplateFiles:
    """Test that all required template files exist."""

    def test_template_files_exist(self):
        """Verify all Jinja2 template files exist."""
        template_dir = Path(__file__).parent.parent / "src" / "strands_mcp_server" / "prompts"

        required_templates = [
            "base.jinja2",
            "tool_development.jinja2",
            "agent_development.jinja2",
            "session_management.jinja2",
            "model_development.jinja2",
            "multiagent_development.jinja2",
        ]

        for template in required_templates:
            template_path = template_dir / template
            assert template_path.exists(), f"Template {template} not found at {template_path}"

    def test_template_syntax_valid(self):
        """Test that all templates have valid Jinja2 syntax."""
        import re

        from jinja2 import Environment, FileSystemLoader, TemplateSyntaxError

        template_dir = Path(__file__).parent.parent / "src" / "strands_mcp_server" / "prompts"
        env = Environment(loader=FileSystemLoader(template_dir))

        # Add the regex_replace filter that the templates use
        def regex_replace_filter(text, pattern, replacement=""):
            if not text:
                return text
            return re.sub(pattern, replacement, text, flags=re.DOTALL)

        env.filters["regex_replace"] = regex_replace_filter

        templates = [
            "tool_development.jinja2",
            "agent_development.jinja2",
            "session_management.jinja2",
            "model_development.jinja2",
            "multiagent_development.jinja2",
        ]

        for template_name in templates:
            try:
                template = env.get_template(template_name)
                # Try to render with empty context to check syntax
                template.render()
            except TemplateSyntaxError as e:
                pytest.fail(f"Template {template_name} has syntax error: {e}")


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
