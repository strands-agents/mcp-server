"""
Comprehensive unit tests for MCP server tools.

This module tests all the MCP tools provided by the server:
1. get_document
2. fuzzy_search_documents
3. smart_search
4. find_related_documents
5. browse_by_category
6. explore_concepts
7. get_document_overview
8. get_learning_path
"""

import json
import pytest
import asyncio
from pathlib import Path
from unittest.mock import Mock, patch, MagicMock, mock_open, AsyncMock
import sys
import os

# Add src to path for imports
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..', 'src'))

from strands_mcp_server.server import (
    get_document, fuzzy_search_documents, smart_search, find_related_documents,
    browse_by_category, explore_concepts, get_document_overview, get_learning_path,
    doc_index
)


class TestMCPTools:
    """Test cases for MCP server tools."""
    
    @pytest.fixture
    def sample_index_data(self):
        """Sample index data for testing."""
        return {
            'documents': {
                'user-guide/quickstart.md': {
                    'title': 'Quick Start Guide',
                    'summary': 'Get started with Strands Agents quickly and easily',
                    'categories': ['Tutorial', 'Getting Started'],
                    'concepts': ['installation', 'setup', 'first agent'],
                    'complexity_score': 2.5
                },
                'api-reference/agents.md': {
                    'title': 'Agent API Reference',
                    'summary': 'Complete API reference for agent creation and management',
                    'categories': ['API Reference', 'Advanced'],
                    'concepts': ['agent', 'api', 'methods'],
                    'complexity_score': 7.2
                },
                'examples/weather-agent.md': {
                    'title': 'Weather Agent Example',
                    'summary': 'Example of building a weather forecasting agent',
                    'categories': ['Example', 'Tutorial'],
                    'concepts': ['weather', 'api integration', 'agent'],
                    'complexity_score': 4.1
                }
            },
            'relationships': {
                'user-guide/quickstart.md': [
                    {
                        'target': 'examples/weather-agent.md',
                        'type': 'next_step',
                        'strength': 0.8,
                        'context': 'Follow up with practical example'
                    }
                ]
            },
            'categories': {
                'Tutorial': ['user-guide/quickstart.md', 'examples/weather-agent.md'],
                'API Reference': ['api-reference/agents.md'],
                'Example': ['examples/weather-agent.md'],
                'Getting Started': ['user-guide/quickstart.md'],
                'Advanced': ['api-reference/agents.md'],
            },
            'concepts': {
                'agent': [
                    {'file_path': 'api-reference/agents.md', 'title': 'Agent API Reference', 'context': 'API methods'},
                    {'file_path': 'examples/weather-agent.md', 'title': 'Weather Agent Example', 'context': 'Example usage'}
                ],
                'installation': [
                    {'file_path': 'user-guide/quickstart.md', 'title': 'Quick Start Guide', 'context': 'Setup process'}
                ]
            },
            'tags': {},
            'metadata': {
                'total_documents': 3,
                'last_updated': '2024-01-01T00:00:00'
            }
        }
    
    @pytest.fixture
    def mock_doc_index(self, sample_index_data):
        """Mock the global doc_index."""
        with patch('strands_mcp_server.server.doc_index') as mock_index:
            mock_index.index = sample_index_data
            mock_index.get_document_info.side_effect = lambda path: sample_index_data['documents'].get(path)
            mock_index.get_related_documents.side_effect = lambda path, limit=5: [
                {
                    'file_path': rel['target'],
                    'title': sample_index_data['documents'][rel['target']]['title'],
                    'summary': sample_index_data['documents'][rel['target']]['summary'],
                    'relationship_type': rel['type'],
                    'relationship_strength': rel['strength'],
                    'relationship_context': rel['context']
                }
                for rel in sample_index_data['relationships'].get(path, [])[:limit]
                if rel['target'] in sample_index_data['documents']
            ]
            mock_index.get_documents_by_category.side_effect = lambda cat: [
                {
                    'file_path': path,
                    'title': sample_index_data['documents'][path]['title'],
                    'summary': sample_index_data['documents'][path]['summary'],
                    'complexity_score': sample_index_data['documents'][path]['complexity_score']
                }
                for path in sample_index_data['categories'].get(cat, [])
                if path in sample_index_data['documents']
            ]
            mock_index.get_documents_by_concept.side_effect = lambda concept: sample_index_data['concepts'].get(concept, [])
            mock_index.get_all_categories.return_value = list(sample_index_data['categories'].keys())
            mock_index.get_all_concepts.return_value = list(sample_index_data['concepts'].keys())
            mock_index.fuzzy_search_titles.return_value = [
                ('Quick Start Guide', 95, 'user-guide/quickstart.md')
            ]
            mock_index.fuzzy_search_concepts.return_value = [
                ('agent', 90, ['api-reference/agents.md', 'examples/weather-agent.md'])
            ]
            mock_index.fuzzy_search_categories.return_value = [
                ('Tutorial', 85, ['user-guide/quickstart.md', 'examples/weather-agent.md'])
            ]
            mock_index.smart_search.return_value = [
                {
                    'file_path': 'user-guide/quickstart.md',
                    'title': 'Quick Start Guide',
                    'summary': 'Get started with Strands Agents quickly and easily',
                    'categories': ['Tutorial', 'Getting Started'],
                    'concepts': ['installation', 'setup'],
                    'scores': {'title': 95},
                    'total_score': 95.0
                }
            ]
            mock_index.get_learning_path.return_value = [
                {
                    'file_path': 'user-guide/quickstart.md',
                    'title': 'Quick Start Guide',
                    'summary': 'Get started with Strands Agents quickly and easily',
                    'total_score': 95.0
                }
            ]
            yield mock_index
    
    @pytest.fixture
    def mock_pkg_resources(self):
        """Mock pkg_resources for file reading."""
        with patch('strands_mcp_server.server.pkg_resources') as mock_pkg:
            mock_file = Mock()
            mock_file.read_text.return_value = "# Test Document\n\nThis is test content."
            mock_pkg.joinpath.return_value = mock_file
            yield mock_pkg


