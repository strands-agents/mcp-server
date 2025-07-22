#!/usr/bin/env python3
"""
Run the Strands MCP server locally with various configuration options.

This script provides a flexible way to run the Strands MCP server with different options:
1. Run with existing content in the MCP server content directory
2. Run with content from a specified directory
3. Sync documentation from a source repository before running
4. Validate markdown files during sync

Usage:
    python run_mcp_server.py [--source SOURCE] [--content-dir CONTENT_DIR] [--sync] [--validate] [--custom]

Options:
    --source SOURCE       Source directory containing markdown files (default: test-repos/docs/docs)
    --content-dir CONTENT_DIR  Path to the content directory (default: src/strands_mcp_server/content)
    --sync                Sync documentation from source to content directory before running
    --validate            Validate markdown files during sync
    --custom              Run the custom server instead of the standard server
"""

import os
import sys
import shutil
import argparse
import subprocess
from pathlib import Path

def parse_args():
    """Parse command-line arguments."""
    parser = argparse.ArgumentParser(
        description="Run the Strands MCP server locally with various configuration options."
    )
    parser.add_argument(
        "--source",
        help="Source directory containing markdown files (default: test-repos/docs/docs)",
        default="test-repos/docs/docs"
    )
    parser.add_argument(
        "--content-dir",
        help="Path to the content directory (default: src/strands_mcp_server/content)",
        default="src/strands_mcp_server/content"
    )
    parser.add_argument(
        "--sync",
        help="Sync documentation from source to content directory before running",
        action="store_true"
    )
    parser.add_argument(
        "--validate",
        help="Validate markdown files during sync",
        action="store_true"
    )
    parser.add_argument(
        "--custom",
        help="Run the custom server instead of the standard server",
        action="store_true"
    )
    return parser.parse_args()

def ensure_source_directory(source_dir):
    """
    Ensure the source directory exists, cloning the repository if necessary.
    
    Args:
        source_dir (str): Source directory containing markdown files
        
    Returns:
        bool: True if the directory exists or was created, False otherwise
    """
    if os.path.isdir(source_dir):
        return True
        
    # Check if we need to clone the repository
    if source_dir == "test-repos/docs/docs" and not os.path.isdir("test-repos/docs"):
        print("Cloning the Strands Agents docs repository...")
        os.makedirs("test-repos", exist_ok=True)
        result = subprocess.run(["git", "clone", "https://github.com/strands-agents/docs.git", "test-repos/docs"], check=True)
        
        # Check if the source directory exists now
        if os.path.isdir(source_dir):
            return True
        else:
            print(f"Error: Source directory '{source_dir}' still does not exist after cloning")
            return False
    else:
        print(f"Error: Source directory '{source_dir}' does not exist")
        return False

def run_sync_script(source_dir, content_dir, validate=False):
    """
    Run the sync script to synchronize docs from a source repository.
    
    Args:
        source_dir (str): Source directory containing markdown files
        content_dir (str): Target directory for synced docs
        validate (bool): Whether to validate markdown files before syncing
        
    Returns:
        bool: True if successful, False otherwise
    """
    # Build the command
    cmd = [
        "python", "scripts/sync_docs.py",
        "--source", source_dir,
        "--target", content_dir
    ]
    
    if validate:
        cmd.append("--validate")
    
    # Run the sync script
    print(f"Running sync script: {' '.join(cmd)}")
    try:
        result = subprocess.run(cmd, check=True)
        return result.returncode == 0
    except subprocess.CalledProcessError:
        print("Error: Sync script failed")
        return False

def run_standard_server():
    """
    Run the standard MCP server.
    
    Returns:
        int: Return code from the server process
    """
    # Run the MCP server
    print("Starting standard MCP server...")
    cmd = ["python", "-m", "strands_mcp_server"]
    
    # Run the server in a new process
    server_process = subprocess.Popen(cmd)
    
    print("\nMCP server is running. Press Ctrl+C to stop.")
    print("\nYou can configure Kiro or Amazon Q to use this server with the following configuration:")
    print("""
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
""")
    
    try:
        # Wait for the server process to terminate
        return server_process.wait()
    except KeyboardInterrupt:
        # Handle Ctrl+C
        print("\nStopping MCP server...")
        server_process.terminate()
        return 0

def run_custom_server(content_dir):
    """
    Run the custom MCP server with a specified content directory.
    
    Args:
        content_dir (str): Path to the content directory
        
    Returns:
        int: Return code from the server process
    """
    # Get the absolute path to the content directory
    content_dir = os.path.abspath(content_dir)
    
    # Set the environment variable
    os.environ["CONTENT_DIR_PATH"] = content_dir
    
    # Run the custom MCP server
    print(f"Starting custom MCP server with content directory: {content_dir}")
    cmd = ["python", "-m", "src.strands_mcp_server.custom_server"]
    
    # Run the server in a new process
    server_process = subprocess.Popen(cmd)
    
    print("\nCustom MCP server is running. Press Ctrl+C to stop.")
    print("\nYou can configure Kiro or Amazon Q to use this server with the following configuration:")
    print(f"""
{{
  "mcpServers": {{
    "strands-local": {{
      "command": "python",
      "args": ["-m", "src.strands_mcp_server.custom_server"],
      "env": {{
        "FASTMCP_LOG_LEVEL": "INFO",
        "CONTENT_DIR_PATH": "{content_dir}"
      }},
      "disabled": false,
      "autoApprove": ["mcp_strands_quickstart", "mcp_strands_model_providers", "mcp_strands_agent_tools"]
    }}
  }}
}}
""")
    
    try:
        # Wait for the server process to terminate
        return server_process.wait()
    except KeyboardInterrupt:
        # Handle Ctrl+C
        print("\nStopping MCP server...")
        server_process.terminate()
        return 0

def main():
    """Main function."""
    # Parse command-line arguments
    args = parse_args()
    
    # Ensure the source directory exists if we need to sync
    if args.sync and not ensure_source_directory(args.source):
        sys.exit(1)
    
    # Sync documentation if requested
    if args.sync:
        if not run_sync_script(args.source, args.content_dir, args.validate):
            sys.exit(1)
    
    # Run the appropriate server
    if args.custom:
        return run_custom_server(args.content_dir)
    else:
        return run_standard_server()

if __name__ == "__main__":
    sys.exit(main())