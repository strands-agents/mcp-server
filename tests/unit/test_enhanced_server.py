#!/usr/bin/env python3
"""
Test script for the enhanced MCP server with document indexing and relationship discovery.
This script demonstrates the new capabilities compared to the basic "1 shot" approach.
"""

import sys
import json
from pathlib import Path

# Add src to path to import our modules
src_dir = Path(__file__).parent.parent / "src"
sys.path.insert(0, str(src_dir))

from scripts.indexer import DocumentIndexer

class DocumentIndex:
    """Compatibility wrapper for FuzzyDocumentIndex to match test expectations."""
    
    def __init__(self):
        # Import here to avoid circular imports
        import sys
        from pathlib import Path
        src_dir = Path(__file__).parent.parent.parent / "src"
        if str(src_dir) not in sys.path:
            sys.path.insert(0, str(src_dir))
        
        from strands_mcp_server.server import FuzzyDocumentIndex
        self._fuzzy_index = FuzzyDocumentIndex()
        self.index = self._fuzzy_index.index
    
    def search_documents(self, query, limit=10):
        """Search documents using fuzzy search."""
        results = self._fuzzy_index.smart_search(query, limit)
        # Convert to expected format
        formatted_results = []
        for result in results:
            formatted_results.append({
                'title': result['title'],
                'score': result['total_score'],
                'file_path': result['file_path'],
                'categories': result.get('categories', []),
                'complexity_score': self.index.get('documents', {}).get(result['file_path'], {}).get('complexity_score', 0)
            })
        return formatted_results
    
    def get_related_documents(self, file_path, limit=5):
        """Get related documents."""
        return self._fuzzy_index.get_related_documents(file_path, limit)
    
    def get_all_categories(self):
        """Get all categories."""
        return self._fuzzy_index.get_all_categories()
    
    def get_documents_by_category(self, category):
        """Get documents by category."""
        return self._fuzzy_index.get_documents_by_category(category)
    
    def get_learning_path(self, topic):
        """Get learning path for a topic."""
        return self._fuzzy_index.get_learning_path(topic)
    
    def get_all_concepts(self):
        """Get all concepts."""
        return self._fuzzy_index.get_all_concepts()

def test_indexer():
    """Test the document indexer functionality."""
    print("=" * 60)
    print("TESTING DOCUMENT INDEXER")
    print("=" * 60)
    
    content_dir = Path(__file__).parent.parent / "src" / "strands_mcp_server" / "content"
    
    if not content_dir.exists():
        print(f"Content directory not found: {content_dir}")
        return
    
    print(f"Building index from: {content_dir}")
    indexer = DocumentIndexer(str(content_dir))
    index = indexer.build_index()
    
    print(f"\nIndex Statistics:")
    print(f"- Documents: {index['metadata']['total_documents']}")
    print(f"- Categories: {len(index['categories'])}")
    print(f"- Concepts: {len(index['concepts'])}")
    print(f"- Tags: {len(index['tags'])}")
    
    # Show some categories
    print(f"\nTop Categories:")
    for category, docs in list(index['categories'].items())[:5]:
        print(f"- {category}: {len(docs)} documents")
    
    # Show some concepts
    print(f"\nTop Concepts:")
    concept_counts = {name: len(docs) for name, docs in index['concepts'].items()}
    top_concepts = sorted(concept_counts.items(), key=lambda x: x[1], reverse=True)[:10]
    for concept, count in top_concepts:
        print(f"- {concept}: {count} documents")
    
    # Show relationships for a sample document
    if index['relationships']:
        sample_doc = list(index['relationships'].keys())[0]
        relationships = index['relationships'][sample_doc]
        print(f"\nSample Relationships for '{sample_doc}':")
        for rel in relationships[:3]:
            print(f"- {rel['target']} ({rel['type']}, strength: {rel['strength']:.2f})")
    
    return index

def test_enhanced_server_features():
    """Test the enhanced server features."""
    print("\n" + "=" * 60)
    print("TESTING ENHANCED SERVER FEATURES")
    print("=" * 60)
    
    # Initialize the document index
    doc_index = DocumentIndex()
    
    if not doc_index.index.get('documents'):
        print("No documents found in index. Make sure to run the sync script first.")
        return
    
    print(f"Loaded index with {len(doc_index.index['documents'])} documents")
    
    # Test search functionality
    print("\n1. TESTING SEARCH FUNCTIONALITY")
    print("-" * 40)
    
    search_queries = ["agent", "python", "deployment", "tools"]
    
    for query in search_queries:
        results = doc_index.search_documents(query, limit=3)
        print(f"\nSearch for '{query}': {len(results)} results")
        for result in results:
            print(f"  - {result['title']} (score: {result['score']})")
    
    # Test relationship discovery
    print("\n2. TESTING RELATIONSHIP DISCOVERY")
    print("-" * 40)
    
    # Get a sample document
    sample_docs = list(doc_index.index['documents'].keys())[:3]
    
    for doc_path in sample_docs:
        related = doc_index.get_related_documents(doc_path, limit=3)
        print(f"\nRelated to '{doc_path}': {len(related)} documents")
        for rel in related:
            print(f"  - {rel['title']} ({rel['relationship_type']})")
    
    # Test category browsing
    print("\n3. TESTING CATEGORY BROWSING")
    print("-" * 40)
    
    categories = doc_index.get_all_categories()
    print(f"Available categories: {len(categories)}")
    
    for category in categories[:5]:  # Show first 5 categories
        docs = doc_index.get_documents_by_category(category)
        print(f"\n{category}: {len(docs)} documents")
        for doc in docs[:2]:  # Show first 2 docs in each category
            print(f"  - {doc['title']} (complexity: {doc['complexity_score']:.1f})")
    
    # Test learning path generation
    print("\n4. TESTING LEARNING PATH GENERATION")
    print("-" * 40)
    
    topics = ["agent", "tools", "deployment"]
    
    for topic in topics:
        learning_path = doc_index.get_learning_path(topic)
        print(f"\nLearning path for '{topic}': {len(learning_path)} documents")
        
        current_section = None
        for i, doc in enumerate(learning_path[:5], 1):  # Show first 5 steps
            doc_info = doc_index.index.get('documents', {}).get(doc['file_path'], {})
            complexity = doc_info.get('complexity_score', 0)
            categories = doc_info.get('categories', [])
            
            # Determine section
            if 'Example' in categories:
                section = "Examples"
            elif complexity <= 2:
                section = "Beginner"
            elif complexity <= 4:
                section = "Intermediate"
            else:
                section = "Advanced"
            
            if section != current_section:
                print(f"  [{section}]")
                current_section = section
            
            print(f"    {i}. {doc['title']} (complexity: {complexity:.1f})")

