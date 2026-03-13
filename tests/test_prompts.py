"""Tests for Strands MCP Server prompt generation functionality."""

import sys
from pathlib import Path
from unittest.mock import Mock, patch

import pytest

# Add src to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from strands_mcp_server.prompts import (
    fetch_content,
    generate_agent_prompt,
    generate_model_prompt,
    generate_multiagent_prompt,
    generate_session_prompt,
    generate_tool_prompt,
    regex_replace_filter,
)


class TestRegexReplaceFilter:
    """Test the custom Jinja2 regex replace filter."""

    def test_regex_replace_basic(self):
        """Test basic regex replacement."""
        text = "Hello World 123"
        result = regex_replace_filter(text, r"\d+", "XXX")
        assert result == "Hello World XXX"

    def test_regex_replace_empty_text(self):
        """Test with empty text."""
        result = regex_replace_filter("", r"\d+", "XXX")
        assert result == ""

    def test_regex_replace_none_text(self):
        """Test with None text."""
        result = regex_replace_filter(None, r"\d+", "XXX")
        assert result is None

    def test_regex_replace_multiline(self):
        """Test multiline replacement with DOTALL flag."""
        text = "Start\n```\ncode block\n```\nEnd"
        result = regex_replace_filter(text, r"```.*?```", "")
        assert result == "Start\n\nEnd"


class TestFetchContent:
    """Test the fetch_content function."""

    @patch("strands_mcp_server.prompts.cache")
    def test_fetch_content_success(self, mock_cache):
        """Test successful content fetching."""
        mock_page = Mock()
        mock_page.content = "Test content"
        mock_cache.ensure_page.return_value = mock_page

        result = fetch_content("https://example.com")

        assert result == "Test content"
        mock_cache.ensure_ready.assert_called_once()
        mock_cache.ensure_page.assert_called_once_with("https://example.com")

    @patch("strands_mcp_server.prompts.cache")
    def test_fetch_content_no_page(self, mock_cache):
        """Test when page is not found."""
        mock_cache.ensure_page.return_value = None

        result = fetch_content("https://example.com")

        assert result == ""

    @patch("strands_mcp_server.prompts.cache")
    def test_fetch_content_no_content(self, mock_cache):
        """Test when page exists but has no content."""
        mock_page = Mock()
        mock_page.content = None
        mock_cache.ensure_page.return_value = mock_page

        result = fetch_content("https://example.com")

        assert result == ""


class TestGenerateToolPrompt:
    """Test the generate_tool_prompt function."""

    @patch("strands_mcp_server.prompts.fetch_content")
    @patch("strands_mcp_server.prompts.cache")
    def test_generate_tool_prompt_basic(self, mock_cache, mock_fetch):
        """Test basic tool prompt generation."""
        mock_fetch.side_effect = ["llms.txt content", "python tools content"]

        result = generate_tool_prompt(
            request="Create a calculator tool",
            tool_use_examples="agent.tool.calculator(expression='2+2')",
            preferred_libraries="sympy",
        )

        # Check that user requirements are included
        assert "Create a calculator tool" in result
        assert "agent.tool.calculator" in result
        assert "sympy" in result
        # Check that SOP wrapper is present
        assert "<agent-sop" in result
        assert "code-assist" in result
        mock_cache.ensure_ready.assert_called_once()

    @patch("strands_mcp_server.prompts.fetch_content")
    @patch("strands_mcp_server.prompts.cache")
    def test_generate_tool_prompt_minimal(self, mock_cache, mock_fetch):
        """Test tool prompt with minimal parameters."""
        mock_fetch.side_effect = ["", ""]

        result = generate_tool_prompt(request="Create a tool")

        assert "Create a tool" in result
        assert "@tool" in result
        assert "Strands" in result


