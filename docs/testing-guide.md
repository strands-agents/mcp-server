# Testing Guide

This document provides comprehensive information about testing the Strands Agents MCP Server.

## Overview

The project includes a comprehensive test suite covering:

- **Unit Tests**: Test individual components in isolation
- **Integration Tests**: Test component interactions and end-to-end workflows
- **Performance Tests**: Test system performance under load
- **GitHub Actions Tests**: Test CI/CD workflow functionality

## Test Structure

```
tests/
├── unit/
│   ├── test_server.py                    # Server initialization and MCP tools
│   ├── test_fuzzy_document_index.py      # Document indexing and fuzzy search
│   ├── test_mcp_tools.py                 # MCP tool functionality
│   ├── test_indexer.py                   # Document indexer component
│   ├── test_sync_docs.py                 # Documentation synchronization
│   ├── test_github_action_workflow.py    # GitHub Actions integration
│   ├── test_integration.py               # End-to-end integration tests
│   └── test_complete_workflow.py         # Simple workflow tests
├── conftest.py                           # Shared test fixtures (if needed)
└── __init__.py
```

## Running Tests

### Quick Start

```bash
# Run all tests
python -m pytest

# Run with coverage
python -m pytest --cov=src/strands_mcp_server --cov=scripts

# Run specific test file
python -m pytest tests/unit/test_server.py

# Run specific test function
python -m pytest tests/unit/test_server.py::TestServerInitialization::test_main_calls_initialize_documentation_tools
```

### Using the Test Runner Script

The project includes a comprehensive test runner script:

```bash
# Quick tests (fast, no slow tests)
python scripts/run_tests.py quick

# Full test suite with coverage
python scripts/run_tests.py full

# Check test environment
python scripts/run_tests.py check

# Run with custom options
python scripts/run_tests.py --unit --verbose --cov-html
```

### Test Runner Options

```bash
# Test selection
--unit              # Run unit tests only
--integration       # Run integration tests only
--performance       # Run performance tests only
--slow              # Include slow tests
--file FILE         # Run specific test file
--function FUNC     # Run specific test function

# Coverage options
--no-cov           # Disable coverage reporting
--cov-html         # Generate HTML coverage report
--cov-xml          # Generate XML coverage report

# Output options
--verbose, -v      # Verbose output
--quiet, -q        # Quiet output
--tb FORMAT        # Traceback format (short/long/line/no)

# Execution options
--parallel N       # Run tests in parallel
--failfast, -x     # Stop on first failure
--lf               # Run last failed tests only
--ff               # Run failed tests first
```

## Test Categories

### Unit Tests

Test individual components in isolation:

- **Server Tests** (`test_server.py`): Server initialization, tool registration
- **Fuzzy Index Tests** (`test_fuzzy_document_index.py`): Search functionality
- **MCP Tools Tests** (`test_mcp_tools.py`): Individual tool functions
- **Indexer Tests** (`test_indexer.py`): Document processing and indexing
- **Sync Tests** (`test_sync_docs.py`): Documentation synchronization

### Integration Tests

Test component interactions:

- **End-to-End Workflows** (`test_integration.py`): Complete system workflows
- **GitHub Actions** (`test_github_action_workflow.py`): CI/CD integration

### Performance Tests

Test system performance:

- Large document sets
- Concurrent operations
- Memory usage
- Response times

## Test Configuration

### pytest.ini

The project uses pytest with the following configuration:

```ini
[tool:pytest]
testpaths = tests
python_files = test_*.py
python_classes = Test*
python_functions = test_*
addopts = 
    -v
    --tb=short
    --strict-markers
    --disable-warnings
    --cov=src/strands_mcp_server
    --cov=scripts
    --cov-report=term-missing
    --cov-report=html:htmlcov
    --cov-report=xml
    --cov-fail-under=80
markers =
    slow: marks tests as slow
    integration: marks tests as integration tests
    unit: marks tests as unit tests
    asyncio: marks tests as async tests
    performance: marks tests as performance tests
```

### Test Markers

Use markers to categorize tests:

```python
import pytest

@pytest.mark.unit
def test_unit_functionality():
    """Unit test example."""
    pass

@pytest.mark.integration
def test_integration_workflow():
    """Integration test example."""
    pass

@pytest.mark.slow
def test_performance_heavy():
    """Slow test example."""
    pass

@pytest.mark.asyncio
async def test_async_function():
    """Async test example."""
    pass
```

## Writing Tests

### Test Structure

Follow this structure for test files:

```python
"""
Test module docstring explaining what is being tested.
"""

import pytest
from unittest.mock import Mock, patch
# ... other imports

class TestComponentName:
    """Test class for a specific component."""
    
    @pytest.fixture
    def sample_data(self):
        """Fixture providing test data."""
        return {"key": "value"}
    
    def test_specific_functionality(self, sample_data):
        """Test a specific piece of functionality."""
        # Arrange
        # Act
        # Assert
        pass
    
    @pytest.mark.asyncio
    async def test_async_functionality(self):
        """Test async functionality."""
        result = await async_function()
        assert result is not None
```

### Best Practices

1. **Use descriptive test names**: `test_fuzzy_search_returns_relevant_results`
2. **Follow AAA pattern**: Arrange, Act, Assert
3. **Use fixtures for setup**: Avoid repetitive setup code
4. **Mock external dependencies**: Use `unittest.mock` for isolation
5. **Test edge cases**: Empty inputs, error conditions, boundary values
6. **Use parametrized tests**: Test multiple scenarios efficiently

```python
@pytest.mark.parametrize("input,expected", [
    ("hello", "HELLO"),
    ("world", "WORLD"),
    ("", ""),
])
def test_uppercase_function(input, expected):
    assert uppercase(input) == expected
```

