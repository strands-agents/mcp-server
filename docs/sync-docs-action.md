# Documentation Sync GitHub Action

This document provides detailed information about the GitHub Action that synchronizes documentation from the Strands Agents docs repository to the MCP server content folder.

## Overview

The Documentation Sync GitHub Action ensures that the MCP server always has the most up-to-date documentation available for users. It automatically fetches the latest documentation from the [Strands Agents docs repository](https://github.com/strands-agents/docs) and updates the content folder in the MCP server repository.

## How It Works

The sync process follows these steps:

1. **Checkout Repositories**: The action checks out both the MCP server repository and the Strands Agents docs repository.
2. **Setup Python Environment**: It sets up a Python environment with the necessary dependencies.
3. **Run Sync Script**: The action executes the `sync_docs.py` script, which:
   - Scans the source directory (docs repository) for markdown files
   - Compares them with files in the target directory (MCP server content folder)
   - Copies new and modified files from source to target
   - Deletes files from target that no longer exist in source
   - Validates markdown files to ensure they are properly formatted
4. **Commit Changes**: If any files were added, updated, or deleted, the action commits the changes back to the repository.
5. **Report Statistics**: The action generates statistics about what was updated and includes them in the workflow run summary.

## Triggers

The action runs automatically in the following scenarios:

1. **Schedule**: Daily at midnight UTC to ensure regular updates
2. **Push to Main**: When changes are pushed to the main branch
3. **Manual Trigger**: When manually triggered through the GitHub Actions interface
4. **Release Publishing**: When a new release is published, as part of the PyPI publish workflow

## Manually Triggering the Action

To manually trigger the documentation sync:

1. Go to the [Actions tab](https://github.com/strands-agents/mcp-server/actions) in the repository
2. Select the "Sync Documentation" workflow from the left sidebar
3. Click the "Run workflow" button
4. Select the branch you want to run the workflow on (typically "main")
5. Click "Run workflow" to start the sync process

![Manual Trigger Screenshot](https://docs.github.com/assets/cb-25535/mw-1440/images/help/actions/workflow-dispatch.webp)

## Workflow Configuration

The workflow is configured in the `.github/workflows/sync-docs.yml` file. Key configuration points include:

- **Triggers**: Schedule, push to main, and manual trigger
- **Permissions**: Write access to repository contents (needed to commit changes)
- **Steps**: Checkout repositories, setup Python, run sync script, commit changes, report statistics

## Integration with PyPI Publishing

The documentation sync is also integrated with the PyPI publishing workflow (`.github/workflows/pypi-publish-on-release.yml`). This ensures that the latest documentation is included in each PyPI release:

1. When a new release is published, the workflow checks out both repositories
2. Before building the package, it runs the sync script to update the documentation in the content folder
3. The package is then built with the latest documentation included
4. The package is published to PyPI

This integration ensures that users always have access to the most current documentation when installing the package from PyPI, even if the documentation in the main repository hasn't been updated recently.

## Sync Script

The sync script (`scripts/sync_docs.py`) is the core component that performs the actual synchronization. It can be run both as part of the GitHub Action and manually for testing purposes.

### Directory Structure Handling

The sync script preserves the directory structure from the source repository:

1. It recursively scans all subdirectories in the source repository for markdown files
2. When copying files to the target directory, it maintains the same directory structure
3. This ensures that documentation organized in subdirectories (like guides, tutorials, reference, etc.) maintains its organization

## Dynamic Tool Registration

When new documentation files are added to the content folder, they are automatically registered as tools when the MCP server starts. This is handled by the `initialize_documentation_tools` function in `server.py`, which recursively scans the content directory for markdown files and registers each file as a documentation tool.

This dynamic registration system allows new documentation to be automatically available as tools without requiring code changes. The system also properly handles subdirectories in the documentation repository:

1. Files in subdirectories are registered with tool names that incorporate their directory structure
2. Tool names for files in subdirectories use underscores to separate directory levels (e.g., `guides_getting_started` for a file at `guides/getting_started.md`)
3. This ensures that all documentation files, regardless of their location in the directory structure, are properly registered as tools and accessible through the MCP interface

### Running the Script Manually

To run the sync script manually:

```bash
# Clone both repositories
git clone https://github.com/strands-agents/mcp-server.git
git clone https://github.com/strands-agents/docs.git

# Run the sync script
cd mcp-server
python scripts/sync_docs.py --source ../docs --target ./src/strands_mcp_server/content --validate
```

### Script Options

The sync script supports the following command-line options:

- `--source`, `-s`: Source directory containing markdown files
- `--target`, `-t`: Target directory to sync files to
- `--log-level`, `-l`: Set the logging level (DEBUG, INFO, WARNING, ERROR, CRITICAL)
- `--validate`, `-v`: Validate markdown files before syncing
- `--strict-validation`: Treat validation failures as errors instead of just skipping files

## Dynamic Tool Registration

When new documentation files are added to the content folder, they are automatically registered as tools when the MCP server starts. This is handled by the `initialize_documentation_tools` function in `server.py`, which scans the content directory for markdown files and registers each file as a documentation tool.

This dynamic registration system allows new documentation to be automatically available as tools without requiring code changes to the server.

## Troubleshooting

If the sync action fails, check the following:

1. **Access to Repositories**: Ensure the GitHub Action has the necessary permissions to access both repositories.
2. **Validation Failures**: Check if any markdown files failed validation. The action generates validation reports in the `validation_reports` directory.
3. **Error Reports**: Look for error reports in the `error_reports` directory for detailed information about any failures.
4. **Workflow Run Logs**: Review the logs for the workflow run in the GitHub Actions interface for error messages and stack traces.

## Statistics and Reporting

After each sync, the action generates statistics about what was updated:

- Added files
- Updated files
- Deleted files
- Unchanged files
- Validation failures (if any)
- Total changes
- Success rate

These statistics are available in the workflow run summary and can help track documentation updates over time.