class TestGetDocument:
    """Test the get_document tool."""
    
    @pytest.fixture
    def mock_doc_index(self):
        """Mock the global doc_index."""
        with patch('strands_mcp_server.server.doc_index') as mock_index:
            mock_index.get_related_documents.return_value = [{
                'file_path': 'examples/weather-agent.md',
                'title': 'Weather Agent Example',
                'summary': 'Example of building a weather forecasting agent',
                'relationship_type': 'next_step',
                'relationship_strength': 0.8,
                'relationship_context': 'Follow up with practical example'
            }]
            yield mock_index
    
    @pytest.fixture
    def mock_pkg_resources(self):
        """Mock pkg_resources for file reading."""
        with patch('strands_mcp_server.server.pkg_resources') as mock_pkg:
            mock_file = Mock()
            mock_file.read_text.return_value = "# Test Document\n\nThis is test content."
            mock_pkg.joinpath.return_value = mock_file
            yield mock_pkg
    
    @pytest.mark.asyncio
    async def test_get_document_success(self, mock_doc_index, mock_pkg_resources):
        """Test successful document retrieval."""
        # Mock the read_text method to return a test document
        mock_pkg_resources.joinpath.return_value.read_text.return_value = "# Test Document\n\nThis is test content."
        
        result = await get_document('user-guide/quickstart.md')
        
        assert "# Test Document" in result
        assert "This is test content." in result
        mock_pkg_resources.joinpath.assert_called_with("content", 'user-guide/quickstart.md')
    
    @pytest.mark.asyncio
    async def test_get_document_with_related(self, mock_doc_index, mock_pkg_resources):
        """Test document retrieval with related documents."""
        # Mock the read_text method to return a test document
        mock_pkg_resources.joinpath.return_value.read_text.return_value = "# Test Document\n\nThis is test content."
        
        # Ensure mock_doc_index.get_related_documents returns expected data
        mock_doc_index.get_related_documents.return_value = [{
            'file_path': 'examples/weather-agent.md',
            'title': 'Weather Agent Example',
            'summary': 'Example of building a weather forecasting agent',
            'relationship_type': 'next_step',
            'relationship_strength': 0.8,
            'relationship_context': 'Follow up with practical example'
        }]
        
        result = await get_document('user-guide/quickstart.md')
        
        # Should include related documents section
        assert "## Related Documents" in result
        assert "Weather Agent Example" in result
        assert "Follow up with practical example" in result
    
    @pytest.mark.asyncio
    async def test_get_document_file_not_found(self, mock_doc_index):
        """Test handling of file not found."""
        with patch('strands_mcp_server.server.pkg_resources') as mock_pkg:
            mock_file = Mock()
            mock_file.read_text.side_effect = FileNotFoundError("File not found")
            mock_pkg.joinpath.return_value = mock_file
            
            result = await get_document('non-existent.md')
            assert "Document not found: non-existent.md" in result
    
    @pytest.mark.asyncio
    async def test_get_document_read_error(self, mock_doc_index):
        """Test handling of file read errors."""
        with patch('strands_mcp_server.server.pkg_resources') as mock_pkg:
            mock_file = Mock()
            mock_file.read_text.side_effect = Exception("Read error")
            mock_pkg.joinpath.return_value = mock_file
            
            result = await get_document('error.md')
            assert "Error reading document: Read error" in result


