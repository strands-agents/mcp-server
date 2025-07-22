from importlib import resources
import json
from pathlib import Path
from typing import Dict, List, Optional, Any, Tuple
import logging

from mcp.server.fastmcp import FastMCP
from thefuzz import fuzz, process

logger = logging.getLogger(__name__)

pkg_resources = resources.files("strands_mcp_server")

mcp = FastMCP(
    "strands-agents-mcp-server-fuzzy",
    instructions="""
    # Strands Agents MCP Server

    This server provides advanced tools to access Strands Agents documentation with intelligent
    relationship discovery, cross-referencing capabilities, and fuzzy search matching.
    
    Strands Agents is a Python SDK for building AI agents.
    It may also be referred to as simply 'Strands'.

    The full documentation can be found at https://strandsagents.com.
    
    ## Available Tools:
    
    1. **get_document** - Retrieve a specific document by file path
    2. **fuzzy_search_documents** - Fuzzy search documents with intelligent matching
    3. **find_related_documents** - Find documents related to a given document
    4. **browse_by_category** - Browse documents by category
    5. **explore_concepts** - Explore documents by concept
    6. **get_document_overview** - Get a comprehensive overview of the documentation
    7. **get_learning_path** - Get a suggested learning path for specific topics
    8. **smart_search** - Intelligent search combining exact, fuzzy, and semantic matching
""",
)

