from importlib import resources

from mcp.server.fastmcp import FastMCP

pkg_resources = resources.files("strands_mcp_server")

mcp = FastMCP(
    "strands-agents-mcp-server",
    instructions="""
    # Strands Agents MCP Server

    This server provides tools to access Strands Agents documentation.
    Strands Agents is a Python SDK for building AI agents.
    It may also be referred to as simply 'Strands'.

    The full documentation can be found at https://strandsagents.com.
""",
)


def create_documentation_tool(filename: str):
    """Create a documentation tool for a given markdown file."""
    # Remove .md extension to get the tool name
    tool_name = filename.replace('.md', '')
    
    # Generate description from filename by converting underscores to spaces and capitalizing
    topic = tool_name.replace('_', ' ').title()
    description = f'Documentation on {topic} in Strands Agents.'

    async def tool_function() -> str:
        return pkg_resources.joinpath("content", filename).read_text(encoding="utf-8")

    mcp.add_tool(tool_function, name=tool_name, description=description)


def initialize_tools():
    """Initialize all documentation tools by scanning the content directory."""
    content_dir = pkg_resources.joinpath("content")
    if content_dir.is_dir():
        for item in content_dir.iterdir():
            if item.is_file() and item.name.endswith('.md'):
                create_documentation_tool(item.name)

initialize_tools()


def main():
    mcp.run()