class TestFuzzySearchDocuments:
    """Test the fuzzy_search_documents tool."""
    
    @pytest.fixture
    def mock_doc_index(self):
        """Mock the global doc_index."""
        with patch('strands_mcp_server.server.doc_index') as mock_index:
            mock_index.fuzzy_search_titles.return_value = [
                ('Quick Start Guide', 95, 'user-guide/quickstart.md')
            ]
            mock_index.fuzzy_search_concepts.return_value = [
                ('agent', 90, ['api-reference/agents.md', 'examples/weather-agent.md'])
            ]
            mock_index.fuzzy_search_categories.return_value = [
                ('Tutorial', 85, ['user-guide/quickstart.md', 'examples/weather-agent.md'])
            ]
            mock_index.smart_search.return_value = [{
                'file_path': 'user-guide/quickstart.md',
                'title': 'Quick Start Guide',
                'summary': 'Get started with Strands Agents quickly and easily',
                'categories': ['Tutorial', 'Getting Started'],
                'concepts': ['installation', 'setup'],
                'scores': {'title': 95},
                'total_score': 95.0
            }]
            mock_index.get_document_info.return_value = {
                'title': 'Quick Start Guide',
                'summary': 'Get started with Strands Agents quickly and easily'
            }
            yield mock_index
    
    @pytest.mark.asyncio
    async def test_fuzzy_search_titles(self, mock_doc_index):
        """Test fuzzy search for titles."""
        # Ensure mock returns expected data
        mock_doc_index.fuzzy_search_titles.return_value = [
            ('Quick Start Guide', 95, 'user-guide/quickstart.md')
        ]
        mock_doc_index.get_document_info.return_value = {
            'title': 'Quick Start Guide',
            'summary': 'Get started with Strands Agents quickly and easily'
        }
        
        result = await fuzzy_search_documents('Quick Start', search_type='titles')
        
        assert "Fuzzy Title Search Results" in result
        assert "Quick Start Guide" in result
        assert "Match: 95%" in result
        assert "user-guide/quickstart.md" in result
    
    @pytest.mark.asyncio
    async def test_fuzzy_search_concepts(self, mock_doc_index):
        """Test fuzzy search for concepts."""
        # Ensure mock returns expected data
        mock_doc_index.fuzzy_search_concepts.return_value = [
            ('agent', 90, ['api-reference/agents.md', 'examples/weather-agent.md'])
        ]
        mock_doc_index.get_document_info.side_effect = lambda path: {
            'api-reference/agents.md': {
                'title': 'Agent API Reference',
                'summary': 'Complete API reference for agent creation and management'
            },
            'examples/weather-agent.md': {
                'title': 'Weather Agent Example',
                'summary': 'Example of building a weather forecasting agent'
            }
        }.get(path)
        
        result = await fuzzy_search_documents('agent', search_type='concepts')
        
        assert "Fuzzy Concept Search Results" in result
        assert "Concept: agent" in result
        assert "Match: 90%" in result
        assert "**Documents:** 2" in result
    
    @pytest.mark.asyncio
    async def test_fuzzy_search_categories(self, mock_doc_index):
        """Test fuzzy search for categories."""
        # Ensure mock returns expected data
        mock_doc_index.fuzzy_search_categories.return_value = [
            ('Tutorial', 85, ['user-guide/quickstart.md', 'examples/weather-agent.md'])
        ]
        mock_doc_index.get_document_info.side_effect = lambda path: {
            'user-guide/quickstart.md': {
                'title': 'Quick Start Guide',
                'summary': 'Get started with Strands Agents quickly and easily'
            },
            'examples/weather-agent.md': {
                'title': 'Weather Agent Example',
                'summary': 'Example of building a weather forecasting agent'
            }
        }.get(path)
        
        result = await fuzzy_search_documents('Tutorial', search_type='categories')
        
        assert "Fuzzy Category Search Results" in result
        assert "Category: Tutorial" in result
        assert "Match: 85%" in result
        assert "**Documents:** 2" in result
    
    @pytest.mark.asyncio
    async def test_fuzzy_search_all(self, mock_doc_index):
        """Test fuzzy search with 'all' type."""
        # Ensure mock returns expected data
        mock_doc_index.smart_search.return_value = [
            {
                'file_path': 'user-guide/quickstart.md',
                'title': 'Quick Start Guide',
                'summary': 'Get started with Strands Agents quickly and easily',
                'categories': ['Tutorial', 'Getting Started'],
                'concepts': ['installation', 'setup'],
                'scores': {'title': 95},
                'total_score': 95.0
            }
        ]
        
        result = await fuzzy_search_documents('agent', search_type='all')
        
        assert "Smart Fuzzy Search Results" in result
        assert "Found 1 matching documents" in result
        assert "Quick Start Guide" in result
        # Format changed, no longer showing Total Score directly
    
    @pytest.mark.asyncio
    async def test_fuzzy_search_no_results(self, mock_doc_index):
        """Test fuzzy search with no results."""
        mock_doc_index.fuzzy_search_titles.return_value = []
        
        result = await fuzzy_search_documents('nonexistent', search_type='titles')
        assert "No documents found with titles matching 'nonexistent'" in result
    
    @pytest.mark.asyncio
    async def test_fuzzy_search_with_limit(self, mock_doc_index):
        """Test fuzzy search with custom limit."""
        # Ensure mock returns expected data
        mock_doc_index.smart_search.return_value = [
            {
                'file_path': 'user-guide/quickstart.md',
                'title': 'Quick Start Guide',
                'summary': 'Get started with Strands Agents quickly and easily',
                'categories': ['Tutorial', 'Getting Started'],
                'concepts': ['installation', 'setup'],
                'scores': {'title': 95},
                'total_score': 95.0
            }
        ]
        
        result = await fuzzy_search_documents('agent', limit=5)
        
        # Should respect the limit parameter
        mock_doc_index.smart_search.assert_called_with('agent', 5)


class TestSmartSearch:
    """Test the smart_search tool."""
    
    @pytest.fixture
    def mock_doc_index(self):
        """Mock the global doc_index."""
        with patch('strands_mcp_server.server.doc_index') as mock_index:
            mock_index.smart_search.return_value = [{
                'file_path': 'user-guide/quickstart.md',
                'title': 'Quick Start Guide',
                'summary': 'Get started with Strands Agents quickly and easily',
                'categories': ['Tutorial', 'Getting Started'],
                'concepts': ['installation', 'setup'],
                'scores': {'title': 95},
                'total_score': 95.0
            }]
            yield mock_index
    
    @pytest.mark.asyncio
    async def test_smart_search_success(self, mock_doc_index):
        """Test successful smart search."""
        # Ensure mock returns expected data
        mock_doc_index.smart_search.return_value = [
            {
                'file_path': 'user-guide/quickstart.md',
                'title': 'Quick Start Guide',
                'summary': 'Get started with Strands Agents quickly and easily',
                'categories': ['Tutorial', 'Getting Started'],
                'concepts': ['installation', 'setup'],
                'scores': {'title': 95},
                'total_score': 95.0
            }
        ]
        
        result = await smart_search('agent')
        
        assert "Smart Search Results" in result
        assert "Found 1 relevant documents" in result
        assert "Quick Start Guide" in result
        # Format changed, no longer showing Relevance Score directly
        # Format changed, no longer showing Match Analysis directly
    
    @pytest.mark.asyncio
    async def test_smart_search_no_results(self, mock_doc_index):
        """Test smart search with no results."""
        mock_doc_index.smart_search.return_value = []
        
        result = await smart_search('nonexistent')
        assert "No documents found matching 'nonexistent'" in result
    
    @pytest.mark.asyncio
    async def test_smart_search_with_limit(self, mock_doc_index):
        """Test smart search with custom limit."""
        # Ensure mock returns expected data
        mock_doc_index.smart_search.return_value = [
            {
                'file_path': 'user-guide/quickstart.md',
                'title': 'Quick Start Guide',
                'summary': 'Get started with Strands Agents quickly and easily',
                'categories': ['Tutorial', 'Getting Started'],
                'concepts': ['installation', 'setup'],
                'scores': {'title': 95},
                'total_score': 95.0
            }
        ]
        
        result = await smart_search('agent', limit=3)
        
        mock_doc_index.smart_search.assert_called_with('agent', 3)


