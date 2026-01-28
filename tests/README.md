# Strands MCP Server Tests

This directory contains tests for the Strands MCP Server prompt generation functionality.

## Test Structure

- `test_prompts.py` - Unit tests for prompt generation functions
- `test_mcp_server.py` - Integration tests for MCP server endpoints

## Running Tests

### Install Dependencies

First, install the development dependencies:

```bash
pip install -e ".[dev]"
```

### Run All Tests

```bash
pytest tests -v
```

### Run Specific Test Files

```bash
# Test prompt generation
pytest tests/test_prompts.py -v

# Test MCP server integration
pytest tests/test_mcp_server.py -v
```

### Run with Coverage

```bash
pytest tests --cov=strands_mcp_server --cov-report=html
```

### Run Specific Test Classes or Functions

```bash
# Run a specific test class
pytest tests/test_prompts.py::TestGenerateToolPrompt -v

# Run a specific test function
pytest tests/test_mcp_server.py::TestTemplateFiles::test_template_files_exist -v
```

## Test Categories

### Unit Tests
- `TestRegexReplaceFilter` - Tests for the Jinja2 regex filter
- `TestFetchContent` - Tests for content fetching
- `TestGenerateToolPrompt` - Tests for tool prompt generation
- `TestGenerateAgentPrompt` - Tests for agent prompt generation
- `TestGenerateSessionPrompt` - Tests for session prompt generation
- `TestGenerateModelPrompt` - Tests for model provider prompt generation
- `TestGenerateMultiagentPrompt` - Tests for multi-agent prompt generation

### Integration Tests
- `TestMCPPromptEndpoints` - Tests for MCP server prompt endpoints
- `TestSearchDocsIntegration` - Tests for document search
- `TestFetchDocIntegration` - Tests for document fetching
- `TestMCPServerRegistration` - Tests for proper MCP registration
- `TestTemplateFiles` - Tests for template file existence and validity

## Adding New Tests

When adding new prompt templates or functionality:

1. Add unit tests for the prompt generation function in `test_prompts.py`
2. Add integration tests for the MCP endpoint in `test_mcp_server.py`
3. Ensure the template file exists and has valid Jinja2 syntax
4. Test with both minimal and full parameters

## Continuous Integration

These tests should be run as part of the CI/CD pipeline to ensure:
- All templates are present and valid
- Prompt generation works correctly
- MCP endpoints are properly registered
- No regressions in functionality