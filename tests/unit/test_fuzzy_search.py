#!/usr/bin/env python3
"""
Test script for the fuzzy search enhanced MCP server.
This script demonstrates the fuzzy matching capabilities using thefuzz.
"""

import sys
import json
from pathlib import Path

# Add src to path to import our modules
src_dir = Path(__file__).parent.parent / "src"
sys.path.insert(0, str(src_dir))

from strands_mcp_server.server import FuzzyDocumentIndex

def test_fuzzy_search_capabilities():
    """Test various fuzzy search scenarios."""
    print("=" * 70)
    print("TESTING FUZZY SEARCH CAPABILITIES")
    print("=" * 70)
    
    # Initialize the fuzzy document index
    doc_index = FuzzyDocumentIndex()
    
    if not doc_index.index.get('documents'):
        print("No documents found in index. Make sure to run the sync script first.")
        return
    
    print(f"Loaded index with {len(doc_index.index['documents'])} documents")
    print(f"Title corpus: {len(doc_index.title_corpus)} titles")
    print(f"Concept corpus: {len(doc_index.concept_corpus)} concepts")
    print(f"Category corpus: {len(doc_index.category_corpus)} categories")
    
    # Test 1: Fuzzy Title Search with typos
    print("\n" + "=" * 50)
    print("TEST 1: FUZZY TITLE SEARCH WITH TYPOS")
    print("=" * 50)
    
    typo_queries = [
        "quickstrt",  # quickstart with typo
        "agnt",       # agent with missing letters
        "deploymet",  # deployment with typo
        "exampl",     # example with missing letter
        "pythn"       # python with missing letter
    ]
    
    for query in typo_queries:
        results = doc_index.fuzzy_search_titles(query, limit=3, threshold=50)
        print(f"\nQuery: '{query}'")
        if results:
            for title, score, file_path in results:
                print(f"  - {title} (Match: {score}%) -> {file_path}")
        else:
            print("  No matches found")
    
    # Test 2: Fuzzy Concept Search
    print("\n" + "=" * 50)
    print("TEST 2: FUZZY CONCEPT SEARCH")
    print("=" * 50)
    
    concept_queries = [
        "agnt",       # agent
        "pythn",      # python
        "deploymt",   # deployment
        "api",        # exact match
        "modl"        # model
    ]
    
    for query in concept_queries:
        results = doc_index.fuzzy_search_concepts(query, limit=3, threshold=60)
        print(f"\nQuery: '{query}'")
        if results:
            for concept, score, file_paths in results:
                print(f"  - Concept: {concept} (Match: {score}%) -> {len(file_paths)} docs")
        else:
            print("  No concept matches found")
    
    # Test 3: Smart Search (Combined)
    print("\n" + "=" * 50)
    print("TEST 3: SMART SEARCH (COMBINED FUZZY MATCHING)")
    print("=" * 50)
    
    smart_queries = [
        "how to deploy agnt",     # Multiple typos
        "pythn exampl",           # Multiple concepts with typos
        "quickstrt guid",         # Title with typos
        "aws deploymet",          # Mixed concepts
        "agent tutrial"           # Mixed title/concept
    ]
    
    for query in smart_queries:
        results = doc_index.smart_search(query, limit=3)
        print(f"\nSmart Search: '{query}'")
        if results:
            for doc in results:
                print(f"  - {doc['title']} (Score: {doc['total_score']:.1f})")
                # Show what matched
                match_details = []
                for match_type, score in doc['scores'].items():
                    match_details.append(f"{match_type}: {score}%")
                print(f"    Matches: {', '.join(match_details)}")
        else:
            print("  No matches found")
    
    # Test 4: Different Fuzzy Algorithms
    print("\n" + "=" * 50)
    print("TEST 4: DIFFERENT FUZZY ALGORITHMS COMPARISON")
    print("=" * 50)
    
    from thefuzz import fuzz
    
    test_pairs = [
        ("quickstart", "quickstrt"),
        ("deployment", "deploymet"),
        ("python agent", "pythn agnt"),
        ("knowledge base", "knowlege bas"),
        ("multi agent", "multiagent")
    ]
    
    print("Comparing different fuzzy matching algorithms:")
    print("Original -> Typo | Ratio | Partial | Token Sort | Token Set")
    print("-" * 65)
    
    for original, typo in test_pairs:
        ratio = fuzz.ratio(original, typo)
        partial = fuzz.partial_ratio(original, typo)
        token_sort = fuzz.token_sort_ratio(original, typo)
        token_set = fuzz.token_set_ratio(original, typo)
        
        print(f"{original:15} -> {typo:10} | {ratio:5}% | {partial:7}% | {token_sort:10}% | {token_set:9}%")