class FuzzyDocumentIndex:
    """Enhanced document index with fuzzy search capabilities."""
    
    def __init__(self):
        self.index = {}
        self.search_cache = {}
        self.load_index()
        self._build_search_corpus()
    
    def load_index(self):
        """Load the document index from JSON file."""
        try:
            index_path = pkg_resources.joinpath("content", "document_index.json")
            if index_path.exists():
                with open(index_path, 'r', encoding='utf-8') as f:
                    self.index = json.load(f)
                logger.info(f"Loaded document index with {len(self.index.get('documents', {}))} documents")
            else:
                logger.warning("Document index not found. Some features may be limited.")
                self.index = {'documents': {}, 'relationships': {}, 'categories': {}, 'concepts': {}, 'tags': {}}
        except Exception as e:
            logger.error(f"Failed to load document index: {e}")
            self.index = {'documents': {}, 'relationships': {}, 'categories': {}, 'concepts': {}, 'tags': {}}
    
    def _build_search_corpus(self):
        """Build search corpus for fuzzy matching."""
        self.title_corpus = {}
        self.concept_corpus = {}
        self.category_corpus = {}
        self.summary_corpus = {}
        
        for file_path, doc_info in self.index.get('documents', {}).items():
            # Build title corpus
            title = doc_info.get('title', '')
            if title:
                self.title_corpus[title] = file_path
            
            # Build concept corpus
            for concept in doc_info.get('concepts', []):
                if concept not in self.concept_corpus:
                    self.concept_corpus[concept] = []
                self.concept_corpus[concept].append(file_path)
            
            # Build category corpus
            for category in doc_info.get('categories', []):
                if category not in self.category_corpus:
                    self.category_corpus[category] = []
                self.category_corpus[category].append(file_path)
            
            # Build summary corpus
            summary = doc_info.get('summary', '')
            if summary:
                self.summary_corpus[summary] = file_path
    
    def fuzzy_search_titles(self, query: str, limit: int = 10, threshold: int = 60) -> List[Tuple[str, int, str]]:
        """Fuzzy search document titles."""
        if not self.title_corpus:
            return []
        
        # Use thefuzz to find best matches
        matches = process.extract(
            query, 
            list(self.title_corpus.keys()), 
            scorer=fuzz.token_sort_ratio,
            limit=limit
        )
        
        # Filter by threshold and return with file paths
        results = []
        for title, score in matches:
            if score >= threshold:
                file_path = self.title_corpus[title]
                results.append((title, score, file_path))
        
        return results
    
    def fuzzy_search_concepts(self, query: str, limit: int = 10, threshold: int = 70) -> List[Tuple[str, int, List[str]]]:
        """Fuzzy search concepts."""
        if not self.concept_corpus:
            return []
        
        matches = process.extract(
            query,
            list(self.concept_corpus.keys()),
            scorer=fuzz.partial_ratio,
            limit=limit
        )
        
        results = []
        for concept, score in matches:
            if score >= threshold:
                file_paths = self.concept_corpus[concept]
                results.append((concept, score, file_paths))
        
        return results
    
    def fuzzy_search_categories(self, query: str, limit: int = 5, threshold: int = 70) -> List[Tuple[str, int, List[str]]]:
        """Fuzzy search categories."""
        if not self.category_corpus:
            return []
        
        matches = process.extract(
            query,
            list(self.category_corpus.keys()),
            scorer=fuzz.token_set_ratio,
            limit=limit
        )
        
        results = []
        for category, score in matches:
            if score >= threshold:
                file_paths = self.category_corpus[category]
                results.append((category, score, file_paths))
        
        return results
    
    def smart_search(self, query: str, limit: int = 10) -> List[Dict]:
        """Intelligent search combining multiple fuzzy matching strategies."""
        all_results = {}  # file_path -> result info
        
        # 1. Fuzzy search titles (highest weight)
        title_matches = self.fuzzy_search_titles(query, limit=limit*2, threshold=50)
        for title, score, file_path in title_matches:
            if file_path not in all_results:
                doc_info = self.index.get('documents', {}).get(file_path, {})
                all_results[file_path] = {
                    'file_path': file_path,
                    'title': title,
                    'summary': doc_info.get('summary', ''),
                    'categories': doc_info.get('categories', []),
                    'concepts': doc_info.get('concepts', [])[:5],
                    'scores': {'title': score},
                    'total_score': score * 2.0  # Weight title matches higher
                }
            else:
                all_results[file_path]['scores']['title'] = score
                all_results[file_path]['total_score'] += score * 2.0
        
        # 2. Fuzzy search concepts
        concept_matches = self.fuzzy_search_concepts(query, limit=limit*2, threshold=60)
        for concept, score, file_paths in concept_matches:
            for file_path in file_paths:
                if file_path not in all_results:
                    doc_info = self.index.get('documents', {}).get(file_path, {})
                    all_results[file_path] = {
                        'file_path': file_path,
                        'title': doc_info.get('title', 'Untitled'),
                        'summary': doc_info.get('summary', ''),
                        'categories': doc_info.get('categories', []),
                        'concepts': doc_info.get('concepts', [])[:5],
                        'scores': {'concept': score},
                        'total_score': score * 1.5,
                        'matched_concept': concept
                    }
                else:
                    if 'concept' not in all_results[file_path]['scores']:
                        all_results[file_path]['scores']['concept'] = score
                        all_results[file_path]['total_score'] += score * 1.5
                        all_results[file_path]['matched_concept'] = concept
        
        # 3. Fuzzy search categories
        category_matches = self.fuzzy_search_categories(query, limit=limit, threshold=60)
        for category, score, file_paths in category_matches:
            for file_path in file_paths:
                if file_path not in all_results:
                    doc_info = self.index.get('documents', {}).get(file_path, {})
                    all_results[file_path] = {
                        'file_path': file_path,
                        'title': doc_info.get('title', 'Untitled'),
                        'summary': doc_info.get('summary', ''),
                        'categories': doc_info.get('categories', []),
                        'concepts': doc_info.get('concepts', [])[:5],
                        'scores': {'category': score},
                        'total_score': score * 1.0,
                        'matched_category': category
                    }
                else:
                    if 'category' not in all_results[file_path]['scores']:
                        all_results[file_path]['scores']['category'] = score
                        all_results[file_path]['total_score'] += score * 1.0
                        all_results[file_path]['matched_category'] = category
        
        # 4. Fuzzy search in summaries
        for file_path, doc_info in self.index.get('documents', {}).items():
            summary = doc_info.get('summary', '')
            if summary:
                # Use partial ratio for summary matching
                score = fuzz.partial_ratio(query.lower(), summary.lower())
                if score >= 50:  # Lower threshold for summary matches
                    if file_path not in all_results:
                        all_results[file_path] = {
                            'file_path': file_path,
                            'title': doc_info.get('title', 'Untitled'),
                            'summary': summary,
                            'categories': doc_info.get('categories', []),
                            'concepts': doc_info.get('concepts', [])[:5],
                            'scores': {'summary': score},
                            'total_score': score * 0.8
                        }
                    else:
                        if 'summary' not in all_results[file_path]['scores']:
                            all_results[file_path]['scores']['summary'] = score
                            all_results[file_path]['total_score'] += score * 0.8
        
        # Sort by total score and return top results
        sorted_results = sorted(all_results.values(), key=lambda x: x['total_score'], reverse=True)
        return sorted_results[:limit]
    
    def get_document_info(self, file_path: str) -> Optional[Dict]:
        """Get information about a specific document."""
        return self.index.get('documents', {}).get(file_path)
    
    def get_related_documents(self, file_path: str, limit: int = 5) -> List[Dict]:
        """Get documents related to the specified document."""
        relationships = self.index.get('relationships', {}).get(file_path, [])
        
        results = []
        for rel in relationships[:limit]:
            target_doc = self.index.get('documents', {}).get(rel['target'])
            if target_doc:
                results.append({
                    'file_path': rel['target'],
                    'title': target_doc.get('title', 'Untitled'),
                    'summary': target_doc.get('summary', ''),
                    'relationship_type': rel['type'],
                    'relationship_strength': rel['strength'],
                    'relationship_context': rel.get('context', '')
                })
        
        return results
    
    def get_documents_by_category(self, category: str) -> List[Dict]:
        """Get all documents in a specific category."""
        file_paths = self.index.get('categories', {}).get(category, [])
        
        results = []
        for file_path in file_paths:
            doc_info = self.index.get('documents', {}).get(file_path)
            if doc_info:
                results.append({
                    'file_path': file_path,
                    'title': doc_info.get('title', 'Untitled'),
                    'summary': doc_info.get('summary', ''),
                    'complexity_score': doc_info.get('complexity_score', 0)
                })
        
        # Sort by complexity (easier first)
        results.sort(key=lambda x: x['complexity_score'])
        return results
    
    def get_documents_by_concept(self, concept: str) -> List[Dict]:
        """Get all documents related to a specific concept."""
        concept_info = self.index.get('concepts', {}).get(concept, [])
        
        results = []
        for item in concept_info:
            results.append({
                'file_path': item['file_path'],
                'title': item['title'],
                'context': item['context']
            })
        
        return results
    
    def get_all_categories(self) -> List[str]:
        """Get all available categories."""
        return list(self.index.get('categories', {}).keys())
    
    def get_all_concepts(self) -> List[str]:
        """Get all available concepts."""
        return list(self.index.get('concepts', {}).keys())
    
    def get_learning_path(self, topic: str) -> List[Dict]:
        """Generate a suggested learning path for a topic using fuzzy search."""
        # Use smart search to find related documents
        related_docs = self.smart_search(topic, limit=20)
        
        if not related_docs:
            return []
        
        # Categorize documents by complexity and type
        beginner_docs = []
        intermediate_docs = []
        advanced_docs = []
        examples = []
        
        for doc in related_docs:
            doc_info = self.index.get('documents', {}).get(doc['file_path'], {})
            complexity = doc_info.get('complexity_score', 0)
            categories = doc_info.get('categories', [])
            
            if 'Example' in categories:
                examples.append(doc)
            elif complexity <= 2:
                beginner_docs.append(doc)
            elif complexity <= 4:
                intermediate_docs.append(doc)
            else:
                advanced_docs.append(doc)
        
        # Build learning path
        learning_path = []
        
        # Start with beginner concepts
        if beginner_docs:
            learning_path.extend(beginner_docs[:3])
        
        # Add some examples
        if examples:
            learning_path.extend(examples[:2])
        
        # Add intermediate content
        if intermediate_docs:
            learning_path.extend(intermediate_docs[:3])
        
        # Add advanced content
        if advanced_docs:
            learning_path.extend(advanced_docs[:2])
        
        return learning_path

