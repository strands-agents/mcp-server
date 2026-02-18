"""Tests for browse_doc MCP tool."""

from unittest.mock import patch

from strands_mcp_server.server import browse_doc
from strands_mcp_server.utils.doc_fetcher import Page


@patch("strands_mcp_server.server.cache")
class TestBrowseDocTocMode:
    """Tests for browse_doc TOC mode (no section param)."""

    def test_returns_toc_for_large_doc(self, mock_cache, api_reference_doc):
        mock_cache.ensure_page.return_value = Page(
            url="https://strandsagents.com/test.md",
            title="Test Doc",
            content=api_reference_doc,
        )

        tru_result = browse_doc(uri="https://strandsagents.com/test.md")

        assert "sections" in tru_result
        assert len(tru_result["sections"]) == 3
        assert tru_result["title"] == "Test Doc"

    def test_small_doc_returns_full_content(self, mock_cache, small_doc):
        mock_cache.ensure_page.return_value = Page(
            url="https://strandsagents.com/small.md",
            title="Small Doc",
            content=small_doc,
        )

        tru_result = browse_doc(uri="https://strandsagents.com/small.md")

        assert tru_result["document_small"] is True
        assert "content" in tru_result
        assert "sections" not in tru_result

    def test_small_doc_ignores_section_param(self, mock_cache, small_doc):
        mock_cache.ensure_page.return_value = Page(
            url="https://strandsagents.com/small.md",
            title="Small Doc",
            content=small_doc,
        )

        tru_result = browse_doc(uri="https://strandsagents.com/small.md", section="1")

        # Section param should be ignored for small docs
        assert tru_result["document_small"] is True
        assert "content" in tru_result
        assert "section_id" not in tru_result

    def test_no_h2_headers_returns_full_content(self, mock_cache, no_h2_doc):
        mock_cache.ensure_page.return_value = Page(
            url="https://strandsagents.com/no-h2.md",
            title="No H2 Doc",
            content=no_h2_doc,
        )

        tru_result = browse_doc(uri="https://strandsagents.com/no-h2.md")

        # No ## sections means fallback to full content
        assert tru_result["document_small"] is True
        assert "content" in tru_result
        assert "sections" not in tru_result


@patch("strands_mcp_server.server.cache")
class TestBrowseDocSectionMode:
    """Tests for browse_doc section mode."""

    def test_returns_section_content(self, mock_cache, api_reference_doc):
        mock_cache.ensure_page.return_value = Page(
            url="https://strandsagents.com/test.md",
            title="Test Doc",
            content=api_reference_doc,
        )

        tru_result = browse_doc(uri="https://strandsagents.com/test.md", section="1")

        assert tru_result["section_id"] == "1"
        assert "content" in tru_result
        assert "sections" not in tru_result

    def test_invalid_section_returns_error(self, mock_cache, api_reference_doc):
        mock_cache.ensure_page.return_value = Page(
            url="https://strandsagents.com/test.md",
            title="Test Doc",
            content=api_reference_doc,
        )

        tru_result = browse_doc(uri="https://strandsagents.com/test.md", section="99")

        assert "error" in tru_result


@patch("strands_mcp_server.server.cache")
class TestBrowseDocErrors:
    """Tests for browse_doc error handling."""

    def test_invalid_url_returns_error(self, mock_cache):
        tru_result = browse_doc(uri="https://evil.com/hack")

        exp_error = "only https://strandsagents.com URLs allowed"
        assert tru_result["error"] == exp_error

    def test_fetch_failure_returns_error(self, mock_cache):
        mock_cache.ensure_page.return_value = None

        tru_result = browse_doc(uri="https://strandsagents.com/missing.md")

        assert tru_result["error"] == "fetch failed"

    def test_empty_uri_returns_url_catalog(self, mock_cache):
        mock_cache.get_url_titles.return_value = {"https://strandsagents.com/a.md": "Doc A"}

        tru_result = browse_doc(uri="")

        assert "urls" in tru_result
        assert len(tru_result["urls"]) == 1