class TestGenerateAgentPrompt:
    """Test the generate_agent_prompt function."""

    @patch("strands_mcp_server.prompts.fetch_content")
    @patch("strands_mcp_server.prompts.cache")
    def test_generate_agent_prompt_full(self, mock_cache, mock_fetch):
        """Test agent prompt with all parameters."""
        mock_fetch.side_effect = [
            "llms.txt content",
            "agent loop content",
            "agent api content",
            "community tools content",
        ]

        result = generate_agent_prompt(
            use_case="Research assistant for academic papers",
            examples="User: Find papers on AI\nAgent: Searching...",
            agent_guidelines="Be thorough and cite sources",
            tools_required="retrieve, file_write",
            model_preferences="Claude Sonnet",
            include_examples=True,
            verbosity="normal",
        )

        assert "Research assistant for academic papers" in result
        assert "Find papers on AI" in result
        assert "Be thorough and cite sources" in result
        assert "retrieve, file_write" in result
        assert "Claude Sonnet" in result
        # Check that SOP wrapper is present
        assert "<agent-sop" in result
        assert "code-assist" in result

    @patch("strands_mcp_server.prompts.fetch_content")
    @patch("strands_mcp_server.prompts.cache")
    def test_generate_agent_prompt_minimal(self, mock_cache, mock_fetch):
        """Test agent prompt with minimal parameters."""
        mock_fetch.side_effect = ["", "", "", ""]

        result = generate_agent_prompt(use_case="Simple agent")

        assert "Simple agent" in result
        assert "Agent" in result
        assert "Strands" in result


class TestGenerateSessionPrompt:
    """Test the generate_session_prompt function."""

    @patch("strands_mcp_server.prompts.fetch_content")
    @patch("strands_mcp_server.prompts.cache")
    def test_generate_session_prompt_with_examples(self, mock_cache, mock_fetch):
        """Test session prompt with examples included."""
        mock_fetch.side_effect = ["llms.txt content", "session management content", "session api content"]

        result = generate_session_prompt(request="Implement persistent sessions with Redis", include_examples=True)

        assert "Implement persistent sessions with Redis" in result
        assert "Session" in result
        # Check that SOP wrapper is present
        assert "<agent-sop" in result
        assert "code-assist" in result

    @patch("strands_mcp_server.prompts.fetch_content")
    @patch("strands_mcp_server.prompts.cache")
    def test_generate_session_prompt_no_examples(self, mock_cache, mock_fetch):
        """Test session prompt without examples."""
        mock_fetch.side_effect = ["", "", ""]

        result = generate_session_prompt(request="Basic session", include_examples=False)

        assert "Basic session" in result
        assert "Session Management" in result


class TestGenerateModelPrompt:
    """Test the generate_model_prompt function."""

    @patch("strands_mcp_server.prompts.fetch_content")
    @patch("strands_mcp_server.prompts.cache")
    def test_generate_model_prompt_full(self, mock_cache, mock_fetch):
        """Test model provider prompt with all parameters."""
        mock_fetch.side_effect = ["custom model content", "models api content"]

        result = generate_model_prompt(
            use_case="Integrate company LLM API",
            model_details="GPT-4 compatible endpoint",
            api_documentation="https://api.company.com/docs",
            auth_requirements="Bearer token authentication",
            special_features="Streaming support required",
            include_examples=True,
        )

        assert "Integrate company LLM API" in result
        assert "GPT-4 compatible endpoint" in result
        assert "https://api.company.com/docs" in result
        assert "Bearer token authentication" in result
        assert "Streaming support required" in result
        # Check that SOP wrapper is present
        assert "<agent-sop" in result
        assert "code-assist" in result

    @patch("strands_mcp_server.prompts.fetch_content")
    @patch("strands_mcp_server.prompts.cache")
    def test_generate_model_prompt_minimal(self, mock_cache, mock_fetch):
        """Test model provider prompt with minimal parameters."""
        mock_fetch.side_effect = ["", ""]

        result = generate_model_prompt(use_case="Custom model")

        assert "Custom model" in result
        assert "Model Provider" in result


