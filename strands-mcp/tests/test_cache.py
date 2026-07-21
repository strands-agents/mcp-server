"""Tests for cache module — negative caching and page loading."""

from unittest.mock import patch

import pytest

from strands_mcp_server.utils import cache, doc_fetcher


@pytest.fixture(autouse=True)
def _reset_globals():
    """Reset cache globals before each test."""
    cache._URL_CACHE.clear()
    cache._URL_TITLES.clear()
    cache._LINKS_LOADED = False
    cache._FAILED_FETCHES.clear()


class TestNegativeCache:
    """Tests that failed fetches are negatively cached to avoid serial timeouts."""

    def test_swallowed_error_no_longer_silent(self):
        """Exception in ensure_page is now logged, not silently swallowed."""
        with patch.object(cache, "logger") as mock_logger, patch.object(
            doc_fetcher, "fetch_and_clean", side_effect=ConnectionError("timeout")
        ):
            tru_result = cache.ensure_page("https://strandsagents.com/broken.md")

            assert tru_result is None
            mock_logger.warning.assert_called_once()
            args, _ = mock_logger.warning.call_args
            assert "https://strandsagents.com/broken.md" in str(args)

    def test_consecutive_call_within_ttl_returns_none(self):
        """Repeated calls within negative cache TTL skip the fetch."""
        with patch.object(doc_fetcher, "fetch_and_clean", side_effect=ConnectionError("timeout")):
            # First call — fails, records the failure
            tru_first = cache.ensure_page("https://strandsagents.com/broken.md")
            assert tru_first is None

        # Second call — should hit negative cache, not call fetch_and_clean
        with patch.object(doc_fetcher, "fetch_and_clean") as mock_fetch:
            tru_second = cache.ensure_page("https://strandsagents.com/broken.md")

            assert tru_second is None
            mock_fetch.assert_not_called()

    def test_successful_fetch_after_ttl_expiry_stores_in_positive_cache(self):
        """After blackout window expires, a retry succeeds and URL moves to positive cache."""
        # First call fails — stored in _FAILED_FETCHES
        with patch.object(doc_fetcher, "fetch_and_clean", side_effect=ConnectionError("timeout")):
            cache.ensure_page("https://strandsagents.com/valid.md")
            assert "https://strandsagents.com/valid.md" in cache._FAILED_FETCHES
            assert cache._URL_CACHE.get("https://strandsagents.com/valid.md") is None

        # Simulate TTL expiry by clearing the failure record
        cache._FAILED_FETCHES.clear()

        # Next call succeeds — stored in positive cache
        mock_page = doc_fetcher.Page(
            url="https://strandsagents.com/valid.md",
            title="Valid Doc",
            content="Some content.",
        )
        with patch.object(doc_fetcher, "fetch_and_clean", return_value=mock_page):
            tru_result = cache.ensure_page("https://strandsagents.com/valid.md")

            assert tru_result is not None
            assert tru_result.title == "Valid Doc"
            # URL should be in the positive cache now
            assert cache._URL_CACHE.get("https://strandsagents.com/valid.md") is not None

    def test_no_negative_cache_for_same_url_different_session_after_ttl(self):
        """After TTL expires, the fetch is retried (tested by bypassing TTL check).

        We simulate TTL expiry by clearing _FAILED_FETCHES, then verify the
        fetch is attempted again.
        """
        # First call fails
        with patch.object(doc_fetcher, "fetch_and_clean", side_effect=ConnectionError("timeout")):
            cache.ensure_page("https://strandsagents.com/retry.md")
            assert "https://strandsagents.com/retry.md" in cache._FAILED_FETCHES

        # Clear the failure record (simulates TTL expiry)
        cache._FAILED_FETCHES.clear()

        # Second call — should retry the fetch
        mock_page = doc_fetcher.Page(
            url="https://strandsagents.com/retry.md",
            title="Retry Doc",
            content="Content now available.",
        )
        with patch.object(doc_fetcher, "fetch_and_clean", return_value=mock_page):
            tru_result = cache.ensure_page("https://strandsagents.com/retry.md")

            assert tru_result is not None
            assert tru_result.title == "Retry Doc"