class TestFindRelatedDocuments:
    """Test the find_related_documents tool."""
    
    @pytest.fixture
    def mock_doc_index(self):
        """Mock the global doc_index."""
        with patch('strands_mcp_server.server.doc_index') as mock_index:
            mock_index.get_related_documents.return_value = [{
                'file_path': 'examples/weather-agent.md',
                'title': 'Weather Agent Example',
                'summary': 'Example of building a weather forecasting agent',
                'relationship_type': 'next_step',
                'relationship_strength': 0.8,
                'relationship_context': 'Follow up with practical example'
            }]
            yield mock_index
    
    @pytest.mark.asyncio
    async def test_find_related_success(self, mock_doc_index):
        """Test finding related documents."""
        # Ensure mock returns expected data
        mock_doc_index.get_related_documents.return_value = [{
            'file_path': 'examples/weather-agent.md',
            'title': 'Weather Agent Example',
            'summary': 'Example of building a weather forecasting agent',
            'relationship_type': 'next_step',
            'relationship_strength': 0.8,
            'relationship_context': 'Follow up with practical example'
        }]
        
        result = await find_related_documents('user-guide/quickstart.md')
        
        assert "Documents Related to 'user-guide/quickstart.md'" in result
        assert "Weather Agent Example" in result
        assert "next_step" in result
        assert "0.80" in result
        assert "Follow up with practical example" in result
    
    @pytest.mark.asyncio
    async def test_find_related_no_results(self, mock_doc_index):
        """Test finding related documents with no results."""
        mock_doc_index.get_related_documents.return_value = []
        
        result = await find_related_documents('isolated.md')
        assert "No related documents found for 'isolated.md'" in result
    
    @pytest.mark.asyncio
    async def test_find_related_with_limit(self, mock_doc_index):
        """Test finding related documents with custom limit."""
        # Ensure mock returns expected data
        mock_doc_index.get_related_documents.return_value = [{
            'file_path': 'examples/weather-agent.md',
            'title': 'Weather Agent Example',
            'summary': 'Example of building a weather forecasting agent',
            'relationship_type': 'next_step',
            'relationship_strength': 0.8,
            'relationship_context': 'Follow up with practical example'
        }]
        
        result = await find_related_documents('user-guide/quickstart.md', limit=3)
        
        mock_doc_index.get_related_documents.assert_called_with('user-guide/quickstart.md', 3)


class TestBrowseByCategory:
    """Test the browse_by_category tool."""
    
    @pytest.fixture
    def mock_doc_index(self):
        """Mock the global doc_index."""
        with patch('strands_mcp_server.server.doc_index') as mock_index:
            mock_index.get_all_categories.return_value = ['Tutorial', 'API Reference', 'Example', 'Getting Started', 'Advanced']
            mock_index.get_documents_by_category.side_effect = lambda cat: {
                'Tutorial': [{'file_path': 'doc1.md', 'title': 'Doc 1', 'summary': 'Summary 1', 'complexity_score': 1.0}],
                'API Reference': [{'file_path': 'doc2.md', 'title': 'Doc 2', 'summary': 'Summary 2', 'complexity_score': 2.0}],
                'Example': [{'file_path': 'doc3.md', 'title': 'Doc 3', 'summary': 'Summary 3', 'complexity_score': 3.0}],
                'Getting Started': [{'file_path': 'doc4.md', 'title': 'Doc 4', 'summary': 'Summary 4', 'complexity_score': 4.0}],
                'Advanced': [{'file_path': 'doc5.md', 'title': 'Doc 5', 'summary': 'Summary 5', 'complexity_score': 5.0}]
            }.get(cat, [])
            yield mock_index
    
    @pytest.mark.asyncio
    async def test_browse_category_list(self, mock_doc_index):
        """Test browsing categories without specifying one."""
        # Ensure mock returns expected data
        mock_doc_index.get_all_categories.return_value = ['Tutorial', 'API Reference', 'Example', 'Getting Started', 'Advanced']
        mock_doc_index.get_documents_by_category.side_effect = lambda cat: {
            'Tutorial': [{'file_path': 'doc1.md'}, {'file_path': 'doc2.md'}],
            'API Reference': [{'file_path': 'doc3.md'}],
            'Example': [{'file_path': 'doc4.md'}],
            'Getting Started': [{'file_path': 'doc5.md'}],
            'Advanced': [{'file_path': 'doc6.md'}, {'file_path': 'doc7.md'}]
        }.get(cat, [])
        
        result = await browse_by_category()
        
        assert "Available Categories" in result
        assert "Tutorial" in result
        assert "API Reference" in result
        assert "documents)" in result  # Should show document counts
    
    @pytest.mark.asyncio
    async def test_browse_specific_category(self, mock_doc_index):
        """Test browsing a specific category."""
        # Ensure mock returns expected data
        # Create a new mock for this specific test that overrides the fixture
        mock_doc_index.get_documents_by_category = Mock(return_value=[
            {
                'file_path': 'user-guide/quickstart.md',
                'title': 'Quick Start Guide',
                'summary': 'Get started with Strands Agents quickly and easily',
                'complexity_score': 2.5
            },
            {
                'file_path': 'examples/weather-agent.md',
                'title': 'Weather Agent Example',
                'summary': 'Example of building a weather forecasting agent',
                'complexity_score': 4.1
            }
        ])
        
        result = await browse_by_category('Tutorial')
        
        assert "Documents in Category: Tutorial" in result
        assert "Found" in result
        assert "documents" in result
        assert "ordered by complexity" in result
        # Skip checking for specific document titles as they may vary
        assert "Weather Agent Example" in result
    
    @pytest.mark.asyncio
    async def test_browse_nonexistent_category(self, mock_doc_index):
        """Test browsing a non-existent category."""
        mock_doc_index.get_documents_by_category.return_value = []
        
        result = await browse_by_category('NonExistent')
        assert "No documents found in category 'NonExistent'" in result
    
    @pytest.mark.asyncio
    async def test_browse_empty_categories(self, mock_doc_index):
        """Test browsing when no categories exist."""
        mock_doc_index.get_all_categories.return_value = []
        
        result = await browse_by_category()
        assert "No categories available" in result


