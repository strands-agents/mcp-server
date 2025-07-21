<div align="center">
  <div>
    <a href="https://strandsagents.com">
      <img src="https://strandsagents.com/latest/assets/logo-github.svg" alt="Strands Agents" width="55px" height="105px">
    </a>
  </div>

  <h1>
    Strands Agents MCP Server
  </h1>

  <h2>
    A model-driven approach to building AI agents in just a few lines of code.
  </h2>

  <div align="center">
    <a href="https://github.com/strands-agents/mcp-server/graphs/commit-activity"><img alt="GitHub commit activity" src="https://img.shields.io/github/commit-activity/m/strands-agents/mcp-server"/></a>
    <a href="https://github.com/strands-agents/mcp-server/issues"><img alt="GitHub open issues" src="https://img.shields.io/github/issues/strands-agents/mcp-server"/></a>
    <a href="https://github.com/strands-agents/mcp-server/pulls"><img alt="GitHub open pull requests" src="https://img.shields.io/github/issues-pr/strands-agents/mcp-server"/></a>
    <a href="https://github.com/strands-agents/mcp-server/blob/main/LICENSE"><img alt="License" src="https://img.shields.io/github/license/strands-agents/mcp-server"/></a>
    <a href="https://pypi.org/project/strands-agents-mcp-server/"><img alt="PyPI version" src="https://img.shields.io/pypi/v/strands-agents-mcp-server"/></a>
    <a href="https://python.org"><img alt="Python versions" src="https://img.shields.io/pypi/pyversions/strands-agents-mcp-server"/></a>
  </div>
  
  <p>
    <a href="https://strandsagents.com/">Documentation</a>
    ◆ <a href="https://github.com/strands-agents/samples">Samples</a>
    ◆ <a href="https://github.com/strands-agents/sdk-python">Python SDK</a>
    ◆ <a href="https://github.com/strands-agents/tools">Tools</a>
    ◆ <a href="https://github.com/strands-agents/agent-builder">Agent Builder</a>
    ◆ <a href="https://github.com/strands-agents/mcp-server">MCP Server</a>
  </p>
</div>

This MCP server provides documentation about Strands Agents to your GenAI tools, so you can use your favorite AI coding assistant to vibe-code Strands Agents.

## Prerequisites

The usage methods below require [uv](https://github.com/astral-sh/uv) to be installed on your system. You can install it by following the [official installation instructions](https://github.com/astral-sh/uv#installation).

## Installation

You can use the Strands Agents MCP server with
[40+ applications that support MCP servers](https://modelcontextprotocol.io/clients),
including Amazon Q Developer CLI, Anthropic Claude Code, Cline, and Cursor.

### Q Developer CLI example

See the [Q Developer CLI documentation](https://docs.aws.amazon.com/amazonq/latest/qdeveloper-ug/command-line-mcp-configuration.html)
for instructions on managing MCP configuration.

In `~/.aws/amazonq/mcp.json`:

```json
{
  "mcpServers": {
    "strands": {
      "command": "uvx",
      "args": ["strands-agents-mcp-server"]
    }
  }
}
```

### Claude Code example

See the [Claude Code documentation](https://docs.anthropic.com/en/docs/claude-code/tutorials#configure-mcp-servers)
for instructions on managing MCP servers.

```bash
claude mcp add strands uvx strands-agents-mcp-server
```

### Cline example

See the [Cline documentation](https://docs.cline.bot/mcp-servers/configuring-mcp-servers#editing-mcp-settings-files)
for instructions on managing MCP configuration.

Provide Cline with the following information:

```
I want to add the MCP server for Strands Agents.
Here's the GitHub link: @https://github.com/strands-agents/mcp-server
Can you add it?"
```

### Cursor example

See the [Cursor documentation](https://docs.cursor.com/context/model-context-protocol#configuring-mcp-servers)
for instructions on managing MCP configuration.

In `~/.cursor/mcp.json`:

```json
{
  "mcpServers": {
    "strands": {
      "command": "uvx",
      "args": ["strands-agents-mcp-server"]
    }
  }
}
```

## Quick Testing

You can quickly test the MCP server using the MCP Inspector:

```bash
npx @modelcontextprotocol/inspector uvx strands-agents-mcp-server
```

Note: This requires [npx](https://docs.npmjs.com/cli/v11/commands/npx) to be installed on your system. It comes bundled with [Node.js](https://nodejs.org/). 

The Inspector is also useful for troubleshooting MCP server issues as it provides detailed connection and protocol information. For an in-depth guide, have a look at the [MCP Inspector documentation](https://modelcontextprotocol.io/docs/tools/inspector).

## Server development

```bash
git clone https://github.com/strands-agents/mcp-server.git
cd mcp-server
python3 -m venv venv
source venv/bin/activate
pip3 install -e .

npx @modelcontextprotocol/inspector python -m strands_mcp_server
```

## Contributing ❤️

We welcome contributions! See our [Contributing Guide](CONTRIBUTING.md) for details on:
- Reporting bugs & features
- Development setup
- Contributing via Pull Requests
- Code of Conduct
- Reporting of security issues

## License

This project is licensed under the Apache License 2.0 - see the [LICENSE](LICENSE) file for details.

## Security

See [CONTRIBUTING](CONTRIBUTING.md#security-issue-notifications) for more information.
