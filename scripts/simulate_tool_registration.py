"""
Simulate the tool registration process for the synchronized documentation files.

This script demonstrates how the MCP server would register the documentation files
as tools, without actually starting the server.
"""

import os
from pathlib import Path

def simulate_create_documentation_tool(file_path: str):
    """
    Simulate the create_documentation_tool function from server.py.
    
    Args:
        file_path (str): The path to the markdown file relative to the content directory
        
    Returns:
        tuple: The tool name and description
    """
    # Convert path to Path object for easier manipulation
    path_obj = Path(file_path)
    
    # Remove .md extension to get the base name
    base_name = path_obj.stem
    
    # If the file is in a subdirectory, include the directory in the tool name
    # Replace directory separators with underscores
    if len(path_obj.parts) > 1:
        # Join all parts except the last one (filename) with underscores
        prefix = '_'.join(path_obj.parts[:-1])
        tool_name = f"{prefix}_{base_name}"
    else:
        tool_name = base_name
    
    # Generate description from filename by converting underscores to spaces and capitalizing
    topic = tool_name.replace('_', ' ').title()
    description = f'Documentation on {topic} in Strands Agents.'
    
    return tool_name, description

def simulate_initialize_documentation_tools(content_dir):
    """
    Simulate the initialize_documentation_tools function from server.py.
    
    Args:
        content_dir (str): The path to the content directory
        
    Returns:
        list: A list of tuples containing the tool name and description for each file
    """
    # Skip these files as they have explicit tool definitions
    skip_files = ["quickstart.md", "model_providers.md", "tools.md"]
    
    # List to store the registered tools
    registered_tools = []
    
    # Recursively find all markdown files
    for root, _, files in os.walk(content_dir):
        for file in files:
            if file.endswith('.md'):
                # Get the relative path from the content directory
                rel_path = os.path.relpath(os.path.join(root, file), content_dir)
                
                # Skip files that already have explicit tool definitions
                if file in skip_files and os.path.dirname(rel_path) == '':
                    continue
                
                # Create a tool with the relative path
                tool_name, description = simulate_create_documentation_tool(rel_path)
                registered_tools.append((tool_name, description))
    
    return registered_tools

def main():
    # Path to the synchronized documentation files
    content_dir = 'test-repos/mcp-content-docs-only'
    
    # Simulate the tool registration process
    registered_tools = simulate_initialize_documentation_tools(content_dir)
    
    # Print the registered tools
    print(f"Total registered tools: {len(registered_tools)}")
    print("\nAll registered tools:")
    for i, (tool_name, description) in enumerate(sorted(registered_tools)):
        print(f"{i+1}. {tool_name}: {description}")

if __name__ == "__main__":
    main()