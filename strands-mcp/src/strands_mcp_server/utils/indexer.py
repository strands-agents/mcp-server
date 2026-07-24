from __future__ import annotations

import math
import re
import threading
from dataclasses import dataclass
from typing import Dict, List, Set, Tuple

# Enhanced tokenization patterns
_TOKEN = re.compile(r"[A-Za-z0-9_]+")
_MD_HEADER = re.compile(r"^#{1,6}\s+(.+)$", re.MULTILINE)
_MD_CODE_BLOCK = re.compile(r"```[\w]*\n([\s\S]*?)```")
_MD_INLINE_CODE = re.compile(r"`([^`]+)`")
_MD_LINK_TEXT = re.compile(r"\[([^\]]+)\]\([^)]+\)")


@dataclass(slots=True)
class Doc:
    """A single indexed document with display and search metadata.

    Attributes:
        uri: Unique identifier/URL for the document
        display_title: Human-readable title shown to users
        content: Full text content (may be empty before fetching)
        index_title: Searchable title text including variants and synonyms
    """

    uri: str
    display_title: str
    content: str
    index_title: str


# Title boost constants
_TITLE_BOOST_EMPTY = 8  # boost for unfetched content
_TITLE_BOOST_SHORT = 5  # boost for short pages (<800 chars)
_TITLE_BOOST_LONG = 3  # boost for longer pages
_SHORT_PAGE_THRESHOLD = 800  # character threshold for short pages

# BM25 parameters
_BM25_K1 = 1.5  # term frequency saturation parameter
_BM25_B = 0.75  # document length normalization parameter

# Test-only hook: if set to a callable, called mid-transaction in add()/update_content()
# after reading shared state but before writing it back. Used by concurrency tests
# to force deterministic interleaving that exposes races hidden by the GIL.
# Production: always None (zero overhead - guarded by `if _TEST_YIELD is not None`).
_TEST_YIELD: object = None


def _tokenize(text: str) -> List[str]:
    """Tokenize text into lowercase tokens."""
    return [t.lower() for t in _TOKEN.findall(text)]


def _count_doc_tokens(doc: Doc) -> int:
    """Count total tokens in a document for length normalization."""
    return len(_tokenize(doc.index_title)) + len(_tokenize(doc.content))