class TestGenerateMultiagentPrompt:
    """Test the generate_multiagent_prompt function."""

    @patch("strands_mcp_server.prompts.fetch_content")
    @patch("strands_mcp_server.prompts.cache")
    def test_generate_multiagent_prompt_graph(self, mock_cache, mock_fetch):
        """Test multi-agent prompt for Graph pattern."""
        mock_fetch.side_effect = ["graph content", "swarm content", "multiagent api content"]

        result = generate_multiagent_prompt(
            use_case="Document processing pipeline",
            pattern="graph",
            agent_roles="Processor, Analyzer, Reporter",
            interaction_requirements="Sequential processing",
            scale_requirements="Handle 1000 docs/hour",
            include_examples=True,
        )

        assert "Document processing pipeline" in result
        assert "GRAPH" in result
        assert "Processor, Analyzer, Reporter" in result
        assert "Sequential processing" in result
        assert "Handle 1000 docs/hour" in result
        # Check that SOP wrapper is present
        assert "<agent-sop" in result
        assert "code-assist" in result

    @patch("strands_mcp_server.prompts.fetch_content")
    @patch("strands_mcp_server.prompts.cache")
    def test_generate_multiagent_prompt_swarm(self, mock_cache, mock_fetch):
        """Test multi-agent prompt for Swarm pattern."""
        mock_fetch.side_effect = ["", "", ""]

        result = generate_multiagent_prompt(use_case="Creative problem solving", pattern="swarm")

        assert "Creative problem solving" in result
        assert "SWARM" in result
        assert "Multi-Agent" in result

    @patch("strands_mcp_server.prompts.fetch_content")
    @patch("strands_mcp_server.prompts.cache")
    def test_generate_multiagent_prompt_hybrid(self, mock_cache, mock_fetch):
        """Test multi-agent prompt for Hybrid pattern."""
        mock_fetch.side_effect = ["", "", ""]

        result = generate_multiagent_prompt(use_case="Complex analysis system", pattern="hybrid")

        assert "Complex analysis system" in result
        assert "HYBRID" in result
        assert "Multi-Agent" in result


# Integration tests
class TestPromptIntegration:
    """Integration tests for prompt generation."""

    @patch("strands_mcp_server.prompts.cache")
    def test_all_prompts_generate_without_error(self, mock_cache):
        """Test that all prompt generators work without errors."""
        mock_cache.ensure_ready.return_value = None
        mock_cache.ensure_page.return_value = None

        # Test each generator
        tool_prompt = generate_tool_prompt("Create tool")
        assert tool_prompt
        assert len(tool_prompt) > 100
        assert "<agent-sop" in tool_prompt

        agent_prompt = generate_agent_prompt("Create agent")
        assert agent_prompt
        assert len(agent_prompt) > 100
        assert "<agent-sop" in agent_prompt

        session_prompt = generate_session_prompt("Session management")
        assert session_prompt
        assert len(session_prompt) > 100
        assert "<agent-sop" in session_prompt

        model_prompt = generate_model_prompt("Custom model")
        assert model_prompt
        assert len(model_prompt) > 100
        assert "<agent-sop" in model_prompt

        multiagent_prompt = generate_multiagent_prompt("Multi-agent system")
        assert multiagent_prompt
        assert len(multiagent_prompt) > 100
        assert "<agent-sop" in multiagent_prompt

    @patch("strands_mcp_server.prompts.jinja_env")
    def test_template_loading_error_handling(self, mock_jinja_env):
        """Test handling of template loading errors."""
        mock_jinja_env.get_template.side_effect = Exception("Template not found")

        with pytest.raises(Exception) as exc_info:
            generate_tool_prompt("Test")

        assert "Template not found" in str(exc_info.value)


class TestSOPIntegration:
    """Test SOP integration with prompts."""

    @patch("strands_mcp_server.prompts.cache")
    def test_prompts_use_code_assist_sop(self, mock_cache):
        """Test that prompts use the code-assist SOP wrapper."""
        mock_cache.ensure_ready.return_value = None
        mock_cache.ensure_page.return_value = None

        result = generate_tool_prompt("Create a test tool")

        # Check SOP structure
        assert '<agent-sop name="code-assist">' in result
        assert "<content>" in result
        assert "<user-input>" in result
        assert "</agent-sop>" in result

    @patch("strands_mcp_server.prompts.cache")
    def test_dynamic_content_in_user_input(self, mock_cache):
        """Test that dynamic content appears in user-input section."""
        mock_cache.ensure_ready.return_value = None
        mock_cache.ensure_page.return_value = None

        result = generate_tool_prompt("Create a unique tool XYZ123")

        # The dynamic content should be in the user-input section
        user_input_start = result.find("<user-input>")
        user_input_end = result.find("</user-input>")
        user_input_content = result[user_input_start:user_input_end]

        assert "Create a unique tool XYZ123" in user_input_content


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
