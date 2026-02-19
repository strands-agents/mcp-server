"""Integration tests for browse_doc MCP tool against live documentation."""

import pytest

from strands_mcp_server.server import browse_doc
from strands_mcp_server.utils.text_processor import SMALL_DOC_THRESHOLD

from .conftest import API_REF_URL, LARGE_DOC_URL


class TestBrowseDocTocModeLive:
    """Test TOC mode against real documentation pages."""

    def test_large_doc_returns_sections(self, live_cache, large_doc_page):
        """Hooks user guide should produce a non-empty TOC with summaries."""
        result = browse_doc(uri=LARGE_DOC_URL)

        assert "sections" in result, f"Expected TOC but got: {list(result.keys())}"
        assert len(result["sections"]) >= 2, "Expected at least 2 ## sections"
        assert result["title"], "Title should not be empty"

        # Every section must have required fields
        for section in result["sections"]:
            assert "id" in section
            assert "title" in section
            assert "summary" in section
            assert "level" in section
            assert section["level"] == 2

    def test_toc_sections_have_summaries(self, live_cache, large_doc_page):
        """Each TOC section should have a non-empty summary."""
        result = browse_doc(uri=LARGE_DOC_URL)
        sections_with_summaries = [s for s in result["sections"] if s["summary"]]
        # At least half the sections should have prose summaries
        assert len(sections_with_summaries) >= len(result["sections"]) // 2

    def test_api_ref_has_children(self, live_cache, api_ref_page):
        """API reference page should have sections with child methods."""
        result = browse_doc(uri=API_REF_URL)

        if "sections" not in result:
            pytest.skip("API ref returned as small doc")

        sections_with_children = [s for s in result["sections"] if s.get("children")]
        assert len(sections_with_children) >= 1, "Expected at least one section with ### children"

        # Children should have id and title
        for section in sections_with_children:
            for child in section["children"]:
                assert "id" in child
                assert "title" in child
                assert "." in child["id"]  # Dotted notation like "1.1"

    def test_toc_includes_preamble(self, live_cache, large_doc_page):
        """TOC response should include preamble text from before first ## section."""
        result = browse_doc(uri=LARGE_DOC_URL)

        assert "preamble" in result
        assert isinstance(result["preamble"], str)
        # Preamble should not contain the H1 title (that's in the title field)
        assert not result["preamble"].startswith("# ")

    def test_toc_strips_internal_fields(self, live_cache, large_doc_page):
        """TOC response must not expose internal _start or _children_internal."""
        result = browse_doc(uri=LARGE_DOC_URL)

        for section in result["sections"]:
            for key in section:
                assert not key.startswith("_"), f"Internal field '{key}' leaked"


class TestBrowseDocSectionModeLive:
    """Test section extraction against real documentation pages."""

    def test_extract_first_section(self, live_cache, large_doc_page):
        """Extracting section '1' should return content with the header."""
        result = browse_doc(uri=LARGE_DOC_URL, section="1")

        assert "content" in result
        assert "section_id" in result
        assert result["section_id"] == "1"
        assert result["section_title"]
        assert result["content"].startswith("## ")

    def test_extract_child_section(self, live_cache, api_ref_page):
        """Extracting a child section like '1.1' should work on API refs."""
        # First get TOC to find a section with children
        toc = browse_doc(uri=API_REF_URL)
        if "sections" not in toc:
            pytest.skip("API ref returned as small doc")

        # Find first section with children
        parent = next((s for s in toc["sections"] if s.get("children")), None)
        if parent is None:
            pytest.skip("No sections with children found")

        child_id = parent["children"][0]["id"]
        result = browse_doc(uri=API_REF_URL, section=child_id)

        assert "content" in result
        assert result["section_id"] == child_id
        assert "###" in result["content"]

    def test_section_content_is_subset_of_full(self, live_cache, large_doc_page):
        """Section content should be a proper subset of the full document."""
        section_result = browse_doc(uri=LARGE_DOC_URL, section="1")

        assert "content" in section_result
        assert len(section_result["content"]) < len(large_doc_page.content), (
            "Section should be smaller than full document"
        )

    def test_invalid_section_returns_error(self, live_cache, large_doc_page):
        """Non-existent section ID should return error, not exception."""
        result = browse_doc(uri=LARGE_DOC_URL, section="999")

        assert "error" in result
        assert "999" in result["error"]


class TestBrowseDocSmallDocLive:
    """Test small document handling by finding a small page dynamically."""

    def test_small_doc_returns_full_content(self, live_cache):
        """Find a page under the size threshold and verify full content return.

        Instead of hardcoding a URL that may grow, we scan the catalog
        and fetch pages until we find one under SMALL_DOC_THRESHOLD.
        """
        catalog = browse_doc(uri="")
        if "urls" not in catalog:
            pytest.skip("Could not get URL catalog")

        # Try pages until we find a small one (limit attempts)
        for entry in catalog["urls"][:20]:
            page = live_cache.ensure_page(entry["url"])
            if page and len(page.content.encode("utf-8")) <= SMALL_DOC_THRESHOLD:
                result = browse_doc(uri=entry["url"])
                assert result.get("document_small") is True
                assert "content" in result
                assert "sections" not in result
                return

        pytest.skip("No small documents found in first 20 catalog entries")


class TestBrowseDocEdgeCasesLive:
    """Test edge cases and error paths against the real network."""

    def test_empty_uri_returns_catalog(self, live_cache):
        """Empty URI should return the full URL catalog from llms.txt."""
        result = browse_doc(uri="")

        assert "urls" in result
        assert len(result["urls"]) >= 10, "Expected at least 10 docs in the catalog"
        # Each entry should have url and title
        for entry in result["urls"][:5]:
            assert "url" in entry
            assert "title" in entry

    def test_invalid_url_rejected(self):
        """Non-strandsagents.com URLs should be rejected."""
        result = browse_doc(uri="https://evil.com/pwned")

        assert "error" in result
        assert "strandsagents.com" in result["error"]

    @pytest.mark.parametrize(
        "malicious_uri",
        [
            "https://strandsagents.com.evil.com/path",
            "https://strandsagents.com@evil.com/path",
            "http://strandsagents.com/valid-looking-path",
        ],
    )
    def test_ssrf_bypass_vectors_rejected(self, malicious_uri):
        result = browse_doc(uri=malicious_uri)

        assert "error" in result