class IndexSearch:
    """Lightweight inverted index with BM25 scoring and Markdown awareness.

    Provides document indexing and search optimized for technical documentation.
    Uses BM25 scoring with special handling for Markdown structure elements.

    Note:
        This class is an internal implementation detail of strands-mcp-server.
        It is NOT part of the public API and may change without notice.
        Do not import or depend on it from external code.

    Thread Safety:
        All public methods (add, update_content, search) are thread-safe.
        A single lock guards all shared state mutations to ensure atomic
        read-modify-write operations when used by concurrent threads
        (e.g., background prefetch daemon + foreground ensure_page).
    """

    def __init__(self) -> None:
        """Initialize an empty search index."""
        self._lock = threading.Lock()
        self.docs: List[Doc] = []
        self.doc_frequency: Dict[str, int] = {}
        self.doc_indices: Dict[str, List[int]] = {}  # token -> doc indices
        self.uri_to_idx: Dict[str, int] = {}  # uri -> doc index for updates
        self.doc_tokens: Dict[int, Set[str]] = {}  # idx -> set of tokens (for rehydration)
        self._doc_lengths: Dict[int, int] = {}  # idx -> cached token count for BM25
        self._total_doc_length: int = 0  # sum of all document lengths for avgdl

    def _get_avgdl(self) -> float:
        """Get average document length for BM25."""
        if not self.docs:
            return 1.0
        return self._total_doc_length / len(self.docs)

    def _index_tokens_for_doc(self, idx: int, doc: Doc) -> Set[str]:
        """Extract and index tokens from a document."""
        seen: Set[str] = set()

        content = doc.content.lower()
        title_text = doc.index_title.lower()
        headers = " ".join(_MD_HEADER.findall(doc.content))
        code_blocks = " ".join(_MD_CODE_BLOCK.findall(doc.content))
        inline_code = " ".join(_MD_INLINE_CODE.findall(doc.content))
        link_text = " ".join(_MD_LINK_TEXT.findall(doc.content))

        haystack_parts = [
            title_text,
            headers.lower(),
            link_text.lower(),
            code_blocks.lower(),
            inline_code.lower(),
            content,
        ]

        haystack = " ".join(part for part in haystack_parts if part)

        for tok in _TOKEN.findall(haystack):
            tok_lower = tok.lower()
            if tok_lower not in seen:
                self.doc_indices.setdefault(tok_lower, []).append(idx)
                # Read-modify-write on doc_frequency: the vulnerable seam.
                # Test hook called between read and write to force interleaving.
                current_df = self.doc_frequency.get(tok_lower, 0)
                if _TEST_YIELD is not None:
                    _TEST_YIELD()  # type: ignore[operator]
                self.doc_frequency[tok_lower] = current_df + 1
                seen.add(tok_lower)

        return seen

    def add(self, doc: Doc) -> None:
        """Add a document to the search index.

        Thread-safe: acquires lock for the entire add operation.
        """
        with self._lock:
            idx = len(self.docs)
            self.docs.append(doc)
            self.uri_to_idx[doc.uri] = idx

            # Cache document length for BM25
            doc_len = _count_doc_tokens(doc)
            self._doc_lengths[idx] = doc_len
            self._total_doc_length += doc_len

            # Index tokens and track which tokens belong to this doc
            self.doc_tokens[idx] = self._index_tokens_for_doc(idx, doc)

    def update_content(self, uri: str, new_content: str) -> bool:
        """Update content for an existing document and reindex.

        Called when document content is hydrated after initial title-only indexing.
        Idempotent - calling with the same content multiple times is safe.

        Thread-safe: acquires lock for the entire update operation.
        """
        with self._lock:
            idx = self.uri_to_idx.get(uri)
            if idx is None:
                return False

            doc = self.docs[idx]

            # Skip if content unchanged (idempotent)
            if doc.content == new_content:
                return True

            # Update cached length and avgdl
            old_length = self._doc_lengths.get(idx, 0)
            doc.content = new_content
            new_length = _count_doc_tokens(doc)
            self._doc_lengths[idx] = new_length
            self._total_doc_length = self._total_doc_length - old_length + new_length

            # Get old tokens and new tokens
            old_tokens = self.doc_tokens.get(idx, set())
            new_tokens = self._extract_tokens(doc)

            # Tokens to remove from index (in old but not in new)
            tokens_to_remove = old_tokens - new_tokens

            # Tokens to add to index (in new but not in old)
            tokens_to_add = new_tokens - old_tokens

            # Update document frequency for removed tokens
            for tok in tokens_to_remove:
                if tok in self.doc_frequency:
                    self.doc_frequency[tok] -= 1
                    if self.doc_frequency[tok] <= 0:
                        del self.doc_frequency[tok]
                if tok in self.doc_indices:
                    try:
                        self.doc_indices[tok].remove(idx)
                    except ValueError:
                        pass
                    if not self.doc_indices[tok]:
                        del self.doc_indices[tok]

            # Add new tokens to index
            for tok in tokens_to_add:
                self.doc_indices.setdefault(tok, []).append(idx)
                # Read-modify-write on doc_frequency: the vulnerable seam.
                current_df = self.doc_frequency.get(tok, 0)
                if _TEST_YIELD is not None:
                    _TEST_YIELD()  # type: ignore[operator]
                self.doc_frequency[tok] = current_df + 1

            # Update tracked tokens
            self.doc_tokens[idx] = new_tokens

            return True

    def _extract_tokens(self, doc: Doc) -> Set[str]:
        """Extract unique tokens from a document without indexing."""
        seen: Set[str] = set()

        content = doc.content.lower()
        title_text = doc.index_title.lower()
        headers = " ".join(_MD_HEADER.findall(doc.content))
        code_blocks = " ".join(_MD_CODE_BLOCK.findall(doc.content))
        inline_code = " ".join(_MD_INLINE_CODE.findall(doc.content))
        link_text = " ".join(_MD_LINK_TEXT.findall(doc.content))

        haystack_parts = [
            title_text,
            headers.lower(),
            link_text.lower(),
            code_blocks.lower(),
            inline_code.lower(),
            content,
        ]

        haystack = " ".join(part for part in haystack_parts if part)

        for tok in _TOKEN.findall(haystack):
            seen.add(tok.lower())

        return seen

    def search(self, query: str, k: int = 8) -> List[Tuple[float, Doc]]:
        """Search the index and return ranked results.

        Uses BM25 scoring with Markdown-aware enhancements for headers (4x),
        code (2x), and links (2x). Title matches receive adaptive boosting.

        Thread-safe: acquires lock to ensure consistent reads of index state.
        """

        def _title_boost_for(doc: Doc) -> int:
            """Calculate title boost based on content length."""
            n = len(doc.content)
            if n == 0:
                return _TITLE_BOOST_EMPTY
            if n < _SHORT_PAGE_THRESHOLD:
                return _TITLE_BOOST_SHORT
            return _TITLE_BOOST_LONG

        def _calculate_md_weighted_tf(doc: Doc, token: str) -> float:
            """Calculate Markdown-weighted term frequency."""
            content_lower = doc.content.lower()
            title_lower = doc.index_title.lower()

            content_tf = content_lower.count(token)
            title_tf = title_lower.count(token) * _title_boost_for(doc)

            header_tf = 0
            for header in _MD_HEADER.findall(doc.content):
                header_tf += header.lower().count(token) * 4

            code_tf = 0
            for code in _MD_CODE_BLOCK.findall(doc.content):
                code_tf += code.lower().count(token) * 2

            link_tf = 0
            for link in _MD_LINK_TEXT.findall(doc.content):
                link_tf += link.lower().count(token) * 2

            return float(content_tf + title_tf + header_tf + code_tf + link_tf)

        def _bm25_score(idx: int, doc: Doc, token: str, idf: float, avgdl: float) -> float:
            """Calculate BM25 score for a token in a document."""
            tf = _calculate_md_weighted_tf(doc, token)
            if tf == 0:
                return 0.0

            # Use cached document length
            doc_len = doc_lengths.get(idx, 1)
            if doc_len == 0:
                doc_len = 1

            # BM25 formula
            numerator = tf * (_BM25_K1 + 1)
            denominator = tf + _BM25_K1 * (1 - _BM25_B + _BM25_B * (doc_len / avgdl))

            return idf * (numerator / denominator)

        q_tokens = [t.lower() for t in _TOKEN.findall(query)]

        # Snapshot index state under lock for consistent reads
        with self._lock:
            docs_snapshot = list(self.docs)
            doc_frequency_snapshot = dict(self.doc_frequency)
            doc_indices_snapshot = {k: list(v) for k, v in self.doc_indices.items()}
            doc_lengths = dict(self._doc_lengths)
            total_doc_length = self._total_doc_length

        scores: Dict[int, float] = {}
        N = max(len(docs_snapshot), 1)
        avgdl = total_doc_length / N if N > 0 else 1.0

        for qt in q_tokens:
            n = doc_frequency_snapshot.get(qt, 0)
            idf = math.log((N - n + 0.5) / (n + 0.5) + 1)

            for idx in doc_indices_snapshot.get(qt, []):
                if idx < len(docs_snapshot):
                    d = docs_snapshot[idx]
                    score = _bm25_score(idx, d, qt, idf, avgdl)
                    scores[idx] = scores.get(idx, 0.0) + score

        ranked = sorted(((score, docs_snapshot[i]) for i, score in scores.items()), key=lambda x: x[0], reverse=True)
        return ranked[:k]
