"""Reproduction tests for PR #40 blockers.

These tests reproduce the race conditions identified by the review bot.
Per REVIEW-PROTOCOL.md Lesson 4: "Reproduce, don't reason" - these tests
MUST fail on the unfixed code before we fix the issues.

BLOCKER 1: Unlocked read-modify-write on shared index state
BLOCKER 2: Page cached before indexing succeeds
"""

import threading
import time
from concurrent.futures import ThreadPoolExecutor, as_completed
from unittest.mock import MagicMock, patch

import pytest

from strands_mcp_server.utils import cache, indexer


class TestBlocker1ConcurrentIndexCorruption:
    """Reproduce BLOCKER 1: concurrent add/update_content corrupts index integrity.

    The bot demonstrated: 60 postings → df=48 (lost increments), same-URI duplication
    (N=1, df=2, postings [0,0], negative BM25).

    Note: The primary demonstration of this bug is through stress testing. Python's GIL
    makes pure-Python races hard to reproduce deterministically, but the lack of locking
    means the code is NOT thread-safe. Adding a Lock is the correct fix regardless of
    whether tests can reliably trigger the race in CI.

    These tests verify the INTERFACE contract: that concurrent operations preserve
    index integrity invariants (df == len(postings), no duplicate postings, df <= N).
    """

    def test_concurrent_add_preserves_integrity_invariants(self):
        """Concurrent add() calls must preserve: df == len(postings), df <= N.

        Without locking, concurrent increments to doc_frequency[token] can be lost:
        Thread A reads df=5, Thread B reads df=5, both write df=6 → lost increment.

        The fix (threading.Lock) ensures these invariants hold under concurrent access.
        """
        index = indexer.IndexSearch()
        num_docs = 100
        num_threads = 10

        # All docs share this token so they all increment doc_frequency["shared"]
        docs = [
            indexer.Doc(
                uri=f"https://example.com/doc{i}",
                display_title=f"Doc {i}",
                content="shared token here unique" + str(i),
                index_title=f"doc {i}",
            )
            for i in range(num_docs)
        ]

        def add_batch(start, end):
            for i in range(start, end):
                index.add(docs[i])

        # Concurrent adds
        batch_size = num_docs // num_threads
        with ThreadPoolExecutor(max_workers=num_threads) as executor:
            futures = [executor.submit(add_batch, i * batch_size, (i + 1) * batch_size) for i in range(num_threads)]
            for f in as_completed(futures):
                f.result()

        # INTEGRITY INVARIANTS that must hold after concurrent operations:
        actual_df = index.doc_frequency.get("shared", 0)
        actual_postings = len(index.doc_indices.get("shared", []))
        actual_N = len(index.docs)

        # Invariant 1: df must equal len(postings) for each token
        assert actual_df == actual_postings, (
            f"Invariant violated: df ({actual_df}) != len(postings) ({actual_postings})"
        )
        # Invariant 2: df must not exceed N
        assert actual_df <= actual_N, f"Invariant violated: df ({actual_df}) > N ({actual_N})"
        # Invariant 3: N must equal expected (no lost docs)
        assert actual_N == num_docs, f"docs list corrupted: expected {num_docs}, got {actual_N}"
        # Invariant 4: all docs added, so df should equal N for 'shared'
        assert actual_df == num_docs, f"doc_frequency lost increments: expected {num_docs}, got {actual_df}"

    def test_concurrent_update_content_preserves_integrity_invariants(self):
        """Concurrent update_content() calls must preserve index integrity.

        Scenario: prefetch daemon thread + foreground ensure_page() both call
        update_content() on the same or different URIs concurrently.

        Without locking, the interleaving of:
        1. read old_tokens
        2. compute new_tokens
        3. update doc_frequency (decrement for removed, increment for added)
        4. update doc_indices (remove idx from old, add to new)
        can corrupt the index.
        """
        index = indexer.IndexSearch()
        num_docs = 50

        # Add docs with empty content
        for i in range(num_docs):
            doc = indexer.Doc(
                uri=f"https://example.com/page{i}",
                display_title=f"Page {i}",
                content="",
                index_title=f"page {i}",
            )
            index.add(doc)

        barrier = threading.Barrier(2)
        errors = []

        def updater_a():
            """Simulates prefetch daemon."""
            try:
                barrier.wait(timeout=5)
                for i in range(num_docs):
                    index.update_content(f"https://example.com/page{i}", f"hydrated content alpha doc{i}")
            except Exception as e:
                errors.append(e)

        def updater_b():
            """Simulates foreground ensure_page."""
            try:
                barrier.wait(timeout=5)
                for i in range(num_docs):
                    index.update_content(f"https://example.com/page{i}", f"hydrated content alpha doc{i}")
            except Exception as e:
                errors.append(e)

        t1 = threading.Thread(target=updater_a)
        t2 = threading.Thread(target=updater_b)
        t1.start()
        t2.start()
        t1.join(timeout=30)
        t2.join(timeout=30)

        assert not errors, f"Exceptions during concurrent update: {errors}"

        # INTEGRITY INVARIANTS after concurrent updates:
        alpha_df = index.doc_frequency.get("alpha", 0)
        alpha_postings = index.doc_indices.get("alpha", [])

        # Invariant 1: df == len(postings)
        assert alpha_df == len(alpha_postings), (
            f"Invariant violated: df ({alpha_df}) != len(postings) ({len(alpha_postings)})"
        )
        # Invariant 2: no duplicate indices in postings
        assert len(alpha_postings) == len(set(alpha_postings)), "Invariant violated: duplicate indices in postings list"
        # Invariant 3: df should equal num_docs (all docs have 'alpha')
        assert alpha_df == num_docs, f"doc_frequency corrupted: expected {num_docs}, got {alpha_df}"

    def test_concurrent_operations_never_produce_negative_bm25(self):
        """Concurrent add() + update_content() must never produce negative BM25 scores.

        The bot showed: race conditions can lead to df > N (same-URI duplication in
        postings), which makes IDF = log((N - df + 0.5) / (df + 0.5) + 1) negative
        when df > N, producing negative BM25 scores.
        """
        index = indexer.IndexSearch()

        # Add initial doc
        doc = indexer.Doc(
            uri="https://example.com/race",
            display_title="Race Doc",
            content="",
            index_title="race doc",
        )
        index.add(doc)

        barrier = threading.Barrier(3)
        negative_scores = []

        def adder():
            """Add more docs concurrently."""
            barrier.wait(timeout=5)
            for i in range(20):
                new_doc = indexer.Doc(
                    uri=f"https://example.com/new{i}",
                    display_title=f"New {i}",
                    content="commonterm specialword",
                    index_title=f"new {i}",
                )
                index.add(new_doc)

        def updater():
            """Update existing doc concurrently."""
            barrier.wait(timeout=5)
            for _ in range(20):
                index.update_content("https://example.com/race", "commonterm updated content")
                time.sleep(0.001)

        def searcher():
            """Search during mutations and record any negative scores."""
            barrier.wait(timeout=5)
            for _ in range(20):
                results = index.search("commonterm")
                for score, doc in results:
                    if score < 0:
                        negative_scores.append((score, doc.uri))
                time.sleep(0.001)

        threads = [
            threading.Thread(target=adder),
            threading.Thread(target=updater),
            threading.Thread(target=searcher),
        ]
        for t in threads:
            t.start()
        for t in threads:
            t.join(timeout=30)

        # No negative BM25 scores should have been observed
        assert not negative_scores, f"Negative BM25 scores observed: {negative_scores[:5]}"

        # Final integrity check: verify all invariants hold
        N = len(index.docs)
        for token, df in index.doc_frequency.items():
            postings = index.doc_indices.get(token, [])
            # Invariant: df == len(postings)
            assert df == len(postings), f"Invariant violated for {token}: df={df}, len(postings)={len(postings)}"
            # Invariant: df <= N
            assert df <= N, f"Invariant violated: doc_frequency[{token}]={df} exceeds N={N}"