# Initialize the fuzzy document index
doc_index = FuzzyDocumentIndex()

@mcp.tool()
async def get_document(file_path: str) -> str:
    """
    Get the content of a specific documentation file.
    
    Args:
        file_path: The relative path to the markdown file (e.g., 'user-guide/quickstart.md')
    
    Returns:
        The full content of the requested document
    """
    try:
        content = pkg_resources.joinpath("content", file_path).read_text(encoding="utf-8")
        
        # Add related documents information
        related = doc_index.get_related_documents(file_path, limit=3)
        if related:
            content += "\n\n## Related Documents\n\n"
            for rel_doc in related:
                content += f"- **{rel_doc['title']}** ({rel_doc['file_path']})\n"
                content += f"  - {rel_doc['summary']}\n"
                content += f"  - Relationship: {rel_doc['relationship_context']}\n\n"
        
        return content
    except FileNotFoundError:
        return f"Document not found: {file_path}"
    except Exception as e:
        return f"Error reading document: {str(e)}"

@mcp.tool()
async def fuzzy_search_documents(query: str, limit: int = 10, search_type: str = "all") -> str:
    """
    Fuzzy search for documents using intelligent matching algorithms.
    
    Args:
        query: Search query (can be imprecise, with typos, or partial matches)
        limit: Maximum number of results to return (default: 10)
        search_type: Type of search - "titles", "concepts", "categories", or "all" (default: "all")
    
    Returns:
        A formatted list of matching documents with fuzzy match scores
    """
    if search_type == "titles":
        results = doc_index.fuzzy_search_titles(query, limit)
        if not results:
            return f"No documents found with titles matching '{query}'"
        
        response = f"## Fuzzy Title Search Results for '{query}'\n\n"
        for title, score, file_path in results:
            response += f"### {title} (Match: {score}%)\n"
            response += f"**File:** {file_path}\n\n"
    
    elif search_type == "concepts":
        results = doc_index.fuzzy_search_concepts(query, limit)
        if not results:
            return f"No concepts found matching '{query}'"
        
        response = f"## Fuzzy Concept Search Results for '{query}'\n\n"
        for concept, score, file_paths in results:
            response += f"### Concept: {concept} (Match: {score}%)\n"
            response += f"**Documents:** {len(file_paths)}\n"
            for file_path in file_paths[:3]:  # Show first 3 documents
                doc_info = doc_index.get_document_info(file_path)
                if doc_info:
                    response += f"- {doc_info.get('title', 'Untitled')} ({file_path})\n"
            if len(file_paths) > 3:
                response += f"- ... and {len(file_paths) - 3} more\n"
            response += "\n"
    
    elif search_type == "categories":
        results = doc_index.fuzzy_search_categories(query, limit)
        if not results:
            return f"No categories found matching '{query}'"
        
        response = f"## Fuzzy Category Search Results for '{query}'\n\n"
        for category, score, file_paths in results:
            response += f"### Category: {category} (Match: {score}%)\n"
            response += f"**Documents:** {len(file_paths)}\n"
            for file_path in file_paths[:3]:  # Show first 3 documents
                doc_info = doc_index.get_document_info(file_path)
                if doc_info:
                    response += f"- {doc_info.get('title', 'Untitled')} ({file_path})\n"
            if len(file_paths) > 3:
                response += f"- ... and {len(file_paths) - 3} more\n"
            response += "\n"
    
    else:  # search_type == "all"
        results = doc_index.smart_search(query, limit)
        if not results:
            return f"No documents found matching '{query}'"
        
        response = f"## Smart Fuzzy Search Results for '{query}'\n\n"
        response += f"Found {len(results)} matching documents:\n\n"
        
        for i, doc in enumerate(results, 1):
            response += f"### {i}. {doc['title']}\n"
            response += f"**File:** {doc['file_path']}\n"
            response += f"**Total Score:** {doc['total_score']:.1f}\n"
            
            # Show match details
            match_details = []
            if 'title' in doc['scores']:
                match_details.append(f"Title: {doc['scores']['title']}%")
            if 'concept' in doc['scores']:
                match_details.append(f"Concept: {doc['scores']['concept']}%")
                if 'matched_concept' in doc:
                    match_details.append(f"(matched: {doc['matched_concept']})")
            if 'category' in doc['scores']:
                match_details.append(f"Category: {doc['scores']['category']}%")
                if 'matched_category' in doc:
                    match_details.append(f"(matched: {doc['matched_category']})")
            if 'summary' in doc['scores']:
                match_details.append(f"Summary: {doc['scores']['summary']}%")
            
            if match_details:
                response += f"**Match Details:** {', '.join(match_details)}\n"
            
            response += f"**Summary:** {doc['summary']}\n"
            if doc['categories']:
                response += f"**Categories:** {', '.join(doc['categories'])}\n"
            if doc['concepts']:
                response += f"**Key Concepts:** {', '.join(doc['concepts'])}\n"
            response += "\n"
    
    return response

