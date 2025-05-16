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


@mcp.tool()
async def quickstart() -> str:
    """Quickstart documentation for Strands Agents SDK."""
    return pkg_resources.joinpath("content", "quickstart.md").read_text(
        encoding="utf-8"
    )


@mcp.tool()
async def model_providers() -> str:
    """Documentation on using different model providers in Strands Agents."""
    return pkg_resources.joinpath("content", "model_providers.md").read_text(
        encoding="utf-8"
    )


@mcp.tool()
async def agent_tools() -> str:
    """Documentation on adding tools to agents using Strands Agents."""
    return pkg_resources.joinpath("content", "tools.md").read_text(encoding="utf-8")


def main():
    mcp.run()