class TestBlocker2CacheBeforeIndexing:
    """Reproduce BLOCKER 2: page cached before indexing succeeds.

    If update_content() raises, the page is already in _URL_CACHE, so subsequent
    calls return the cached page and never retry indexing → body search permanently empty.
    """

    @pytest.fixture(autouse=True)
    def reset_cache_state(self):
        """Reset cache module global state before each test."""
        cache._INDEX = None
        cache._URL_CACHE = {}
        cache._URL_TITLES = {}
        cache._LINKS_LOADED = False
        cache._PREFETCH_STARTED = False
        yield
        cache._INDEX = None
        cache._URL_CACHE = {}
        cache._URL_TITLES = {}
        cache._LINKS_LOADED = False
        cache._PREFETCH_STARTED = False

    def test_indexing_failure_leaves_page_unsearchable_forever(self):
        """When update_content raises, the page should NOT be cached (or should be retryable).

        Current bug: page is assigned to _URL_CACHE BEFORE update_content() is called.
        If update_content() raises, the page is cached but body terms are not indexed.
        Subsequent calls return the cached page, never retrying indexing.
        """
        # Setup: index with a doc that has empty content
        cache._INDEX = indexer.IndexSearch()
        url = "https://strandsagents.com/broken.md"
        cache._URL_CACHE[url] = None

        doc = indexer.Doc(
            uri=url,
            display_title="Broken Doc",
            content="",
            index_title="broken doc",
        )
        cache._INDEX.add(doc)

        # Verify: "specialterm" not yet searchable
        results_before = cache._INDEX.search("specialterm")
        assert len(results_before) == 0

        # Mock fetch to succeed but update_content to fail
        mock_raw = MagicMock()
        mock_raw.title = "Broken Doc"
        mock_raw.content = "This has specialterm that should be searchable."

        call_count = [0]
        original_update = cache._INDEX.update_content

        def failing_update(uri, content):
            call_count[0] += 1
            if call_count[0] == 1:
                raise RuntimeError("Simulated indexing failure")
            return original_update(uri, content)

        with patch("strands_mcp_server.utils.cache.doc_fetcher.fetch_and_clean", return_value=mock_raw):
            with patch("strands_mcp_server.utils.cache.text_processor.format_display_title", return_value="Broken Doc"):
                with patch.object(cache._INDEX, "update_content", side_effect=failing_update):
                    # First call: fetch succeeds, indexing fails
                    cache.ensure_page(url)

        # The page should either be None (not cached) or retriable
        # Current bug: page1 is not None because it was cached before indexing

        # Second call: should retry indexing, not return stale cached page
        with patch("strands_mcp_server.utils.cache.doc_fetcher.fetch_and_clean", return_value=mock_raw):
            with patch("strands_mcp_server.utils.cache.text_processor.format_display_title", return_value="Broken Doc"):
                # This time update_content should succeed (call_count[0] > 1)
                cache.ensure_page(url)

        # After retry, the term should be searchable
        results_after = cache._INDEX.search("specialterm")
        assert len(results_after) == 1, (
            f"Body term 'specialterm' not searchable after retry - "
            f"page was cached before indexing and never retried. "
            f"Got {len(results_after)} results."
        )

    def test_fetch_failure_does_not_cache_none(self):
        """When fetch_and_clean raises, the URL should remain retryable (cache stays None)."""
        cache._INDEX = indexer.IndexSearch()
        url = "https://strandsagents.com/flaky.md"
        cache._URL_CACHE[url] = None

        doc = indexer.Doc(
            uri=url,
            display_title="Flaky Doc",
            content="",
            index_title="flaky doc",
        )
        cache._INDEX.add(doc)

        call_count = [0]

        def flaky_fetch(u):
            call_count[0] += 1
            if call_count[0] == 1:
                raise ConnectionError("Network flake")
            mock_raw = MagicMock()
            mock_raw.title = "Flaky Doc"
            mock_raw.content = "flakyterm content here"
            return mock_raw

        with patch("strands_mcp_server.utils.cache.doc_fetcher.fetch_and_clean", side_effect=flaky_fetch):
            with patch("strands_mcp_server.utils.cache.text_processor.format_display_title", return_value="Flaky Doc"):
                # First call: fetch fails
                page1 = cache.ensure_page(url)
                assert page1 is None

                # Cache should still be None so retry is possible
                assert cache._URL_CACHE.get(url) is None, "Failed fetch should not populate cache"

                # Second call: fetch succeeds
                page2 = cache.ensure_page(url)
                assert page2 is not None

        # Term should be searchable
        results = cache._INDEX.search("flakyterm")
        assert len(results) == 1