@mcp.tool()
async def smart_search(query: str, limit: int = 10) -> str:
    """
    Intelligent search combining exact matching, fuzzy matching, and semantic analysis.
    
    Args:
        query: Search query (natural language, keywords, or concepts)
        limit: Maximum number of results to return (default: 10)
    
    Returns:
        Comprehensive search results with relevance scoring
    """
    results = doc_index.smart_search(query, limit)
    
    if not results:
        return f"No documents found matching '{query}'"
    
    response = f"# Smart Search Results for '{query}'\n\n"
    response += f"Found {len(results)} relevant documents using intelligent matching:\n\n"
    
    for i, doc in enumerate(results, 1):
        response += f"## {i}. {doc['title']}\n"
        response += f"**File:** {doc['file_path']}\n"
        response += f"**Relevance Score:** {doc['total_score']:.1f}\n"
        
        # Detailed match breakdown
        response += f"**Match Analysis:**\n"
        for match_type, score in doc['scores'].items():
            response += f"- {match_type.title()}: {score}%\n"
        
        # Show what was matched
        matched_items = []
        if 'matched_concept' in doc:
            matched_items.append(f"Concept: {doc['matched_concept']}")
        if 'matched_category' in doc:
            matched_items.append(f"Category: {doc['matched_category']}")
        
        if matched_items:
            response += f"**Matched:** {', '.join(matched_items)}\n"
        
        response += f"**Summary:** {doc['summary']}\n"
        
        if doc['categories']:
            response += f"**Categories:** {', '.join(doc['categories'])}\n"
        if doc['concepts']:
            response += f"**Key Concepts:** {', '.join(doc['concepts'])}\n"
        
        response += "\n"
    
    return response

