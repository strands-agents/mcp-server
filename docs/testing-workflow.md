# Testing the Documentation Sync Workflow

This document provides instructions for testing the complete documentation sync workflow, including the GitHub Action, sync script, and dynamic tool registration.

## Overview

The documentation sync workflow consists of three main components:

1. **GitHub Action Workflow**: Defined in `.github/workflows/sync-docs.yml`, this workflow runs on a schedule, when triggered manually, or when changes are pushed to the main branch.
2. **Sync Script**: Located at `scripts/sync_docs.py`, this script handles the actual synchronization of markdown files between repositories.
3. **Dynamic Tool Registration**: Implemented in `src/strands_mcp_server/server.py`, this component automatically registers markdown files as documentation tools in the MCP server.

## Testing the Complete Workflow

### 1. Unit Tests

The complete workflow is tested through several unit test files:

- `tests/unit/test_complete_workflow.py`: Tests the basic functionality of the sync script and tool registration.
- `tests/unit/test_github_action_workflow.py`: Tests the GitHub Action workflow with mock repositories.
- `tests/unit/test_sync_docs.py`: Tests the sync script in detail, including validation and error handling.
- `tests/unit/test_dynamic_tool_registration.py`: Tests the dynamic tool registration functionality.

To run all the tests:

```bash
python -m unittest discover tests/unit
```

### 2. Manual Testing

#### Testing the Sync Script

You can manually test the sync script by running:

```bash
python scripts/sync_docs.py --source /path/to/source --target /path/to/target --validate
```

This will synchronize markdown files from the source directory to the target directory, validating them in the process.

#### Testing the GitHub Action

To test the GitHub Action workflow:

1. Make changes to the documentation in the Strands Agents docs repository.
2. Trigger the workflow manually from the GitHub Actions tab.
3. Verify that the changes are properly synced to the MCP server content folder.

#### Testing the Dynamic Tool Registration

To test the dynamic tool registration:

1. Add a new markdown file to the `src/strands_mcp_server/content` directory.
2. Start the MCP server.
3. Verify that the new file is automatically registered as a documentation tool.

## Troubleshooting

### Common Issues

1. **Validation Failures**: If files fail validation, check the validation reports in the `validation_reports` directory.
2. **Sync Errors**: If the sync script encounters errors, check the error reports in the `error_reports` directory.
3. **Tool Registration Issues**: If tools are not being registered correctly, check that the markdown files are properly formatted and located in the correct directory.

### Debugging

For more detailed debugging:

1. Run the sync script with the `--log-level DEBUG` option:
   ```bash
   python scripts/sync_docs.py --source /path/to/source --target /path/to/target --log-level DEBUG
   ```

2. Check the GitHub Action logs for detailed information about the workflow execution.

3. Add print statements to the `initialize_documentation_tools` function in `server.py` to debug tool registration issues.

## Conclusion

By thoroughly testing all components of the documentation sync workflow, we can ensure that the MCP server always has the most up-to-date documentation available for users. The automated tests provide confidence that the workflow works correctly, while manual testing allows for verification in real-world scenarios.