def test_real_world_scenarios():
    """Test real-world fuzzy search scenarios."""
    print("\n" + "=" * 70)
    print("REAL-WORLD FUZZY SEARCH SCENARIOS")
    print("=" * 70)
    
    doc_index = FuzzyDocumentIndex()
    
    if not doc_index.index.get('documents'):
        print("No documents found in index.")
        return
    
    scenarios = [
        {
            "description": "User types with mobile keyboard typos",
            "queries": ["qiuckstart", "deploymebt", "examoles", "pytjon"]
        },
        {
            "description": "User remembers partial terms",
            "queries": ["quick", "deploy", "exam", "pyth"]
        },
        {
            "description": "User uses different terminology",
            "queries": ["setup", "install", "demo", "sample"]
        },
        {
            "description": "User searches with natural language",
            "queries": ["how to start", "getting started", "first steps", "begin"]
        }
    ]
    
    for scenario in scenarios:
        print(f"\nScenario: {scenario['description']}")
        print("-" * 50)
        
        for query in scenario['queries']:
            results = doc_index.smart_search(query, limit=2)
            print(f"\nQuery: '{query}'")
            if results:
                for i, doc in enumerate(results, 1):
                    print(f"  {i}. {doc['title']} (Score: {doc['total_score']:.1f})")
                    if 'matched_concept' in doc:
                        print(f"     Matched concept: {doc['matched_concept']}")
                    if 'matched_category' in doc:
                        print(f"     Matched category: {doc['matched_category']}")
            else:
                print("  No matches found")

def demonstrate_fuzzy_benefits():
    """Demonstrate the benefits of fuzzy search over exact matching."""
    print("\n" + "=" * 70)
    print("FUZZY SEARCH BENEFITS DEMONSTRATION")
    print("=" * 70)
    
    doc_index = FuzzyDocumentIndex()
    
    if not doc_index.index.get('documents'):
        print("No documents found in index.")
        return
    
    test_cases = [
        {
            "query": "agent to agent",
            "description": "Exact match - should work well"
        },
        {
            "query": "quickstrt",
            "description": "Missing letter - fuzzy search helps"
        },
        {
            "query": "quikstart",
            "description": "Transposed letters - fuzzy search helps"
        },
        {
            "query": "quick start",
            "description": "Space instead of compound - token matching helps"
        },
        {
            "query": "start quick",
            "description": "Reversed order - token set matching helps"
        }
    ]
    
    print("Comparing search effectiveness:")
    print("Query -> Description -> Results Found")
    print("-" * 60)
    
    for case in test_cases:
        results = doc_index.smart_search(case['query'], limit=3)
        result_count = len(results)
        
        print(f"{case['query']:15} -> {case['description']:30} -> {result_count} results")
        
        if results:
            best_match = results[0]
            print(f"                   Best: {best_match['title']} ({best_match['total_score']:.1f})")

def performance_comparison():
    """Compare performance of different search approaches."""
    print("\n" + "=" * 70)
    print("PERFORMANCE COMPARISON")
    print("=" * 70)
    
    doc_index = FuzzyDocumentIndex()
    
    if not doc_index.index.get('documents'):
        print("No documents found in index.")
        return
    
    import time
    
    test_queries = ["agent", "deployment", "python", "example", "quickstart"]
    
    print("Timing different search approaches:")
    print("Query -> Title Search | Concept Search | Smart Search")
    print("-" * 55)
    
    for query in test_queries:
        # Time title search
        start = time.time()
        title_results = doc_index.fuzzy_search_titles(query, limit=5)
        title_time = (time.time() - start) * 1000
        
        # Time concept search
        start = time.time()
        concept_results = doc_index.fuzzy_search_concepts(query, limit=5)
        concept_time = (time.time() - start) * 1000
        
        # Time smart search
        start = time.time()
        smart_results = doc_index.smart_search(query, limit=5)
        smart_time = (time.time() - start) * 1000
        
        print(f"{query:10} -> {title_time:8.2f}ms | {concept_time:10.2f}ms | {smart_time:8.2f}ms")

def main():
    """Main function to run all fuzzy search tests."""
    print("Fuzzy Search Enhanced MCP Server Testing Suite")
    print("This demonstrates the power of fuzzy matching with thefuzz")
    
    # Test basic fuzzy search capabilities
    test_fuzzy_search_capabilities()
    
    # Test real-world scenarios
    test_real_world_scenarios()
    
    # Demonstrate benefits
    demonstrate_fuzzy_benefits()
    
    # Performance comparison
    performance_comparison()
    
    print("\n" + "=" * 70)
    print("SUMMARY")
    print("=" * 70)
    print("The fuzzy search enhancement provides:")
    print("1. Typo tolerance - handles common typing mistakes")
    print("2. Partial matching - finds documents with incomplete queries")
    print("3. Token flexibility - handles word order and spacing differences")
    print("4. Multi-strategy search - combines different matching approaches")
    print("5. Intelligent scoring - ranks results by relevance")
    print("\nThis transforms your MCP server from exact-match-only to")
    print("intelligent, user-friendly search that works like modern search engines!")

if __name__ == "__main__":
    main()