@mcp.tool()
async def find_related_documents(file_path: str, limit: int = 5) -> str:
    """
    Find documents related to a specific document.
    
    Args:
        file_path: The path to the source document
        limit: Maximum number of related documents to return (default: 5)
    
    Returns:
        A list of related documents with relationship information
    """
    related = doc_index.get_related_documents(file_path, limit)
    
    if not related:
        return f"No related documents found for '{file_path}'"
    
    response = f"## Documents Related to '{file_path}'\n\n"
    
    for i, doc in enumerate(related, 1):
        response += f"### {i}. {doc['title']}\n"
        response += f"**File:** {doc['file_path']}\n"
        response += f"**Relationship:** {doc['relationship_type']} (strength: {doc['relationship_strength']:.2f})\n"
        response += f"**Context:** {doc['relationship_context']}\n"
        response += f"**Summary:** {doc['summary']}\n\n"
    
    return response

@mcp.tool()
async def browse_by_category(category: str = None) -> str:
    """
    Browse documents by category or list all available categories.
    
    Args:
        category: The category to browse (optional - if not provided, lists all categories)
    
    Returns:
        Either a list of categories or documents in the specified category
    """
    if category is None:
        categories = doc_index.get_all_categories()
        if not categories:
            return "No categories available"
        
        response = "## Available Categories\n\n"
        for cat in sorted(categories):
            doc_count = len(doc_index.get_documents_by_category(cat))
            response += f"- **{cat}** ({doc_count} documents)\n"
        
        return response
    
    documents = doc_index.get_documents_by_category(category)
    
    if not documents:
        return f"No documents found in category '{category}'"
    
    response = f"## Documents in Category: {category}\n\n"
    response += f"Found {len(documents)} documents (ordered by complexity):\n\n"
    
    for i, doc in enumerate(documents, 1):
        response += f"### {i}. {doc['title']}\n"
        response += f"**File:** {doc['file_path']}\n"
        response += f"**Complexity:** {doc['complexity_score']:.1f}/10\n"
        response += f"**Summary:** {doc['summary']}\n\n"
    
    return response

@mcp.tool()
async def explore_concepts(concept: str = None) -> str:
    """
    Explore documents by concept or list all available concepts.
    
    Args:
        concept: The concept to explore (optional - if not provided, lists all concepts)
    
    Returns:
        Either a list of concepts or documents related to the specified concept
    """
    if concept is None:
        concepts = doc_index.get_all_concepts()
        if not concepts:
            return "No concepts available"
        
        # Show top 50 most common concepts
        concept_counts = {}
        for concept_name, docs in doc_index.index.get('concepts', {}).items():
            concept_counts[concept_name] = len(docs)
        
        sorted_concepts = sorted(concept_counts.items(), key=lambda x: x[1], reverse=True)[:50]
        
        response = "## Top Concepts (by document frequency)\n\n"
        for concept_name, count in sorted_concepts:
            response += f"- **{concept_name}** ({count} documents)\n"
        
        return response
    
    documents = doc_index.get_documents_by_concept(concept)
    
    if not documents:
        return f"No documents found for concept '{concept}'"
    
    response = f"## Documents Related to Concept: {concept}\n\n"
    response += f"Found {len(documents)} documents:\n\n"
    
    for i, doc in enumerate(documents, 1):
        response += f"### {i}. {doc['title']}\n"
        response += f"**File:** {doc['file_path']}\n"
        response += f"**Context:** {doc['context']}\n\n"
    
    return response

