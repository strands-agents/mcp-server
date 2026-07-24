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
        url = "https://strandsagents.com/valid.md"
        failed_at = 100.0
        page = doc_fetcher.Page(url=url, title="Valid Doc", content="Some content.")

        # First call fails — stored in _FAILED_FETCHES at timestamp 100.0
        with (
            patch.object(cache.time, "monotonic", return_value=failed_at),
            patch.object(doc_fetcher, "fetch_and_clean", side_effect=ConnectionError("timeout")),
        ):
            assert cache.ensure_page(url) is None
            assert cache._FAILED_FETCHES.get(url) == failed_at
            assert cache._URL_CACHE.get(url) is None

        # Advance clock past TTL boundary — retry the fetch
        with (
            patch.object(cache.time, "monotonic", return_value=failed_at + cache.NEGATIVE_CACHE_TTL),
            patch.object(doc_fetcher, "fetch_and_clean", return_value=page),
        ):
            tru_result = cache.ensure_page(url)

            assert tru_result is not None
            assert tru_result.title == "Valid Doc"
            # URL should be in the positive cache now
            assert cache._URL_CACHE.get(url) is not None

    def test_no_negative_cache_for_same_url_different_session_after_ttl(self):
        """After TTL expires, the fetch is retried."""
        url = "https://strandsagents.com/retry.md"
        failed_at = 200.0
        page = doc_fetcher.Page(url=url, title="Retry Doc", content="Content now available.")

        # First call fails — stored in _FAILED_FETCHES at timestamp 200.0
        with (
            patch.object(cache.time, "monotonic", return_value=failed_at),
            patch.object(doc_fetcher, "fetch_and_clean", side_effect=ConnectionError("timeout")),
        ):
            assert cache.ensure_page(url) is None
            assert cache._FAILED_FETCHES.get(url) == failed_at

        # Hit negative cache (just before expiry)
        with (
            patch.object(cache.time, "monotonic", return_value=failed_at + cache.NEGATIVE_CACHE_TTL - 0.001),
            patch.object(doc_fetcher, "fetch_and_clean") as mock_fetch,
        ):
            assert cache.ensure_page(url) is None
            mock_fetch.assert_not_called()

        # Advance past TTL boundary — fetch is retried
        with (
            patch.object(cache.time, "monotonic", return_value=failed_at + cache.NEGATIVE_CACHE_TTL),
            patch.object(doc_fetcher, "fetch_and_clean", return_value=page),
        ):
            tru_result = cache.ensure_page(url)

            assert tru_result is not None
            assert tru_result.title == "Retry Doc"