class TestExploreConcepts:
    """Test the explore_concepts tool."""
    
    @pytest.fixture
    def mock_doc_index(self):
        """Mock the global doc_index."""
        with patch('strands_mcp_server.server.doc_index') as mock_index:
            mock_index.get_all_concepts.return_value = ['agent', 'installation']
            mock_index.get_documents_by_concept.return_value = [{
                'file_path': 'doc.md',
                'title': 'Document',
                'context': 'Context'
            }]
            mock_index.index = {
                'concepts': {
                    'agent': [{'file_path': 'doc1.md'}, {'file_path': 'doc2.md'}],
                    'installation': [{'file_path': 'doc3.md'}]
                }
            }
            yield mock_index
    
    @pytest.mark.asyncio
    async def test_explore_concepts_list(self, mock_doc_index):
        """Test exploring concepts without specifying one."""
        # Mock concept counts
        mock_doc_index.index = {
            'concepts': {
                'agent': [{'file_path': 'doc1.md'}, {'file_path': 'doc2.md'}],
                'installation': [{'file_path': 'doc3.md'}]
            }
        }
        
        result = await explore_concepts()
        
        assert "Top Concepts" in result
        assert "agent" in result
        assert "installation" in result
        assert "(2 documents)" in result
        assert "(1 documents)" in result
    
    @pytest.mark.asyncio
    async def test_explore_specific_concept(self, mock_doc_index):
        """Test exploring a specific concept."""
        # Ensure mock returns expected data
        mock_doc_index.get_documents_by_concept.return_value = [
            {
                'file_path': 'api-reference/agents.md',
                'title': 'Agent API Reference',
                'context': 'API methods'
            },
            {
                'file_path': 'examples/weather-agent.md',
                'title': 'Weather Agent Example',
                'context': 'Example usage'
            }
        ]
        
        result = await explore_concepts('agent')
        
        assert "Documents Related to Concept: agent" in result
        assert "Found 2 documents" in result
        assert "Agent API Reference" in result
        assert "Weather Agent Example" in result
    
    @pytest.mark.asyncio
    async def test_explore_nonexistent_concept(self, mock_doc_index):
        """Test exploring a non-existent concept."""
        mock_doc_index.get_documents_by_concept.return_value = []
        
        result = await explore_concepts('nonexistent')
        assert "No documents found for concept 'nonexistent'" in result
    
    @pytest.mark.asyncio
    async def test_explore_empty_concepts(self, mock_doc_index):
        """Test exploring when no concepts exist."""
        mock_doc_index.get_all_concepts.return_value = []
        
        result = await explore_concepts()
        assert "No concepts available" in result


class TestGetDocumentOverview:
    """Test the get_document_overview tool."""
    
    @pytest.fixture
    def mock_doc_index(self):
        """Mock the global doc_index."""
        with patch('strands_mcp_server.server.doc_index') as mock_index:
            mock_index.index = {
                'metadata': {
                    'total_documents': 3,
                    'last_updated': '2024-01-01T00:00:00'
                },
                'categories': {
                    'Tutorial': ['user-guide/quickstart.md', 'examples/weather-agent.md'],
                    'API Reference': ['api-reference/agents.md'],
                    'Example': ['examples/weather-agent.md'],
                    'Getting Started': ['user-guide/quickstart.md'],
                    'Advanced': ['api-reference/agents.md']
                },
                'concepts': {
                    'agent': [
                        {'file_path': 'api-reference/agents.md', 'title': 'Agent API Reference', 'context': 'API methods'},
                        {'file_path': 'examples/weather-agent.md', 'title': 'Weather Agent Example', 'context': 'Example usage'}
                    ],
                    'installation': [
                        {'file_path': 'user-guide/quickstart.md', 'title': 'Quick Start Guide', 'context': 'Setup process'}
                    ]
                },
                'documents': {
                    'user-guide/quickstart.md': {
                        'title': 'Quick Start Guide',
                        'summary': 'Get started with Strands Agents quickly and easily'
                    },
                    'api-reference/agents.md': {
                        'title': 'Agent API Reference',
                        'summary': 'Complete API reference for agent creation and management'
                    },
                    'examples/weather-agent.md': {
                        'title': 'Weather Agent Example',
                        'summary': 'Example of building a weather forecasting agent'
                    }
                }
            }
            mock_index.get_documents_by_category.side_effect = lambda cat: [
                {
                    'file_path': path,
                    'title': mock_index.index['documents'][path]['title'],
                    'summary': mock_index.index['documents'][path]['summary'],
                    'complexity_score': 1.0
                }
                for path in mock_index.index['categories'].get(cat, [])
                if path in mock_index.index['documents']
            ][:3]
            yield mock_index
    
    @pytest.mark.asyncio
    async def test_get_overview(self, mock_doc_index):
        """Test getting document overview."""
        # Ensure mock returns expected data
        mock_doc_index.index = {
            'metadata': {
                'total_documents': 3,
                'last_updated': '2024-01-01T00:00:00'
            },
            'categories': {
                'Tutorial': ['user-guide/quickstart.md', 'examples/weather-agent.md'],
                'API Reference': ['api-reference/agents.md'],
                'Example': ['examples/weather-agent.md'],
                'Getting Started': ['user-guide/quickstart.md'],
                'Advanced': ['api-reference/agents.md']
            },
            'concepts': {
                'agent': [
                    {'file_path': 'api-reference/agents.md', 'title': 'Agent API Reference', 'context': 'API methods'},
                    {'file_path': 'examples/weather-agent.md', 'title': 'Weather Agent Example', 'context': 'Example usage'}
                ],
                'installation': [
                    {'file_path': 'user-guide/quickstart.md', 'title': 'Quick Start Guide', 'context': 'Setup process'}
                ]
            },
            'documents': {
                'user-guide/quickstart.md': {
                    'title': 'Quick Start Guide',
                    'summary': 'Get started with Strands Agents quickly and easily'
                },
                'api-reference/agents.md': {
                    'title': 'Agent API Reference',
                    'summary': 'Complete API reference for agent creation and management'
                },
                'examples/weather-agent.md': {
                    'title': 'Weather Agent Example',
                    'summary': 'Example of building a weather forecasting agent'
                }
            }
        }
        
        # Set up mock for get_documents_by_category
        mock_doc_index.get_documents_by_category.side_effect = lambda cat: [
            {
                'file_path': path,
                'title': mock_doc_index.index['documents'][path]['title'],
                'summary': mock_doc_index.index['documents'][path]['summary'],
                'complexity_score': 1.0
            }
            for path in mock_doc_index.index['categories'].get(cat, [])
            if path in mock_doc_index.index['documents']
        ][:3]  # Limit to 3 examples
        
        result = await get_document_overview()
        
        assert "Strands Agents Documentation Overview" in result
        assert "Statistics" in result
        assert "**Total Documents:** 3" in result
        # Format changed, now using bullet points with different formatting
        assert "**Categories:**" in result
        assert "**Concepts:** 2" in result
        assert "**Last Updated:** 2024-01-01T00:00:00" in result
        assert "Documentation Structure" in result
        assert "Most Common Concepts" in result
    
    @pytest.mark.asyncio
    async def test_get_overview_with_examples(self, mock_doc_index):
        """Test overview includes category examples."""
        # Ensure mock returns expected data (same as in test_get_overview)
        mock_doc_index.index = {
            'metadata': {
                'total_documents': 3,
                'last_updated': '2024-01-01T00:00:00'
            },
            'categories': {
                'Tutorial': ['user-guide/quickstart.md', 'examples/weather-agent.md'],
                'API Reference': ['api-reference/agents.md'],
                'Example': ['examples/weather-agent.md'],
                'Getting Started': ['user-guide/quickstart.md'],
                'Advanced': ['api-reference/agents.md']
            },
            'concepts': {
                'agent': [
                    {'file_path': 'api-reference/agents.md', 'title': 'Agent API Reference', 'context': 'API methods'},
                    {'file_path': 'examples/weather-agent.md', 'title': 'Weather Agent Example', 'context': 'Example usage'}
                ],
                'installation': [
                    {'file_path': 'user-guide/quickstart.md', 'title': 'Quick Start Guide', 'context': 'Setup process'}
                ]
            },
            'documents': {
                'user-guide/quickstart.md': {
                    'title': 'Quick Start Guide',
                    'summary': 'Get started with Strands Agents quickly and easily'
                },
                'api-reference/agents.md': {
                    'title': 'Agent API Reference',
                    'summary': 'Complete API reference for agent creation and management'
                },
                'examples/weather-agent.md': {
                    'title': 'Weather Agent Example',
                    'summary': 'Example of building a weather forecasting agent'
                }
            }
        }
        
        # Set up mock for get_documents_by_category
        mock_doc_index.get_documents_by_category.side_effect = lambda cat: [
            {
                'file_path': path,
                'title': mock_doc_index.index['documents'][path]['title'],
                'summary': mock_doc_index.index['documents'][path]['summary'],
                'complexity_score': 1.0
            }
            for path in mock_doc_index.index['categories'].get(cat, [])
            if path in mock_doc_index.index['documents']
        ][:3]  # Limit to 3 examples
        
        result = await get_document_overview()
        
        # Should show examples from each category
        assert "Tutorial" in result
        assert "API Reference" in result
        # Should show document titles as examples
        assert "Quick Start Guide" in result or "Agent API Reference" in result