@mcp.tool()
async def get_document_overview() -> str:
    """
    Get a comprehensive overview of the documentation structure.
    
    Returns:
        An overview of the documentation including statistics and organization
    """
    metadata = doc_index.index.get('metadata', {})
    categories = doc_index.index.get('categories', {})
    concepts = doc_index.index.get('concepts', {})
    
    response = "# Strands Agents Documentation Overview\n\n"
    
    # Statistics
    response += "## Statistics\n\n"
    response += f"- **Total Documents:** {metadata.get('total_documents', 0)}\n"
    response += f"- **Categories:** {len(categories)}\n"
    response += f"- **Concepts:** {len(concepts)}\n"
    response += f"- **Last Updated:** {metadata.get('last_updated', 'Unknown')}\n\n"
    
    # Categories breakdown
    response += "## Documentation Structure\n\n"
    for category, file_paths in sorted(categories.items()):
        response += f"### {category} ({len(file_paths)} documents)\n"
        
        # Get a few example documents from this category
        examples = doc_index.get_documents_by_category(category)[:3]
        for doc in examples:
            response += f"- {doc['title']}\n"
        
        if len(file_paths) > 3:
            response += f"- ... and {len(file_paths) - 3} more\n"
        response += "\n"
    
    # Popular concepts
    concept_counts = {name: len(docs) for name, docs in concepts.items()}
    top_concepts = sorted(concept_counts.items(), key=lambda x: x[1], reverse=True)[:10]
    
    response += "## Most Common Concepts\n\n"
    for concept, count in top_concepts:
        response += f"- **{concept}** (appears in {count} documents)\n"
    
    return response

@mcp.tool()
async def get_learning_path(topic: str) -> str:
    """
    Get a suggested learning path for a specific topic using fuzzy search.
    
    Args:
        topic: The topic you want to learn about
    
    Returns:
        A structured learning path with documents ordered by complexity and learning progression
    """
    learning_path = doc_index.get_learning_path(topic)
    
    if not learning_path:
        return f"No learning path found for topic '{topic}'. Try using fuzzy search to find related documents first."
    
    response = f"# Learning Path: {topic}\n\n"
    response += f"Here's a suggested learning path with {len(learning_path)} documents:\n\n"
    
    current_section = None
    for i, doc in enumerate(learning_path, 1):
        doc_info = doc_index.index.get('documents', {}).get(doc['file_path'], {})
        complexity = doc_info.get('complexity_score', 0)
        categories = doc_info.get('categories', [])
        
        # Determine section
        if 'Example' in categories:
            section = "Examples & Practice"
        elif complexity <= 2:
            section = "Getting Started"
        elif complexity <= 4:
            section = "Intermediate Topics"
        else:
            section = "Advanced Topics"
        
        # Add section header if changed
        if section != current_section:
            response += f"## {section}\n\n"
            current_section = section
        
        response += f"### {i}. {doc['title']}\n"
        response += f"**File:** {doc['file_path']}\n"
        response += f"**Complexity:** {complexity:.1f}/10\n"
        response += f"**Summary:** {doc['summary']}\n"
        
        # Show fuzzy match score if available
        if 'total_score' in doc:
            response += f"**Relevance:** {doc['total_score']:.1f}\n"
        
        # Add related documents for context
        related = doc_index.get_related_documents(doc['file_path'], limit=2)
        if related:
            response += f"**Related:** "
            response += ", ".join([r['title'] for r in related])
            response += "\n"
        
        response += "\n"
    
    return response

def main():
    """Main function to run the fuzzy enhanced MCP server."""
    logger.info("Starting Fuzzy Enhanced Strands Agents MCP Server")
    # Initialize dynamic documentation tools for backward compatibility
    mcp.run()

if __name__ == "__main__":
    main()
