"""Tests for doc_fetcher security hardening: redirect policy and response size cap."""

import urllib.error
import urllib.request
from unittest.mock import MagicMock, patch

import pytest

from strands_mcp_server.config import doc_config
from strands_mcp_server.utils.doc_fetcher import _get, _SameHostRedirectHandler, _validate_fetch_url


@pytest.fixture
def mock_http_response():
    """Create a mock HTTP response usable as a context manager."""
    response = MagicMock()
    response.__enter__ = lambda s: s
    response.__exit__ = MagicMock(return_value=False)
    return response


class TestSameHostRedirectHandler:
    """Verify that only same-host HTTPS redirects are allowed."""

    def _make_request(self, url: str) -> urllib.request.Request:
        return urllib.request.Request(url)

    def test_same_host_redirect_allowed(self):
        handler = _SameHostRedirectHandler()
        req = self._make_request("https://strandsagents.com/old-page/")

        result = handler.redirect_request(
            req=req,
            fp=MagicMock(),
            code=301,
            msg="Moved",
            headers=MagicMock(),
            newurl="https://strandsagents.com/new-page/",
        )

        assert isinstance(result, urllib.request.Request)
        assert result.full_url == "https://strandsagents.com/new-page/"

    def test_scheme_downgrade_blocked(self):
        handler = _SameHostRedirectHandler()
        req = self._make_request("https://strandsagents.com/page/")

        with pytest.raises(urllib.error.URLError, match="only https URLs are allowed"):
            handler.redirect_request(
                req=req,
                fp=MagicMock(),
                code=302,
                msg="Found",
                headers=MagicMock(),
                newurl="http://strandsagents.com/page/",
            )

    def test_redirect_with_different_https_host_blocked(self):
        handler = _SameHostRedirectHandler()
        req = self._make_request("https://strandsagents.com/page/")

        with pytest.raises(urllib.error.URLError, match="cross-host redirect blocked"):
            handler.redirect_request(
                req=req,
                fp=MagicMock(),
                code=302,
                msg="Found",
                headers=MagicMock(),
                newurl="https://evil.com/steal/",
            )


class TestResponseSizeCap:
    """Verify that oversized responses are rejected."""

    @patch("strands_mcp_server.utils.doc_fetcher._opener")
    def test_oversized_response_raises_runtime_error(self, mock_opener, mock_http_response):
        oversize_data = b"x" * (doc_config.max_response_bytes + 1)
        mock_http_response.read.return_value = oversize_data
        mock_http_response.headers = {}
        mock_opener.open.return_value = mock_http_response

        with pytest.raises(RuntimeError, match="response exceeds"):
            _get("https://strandsagents.com/latest/")

        mock_http_response.read.assert_called_once_with(doc_config.max_response_bytes + 1)

    @patch("strands_mcp_server.utils.doc_fetcher._opener")
    def test_boundary_response_at_exact_limit_succeeds(self, mock_opener, mock_http_response):
        boundary_data = b"x" * doc_config.max_response_bytes
        mock_http_response.read.return_value = boundary_data
        mock_http_response.headers = {}
        mock_opener.open.return_value = mock_http_response

        result = _get("https://strandsagents.com/latest/")

        assert result == boundary_data.decode("utf-8")
        mock_http_response.read.assert_called_once_with(doc_config.max_response_bytes + 1)

    @patch("strands_mcp_server.utils.doc_fetcher._opener")
    def test_normal_response_returns_content(self, mock_opener, mock_http_response):
        body = b"<html><body>Hello</body></html>"
        mock_http_response.read.return_value = body
        mock_http_response.headers = {}
        mock_opener.open.return_value = mock_http_response

        result = _get("https://strandsagents.com/latest/")

        assert result == body.decode("utf-8")
        mock_http_response.read.assert_called_once_with(doc_config.max_response_bytes + 1)


class TestUrlValidation:
    """Verify that _get() rejects unsafe URLs before making any request."""

    @pytest.mark.parametrize("url", ["http://example.com/", "ftp://example.com/", "file:///etc/passwd"])
    def test_non_https_url_rejected(self, url):
        with pytest.raises(urllib.error.URLError, match="only https URLs are allowed"):
            _validate_fetch_url(url)

    def test_userinfo_url_rejected(self):
        with pytest.raises(urllib.error.URLError, match="userinfo"):
            _validate_fetch_url("https://user@evil.com/path")

    def test_no_hostname_url_rejected(self):
        with pytest.raises(urllib.error.URLError, match="no hostname"):
            _validate_fetch_url("https:///path")

    def test_get_rejects_non_https(self):
        with pytest.raises(urllib.error.URLError, match="only https URLs are allowed"):
            _get("http://example.com/")

    @patch("strands_mcp_server.utils.doc_fetcher._opener")
    def test_https_url_passes_validation(self, mock_opener, mock_http_response):
        mock_http_response.read.return_value = b"ok"
        mock_http_response.headers = {}
        mock_opener.open.return_value = mock_http_response

        result = _get("https://strandsagents.com/page/")

        assert result == "ok"