class TestGetLearningPath:
    """Test the get_learning_path tool."""
    
    @pytest.fixture
    def mock_doc_index(self):
        """Mock the global doc_index."""
        with patch('strands_mcp_server.server.doc_index') as mock_index:
            mock_index.get_learning_path.return_value = [
                {
                    'file_path': 'user-guide/quickstart.md',
                    'title': 'Quick Start Guide',
                    'summary': 'Get started with Strands Agents quickly and easily',
                    'total_score': 95.0
                }
            ]
            mock_index.index = {
                'documents': {
                    'user-guide/quickstart.md': {
                        'complexity_score': 2.5,
                        'categories': ['Tutorial', 'Getting Started']
                    }
                }
            }
            mock_index.get_related_documents.return_value = []
            yield mock_index
    
    @pytest.mark.asyncio
    async def test_get_learning_path_success(self, mock_doc_index):
        """Test successful learning path generation."""
        # Ensure mock returns expected data
        mock_doc_index.get_learning_path.return_value = [
            {
                'file_path': 'user-guide/quickstart.md',
                'title': 'Quick Start Guide',
                'summary': 'Get started with Strands Agents quickly and easily',
                'total_score': 95.0
            }
        ]
        
        # Mock document info for complexity scores
        mock_doc_index.index = {
            'documents': {
                'user-guide/quickstart.md': {
                    'complexity_score': 2.5,
                    'categories': ['Tutorial', 'Getting Started']
                }
            }
        }
        
        # Mock get_related_documents
        mock_doc_index.get_related_documents.return_value = []
        
        result = await get_learning_path('agent')
        
        assert "Learning Path: agent" in result
        assert "suggested learning path with 1 documents" in result
        assert "Quick Start Guide" in result
        assert "Complexity:" in result
        assert "Relevance:" in result
    
    @pytest.mark.asyncio
    async def test_get_learning_path_no_results(self, mock_doc_index):
        """Test learning path with no results."""
        mock_doc_index.get_learning_path.return_value = []
        
        result = await get_learning_path('nonexistent')
        assert "No learning path found for topic 'nonexistent'" in result
        assert "Try using fuzzy search" in result
    
    @pytest.mark.asyncio
    async def test_get_learning_path_with_sections(self, mock_doc_index):
        """Test learning path with different complexity sections."""
        # Mock a more complex learning path
        mock_doc_index.get_learning_path.return_value = [
            {
                'file_path': 'beginner.md',
                'title': 'Beginner Guide',
                'summary': 'Basic concepts',
                'total_score': 90.0
            },
            {
                'file_path': 'advanced.md',
                'title': 'Advanced Topics',
                'summary': 'Complex concepts',
                'total_score': 85.0
            }
        ]
        
        # Mock document info for complexity scores
        mock_doc_index.index = {
            'documents': {
                'beginner.md': {'complexity_score': 1.0, 'categories': []},
                'advanced.md': {'complexity_score': 8.0, 'categories': []}
            }
        }
        
        # Mock get_related_documents
        mock_doc_index.get_related_documents.return_value = []
        
        result = await get_learning_path('topic')
        
        assert "Getting Started" in result
        assert "Advanced Topics" in result


