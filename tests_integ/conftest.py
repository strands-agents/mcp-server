import os

import pytest

from strands_mcp_server.utils import cache
from strands_mcp_server.utils.text_processor import SMALL_DOC_THRESHOLD

# Skip all integration tests when SKIP_INTEG_TESTS is set.
# Useful for CI environments without network access.
if os.environ.get("SKIP_INTEG_TESTS"):
    pytest.skip("SKIP_INTEG_TESTS is set", allow_module_level=True)

# Known stable documentation URLs for regression testing.
# These are core pages unlikely to be removed.
LARGE_DOC_URL = "https://strandsagents.com/latest/documentation/docs/user-guide/concepts/agents/hooks/index.md"

# Mark all tests in this directory as integration tests
pytestmark = [
    pytest.mark.integ,
    pytest.mark.timeout(60),
]


@pytest.fixture(scope="session")
def live_cache():
    """Initialize the real cache from strandsagents.com llms.txt.

    Session-scoped to avoid re-fetching the llms.txt index for every test.
    """
    cache.ensure_ready()
    return cache


@pytest.fixture(scope="session")
def large_doc_page(live_cache):
    """Fetch and cache a known large documentation page.

    The Hooks user guide is ~23KB with multiple ## sections - ideal for
    testing TOC generation and section extraction on real content.
    """
    page = live_cache.ensure_page(LARGE_DOC_URL)
    if page is None:
        pytest.skip(f"Could not fetch {LARGE_DOC_URL}")
    if len(page.content.encode("utf-8")) <= SMALL_DOC_THRESHOLD:
        pytest.skip(
            f"Doc at {LARGE_DOC_URL} is only {len(page.content.encode('utf-8'))} bytes (need >{SMALL_DOC_THRESHOLD})"
        )
    return page


@pytest.fixture(scope="session")
def url_titles(live_cache):
    """Get the full URL-to-title mapping from llms.txt."""
    return live_cache.get_url_titles()