def compare_approaches():
    """Compare the old '1 shot' approach with the new enhanced approach."""
    print("\n" + "=" * 60)
    print("COMPARING APPROACHES")
    print("=" * 60)
    
    print("OLD APPROACH (1 Shot):")
    print("- Agent provides keyword")
    print("- Server returns single document content")
    print("- No context about related documents")
    print("- No discovery of connections")
    print("- Limited to exact file path knowledge")
    
    print("\nNEW ENHANCED APPROACH:")
    print("- Agent can search by concepts, keywords, topics")
    print("- Server provides related documents automatically")
    print("- Intelligent relationship discovery")
    print("- Category-based browsing")
    print("- Learning path suggestions")
    print("- Concept exploration")
    print("- Document complexity scoring")
    
    print("\nBENEFITS FOR AGENTS:")
    print("- Better context discovery")
    print("- More comprehensive answers")
    print("- Guided learning progression")
    print("- Reduced need for exact file knowledge")
    print("- Automatic cross-referencing")

def demonstrate_use_cases():
    """Demonstrate practical use cases for the enhanced server."""
    print("\n" + "=" * 60)
    print("PRACTICAL USE CASES")
    print("=" * 60)
    
    doc_index = DocumentIndex()
    
    if not doc_index.index.get('documents'):
        print("No documents found in index.")
        return
    
    print("USE CASE 1: 'I want to learn about agents'")
    print("-" * 50)
    learning_path = doc_index.get_learning_path("agent")
    if learning_path:
        print("Enhanced server provides structured learning path:")
        for i, doc in enumerate(learning_path[:3], 1):
            print(f"  {i}. {doc['title']}")
    else:
        print("No learning path found")
    
    print("\nUSE CASE 2: 'What's related to deployment?'")
    print("-" * 50)
    search_results = doc_index.search_documents("deployment", limit=3)
    if search_results:
        print("Enhanced server finds related concepts:")
        for result in search_results:
            print(f"  - {result['title']} (categories: {', '.join(result['categories'])})")
    
    print("\nUSE CASE 3: 'Show me examples'")
    print("-" * 50)
    example_docs = doc_index.get_documents_by_category("Example")
    if example_docs:
        print("Enhanced server categorizes examples:")
        for doc in example_docs[:3]:
            print(f"  - {doc['title']} (complexity: {doc['complexity_score']:.1f})")
    
    print("\nUSE CASE 4: 'What concepts are available?'")
    print("-" * 50)
    concepts = doc_index.get_all_concepts()
    if concepts:
        concept_counts = {}
        for concept_name, docs in doc_index.index.get('concepts', {}).items():
            concept_counts[concept_name] = len(docs)
        
        top_concepts = sorted(concept_counts.items(), key=lambda x: x[1], reverse=True)[:5]
        print("Enhanced server provides concept overview:")
        for concept, count in top_concepts:
            print(f"  - {concept} ({count} documents)")

def main():
    """Main function to run all tests."""
    print("Enhanced MCP Server Testing Suite")
    print("This demonstrates the improvements over the basic '1 shot' approach")
    
    # Test the indexer
    index = test_indexer()
    
    if not index or not index.get('documents'):
        print("\nNo documents found. Please ensure you have content in the content directory.")
        print("You may need to run the sync script first:")
        print("  python scripts/sync_docs.py --target src/strands_mcp_server/content")
        return
    
    # Test enhanced server features
    test_enhanced_server_features()
    
    # Compare approaches
    compare_approaches()
    
    # Demonstrate use cases
    demonstrate_use_cases()
    
    print("\n" + "=" * 60)
    print("SUMMARY")
    print("=" * 60)
    print("The enhanced MCP server transforms your documentation from a")
    print("'1 shot' keyword lookup into an intelligent knowledge system")
    print("that helps agents discover relationships, follow learning paths,")
    print("and explore concepts systematically.")
    print("\nThis enables much richer agent interactions and better")
    print("contextual understanding of your documentation.")

if __name__ == "__main__":
    main()