class TestMCPToolsIntegration:
    """Integration tests for MCP tools."""
    
    @pytest.fixture
    def mock_doc_index(self):
        """Mock the global doc_index."""
        with patch('strands_mcp_server.server.doc_index') as mock_index:
            mock_index.smart_search.return_value = [{
                'file_path': 'user-guide/quickstart.md',
                'title': 'Quick Start Guide',
                'summary': 'Get started with Strands Agents quickly and easily',
                'categories': ['Tutorial', 'Getting Started'],
                'concepts': ['installation', 'setup'],
                'scores': {'title': 95},
                'total_score': 95.0
            }]
            mock_index.get_related_documents.return_value = [{
                'file_path': 'examples/weather-agent.md',
                'title': 'Weather Agent Example',
                'summary': 'Example of building a weather forecasting agent',
                'relationship_type': 'next_step',
                'relationship_strength': 0.8,
                'relationship_context': 'Follow up with practical example'
            }]
            mock_index.get_documents_by_category.return_value = [
                {
                    'file_path': 'user-guide/quickstart.md',
                    'title': 'Quick Start Guide',
                    'summary': 'Get started with Strands Agents quickly and easily',
                    'complexity_score': 2.5
                },
                {
                    'file_path': 'examples/weather-agent.md',
                    'title': 'Weather Agent Example',
                    'summary': 'Example of building a weather forecasting agent',
                    'complexity_score': 4.1
                }
            ]
            mock_index.get_learning_path.return_value = [{
                'file_path': 'user-guide/quickstart.md',
                'title': 'Quick Start Guide',
                'summary': 'Get started with Strands Agents quickly and easily',
                'total_score': 95.0
            }]
            mock_index.index = {
                'documents': {
                    'user-guide/quickstart.md': {
                        'complexity_score': 2.5,
                        'categories': ['Tutorial', 'Getting Started']
                    }
                }
            }
            yield mock_index
    
    @pytest.fixture
    def mock_pkg_resources(self):
        """Mock pkg_resources for file reading."""
        with patch('strands_mcp_server.server.pkg_resources') as mock_pkg:
            mock_file = Mock()
            mock_file.read_text.return_value = "# Test Document\n\nThis is test content."
            mock_pkg.joinpath.return_value = mock_file
            yield mock_pkg
    
    @pytest.mark.asyncio
    async def test_tool_chain_workflow(self, mock_doc_index, mock_pkg_resources):
        """Test a typical workflow using multiple tools."""
        # Set up mocks for each tool
        # 1. Smart search
        mock_doc_index.smart_search.return_value = [{
            'file_path': 'user-guide/quickstart.md',
            'title': 'Quick Start Guide',
            'summary': 'Get started with Strands Agents quickly and easily',
            'categories': ['Tutorial', 'Getting Started'],
            'concepts': ['installation', 'setup'],
            'scores': {'title': 95},
            'total_score': 95.0
        }]
        
        # 2. Get document
        mock_pkg_resources.joinpath.return_value.read_text.return_value = "# Test Document\n\nThis is test content."
        
        # 3. Related documents
        mock_doc_index.get_related_documents.return_value = [{
            'file_path': 'examples/weather-agent.md',
            'title': 'Weather Agent Example',
            'summary': 'Example of building a weather forecasting agent',
            'relationship_type': 'next_step',
            'relationship_strength': 0.8,
            'relationship_context': 'Follow up with practical example'
        }]
        
        # 4. Browse by category
        mock_doc_index.get_documents_by_category.return_value = [
            {
                'file_path': 'user-guide/quickstart.md',
                'title': 'Quick Start Guide',
                'summary': 'Get started with Strands Agents quickly and easily',
                'complexity_score': 2.5
            },
            {
                'file_path': 'examples/weather-agent.md',
                'title': 'Weather Agent Example',
                'summary': 'Example of building a weather forecasting agent',
                'complexity_score': 4.1
            }
        ]
        
        # 5. Learning path
        mock_doc_index.get_learning_path.return_value = [{
            'file_path': 'user-guide/quickstart.md',
            'title': 'Quick Start Guide',
            'summary': 'Get started with Strands Agents quickly and easily',
            'total_score': 95.0
        }]
        mock_doc_index.index = {
            'documents': {
                'user-guide/quickstart.md': {
                    'complexity_score': 2.5,
                    'categories': ['Tutorial', 'Getting Started']
                }
            }
        }
        
        # Run the workflow
        # 1. Search for documents
        search_result = await smart_search('agent')
        assert "Smart Search Results" in search_result
        
        # 2. Get a specific document
        doc_result = await get_document('user-guide/quickstart.md')
        assert "# Test Document" in doc_result
        
        # 3. Find related documents
        related_result = await find_related_documents('user-guide/quickstart.md')
        assert "Documents Related to" in related_result
        
        # 4. Browse by category
        category_result = await browse_by_category('Tutorial')
        assert "Documents in Category: Tutorial" in category_result
        
        # 5. Get learning path
        path_result = await get_learning_path('agent')
        assert "Learning Path: agent" in path_result
    
    @pytest.mark.asyncio
    async def test_error_handling_consistency(self, mock_doc_index):
        """Test that all tools handle errors consistently."""
        # Mock various error conditions
        mock_doc_index.smart_search.return_value = []
        mock_doc_index.get_related_documents.return_value = []
        mock_doc_index.get_documents_by_category.return_value = []
        mock_doc_index.get_documents_by_concept.return_value = []
        mock_doc_index.get_learning_path.return_value = []
        
        # All tools should handle empty results gracefully
        results = await asyncio.gather(
            smart_search('nonexistent'),
            find_related_documents('nonexistent.md'),
            browse_by_category('NonExistent'),
            explore_concepts('nonexistent'),
            get_learning_path('nonexistent')
        )
        
        # All should return informative messages, not crash
        for result in results:
            assert isinstance(result, str)
            assert len(result) > 0
            assert "not found" in result.lower() or "no " in result.lower()


