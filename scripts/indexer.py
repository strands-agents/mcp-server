#!/usr/bin/env python3
"""
Document indexer for building relationships and cross-references between markdown files.
This module creates a comprehensive index that helps agents discover related documents.
"""

import os
import re
import json
from pathlib import Path
from typing import Dict, List, Set, Tuple, Optional
from collections import defaultdict
import logging

logger = logging.getLogger(__name__)

class DocumentIndexer:
    """
    Builds an index of markdown documents with relationships, cross-references, and metadata.
    """
    
    def __init__(self, content_dir: str):
        self.content_dir = Path(content_dir)
        self.index = {
            'documents': {},
            'relationships': {},
            'tags': defaultdict(list),
            'categories': defaultdict(list),
            'cross_references': defaultdict(list),
            'concepts': defaultdict(list),
            'metadata': {
                'total_documents': 0,
                'last_updated': None,
                'version': '1.0'
            }
        }
    
    def build_index(self) -> Dict:
        """
        Build a comprehensive index of all markdown documents.
        
        Returns:
            Dict: Complete index with relationships and metadata
        """
        logger.info(f"Building document index from {self.content_dir}")
        
        # First pass: Extract basic document information
        documents = self._scan_documents()
        
        # Second pass: Build relationships and cross-references
        self._build_relationships(documents)
        
        # Third pass: Extract concepts and categorize
        self._extract_concepts(documents)
        
        # Update metadata
        self.index['metadata']['total_documents'] = len(documents)
        self.index['metadata']['last_updated'] = self._get_current_timestamp()
        
        logger.info(f"Index built with {len(documents)} documents")
        return self.index
    
    def _scan_documents(self) -> Dict[str, Dict]:
        """Scan all markdown files and extract basic information."""
        documents = {}
        
        for md_file in self.content_dir.glob('**/*.md'):
            rel_path = str(md_file.relative_to(self.content_dir))
            
            try:
                with open(md_file, 'r', encoding='utf-8') as f:
                    content = f.read()
                
                doc_info = self._extract_document_info(content, rel_path)
                documents[rel_path] = doc_info
                self.index['documents'][rel_path] = doc_info
                
            except Exception as e:
                logger.error(f"Error processing {rel_path}: {e}")
                continue
        
        return documents
    
    def _extract_document_info(self, content: str, file_path: str) -> Dict:
        """Extract comprehensive information from a document."""
        lines = content.split('\n')
        
        # Extract title
        title = self._extract_title(lines)
        
        # Extract headers for structure
        headers = self._extract_headers(lines)
        
        # Extract links (both internal and external)
        internal_links, external_links = self._extract_links(content)
        
        # Extract code blocks and their languages
        code_blocks = self._extract_code_blocks(content)
        
        # Extract tags and categories from content
        tags = self._extract_tags(content)
        categories = self._infer_categories(file_path, content)
        
        # Extract key concepts and terms
        concepts = self._extract_key_concepts(content)
        
        # Calculate document metrics
        word_count = len(content.split())
        complexity_score = self._calculate_complexity(content, headers, code_blocks)
        
        return {
            'title': title,
            'file_path': file_path,
            'headers': headers,
            'internal_links': internal_links,
            'external_links': external_links,
            'code_blocks': code_blocks,
            'tags': tags,
            'categories': categories,
            'concepts': concepts,
            'word_count': word_count,
            'complexity_score': complexity_score,
            'summary': self._generate_summary(content, title)
        }
    
    def _extract_title(self, lines: List[str]) -> str:
        """Extract document title from first header or filename."""
        for line in lines:
            line = line.strip()
            if line.startswith('# '):
                return line[2:].strip()
        return "Untitled Document"
    
    def _extract_headers(self, lines: List[str]) -> List[Dict]:
        """Extract all headers with their levels and content."""
        headers = []
        for i, line in enumerate(lines):
            line = line.strip()
            if line.startswith('#'):
                level = len(line) - len(line.lstrip('#'))
                if level <= 6:  # Valid markdown header levels
                    content = line[level:].strip()
                    headers.append({
                        'level': level,
                        'content': content,
                        'line_number': i + 1
                    })
        return headers
    
    def _extract_links(self, content: str) -> Tuple[List[str], List[str]]:
        """Extract internal and external links from markdown content."""
        # Markdown link pattern: [text](url)
        link_pattern = r'\[([^\]]+)\]\(([^)]+)\)'
        links = re.findall(link_pattern, content)
        
        internal_links = []
        external_links = []
        
        for text, url in links:
            if url.startswith(('http://', 'https://')):
                external_links.append({'text': text, 'url': url})
            elif url.endswith('.md') or '/' in url:
                internal_links.append({'text': text, 'url': url})
        
        return internal_links, external_links
    
    def _extract_code_blocks(self, content: str) -> List[Dict]:
        """Extract code blocks with their languages."""
        code_blocks = []
        
        # Pattern for fenced code blocks
        pattern = r'```(\w+)?\n(.*?)\n```'
        matches = re.findall(pattern, content, re.DOTALL)
        
        for language, code in matches:
            code_blocks.append({
                'language': language or 'text',
                'code': code.strip(),
                'length': len(code.strip().split('\n'))
            })
        
        return code_blocks
    
    def _extract_tags(self, content: str) -> List[str]:
        """Extract tags from content (looking for common tag patterns)."""
        tags = set()
        
        # Look for hashtag-style tags
        hashtag_pattern = r'#(\w+)'
        hashtags = re.findall(hashtag_pattern, content)
        tags.update(hashtags)
        
        # Look for common technical terms that could be tags
        tech_terms = [
            'python', 'javascript', 'typescript', 'react', 'vue', 'angular',
            'aws', 'azure', 'gcp', 'docker', 'kubernetes', 'api', 'rest',
            'graphql', 'database', 'sql', 'nosql', 'mongodb', 'postgresql',
            'redis', 'elasticsearch', 'kafka', 'rabbitmq', 'nginx', 'apache'
        ]
        
        content_lower = content.lower()
        for term in tech_terms:
            if term in content_lower:
                tags.add(term)
        
        return list(tags)
    
    def _infer_categories(self, file_path: str, content: str) -> List[str]:
        """Infer document categories from path and content."""
        categories = []
        
        # Categories from file path
        path_parts = Path(file_path).parts
        for part in path_parts[:-1]:  # Exclude filename
            if part not in ['content', 'docs']:
                categories.append(part.replace('-', ' ').replace('_', ' ').title())
        
        # Categories from content analysis
        content_lower = content.lower()
        
        category_keywords = {
            'Tutorial': ['tutorial', 'guide', 'how to', 'step by step', 'walkthrough'],
            'API Reference': ['api', 'reference', 'endpoint', 'method', 'parameter'],
            'Example': ['example', 'sample', 'demo', 'illustration'],
            'Concept': ['concept', 'overview', 'introduction', 'understanding'],
            'Deployment': ['deploy', 'deployment', 'production', 'hosting'],
            'Configuration': ['config', 'configuration', 'setup', 'install'],
            'Troubleshooting': ['troubleshoot', 'debug', 'error', 'problem', 'issue']
        }
        
        for category, keywords in category_keywords.items():
            if any(keyword in content_lower for keyword in keywords):
                categories.append(category)
        
        return list(set(categories))
    
    def _extract_key_concepts(self, content: str) -> List[str]:
        """Extract key concepts and important terms from content."""
        concepts = set()
        
        # Extract terms from headers
        header_pattern = r'^#+\s+(.+)$'
        headers = re.findall(header_pattern, content, re.MULTILINE)
        for header in headers:
            # Split header into words and add significant ones
            words = re.findall(r'\b[A-Z][a-z]+\b', header)
            concepts.update(words)
        
        # Extract capitalized terms (likely proper nouns/concepts)
        capitalized_pattern = r'\b[A-Z][a-z]{2,}\b'
        capitalized_terms = re.findall(capitalized_pattern, content)
        
        # Filter out common words
        common_words = {'The', 'This', 'That', 'With', 'For', 'And', 'But', 'You', 'Your'}
        significant_terms = [term for term in capitalized_terms if term not in common_words]
        concepts.update(significant_terms)
        
        # Extract terms in backticks (code/technical terms)
        backtick_pattern = r'`([^`]+)`'
        code_terms = re.findall(backtick_pattern, content)
        concepts.update(code_terms)
        
        return list(concepts)[:20]  # Limit to top 20 concepts
    
    def _calculate_complexity(self, content: str, headers: List[Dict], code_blocks: List[Dict]) -> float:
        """Calculate a complexity score for the document."""
        score = 0.0
        
        # Base score from word count
        word_count = len(content.split())
        score += min(word_count / 1000, 5.0)  # Max 5 points for length
        
        # Points for structure (headers)
        score += min(len(headers) * 0.5, 3.0)  # Max 3 points for structure
        
        # Points for code blocks
        score += min(len(code_blocks) * 0.3, 2.0)  # Max 2 points for code
        
        # Points for links and references
        link_count = len(re.findall(r'\[([^\]]+)\]\(([^)]+)\)', content))
        score += min(link_count * 0.2, 2.0)  # Max 2 points for links
        
        return round(score, 2)
    
    def _generate_summary(self, content: str, title: str) -> str:
        """Generate a brief summary of the document."""
        # Take first paragraph or first few sentences
        paragraphs = content.split('\n\n')
        
        for paragraph in paragraphs:
            paragraph = paragraph.strip()
            if paragraph and not paragraph.startswith('#') and len(paragraph) > 50:
                # Take first 200 characters
                summary = paragraph[:200]
                if len(paragraph) > 200:
                    summary += "..."
                return summary
        
        return f"Documentation for {title}"
    
    def _build_relationships(self, documents: Dict[str, Dict]):
        """Build relationships between documents based on links and content similarity."""
        for file_path, doc_info in documents.items():
            relationships = []
            
            # Direct link relationships
            for link in doc_info['internal_links']:
                target_path = self._resolve_link_path(link['url'], file_path)
                if target_path and target_path in documents:
                    relationships.append({
                        'type': 'direct_link',
                        'target': target_path,
                        'strength': 1.0,
                        'context': link['text']
                    })
            
            # Category-based relationships
            for other_path, other_doc in documents.items():
                if other_path != file_path:
                    common_categories = set(doc_info['categories']) & set(other_doc['categories'])
                    if common_categories:
                        relationships.append({
                            'type': 'category_similarity',
                            'target': other_path,
                            'strength': len(common_categories) * 0.3,
                            'context': f"Shared categories: {', '.join(common_categories)}"
                        })
            
            # Concept-based relationships
            for other_path, other_doc in documents.items():
                if other_path != file_path:
                    common_concepts = set(doc_info['concepts']) & set(other_doc['concepts'])
                    if len(common_concepts) >= 2:  # At least 2 shared concepts
                        relationships.append({
                            'type': 'concept_similarity',
                            'target': other_path,
                            'strength': len(common_concepts) * 0.2,
                            'context': f"Shared concepts: {', '.join(list(common_concepts)[:3])}"
                        })
            
            # Sort by strength and keep top relationships
            relationships.sort(key=lambda x: x['strength'], reverse=True)
            self.index['relationships'][file_path] = relationships[:10]  # Keep top 10
    
    def _resolve_link_path(self, link_url: str, current_file: str) -> Optional[str]:
        """Resolve a relative link to an absolute path within the content directory."""
        if link_url.startswith('/'):
            # Absolute path from content root
            return link_url[1:] if link_url.endswith('.md') else None
        
        # Relative path
        current_dir = Path(current_file).parent
        resolved_path = current_dir / link_url
        
        try:
            # Normalize the path
            normalized = resolved_path.resolve()
            relative_to_content = normalized.relative_to(self.content_dir.resolve())
            return str(relative_to_content)
        except (ValueError, OSError):
            return None
    
    def _extract_concepts(self, documents: Dict[str, Dict]):
        """Extract and categorize concepts across all documents."""
        # Build concept index
        for file_path, doc_info in documents.items():
            for concept in doc_info['concepts']:
                self.index['concepts'][concept].append({
                    'file_path': file_path,
                    'title': doc_info['title'],
                    'context': doc_info['summary'][:100] + "..."
                })
            
            for tag in doc_info['tags']:
                self.index['tags'][tag].append(file_path)
            
            for category in doc_info['categories']:
                self.index['categories'][category].append(file_path)
    
    def _get_current_timestamp(self) -> str:
        """Get current timestamp in ISO format."""
        from datetime import datetime
        return datetime.now().isoformat()
    
    def save_index(self, output_path: str):
        """Save the index to a JSON file."""
        with open(output_path, 'w', encoding='utf-8') as f:
            json.dump(self.index, f, indent=2, ensure_ascii=False)
        logger.info(f"Index saved to {output_path}")
    
    def load_index(self, input_path: str) -> Dict:
        """Load an existing index from a JSON file."""
        try:
            with open(input_path, 'r', encoding='utf-8') as f:
                self.index = json.load(f)
            logger.info(f"Index loaded from {input_path}")
            return self.index
        except FileNotFoundError:
            logger.warning(f"Index file not found: {input_path}")
            return {}
        except json.JSONDecodeError as e:
            logger.error(f"Error loading index: {e}")
            return {}

def main():
    """CLI interface for building document index."""
    import argparse
    
    parser = argparse.ArgumentParser(description="Build document index for MCP server")
    parser.add_argument("--content-dir", "-c", required=True, help="Content directory path")
    parser.add_argument("--output", "-o", help="Output JSON file path", 
                       default="document_index.json")
    parser.add_argument("--log-level", "-l", choices=["DEBUG", "INFO", "WARNING", "ERROR"],
                       default="INFO", help="Logging level")
    
    args = parser.parse_args()
    
    # Setup logging
    logging.basicConfig(
        level=getattr(logging, args.log_level),
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )
    
    # Build index
    indexer = DocumentIndexer(args.content_dir)
    index = indexer.build_index()
    indexer.save_index(args.output)
    
    # Print summary
    print(f"\nIndex Summary:")
    print(f"Documents: {index['metadata']['total_documents']}")
    print(f"Categories: {len(index['categories'])}")
    print(f"Concepts: {len(index['concepts'])}")
    print(f"Tags: {len(index['tags'])}")

if __name__ == "__main__":
    main()
