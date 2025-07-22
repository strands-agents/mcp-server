# Running the Strands MCP Server Locally

This document explains how to run the Strands MCP server locally with synced documentation.

## Prerequisites

- Python 3.8 or higher
- Git (for cloning the docs repository)
- The Strands MCP server package installed

## Running the Server

We provide a script that automates the process of syncing documentation and running the MCP server locally:

```bash
python run_local_mcp_server.py
```

This script will:

1. Clone the Strands Agents docs repository if it doesn't exist
2. Run the sync script to synchronize docs from the repository
3. Copy the synced docs to the MCP server content directory
4. Run the MCP server locally

## Options

The script supports the following options:

- `--source SOURCE`: Source directory containing markdown files (default: test-repos/docs/docs)
- `--validate`: Validate markdown files before syncing

Example:

```bash
# Run with a custom source directory
python run_local_mcp_server.py --source /path/to/docs

# Run with validation
python run_local_mcp_server.py --validate
```

## Configuring Kiro or Amazon Q

To use the local MCP server with Kiro or Amazon Q, add the following configuration to your MCP configuration file:

```json
{
  "mcpServers": {
    "strands-local": {
      "command": "python",
      "args": ["-m", "strands_mcp_server"],
      "env": {
        "FASTMCP_LOG_LEVEL": "INFO"
      },
      "disabled": false,
      "autoApprove": ["mcp_strands_quickstart", "mcp_strands_model_providers", "mcp_strands_agent_tools"]
    }
  }
}
```

## Stopping the Server

To stop the server, press `Ctrl+C` in the terminal where the server is running.

## Troubleshooting

If you encounter any issues:

1. Make sure the Strands MCP server package is installed
2. Check that the source directory exists and contains markdown files
3. Verify that the content directory is writable
4. Check the server logs for any error messages