class TestMCPToolsParameterValidation:
    """Test parameter validation for MCP tools."""
    
    @pytest.fixture
    def mock_doc_index(self):
        """Mock the global doc_index."""
        with patch('strands_mcp_server.server.doc_index') as mock_index:
            mock_index.smart_search.return_value = [{
                'file_path': 'test.md',
                'title': 'Test Document',
                'summary': 'Test summary',
                'categories': ['Test'],
                'concepts': ['test'],
                'scores': {'title': 95},
                'total_score': 95.0
            }]
            mock_index.get_related_documents.return_value = [{
                'file_path': 'related.md',
                'title': 'Related Document',
                'summary': 'Related summary',
                'relationship_type': 'related',
                'relationship_strength': 0.8,
                'relationship_context': 'Related context'
            }]
            mock_index.get_all_categories.return_value = ['Tutorial', 'API Reference']
            mock_index.get_documents_by_category.return_value = [{
                'file_path': 'doc.md',
                'title': 'Document',
                'summary': 'Summary',
                'complexity_score': 1.0
            }]
            mock_index.get_all_concepts.return_value = ['agent', 'installation']
            mock_index.get_documents_by_concept.return_value = [{
                'file_path': 'doc.md',
                'title': 'Document',
                'context': 'Context'
            }]
            mock_index.index = {
                'concepts': {
                    'agent': [{'file_path': 'doc1.md'}, {'file_path': 'doc2.md'}],
                    'installation': [{'file_path': 'doc3.md'}]
                }
            }
            yield mock_index
    
    @pytest.fixture
    def mock_pkg_resources(self):
        """Mock pkg_resources for file reading."""
        with patch('strands_mcp_server.server.pkg_resources') as mock_pkg:
            mock_file = Mock()
            mock_file.read_text.return_value = "# Test Document\n\nThis is test content."
            mock_pkg.joinpath.return_value = mock_file
            yield mock_pkg
    
    @pytest.mark.asyncio
    async def test_parameter_types(self, mock_doc_index, mock_pkg_resources):
        """Test that tools handle different parameter types correctly."""
        # Set up mocks for each tool
        mock_pkg_resources.joinpath.return_value.read_text.return_value = "# Test Document\n\nThis is test content."
        mock_doc_index.smart_search.return_value = [{
            'file_path': 'test.md',
            'title': 'Test Document',
            'summary': 'Test summary',
            'categories': ['Test'],
            'concepts': ['test'],
            'scores': {'title': 95},
            'total_score': 95.0
        }]
        mock_doc_index.get_related_documents.return_value = [{
            'file_path': 'related.md',
            'title': 'Related Document',
            'summary': 'Related summary',
            'relationship_type': 'related',
            'relationship_strength': 0.8,
            'relationship_context': 'Related context'
        }]
        
        # Test with various parameter types
        await get_document('test.md')  # string
        await fuzzy_search_documents('query', limit=5, search_type='all')  # mixed types
        await smart_search('query', limit=10)  # int parameter
        await find_related_documents('test.md', limit=3)  # int parameter
        
        # Should not raise exceptions
        assert True
    
    @pytest.mark.asyncio
    async def test_optional_parameters(self, mock_doc_index):
        """Test tools with optional parameters."""
        # Set up mocks for each tool
        mock_doc_index.get_all_categories.return_value = ['Tutorial', 'API Reference']
        mock_doc_index.get_documents_by_category.return_value = [{
            'file_path': 'doc.md',
            'title': 'Document',
            'summary': 'Summary',
            'complexity_score': 1.0
        }]
        mock_doc_index.get_all_concepts.return_value = ['agent', 'installation']
        mock_doc_index.get_documents_by_concept.return_value = [{
            'file_path': 'doc.md',
            'title': 'Document',
            'context': 'Context'
        }]
        mock_doc_index.index = {
            'concepts': {
                'agent': [{'file_path': 'doc1.md'}, {'file_path': 'doc2.md'}],
                'installation': [{'file_path': 'doc3.md'}]
            }
        }
        
        # Test with and without optional parameters
        result1 = await browse_by_category()  # No category specified
        result2 = await browse_by_category('Tutorial')  # Category specified
        
        result3 = await explore_concepts()  # No concept specified
        result4 = await explore_concepts('agent')  # Concept specified
        
        # Both should work
        assert isinstance(result1, str)
        assert isinstance(result2, str)
        assert isinstance(result3, str)
        assert isinstance(result4, str)
    
    @pytest.mark.asyncio
    async def test_default_values(self, mock_doc_index):
        """Test that default parameter values work correctly."""
        # Set up mocks for each tool
        mock_doc_index.smart_search.return_value = [{
            'file_path': 'test.md',
            'title': 'Test Document',
            'summary': 'Test summary',
            'categories': ['Test'],
            'concepts': ['test'],
            'scores': {'title': 95},
            'total_score': 95.0
        }]
        mock_doc_index.get_related_documents.return_value = [{
            'file_path': 'related.md',
            'title': 'Related Document',
            'summary': 'Related summary',
            'relationship_type': 'related',
            'relationship_strength': 0.8,
            'relationship_context': 'Related context'
        }]
        
        # Test default limits
        await smart_search('query')  # Should use default limit
        await fuzzy_search_documents('query')  # Should use default limit and search_type
        await find_related_documents('test.md')  # Should use default limit
        
        # Verify default values were used
        mock_doc_index.smart_search.assert_called_with('query', 10)  # Default limit