### Async Testing

For async functions, use `pytest.mark.asyncio`:

```python
@pytest.mark.asyncio
async def test_async_mcp_tool():
    """Test async MCP tool functionality."""
    result = await get_document("test.md")
    assert "content" in result
```

### Mocking

Use mocking to isolate components:

```python
from unittest.mock import Mock, patch, mock_open

def test_file_reading():
    """Test file reading with mocked file system."""
    with patch('builtins.open', mock_open(read_data='test content')):
        result = read_file('test.txt')
        assert result == 'test content'

@patch('external_service.api_call')
def test_external_service(mock_api):
    """Test with mocked external service."""
    mock_api.return_value = {'status': 'success'}
    result = call_external_service()
    assert result['status'] == 'success'
```

## Coverage Reports

### Viewing Coverage

After running tests with coverage:

```bash
# Terminal report
python -m pytest --cov=src --cov-report=term-missing

# HTML report
python -m pytest --cov=src --cov-report=html
open htmlcov/index.html

# XML report (for CI)
python -m pytest --cov=src --cov-report=xml
```

### Coverage Goals

- **Minimum Coverage**: 80% (enforced by pytest configuration)
- **Target Coverage**: 90%+ for critical components
- **Focus Areas**: Core functionality, error handling, edge cases

## Continuous Integration

### GitHub Actions

Tests run automatically on:

- Pull requests
- Pushes to main branch
- Release creation

### Local Pre-commit

Run tests before committing:

```bash
# Quick tests
python scripts/run_tests.py quick

# Full suite
python scripts/run_tests.py full
```

## Debugging Tests

### Running Individual Tests

```bash
# Single test file
python -m pytest tests/unit/test_server.py -v

# Single test class
python -m pytest tests/unit/test_server.py::TestServerInitialization -v

# Single test method
python -m pytest tests/unit/test_server.py::TestServerInitialization::test_main_calls_initialize_documentation_tools -v
```

### Debug Output

```bash
# Show print statements
python -m pytest -s

# Show local variables on failure
python -m pytest --tb=long

# Drop into debugger on failure
python -m pytest --pdb
```

### Common Issues

1. **Import Errors**: Ensure `src` is in Python path
2. **Async Test Failures**: Use `@pytest.mark.asyncio`
3. **Mock Issues**: Reset mocks between tests
4. **File Path Issues**: Use `Path` objects for cross-platform compatibility

## Performance Testing

### Load Testing

Test with large datasets:

```python
@pytest.mark.performance
def test_large_document_set():
    """Test performance with many documents."""
    # Create 1000 test documents
    # Measure processing time
    # Assert reasonable performance
```

### Memory Testing

Monitor memory usage:

```python
import psutil
import os

def test_memory_usage():
    """Test memory usage stays reasonable."""
    process = psutil.Process(os.getpid())
    initial_memory = process.memory_info().rss
    
    # Perform memory-intensive operation
    
    final_memory = process.memory_info().rss
    memory_increase = final_memory - initial_memory
    
    # Assert memory increase is reasonable
    assert memory_increase < 100 * 1024 * 1024  # Less than 100MB
```

## Test Data Management

### Fixtures

Use fixtures for reusable test data:

```python
@pytest.fixture
def sample_documents():
    """Provide sample documents for testing."""
    return {
        'doc1.md': '# Document 1\n\nContent...',
        'doc2.md': '# Document 2\n\nContent...',
    }

@pytest.fixture
def temp_directory():
    """Provide temporary directory for tests."""
    import tempfile
    import shutil
    
    temp_dir = tempfile.mkdtemp()
    yield temp_dir
    shutil.rmtree(temp_dir)
```

### Test Isolation

Ensure tests don't interfere with each other:

```python
def setup_method(self):
    """Set up before each test method."""
    # Reset state
    pass

def teardown_method(self):
    """Clean up after each test method."""
    # Clean up resources
    pass
```

## Contributing Tests

When adding new functionality:

1. **Write tests first** (TDD approach)
2. **Test both success and failure cases**
3. **Include edge cases and boundary conditions**
4. **Update documentation** if needed
5. **Ensure tests pass** before submitting PR

### Test Review Checklist

- [ ] Tests cover new functionality
- [ ] Tests include error cases
- [ ] Tests are properly isolated
- [ ] Tests have descriptive names
- [ ] Tests follow project conventions
- [ ] Coverage remains above threshold
- [ ] Tests pass consistently

## Troubleshooting

### Common Test Failures

1. **Import Errors**
   ```bash
   # Add src to Python path
   export PYTHONPATH="${PYTHONPATH}:$(pwd)/src"
   ```

2. **Async Test Issues**
   ```python
   # Use proper async test decorator
   @pytest.mark.asyncio
   async def test_async_function():
       pass
   ```

3. **Mock Reset Issues**
   ```python
   # Reset mocks in setup
   def setup_method(self):
       mock_object.reset_mock()
   ```

4. **File Path Issues**
   ```python
   # Use Path objects
   from pathlib import Path
   test_file = Path(__file__).parent / 'test_data.txt'
   ```

### Getting Help

- Check test output for specific error messages
- Use `--tb=long` for detailed tracebacks
- Run individual tests to isolate issues
- Check mock configurations and return values
- Verify test data and fixtures

## Resources

- [pytest Documentation](https://docs.pytest.org/)
- [unittest.mock Documentation](https://docs.python.org/3/library/unittest.mock.html)
- [Coverage.py Documentation](https://coverage.readthedocs.io/)
- [pytest-asyncio Documentation](https://pytest-asyncio.readthedocs.io/)
